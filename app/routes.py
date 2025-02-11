from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Referencia, Componente, CustoOperacional, Salario, MaoDeObra
from app.forms import ReferenciaForm, ComponenteForm, CustoOperacionalForm, SalarioForm, MaoDeObraForm
import os
#SOLADO
from flask import render_template, redirect, url_for, flash, request
from app import db
from app.models import Solado, Tamanho
from app.forms import SoladoForm
import os

bp = Blueprint('routes', __name__)

UPLOAD_FOLDER = 'app/static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@bp.route('/')
def home():
    return render_template('home.html')

    #REFERENCIAS OK
@bp.route('/referencias')
def listar_referencias():
    referencias = Referencia.query.all()
    return render_template('referencias.html', referencias=referencias)

@bp.route('/referencia/nova', methods=['GET', 'POST'])
def nova_referencia():
    form = ReferenciaForm()
    if form.validate_on_submit():
        imagem_filename = None
        if form.imagem.data:
            imagem_filename = form.imagem.data.filename
            form.imagem.data.save(os.path.join(UPLOAD_FOLDER, imagem_filename))
        
        referencia = Referencia(
            codigo_referencia=form.codigo_referencia.data,
            descricao=form.descricao.data,
            imagem=imagem_filename
        )
        db.session.add(referencia)
        db.session.commit()
        flash('Referência adicionada com sucesso!', 'success')
        return redirect(url_for('routes.listar_referencias'))
    
    return render_template('nova_referencia.html', form=form)

@bp.route('/referencia/editar/<int:id>', methods=['GET', 'POST'])
def editar_referencia(id):
    referencia = Referencia.query.get_or_404(id)
    form = ReferenciaForm(obj=referencia)
    
    if form.validate_on_submit():
        referencia.codigo_referencia = form.codigo_referencia.data
        referencia.descricao = form.descricao.data
        
        if form.imagem.data:
            imagem_filename = form.imagem.data.filename
            form.imagem.data.save(os.path.join(UPLOAD_FOLDER, imagem_filename))
            referencia.imagem = imagem_filename
        
        db.session.commit()
        flash('Referência atualizada com sucesso!', 'success')
        return redirect(url_for('routes.listar_referencias'))
    
    return render_template('editar_referencia.html', form=form, referencia=referencia)

@bp.route('/referencia/excluir/<int:id>', methods=['POST'])
def excluir_referencia(id):
    referencia = Referencia.query.get_or_404(id)
    db.session.delete(referencia)
    db.session.commit()
    flash('Referência excluída com sucesso!', 'danger')
    return redirect(url_for('routes.listar_referencias'))


        #COMPONENTES OK
@bp.route('/componentes')
def listar_componentes():
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
            consumo=form.consumo.data,
            preco_unitario=form.preco_unitario.data
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
        componente.consumo = form.consumo.data
        componente.preco_unitario = form.preco_unitario.data
        
        db.session.commit()
        flash('Componente atualizado com sucesso!', 'success')
        return redirect(url_for('routes.listar_componentes'))
    
    return render_template('editar_componente.html', form=form, componente=componente)

@bp.route('/componente/excluir/<int:id>', methods=['POST'])
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

@bp.route('/mao_de_obra/nova', methods=['GET', 'POST'])
def nova_mao_de_obra():
    form = MaoDeObraForm()
    form.salario_id.choices = [(s.id, f"R$ {s.preco}") for s in Salario.query.all()]
    
    if form.validate_on_submit():
        salario = Salario.query.get(form.salario_id.data)
        preco_liquido = form.multiplicador.data * salario.preco
        preco_bruto = preco_liquido * (1 + salario.encargos / 100)

        mao_de_obra = MaoDeObra(
            descricao=form.descricao.data,
            salario_id=form.salario_id.data,
            multiplicador=form.multiplicador.data,
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

@bp.route('/solados')
def listar_solados():
    solados = Solado.query.options(db.joinedload(Solado.tamanhos)).all()
    return render_template('solados.html', solados=solados)


@bp.route('/solado/<int:id>')
def ver_solado(id):
    solado = Solado.query.get_or_404(id)

    # capturamos os 4 valores
    total_quantidade, peso_medio_total, peso_friso_total, peso_sem_friso_total = solado.calcular_totais()

    return render_template('ver_solado.html', solado=solado,
                           total_quantidade=total_quantidade,
                           peso_medio_total=peso_medio_total,
                           peso_friso_total=peso_friso_total,
                           peso_sem_friso_total=peso_sem_friso_total)



@bp.route('/solado/novo', methods=['GET', 'POST'])
def novo_solado():
    form = SoladoForm()
    
    if form.validate_on_submit():
        print("🚀 Formulário validado! Processando os dados...")

        # Salvar a imagem do solado
        imagem_filename = None
        if form.imagem.data:
            imagem_filename = form.imagem.data.filename
            form.imagem.data.save(os.path.join(UPLOAD_FOLDER, imagem_filename))

        # Criar o Solado no banco
        solado = Solado(
            referencia=form.referencia.data,
            descricao=form.descricao.data,
            imagem=imagem_filename
        )
        db.session.add(solado)
        db.session.flush()  # Para obter o ID antes de salvar os tamanhos

        print(f"✅ Solado criado com ID: {solado.id}, Referência: {solado.referencia}")

        # Criar e associar os tamanhos ao Solado
        for tamanho_data in form.tamanhos.data:
            print(f"📝 Adicionando tamanho: {tamanho_data}")
            
            tamanho = Tamanho(
                nome=tamanho_data['nome'],
                quantidade=tamanho_data['quantidade'],
                peso_medio=tamanho_data['peso_medio'],
                peso_friso=tamanho_data['peso_friso'],
                peso_sem_friso=tamanho_data['peso_sem_friso'],
                solado_id=solado.id
            )
            db.session.add(tamanho)

        db.session.commit()
        flash('Solado cadastrado com sucesso!', 'success')
        print("✅ Solado e tamanhos cadastrados com sucesso!")
        return redirect(url_for('routes.listar_solados'))
    
    else:
        print("❌ O formulário não foi validado!")
        print("🛑 Erros no formulário:", form.errors)  # Exibe os erros no terminal

    return render_template('novo_solado.html', form=form)

@bp.route('/solado/editar/<int:id>', methods=['GET', 'POST'])
def editar_solado(id):
    solado = Solado.query.get_or_404(id)
    form = SoladoForm(obj=solado)

    if form.validate_on_submit():
        # Atualiza os dados do solado
        solado.referencia = form.referencia.data
        solado.descricao = form.descricao.data

        if form.imagem.data:
            imagem_filename = form.imagem.data.filename
            form.imagem.data.save(os.path.join(UPLOAD_FOLDER, imagem_filename))
            solado.imagem = imagem_filename

        # Atualiza os tamanhos
        for tamanho, tamanho_data in zip(solado.tamanhos, form.tamanhos.data):
            tamanho.nome = tamanho_data['nome']
            tamanho.quantidade = tamanho_data['quantidade']
            tamanho.peso_medio = tamanho_data['peso_medio']
            tamanho.peso_friso = tamanho_data['peso_friso']
            tamanho.peso_sem_friso = tamanho_data['peso_sem_friso']

        db.session.commit()
        flash("Solado atualizado com sucesso!", "success")
        return redirect(url_for('routes.listar_solados'))

    return render_template('editar_solado.html', form=form, solado=solado)

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