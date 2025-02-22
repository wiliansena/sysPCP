from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from app import db
from app.models import FormulacaoSolado, FormulacaoSoladoFriso, Referencia, Componente, CustoOperacional, ReferenciaAlca, ReferenciaComponentes, ReferenciaCustoOperacional, ReferenciaMaoDeObra, ReferenciaSolado, Salario, MaoDeObra
from app.forms import ReferenciaForm, ComponenteForm, CustoOperacionalForm, SalarioForm, MaoDeObraForm
import os
#SOLADO
from flask import render_template, redirect, url_for, flash, request
from app import db
from app.models import Solado, Tamanho, Componente, FormulacaoSolado, Alca, TamanhoAlca, FormulacaoAlca, Colecao
from app.forms import SoladoForm, AlcaForm, ColecaoForm
from flask import Blueprint
import os
from werkzeug.utils import secure_filename  # 🔹 Para salvar o nome do arquivo corretamente
from flask import current_app  # 🔹 Para acessar a configuração da aplicação
from flask_wtf import FlaskForm
from wtforms import HiddenField
from app import db, csrf  # 🔹 Importando o `csrf` que foi definido no __init__.py
from flask.views import MethodView
from decimal import Decimal, ROUND_HALF_UP  # Importa Decimal para cálculos precisos
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('routes', __name__)

UPLOAD_FOLDER = 'app/static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class DeleteForm(FlaskForm):
    csrf_token = HiddenField()

@bp.route('/')
def home():
    return render_template('home.html')

    #REFERENCIAS




@bp.route('/referencias', methods=['GET'])
def listar_referencias():
    filtro = request.args.get('filtro', '')
    if filtro:
        referencias = Referencia.query.filter(Referencia.codigo_referencia.ilike(f"{filtro}%")).all()
    else:
        referencias = Referencia.query.all()
    return render_template('referencias.html', referencias=referencias)



# 🔹 Função para converter valores para float de forma segura
def parse_float(value, default=0):
    try:
        return float(value.strip()) if value.strip() else default
    except (ValueError, AttributeError):
        return default



@bp.route('/referencia/novo', methods=['GET', 'POST'])
def nova_referencia():
    form = ReferenciaForm()

    # 🔹 Recupera os dados do banco corretamente
    solados = Solado.query.all()
    alcas = Alca.query.all()
    componentes = Componente.query.all()
    custos_operacionais = CustoOperacional.query.all()
    mao_de_obra = MaoDeObra.query.all()

    if form.validate_on_submit():
        referencia = Referencia(
            codigo_referencia=form.codigo_referencia.data,
            descricao=form.descricao.data,
            linha=form.linha.data,
            imagem=form.imagem.data.filename if form.imagem.data else None,
            
            # 🔹 Correção: Convertendo `Decimal` para `float`
            total_solado= sum(float(consumo) * float(Solado.query.get(int(solado_id)).custo_total)
                              for solado_id, consumo in zip(request.form.getlist("solado_id[]"), request.form.getlist("solado_consumo[]")) if consumo),

            total_alcas= sum(float(consumo) * float(Alca.query.get(int(alca_id)).preco_total)
                             for alca_id, consumo in zip(request.form.getlist("alca_id[]"), request.form.getlist("alca_consumo[]")) if consumo),

            total_componentes= sum(float(consumo) * float(Componente.query.get(int(componente_id)).preco)
                                   for componente_id, consumo in zip(request.form.getlist("componente_id[]"), request.form.getlist("componente_consumo[]")) if consumo),

            total_operacional= sum(float(consumo) * float(CustoOperacional.query.get(int(custo_id)).preco)
                                   for custo_id, consumo in zip(request.form.getlist("custo_id[]"), request.form.getlist("custo_consumo[]")) if consumo),

            total_mao_de_obra= sum(float(consumo) * float(MaoDeObra.query.get(int(mao_obra_id)).diaria)
                                   for mao_obra_id, consumo in zip(request.form.getlist("mao_obra_id[]"), request.form.getlist("mao_obra_consumo[]")) if consumo),
        )

        # Salvar imagem
        if form.imagem.data:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join("static/uploads", imagem_filename)
            form.imagem.data.save(caminho_imagem)
            referencia.imagem = imagem_filename

        db.session.add(referencia)
        db.session.flush()  # Captura o ID antes de inserir os relacionamentos

        # Associar os itens corretamente
        for solado_id, consumo in zip(request.form.getlist("solado_id[]"), request.form.getlist("solado_consumo[]")):
            db.session.add(ReferenciaSolado(
                referencia_id=referencia.id,
                solado_id=int(solado_id),
                consumo=float(consumo) if consumo else 0,
                preco_unitario=float(Solado.query.get(int(solado_id)).custo_total)
            ))

        for alca_id, consumo in zip(request.form.getlist("alca_id[]"), request.form.getlist("alca_consumo[]")):
            db.session.add(ReferenciaAlca(
                referencia_id=referencia.id,
                alca_id=int(alca_id),
                consumo=float(consumo) if consumo else 0,
                preco_unitario=float(Alca.query.get(int(alca_id)).preco_total)
            ))

        for componente_id, consumo in zip(request.form.getlist("componente_id[]"), request.form.getlist("componente_consumo[]")):
            db.session.add(ReferenciaComponentes(
                referencia_id=referencia.id,
                componente_id=int(componente_id),
                consumo=float(consumo) if consumo else 0,
                preco_unitario=float(Componente.query.get(int(componente_id)).preco)
            ))

        for custo_id, consumo in zip(request.form.getlist("custo_id[]"), request.form.getlist("custo_consumo[]")):
            db.session.add(ReferenciaCustoOperacional(
                referencia_id=referencia.id,
                custo_id=int(custo_id),
                consumo=float(consumo) if consumo else 0,
                preco_unitario=float(CustoOperacional.query.get(int(custo_id)).preco)
            ))

        for mao_obra_id, consumo, producao in zip(request.form.getlist("mao_obra_id[]"), request.form.getlist("mao_obra_consumo[]"), request.form.getlist("mao_obra_producao[]")):
            db.session.add(ReferenciaMaoDeObra(
                referencia_id=referencia.id,
                mao_de_obra_id=int(mao_obra_id),
                consumo=float(consumo) if consumo else 0,
                producao=float(producao) if producao else 1,
                preco_unitario=float(MaoDeObra.query.get(int(mao_obra_id)).diaria)
            ))

        db.session.commit()
        flash("Referência cadastrada com sucesso!", "success")
        return redirect(url_for('routes.listar_referencias'))

    return render_template(
        'nova_referencia.html',
        form=form,
        solados=solados,
        alcas=alcas,
        componentes=componentes,
        custos_operacionais=custos_operacionais,
        mao_de_obra=mao_de_obra
    )



@bp.route('/referencia/ver/<int:id>', methods=['GET'])
def ver_referencia(id):
    referencia = Referencia.query.get_or_404(id)
    
    # 🔹 Certifique-se de calcular os totais antes de exibir a referência
    referencia.calcular_totais()

    # Recuperando os itens associados
    solados = ReferenciaSolado.query.filter_by(referencia_id=referencia.id).all()
    alcas = ReferenciaAlca.query.filter_by(referencia_id=referencia.id).all()
    componentes = ReferenciaComponentes.query.filter_by(referencia_id=referencia.id).all()
    custos_operacionais = ReferenciaCustoOperacional.query.filter_by(referencia_id=referencia.id).all()
    mao_de_obra = ReferenciaMaoDeObra.query.filter_by(referencia_id=referencia.id).all()

    return render_template(
        'ver_referencia.html',
        referencia=referencia,
        solados=solados,
        alcas=alcas,
        componentes=componentes,
        custos_operacionais=custos_operacionais,
        mao_de_obra=mao_de_obra
    )

@bp.route('/referencia/editar/<int:id>', methods=['GET', 'POST'])
def editar_referencia(id):
    """Edita uma referência existente mantendo os itens e permitindo adicionar novos."""

    referencia = Referencia.query.get_or_404(id)
    form = ReferenciaForm(obj=referencia)

    # 🔹 Recuperar os itens vinculados para exibição no template
    solados = {str(s.solado_id): s for s in ReferenciaSolado.query.filter_by(referencia_id=id).all()}
    alcas = {str(a.alca_id): a for a in ReferenciaAlca.query.filter_by(referencia_id=id).all()}
    componentes = {str(c.componente_id): c for c in ReferenciaComponentes.query.filter_by(referencia_id=id).all()}
    custos_operacionais = {str(co.custo_id): co for co in ReferenciaCustoOperacional.query.filter_by(referencia_id=id).all()}
    mao_de_obra = {str(m.mao_de_obra_id): m for m in ReferenciaMaoDeObra.query.filter_by(referencia_id=id).all()}

    # 🔹 Recuperar todos os itens disponíveis nos modais
    solados_disponiveis = Solado.query.all()
    alcas_disponiveis = Alca.query.all()
    componentes_disponiveis = Componente.query.all()
    custos_disponiveis = CustoOperacional.query.all()
    mao_de_obra_disponiveis = MaoDeObra.query.all()

    if form.validate_on_submit():
        referencia.codigo_referencia = form.codigo_referencia.data
        referencia.descricao = form.descricao.data
        referencia.linha = form.linha.data

        # Se houver uma nova imagem, salva
        if form.imagem.data:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join("static/uploads", imagem_filename)
            form.imagem.data.save(caminho_imagem)
            referencia.imagem = imagem_filename

        ### **🔹 Atualizar SOMENTE os itens modificados e adicionar novos**

        # **Solados**
        solado_ids = request.form.getlist("solado_id[]")
        solado_consumos = request.form.getlist("solado_consumo[]")

        for solado_id, consumo in zip(solado_ids, solado_consumos):
            consumo = float(consumo) if consumo else 1.0  # Evita remover itens se não for informado consumo
            if solado_id in solados:
                solados[solado_id].consumo = consumo  # Atualiza consumo
            else:
                db.session.add(ReferenciaSolado(
                    referencia_id=id,
                    solado_id=int(solado_id),
                    consumo=consumo,
                    preco_unitario=Solado.query.get(int(solado_id)).custo_total
                ))

        # **Alças**
        alca_ids = request.form.getlist("alca_id[]")
        alca_consumos = request.form.getlist("alca_consumo[]")

        for alca_id, consumo in zip(alca_ids, alca_consumos):
            consumo = float(consumo) if consumo else 1.0
            if alca_id in alcas:
                alcas[alca_id].consumo = consumo
            else:
                db.session.add(ReferenciaAlca(
                    referencia_id=id,
                    alca_id=int(alca_id),
                    consumo=consumo,
                    preco_unitario=Alca.query.get(int(alca_id)).preco_total
                ))

        # **Componentes**
        componente_ids = request.form.getlist("componente_id[]")
        componente_consumos = request.form.getlist("componente_consumo[]")

        for componente_id, consumo in zip(componente_ids, componente_consumos):
            consumo = float(consumo) if consumo else 1.0
            if componente_id in componentes:
                componentes[componente_id].consumo = consumo
            else:
                db.session.add(ReferenciaComponentes(
                    referencia_id=id,
                    componente_id=int(componente_id),
                    consumo=consumo,
                    preco_unitario=Componente.query.get(int(componente_id)).preco
                ))

        # **Custos Operacionais**
        custo_ids = request.form.getlist("custo_id[]")
        custo_consumos = request.form.getlist("custo_consumo[]")

        for custo_id, consumo in zip(custo_ids, custo_consumos):
            consumo = float(consumo) if consumo else 1.0
            if custo_id in custos_operacionais:
                custos_operacionais[custo_id].consumo = consumo
            else:
                db.session.add(ReferenciaCustoOperacional(
                    referencia_id=id,
                    custo_id=int(custo_id),
                    consumo=consumo,
                    preco_unitario=CustoOperacional.query.get(int(custo_id)).preco
                ))

        # **Mão de Obra**
        mao_ids = request.form.getlist("mao_obra_id[]")
        mao_consumos = request.form.getlist("mao_obra_consumo[]")
        mao_producoes = request.form.getlist("mao_obra_producao[]")

        for mao_id, consumo, producao in zip(mao_ids, mao_consumos, mao_producoes):
            consumo = float(consumo) if consumo else 1.0
            producao = float(producao) if producao else 1.0
            if mao_id in mao_de_obra:
                mao_de_obra[mao_id].consumo = consumo
                mao_de_obra[mao_id].producao = producao
            else:
                db.session.add(ReferenciaMaoDeObra(
                    referencia_id=id,
                    mao_de_obra_id=int(mao_id),
                    consumo=consumo,
                    producao=producao,
                    preco_unitario=MaoDeObra.query.get(int(mao_id)).diaria
                ))

        ### **🔹 Remover SOMENTE os itens que foram excluídos pelo usuário**
        ids_atualizados = set(solado_ids + alca_ids + componente_ids + custo_ids + mao_ids)

        for s in list(solados.values()):
            if str(s.solado_id) not in ids_atualizados:
                db.session.delete(s)
        for a in list(alcas.values()):
            if str(a.alca_id) not in ids_atualizados:
                db.session.delete(a)
        for c in list(componentes.values()):
            if str(c.componente_id) not in ids_atualizados:
                db.session.delete(c)
        for co in list(custos_operacionais.values()):
            if str(co.custo_id) not in ids_atualizados:
                db.session.delete(co)
        for m in list(mao_de_obra.values()):
            if str(m.mao_de_obra_id) not in ids_atualizados:
                db.session.delete(m)

        ### **🔹 Atualizar totais**
        referencia.calcular_totais()

        db.session.commit()
        flash("Referência atualizada com sucesso!", "success")
        return redirect(url_for('routes.listar_referencias'))

    return render_template(
        'editar_referencia.html',
        form=form,
        referencia=referencia,
        solados=solados.values(),
        alcas=alcas.values(),
        componentes=componentes.values(),
        custos_operacionais=custos_operacionais.values(),
        mao_de_obra=mao_de_obra.values(),
        solados_disponiveis=solados_disponiveis,
        alcas_disponiveis=alcas_disponiveis,
        componentes_disponiveis=componentes_disponiveis,
        custos_disponiveis=custos_disponiveis,
        mao_de_obra_disponiveis=mao_de_obra_disponiveis
    )




@bp.route('/referencia/excluir/<int:id>', methods=['POST'])
def excluir_referencia(id):
    """Exclui uma referência."""
    referencia = Referencia.query.get_or_404(id)
    
    # 🔹 Excluir os relacionamentos primeiro
    ReferenciaSolado.query.filter_by(referencia_id=referencia.id).delete()
    ReferenciaAlca.query.filter_by(referencia_id=referencia.id).delete()
    ReferenciaComponentes.query.filter_by(referencia_id=referencia.id).delete()
    ReferenciaCustoOperacional.query.filter_by(referencia_id=referencia.id).delete()
    ReferenciaMaoDeObra.query.filter_by(referencia_id=referencia.id).delete()

    # 🔹 Excluir a própria referência
    db.session.delete(referencia)
    db.session.commit()
    
    flash("Referência excluída com sucesso!", "success")
    return redirect(url_for('routes.listar_referencias'))





@bp.route('/colecoes')
def listar_colecoes():
    colecoes = Colecao.query.all()
    return render_template('colecoes.html', colecoes=colecoes)

@bp.route('/colecao/novo', methods=['GET', 'POST'])
def nova_colecao():
    form = ColecaoForm()
    if form.validate_on_submit():
        colecao = Colecao(
            codigo=form.codigo.data
        )
        db.session.add(colecao)
        db.session.commit()
        flash('Coleção adicionada com sucesso!', 'success')
        return redirect(url_for('routes.listar_colecoes'))
    return render_template('nova_colecao.html', form=form)

@bp.route('/colecao/editar/<int:id>', methods=['GET', 'POST'])
def editar_colecao(id):
    colecao = Colecao.query.get_or_404(id)
    form = ColecaoForm(obj=colecao)
    
    if form.validate_on_submit():
        colecao.codigo = form.codigo.data
        db.session.commit()
        flash('Coleção atualizada com sucesso!', 'success')
        return redirect(url_for('routes.listar_colecoes'))
    
    return render_template('editar_colecao.html', form=form, colecao=colecao)

@bp.route('/colecao/excluir/<int:id>', methods=['POST'])
def excluir_colecao(id):
    colecao = Colecao.query.get_or_404(id)
    db.session.delete(colecao)
    db.session.commit()
    flash('Coleção excluída com sucesso!', 'danger')
    return redirect(url_for('routes.listar_colecoes'))


        #COMPONENTES OK

@bp.route('/componentes', methods=['GET'])
def listar_componentes():
    filtro = request.args.get('filtro', '')
    if filtro:
        componentes = Componente.query.filter(Componente.descricao.ilike(f"{filtro}%")).all()
    else:
        componentes = Componente.query.all()
    return render_template('componentes.html', componentes=componentes)


@bp.route('/componente/novo', methods=['GET', 'POST'])
def novo_componente():
    form = ComponenteForm()
    if form.validate_on_submit():
        componente = Componente(
            codigo=form.codigo.data,
            tipo=form.tipo.data,
            descricao=form.descricao.data,
            unidade_medida=form.unidade_medida.data,
            preco=form.preco.data
        )
        db.session.add(componente)
        db.session.commit()
        flash('Componente adicionado com sucesso!', 'success')
        return redirect(url_for('routes.listar_componentes'))
    return render_template('novo_componente.html', form=form)

@bp.route('/componente/editar/<int:id>', methods=['GET', 'POST'])
def editar_componente(id):
    componente = Componente.query.get_or_404(id)
    form = ComponenteForm(obj=componente)
    
    if form.validate_on_submit():
        componente.codigo = form.codigo.data
        componente.tipo = form.tipo.data
        componente.descricao = form.descricao.data
        componente.unidade_medida = form.unidade_medida.data
        componente.preco = form.preco.data
        
        db.session.commit()
        flash('Componente atualizado com sucesso!', 'success')
        return redirect(url_for('routes.listar_componentes'))
    
    return render_template('editar_componente.html', form=form, componente=componente)


@bp.route('/componente/excluir/<int:id>', methods=['POST'])
@csrf.exempt  # 🔹 Desativa CSRF apenas para essa rota
def excluir_componente(id):
    componente = Componente.query.get_or_404(id)
    db.session.delete(componente)
    db.session.commit()
    flash('Componente excluído com sucesso!', 'danger')
    return redirect(url_for('routes.listar_componentes'))

#CUSTOS OPERACIONAIS ROTAS!
@bp.route('/custos')
def listar_custos():
    custos = CustoOperacional.query.all()
    return render_template('custos.html', custos=custos)

        #CUSTOS OPERACIONAIS OK
@bp.route('/custo/novo', methods=['GET', 'POST'])
def novo_custo():
    form = CustoOperacionalForm()
    if form.validate_on_submit():
        custo = CustoOperacional(
            codigo=form.codigo.data,
            descricao=form.descricao.data,
            tipo=form.tipo.data,
            unidade_medida=form.unidade_medida.data,
            preco=form.preco.data
        )
        db.session.add(custo)
        db.session.commit()
        flash('Custo operacional adicionado com sucesso!', 'success')
        return redirect(url_for('routes.listar_custos'))
    return render_template('novo_custo.html', form=form)

@bp.route('/custo/editar/<int:id>', methods=['GET', 'POST'])
def editar_custo(id):
    custo = CustoOperacional.query.get_or_404(id)
    form = CustoOperacionalForm(obj=custo)
    
    if form.validate_on_submit():
        custo.codigo = form.codigo.data
        custo.descricao = form.descricao.data
        custo.tipo = form.tipo.data
        custo.unidade_medida = form.unidade_medida.data
        custo.preco = form.preco.data
        
        db.session.commit()
        flash('Custo operacional atualizado com sucesso!', 'success')
        return redirect(url_for('routes.listar_custos'))
    
    return render_template('editar_custo.html', form=form, custo=custo)

@bp.route('/custo/excluir/<int:id>', methods=['POST'])
def excluir_custo(id):
    custo = CustoOperacional.query.get_or_404(id)
    db.session.delete(custo)
    db.session.commit()
    flash('Custo operacional excluído com sucesso!', 'danger')
    return redirect(url_for('routes.listar_custos'))

        #SALARIO!
@bp.route('/salarios')
def listar_salarios():
    salarios = Salario.query.all()
    return render_template('salarios.html', salarios=salarios)

@bp.route('/salario/novo', methods=['GET', 'POST'])
def novo_salario():
    form = SalarioForm()
    if form.validate_on_submit():
        salario = Salario(
            preco=form.preco.data,
            encargos=form.encargos.data
        )
        db.session.add(salario)
        db.session.commit()
        flash('Salário adicionado com sucesso!', 'success')
        return redirect(url_for('routes.listar_salarios'))
    return render_template('novo_salario.html', form=form)

@bp.route('/salario/editar/<int:id>', methods=['GET', 'POST'])
def editar_salario(id):
    salario = Salario.query.get_or_404(id)
    form = SalarioForm(obj=salario)

    if form.validate_on_submit():
        # Atualiza o salário no banco de dados
        salario.preco = form.preco.data
        salario.encargos = form.encargos.data
        db.session.commit()  # Salva a alteração do salário antes de recalcular

        # Atualiza todas as Mãos de Obra que utilizam esse salário
        mao_de_obra_relacionadas = MaoDeObra.query.filter_by(salario_id=salario.id).all()
        for mao in mao_de_obra_relacionadas:
            mao.preco_liquido = mao.multiplicador * salario.preco
            mao.preco_bruto = mao.preco_liquido * (1 + salario.encargos / 100)

            # Força a atualização no banco de dados
            db.session.add(mao)

        db.session.commit()  # Confirma todas as atualizações

        flash('Salário atualizado e valores da mão de obra recalculados automaticamente!', 'success')
        return redirect(url_for('routes.listar_salarios'))

    return render_template('editar_salario.html', form=form, salario=salario)

@bp.route('/salario/excluir/<int:id>', methods=['POST'])
def excluir_salario(id):
    salario = Salario.query.get_or_404(id)
    db.session.delete(salario)
    db.session.commit()
    flash('Salário excluído com sucesso!', 'danger')
    return redirect(url_for('routes.listar_salarios'))

@bp.route('/mao_de_obra')
def listar_mao_de_obra():
    mao_de_obra = MaoDeObra.query.all()
    return render_template('mao_de_obra.html', mao_de_obra=mao_de_obra)



from decimal import Decimal, ROUND_HALF_UP  # Importa Decimal para cálculos precisos

@bp.route('/mao_de_obra/nova', methods=['GET', 'POST'])
def nova_mao_de_obra():
    form = MaoDeObraForm()
    form.salario_id.choices = [(s.id, f"R$ {s.preco}") for s in Salario.query.all()]

    if form.validate_on_submit():
        salario = Salario.query.get(form.salario_id.data)

        # 🔹 Convertendo os valores para Decimal para cálculos precisos
        multiplicador = Decimal(str(form.multiplicador.data))
        preco_liquido = multiplicador * salario.preco  # ✅ Calcula o Preço Líquido

        # 🔹 Pegando o encargo da tabela Salario e garantindo que seja Decimal
        encargos = Decimal(str(salario.encargos)) if salario.encargos else Decimal(1)

        # 🔹 Ccálculo do Preço Bruto
        preco_bruto = preco_liquido * encargos

        # 🔹 Arredondando os valores para evitar casas decimais excessivas
        preco_liquido = preco_liquido.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        preco_bruto = preco_bruto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # 🔹 Criando o objeto MaoDeObra com os valores já convertidos corretamente
        mao_de_obra = MaoDeObra(
            descricao=form.descricao.data,
            salario_id=form.salario_id.data,
            multiplicador=multiplicador,  
            preco_liquido=preco_liquido,  
            preco_bruto=preco_bruto  
        )

        db.session.add(mao_de_obra)
        db.session.commit()
        flash('Mão de obra adicionada com sucesso!', 'success')
        return redirect(url_for('routes.listar_mao_de_obra'))
    
    return render_template('nova_mao_de_obra.html', form=form)


@bp.route('/mao_de_obra/editar/<int:id>', methods=['GET', 'POST'])
def editar_mao_de_obra(id):
    mao = MaoDeObra.query.get_or_404(id)
    form = MaoDeObraForm(obj=mao)

    # Atualizar opções de salário no formulário
    form.salario_id.choices = [(s.id, f"R$ {s.preco}") for s in Salario.query.all()]

    if form.validate_on_submit():
        mao.descricao = form.descricao.data
        mao.salario_id = form.salario_id.data
        mao.multiplicador = form.multiplicador.data

        salario = Salario.query.get(mao.salario_id)
        mao.preco_liquido = mao.multiplicador * salario.preco
        mao.preco_bruto = mao.preco_liquido * (1 + salario.encargos / 100)

        db.session.commit()
        flash('Mão de obra atualizada com sucesso!', 'success')
        return redirect(url_for('routes.listar_mao_de_obra'))

    return render_template('editar_mao_de_obra.html', form=form, mao=mao)

@bp.route('/mao_de_obra/excluir/<int:id>', methods=['POST'])
def excluir_mao_de_obra(id):
    mao = MaoDeObra.query.get_or_404(id)
    db.session.delete(mao)
    db.session.commit()
    flash('Mão de obra excluída com sucesso!', 'danger')
    return redirect(url_for('routes.listar_mao_de_obra'))


    #SOLADO

UPLOAD_FOLDER = 'app/static/uploads'


@bp.route('/solados', methods=['GET'])
def listar_solados():
    filtro = request.args.get('filtro', '')

    if filtro:
        solados = Solado.query.filter(Solado.referencia.ilike(f"{filtro}%")).all()
    else:
        solados = Solado.query.all()

    return render_template('solados.html', solados=solados)



@bp.route('/solado/ver/<int:id>')
def ver_solado(id):
    solado = Solado.query.get_or_404(id)

    # 🟢 Calcular totais da ficha técnica
    total_grade, peso_medio_total, peso_friso_total, peso_sem_friso_total = solado.calcular_totais()

    # 🟢 Calcular valores da formulação SEM friso
    if solado.formulacao:
        carga_total = solado.formulacao[0].carga_total
        pares_por_carga = solado.formulacao[0].pares_por_carga
        preco_total = solado.formulacao[0].preco_total
    else:
        carga_total = Decimal(0)
        pares_por_carga = Decimal(0)
        preco_total = Decimal(0)

    # 🟢 Calcular valores da formulação COM friso
    if solado.formulacao_friso:
        carga_total_friso = solado.formulacao_friso[0].carga_total
        pares_por_carga_friso = solado.formulacao_friso[0].pares_por_carga
        preco_total_friso = solado.formulacao_friso[0].preco_total  # ✅ Agora usa peso_friso_total
    else:
        carga_total_friso = Decimal(0)
        pares_por_carga_friso = Decimal(0)
        preco_total_friso = Decimal(0)
    
    custo_total = solado.custo_total  # Novo cálculo

    # 🔹 Logs para depuração
    print("\n===== DEPURAÇÃO =====")
    print(f"Total Grade: {total_grade}")
    print(f"Peso Médio Total: {peso_medio_total}")
    print(f"Peso Friso Total: {peso_friso_total}")
    print(f"Peso Sem Friso Total: {peso_sem_friso_total}")

    print(f"\nFormulação SEM Friso:")
    print(f"Carga Total: {carga_total}")
    print(f"Pares por Carga: {pares_por_carga}")
    print(f"Preço Total: R$ {preco_total}")

    print(f"\nFormulação COM Friso:")
    print(f"Carga Total Friso: {carga_total_friso}")
    print(f"Pares por Carga Friso: {pares_por_carga_friso}")
    print(f"Preço Total Friso: R$ {preco_total_friso}")
    print(f"Preço Custo total: R$ {custo_total}")
    print("=====================\n")

    return render_template('ver_solado.html', solado=solado,
                           total_grade=total_grade,
                           peso_medio_total=peso_medio_total,
                           peso_friso_total=peso_friso_total,
                           peso_sem_friso_total=peso_sem_friso_total,
                           carga_total=carga_total,
                           pares_por_carga=pares_por_carga,
                           preco_total=preco_total,
                           carga_total_friso=carga_total_friso,
                           pares_por_carga_friso=pares_por_carga_friso,
                           preco_total_friso=preco_total_friso, custo_total=custo_total)



@bp.route('/solado/novo', methods=['GET', 'POST'])
def novo_solado():
    form = SoladoForm()
    componentes = Componente.query.all()

    if form.validate_on_submit():
        print(request.form)  # <-- Adicionado para debug

        # Criar um novo objeto Solado
        novo_solado = Solado(
            referencia=form.referencia.data,
            descricao=form.descricao.data
        )

        # Salvar imagem
        if form.imagem.data:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_filename)
            form.imagem.data.save(caminho_imagem)
            novo_solado.imagem = imagem_filename

        db.session.add(novo_solado)
        db.session.flush()  # Garante que o ID do solado está disponível
        
                # Adiciona os tamanhos preenchidos
        for tamanho_data in form.tamanhos.data:
            if tamanho_data["nome"]:  # Apenas adiciona se houver um nome
                tamanho = Tamanho(
                    solado_id=novo_solado.id,
                    nome=tamanho_data["nome"],
                    quantidade=tamanho_data["quantidade"],
                    peso_medio=tamanho_data["peso_medio"],
                    peso_friso=tamanho_data["peso_friso"],
                    peso_sem_friso=tamanho_data["peso_sem_friso"]
                )
                db.session.add(tamanho)

        # 🔹 Debug: Verifica se os dados chegaram corretamente
        print("Componentes Sem Friso:", request.form.getlist("componentes_sem_friso[]"))
        print("Cargas Sem Friso:", request.form.getlist("carga_sem_friso[]"))
        print("Componentes Com Friso:", request.form.getlist("componentes_friso[]"))
        print("Cargas Com Friso:", request.form.getlist("carga_friso[]"))

        # Adiciona os componentes da formulação (Sem Friso)
        componentes_ids = request.form.getlist("componentes_sem_friso[]")
        cargas = request.form.getlist("carga_sem_friso[]")

        for componente_id, carga in zip(componentes_ids, cargas):
            componente = Componente.query.get(int(componente_id))
            carga_valor = float(carga) if carga else 0.0  # Preenchendo vazio com 0.0

            if componente:
                nova_formulacao = FormulacaoSolado(
                    solado_id=novo_solado.id,
                    componente_id=componente.id,
                    carga=carga_valor
                )
                db.session.add(nova_formulacao)

        # Adiciona os componentes da formulação (Com Friso)
        componentes_friso_ids = request.form.getlist("componentes_friso[]")
        cargas_friso = request.form.getlist("carga_friso[]")

        for componente_id, carga in zip(componentes_friso_ids, cargas_friso):
            componente = Componente.query.get(int(componente_id))
            carga_valor_friso = float(carga) if carga else 0.0  # Preenchendo vazio com 0.0

            if componente:
                nova_formulacao_friso = FormulacaoSoladoFriso(
                    solado_id=novo_solado.id,
                    componente_id=componente.id,
                    carga=carga_valor_friso
                )
                db.session.add(nova_formulacao_friso)

        db.session.commit()
        flash("Solado cadastrado com sucesso!", "success")
        return redirect(url_for('routes.listar_solados'))

    return render_template('novo_solado.html', form=form, componentes=componentes)


@bp.route('/solado/editar/<int:id>', methods=['GET', 'POST'])
def editar_solado(id):
    solado = Solado.query.get_or_404(id)  # Busca o solado no banco
    form = SoladoForm(obj=solado)  # Preenche o formulário com os dados existentes
    componentes = Componente.query.all()  # Para exibir os componentes no modal

    if form.validate_on_submit():
        # 🔹 Atualizar os dados do solado
        solado.descricao = form.descricao.data

        # 🔹 Atualizar imagem, se foi enviada uma nova
        if form.imagem.data:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_filename)
            form.imagem.data.save(caminho_imagem)
            solado.imagem = imagem_filename

        # 🔹 Atualizar tamanhos (remove os antigos e insere os novos)
        Tamanho.query.filter_by(solado_id=solado.id).delete()
        for tamanho_data in form.tamanhos.data:
            tamanho = Tamanho(
                solado_id=solado.id,
                nome=tamanho_data["nome"],
                quantidade=tamanho_data["quantidade"],
                peso_medio=tamanho_data["peso_medio"],
                peso_friso=tamanho_data["peso_friso"],
                peso_sem_friso=tamanho_data["peso_sem_friso"]
            )
            db.session.add(tamanho)

        # 🔹 Remover e atualizar formulação SEM friso
        FormulacaoSolado.query.filter_by(solado_id=solado.id).delete()
        componentes_ids = request.form.getlist("componentes_sem_friso[]")
        cargas = request.form.getlist("carga_sem_friso[]")

        for componente_id, carga in zip(componentes_ids, cargas):
            componente = Componente.query.get(int(componente_id))
            if componente:
                nova_formulacao = FormulacaoSolado(
                    solado_id=solado.id,
                    componente_id=componente.id,
                    carga=float(carga) if carga else 0
                )
                db.session.add(nova_formulacao)

        # 🔹 Remover e atualizar formulação COM friso
        FormulacaoSoladoFriso.query.filter_by(solado_id=solado.id).delete()
        componentes_friso_ids = request.form.getlist("componentes_friso[]")
        cargas_friso = request.form.getlist("carga_friso[]")

        for componente_id, carga in zip(componentes_friso_ids, cargas_friso):
            componente = Componente.query.get(int(componente_id))
            if componente:
                nova_formulacao_friso = FormulacaoSoladoFriso(
                    solado_id=solado.id,
                    componente_id=componente.id,
                    carga=float(carga) if carga else 0
                )
                db.session.add(nova_formulacao_friso)

        # 🔹 Commitando as alterações no banco
        db.session.commit()
        flash("Solado atualizado com sucesso!", "success")
        return redirect(url_for('routes.listar_solados'))

    return render_template('editar_solado.html', form=form, solado=solado, componentes=componentes)


@bp.route('/solado/excluir/<int:id>', methods=['POST'])
def excluir_solado(id):
    solado = Solado.query.get_or_404(id)

    # Apagar a imagem do solado, se existir
    if solado.imagem:
        caminho_imagem = os.path.join(UPLOAD_FOLDER, solado.imagem)
        if os.path.exists(caminho_imagem):
            os.remove(caminho_imagem)

    # Excluir todos os tamanhos associados ao solado
    Tamanho.query.filter_by(solado_id=id).delete()

    # Excluir o solado
    db.session.delete(solado)
    db.session.commit()
    
    flash('Solado excluído com sucesso!', 'danger')
    return redirect(url_for('routes.listar_solados'))

    #ALCA

#@bp.route('/alcas', methods=['GET'])
#def listar_alcas():
#    filtro = request.args.get('filtro', '')
#    if filtro:
#        alcas = Alca.query.filter(Alca.referencia.startswith(filtro)).all()
#   else:
#       alcas = Alca.query.all()
#   
#   return render_template('alcas.html', alcas=alcas)

@bp.route('/alcas', methods=['GET'])
def listar_alcas():
    filtro = request.args.get('filtro', '')

    if filtro:
        alcas = Alca.query.filter(Alca.referencia.ilike(f"{filtro}%")).all()
    else:
        alcas = Alca.query.all()

    return render_template('alcas.html', alcas=alcas)


@bp.route('/alca/nova', methods=['GET', 'POST'])
def nova_alca():
    form = AlcaForm()
    componentes = Componente.query.all()

    if form.validate_on_submit():
        nova_alca = Alca(
            referencia=form.referencia.data,
            descricao=form.descricao.data
        )

        # Salvar imagem, se for enviada
        if form.imagem.data:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_filename)
            form.imagem.data.save(caminho_imagem)
            nova_alca.imagem = imagem_filename

        db.session.add(nova_alca)
        db.session.flush()  # Garante que o ID da alça está disponível

        # Adiciona os tamanhos e pesos preenchidos
        for tamanho_data in form.tamanhos.data:
            nome = tamanho_data["nome"] if tamanho_data["nome"] else "--"
            quantidade = (tamanho_data["quantidade"]) if tamanho_data["quantidade"] else 0
            peso_medio = (tamanho_data["peso_medio"]) if tamanho_data["peso_medio"] else 0.0

            tamanho = TamanhoAlca(
                alca_id=nova_alca.id,
                nome=nome,
                quantidade=quantidade,
                peso_medio=peso_medio
            )
            db.session.add(tamanho)

        # Adiciona os componentes da formulação
        componentes_ids = request.form.getlist("componentes[]")
        cargas = request.form.getlist("carga[]")

        for componente_id, carga in zip(componentes_ids, cargas):
            componente = Componente.query.get(int(componente_id))
            carga_valor = float(carga) if carga else 0.0  # Se vier vazio, preenche com 0.0

            if componente:
                nova_formulacao = FormulacaoAlca(
                    alca_id=nova_alca.id,
                    componente_id=componente.id,
                    carga=carga_valor
                )
                db.session.add(nova_formulacao)

        db.session.commit()
        flash("Alça cadastrada com sucesso!", "success")
        return redirect(url_for('routes.listar_alcas'))

    return render_template('nova_alca.html', form=form, componentes=componentes)

@bp.route('/alca/editar/<int:id>', methods=['GET', 'POST'])
def editar_alca(id):
    alca = Alca.query.get_or_404(id)
    form = AlcaForm(obj=alca)
    componentes = Componente.query.all()  # Para exibir os componentes no modal

    if form.validate_on_submit():
        # Atualizar dados da alça
        alca.descricao = form.descricao.data

        # Atualizar imagem, se foi enviada uma nova
        if form.imagem.data:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_filename)
            form.imagem.data.save(caminho_imagem)
            alca.imagem = imagem_filename

        # Atualizar tamanhos (remover os antigos e adicionar os novos)
        alca.tamanhos.clear()
        for tamanho_data in form.tamanhos.data:
            nome = tamanho_data["nome"] if tamanho_data["nome"] else "--"
            quantidade = (tamanho_data["quantidade"]) if tamanho_data["quantidade"] else 0
            peso_medio = (tamanho_data["peso_medio"]) if tamanho_data["peso_medio"] else 0.0

            tamanho = TamanhoAlca(
                alca_id=alca.id,
                nome=nome,
                quantidade=quantidade,
                peso_medio=peso_medio
            )
            alca.tamanhos.append(tamanho)

        # Atualizar formulação (remover os antigos e adicionar os novos)
        alca.formulacao.clear()
        componentes_ids = request.form.getlist("componentes[]")
        cargas = request.form.getlist("carga[]")

        for componente_id, carga in zip(componentes_ids, cargas):
            componente = Componente.query.get(int(componente_id))
            carga_valor = float(carga) if carga else 0.0  # Se vier vazio, preenche com 0.0

            if componente:
                nova_formulacao = FormulacaoAlca(
                    alca_id=alca.id,
                    componente_id=componente.id,
                    carga=carga_valor
                )
                alca.formulacao.append(nova_formulacao)

        db.session.commit()
        flash("Alça atualizada com sucesso!", "success")
        return redirect(url_for('routes.listar_alcas'))

    return render_template('editar_alca.html', form=form, alca=alca, componentes=componentes)

@bp.route('/alca/ver/<int:id>', methods=['GET'])
def ver_alca(id):
    alca = Alca.query.get_or_404(id)

    # 🟢 Calcular totais da ficha técnica
    total_grade, peso_medio_total = alca.calcular_totais()
    
        # 🟢 Calcular valores da formulação SEM friso
    if alca.formulacao:
        carga_total = alca.formulacao[0].carga_total
        pares_por_carga = alca.formulacao[0].pares_por_carga
        preco_total = alca.formulacao[0].preco_total
    else:
        carga_total = Decimal(0)
        pares_por_carga = Decimal(0)
        preco_total = Decimal(0)


    return render_template(
        'ver_alca.html', 
        alca=alca, 
        total_grade=total_grade, 
        peso_medio_total=peso_medio_total, 
        pares_por_carga=pares_por_carga, 
        preco_total=preco_total, carga_total=carga_total
    )



@bp.route('/alca/excluir/<int:id>', methods=['POST'])
def excluir_alca(id):
    alca = Alca.query.get_or_404(id)

    try:
        # Remover todas as referências antes de excluir
        FormulacaoAlca.query.filter_by(alca_id=id).delete()
        TamanhoAlca.query.filter_by(alca_id=id).delete()

        db.session.delete(alca)
        db.session.commit()
        flash("Alça excluída com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir a alça: {str(e)}", "danger")

    return redirect(url_for('routes.listar_alcas'))


