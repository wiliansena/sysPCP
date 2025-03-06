from sqlite3 import IntegrityError
from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import FormulacaoSolado, FormulacaoSoladoFriso, LogAcao, Referencia, Componente, CustoOperacional, ReferenciaAlca, ReferenciaComponentes, ReferenciaCustoOperacional, ReferenciaEmbalagem1, ReferenciaEmbalagem2, ReferenciaEmbalagem3, ReferenciaMaoDeObra, ReferenciaSolado, Salario, MaoDeObra, Margem
from app.forms import MargemForm, ReferenciaForm, ComponenteForm, CustoOperacionalForm, SalarioForm, MaoDeObraForm
import os
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

@bp.route('/logs')
@login_required
def listar_logs():
    logs = LogAcao.query.order_by(LogAcao.data_hora.desc()).all()
    return render_template('logs.html', logs=logs)


@bp.route('/')
@login_required
def home():
    return render_template('home.html')

    #REFERENCIAS


@bp.route('/referencias', methods=['GET'])
@login_required
def listar_referencias():
    filtro = request.args.get('filtro', '')
    if filtro:
        referencias = Referencia.query.filter(Referencia.codigo_referencia.ilike(f"%{filtro}%")).all()
    else:
        referencias = Referencia.query.order_by(Referencia.id.desc()).all()
    return render_template('referencias.html', referencias=referencias)



# 🔹 Função para converter valores para float de forma segura
def parse_float(value, default=0):
    try:
        return float(value.strip()) if value.strip() else default
    except (ValueError, AttributeError):
        return default



@bp.route('/referencia/novo', methods=['GET', 'POST'])
@login_required
def nova_referencia():
    form = ReferenciaForm()

    # Recupera os dados para os modais
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
        )

        # Salvar imagem se houver
        if form.imagem.data:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_filename)
            form.imagem.data.save(caminho_imagem)
            referencia.imagem = imagem_filename

        db.session.add(referencia)
        db.session.flush()  # Garante que referencia.id esteja definido

        # Associa os Solados
        for solado_id, consumo in zip(
                request.form.getlist("solado_id[]"),
                request.form.getlist("solado_consumo[]")
        ):
            db.session.add(ReferenciaSolado(
                referencia_id=referencia.id,
                solado_id=int(solado_id),
                consumo=consumo if consumo else 0,
                preco_unitario=Solado.query.get(int(solado_id)).custo_total
            ))

        # Associa as Alças
        for alca_id, consumo in zip(
                request.form.getlist("alca_id[]"),
                request.form.getlist("alca_consumo[]")
        ):
            db.session.add(ReferenciaAlca(
                referencia_id=referencia.id,
                alca_id=int(alca_id),
                consumo=consumo if consumo else 0,
                preco_unitario=Alca.query.get(int(alca_id)).preco_total
            ))

        # Associa os Componentes
        for componente_id, consumo in zip(
                request.form.getlist("componente_id[]"),
                request.form.getlist("componente_consumo[]")
        ):
            db.session.add(ReferenciaComponentes(
                referencia_id=referencia.id,
                componente_id=int(componente_id),
                consumo=consumo if consumo else 0,
                preco_unitario=Componente.query.get(int(componente_id)).preco
            ))

        # 🔹 Associa os Componentes das Embalagens 1, 2 e 3
        for componente_id, consumo in zip(
                request.form.getlist("componentes_embalagem1[]"),
                request.form.getlist("consumo_embalagem1[]")
        ):
            db.session.add(ReferenciaEmbalagem1(
                referencia_id=referencia.id,
                componente_id=int(componente_id),
                consumo=consumo if consumo else 0,
                preco_unitario=Componente.query.get(int(componente_id)).preco
            ))

        for componente_id, consumo in zip(
                request.form.getlist("componentes_embalagem2[]"),
                request.form.getlist("consumo_embalagem2[]")
        ):
            db.session.add(ReferenciaEmbalagem2(
                referencia_id=referencia.id,
                componente_id=int(componente_id),
                consumo=consumo if consumo else 0,
                preco_unitario=Componente.query.get(int(componente_id)).preco
            ))

        for componente_id, consumo in zip(
                request.form.getlist("componentes_embalagem3[]"),
                request.form.getlist("consumo_embalagem3[]")
        ):
            db.session.add(ReferenciaEmbalagem3(
                referencia_id=referencia.id,
                componente_id=int(componente_id),
                consumo=consumo if consumo else 0,
                preco_unitario=Componente.query.get(int(componente_id)).preco
            ))

        # Associa os Custos Operacionais
        for custo_id, consumo in zip(
                request.form.getlist("custo_id[]"),
                request.form.getlist("custo_consumo[]")
        ):
            db.session.add(ReferenciaCustoOperacional(
                referencia_id=referencia.id,
                custo_id=int(custo_id),
                consumo=consumo if consumo else 0,
                preco_unitario=CustoOperacional.query.get(int(custo_id)).preco
            ))

        # Associa a Mão de Obra
        for mao_obra_id, consumo, producao in zip(
                request.form.getlist("mao_obra_id[]"),
                request.form.getlist("mao_obra_consumo[]"),
                request.form.getlist("mao_obra_producao[]")
        ):
            db.session.add(ReferenciaMaoDeObra(
                referencia_id=referencia.id,
                mao_de_obra_id=int(mao_obra_id),
                consumo=consumo if consumo else 0,
                producao=producao if producao else 1,
                preco_unitario=MaoDeObra.query.get(int(mao_obra_id)).diaria
            ))

        # 🔹 Agora, calcula os custos individuais de cada embalagem
        referencia.calcular_totais()

        # 🔹 Adiciona novamente a referência à sessão antes de confirmar a transação
        db.session.add(referencia)

        # 🔹 Confirma as alterações no banco
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
@login_required
def ver_referencia(id):
    referencia = Referencia.query.get_or_404(id)
    
    # 🔹 Certifique-se de calcular os totais antes de exibir a referência
    referencia.calcular_totais()

    # Recuperando os itens associados
    solados = ReferenciaSolado.query.filter_by(referencia_id=referencia.id).all()
    alcas = ReferenciaAlca.query.filter_by(referencia_id=referencia.id).all()
    componentes = ReferenciaComponentes.query.filter_by(referencia_id=referencia.id).all()
    embalagem1 = ReferenciaEmbalagem1.query.filter_by(referencia_id=referencia.id).all()
    embalagem2 = ReferenciaEmbalagem2.query.filter_by(referencia_id=referencia.id).all()
    embalagem3 = ReferenciaEmbalagem3.query.filter_by(referencia_id=referencia.id).all()
    custos_operacionais = ReferenciaCustoOperacional.query.filter_by(referencia_id=referencia.id).all()
    mao_de_obra = ReferenciaMaoDeObra.query.filter_by(referencia_id=referencia.id).all()

    return render_template(
        'ver_referencia.html',
        referencia=referencia,
        solados=solados,
        alcas=alcas,
        componentes=componentes,
        embalagem1=embalagem1,
        embalagem2=embalagem2,
        embalagem3=embalagem3,
        custos_operacionais=custos_operacionais,
        mao_de_obra=mao_de_obra
    )


from flask import render_template, request, redirect, url_for, flash
from app import db
from app.models import Referencia, ReferenciaSolado, ReferenciaAlca, ReferenciaComponentes, ReferenciaCustoOperacional, ReferenciaMaoDeObra, Solado, Alca, Componente, CustoOperacional, MaoDeObra
from app.forms import ReferenciaForm
import os
from werkzeug.utils import secure_filename


@bp.route('/referencia/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_referencia(id):
    """Edita uma referência existente permitindo adicionar, atualizar ou remover itens."""
    referencia = Referencia.query.get_or_404(id)
    form = ReferenciaForm(obj=referencia)

    # Recupera os itens já associados à referência
    solados = ReferenciaSolado.query.filter_by(referencia_id=id).all()
    alcas = ReferenciaAlca.query.filter_by(referencia_id=id).all()
    componentes = ReferenciaComponentes.query.filter_by(referencia_id=id).all()
    embalagem1 = ReferenciaEmbalagem1.query.filter_by(referencia_id=id).all()
    embalagem2 = ReferenciaEmbalagem2.query.filter_by(referencia_id=id).all()
    embalagem3 = ReferenciaEmbalagem3.query.filter_by(referencia_id=id).all()
    custos_operacionais = ReferenciaCustoOperacional.query.filter_by(referencia_id=id).all()
    mao_de_obra = ReferenciaMaoDeObra.query.filter_by(referencia_id=id).all()

    if form.validate_on_submit():
        referencia.codigo_referencia = form.codigo_referencia.data
        referencia.descricao = form.descricao.data
        referencia.linha = form.linha.data

        # Atualiza a imagem se enviada
        if form.imagem.data:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_filename)
            form.imagem.data.save(caminho_imagem)
            referencia.imagem = imagem_filename

        # 🔹 Remover todos os itens antigos antes de adicionar os novos
        def remover_itens(modelo):
            db.session.query(modelo).filter_by(referencia_id=id).delete()

        remover_itens(ReferenciaSolado)
        remover_itens(ReferenciaAlca)
        remover_itens(ReferenciaComponentes)
        remover_itens(ReferenciaCustoOperacional)
        remover_itens(ReferenciaMaoDeObra)
        remover_itens(ReferenciaEmbalagem1)
        remover_itens(ReferenciaEmbalagem2)
        remover_itens(ReferenciaEmbalagem3)

        # 🔹 Confirma a remoção para evitar erro de referências
        db.session.commit()

        # 🔹 Função para adicionar novos itens
        def adicionar_itens(modelo, nome_form, chave_id, chave_preco):
            ids_post = request.form.getlist(f"{nome_form}_id[]")
            consumos_post = request.form.getlist(f"{nome_form}_consumo[]")

            for item_id, consumo in zip(ids_post, consumos_post):
                consumo_decimal = Decimal(consumo) if consumo else Decimal(0)
                preco_unitario = Decimal(0)

                if modelo == ReferenciaCustoOperacional:
                    item_banco = CustoOperacional.query.get(int(item_id))
                else:
                    item_banco = modelo.query.get(int(item_id))

                if item_banco:
                    preco_unitario = getattr(item_banco, chave_preco, Decimal(0))

                db.session.add(modelo(
                    referencia_id=id,
                    **{chave_id: int(item_id)},
                    consumo=consumo_decimal,
                    preco_unitario=preco_unitario
                ))

        adicionar_itens(ReferenciaSolado, "solado", "solado_id", "custo_total")
        adicionar_itens(ReferenciaAlca, "alca", "alca_id", "preco_total")
        adicionar_itens(ReferenciaComponentes, "componente", "componente_id", "preco")
        adicionar_itens(ReferenciaCustoOperacional, "custo", "custo_id", "preco")

        # 🔹 Adicionar mão de obra corretamente
        mao_ids_post = request.form.getlist("mao_obra_id[]")
        mao_consumos = request.form.getlist("mao_obra_consumo[]")
        mao_producoes = request.form.getlist("mao_obra_producao[]")

        for mao_id, consumo, producao in zip(mao_ids_post, mao_consumos, mao_producoes):
            consumo_decimal = Decimal(consumo) if consumo else Decimal(0)
            producao_decimal = Decimal(producao) if producao else Decimal(1)

            db.session.add(ReferenciaMaoDeObra(
                referencia_id=id,
                mao_de_obra_id=int(mao_id),
                consumo=consumo_decimal,
                producao=producao_decimal,
                preco_unitario=MaoDeObra.query.get(int(mao_id)).diaria
            ))

        # 🔹 Adiciona os itens das embalagens

        # 🔹 Função para adicionar os itens das embalagens corretamente
        def adicionar_embalagem(modelo, nome_form):
            ids_post = request.form.getlist(f"{nome_form}_id[]")
            consumos_post = request.form.getlist(f"{nome_form}_consumo[]")

            for item_id, consumo in zip(ids_post, consumos_post):
                consumo_decimal = Decimal(consumo) if consumo else Decimal(0)

                # 🔹 Buscar o preço correto do componente no banco
                componente = Componente.query.get(int(item_id))
                preco_unitario = componente.preco if componente else Decimal(0)

                novo_item = modelo(
                    referencia_id=id,
                    componente_id=int(item_id),
                    consumo=consumo_decimal,
                    preco_unitario=preco_unitario  # 🔹 Agora salva o preço correto
                )
                db.session.add(novo_item)

        # 🔹 Agora chamamos a função corrigida para adicionar os itens das embalagens
        adicionar_embalagem(ReferenciaEmbalagem1, "embalagem1")
        adicionar_embalagem(ReferenciaEmbalagem2, "embalagem2")
        adicionar_embalagem(ReferenciaEmbalagem3, "embalagem3")

        # 🔹 Recalcular os totais
        referencia.calcular_totais()

        # 🔹 Adiciona novamente a referência para garantir que os valores calculados sejam salvos
        db.session.add(referencia)

        try:
            db.session.commit()

            # 🔹 Salva o log
            log = LogAcao(
                usuario_id=current_user.id,
                usuario_nome=current_user.nome,
                acao=f"Editou a Referência: {referencia.codigo_referencia}"
            )
            db.session.add(log)

            flash("Referência atualizada com sucesso!", "success")
            return redirect(url_for('routes.listar_referencias'))
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar no banco: {e}")
            flash("Erro ao salvar as alterações. Verifique os logs.", "danger")

    # 🔹 Agora renderiza a página com todas as informações corretamente
    return render_template(
        'editar_referencia.html',
        form=form,
        referencia=referencia,
        solados=solados,
        alcas=alcas,
        componentes=componentes,
        embalagem1=embalagem1,
        embalagem2=embalagem2,
        embalagem3=embalagem3,
        custos_operacionais=custos_operacionais,
        mao_de_obra=mao_de_obra,
        # 🔹 Passando os itens disponíveis para o modal
        solados_disponiveis=Solado.query.all(),
        alcas_disponiveis=Alca.query.all(),
        componentes_disponiveis=Componente.query.all(),
        custos_disponiveis=CustoOperacional.query.all(),
        mao_de_obra_disponiveis=MaoDeObra.query.all()
    )



import random, string

import random, string

@bp.route('/referencia/copiar/<int:id>', methods=['GET'])
@login_required
def copiar_referencia(id):
    # Recupera a referência original ou retorna 404 se não existir
    referencia = Referencia.query.get_or_404(id)
    
    # Obter prefixo do código original, limitado a 7 caracteres
    prefix = referencia.codigo_referencia[:7]
    
    # Gerar uma string aleatória de 6 caracteres (letras maiúsculas e dígitos)
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Montar o código temporário no formato: "ORIG-COPIA-RANDOM"
    codigo_temporario = f"{prefix}-COPIA-{random_string}"
    
    # Cria a nova referência usando o código temporário
    nova_referencia = Referencia(
        codigo_referencia=codigo_temporario,
        descricao=referencia.descricao,
        linha=referencia.linha,
        imagem=referencia.imagem
    )
    db.session.add(nova_referencia)
    db.session.flush()  # Garante que nova_referencia.id seja definido antes de criar as relações

    # 🔹 Copia os Solados
    for solado in referencia.solados:
        nova_solado = ReferenciaSolado(
            referencia_id=nova_referencia.id,
            solado_id=solado.solado_id,
            consumo=solado.consumo,
            preco_unitario=solado.preco_unitario
        )
        db.session.add(nova_solado)

    # 🔹 Copia as Alças
    for alca in referencia.alcas:
        nova_alca = ReferenciaAlca(
            referencia_id=nova_referencia.id,
            alca_id=alca.alca_id,
            consumo=alca.consumo,
            preco_unitario=alca.preco_unitario
        )
        db.session.add(nova_alca)

    # 🔹 Copia os Componentes
    for comp in referencia.componentes:
        novo_componente = ReferenciaComponentes(
            referencia_id=nova_referencia.id,
            componente_id=comp.componente_id,
            consumo=comp.consumo,
            preco_unitario=comp.preco_unitario
        )
        db.session.add(novo_componente)

    # 🔹 Copia os Custos Operacionais
    for custo in referencia.custos_operacionais:
        novo_custo = ReferenciaCustoOperacional(
            referencia_id=nova_referencia.id,
            custo_id=custo.custo_id,
            consumo=custo.consumo,
            preco_unitario=custo.preco_unitario
        )
        db.session.add(novo_custo)

    # 🔹 Copia a Mão de Obra
    for mao in referencia.mao_de_obra:
        nova_mao = ReferenciaMaoDeObra(
            referencia_id=nova_referencia.id,
            mao_de_obra_id=mao.mao_de_obra_id,
            consumo=mao.consumo,
            producao=mao.producao,
            preco_unitario=mao.preco_unitario
        )
        db.session.add(nova_mao)

    # 🔹 Copia a Embalagem 1
    for embalagem in referencia.embalagem1:
        nova_embalagem = ReferenciaEmbalagem1(
            referencia_id=nova_referencia.id,
            componente_id=embalagem.componente_id,
            consumo=embalagem.consumo,
            preco_unitario=embalagem.preco_unitario
        )
        db.session.add(nova_embalagem)

    # 🔹 Copia a Embalagem 2
    for embalagem in referencia.embalagem2:
        nova_embalagem = ReferenciaEmbalagem2(
            referencia_id=nova_referencia.id,
            componente_id=embalagem.componente_id,
            consumo=embalagem.consumo,
            preco_unitario=embalagem.preco_unitario
        )
        db.session.add(nova_embalagem)

    # 🔹 Copia a Embalagem 3
    for embalagem in referencia.embalagem3:
        nova_embalagem = ReferenciaEmbalagem3(
            referencia_id=nova_referencia.id,
            componente_id=embalagem.componente_id,
            consumo=embalagem.consumo,
            preco_unitario=embalagem.preco_unitario
        )
        db.session.add(nova_embalagem)

    # 🔹 Confirma a cópia e redireciona para edição
    db.session.commit()
    flash("Referência copiada com sucesso! Lembre-se de atualizar o código e ajustar os itens conforme necessário.", "success")
    return redirect(url_for('routes.editar_referencia', id=nova_referencia.id))



from flask import request, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError

@bp.route('/referencia/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_referencia(id):
    """Exclui uma referência, mas exige que o usuário digite 'excluir' para confirmar."""

    referencia = Referencia.query.get_or_404(id)

    # 🔹 Verifica se o usuário digitou "excluir" corretamente
    confirmacao = request.form.get("confirmacao", "").strip().lower()

    if confirmacao != "excluir":
        flash("Erro: Você deve digitar 'excluir' para confirmar a exclusão da referência.", "danger")
        return redirect(url_for('routes.listar_referencias'))

    try:
        # 🔹 Excluir os relacionamentos primeiro
        ReferenciaSolado.query.filter_by(referencia_id=referencia.id).delete()
        ReferenciaAlca.query.filter_by(referencia_id=referencia.id).delete()
        ReferenciaComponentes.query.filter_by(referencia_id=referencia.id).delete()
        ReferenciaCustoOperacional.query.filter_by(referencia_id=referencia.id).delete()
        ReferenciaMaoDeObra.query.filter_by(referencia_id=referencia.id).delete()
        
                # 🔹 Salva o log antes de excluir
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Excluiu a Referência: {referencia.codigo_referencia}"
        )
        db.session.add(log)

        # 🔹 Excluir a própria referência
        db.session.delete(referencia)
        db.session.commit()

        flash("Referência excluída com sucesso!", "success")

    except IntegrityError:
        db.session.rollback()
        flash("Erro: Não foi possível excluir esta referência pois está vinculada a outros registros.", "danger")

    return redirect(url_for('routes.listar_referencias'))





@bp.route('/colecoes')
@login_required
def listar_colecoes():
    colecoes = Colecao.query.order_by(Colecao.id.desc()).all()
    return render_template('colecoes.html', colecoes=colecoes)

@bp.route('/colecao/novo', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
def excluir_colecao(id):
    colecao = Colecao.query.get_or_404(id)
    db.session.delete(colecao)
    db.session.commit()
    flash('Coleção excluída com sucesso!', 'danger')
    return redirect(url_for('routes.listar_colecoes'))


        #COMPONENTES OK


@bp.route('/componentes', methods=['GET'])
@login_required
def listar_componentes():
    filtro = request.args.get('filtro', '')
    componentes = []  # Inicialmente, a lista estará vazia

    if filtro == "TODOS":
        componentes = Componente.query.all()
    elif filtro:
        componentes = Componente.query.filter(Componente.descricao.ilike(f"%{filtro}%")).all()

    return render_template('componentes.html', componentes=componentes)



@bp.route('/componente/novo', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
@csrf.exempt  # 🔹 Desativa CSRF apenas para essa rota
def excluir_componente(id):
    componente = Componente.query.get_or_404(id)

    try:
        db.session.delete(componente)
        db.session.commit()
        flash('Componente excluído com sucesso!', 'success')

    except IntegrityError:
        db.session.rollback()

        # 🔹 Mensagem genérica sem listar onde o componente é usado
        flash("Erro: Este componente não pode ser excluído porque está sendo utilizado em outras tabelas do sistema.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir o componente: {str(e)}", "danger")

    return redirect(url_for('routes.listar_componentes'))

#CUSTOS OPERACIONAIS ROTAS!
@bp.route('/custos')
@login_required
def listar_custos():
    custos = CustoOperacional.query.order_by(CustoOperacional.id.desc()).all()
    return render_template('custos.html', custos=custos)

        #CUSTOS OPERACIONAIS OK
@bp.route('/custo/novo', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
def excluir_custo(id):
    custo = CustoOperacional.query.get_or_404(id)

    try:
        db.session.delete(custo)
        db.session.commit()
        flash('Custo operacional excluído com sucesso!', 'success')

    except IntegrityError:
        db.session.rollback()
        
        # 🔹 Mensagem genérica sem listar onde o custo está sendo usado
        flash("Erro: Este custo operacional não pode ser excluído porque está sendo utilizado em outras tabelas do sistema.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir o custo operacional: {str(e)}", "danger")

    return redirect(url_for('routes.listar_custos'))

        #SALARIO!
@bp.route('/salarios')
@login_required
def listar_salarios():
    salarios = Salario.query.order_by(Salario.id.desc()).all()
    return render_template('salarios.html', salarios=salarios)

@bp.route('/salario/novo', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
def excluir_salario(id):
    salario = Salario.query.get_or_404(id)

    try:
        db.session.delete(salario)
        db.session.commit()
        flash('Salário excluído com sucesso!', 'success')

    except IntegrityError:
        db.session.rollback()

        # 🔹 Mensagem específica indicando a tabela "Mão de Obra"
        flash("Erro: Este salário não pode ser excluído porque está sendo utilizado na tabela 'Mão de Obra'.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir o salário: {str(e)}", "danger")

    return redirect(url_for('routes.listar_salarios'))

@bp.route('/mao_de_obra')
@login_required
def listar_mao_de_obra():
    mao_de_obra = MaoDeObra.query.order_by(MaoDeObra.id.desc()).all()
    return render_template('mao_de_obra.html', mao_de_obra=mao_de_obra)



from decimal import Decimal, ROUND_HALF_UP  # Importa Decimal para cálculos precisos

@bp.route('/mao_de_obra/nova', methods=['GET', 'POST'])
@login_required
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
@login_required
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
        mao.preco_liquido = Decimal(mao.multiplicador) * Decimal(salario.preco)
        mao.preco_bruto = Decimal(mao.preco_liquido) * Decimal((1 + salario.encargos / 100))

        db.session.commit()
        flash('Mão de obra atualizada com sucesso!', 'success')
        return redirect(url_for('routes.listar_mao_de_obra'))

    return render_template('editar_mao_de_obra.html', form=form, mao=mao)

@bp.route('/mao_de_obra/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_mao_de_obra(id):
    mao = MaoDeObra.query.get_or_404(id)

    try:
        db.session.delete(mao)
        db.session.commit()
        flash('Mão de obra excluída com sucesso!', 'success')

    except IntegrityError:
        db.session.rollback()

        # 🔹 Mensagem genérica sem listar onde a mão de obra está sendo usada
        flash("Erro: Esta mão de obra não pode ser excluída porque está sendo utilizada em referências!", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir a mão de obra: {str(e)}", "danger")

    return redirect(url_for('routes.listar_mao_de_obra'))


    #SOLADO

UPLOAD_FOLDER = 'app/static/uploads'


@bp.route('/solados', methods=['GET'])
@login_required
def listar_solados():
    filtro = request.args.get('filtro', '')

    if filtro:
        solados = Solado.query.filter(Solado.referencia.ilike(f"%{filtro}%")).all()
    else:
        solados = Solado.query.order_by(Solado.id.desc()).all()

    return render_template('solados.html', solados=solados)



@bp.route('/solado/ver/<int:id>')
@login_required
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
@login_required
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
@login_required
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
        
        # 🔹 Salva o log
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou o Solado: {solado.referencia}"
        )
        db.session.add(log)
        
        flash("Solado atualizado com sucesso!", "success")
        return redirect(url_for('routes.listar_solados'))

    return render_template('editar_solado.html', form=form, solado=solado, componentes=componentes)

import random, string
from flask import redirect, url_for, flash
from werkzeug.utils import secure_filename

@bp.route('/solado/copiar/<int:id>', methods=['GET'])
@login_required
def copiar_solado(id):
    # Recupera o solado original ou retorna 404 se não existir
    solado = Solado.query.get_or_404(id)
    
    # Gera o código temporário baseado no campo "referencia"
    # Usa os primeiros 7 caracteres do código original ou "SOLADO" se estiver vazio
    prefix = solado.referencia[:7] if solado.referencia else "SOLADO"
    random_string = ''.join(random.choices(string.ascii_lowercase, k=6))
    codigo_temporario = f"{prefix}-cópia-{random_string}"
    
    # Cria a nova instância de Solado com o código temporário e os demais dados copiados
    nova_solado = Solado(
        referencia=codigo_temporario,
        descricao=solado.descricao,
        imagem=solado.imagem
    )
    db.session.add(nova_solado)
    db.session.flush()  # Garante que nova_solado.id esteja definido para os relacionamentos

    # Copia os Tamanhos (consulta Tamanho onde solado_id == solado.id)
    tamanhos = Tamanho.query.filter_by(solado_id=solado.id).all()
    for tamanho in tamanhos:
        novo_tamanho = Tamanho(
            solado_id=nova_solado.id,
            nome=tamanho.nome,
            quantidade=tamanho.quantidade,
            peso_medio=tamanho.peso_medio,
            peso_friso=tamanho.peso_friso,
            peso_sem_friso=tamanho.peso_sem_friso
        )
        db.session.add(novo_tamanho)

    # Copia a formulação SEM friso (consulta FormulacaoSolado onde solado_id == solado.id)
    formulacoes_sem_friso = FormulacaoSolado.query.filter_by(solado_id=solado.id).all()
    for formulacao in formulacoes_sem_friso:
        nova_formulacao = FormulacaoSolado(
            solado_id=nova_solado.id,
            componente_id=formulacao.componente_id,
            carga=formulacao.carga
        )
        db.session.add(nova_formulacao)

    # Copia a formulação COM friso (consulta FormulacaoSoladoFriso onde solado_id == solado.id)
    formulacoes_com_friso = FormulacaoSoladoFriso.query.filter_by(solado_id=solado.id).all()
    for formulacao_friso in formulacoes_com_friso:
        nova_formulacao_friso = FormulacaoSoladoFriso(
            solado_id=nova_solado.id,
            componente_id=formulacao_friso.componente_id,
            carga=formulacao_friso.carga
        )
        db.session.add(nova_formulacao_friso)

    db.session.commit()
    flash("Solado copiado com sucesso! Atualize o código e os demais dados conforme necessário.", "success")
    return redirect(url_for('routes.editar_solado', id=nova_solado.id))



@bp.route('/solado/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_solado(id):
    solado = Solado.query.get_or_404(id)

    try:
        # Remover todas as referências antes de excluir
        Tamanho.query.filter_by(solado_id=id).delete()
        
                        # 🔹 Salva o log antes de excluir
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Excluiu o Solado: {solado.referencia}"
        )
        db.session.add(log)

        db.session.delete(solado)
        db.session.commit()
        flash("Solado excluído com sucesso!", "success")

    except IntegrityError:
        db.session.rollback()

        # 🔹 Buscar os códigos das referências associadas a este solado
        referencias = (
            db.session.query(Referencia.codigo_referencia)  # Pegando o campo correto
            .join(ReferenciaSolado, Referencia.id == ReferenciaSolado.referencia_id)
            .filter(ReferenciaSolado.solado_id == id)
            .all()
        )

        # Converte a lista de tuplas em uma string separada por vírgula
        referencias_str = ", ".join([ref.codigo_referencia for ref in referencias])

        flash(f"Erro: Este solado não pode ser excluído porque está associado às referências: {referencias_str}.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir o solado: {str(e)}", "danger")

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
@login_required
def listar_alcas():
    filtro = request.args.get('filtro', '')

    if filtro:
        alcas = Alca.query.filter(Alca.referencia.ilike(f"%{filtro}%")).all()
    else:
        alcas = Alca.query.order_by(Alca.id.desc()).all()

    return render_template('alcas.html', alcas=alcas)


@bp.route('/alca/nova', methods=['GET', 'POST'])
@login_required
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
@login_required
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
        
        # 🔹 Salva o log
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou a alca: {alca.referencia}"
        )
        db.session.add(log)
        
        flash("Alça atualizada com sucesso!", "success")
        return redirect(url_for('routes.listar_alcas'))

    return render_template('editar_alca.html', form=form, alca=alca, componentes=componentes)


import random, string
from flask import redirect, url_for, flash
from werkzeug.utils import secure_filename

@bp.route('/alca/copiar/<int:id>', methods=['GET'])
@login_required
def copiar_alca(id):
    # Recupera a alça original ou retorna 404 se não existir
    alca = Alca.query.get_or_404(id)
    
    # Gera o código temporário baseado no campo "referencia" da alça
    # Se alca.referencia estiver definido, usa os primeiros 7 caracteres; caso contrário, usa "ALCA"
    prefix = alca.referencia[:7] if alca.referencia else "ALCA"
    random_string = ''.join(random.choices(string.ascii_lowercase, k=6))
    codigo_temporario = f"{prefix}-cópia-{random_string}"
    
    # Cria a nova instância de Alca com o código temporário e demais dados copiados
    nova_alca = Alca(
        referencia=codigo_temporario,
        descricao=alca.descricao,
        imagem=alca.imagem
        # Adicione outros campos se necessário
    )
    db.session.add(nova_alca)
    db.session.flush()  # Garante que nova_alca.id seja definido para os relacionamentos

    # Copia os tamanhos da alça (assumindo que alca.tamanhos é uma lista de objetos TamanhoAlca)
    for tamanho in alca.tamanhos:
        novo_tamanho = TamanhoAlca(
            alca_id=nova_alca.id,
            nome=tamanho.nome,
            quantidade=tamanho.quantidade,
            peso_medio=tamanho.peso_medio
        )
        db.session.add(novo_tamanho)

    # Copia a formulação da alça (assumindo que alca.formulacao é uma lista de objetos FormulacaoAlca)
    for formulacao in alca.formulacao:
        nova_formulacao = FormulacaoAlca(
            alca_id=nova_alca.id,
            componente_id=formulacao.componente_id,
            carga=formulacao.carga
        )
        db.session.add(nova_formulacao)

    db.session.commit()
    flash("Alça copiada com sucesso! Atualize o código e os demais dados conforme necessário.", "success")
    return redirect(url_for('routes.editar_alca', id=nova_alca.id))


@bp.route('/alca/ver/<int:id>', methods=['GET'])
@login_required
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



from sqlalchemy.exc import IntegrityError

@bp.route('/alca/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_alca(id):
    alca = Alca.query.get_or_404(id)

    try:
        # Remover todas as referências antes de excluir
        FormulacaoAlca.query.filter_by(alca_id=id).delete()
        TamanhoAlca.query.filter_by(alca_id=id).delete()
        
                        # 🔹 Salva o log antes de excluir
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Excluiu a Alça: {alca.referencia}"
        )
        db.session.add(log)

        db.session.delete(alca)
        db.session.commit()
        flash("Alça excluída com sucesso!", "success")

    except IntegrityError:
        db.session.rollback()

        # 🔹 Buscar os códigos das referências associadas à alça
        referencias = (
            db.session.query(Referencia.codigo_referencia)  # Agora pegando o campo correto
            .join(ReferenciaAlca, Referencia.id == ReferenciaAlca.referencia_id)
            .filter(ReferenciaAlca.alca_id == id)
            .all()
        )

        # Converte a lista de tuplas em uma string separada por vírgula
        referencias_str = ", ".join([ref.codigo_referencia for ref in referencias])

        flash(f"Erro: Esta alça não pode ser excluída porque está associada às referências: {referencias_str}.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir a alça: {str(e)}", "danger")

    return redirect(url_for('routes.listar_alcas'))


# Rota para listar todas as margens
"""@bp.route('/margens', methods=['GET'])
@login_required
def listar_margens():
    margens = Margem.query.all()
    return render_template('margens.html', margens=margens)"""

@bp.route('/margens', methods=['GET'])
@login_required
def listar_margens():
    filtro = request.args.get('filtro', '')

    if filtro:
        margens = Margem.query.join(Referencia).filter(
            Referencia.codigo_referencia.ilike(f"%{filtro}%") | 
            Referencia.descricao.ilike(f"%{filtro}%")
        ).all()
    else:
        margens = Margem.query.order_by(Margem.id.desc()).all()

    return render_template('margens.html', margens=margens)


# Rota para criar uma nova margem
@bp.route('/margem/nova', methods=['GET', 'POST'])
@login_required
def nova_margem():
    form = MargemForm()
    referencias = Referencia.query.all()
    
    form.referencia_id.choices = [(r.id, f"{r.codigo_referencia} - {r.descricao}") for r in referencias]

    if form.validate_on_submit():
        referencia = Referencia.query.get(form.referencia_id.data)
        if not referencia:
            flash("Erro: Referência não encontrada.", "danger")
            return redirect(url_for('routes.nova_margem'))

        nova_margem = Margem(
            cliente=form.cliente.data,
            referencia_id=form.referencia_id.data,
            referencia=referencia,
            preco_venda=form.preco_venda.data,
            embalagem_escolhida=form.embalagem_escolhida.data,
            comissao_porcentagem=form.comissao_porcentagem.data or Decimal(0),
            comissao_valor=form.comissao_valor.data or Decimal(0),
            financeiro_porcentagem=form.financeiro_porcentagem.data or Decimal(0),
            financeiro_valor=form.financeiro_valor.data or Decimal(0),
            duvidosos_porcentagem=form.duvidosos_porcentagem.data or Decimal(0),
            duvidosos_valor=form.duvidosos_valor.data or Decimal(0),
            frete_porcentagem=form.frete_porcentagem.data or Decimal(0),
            frete_valor=form.frete_valor.data or Decimal(0),
            tributos_porcentagem=form.tributos_porcentagem.data or Decimal(0),
            tributos_valor=form.tributos_valor.data or Decimal(0),
            outros_porcentagem=form.outros_porcentagem.data or Decimal(0),
            outros_valor=form.outros_valor.data or Decimal(0),
            
            # Campos fixos armazenados no banco
            custo_total=Decimal(0),
            preco_embalagem_escolhida=Decimal(0),
            lucro_unitario=Decimal(0),
            margem=Decimal(0),
            preco_sugerido_5=Decimal(0),
            preco_sugerido_7=Decimal(0),
            preco_sugerido_10=Decimal(0),
            preco_sugerido_12=Decimal(0),
            preco_sugerido_15=Decimal(0),
            preco_sugerido_20=Decimal(0)
        )

        db.session.add(nova_margem)
        nova_margem.calcular_custos()
        db.session.commit()

        flash("Margem cadastrada com sucesso!", "success")
        return redirect(url_for('routes.listar_margens'))

    return render_template('nova_margem.html', form=form, referencias=referencias)

@bp.route('/margem/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_margem(id):
    """
    Rota para editar uma margem existente.
    """
    margem = Margem.query.get_or_404(id)  # Busca a margem pelo ID ou retorna erro 404
    form = MargemForm(obj=margem)  # Preenche o formulário com os dados da margem existente
    referencias = Referencia.query.all()
    
    # 🔹 Preenche as opções do campo de referência corretamente
    form.referencia_id.choices = [(r.id, f"{r.codigo_referencia} - {r.descricao}") for r in referencias]

    if form.validate_on_submit():
        referencia = Referencia.query.get(form.referencia_id.data)

        if not referencia:
            flash("Erro: Referência não encontrada.", "danger")
            return redirect(url_for('routes.editar_margem', id=id))

        # 🔹 Atualiza os dados da margem existente
        margem.cliente = form.cliente.data
        margem.referencia_id = referencia.id  # Garante que o ID seja atualizado corretamente
        margem.referencia = referencia  # Garante que o objeto seja atualizado
        margem.preco_venda = form.preco_venda.data
        margem.embalagem_escolhida = form.embalagem_escolhida.data
        
        margem.comissao_porcentagem = form.comissao_porcentagem.data or Decimal(0)
        margem.comissao_valor = form.comissao_valor.data or Decimal(0)
        margem.financeiro_porcentagem = form.financeiro_porcentagem.data or Decimal(0)
        margem.financeiro_valor = form.financeiro_valor.data or Decimal(0)
        margem.duvidosos_porcentagem = form.duvidosos_porcentagem.data or Decimal(0)
        margem.duvidosos_valor = form.duvidosos_valor.data or Decimal(0)
        margem.frete_porcentagem = form.frete_porcentagem.data or Decimal(0)
        margem.frete_valor = form.frete_valor.data or Decimal(0)
        margem.tributos_porcentagem = form.tributos_porcentagem.data or Decimal(0)
        margem.tributos_valor = form.tributos_valor.data or Decimal(0)
        margem.outros_porcentagem = form.outros_porcentagem.data or Decimal(0)
        margem.outros_valor = form.outros_valor.data or Decimal(0)

        # 🔹 Recalcula os custos
        margem.calcular_custos()

        db.session.commit()
        
        # 🔹 Salva o log
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou a Margem: {margem.id} - vinculada a Ref: {margem.referencia.codigo_referencia}"
        )
        db.session.add(log)

        flash("Margem atualizada com sucesso!", "success")
        return redirect(url_for('routes.listar_margens'))

    return render_template('editar_margem.html', form=form, referencias=referencias, margem=margem)



@bp.route('/margem/copiar/<int:id>', methods=['GET'])
@login_required
def copiar_margem(id):
    margem_original = Margem.query.get_or_404(id)
    referencia = Referencia.query.get(margem_original.referencia_id)
    
    if not referencia:
        flash("Erro: Referência não encontrada para cópia.", "danger")
        return redirect(url_for('routes.listar_margens'))

    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    cliente_temp = f"{margem_original.cliente}-COPIA-{random_string}" if margem_original.cliente else f"COPIA-{random_string}"

    nova_margem = Margem(
        cliente=cliente_temp,
        referencia_id=referencia.id,
        referencia=referencia,
        preco_venda=margem_original.preco_venda,
        embalagem_escolhida=margem_original.embalagem_escolhida,
        comissao_porcentagem=margem_original.comissao_porcentagem,
        comissao_valor=margem_original.comissao_valor,
        financeiro_porcentagem=margem_original.financeiro_porcentagem,
        financeiro_valor=margem_original.financeiro_valor,
        duvidosos_porcentagem=margem_original.duvidosos_porcentagem,
        duvidosos_valor=margem_original.duvidosos_valor,
        frete_porcentagem=margem_original.frete_porcentagem,
        frete_valor=margem_original.frete_valor,
        tributos_porcentagem=margem_original.tributos_porcentagem,
        tributos_valor=margem_original.tributos_valor,
        outros_porcentagem=margem_original.outros_porcentagem,
        outros_valor=margem_original.outros_valor,
        
        custo_total=margem_original.custo_total,
        preco_embalagem_escolhida=margem_original.preco_embalagem_escolhida,
        lucro_unitario=margem_original.lucro_unitario,
        margem=margem_original.margem,
        preco_sugerido_5=margem_original.preco_sugerido_5,
        preco_sugerido_7=margem_original.preco_sugerido_7,
        preco_sugerido_10=margem_original.preco_sugerido_10,
        preco_sugerido_12=margem_original.preco_sugerido_12,
        preco_sugerido_15=margem_original.preco_sugerido_15,
        preco_sugerido_20=margem_original.preco_sugerido_20
    )

    db.session.add(nova_margem)
    nova_margem.calcular_custos()
    db.session.commit()

    flash("Margem copiada com sucesso!", "success")
    return redirect(url_for('routes.editar_margem', id=nova_margem.id))


@bp.route('/margem/<int:id>', methods=['GET'])
@login_required
def ver_margem(id):
    """
    Rota para exibir os detalhes de uma margem específica.
    """
    margem = Margem.query.get_or_404(id)  # Busca a margem ou retorna erro 404 se não existir
    return render_template('ver_margem.html', margem=margem)




# Rota para excluir uma margem
@bp.route('/margem/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_margem(id):
    margem = Margem.query.get_or_404(id)
    
        # 🔹 Salva o log antes de excluir
    log = LogAcao(
        usuario_id=current_user.id,
        usuario_nome=current_user.nome,
        acao=f"Excluiu a margem ID {margem.id} vinculada a Referencia: {margem.referencia.codigo_referencia}"
    )
    db.session.add(log)
    
    db.session.delete(margem)
    db.session.commit()
    flash('Margem excluída com sucesso!', 'success')
    return redirect(url_for('routes.listar_margens'))






