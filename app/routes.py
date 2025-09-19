import io
from sqlite3 import IntegrityError
from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
import pytz
from app import db, csrf
from app.models import Colaborador, ComponenteCor, ComponentePrecoHistorico, Cor, Estado, FormulacaoSolado, FormulacaoSoladoFriso, Funcionario, Grade, Linha, LogAcao, Manutencao, ManutencaoMaquina, ManutencaoPeca, Maquina, MargemPorPedido, MargemPorPedidoReferencia, Material, MaterialCor, Matriz, MovimentacaoComponente, MovimentacaoMaterial, MovimentacaoMatriz, Municipio, OrdemCompra, Peca, Permissao, PlanejamentoProducao, ProducaoConvencional, ProducaoDiaria, ProducaoFuncionario, ProducaoRotativa, ProducaoSetor, QuebraAlca, QuebraAlcaLinha, QuebraSolado, QuebraSoladoLinha, Referencia, Componente, CustoOperacional, ReferenciaAlca, ReferenciaComponentes, ReferenciaCustoOperacional, ReferenciaEmbalagem1, ReferenciaEmbalagem2, ReferenciaEmbalagem3, ReferenciaMaoDeObra, ReferenciaSolado, Remessa, Salario, MaoDeObra, Margem, Setor, TamanhoGrade, TamanhoMatriz, TamanhoMovimentacao, Tipo, TipoColaborador, TipoMaquina, TrocaHorario, TrocaMatriz, Usuario, hora_brasilia
from app.forms import ColaboradorForm, CorForm, DeleteForm, EstadoForm, ExcluirProducaoPorDataForm, FuncionarioForm, GradeForm, LinhaForm, ManutencaoForm, MaquinaForm, MargemForm, MargemPorPedidoForm, MargemPorPedidoReferenciaForm, MaterialForm, MatrizForm, MovimentacaoMatrizForm, OrdemCompraForm, PecaForm, PlanejamentoProducaoForm, ProducaoConvencionalForm, ProducaoDiariaForm, ProducaoFuncionarioForm, ProducaoRotativaForm, ProducaoSetorForm, QuebraAlcaForm, QuebraSoladoForm, ReferenciaForm, ComponenteForm, CustoOperacionalForm, RemessaForm, SalarioForm, MaoDeObraForm, SetorForm, TipoForm, TipoMaquinaForm, TrocaMatrizForm, UsuarioForm
import os
from flask import render_template, redirect, url_for, flash, request
from app.models import Solado, Tamanho, Componente, FormulacaoSolado, Alca, TamanhoAlca, FormulacaoAlca, Colecao
from app.forms import SoladoForm, AlcaForm, ColecaoForm
from flask import Blueprint
import os
from werkzeug.utils import secure_filename  # 🔹 Para salvar o nome do arquivo corretamente
from flask import current_app  # 🔹 Para acessar a configuração da aplicação
from decimal import Decimal, ROUND_HALF_UP  # Importa Decimal para cálculos precisos
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from flask import request, jsonify
from werkzeug.utils import secure_filename
from flask import current_app
from app.utils import allowed_file, formatar_moeda, formatar_numero, requer_permissao
from flask import g
import random, string
from sqlalchemy import case
from flask import render_template, make_response
from weasyprint import HTML
from io import BytesIO
from sqlalchemy.orm import aliased
from flask import jsonify, request
from sqlalchemy import func
from flask_wtf.csrf import validate_csrf, CSRFError
from sqlalchemy import asc, desc
from flask import Response
from datetime import date, datetime


bp = Blueprint('routes', __name__)

from app import cadastro_routes
from app import planejamentos_routes  # Importando as rotas de cadastro para usar o bp da rota principal

UPLOAD_FOLDER = 'app/static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@bp.before_request
def carregar_permissoes():
    """Garante que as permissões do usuário estejam disponíveis em todas as páginas."""
    if current_user.is_authenticated:
        g.permissoes = current_user.todas_permissoes
    else:
        g.permissoes = set()  # Usuário sem permissões


    
@bp.route('/usuarios')
@login_required
@requer_permissao('usuarios', 'ver')
def listar_usuarios():

    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)



@bp.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('usuarios', 'ver')
def novo_usuario():

    form = UsuarioForm()
    if form.validate_on_submit():
        novo_usuario = Usuario(
            nome=form.nome.data
        )
        novo_usuario.set_password(form.senha.data)
        db.session.add(novo_usuario)
        db.session.commit()
        flash("Usuário criado com sucesso!", "success")
        return redirect(url_for('routes.listar_usuarios'))

    return render_template('novo_usuario.html', form=form)


@bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('usuarios', 'editar')
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    # 🔹 Permite que o Admin edite apenas a si mesmo, mas impede outros de editá-lo
    if usuario.nome.lower() == "admin" and current_user.nome.lower() != "admin":
        flash("Você não pode editar o usuário Admin!", "danger")
        return redirect(url_for('routes.listar_usuarios'))

    form = UsuarioForm(obj=usuario)

    if form.validate_on_submit():
        usuario.nome = form.nome.data
        if form.senha.data:
            usuario.set_password(form.senha.data)
        db.session.commit()
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for('routes.listar_usuarios'))

    return render_template('usuarios/editar_usuario.html', form=form, usuario=usuario)

from app.auth.forms import AdminAlterarSenhaForm

@bp.route('/usuarios/alterar_senha/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('usuarios', 'editar')
def alterar_senha_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    # 🔐 Só o Admin pode alterar senhas de outros usuários
    if current_user.nome.lower() != "admin":
        flash("Apenas o usuário Admin pode alterar senhas de outros usuários.", "danger")
        return redirect(url_for('routes.listar_usuarios'))

    form = AdminAlterarSenhaForm()

    if form.validate_on_submit():
        usuario.set_password(form.nova_senha.data)
        db.session.commit()
        flash(f"Senha do usuário '{usuario.nome}' alterada com sucesso!", "success")
        return redirect(url_for('routes.listar_usuarios'))

    return render_template("usuarios/alterar_senha.html", form=form, usuario=usuario)



@bp.route('/usuarios/permissoes/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('usuarios', 'ver')
def gerenciar_permissoes(id):
    usuario = Usuario.query.get_or_404(id)

    # 🔹 Bloqueia edição do Admin apenas se não for o próprio Admin acessando
    if usuario.nome.lower() == "admin" and current_user.nome.lower() != "admin":
        flash("As permissões do Admin não podem ser modificadas por outro usuário!", "danger")
        return redirect(url_for('routes.listar_usuarios'))

    categorias = ["cadastro","comercial","financeiro","administrativo","desenvolvimento","manutencao","margens",
                  "custoproducao", "componentes",
                  "ppcp","controleproducao",
                  "funcionario", "usuarios", "trocar_senha"]
    acoes = ["criar", "ver", "editar", "excluir"]

    if request.method == "POST":
        # 🔹 O próprio Admin pode modificar suas permissões
        if current_user.nome.lower() == "admin" or usuario.nome.lower() != "admin":
            Permissao.query.filter_by(usuario_id=id).delete()
            
            for categoria in categorias:
                for acao in acoes:
                    if request.form.get(f"{categoria}_{acao}"):
                        db.session.add(Permissao(usuario_id=id, categoria=categoria, acao=acao))

            db.session.commit()
            flash("Permissões atualizadas com sucesso!", "success")
        else:
            flash("Você não pode modificar as permissões do Admin!", "danger")

        return redirect(url_for('routes.listar_usuarios'))

    permissoes_existentes = {f"{p.categoria}_{p.acao}" for p in usuario.permissoes}

    return render_template('gerenciar_permissoes.html', usuario=usuario, categorias=categorias, acoes=acoes, permissoes_existentes=permissoes_existentes)


@bp.route('/logs')
@login_required
@requer_permissao('usuarios', 'ver')
def listar_logs():
    logs = LogAcao.query.order_by(LogAcao.data_hora.desc()).all()
    return render_template('logs.html', logs=logs)


@bp.route('/')
@login_required
def home():
    user_agent = request.headers.get('User-Agent', '').lower()
    if any(mobile in user_agent for mobile in ['iphone', 'android', 'mobile']):
        return redirect(url_for('routes.home_mobile'))
    return render_template('home.html')

@bp.route('/home')
@login_required
def home_desktop():
    return render_template('home.html')


@bp.route('/home_mobile')
@login_required
def home_mobile():
    return render_template('home_mobile.html')




    #REFERENCIAS


@bp.route('/referencias', methods=['GET'])
@login_required
@requer_permissao('custoproducao', 'ver')
def listar_referencias():
    filtro = request.args.get('filtro', '')
    pagina = request.args.get('page', 1, type=int)
    por_pagina = 10

    query = Referencia.query

    if filtro:
        query = query.filter(Referencia.codigo_referencia.ilike(f"%{filtro}%"))

    query = query.order_by(Referencia.id.desc())

    paginadas = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

    # 🔹 Atualiza os totais apenas das exibidas
    for ref in paginadas.items:
        ref.calcular_totais()
        db.session.add(ref)
    db.session.commit()

    return render_template(
        'referencias.html',
        referencias=paginadas.items,
        paginacao=paginadas,
        filtro=filtro
    )



from app.models import Referencia, Colecao

@bp.route("/referencias/exportar")
@login_required
def exportar_referencias_excel():
    referencias = (
        db.session.query(
            Referencia.codigo_referencia,
            Referencia.descricao,
            Referencia.linha,
            Colecao.codigo.label("colecao")
        )
        .join(Colecao, Referencia.colecao_id == Colecao.id)
        .all()
    )

    # Criar DataFrame
    df = pd.DataFrame(referencias, columns=["Código", "Descrição", "Linha", "Coleção"])

    # Exportar para Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Referências')
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="referencias.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




# 🔹 Função para converter valores para float de forma segura
def parse_float(value, default=0):
    try:
        return float(value.strip()) if value.strip() else default
    except (ValueError, AttributeError):
        return default



@bp.route('/referencia/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('custoproducao', 'criar')
def nova_referencia():
    form = ReferenciaForm()
    form.colecao_id.choices = [(c.id, c.codigo) for c in Colecao.query.all()]

    # Recupera os dados para os modais
    solados = Solado.query.all()
    alcas = Alca.query.all()
    componentes = Componente.query.all()
    custos_operacionais = CustoOperacional.query.all()
    mao_de_obra = MaoDeObra.query.all()
    colecoes = Colecao.query.all()
    
        # Definir uma coleção padrão
    if request.method == "GET":
        form.colecao_id.data = 3  # COLEÇÃO 2025.1 PADRÃO

    if form.validate_on_submit():
        
        referencia = Referencia(
            codigo_referencia=form.codigo_referencia.data,
            descricao=form.descricao.data,
            linha=form.linha.data,
            colecao_id=form.colecao_id.data,
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
        mao_de_obra=mao_de_obra,
        colecoes=colecoes
    )


@bp.route('/referencia/ver/<int:id>', methods=['GET'])
@login_required
@requer_permissao('custoproducao', 'ver')
def ver_referencia(id):
    referencia = Referencia.query.get_or_404(id)
    
    # 🔹 Sempre recalcula os totais antes de exibir
    referencia.calcular_totais()
    db.session.add(referencia)  # 🔹 Garante que a referência seja atualizada no banco
    db.session.commit()  # 🔹 Salva os valores atualizados no banco
    

    # Recuperando os itens associados
    solados = ReferenciaSolado.query.filter_by(referencia_id=referencia.id).all()
    alcas = ReferenciaAlca.query.filter_by(referencia_id=referencia.id).all()
    componentes = ReferenciaComponentes.query.filter_by(referencia_id=referencia.id).all()
    embalagem1 = ReferenciaEmbalagem1.query.filter_by(referencia_id=referencia.id).all()
    embalagem2 = ReferenciaEmbalagem2.query.filter_by(referencia_id=referencia.id).all()
    embalagem3 = ReferenciaEmbalagem3.query.filter_by(referencia_id=referencia.id).all()
    custos_operacionais = ReferenciaCustoOperacional.query.filter_by(referencia_id=referencia.id).all()
    mao_de_obra = ReferenciaMaoDeObra.query.filter_by(referencia_id=referencia.id).all()
    colecao = Colecao.query.get(referencia.colecao_id)  # 🔹 Obtém a coleção associada

    
    # ✅ Pega os valores diretamente da referência
    custo_total_embalagem1 = referencia.custo_total_embalagem1
    custo_total_embalagem2 = referencia.custo_total_embalagem2
    custo_total_embalagem3 = referencia.custo_total_embalagem3
    

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
        mao_de_obra=mao_de_obra,
        custo_total_embalagem1=custo_total_embalagem1,
        custo_total_embalagem2=custo_total_embalagem2,
        custo_total_embalagem3=custo_total_embalagem3,
        colecao=colecao  # 🔹 Passa a coleção para o template
    )


from flask import render_template, request, redirect, url_for, flash
from app import db
from app.models import Referencia, ReferenciaSolado, ReferenciaAlca, ReferenciaComponentes, ReferenciaCustoOperacional, ReferenciaMaoDeObra, Solado, Alca, Componente, CustoOperacional, MaoDeObra
from app.forms import ReferenciaForm
import os
from werkzeug.utils import secure_filename

@bp.route('/referencia/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('custoproducao', 'editar')
def editar_referencia(id):
    """Edita uma referência existente permitindo adicionar, atualizar ou remover itens."""
    referencia = Referencia.query.get_or_404(id)
    form = ReferenciaForm(obj=referencia)
    form.colecao_id.choices = [(c.id, c.codigo) for c in Colecao.query.all()]

    # Recupera os itens já associados à referência
    solados = ReferenciaSolado.query.filter_by(referencia_id=id).all()
    alcas = ReferenciaAlca.query.filter_by(referencia_id=id).all()
    componentes = ReferenciaComponentes.query.filter_by(referencia_id=id).all()
    embalagem1 = ReferenciaEmbalagem1.query.filter_by(referencia_id=id).all()
    embalagem2 = ReferenciaEmbalagem2.query.filter_by(referencia_id=id).all()
    embalagem3 = ReferenciaEmbalagem3.query.filter_by(referencia_id=id).all()
    custos_operacionais = ReferenciaCustoOperacional.query.filter_by(referencia_id=id).all()
    mao_de_obra = ReferenciaMaoDeObra.query.filter_by(referencia_id=id).all()
    colecao = Colecao.query.get(referencia.colecao_id)

    if form.validate_on_submit():
        nova_referencia = form.codigo_referencia.data.strip()

        # Verifica se a referência já existe no banco e não é a mesma que está sendo editada
        referencia_existente = Referencia.query.filter(
            Referencia.codigo_referencia == nova_referencia,
            Referencia.id != id  # Exclui a própria referência da verificação
        ).first()

        if referencia_existente:
            flash("Erro: Já existe uma referência com esse código no banco!", "danger")
            return redirect(url_for('routes.editar_referencia', id=id))

        # Atualiza os dados da referência
        referencia.codigo_referencia = nova_referencia
        referencia.descricao = form.descricao.data
        referencia.linha = form.linha.data
        referencia.colecao_id = form.colecao_id.data

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

        db.session.commit()  # 🔹 Confirma a remoção para evitar erro de referências

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
        def adicionar_embalagem(modelo, nome_form):
            ids_post = request.form.getlist(f"{nome_form}_id[]")
            consumos_post = request.form.getlist(f"{nome_form}_consumo[]")

            for item_id, consumo in zip(ids_post, consumos_post):
                consumo_decimal = Decimal(consumo) if consumo else Decimal(0)

                componente = Componente.query.get(int(item_id))
                preco_unitario = componente.preco if componente else Decimal(0)

                novo_item = modelo(
                    referencia_id=id,
                    componente_id=int(item_id),
                    consumo=consumo_decimal,
                    preco_unitario=preco_unitario
                )
                db.session.add(novo_item)

        adicionar_embalagem(ReferenciaEmbalagem1, "embalagem1")
        adicionar_embalagem(ReferenciaEmbalagem2, "embalagem2")
        adicionar_embalagem(ReferenciaEmbalagem3, "embalagem3")

        # 🔹 Recalcular os totais
        referencia.calcular_totais()
        db.session.add(referencia)

        try:
            # 🔹 Salva o log
            log = LogAcao(
                usuario_id=current_user.id,
                usuario_nome=current_user.nome,
                acao=f"Editou a Referência: {referencia.codigo_referencia}"
            )
            db.session.add(log)
            db.session.commit()
            flash("Referência atualizada com sucesso!", "success")
            return redirect(url_for('routes.listar_referencias'))
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar no banco: {e}")
            flash("Erro ao salvar as alterações. Verifique os logs.", "danger")

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
        solados_disponiveis=Solado.query.all(),
        alcas_disponiveis=Alca.query.all(),
        componentes_disponiveis=Componente.query.all(),
        custos_disponiveis=CustoOperacional.query.all(),
        mao_de_obra_disponiveis=MaoDeObra.query.all(),
        colecao=colecao
    )



@bp.route('/referencia/copiar/<int:id>', methods=['GET'])
@login_required
@requer_permissao('custoproducao', 'editar')
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
        colecao_id=referencia.colecao_id,
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
@requer_permissao('custoproducao', 'excluir')
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
@requer_permissao('desenvolvimento', 'ver')
def listar_colecoes():
    colecoes = Colecao.query.order_by(Colecao.id.desc()).all()
    return render_template('colecoes.html', colecoes=colecoes)

@bp.route('/colecao/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('desenvolvimento', 'criar')
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
@requer_permissao('desenvolvimento', 'editar')
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
@requer_permissao('desenvolvimento', 'excluir')
def excluir_colecao(id):
    colecao = Colecao.query.get_or_404(id)
    referencias_vinculadas = Referencia.query.filter_by(colecao_id=colecao.id).all()
    
    if referencias_vinculadas:
        referencias_str = ", ".join([ref.codigo_referencia for ref in referencias_vinculadas])
        flash(f"Erro: Não é possível excluir a coleção pois está vinculada às referências: {referencias_str}.", "danger")
        return redirect(url_for('routes.listar_colecoes'))
    
    try:
        db.session.delete(colecao)
        db.session.commit()
        flash("Coleção excluída com sucesso!", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Erro: Não foi possível excluir a coleção.", "danger")
    
    return redirect(url_for('routes.listar_colecoes'))



#COMPONENTES OK

# ---------- helper: validar fornecedor ----------
def _resolver_fornecedor_id(form_value: str | None) -> int | None:
    """
    Recebe o valor vindo do template (Select2/hidden) e retorna:
      - int válido (ID de colaborador do tipo 'Fornecedor'), ou
      - None se vazio/não informado.
    Se o ID não existir ou não for do tipo 'Fornecedor', retorna None e o caller pode decidir o que fazer.
    """
    if not form_value:
        return None
    try:
        fid = int(form_value)
    except (TypeError, ValueError):
        return None

    # Verifica se o colaborador existe e tem tipo "Fornecedor" (case-insensitive)
    colab = (db.session.query(Colaborador)
             .join(TipoColaborador, Colaborador.tipo_id == TipoColaborador.id)
             .filter(Colaborador.id == fid, TipoColaborador.descricao.ilike('%Fornecedor%'))
             .first())
    return colab.id if colab else None


# ---------- LISTAGEM ----------
@bp.route('/componentes', methods=['GET'])
@login_required
@requer_permissao('componentes', 'ver')
def listar_componentes():
    # Filtros
    codigo = (request.args.get('codigo') or '').strip()
    descricao = (request.args.get('descricao') or '').strip()
    tipo = (request.args.get('tipo') or '').strip()

    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    if per_page not in (10, 25, 50, 100):
        per_page = 25

    # Query base
    q = Componente.query

    if codigo:
        q = q.filter(Componente.codigo.ilike(f"%{codigo}%"))
    if descricao:
        q = q.filter(Componente.descricao.ilike(f"%{descricao}%"))
    if tipo:
        q = q.filter(Componente.tipo.ilike(f"%{tipo}%"))

    q = q.order_by(Componente.id.desc())

    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    componentes = pagination.items

    return render_template(
        'componentes.html',
        componentes=componentes,
        pagination=pagination,
        per_page=per_page,
        codigo=codigo,
        descricao=descricao,
        tipo=tipo
    )

@bp.route('/componente/<int:id>', methods=['GET'])
@login_required
@requer_permissao('componentes', 'ver')
def ver_componente(id):
    componente = (Componente.query
                  .options(joinedload(Componente.cores).joinedload(ComponenteCor.cor))
                  .get_or_404(id))
    # fornecedor já acessível via componente.fornecedor (id/nome)
    return render_template('ver_componente.html', componente=componente)


# helper: fornecedores (somente colaborador do tipo "Fornecedor")
def _listar_fornecedores():
    return (db.session.query(Colaborador)
            .join(TipoColaborador, Colaborador.tipo_id == TipoColaborador.id)
            .filter(TipoColaborador.descricao.ilike('%fornecedor%'))
            .order_by(Colaborador.nome.asc())
            .all())

@bp.route('/componente/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('componentes', 'criar')
def novo_componente():
    form = ComponenteForm()
    cores = Cor.query.order_by(Cor.nome.asc()).all()
    fornecedores = _listar_fornecedores()  # <<< AQUI

    if form.validate_on_submit():
        fornecedor_id = _resolver_fornecedor_id(request.form.get('fornecedor_id'))
        componente = Componente(
            codigo=form.codigo.data,
            tipo=form.tipo.data,
            descricao=form.descricao.data,
            unidade_medida=form.unidade_medida.data,
            preco=form.preco.data if form.preco.data is not None else Decimal('0'),
            fornecedor_id=fornecedor_id
        )
        db.session.add(componente)
        db.session.flush()

        selecionadas = []
        for x in request.form.getlist('cores[]'):
            if x.isdigit():
                selecionadas.append(int(x))
        if not selecionadas:
            sem_cor = Cor.query.filter(Cor.nome.ilike('Sem cor')).first()
            if sem_cor:
                selecionadas = [sem_cor.id]
        for cor_id in selecionadas:
            db.session.add(ComponenteCor(componente_id=componente.id, cor_id=cor_id, quantidade=Decimal('0.00')))

        db.session.commit()
        flash('Componente adicionado com sucesso!', 'success')
        return redirect(url_for('routes.listar_componentes'))

    return render_template('novo_componente.html', form=form, cores=cores, fornecedores=fornecedores)  # <<< AQUI

@bp.route('/componente/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('componentes', 'editar')
def editar_componente(id):
    componente = (Componente.query
                  .options(joinedload(Componente.cores).joinedload(ComponenteCor.cor))
                  .get_or_404(id))

    form = ComponenteForm(obj=componente)
    cores = Cor.query.order_by(Cor.nome.asc()).all()
    fornecedores = _listar_fornecedores()  # <<< AQUI

    existentes = {cc.cor_id: cc for cc in componente.cores}
    vinculadas_ids = set(existentes.keys())

    if form.validate_on_submit():
        componente.codigo = form.codigo.data
        componente.tipo = form.tipo.data
        componente.descricao = form.descricao.data
        componente.unidade_medida = form.unidade_medida.data

        fornecedor_id = _resolver_fornecedor_id(request.form.get('fornecedor_id'))
        componente.fornecedor_id = fornecedor_id  # pode ser None

        preco_ant = componente.preco or Decimal('0')
        preco_novo = form.preco.data if form.preco.data is not None else Decimal('0')
        if preco_ant != preco_novo:
            db.session.add(ComponentePrecoHistorico(
                componente_id=componente.id,
                preco_anterior=preco_ant,
                preco_novo=preco_novo,
                origem='manual',
                usuario_id=getattr(current_user, 'id', None),
                usuario_nome=getattr(current_user, 'nome', None) or getattr(current_user, 'username', None)
            ))
            componente.preco = preco_novo
            preco_msg = f" Preço alterado de {preco_ant} para {preco_novo}."
        else:
            preco_msg = ""

        selecionadas = set()
        for cid in request.form.getlist('cores[]'):
            try:
                selecionadas.add(int(cid))
            except (TypeError, ValueError):
                pass
        if not selecionadas:
            sem_cor = Cor.query.filter(Cor.nome.ilike('Sem cor')).first()
            if sem_cor:
                selecionadas = {sem_cor.id}

        add_count = 0
        for cor_id in selecionadas - vinculadas_ids:
            db.session.add(ComponenteCor(componente_id=componente.id, cor_id=cor_id, quantidade=Decimal('0.00')))
            add_count += 1

        bloqueadas = []
        for cor_id, cc in list(existentes.items()):
            if cor_id not in selecionadas:
                qtd = cc.quantidade or Decimal('0.00')
                if qtd == 0:
                    db.session.delete(cc)
                else:
                    bloqueadas.append(cc.cor.nome if cc.cor else f'Cor #{cor_id}')

        db.session.commit()

        if bloqueadas:
            flash(('Componente salvo.' + preco_msg +
                   ' Não removi estas cores pois possuem saldo: ' + ', '.join(bloqueadas)).strip(), 'warning')
        elif add_count or preco_msg or (fornecedor_id is not None):
            extras = []
            if add_count: extras.append(f'{add_count} cor(es) adicionada(s)')
            if preco_msg: extras.append('preço atualizado')
            if fornecedor_id is not None: extras.append('fornecedor atualizado')
            flash(('Componente atualizado com sucesso: ' + ', '.join(extras) + '.').strip(), 'success')
        else:
            flash('Componente atualizado com sucesso!', 'success')

        return redirect(url_for('routes.listar_componentes'))

    return render_template('editar_componente.html',
                           form=form,
                           componente=componente,
                           cores=cores,
                           fornecedores=fornecedores,  # <<< AQUI
                           vinculadas_ids=vinculadas_ids)


# ---------- EXCLUIR ----------
@bp.route('/componente/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('componentes', 'excluir')
@csrf.exempt  # mantém seu padrão atual
def excluir_componente(id):
    componente = Componente.query.get_or_404(id)

    try:
        db.session.delete(componente)
        db.session.commit()
        flash('Componente excluído com sucesso!', 'success')

    except IntegrityError:
        db.session.rollback()
        flash("Erro: Este componente não pode ser excluído porque está sendo utilizado em outras tabelas do sistema.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir o componente: {str(e)}", "danger")

    return redirect(url_for('routes.listar_componentes'))


@bp.route('/importar_componentes', methods=['POST'])
@login_required
@requer_permissao('componentes', 'editar')
def importar_componentes():
    if 'file' not in request.files:
        flash("Nenhum arquivo enviado.", "danger")
        return redirect(url_for('routes.listar_componentes'))

    file = request.files['file']
    if file.filename == '':
        flash("Arquivo inválido.", "danger")
        return redirect(url_for('routes.listar_componentes'))

    upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp')
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath, dtype={'codigo': str})
        atualizados = 0
        criados = 0

        # cor padrão "Sem cor"
        sem_cor = Cor.query.filter(Cor.nome.ilike('Sem cor')).first()
        if not sem_cor:
            flash('A cor "Sem cor" não foi encontrada. Crie-a antes de importar.', 'danger')
            return redirect(url_for('routes.listar_componentes'))

        for _, row in df.iterrows():
            codigo = (row.get('codigo') or '').strip()
            descricao = (row.get('descricao') or '').strip()
            tipo = (row.get('tipo') or '').strip()
            unidade_medida = (row.get('unidade_medida') or '').strip()
            # aceita "1,23" ou 1.23
            preco = Decimal(str(row.get('preco', '0')).replace(',', '.'))

            if not codigo:
                continue  # ignora linha sem código

            componente = Componente.query.filter_by(codigo=codigo).first()

            if componente:
                preco_ant = componente.preco or Decimal('0')
                mudou_preco = (preco_ant != preco)

                mudou_outros = (
                    componente.descricao != descricao or
                    componente.tipo != tipo or
                    componente.unidade_medida != unidade_medida
                )

                # histórico se o preço mudou (com usuário da importação)
                if mudou_preco:
                    db.session.add(ComponentePrecoHistorico(
                        componente_id=componente.id,
                        preco_anterior=preco_ant,
                        preco_novo=preco,
                        origem='importacao',
                        usuario_id=getattr(current_user, 'id', None),
                        usuario_nome=getattr(current_user, 'nome', None) or getattr(current_user, 'username', None)
                    ))

                if mudou_preco or mudou_outros:
                    componente.descricao = descricao
                    componente.tipo = tipo
                    componente.unidade_medida = unidade_medida
                    componente.preco = preco
                    atualizados += 1

                # garante vínculo "Sem cor" se ainda não tiver nenhuma cor
                tem_vinculo = ComponenteCor.query.filter_by(componente_id=componente.id).first()
                if not tem_vinculo:
                    db.session.add(ComponenteCor(
                        componente_id=componente.id,
                        cor_id=sem_cor.id,
                        quantidade=Decimal('0.00')
                    ))

            else:
                # cria novo
                componente = Componente(
                    codigo=codigo,
                    descricao=descricao,
                    tipo=tipo,
                    unidade_medida=unidade_medida,
                    preco=preco
                )
                db.session.add(componente)
                db.session.flush()  # precisa do ID

                # vincula "Sem cor"
                db.session.add(ComponenteCor(
                    componente_id=componente.id,
                    cor_id=sem_cor.id,
                    quantidade=Decimal('0.00')
                ))

                criados += 1

        db.session.commit()
        flash(f"Importação concluída! {criados} componentes criados, {atualizados} atualizados.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao processar arquivo: {str(e)}", "danger")

    finally:
        try:
            os.remove(filepath)
        except Exception:
            pass

    return redirect(url_for('routes.listar_componentes'))

##### MOVIMENTACAO COMPONENTE  #######


@bp.route('/componente/<int:componente_id>/movimentos')
@login_required
@requer_permissao('componentes', 'ver')
def listar_movimentos_componente(componente_id):
    # Carrega componente + cores vinculadas
    comp = (Componente.query
            .options(joinedload(Componente.cores).joinedload(ComponenteCor.cor))
            .get_or_404(componente_id))

    # Últimas 50 movimentações (histórico)
    movimentos = (MovimentacaoComponente.query
                  .filter_by(componente_id=comp.id)
                  .order_by(MovimentacaoComponente.id.desc())
                  .limit(50)
                  .all())

    # Select de cor: somente cores vinculadas ao componente
    cores_vinculadas = sorted([cc.cor for cc in comp.cores if cc.cor],
                              key=lambda c: c.nome.lower())

    # Monta linhas de saldo + totais no backend
    rows_saldo = []
    total_q = Decimal('0.00')
    total_v = Decimal('0.00')
    preco = comp.preco or Decimal('0.00')

    for cc in sorted(comp.cores, key=lambda cc: (cc.cor.nome if cc.cor else '').lower()):
        q = cc.quantidade or Decimal('0.00')
        v = q * preco
        rows_saldo.append({
            "cor_nome": cc.cor.nome if cc.cor else "-",
            "q": q,
            "v": v
        })
        total_q += q
        total_v += v

    return render_template('movimentos_componente.html',
                           componente=comp,
                           movimentos=movimentos,
                           cores=cores_vinculadas,
                           rows_saldo=rows_saldo,
                           total_q=total_q,
                           total_v=total_v)


@bp.route('/componente/<int:componente_id>/movimentar', methods=['POST'])
@login_required
@requer_permissao('componentes', 'editar')
def movimentar_componente(componente_id):
    comp = Componente.query.get_or_404(componente_id)

    tipo = (request.form.get('tipo') or '').upper()   # ENTRADA | SAIDA
    cor_id = request.form.get('cor_id', type=int)
    qtd_raw = (request.form.get('quantidade') or '').strip()
    observacao = (request.form.get('observacao') or '').strip() or None

    if tipo not in ('ENTRADA', 'SAIDA') or not cor_id:
        flash('Dados de movimentação incompletos.', 'danger')
        return redirect(url_for('routes.listar_movimentos_componente', componente_id=comp.id))

    try:
        quantidade = Decimal(qtd_raw.replace(',', '.'))
    except InvalidOperation:
        flash('Quantidade inválida.', 'danger')
        return redirect(url_for('routes.listar_movimentos_componente', componente_id=comp.id))

    if quantidade <= 0:
        flash('Quantidade deve ser maior que zero.', 'danger')
        return redirect(url_for('routes.listar_movimentos_componente', componente_id=comp.id))

    # Garante que a cor é vinculada ao componente
    cc = ComponenteCor.query.filter_by(componente_id=comp.id, cor_id=cor_id).first()
    if not cc:
        flash('Esta cor não está vinculada a este componente.', 'warning')
        return redirect(url_for('routes.listar_movimentos_componente', componente_id=comp.id))

    saldo_atual = cc.quantidade or Decimal('0.00')

    # Bloqueia saída acima do saldo
    if tipo == 'SAIDA' and quantidade > saldo_atual:
        flash('Saída maior que o saldo disponível para essa cor.', 'warning')
        return redirect(url_for('routes.listar_movimentos_componente', componente_id=comp.id))

    # Aplica no saldo
    cc.quantidade = (saldo_atual + quantidade) if tipo == 'ENTRADA' else (saldo_atual - quantidade)

    # Registra histórico
    db.session.add(MovimentacaoComponente(
        componente_id=comp.id,
        cor_id=cor_id,
        tipo=tipo,
        quantidade=quantidade,
        observacao=observacao
    ))

    db.session.commit()
    flash(f'{tipo.title()} registrada com sucesso.', 'success')
    return redirect(url_for('routes.listar_movimentos_componente', componente_id=comp.id))


### HISTÓRICO DE PREÇO DO COMPONENTE #####

@bp.route('/componente/<int:componente_id>/precos')
@login_required
@requer_permissao('componentes', 'ver')
def historico_precos_componente(componente_id):
    componente = Componente.query.get_or_404(componente_id)
    hist = (ComponentePrecoHistorico.query
            .filter_by(componente_id=componente.id)
            .order_by(ComponentePrecoHistorico.alterado_em.desc())
            .all())
    return render_template('historico_precos_componente.html',
                           componente=componente, historico=hist)


#CUSTOS OPERACIONAIS ROTAS!
@bp.route('/custos')
@requer_permissao('custoproducao', 'ver')
@login_required
def listar_custos():
    custos = CustoOperacional.query.order_by(CustoOperacional.id.desc()).all()
    return render_template('custos.html', custos=custos)

        #CUSTOS OPERACIONAIS OK
@bp.route('/custo/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('custoproducao', 'criar')
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
@requer_permissao('custoproducao', 'editar')
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
@requer_permissao('custoproducao', 'excluir')
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
@requer_permissao('custoproducao', 'ver')
def listar_salarios():
    salarios = Salario.query.order_by(Salario.id.desc()).all()
    return render_template('salarios.html', salarios=salarios)

@bp.route('/salario/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('custoproducao', 'criar')
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
@requer_permissao('custoproducao', 'editar')
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
@requer_permissao('custoproducao', 'excluir')
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

@bp.route('/mao_de_obra', methods=['GET'])
@login_required
@requer_permissao('custoproducao', 'ver')
def listar_mao_de_obra():
    mao_de_obra = MaoDeObra.query.order_by(MaoDeObra.id.desc()).all()

    # 🔹 Recalcula os valores antes de exibir
    for mao in mao_de_obra:
        mao.calcular_valores()
        db.session.commit()  # Salva os valores recalculados no banco

    return render_template('mao_de_obra.html', mao_de_obra=mao_de_obra)




from decimal import Decimal, ROUND_HALF_UP  # Importa Decimal para cálculos precisos

@bp.route('/mao_de_obra/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('custoproducao', 'criar')
def nova_mao_de_obra():
    form = MaoDeObraForm()
    form.salario_id.choices = [(s.id, f"R$ {s.preco}") for s in Salario.query.all()]

    if form.validate_on_submit():
        try:
            mao_de_obra = MaoDeObra(
                descricao=form.descricao.data,
                salario_id=form.salario_id.data,
                multiplicador=form.multiplicador.data
            )

            # 🔹 Chama o método para calcular todos os valores (incluindo diária)
            mao_de_obra.calcular_valores()

            db.session.add(mao_de_obra)
            db.session.commit()

            flash('Mão de obra adicionada com sucesso!', 'success')
            return redirect(url_for('routes.listar_mao_de_obra'))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('nova_mao_de_obra.html', form=form)


@bp.route('/mao_de_obra/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('custoproducao', 'editar')
def editar_mao_de_obra(id):
    mao = MaoDeObra.query.get_or_404(id)
    form = MaoDeObraForm(obj=mao)

    # Atualizar opções de salário no formulário
    form.salario_id.choices = [(s.id, f"R$ {s.preco}") for s in Salario.query.all()]

    if form.validate_on_submit():
        try:
            mao.descricao = form.descricao.data
            mao.salario_id = form.salario_id.data
            mao.multiplicador = form.multiplicador.data

            # 🔹 Chama o método para recalcular os valores (incluindo diária)
            mao.calcular_valores()

            db.session.commit()
            flash('Mão de obra atualizada com sucesso!', 'success')
            return redirect(url_for('routes.listar_mao_de_obra'))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('editar_mao_de_obra.html', form=form, mao=mao)


@bp.route('/mao_de_obra/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('custoproducao', 'excluir')
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
@requer_permissao('custoproducao', 'ver')
def listar_solados():
    filtro = request.args.get('filtro', '')
    page = request.args.get('page', 1, type=int)

    query = Solado.query

    if filtro:
        query = query.filter(Solado.referencia.ilike(f"%{filtro}%"))

    solados = query.order_by(Solado.id.desc()).paginate(page=page, per_page=5)

    return render_template('solados.html', solados=solados)

@bp.route("/solados/exportar")
@login_required
def exportar_solados_excel():
    solados = Solado.query.with_entities(
        Solado.referencia, Solado.descricao, Solado.imagem
        ).all()

    # Criar DataFrame com os dados
    df = pd.DataFrame(solados, columns=["Referencia","Descrição","Imagem"])

    # Criar buffer de memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Solados')
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="solados.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



@bp.route('/solado/ver/<int:id>')
@login_required
@requer_permissao('custoproducao', 'ver')
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
@requer_permissao('custoproducao', 'criar')
def novo_solado():
    form = SoladoForm()
    componentes = Componente.query.all()

    if form.validate_on_submit():
        
        # Verificação se já existe um solado com a mesma referência
        solado_existente = Solado.query.filter_by(referencia=form.referencia.data).first()
        if solado_existente:
            flash("Já existe um solado com essa referência!", "warning")
            return redirect(url_for('routes.novo_solado'))

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
@requer_permissao('custoproducao', 'editar')
def editar_solado(id):
    solado = Solado.query.get_or_404(id)  # Busca o solado no banco
    form = SoladoForm(obj=solado)  # Preenche o formulário com os dados existentes
    componentes = Componente.query.all()  # Para exibir os componentes no modal

    if form.validate_on_submit():
        # 🔹 Verifica se a referência foi alterada e se já existe no banco
        if form.referencia.data != solado.referencia:
            referencia_existente = Solado.query.filter_by(referencia=form.referencia.data).first()
            if referencia_existente:
                flash("A referência informada já existe no banco de dados!", "danger")
                return redirect(url_for('routes.editar_solado', id=id))

            # Se passou pela verificação, atualiza a referência
            solado.referencia = form.referencia.data

        # 🔹 Atualizar a descrição
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

        # 🔹 Salva o log
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou o Solado: {solado.referencia}"
        )
        db.session.add(log)

        # 🔹 Commitando as alterações no banco
        db.session.commit()

        flash("Solado atualizado com sucesso!", "success")
        return redirect(url_for('routes.listar_solados'))

    return render_template('editar_solado.html', form=form, solado=solado, componentes=componentes)




@bp.route('/solado/copiar/<int:id>', methods=['GET'])
@login_required
@requer_permissao('custoproducao', 'editar')
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
@requer_permissao('custoproducao', 'excluir')
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


@bp.route('/alcas', methods=['GET'])
@login_required
@requer_permissao('custoproducao', 'ver')
def listar_alcas():
    filtro = request.args.get('filtro', '')
    pagina = request.args.get('page', 1, type=int)
    por_pagina = 10

    query = Alca.query

    if filtro:
        query = query.filter(Alca.referencia.ilike(f"%{filtro}%"))

    query = query.order_by(Alca.id.desc())

    paginadas = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

    return render_template(
        'alcas.html',
        alcas=paginadas.items,
        paginacao=paginadas,
        filtro=filtro
    )

@bp.route("/alcas/exportar")
@login_required
def exportar_alcas_excel():
    alcas = Alca.query.with_entities(
        Alca.referencia, Alca.descricao, Alca.imagem
        ).all()

    # Criar DataFrame com os dados
    df = pd.DataFrame(alcas, columns=["Referencia","Descrição","Imagem"])

    # Criar buffer de memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='alcas')
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="alcas.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@bp.route('/alca/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('custoproducao', 'criar')
def nova_alca():
    form = AlcaForm()
    componentes = Componente.query.all()

    if form.validate_on_submit():
        # Verificação se já existe uma alça com a mesma referência
        alca_existente = Alca.query.filter_by(referencia=form.referencia.data).first()
        if alca_existente:
            flash("Já existe uma alça com essa referência!", "warning")
            return redirect(url_for('routes.nova_alca'))
        
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
@requer_permissao('custoproducao', 'criar')
def editar_alca(id):
    alca = Alca.query.get_or_404(id)
    form = AlcaForm(obj=alca)
    componentes = Componente.query.all()  # Para exibir os componentes no modal

    if form.validate_on_submit():
        # **🔹 Verifica se a referência foi alterada**
        if form.referencia.data != alca.referencia:
            referencia_existente = Alca.query.filter_by(referencia=form.referencia.data).first()
            if referencia_existente:
                flash("A referência informada já existe no banco de dados!", "danger")
                return redirect(url_for('routes.editar_alca', id=id))
            
            # Se não existe no banco, pode atualizar a referência
            alca.referencia = form.referencia.data

        # **🔹 Atualizar os outros dados da alça**
        alca.descricao = form.descricao.data

        # **🔹 Atualizar imagem, se foi enviada uma nova**
        if form.imagem.data:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_filename)
            form.imagem.data.save(caminho_imagem)
            alca.imagem = imagem_filename

        # **🔹 Atualizar tamanhos (remove os antigos e insere os novos)**
        alca.tamanhos.clear()
        for tamanho_data in form.tamanhos.data:
            nome = tamanho_data["nome"] if tamanho_data["nome"] else "--"
            quantidade = tamanho_data["quantidade"] if tamanho_data["quantidade"] else 0
            peso_medio = tamanho_data["peso_medio"] if tamanho_data["peso_medio"] else 0.0

            tamanho = TamanhoAlca(
                alca_id=alca.id,
                nome=nome,
                quantidade=quantidade,
                peso_medio=peso_medio
            )
            alca.tamanhos.append(tamanho)

        # **🔹 Atualizar formulação (remove os antigos e insere os novos)**
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

        # **🔹 Salva o log**
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou a alça: {alca.referencia}"
        )
        db.session.add(log)
        db.session.commit()
        flash("Alça atualizada com sucesso!", "success")
        return redirect(url_for('routes.listar_alcas'))

    return render_template('editar_alca.html', form=form, alca=alca, componentes=componentes)



@bp.route('/alca/copiar/<int:id>', methods=['GET'])
@login_required
@requer_permissao('custoproducao', 'editar')
def copiar_alca(id):
    # Recupera a alça original ou retorna 404 se não existir
    alca = Alca.query.get_or_404(id)
    
    # Gera o código temporário baseado no campo "referencia" da alça
    # Se alca.referencia estiver definido, usa os primeiros 7 caracteres; caso contrário, usa "ALCA"
    prefix = alca.referencia[:7] if alca.referencia else "ALCA"
    random_string = ''.join(random.choices(string.ascii_lowercase, k=4))
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
@requer_permissao('custoproducao', 'ver')
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
@requer_permissao('custoproducao', 'excluir')
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

@bp.route('/margens', methods=['GET'])
@login_required
@requer_permissao('margens', 'ver')
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
@requer_permissao('margens', 'criar')
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

            #DOLAR
            dolar = form.dolar.data or Decimal(0),
            
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
            preco_sugerido_20=Decimal(0),
            #DOLAR
            preco_venda_dolar=Decimal(0)
        )

        db.session.add(nova_margem)
        nova_margem.calcular_custos()
        db.session.commit()

        flash("Margem cadastrada com sucesso!", "success")
        return redirect(url_for('routes.listar_margens'))

    return render_template('nova_margem.html', form=form, referencias=referencias)

@bp.route('/margem/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('margens', 'editar')
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

        #DOLAR
        margem.dolar = Decimal(form.dolar.data or 0)

        # 🔹 Recalcula os custos
        margem.calcular_custos()
        
        # 🔹 Salva o log
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou a Margem: {margem.id} - vinculada a Ref: {margem.referencia.codigo_referencia}"
        )
        db.session.add(log)

        db.session.commit()
        flash("Margem atualizada com sucesso!", "success")
        return redirect(url_for('routes.listar_margens'))

    return render_template('editar_margem.html', form=form, referencias=referencias, margem=margem)



@bp.route('/margem/copiar/<int:id>', methods=['GET'])
@login_required
@requer_permissao('margens', 'editar')
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
        preco_sugerido_20=margem_original.preco_sugerido_20,

        #DOLAR
        dolar=margem_original.dolar,
        preco_venda_dolar=margem_original.preco_venda_dolar
    )

    db.session.add(nova_margem)
    nova_margem.calcular_custos()
    db.session.commit()

    flash("Margem copiada com sucesso!", "success")
    return redirect(url_for('routes.editar_margem', id=nova_margem.id))


@bp.route('/margem/<int:id>', methods=['GET'])
@login_required
@requer_permissao('margens', 'ver')
def ver_margem(id):
    """
    Rota para exibir os detalhes de uma margem específica.
    """
    margem = Margem.query.get_or_404(id)  # Busca a margem ou retorna erro 404 se não existir
    return render_template('ver_margem.html', margem=margem)




# Rota para excluir uma margem
@bp.route('/margem/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('margens', 'excluir')
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



from sqlalchemy import or_

@bp.route('/margens_pedido', methods=['GET'])
@login_required
@requer_permissao('margens', 'ver')
def listar_margens_pedido():
    filtro = request.args.get('filtro', '').strip()

    if filtro:
        margens = MargemPorPedido.query.filter(
            or_(
                MargemPorPedido.pedido.ilike(f'%{filtro}%'),
                MargemPorPedido.remessa.ilike(f'%{filtro}%'),
                MargemPorPedido.cliente.ilike(f'%{filtro}%'),
                MargemPorPedido.nota_fiscal.ilike(f'%{filtro}%')
            )
        ).order_by(MargemPorPedido.id.desc()).all()
    else:
        margens = MargemPorPedido.query.order_by(MargemPorPedido.id.desc()).all()

    return render_template('margens_pedido.html', margens=margens)




@bp.route('/margem_pedido/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('margens', 'criar')
def nova_margem_pedido():
    form = MargemPorPedidoForm()
    referencia_form = MargemPorPedidoReferenciaForm()
    referencias = Referencia.query.all()

    if form.validate_on_submit():
        # Criar o pedido principal
        margem_pedido = MargemPorPedido(
            pedido=form.pedido.data,
            nota_fiscal=form.nota_fiscal.data,
            cliente=form.cliente.data,
            remessa=form.remessa.data,
            comissao_porcentagem=Decimal(form.comissao_porcentagem.data),
            comissao_valor=Decimal(form.comissao_valor.data),
            financeiro_porcentagem=Decimal(form.financeiro_porcentagem.data),
            financeiro_valor=Decimal(form.financeiro_valor.data),
            duvidosos_porcentagem=Decimal(form.duvidosos_porcentagem.data),
            duvidosos_valor=Decimal(form.duvidosos_valor.data),
            frete_porcentagem=Decimal(form.frete_porcentagem.data),
            frete_valor=Decimal(form.frete_valor.data),
            tributos_porcentagem=Decimal(form.tributos_porcentagem.data),
            tributos_valor=Decimal(form.tributos_valor.data),
            outros_porcentagem=Decimal(form.outros_porcentagem.data),
            outros_valor=Decimal(form.outros_valor.data)
        )
        db.session.add(margem_pedido)
        db.session.flush()  # Garante que a ID do pedido seja gerada antes de associar referências

        # Captura os CÓDIGOS das referências enviadas no formulário
        referencias_codigos = request.form.getlist("referencia_id[]")

        for codigo in referencias_codigos:
            quantidade = request.form.get(f"quantidade_{codigo}", type=int)
            embalagem_escolhida = request.form.get(f"embalagem_{codigo}")
            preco_venda = Decimal(request.form.get(f"preco_venda_{codigo}", "0.00"))

            # ✅ BUSCA O ID DA REFERÊNCIA NO BANCO USANDO O `codigo_referencia`
            referencia = Referencia.query.filter_by(codigo_referencia=codigo).first()
            if referencia:
                ref_margem = MargemPorPedidoReferencia(
                    margem_pedido_id=margem_pedido.id,
                    referencia_id=referencia.id,  # Usa o ID correto do banco
                    embalagem_escolhida=embalagem_escolhida,
                    quantidade=quantidade,
                    preco_venda=preco_venda
                )
                ref_margem.calcular_totais()  # 🔹 Faz o cálculo no modelo
                db.session.add(ref_margem)
            else:
                flash(f"Erro: Referência {codigo} não encontrada no banco de dados.", "danger")

        # 🔹 Agora chama os cálculos do pedido após adicionar todas as referências
        margem_pedido.calcular_totais()
        db.session.commit()

        flash("Margem por pedido salva com sucesso!", "success")
        return redirect(url_for('routes.listar_margens_pedido'))

    return render_template(
        'nova_margem_pedido.html',
        form=form,
        referencia_form=referencia_form,
        referencias=referencias
    )



@bp.route('/margem_pedido/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('margens', 'editar')
def editar_margem_pedido(id):
    """ Edita uma margem por pedido existente """
    margem_pedido = MargemPorPedido.query.get_or_404(id)
    form = MargemPorPedidoForm(obj=margem_pedido)
    referencia_form = MargemPorPedidoReferenciaForm()
    referencias = Referencia.query.all()

    if form.validate_on_submit():
        # Atualizar os dados principais
        margem_pedido.pedido = form.pedido.data
        margem_pedido.nota_fiscal = form.nota_fiscal.data
        margem_pedido.cliente = form.cliente.data
        margem_pedido.remessa = form.remessa.data
        margem_pedido.comissao_porcentagem = Decimal(form.comissao_porcentagem.data)
        margem_pedido.comissao_valor = Decimal(form.comissao_valor.data)
        margem_pedido.financeiro_porcentagem = Decimal(form.financeiro_porcentagem.data)
        margem_pedido.financeiro_valor = Decimal(form.financeiro_valor.data)
        margem_pedido.duvidosos_porcentagem = Decimal(form.duvidosos_porcentagem.data)
        margem_pedido.duvidosos_valor = Decimal(form.duvidosos_valor.data)
        margem_pedido.frete_porcentagem = Decimal(form.frete_porcentagem.data)
        margem_pedido.frete_valor = Decimal(form.frete_valor.data)
        margem_pedido.tributos_porcentagem = Decimal(form.tributos_porcentagem.data)
        margem_pedido.tributos_valor = Decimal(form.tributos_valor.data)
        margem_pedido.outros_porcentagem = Decimal(form.outros_porcentagem.data)
        margem_pedido.outros_valor = Decimal(form.outros_valor.data)

        # Excluir referências antigas
        MargemPorPedidoReferencia.query.filter_by(margem_pedido_id=id).delete()

        # Adicionar novas referências associadas
        referencias_ids = request.form.getlist("referencia_id[]")

        for ref_id in referencias_ids:
            quantidade = request.form.get(f"quantidade_{ref_id}", type=int)
            embalagem_escolhida = (request.form.get(f"embalagem_{ref_id}") or "").strip().lower()
            preco_venda = Decimal(request.form.get(f"preco_venda_{ref_id}", "0.00"))

            referencia = Referencia.query.get(ref_id)
            if referencia:
                ref_margem = MargemPorPedidoReferencia(
                    margem_pedido_id=margem_pedido.id,
                    referencia_id=referencia.id,
                    embalagem_escolhida=embalagem_escolhida,
                    quantidade=quantidade,
                    preco_venda=preco_venda
                )
                ref_margem.calcular_totais()  # 🔹 Faz o cálculo no modelo
                db.session.add(ref_margem)

        # Recalcular totais
        margem_pedido.calcular_totais()
        # 🔹 Salva o log
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou o Margem_Pedido: {margem_pedido.id} - Pedido: {margem_pedido.pedido}"
        )
        db.session.add(log)
        db.session.commit()

        flash("Margem por pedido editada com sucesso!", "success")
        return redirect(url_for('routes.listar_margens_pedido'))

    return render_template(
        'editar_margem_pedido.html',
        form=form,
        referencia_form=referencia_form,
        referencias=referencias,
        margem_pedido=margem_pedido
    )

#### COPIAR  #####
@bp.route('/margem_pedido/copiar/<int:id>', methods=['GET'])
@login_required
@requer_permissao('margens', 'criar')
def copiar_margem_pedido(id):
    """ Copia uma margem por pedido existente """
    margem_original = MargemPorPedido.query.get_or_404(id)

    # Gera um sufixo aleatório de 4 caracteres (letras e números)
    sufixo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

    nova_margem = MargemPorPedido(
        pedido=f"{margem_original.pedido}-{sufixo}-copia",
        nota_fiscal=margem_original.nota_fiscal,
        cliente=margem_original.cliente,
        remessa=margem_original.remessa,
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
        outros_valor=margem_original.outros_valor
    )

    db.session.add(nova_margem)
    db.session.flush()  # Garante que nova_margem.id seja gerado

    # Copiar referências vinculadas
    for ref in margem_original.referencias:
        nova_ref = MargemPorPedidoReferencia(
            margem_pedido_id=nova_margem.id,
            referencia_id=ref.referencia_id,
            embalagem_escolhida=ref.embalagem_escolhida,
            quantidade=ref.quantidade,
            preco_venda=ref.preco_venda
        )
        nova_ref.calcular_totais()
        db.session.add(nova_ref)

    # Recalcular totais da nova margem
    nova_margem.calcular_totais()

    # Log de cópia
    log = LogAcao(
        usuario_id=current_user.id,
        usuario_nome=current_user.nome,
        acao=f"Copiou a Margem_Pedido: {margem_original.id} para nova margem {nova_margem.id}"
    )
    db.session.add(log)

    db.session.commit()

    flash("Margem por pedido copiada com sucesso!", "success")
    return redirect(url_for('routes.editar_margem_pedido', id=nova_margem.id))



@bp.route('/margem_pedido/ver/<int:id>')
@login_required
@requer_permissao('margens', 'ver')
def ver_margem_pedido(id):
    """ Exibe os detalhes de uma margem por pedido """
    margem = MargemPorPedido.query.get_or_404(id)
    return render_template('ver_margem_pedido.html', margem=margem)


@bp.route('/margem_pedido/excluir/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('margens', 'excluir')
def excluir_margem_pedido(id):
    """ Exclui apenas a margem por pedido """
    margem_pedido = MargemPorPedido.query.get_or_404(id)

    try:
        db.session.delete(margem_pedido)
        # 🔹 Salva o log
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Excluiu a Margem_Pedido: {margem_pedido.id} - Pedido: {margem_pedido.pedido}"
        )
        db.session.add(log)
        db.session.commit()
        flash("Margem por pedido excluída com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"ERRO AO EXCLUIR Margem_Pedido: {margem_pedido.id} - Pedido: {margem_pedido.pedido}"
        )
        db.session.add(log)
        flash(f"Erro ao excluir margem: {str(e)}", "danger")

    return redirect(url_for('routes.listar_margens_pedido'))



@bp.route('/custo_remessa', methods=['GET', 'POST'])
@login_required
@requer_permissao('margens', 'ver')
def custo_remessa():
    margem_pedidos = []
    totais = {
        "total_preco_venda": Decimal(0),
        "total_custo": Decimal(0),
        "lucro_total": Decimal(0),
        "margem_media": Decimal(0),
    }

    remessa_selecionada = None
    remessas_disponiveis = db.session.query(MargemPorPedido.remessa).distinct().order_by(MargemPorPedido.remessa).all()
    remessas = [r[0] for r in remessas_disponiveis]

    if request.method == "POST":
        remessa_selecionada = request.form.get("remessa", "").strip()

        if remessa_selecionada:
            margem_pedidos = MargemPorPedido.query.filter_by(remessa=remessa_selecionada).all()

            if margem_pedidos:
                total_venda = sum(m.total_preco_venda for m in margem_pedidos)
                total_custo = sum(m.total_custo for m in margem_pedidos)
                lucro_total = sum(m.lucro_total for m in margem_pedidos)

                margem_media = (lucro_total / total_venda * 100) if total_venda > 0 else 0

                totais = {
                    "total_preco_venda": round(total_venda, 2),
                    "total_custo": round(total_custo, 2),
                    "lucro_total": round(lucro_total, 2),
                    "margem_media": round(margem_media, 2),
                }
            else:
                flash("Nenhuma margem por pedido encontrada para essa remessa.", "warning")

    return render_template(
        "custo_remessa.html",
        margem_pedidos=margem_pedidos,
        totais=totais,
        remessas=remessas,
        remessa_selecionada=remessa_selecionada
    )




 ####  IMPORTAÇÕES   #######
import re

def extrair_codigo_central(codigo_raw):
    """
    Extrai o código principal da referência, ignorando prefixos/sufixos.
    Exemplo: 'AB4VZ.KITEVA170B' → 'KITEVA170'
    """
    codigo_raw = str(codigo_raw).strip().upper()

    # Regex: pega a parte entre o ponto e antes da letra final
    match = re.search(r'\.([A-Z0-9]+)', codigo_raw)
    if match:
        base = match.group(1)
        # Remove letra final se houver (ex: B, C, D)
        if base[-1].isalpha() and base[:-1].isdigit() is False:
            base = base[:-1]
        return base
    return codigo_raw
@bp.route('/margem_pedido/importar', methods=['POST'])
@login_required
@requer_permissao('margens', 'editar')
@csrf.exempt
def importar_referencias():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado"})

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Arquivo inválido"})

    from werkzeug.utils import secure_filename
    import pandas as pd
    import os
    import re

    def extrair_codigo_central(codigo_raw):
        codigo_raw = str(codigo_raw).strip().upper()
        match = re.search(r'\.([A-Z0-9]+)', codigo_raw)
        if match:
            base = match.group(1)
            if base[-1].isalpha() and base[:-1].isdigit() is False:
                base = base[:-1]
            return base
        return codigo_raw

    filename = secure_filename(file.filename)
    filepath = os.path.join('app/static/uploads', filename)
    file.save(filepath)

    try:
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            df = pd.read_csv(filepath, delimiter=";")

        df.columns = [col.strip() for col in df.columns]

        referencias_dict = {}
        referencias_caixa = {}
        referencias_nao_encontradas = []

        for _, row in df.iterrows():
            # Ignora linhas em branco ou com "Pedido:" na célula
            if pd.isna(row["Referência"]) or pd.isna(row["Qtde"]) or pd.isna(row["Preço"]):
                continue
            if "pedido" in str(row["Referência"]).strip().lower():
                continue

            codigo_original = str(row["Referência"]).strip()
            codigo_ref = extrair_codigo_central(codigo_original)
            descricao = str(row["Descrição"]).strip()
            quantidade = int(row["Qtde"])
            preco_venda = float(row["Preço"])

            embalagem_raw = str(row["Embalagem"]).strip().upper()
            if embalagem_raw.startswith("SACO"):
                embalagem = "Saco"
            elif embalagem_raw.startswith("CAIXA"):
                embalagem = "caixa"
            else:
                embalagem = "Saco"

            referencia = Referencia.query.filter_by(codigo_referencia=codigo_ref).first()
            if not referencia:
                referencias_nao_encontradas.append(codigo_ref)
                continue

            destino = referencias_caixa if embalagem == "caixa" else referencias_dict
            if codigo_ref in destino:
                destino[codigo_ref]["quantidade"] += quantidade
            else:
                destino[codigo_ref] = {
                    "codigo": codigo_ref,
                    "descricao": descricao,
                    "quantidade": quantidade,
                    "embalagem": embalagem,
                    "preco_venda": preco_venda
                }

        if referencias_nao_encontradas:
            lista = ", ".join(set(referencias_nao_encontradas))
            return jsonify({
                "success": False,
                "error": f"As seguintes referências não possuem custo cadastrado no sistema: {lista}"
            })

        return jsonify({
            "success": True,
            "referencias": list(referencias_dict.values()),
            "referencias_caixa": list(referencias_caixa.values())
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})





#########  CONTROLE DE PRODUÇÃO ##########
# --------- TIPO MÁQUINA ---------

@bp.route('/tipos_maquina')
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_tipos_maquina():
    q = (request.args.get('q') or '').strip()
    query = TipoMaquina.query
    if q:
        query = query.filter(TipoMaquina.nome.ilike(f'%{q}%'))
    tipos = query.order_by(TipoMaquina.nome.asc()).all()
    return render_template('listar_tipos_maquina.html', tipos=tipos, q=q)

@bp.route('/tipos_maquina/novo', methods=['GET','POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def novo_tipo_maquina():
    form = TipoMaquinaForm()
    if form.validate_on_submit():
        tm = TipoMaquina(nome=form.nome.data.strip())
        db.session.add(tm)
        db.session.commit()
        flash('Tipo criado com sucesso!', 'success')
        return redirect(url_for('routes.listar_tipos_maquina'))
    return render_template('novo_tipo_maquina.html', form=form)

@bp.route('/tipos_maquina/editar/<int:id>', methods=['GET','POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_tipo_maquina(id):
    tm = TipoMaquina.query.get_or_404(id)
    form = TipoMaquinaForm(obj=tm)
    form._editing_id = id  # permite manter o mesmo nome sem bloquear
    if form.validate_on_submit():
        # checagem extra case-insensitive
        existe = (db.session.query(TipoMaquina.id)
                  .filter(func.lower(TipoMaquina.nome) == func.lower(form.nome.data.strip()),
                          TipoMaquina.id != id).first())
        if existe:
            flash('Já existe um tipo com esse nome.', 'danger')
            return render_template('editar_tipo_maquina.html', form=form, tm=tm)

        tm.nome = form.nome.data.strip()
        db.session.commit()
        flash('Tipo atualizado com sucesso!', 'success')
        return redirect(url_for('routes.listar_tipos_maquina'))
    return render_template('editar_tipo_maquina.html', form=form, tm=tm)

@bp.route('/tipos_maquina/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_tipo_maquina(id):
    token = request.form.get('csrf_token', '')
    try:
        validate_csrf(token)
    except CSRFError:
        flash('Falha na validação do CSRF.', 'danger')
        return redirect(url_for('routes.listar_tipos_maquina'))

    if (request.form.get('confirm_text') or '').strip().lower() != 'excluir':
        flash('Você precisa digitar "excluir" para confirmar.', 'warning')
        return redirect(url_for('routes.listar_tipos_maquina'))

    tm = TipoMaquina.query.get_or_404(id)

    if Maquina.query.filter_by(tipo_id=tm.id).first():
        flash('Não é possível excluir: existem máquinas vinculadas a este tipo.', 'danger')
        return redirect(url_for('routes.listar_tipos_maquina'))

    db.session.delete(tm)
    db.session.commit()
    flash('Tipo excluído com sucesso!', 'success')
    return redirect(url_for('routes.listar_tipos_maquina'))


@bp.route('/maquinas', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_maquinas():
    """ Lista todas as máquinas cadastradas """
    filtro = request.args.get('filtro', '')
    maquinas = Maquina.query.filter(Maquina.descricao.ilike(f"%{filtro}%")).order_by(Maquina.id.desc()).all()
    return render_template('maquinas.html', maquinas=maquinas)

# --------- MÁQUINA (novo/editar) ---------

def _tipos_choices():
    return [(t.id, t.nome) for t in TipoMaquina.query.order_by(TipoMaquina.nome).all()]

@bp.route('/maquinas/novo', methods=['GET','POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_maquina():
    form = MaquinaForm()
    form.tipo_id.choices = _tipos_choices()
    if form.validate_on_submit():
        m = Maquina(
            codigo=form.codigo.data.strip(),
            descricao=form.descricao.data.strip(),
            tipo_id=form.tipo_id.data,
            status=form.status.data,
            preco=form.preco.data
        )
        db.session.add(m)
        db.session.commit()
        flash('Máquina criada com sucesso!', 'success')
        return redirect(url_for('routes.listar_maquinas'))
    return render_template('nova_maquina.html', form=form)

@bp.route('/maquinas/editar/<int:id>', methods=['GET','POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_maquina(id):
    m = Maquina.query.get_or_404(id)
    form = MaquinaForm(obj=m)
    form.tipo_id.choices = _tipos_choices()
    if form.validate_on_submit():
        m.codigo = form.codigo.data.strip()
        m.descricao = form.descricao.data.strip()
        m.tipo_id = form.tipo_id.data
        m.status = form.status.data
        m.preco = form.preco.data
        db.session.commit()
        flash('Máquina atualizada com sucesso!', 'success')
        return redirect(url_for('routes.listar_maquinas'))
    return render_template('editar_maquina.html', form=form, maq=m)


@bp.route('/maquina/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_maquina(id):
    """ Exclui uma máquina do sistema """
    maquina = Maquina.query.get_or_404(id)

    db.session.delete(maquina)
    db.session.commit()

    flash('Máquina excluída com sucesso!', 'success')
    return redirect(url_for('routes.listar_maquinas'))


@bp.route('/trocas_matriz', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_trocas_matriz():
    trocas = TrocaMatriz.query.order_by(TrocaMatriz.id.desc()).all()
    return render_template('trocas_matriz.html', trocas=trocas)


from datetime import datetime, time, timezone  # 🔹 Importando time corretamente

def parse_time(value):
    """ Converte string para time ou retorna 00:00 se vazia. """
    if value:
        return datetime.strptime(value, "%H:%M").time()  # Converte string para TIME
    return time(0, 0)  # 🔹 Correção: agora retorna 00:00 corretamente


@bp.route('/troca_matriz/ver/<int:id>', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def ver_troca_matriz(id):
    troca = TrocaMatriz.query.get_or_404(id)

    # Detectar trocas com dados preenchidos
    trocas_ativas = []
    for i in range(1, 8):
        for horario in troca.horarios:
            if getattr(horario, f"inicio_{i}") or getattr(horario, f"fim_{i}") or getattr(horario, f"motivo_{i}"):
                trocas_ativas.append(i)
            break  # Não precisa verificar mais se já encontrou dados nessa troca

    return render_template('ver_troca_matriz.html', troca=troca, trocas_ativas=trocas_ativas)

from datetime import datetime, time

def parse_time(value):
    """ Converte strings para objetos time ou retorna 00:00 se vazio. """
    return datetime.strptime(value, "%H:%M").time() if value else time(0, 0)


@bp.route('/troca_matriz/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_troca_matriz():
    form = TrocaMatrizForm()
    matrizes = Matriz.query.order_by(Matriz.codigo).all()

    # 🔹 Carregar as máquinas cadastradas
        # Carregar opções de funcionários e máquinas
    form.trocador_id.choices = [(f.id, f.nome) for f in Funcionario.query.filter_by(funcao="Trocador").order_by(Funcionario.nome).all()]
    form.operador_id.choices = [(f.id, f.nome) for f in Funcionario.query.filter_by(funcao="Operador").order_by(Funcionario.nome).all()]
    form.maquina_id.choices = [(m.id, f"{m.codigo} - {m.descricao}") for m in Maquina.query.order_by(Maquina.codigo).all()]

    # 🔹 Definir os horários fixos na ordem correta
    horarios = ["7h às 8h", "8h às 9h", "9h às 10h", "10h às 11h", "11h às 12h",
                "12h às 13h", "13h às 14h", "14h às 15h", "15h às 16h", "16h às 17h"]

    for i in range(len(horarios)):
        form.trocas[i].horario.data = horarios[i]

    if form.validate_on_submit():
        troca_matriz = TrocaMatriz(
            data=form.data.data,
            trocador_id=form.trocador_id.data,
            operador_id=form.operador_id.data,
            maquina_id=form.maquina_id.data
        )
        db.session.add(troca_matriz)
        db.session.flush()  # 🔹 Garante que o ID da troca matriz está disponível

        for i, troca in enumerate(form.trocas.entries):
            matriz_id_form = request.form.get(f'matriz_id_{i}')
            nova_troca = TrocaHorario(
                troca_matriz_id=troca_matriz.id,
                horario=horarios[i],
                pares=troca.form.pares.data or 0,
                producao_esperada=troca.form.producao_esperada.data or 0,
                matriz_id=int(matriz_id_form) if matriz_id_form else None,

                inicio_1=parse_time(troca.form.inicio_1.data),
                fim_1=parse_time(troca.form.fim_1.data),
                inicio_2=parse_time(troca.form.inicio_2.data),
                fim_2=parse_time(troca.form.fim_2.data),
                inicio_3=parse_time(troca.form.inicio_3.data),
                fim_3=parse_time(troca.form.fim_3.data),
                inicio_4=parse_time(troca.form.inicio_4.data),
                fim_4=parse_time(troca.form.fim_4.data),
                inicio_5=parse_time(troca.form.inicio_5.data),
                fim_5=parse_time(troca.form.fim_5.data),
                inicio_6=parse_time(troca.form.inicio_6.data),
                fim_6=parse_time(troca.form.fim_6.data),
                inicio_7=parse_time(troca.form.inicio_7.data),
                fim_7=parse_time(troca.form.fim_7.data),

                motivo_1=troca.form.motivo_1.data,
                motivo_2=troca.form.motivo_2.data,
                motivo_3=troca.form.motivo_3.data,
                motivo_4=troca.form.motivo_4.data,
                motivo_5=troca.form.motivo_5.data,
                motivo_6=troca.form.motivo_6.data,
                motivo_7=troca.form.motivo_7.data,
            )

            nova_troca.atualizar_tempo_total()
            db.session.add(nova_troca)


        # 🔹 Atualiza os cálculos gerais da troca matriz
        # 🔹 Atualiza os cálculos gerais da troca matriz
        troca_matriz.atualizar_tempo_total_geral()
        troca_matriz.calcular_total_pares()
        troca_matriz.calcular_total_esperado()
        troca_matriz.calcular_eficiencia_geral()

        db.session.commit()
        flash('Troca de matriz registrada com sucesso!', 'success')
        return redirect(url_for('routes.listar_trocas_matriz'))

    return render_template('nova_troca_matriz.html', form=form, matrizes=matrizes)

@bp.route('/troca_matriz/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_troca_matriz(id):
    troca_matriz = TrocaMatriz.query.get_or_404(id)
    form = TrocaMatrizForm(obj=troca_matriz)
    matrizes = Matriz.query.order_by(Matriz.codigo).all()

    form.trocador_id.choices = [(f.id, f.nome) for f in Funcionario.query.filter_by(funcao="Trocador").order_by(Funcionario.nome).all()]
    form.operador_id.choices = [(f.id, f.nome) for f in Funcionario.query.filter_by(funcao="Operador").order_by(Funcionario.nome).all()]
    form.maquina_id.choices = [(m.id, f"{m.codigo} - {m.descricao}") for m in Maquina.query.order_by(Maquina.codigo).all()]

    horarios = [
        "7h às 8h", "8h às 9h", "9h às 10h", "10h às 11h", "11h às 12h",
        "12h às 13h", "13h às 14h", "14h às 15h", "15h às 16h", "16h às 17h"
    ]
    troca_matriz.horarios.sort(key=lambda x: horarios.index(x.horario))

    if request.method == 'GET':
        for i, troca in enumerate(troca_matriz.horarios):
            if i < len(form.trocas.entries):
                form.trocas[i].horario.data = troca.horario
                form.trocas[i].pares.data = troca.pares
                form.trocas[i].producao_esperada.data = troca.producao_esperada

                # Passa a matriz selecionada, se houver
                form.trocas[i].matriz_id = troca.matriz_id
                form.trocas[i].matriz_codigo = troca.matriz.codigo if troca.matriz else ""
                form.trocas[i].matriz_descricao = troca.matriz.descricao if troca.matriz else ""

                for j in range(1, 8):
                    inicio = getattr(troca, f'inicio_{j}')
                    fim = getattr(troca, f'fim_{j}')
                    motivo = getattr(troca, f'motivo_{j}', '')

                    getattr(form.trocas[i], f'inicio_{j}').data = inicio.strftime("%H:%M") if inicio else ""
                    getattr(form.trocas[i], f'fim_{j}').data = fim.strftime("%H:%M") if fim else ""
                    if hasattr(form.trocas[i], f'motivo_{j}'):
                        getattr(form.trocas[i], f'motivo_{j}').data = motivo

    if form.validate_on_submit():
        troca_matriz.data = form.data.data
        troca_matriz.trocador_id = form.trocador_id.data
        troca_matriz.maquina_id = form.maquina_id.data
        troca_matriz.operador_id = form.operador_id.data

        for i, troca in enumerate(troca_matriz.horarios):
            if i < len(form.trocas.entries):
                troca.pares = form.trocas[i].pares.data or 0
                troca.producao_esperada = form.trocas[i].producao_esperada.data or 0

                # Atualiza a matriz usada nessa linha
                # ✅ NOVO: atualiza a matriz_id
                matriz_id_form = request.form.get(f'matriz_id_{i}')
                if matriz_id_form:
                    troca.matriz_id = int(matriz_id_form)
                else:
                    troca.matriz_id = None

                for j in range(1, 8):
                    setattr(troca, f'inicio_{j}', parse_time(getattr(form.trocas[i], f'inicio_{j}').data))
                    setattr(troca, f'fim_{j}', parse_time(getattr(form.trocas[i], f'fim_{j}').data))

                    motivo_valor = getattr(form.trocas[i], f'motivo_{j}').data
                    setattr(troca, f'motivo_{j}', motivo_valor if motivo_valor is not None else "")



                troca.atualizar_tempo_total()
                troca.eficiencia_por_tempo()

        troca_matriz.atualizar_tempo_total_geral()
        troca_matriz.calcular_total_pares()
        troca_matriz.calcular_eficiencia_geral()
        troca_matriz.calcular_total_esperado()

        db.session.commit()
        flash('Troca de matriz editada com sucesso!', 'success')
        return redirect(url_for('routes.listar_trocas_matriz'))

    return render_template('editar_troca_matriz.html', form=form, troca_matriz=troca_matriz, matrizes=matrizes)



from flask import send_file
from io import BytesIO
from openpyxl import Workbook

@bp.route('/troca_matriz/<int:id>/exportar_excel')
@login_required
@requer_permissao('controleproducao', 'ver')
def exportar_troca_excel(id):

    troca = TrocaMatriz.query.get_or_404(id)

    horarios_padrao = [
        "7h às 8h", "8h às 9h", "9h às 10h", "10h às 11h", "11h às 12h",
        "12h às 13h", "13h às 14h", "14h às 15h", "15h às 16h", "16h às 17h"
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "Troca de Matriz"

    # Cabeçalho simplificado
    cabecalho = ["Horário", "Pares", "Matriz", "Capacidade", "Diferença"]
    for i in range(1, 8):
        cabecalho.extend([f"Início {i}ª", f"Fim {i}ª", f"Motivo {i}ª", f"Total {i}ª"])
    cabecalho.append("Total Tempo")
    ws.append(cabecalho)

    for h_padrao in horarios_padrao:
        linha = []
        h = next((item for item in troca.horarios if item.horario == h_padrao), None)
        if h:
            matriz = h.matriz
            linha.extend([
                h.horario,
                h.pares,
                f"{matriz.codigo} - {matriz.descricao}" if matriz else "Nenhuma",
                h.producao_esperada,
                h.pares - h.producao_esperada
            ])
            for i in range(1, 8):
                ini = getattr(h, f'inicio_{i}')
                fim = getattr(h, f'fim_{i}')
                motivo = getattr(h, f'motivo_{i}', '')
                duracao = getattr(h, f'duracao_{i}', 0)
                linha.extend([
                    ini.strftime("%H:%M") if ini else "",
                    fim.strftime("%H:%M") if fim else "",
                    motivo or "",
                    f"{duracao // 60:02}:{duracao % 60:02}"
                ])
            linha.append(f"{h.tempo_total_troca // 60:02}:{h.tempo_total_troca % 60:02}")
        else:
            linha = [h_padrao] + [""] * (len(cabecalho) - 1)
        ws.append(linha)

    # Aba de Eficiência
    aba = wb.create_sheet("Eficiência Geral")
    aba.append(["Tempo Produtivo Real", f"{troca.calcular_tempo_produtivo_real() // 60:02}:{troca.calcular_tempo_produtivo_real() % 60:02}"])
    aba.append(["Tempo Parado", f"{troca.tempo_total_geral // 60:02}:{troca.tempo_total_geral % 60:02}"])
    aba.append(["Total Pares Produzidos", troca.total_pares_produzidos])
    aba.append(["Capacidade Total", troca.calcular_total_esperado()])
    aba.append(["Diferença Total", troca.total_pares_produzidos - troca.calcular_total_esperado()])
    aba.append(["Pares por Minuto", troca.calcular_eficiencia_geral()])
    aba.append(["Pares por Hora", round(troca.calcular_eficiencia_geral() * 60, 2)])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output, as_attachment=True,
                     download_name=f'TrocaMatriz_{troca.id}.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')





@bp.route('/troca_matriz/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_troca_matriz(id):
    troca_matriz = TrocaMatriz.query.get_or_404(id)

    try:
        db.session.delete(troca_matriz)
        db.session.commit()
        flash("Troca de matriz excluída com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir troca de matriz: {str(e)}", "danger")

    return redirect(url_for('routes.listar_trocas_matriz'))



# 🔹 Listar Matrizes
@bp.route('/matrizes')
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_matrizes():
    matrizes = Matriz.query.order_by(Matriz.id.desc()).all()
    return render_template('listar_matrizes.html', matrizes=matrizes)




@bp.route('/matriz/ver/<int:id>')
@login_required
@requer_permissao('controleproducao', 'ver')
def ver_matriz(id):
    matriz = Matriz.query.get_or_404(id)

    # Ordenar tamanhos corretamente
    tamanhos_ordenados = sorted(
        matriz.tamanhos,
        key=lambda t: list(map(int, t.nome.split("/"))) if "/" in t.nome else [int(t.nome)] if t.nome.isdigit() else [float("inf")]
    )

    return render_template('ver_matriz.html', matriz=matriz, tamanhos_ordenados=tamanhos_ordenados)

# 🔹 Nova Matriz

@bp.route('/matriz/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_matriz():
    form = MatrizForm()
    linhas = Linha.query.order_by(Linha.nome).all()
    cores = Cor.query.order_by(Cor.nome).all()

    if request.method == 'POST':
        linha_id = request.form.get('linha_id')
        cores_ids = request.form.getlist('cores')

        # ⚠️ Validação manual antes de salvar
        if not linha_id:
            flash('Você precisa selecionar uma LINHA.', 'danger')
            return render_template('nova_matriz.html', form=form, linhas=linhas, cores=cores)

        if not cores_ids:
            flash('Você precisa selecionar pelo menos uma COR.', 'danger')
            return render_template('nova_matriz.html', form=form, linhas=linhas, cores=cores)

        if form.validate_on_submit():
            nova_matriz = Matriz(
                codigo=form.codigo.data,
                descricao=form.descricao.data,
                tipo=form.tipo.data,
                status=form.status.data,
                capacidade=form.capacidade.data or 0,
                quantidade=form.quantidade.data or 0,
                linha_id=int(linha_id)  # 🔹 converte para int aqui
            )

            # ✅ Salvar imagem se houver
            if form.imagem.data:
                imagem_filename = secure_filename(form.imagem.data.filename)
                upload_path = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path, exist_ok=True)
                caminho_imagem = os.path.join(upload_path, imagem_filename)
                form.imagem.data.save(caminho_imagem)
                nova_matriz.imagem = imagem_filename

            # ✅ Adicionar tamanhos corretamente
            for campo in form.tamanhos.entries:
                nome = campo.form.nome.data.strip() or '--'
                quantidade = campo.form.quantidade.data or 0
                tamanho = TamanhoMatriz(nome=nome, quantidade=quantidade)
                nova_matriz.tamanhos.append(tamanho)

            # ✅ Adicionar cores selecionadas
            cores_selecionadas = Cor.query.filter(Cor.id.in_(cores_ids)).all()
            nova_matriz.cores = cores_selecionadas

            # ✅ Atualiza o total com base nas quantidades dos tamanhos
            nova_matriz.quantidade = nova_matriz.calcular_total_grade()

            db.session.add(nova_matriz)
            db.session.commit()

            flash('Matriz cadastrada com sucesso!', 'success')
            return redirect(url_for('routes.listar_matrizes'))

    return render_template('nova_matriz.html', form=form, linhas=linhas, cores=cores)




# 🔹 Editar Matriz
@bp.route('/matriz/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_matriz(id):
    matriz = Matriz.query.get_or_404(id)
    form = MatrizForm(obj=matriz)

    # Choices para SelectField
    form.status.choices = [('Ativa', 'Ativa'), ('Inativa', 'Inativa')]

    linhas = Linha.query.order_by(Linha.nome).all()
    cores = Cor.query.order_by(Cor.nome).all()

    if request.method == 'GET':
        for i in range(len(form.tamanhos.entries)):
            if i < len(matriz.tamanhos):
                form.tamanhos[i].nome.data = matriz.tamanhos[i].nome
                form.tamanhos[i].quantidade.data = matriz.tamanhos[i].quantidade

    if form.validate_on_submit():
        matriz.codigo = form.codigo.data
        matriz.descricao = form.descricao.data
        matriz.tipo = form.tipo.data
        matriz.status = form.status.data
        matriz.capacidade = form.capacidade.data

        # Linha
        linha_id = request.form.get("linha_id")
        matriz.linha_id = int(linha_id) if linha_id else None

        # Cores
        cores_ids = request.form.getlist("cores")
        matriz.cores = Cor.query.filter(Cor.id.in_(cores_ids)).all()

        # 🔹 Tamanhos - agora organizados!
        matriz.tamanhos = []  # limpa

        tamanhos_preenchidos = []
        tamanhos_vazios = []

        for campo in form.tamanhos:
            nome = campo.nome.data or "--"
            qtd = campo.quantidade.data or 0
            if nome != "--":
                tamanhos_preenchidos.append(TamanhoMatriz(nome=nome, quantidade=qtd))
            else:
                tamanhos_vazios.append(TamanhoMatriz(nome=nome, quantidade=qtd))

        # 🔹 Primeiro salva os preenchidos, depois os vazios
        matriz.tamanhos = tamanhos_preenchidos + tamanhos_vazios

        # Atualiza quantidade total
        matriz.quantidade = matriz.calcular_total_grade()

        # Upload da imagem
        imagem = form.imagem.data
        if imagem:
            filename = secure_filename(imagem.filename)
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            imagem.save(path)
            matriz.imagem = filename

        # 🔹 Salva o log
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou a Matriz: {matriz.codigo}"
        )
        db.session.add(log)

        db.session.commit()
        flash("Matriz atualizada com sucesso!", "success")
        return redirect(url_for('routes.listar_matrizes'))

    return render_template('editar_matriz.html', form=form, matriz=matriz, linhas=linhas, cores=cores)



@bp.route("/relatorio/matriz_tempo_real")
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_matriz_tempo_real():
    from sqlalchemy import func

    totais_linha = db.session.query(
        Linha.nome.label("nome"),
        func.sum(TamanhoMatriz.quantidade).label("total")
    ).select_from(Matriz)\
     .join(Linha, Matriz.linha_id == Linha.id)\
     .join(TamanhoMatriz, TamanhoMatriz.matriz_id == Matriz.id)\
     .group_by(Linha.nome)\
     .order_by(Linha.nome)\
     .all()

    total_geral = sum(item.total or 0 for item in totais_linha)

    return render_template("relatorio_matriz_tempo_real.html", totais_linha=totais_linha, total_geral=total_geral)


@bp.route('/matriz/<int:id>/zerar', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')  # use a permissão que preferir
def zerar_matriz(id):
    matriz = Matriz.query.get_or_404(id)

    # Zera a quantidade de todos os tamanhos
    for tamanho in matriz.tamanhos:
        tamanho.quantidade = 0

    # Zera a quantidade total da matriz
    matriz.quantidade = 0

    # Remove as movimentações da matriz
    movimentacoes = MovimentacaoMatriz.query.filter_by(matriz_id=id).all()
    for mov in movimentacoes:
        db.session.delete(mov)
    
    # 🔹 Salva o log
    log = LogAcao(
        usuario_id=current_user.id,
        usuario_nome=current_user.nome,
        acao=f"Zerou a Matriz: {matriz.codigo}"
    )
    db.session.add(log)

    db.session.commit()
    flash('Todas as movimentações da matriz foram apagadas e os tamanhos zerados.', 'success')
    return redirect(url_for('routes.listar_movimentacoes_matriz'))



# 🔹 Excluir Matriz
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError

@bp.route('/matriz/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_matriz(id):
    from app.models import Matriz, MovimentacaoMatriz, TrocaHorario
    from flask import request, flash, redirect, url_for

    # ✅ Validação CSRF manual
    token = request.form.get('csrf_token')
    try:
        validate_csrf(token)
    except ValidationError:
        flash('Erro de segurança: CSRF token inválido ou ausente.', 'danger')
        return redirect(url_for('routes.listar_matrizes'))

    # ✅ Validação do campo "excluir"
    confirmacao = request.form.get('confirmacao', '').strip().lower()
    if confirmacao != 'excluir':
        flash('Confirmação inválida. Digite "excluir" para confirmar.', 'danger')
        return redirect(url_for('routes.listar_matrizes'))

    matriz = Matriz.query.get_or_404(id)

    # ✅ Verificações
    if MovimentacaoMatriz.query.filter_by(matriz_id=matriz.id).first():
        flash('Não é possível excluir: existem movimentações registradas.', 'danger')
        return redirect(url_for('routes.listar_matrizes'))

    if TrocaHorario.query.filter_by(matriz_id=matriz.id).first():
        flash('Não é possível excluir: existem trocas registradas.', 'danger')
        return redirect(url_for('routes.listar_matrizes'))

    db.session.delete(matriz)
    db.session.commit()
    flash('Matriz excluída com sucesso!', 'success')
    return redirect(url_for('routes.listar_matrizes'))






### CORES DA MATRIZ #####

@bp.route('/matriz/<int:matriz_id>/cores')
@login_required
def obter_cores_por_matriz(matriz_id):
    matriz = Matriz.query.get_or_404(matriz_id)
    cores = [{"id": cor.id, "nome": cor.nome} for cor in matriz.cores]
    return jsonify(cores)

### TAMANHOS DA MATRIZ #####
@bp.route('/matriz/<int:matriz_id>/tamanhos')
def tamanhos_por_matriz(matriz_id):
    matriz = Matriz.query.get_or_404(matriz_id)

    def chave_ordenacao(t):
        try:
            if "/" in t.nome:
                return [int(n) for n in t.nome.split("/")]
            else:
                return [int(t.nome)]
        except ValueError:
            return [float('inf')]  # joga no final se não for número

    tamanhos_ordenados = sorted(matriz.tamanhos, key=chave_ordenacao)

    tamanhos = [{'nome': t.nome, 'quantidade': t.quantidade} for t in tamanhos_ordenados]
    return jsonify(tamanhos)



@bp.route('/movimentacao_matriz/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_movimentacao_matriz():
    form = MovimentacaoMatrizForm()
    matriz_id = request.args.get("matriz_id") or request.form.get("matriz_id")

    matrizes = Matriz.query.order_by(Matriz.id.desc()).all()
    cores = Cor.query.order_by(Cor.nome).all()
    matriz = Matriz.query.get(matriz_id) if matriz_id else None

    if matriz and not form.tamanhos.entries[0].nome.data:
        form.matriz_id.data = matriz.id

        while len(form.tamanhos) > 0:
            form.tamanhos.pop_entry()

        tamanhos_ordenados = sorted(matriz.tamanhos, key=lambda t: t.nome)

        for t in tamanhos_ordenados:
            form.tamanhos.append_entry({
                'nome': t.nome,
                'quantidade': 0
            })



    if not form.validate_on_submit():
        print("Erros no formulário:", form.errors)
    else:

        nova_movimentacao = MovimentacaoMatriz(
            tipo=form.tipo.data,
            motivo=form.motivo.data,
            posicao_estoque=form.posicao_estoque.data,
            matriz_id=form.matriz_id.data,
            cor_id=form.cor_id.data,
            data=datetime.utcnow()
        )

        total_movimento = 0

        for campo in form.tamanhos.entries:
            nome = campo.form.nome.data
            qtd = campo.form.quantidade.data or 0

            if qtd != 0:
                nova_movimentacao.tamanhos_movimentados.append(
                    TamanhoMovimentacao(nome=nome, quantidade=qtd)
                )
                total_movimento += qtd

        # Aplica a movimentação na matriz
        matriz = Matriz.query.get(form.matriz_id.data)
        for campo in form.tamanhos.entries:
            tamanho = next((t for t in matriz.tamanhos if t.nome == campo.form.nome.data), None)
            if tamanho:
                if form.tipo.data == "Entrada":
                    tamanho.quantidade += campo.form.quantidade.data or 0
                else:
                    tamanho.quantidade -= campo.form.quantidade.data or 0

        # Atualiza o campo `quantidade` da matriz
        matriz.quantidade = matriz.calcular_total_grade()

        db.session.add(nova_movimentacao)
        db.session.commit()

        flash("Movimentação registrada com sucesso!", "success")
        return redirect(url_for('routes.listar_movimentacoes_matriz'))

    return render_template(
        'nova_movimentacao_matriz.html',
        form=form,
        matrizes=matrizes,
        cores=cores,
        matriz=matriz
    )

@bp.route('/movimentacoes_matriz', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_movimentacoes_matriz():
    tipo = request.args.get('tipo')
    matriz_id = request.args.get('matriz_id')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    query = MovimentacaoMatriz.query

    if tipo:
        query = query.filter_by(tipo=tipo)
    if matriz_id:
        query = query.filter_by(matriz_id=matriz_id)

    if data_inicio:
        try:
            data_i = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(MovimentacaoMatriz.data >= data_i)
        except:
            pass

    if data_fim:
        try:
            data_f = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(MovimentacaoMatriz.data < data_f)
        except:
            pass

    movimentacoes = query.order_by(MovimentacaoMatriz.data.desc()).all()
    matrizes = Matriz.query.order_by(Matriz.id.desc()).all()


    return render_template('listar_movimentacoes_matriz.html', movimentacoes=movimentacoes, matrizes=matrizes)



@bp.route('/movimentacao_matriz/<int:id>/ver')
@login_required
@requer_permissao('controleproducao', 'ver')
def ver_movimentacao_matriz(id):
    movimentacao = MovimentacaoMatriz.query.get_or_404(id)
    return render_template('ver_movimentacao_matriz.html', movimentacao=movimentacao)

@bp.route('/movimentacao_matriz/<int:id>/excluir', methods=['POST', 'GET'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_movimentacao_matriz(id):
    movimentacao = MovimentacaoMatriz.query.get_or_404(id)

    # ⚠️ Ao excluir a movimentação, desfaz o efeito na matriz
    matriz = movimentacao.matriz
    tipo = movimentacao.tipo

    for item in movimentacao.tamanhos_movimentados:
        tamanho = next((t for t in matriz.tamanhos if t.nome == item.nome), None)
        if tamanho:
            if tipo == "Entrada":
                tamanho.quantidade -= item.quantidade
            else:
                tamanho.quantidade += item.quantidade

    # Atualiza total da matriz
    matriz.quantidade = matriz.calcular_total_grade()

    db.session.delete(movimentacao)
    db.session.commit()
    flash("Movimentação excluída com sucesso!", "success")
    return redirect(url_for('routes.listar_movimentacoes_matriz'))


@bp.route('/relatorio/estoque_matriz', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_estoque_matriz():
    linha_id = request.args.get("linha_id")
    matriz_id = request.args.get("matriz_id")
    tipo_filtro = request.args.get("tipo")

    linhas = Linha.query.order_by(Linha.nome).all()
    matrizes = Matriz.query.order_by(Matriz.codigo).all()

    resultado = []
    tamanhos = []
    total_geral = 0

    matrizes_filtradas = []
    if matriz_id:
        matriz = Matriz.query.get(matriz_id)
        if matriz:
            matrizes_filtradas = [matriz]
    elif linha_id:
        matrizes_filtradas = Matriz.query.filter_by(linha_id=linha_id).all()

    if matrizes_filtradas:
        tamanhos_set = set()
        for matriz in matrizes_filtradas:
            tamanhos_set.update([t.nome for t in matriz.tamanhos if t.nome != '--'])
        tamanhos = sorted(tamanhos_set)

        for matriz in matrizes_filtradas:
            for cor in matriz.cores:
                linha_dados = {
                    'codigo': matriz.codigo,
                    'matriz': matriz.id,
                    'cor': cor.nome,
                    'tamanhos': {},
                    'total': 0
                }

                for tamanho in tamanhos:
                    if tipo_filtro == "Entrada":
                        qtd_total = db.session.query(
                            db.func.sum(TamanhoMovimentacao.quantidade)
                        ).join(MovimentacaoMatriz).filter(
                            MovimentacaoMatriz.matriz_id == matriz.id,
                            MovimentacaoMatriz.cor_id == cor.id,
                            TamanhoMovimentacao.nome == tamanho,
                            MovimentacaoMatriz.tipo == "Entrada"
                        )
                    elif tipo_filtro == "Saída":
                        qtd_total = db.session.query(
                            db.func.sum(TamanhoMovimentacao.quantidade)
                        ).join(MovimentacaoMatriz).filter(
                            MovimentacaoMatriz.matriz_id == matriz.id,
                            MovimentacaoMatriz.cor_id == cor.id,
                            TamanhoMovimentacao.nome == tamanho,
                            MovimentacaoMatriz.tipo == "Saída"
                        )
                    else:
                        qtd_total = db.session.query(
                            db.func.sum(
                                case(
                                    (MovimentacaoMatriz.tipo == 'Entrada', TamanhoMovimentacao.quantidade),
                                    (MovimentacaoMatriz.tipo == 'Saída', -TamanhoMovimentacao.quantidade),
                                    else_=0
                                )
                            )
                        ).join(MovimentacaoMatriz).filter(
                            MovimentacaoMatriz.matriz_id == matriz.id,
                            MovimentacaoMatriz.cor_id == cor.id,
                            TamanhoMovimentacao.nome == tamanho
                        )

                    qtd = qtd_total.scalar() or 0
                    linha_dados['tamanhos'][tamanho] = qtd
                    linha_dados['total'] += qtd

                resultado.append(linha_dados)
                total_geral += linha_dados['total']

    return render_template(
        'relatorio_estoque_matriz.html',
        linhas=linhas,
        matrizes=matrizes,
        resultado=resultado,
        tamanhos=tamanhos,
        total_geral=total_geral
    )







@bp.route('/funcionarios', methods=['GET'])
@login_required
@requer_permissao('funcionario', 'ver')
def listar_funcionarios():
    funcionarios = Funcionario.query.order_by(Funcionario.nome).all()
    return render_template('funcionarios.html', funcionarios=funcionarios)

@bp.route('/funcionario/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('funcionario', 'criar')
def novo_funcionario():
    form = FuncionarioForm()
    form.setor_id.choices = [(s.id, s.nome) for s in Setor.query.order_by(Setor.nome).all()]
    
    if form.validate_on_submit():
        novo_funcionario = Funcionario(
            nome=form.nome.data,
            funcao=form.funcao.data,
            setor_id = form.setor_id.data
        )
        db.session.add(novo_funcionario)
        db.session.commit()
        flash("Funcionário cadastrado com sucesso!", "success")
        return redirect(url_for('routes.listar_funcionarios'))
    return render_template('novo_funcionario.html', form=form)



@bp.route('/funcionario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('funcionario', 'editar')
def editar_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    form = FuncionarioForm(obj=funcionario)
    form.setor_id.choices = [(s.id, s.nome) for s in Setor.query.order_by(Setor.nome).all()]

    if form.validate_on_submit():
        funcionario.nome = form.nome.data
        funcionario.funcao = form.funcao.data
        funcionario.setor_id = form.setor_id.data
        db.session.commit()
        flash("Funcionário atualizado!", "success")
        return redirect(url_for('routes.listar_funcionarios'))
    
    return render_template('editar_funcionario.html', form=form, funcionario=funcionario)

@bp.route('/funcionario/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('funcionario', 'excluir')
def excluir_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    db.session.delete(funcionario)
    db.session.commit()
    flash("Funcionário removido!", "success")
    return redirect(url_for('routes.listar_funcionarios'))


# Listar
@bp.route('/setores')
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_setores():
    setores = Setor.query.order_by(Setor.id.asc()).all()
    return render_template('listar_setores.html', setores=setores)

# Criar
@bp.route('/setores/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def novo_setor():
    form = SetorForm()
    if form.validate_on_submit():
        setor = Setor(nome=form.nome.data)
        db.session.add(setor)
        db.session.commit()
        flash('Setor criado com sucesso!', 'success')
        return redirect(url_for('routes.listar_setores'))
    return render_template('novo_setor.html', form=form)

# Editar
@bp.route('/setores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_setor(id):
    setor = Setor.query.get_or_404(id)
    form = SetorForm(obj=setor)
    if form.validate_on_submit():
        setor.nome = form.nome.data
        db.session.commit()
        flash('Setor atualizado com sucesso!', 'success')
        return redirect(url_for('routes.listar_setores'))
    return render_template('editar_setor.html', form=form, setor=setor)

# Excluir
@bp.route('/setores/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_setor(id):
    setor = Setor.query.get_or_404(id)
    db.session.delete(setor)
    db.session.commit()
    flash('Setor excluído com sucesso!', 'success')
    return redirect(url_for('routes.listar_setores'))





# ROTA OTIMIZADA
@bp.route('/OrdemCompras')
@login_required
@requer_permissao('administrativo', 'ver')
def listar_ordemCompras():
    form = OrdemCompraForm()
    oc_query = OrdemCompra.query.options(
        db.joinedload(OrdemCompra.solicitante),
        db.joinedload(OrdemCompra.responsavel)
    ).order_by(OrdemCompra.id.desc()).all()

    return render_template(
        'listar_ordemCompras.html',
        ordemcompras=oc_query,
        status_choices=form.status.choices,
        prioridade_choices=form.prioridade.choices,
        setor_choices=form.setor.choices,
        form=form
    )

@bp.route('/OrdemComprasKanban')
@login_required
@requer_permissao('administrativo', 'ver')
def listar_ordemComprasKanban():
    form = OrdemCompraForm()
    oc_query = OrdemCompra.query.options(
        db.joinedload(OrdemCompra.solicitante),
        db.joinedload(OrdemCompra.responsavel)
    ).all()

    # Agrupar por status dinamicamente com base no form
    ordemcompras_por_status = {status[0]: [] for status in form.status.choices}
    for oc in oc_query:
        ordemcompras_por_status.get(oc.status, []).append(oc)

    return render_template(
        'listar_ordemCompras_kanban.html',
        ordemcompras_por_status=ordemcompras_por_status,
        form=form
    )



@bp.route("/ordemCompras/exportar")
@login_required
def exportar_ordemCompras_excel():

    Solicitante = aliased(Funcionario)
    Responsavel = aliased(Funcionario)

    ordemcompras = (
        db.session.query(
            OrdemCompra.id,
            OrdemCompra.titulo,
            OrdemCompra.nota_fiscal,
            OrdemCompra.status,
            OrdemCompra.setor,
            OrdemCompra.prioridade,
            Solicitante.nome.label("Solicitante"),
            Responsavel.nome.label("Responsavel")
        )
        .join(Solicitante, OrdemCompra.solicitante_id == Solicitante.id)
        .join(Responsavel, OrdemCompra.responsavel_id == Responsavel.id)
        .all()
    )

    # Criar DataFrame
    df = pd.DataFrame(ordemcompras, columns=["id", "titulo", "nota fiscal",
                                              "status", "setor", "prioridade",
                                                "solicitante", "Responsavel"])

    # Exportar para Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ordens_Compras')
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="oc.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@bp.route('/ordemCompra/ver/<int:id>')
@login_required
@requer_permissao('administrativo', 'ver')
def ver_ordemCompra(id):
    ordemcompra = OrdemCompra.query.get_or_404(id)
    return render_template('ver_ordemCompra.html', ordemcompra=ordemcompra)


@bp.route('/ordemCompra/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('administrativo', 'criar')
def nova_ordemCompra():
    form = OrdemCompraForm()
    funcionarios = Funcionario.query.all()
    responsaveis = Funcionario.query.filter_by(funcao='Compras').all()


    if form.validate_on_submit():
        ordemcompra = OrdemCompra(
            titulo=form.titulo.data,
            nota_fiscal=form.nota_fiscal.data or '-',
            status=form.status.data,
            setor=form.setor.data,
            prioridade=form.prioridade.data,
            solicitante_id=request.form.get("solicitante_id") or None,
            responsavel_id=request.form.get("responsavel_id") or None,
            descricao=form.descricao.data,
            valor = form.valor.data or 0
        )


        db.session.add(ordemcompra)
        db.session.commit()
        flash("Manutenção cadastrada com sucesso!", "success")
        return redirect(url_for('routes.listar_ordemCompras'))

    return render_template(
        'nova_ordemCompra.html',
        form=form,
        funcionarios=funcionarios,
        responsaveis=responsaveis  # 🔹 Passa os funcionários pro template
    )



@bp.route('/ordemCompra/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('administrativo', 'editar')
def editar_ordemCompra(id):
    ordemcompra = OrdemCompra.query.get_or_404(id)
    form = OrdemCompraForm()

    funcionarios = Funcionario.query.all()

    if form.validate_on_submit():
        
        #Bloqueio no POST caso já esteja finalizada
        if ordemcompra.status == "Finalizado":
            flash("Esta O.C está finalizada e não pode mais ser alterada.", "warning")
            return redirect(url_for('routes.listar_ordemCompras'))
        
        status_anterior = ordemcompra.status
        ordemcompra.titulo = form.titulo.data
        ordemcompra.nota_fiscal = form.nota_fiscal.data or '-'
        ordemcompra.status = form.status.data
        ordemcompra.setor = form.setor.data
        ordemcompra.prioridade = form.prioridade.data
        ordemcompra.solicitante_id = request.form.get("solicitante_id") or ordemcompra.solicitante_id
        ordemcompra.responsavel_id = request.form.get("responsavel_id") or ordemcompra.responsavel_id
        ordemcompra.descricao = form.descricao.data
        ordemcompra.valor = form.valor.data or 0

        # Só gera a data_fim se o status tiver sido ALTERADO para Finalizado
        if status_anterior != "Finalizado" and ordemcompra.status == "Finalizado":
            ordemcompra.data_fim = datetime.now().replace(microsecond=0)

        db.session.commit()

        flash("Ordem de Compra atualizada com sucesso!", "success")
        return redirect(url_for('routes.listar_ordemCompras'))
    else:
        print("Erro")
        print(form.errors)

    # Pré-carregar o form
    form.titulo.data = ordemcompra.titulo
    form.nota_fiscal.data = ordemcompra.nota_fiscal
    form.status.data = ordemcompra.status
    form.setor.data = ordemcompra.setor
    form.prioridade.data = ordemcompra.prioridade
    form.descricao.data = ordemcompra.descricao
    form.valor.data = ordemcompra.valor

    return render_template(
        'editar_ordemCompra.html',
        form=form,
        ordemcompra=ordemcompra,
        funcionarios=funcionarios
    )

@bp.route('/ordemCompra/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('administrativo', 'excluir')
def excluir_ordemCompra(id):
    ordemcompra = OrdemCompra.query.get_or_404(id)

    db.session.delete(ordemcompra)
    db.session.commit()
    flash("Ordem de compra excluída com sucesso!", "success")
    return redirect(url_for('routes.listar_ordemCompras'))


from sqlalchemy import func, or_

@bp.route("/manutencoes", methods=["GET"])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_manutencoes():
    from app.models import Manutencao, Funcionario, Setor  # ajuste import

    # Responsáveis SOMENTE do setor MANUTENÇÃO (por nome) OU setor_id == 2
    responsaveis = (
        Funcionario.query
        .join(Setor, Funcionario.setor_id == Setor.id)
        .filter(
            or_(
                func.upper(Setor.nome) == 'MANUTENCAO',  # ou 'MANUTENÇÃO' se preferir com acento
                Setor.id == 2
            )
        )
        .order_by(Funcionario.nome.asc())
        .all()
    )

    # ids válidos (para evitar filtrar por alguém fora do setor Manutenção)
    ids_responsaveis_validos = {r.id for r in responsaveis}

    responsavel_id = request.args.get("responsavel_id", type=int)

    # Base query
    q = Manutencao.query

    # Só aplica o filtro se o id estiver dentro do conjunto permitido
    if responsavel_id and responsavel_id in ids_responsaveis_validos:
        q = q.filter(Manutencao.responsavel_id == responsavel_id)

    # Carrega já filtradas/ordenadas
    itens = q.order_by(Manutencao.id.desc()).all()

    # Agrupa por status
    grupos = {"Aberto": [], "Verificando": [], "Finalizado": []}
    for m in itens:
        grupos.setdefault(m.status, []).append(m)

    # Contadores de prioridades por status
    prioridades = {}
    for status, lista in grupos.items():
        cont = {"Urgente": 0, "Alta": 0, "Normal": 0, "Baixa": 0}
        for m in lista:
            if m.prioridade in cont:
                cont[m.prioridade] += 1
        prioridades[status] = cont

    return render_template(
        "listar_manutencoes.html",
        manutencoes=grupos,
        prioridades=prioridades,
        responsaveis=responsaveis,  # <-- já filtrados
        responsavel_id_selecionado=responsavel_id if responsavel_id in ids_responsaveis_validos else None
    )





@bp.route('/manutencao/ver/<int:id>')
@login_required
@requer_permissao('manutencao', 'ver')
def ver_manutencao(id):
    manutencao = Manutencao.query.options(
        db.joinedload(Manutencao.solicitante),
        db.joinedload(Manutencao.responsavel),
        db.joinedload(Manutencao.maquinas).joinedload(ManutencaoMaquina.maquina),
        db.joinedload(Manutencao.pecas).joinedload(ManutencaoPeca.peca)
    ).get_or_404(id)

    return render_template(
        'ver_manutencao.html',
        manutencao=manutencao
    )


# ROTA nova_manutencao
from sqlalchemy import func, or_

@bp.route('/manutencao/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('manutencao', 'criar')
def nova_manutencao():
    form = ManutencaoForm()

    # Máquinas e peças (sem filtro)
    maquinas = Maquina.query.order_by(Maquina.codigo).all()
    pecas = Peca.query.order_by(Peca.descricao).all()

    # Solicitante: todos os funcionários (sem filtro)
    funcionarios_solicitantes = Funcionario.query.order_by(Funcionario.nome).all()

    # Responsável: SOMENTE quem é do setor MANUTENÇÃO (por nome) OU setor_id == 2
    funcionarios_responsaveis = (
        Funcionario.query
        .join(Setor, Funcionario.setor_id == Setor.id)
        .filter(
            or_(
                func.upper(Setor.nome) == 'MANUTENCAO',   # compara pelo nome (em maiúsculas)
                Setor.id == 2                             # ou pelo id 2
            )
        )
        .order_by(Funcionario.nome)
        .all()
    )

    if form.validate_on_submit():
        manutencao = Manutencao(
            titulo=form.titulo.data,
            status=form.status.data,
            tipo=form.tipo.data,
            prioridade=form.prioridade.data,
            solicitante_id=request.form.get("solicitante_id") or None,
            responsavel_id=request.form.get("responsavel_id") or None,
            descricao=form.descricao.data
        )
        db.session.add(manutencao)
        db.session.flush()  # garante ID para vinculações

        # Vincula máquinas
        for maquina_id in request.form.getlist('maquina_id[]'):
            db.session.add(ManutencaoMaquina(
                manutencao_id=manutencao.id,
                maquina_id=int(maquina_id)
            ))

        # Vincula peças
        for peca_id in request.form.getlist('peca_id[]'):
            db.session.add(ManutencaoPeca(
                manutencao_id=manutencao.id,
                peca_id=int(peca_id)
            ))

        db.session.commit()
        flash("Manutenção cadastrada com sucesso!", "success")
        return redirect(url_for('routes.listar_manutencoes'))

    return render_template(
        'nova_manutencao.html',
        form=form,
        maquinas=maquinas,
        pecas=pecas,
        funcionarios_solicitantes=funcionarios_solicitantes,  # todos
        funcionarios_responsaveis=funcionarios_responsaveis    # filtrados (MANUTENÇÃO)
    )


# rota de editar manutenção com carregamento de máquinas, componentes e funcionários corretamente
@bp.route('/manutencao/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('manutencao', 'editar')
def editar_manutencao(id):
    manutencao = Manutencao.query.get_or_404(id)
    form = ManutencaoForm()

    maquinas = Maquina.query.all()
    pecas = Peca.query.all()

    # Solicitante: todos os funcionários (sem filtro)
    funcionarios_solicitantes = Funcionario.query.order_by(Funcionario.nome).all()

    # Responsável: SOMENTE quem é do setor MANUTENÇÃO (por nome) OU setor_id == 2
    funcionarios_responsaveis = (
        Funcionario.query
        .join(Setor, Funcionario.setor_id == Setor.id)
        .filter(
            or_(
                func.upper(Setor.nome) == 'MANUTENCAO',   # compara pelo nome (em maiúsculas)
                Setor.id == 2                             # ou pelo id 2
            )
        )
        .order_by(Funcionario.nome)
        .all()
    )

    if form.validate_on_submit():
        
        #Bloqueio no POST caso já esteja finalizada
        if manutencao.status == "Finalizado":
            flash("Esta manutenção está finalizada e não pode mais ser alterada.", "warning")
            return redirect(url_for('routes.listar_manutencoes'))
        
        status_anterior = manutencao.status
        manutencao.titulo = form.titulo.data
        manutencao.status = form.status.data
        print("VALOR STATUS:", manutencao.status)
        print("FORM STATUS CHOICES:", form.status.choices)

        manutencao.tipo = form.tipo.data
        manutencao.prioridade = form.prioridade.data
        manutencao.solicitante_id = request.form.get("solicitante_id") or manutencao.solicitante_id
        manutencao.responsavel_id = request.form.get("responsavel_id") or manutencao.responsavel_id

        manutencao.descricao = form.descricao.data
        
        # Só gera a data_fim se o status tiver sido ALTERADO para Finalizado
        if status_anterior != "Finalizado" and manutencao.status == "Finalizado":
            manutencao.data_fim = datetime.now().replace(microsecond=0)



        # Limpa as ligações anteriores
        ManutencaoMaquina.query.filter_by(manutencao_id=manutencao.id).delete()
        ManutencaoPeca.query.filter_by(manutencao_id=manutencao.id).delete()

        # Reinsere máquinas
        for maquina_id in request.form.getlist('maquina_id[]'):
            db.session.add(ManutencaoMaquina(
                manutencao_id=manutencao.id,
                maquina_id=int(maquina_id)
            ))

        
        # Reinsere pecas
        for peca_id in request.form.getlist('peca_id[]'):
            db.session.add(ManutencaoPeca(
                manutencao_id=manutencao.id,
                peca_id=int(peca_id)
            ))

        db.session.commit()
        flash("Manutenção atualizada com sucesso!", "success")
        return redirect(url_for('routes.listar_manutencoes'))

    # Pré-carregar o form
    form.titulo.data = manutencao.titulo
    form.status.data = manutencao.status
    form.tipo.data = manutencao.tipo
    form.prioridade.data = manutencao.prioridade
    form.descricao.data = manutencao.descricao

    return render_template(
        'editar_manutencao.html',
        form=form,
        manutencao=manutencao,
        maquinas=maquinas,
        funcionarios_solicitantes=funcionarios_solicitantes, #todos
        funcionarios_responsaveis=funcionarios_responsaveis, #filtrados pela manutencao
        pecas = pecas
    )



@bp.route('/manutencao/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('manutencao', 'excluir')
def excluir_manutencao(id):
    manutencao = Manutencao.query.get_or_404(id)

    # Remove máquinas e componentes vinculados
    ManutencaoMaquina.query.filter_by(manutencao_id=manutencao.id).delete()
    ManutencaoPeca.query.filter_by(manutencao_id=manutencao.id).delete()

    db.session.delete(manutencao)
    db.session.commit()
    flash("Manutenção excluída com sucesso!", "success")
    return redirect(url_for('routes.listar_manutencoes'))

from datetime import datetime, timedelta

@bp.route('/manutencao/relatorio', methods=['GET'])
@login_required
@requer_permissao('manutencao', 'ver')
def relatorio_manutencoes():
    funcionarios = Funcionario.query.all()

    filtros = {
        "id": request.args.get('id'),
        "status": request.args.get('status'),
        "prioridade": request.args.get('prioridade'),
        "responsavel_id": request.args.get('responsavel_id'),
        "solicitante_id": request.args.get('solicitante_id'),
        "data_inicio_de": request.args.get('data_inicio_de'),
        "data_inicio_ate": request.args.get('data_inicio_ate'),
        "data_fim_de": request.args.get('data_fim_de'),
        "data_fim_ate": request.args.get('data_fim_ate')
    }

    manutencoes = []

    if request.args:
        query = Manutencao.query
        if filtros["id"]:
            query = query.filter(Manutencao.id == int(filtros["id"]))
        if filtros["status"]:
            query = query.filter(Manutencao.status == filtros["status"])
        if filtros["prioridade"]:
            query = query.filter(Manutencao.prioridade == filtros["prioridade"])
        if filtros["responsavel_id"]:
            query = query.filter(Manutencao.responsavel_id == int(filtros["responsavel_id"]))
        if filtros["solicitante_id"]:
            query = query.filter(Manutencao.solicitante_id == int(filtros["solicitante_id"]))
        
        # Filtro Data Início
        if filtros["data_inicio_de"]:
            query = query.filter(Manutencao.data_inicio >= filtros["data_inicio_de"])
        if filtros["data_inicio_ate"]:
            data_ate = datetime.strptime(filtros["data_inicio_ate"], '%Y-%m-%d') + timedelta(hours=23, minutes=59, seconds=59)
            query = query.filter(Manutencao.data_inicio <= data_ate)

        # Filtro Data Fim
        if filtros["data_fim_de"]:
            query = query.filter(Manutencao.data_fim >= filtros["data_fim_de"])
        if filtros["data_fim_ate"]:
            data_fim_ate = datetime.strptime(filtros["data_fim_ate"], '%Y-%m-%d') + timedelta(hours=23, minutes=59, seconds=59)
            query = query.filter(Manutencao.data_fim <= data_fim_ate)
            
        # ✅ Ordenação pelo mais recente
        query = query.order_by(Manutencao.id.desc())

        manutencoes = query.all()

    return render_template(
        'relatorio_manutencoes.html',
        manutencoes=manutencoes,
        funcionarios=funcionarios,
        filtros=filtros, data_emissao=datetime.now()
    )


@bp.route('/manutencao/relatorio-pecas', methods=['GET', 'POST'])
@login_required
@requer_permissao('manutencao', 'ver')
def relatorio_pecas_manutencao():
    manutencoes = Manutencao.query.order_by(Manutencao.id.desc()).all()
    resultado = {}
    total_geral = 0

    if request.method == 'POST':
        manutencao_ids = request.form.getlist('manutencoes[]')
        if manutencao_ids:
            for mid in manutencao_ids:
                manutencao = Manutencao.query.get(int(mid))
                
                pecas = db.session.query(
                    Peca.codigo,
                    Peca.descricao,
                    Peca.preco
                ).join(ManutencaoPeca, Peca.id == ManutencaoPeca.peca_id) \
                 .filter(ManutencaoPeca.manutencao_id == mid).all()

                subtotal = sum([float(p[2]) for p in pecas]) if pecas else 0
                total_geral += subtotal

                resultado[manutencao] = {
                    "pecas": pecas,
                    "subtotal": subtotal
                }

    return render_template('relatorio_pecas_manutencao.html',
                           manutencoes=manutencoes, resultado=resultado,
                           total_geral=total_geral, data_emissao=datetime.now())




### COR  #####

@bp.route('/cores', methods=['GET'])
@login_required
@requer_permissao('desenvolvimento', 'ver')
def listar_cores():
    cores = Cor.query.order_by(Cor.id).all()
    return render_template('listar_cores.html', cores=cores)

@bp.route('/cor/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('desenvolvimento', 'criar')
def nova_cor():
    form = CorForm()
    if form.validate_on_submit():
        nova_cor = Cor(
            nome=form.nome.data
        )
        db.session.add(nova_cor)
        db.session.commit()
        flash("Cor cadastrada com sucesso!", "success")
        return redirect(url_for('routes.listar_cores'))
    return render_template('nova_cor.html', form=form)



@bp.route('/cor/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('desenvolvimento', 'editar')
def editar_cor(id):
    cor = Cor.query.get_or_404(id)
    form = CorForm(obj=cor)

    if form.validate_on_submit():
        cor.nome = form.nome.data

        db.session.commit()
        flash("Cor atualizada!", "success")
        return redirect(url_for('routes.listar_cores'))
    
    return render_template('editar_cor.html', form=form, cor=cor)

@bp.route('/cor/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('desenvolvimento', 'excluir')
def excluir_cor(id):
    cor = Cor.query.get_or_404(id)

    db.session.delete(cor)
    db.session.commit()

    flash("Cor removido!", "success")
    return redirect(url_for('routes.listar_cores'))


#### LINHA ####

### COR  #####

@bp.route('/linhas', methods=['GET'])
@login_required
@requer_permissao('desenvolvimento', 'ver')
def listar_linhas():
    linhas = Linha.query.order_by(Linha.id).all()
    return render_template('listar_linhas.html', linhas=linhas)

@bp.route('/linha/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('desenvolvimento', 'criar')
def nova_linha():
    form = LinhaForm()
    if form.validate_on_submit():
        nova_linha = Linha(
            nome=form.nome.data,
            grupo=form.grupo.data
        )
        db.session.add(nova_linha)
        db.session.commit()
        flash("Linha cadastrada com sucesso!", "success")
        return redirect(url_for('routes.listar_linhas'))
    return render_template('nova_linha.html', form=form)



@bp.route('/linha/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('desenvolvimento', 'editar')
def editar_linha(id):
    linha = Linha.query.get_or_404(id)
    form = LinhaForm(obj=linha)

    if form.validate_on_submit():
        linha.nome = form.nome.data
        linha.grupo = form.grupo.data

        db.session.commit()
        flash("Linha atualizada!", "success")
        return redirect(url_for('routes.listar_linhas'))
    
    return render_template('editar_linha.html', form=form, linha=linha)

@bp.route('/linha/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('desenvolvimento', 'excluir')
def excluir_linha(id):
    linha = Linha.query.get_or_404(id)

    db.session.delete(linha)
    db.session.commit()

    flash("Linha removida!", "success")
    return redirect(url_for('routes.listar_linhas'))



@bp.route('/grades')
@login_required
def listar_grades():
    grades = Grade.query.order_by(Grade.descricao).all()
    return render_template('listar_grades.html', grades=grades)

@bp.route('/grade/ver/<int:id>')
@login_required
def ver_grade(id):
    grade = Grade.query.get_or_404(id)
    tamanhos_ordenados = sorted(grade.tamanhos, key=lambda t: t.nome)
    return render_template('ver_grade.html', grade=grade, tamanhos=tamanhos_ordenados)


# routes.py
@bp.route('/grade/nova', methods=['GET', 'POST'])
@login_required
def nova_grade():
    form = GradeForm()

    if form.validate_on_submit():
        nova_grade = Grade(descricao=form.descricao.data)

        for campo in form.tamanhos:
            tamanho = TamanhoGrade(
                nome=campo.nome.data,
                quantidade=campo.quantidade.data or 0
            )
            nova_grade.tamanhos.append(tamanho)

        db.session.add(nova_grade)
        db.session.commit()

        flash('Grade salva com sucesso!', 'success')
        return redirect(url_for('routes.listar_grades'))

    return render_template('nova_grade.html', form=form)




@bp.route('/grade/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_grade(id):
    grade = Grade.query.get_or_404(id)
    form = GradeForm(obj=grade)

    if request.method == 'GET':
        for i in range(len(form.tamanhos.entries)):
            if i < len(grade.tamanhos):
                form.tamanhos[i].nome.data = grade.tamanhos[i].nome
                form.tamanhos[i].quantidade.data = grade.tamanhos[i].quantidade

    if form.validate_on_submit():
        grade.descricao = form.descricao.data
        grade.tamanhos = []
        for campo in form.tamanhos:
            tamanho = TamanhoGrade(
                nome=campo.nome.data,
                quantidade=campo.quantidade.data or 0
            )
            grade.tamanhos.append(tamanho)

        db.session.commit()
        flash('Grade atualizada com sucesso!', 'success')
        return redirect(url_for('routes.listar_grades'))

    return render_template('editar_grade.html', form=form)


@bp.route('/grade/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_grade(id):
    grade = Grade.query.get_or_404(id)
    db.session.delete(grade)
    db.session.commit()
    flash('Grade excluída com sucesso!', 'success')
    return redirect(url_for('routes.listar_grades'))




#### PLANEJAMENTO DE PRODUÇÃO ######

@bp.route('/remessas')
@login_required
@requer_permissao('ppcp', 'ver')
def listar_remessas():
    remessas = Remessa.query.order_by(Remessa.data_criacao.desc()).all()
    delete_form = DeleteForm()
    return render_template('listar_remessas.html', remessas=remessas, delete_form=delete_form)


@bp.route('/remessa/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('ppcp', 'criar')
def nova_remessa():
    form = RemessaForm()
    if form.validate_on_submit():
        remessa = Remessa(
            codigo=form.codigo.data,
            descricao=form.descricao.data or '-'
                          )
        db.session.add(remessa)
        db.session.commit()
        flash('Remessa criada com sucesso!', 'success')
        return redirect(url_for('routes.listar_remessas'))
    return render_template('nova_remessa.html', form=form)

@bp.route('/remessa/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('ppcp', 'editar')
def editar_remessa(id):
    remessa = Remessa.query.get_or_404(id)
    form = RemessaForm(obj=remessa)

    if form.validate_on_submit():
        remessa.codigo = form.codigo.data
        remessa.descricao = form.descricao.data or '-'

        # Se o usuário tentou preencher a data de fechamento
        if form.data_fechamento.data:
            # 🔹 Buscar todos os planejamentos ligados a essa remessa
            planejamentos = PlanejamentoProducao.query.filter_by(remessa_id=remessa.id).all()

            # 🔹 Verificar quais planejamentos ainda estão abertos
            planejamentos_abertos = [p for p in planejamentos if not p.fechado]

            if planejamentos_abertos:
                # Ainda tem planejamentos abertos - Não permite fechar
                refs_abertas = ', '.join(p.referencia for p in planejamentos_abertos)
                flash(f'Não é possível fechar a remessa. Existem planejamentos abertos: {refs_abertas}', 'danger')
                return redirect(url_for('routes.editar_remessa', id=remessa.id))
            else:
                # 🔹 Todos fechados, pode salvar a data de fechamento
                remessa.data_fechamento = form.data_fechamento.data

        else:
            # Se não preencher data, mantém vazio
            remessa.data_fechamento = None

        db.session.commit()
        flash('Remessa atualizada com sucesso!', 'success')
        return redirect(url_for('routes.listar_remessas'))

    return render_template('editar_remessa.html', form=form, remessa=remessa)


@bp.route('/remessa/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('ppcp', 'excluir')
def excluir_remessa(id):
    form = DeleteForm()
    
    if not form.validate_on_submit():
        flash('Erro de segurança: CSRF token inválido ou ausente.', 'danger')
        return redirect(url_for('routes.listar_remessas'))

    confirmacao = request.form.get('confirmacao', '').strip().lower()
    if confirmacao != 'excluir':
        flash('Confirmação inválida. Digite "excluir" para confirmar a exclusão.', 'danger')
        return redirect(url_for('routes.listar_remessas'))

    # Só agora acessamos a remessa, com CSRF já validado
    remessa = Remessa.query.get_or_404(id)

    planejamentos = PlanejamentoProducao.query.filter_by(remessa_id=id).all()
    for planejamento in planejamentos:
        db.session.delete(planejamento)

    db.session.delete(remessa)

    log = LogAcao(
        usuario_id=current_user.id,
        usuario_nome=current_user.nome,
        acao=f"Excluiu a Remessa: {remessa.codigo}"
    )
    db.session.add(log)

    db.session.commit()

    flash('Remessa e tudo de origem (planejamentos, prod, fat) da mesma foram excluídos com sucesso.', 'success')
    return redirect(url_for('routes.listar_remessas'))




### PLANEJAMENTOS ######

@bp.route('/planejamentos')
@login_required
@requer_permissao('ppcp', 'ver')
def listar_planejamentos():
    remessa_ids = request.args.getlist('remessa_id')
    status = request.args.get('status')

    planejamentos = []
    grupos = {
        'GRUPO_REF_01': [],
        'GRUPO_REF_02': [],
        'GRUPO_REF_03': []
    }
    total_por_grupo = {
        'GRUPO_REF_01': 0,
        'GRUPO_REF_02': 0,
        'GRUPO_REF_03': 0
    }

    if remessa_ids:  # Só busca se o usuário filtrou
        planejamentos_query = PlanejamentoProducao.query.order_by(PlanejamentoProducao.id.asc())

        # 🔹 Se a pessoa escolher "todas", ignora filtro de remessa
        if 'todas' not in remessa_ids:
            planejamentos_query = planejamentos_query.filter(PlanejamentoProducao.remessa_id.in_([int(rid) for rid in remessa_ids]))

        # 🔹 Filtro por status
        if status == 'fechado':
            planejamentos_query = planejamentos_query.filter_by(fechado=True)
        elif status == 'aberto':
            planejamentos_query = planejamentos_query.filter_by(fechado=False)

        planejamentos = planejamentos_query.all()

        # 🔹 Organizar em grupos
        for p in planejamentos:
            grupo = p.linha.grupo if p.linha and p.linha.grupo in grupos else 'GRUPO_REF_01'
            grupos[grupo].append(p)
            total_por_grupo[grupo] += p.quantidade

    total_geral = sum(total_por_grupo.values())
    remessas = Remessa.query.order_by(Remessa.id.desc()).all()

    return render_template(
        'listar_planejamentos.html',
        grupos=grupos,
        totais=total_por_grupo,
        total_geral=total_geral,
        remessas=remessas
    )


@bp.route('/relatorio_planejamentos_pdf')
@login_required
@requer_permissao('ppcp', 'ver')
def relatorio_planejamentos_pdf():
    remessa_ids = request.args.getlist('remessa_id')
    status = request.args.get('status')

    planejamentos_query = PlanejamentoProducao.query.order_by(PlanejamentoProducao.id.asc())
    if 'todas' not in remessa_ids:
        planejamentos_query = planejamentos_query.filter(PlanejamentoProducao.remessa_id.in_([int(rid) for rid in remessa_ids]))
    if status == 'fechado':
        planejamentos_query = planejamentos_query.filter_by(fechado=True)
    elif status == 'aberto':
        planejamentos_query = planejamentos_query.filter_by(fechado=False)

    planejamentos = planejamentos_query.all()

    grupos = {'GRUPO_REF_01': [], 'GRUPO_REF_02': [], 'GRUPO_REF_03': []}
    totais = {'GRUPO_REF_01': 0, 'GRUPO_REF_02': 0, 'GRUPO_REF_03': 0}

    for p in planejamentos:
        grupo = p.linha.grupo if p.linha and p.linha.grupo in grupos else 'GRUPO_REF_01'
        grupos[grupo].append(p)
        totais[grupo] += p.quantidade

    total_geral = sum(totais.values())
    remessas = Remessa.query.order_by(Remessa.codigo).all()

    # 🔹 Criar lista de linhas unificadas (mesmo número de linhas por grupo)
    max_linhas = max(len(grupos['GRUPO_REF_01']), len(grupos['GRUPO_REF_02']), len(grupos['GRUPO_REF_03']))
    linhas_unificadas = []

    for i in range(max_linhas):
        linha = {
            'GRUPO_REF_01': grupos['GRUPO_REF_01'][i] if i < len(grupos['GRUPO_REF_01']) else None,
            'GRUPO_REF_02': grupos['GRUPO_REF_02'][i] if i < len(grupos['GRUPO_REF_02']) else None,
            'GRUPO_REF_03': grupos['GRUPO_REF_03'][i] if i < len(grupos['GRUPO_REF_03']) else None,
        }
        linhas_unificadas.append(linha)

    html_content = render_template(
        'relatorio_planejamentos_pdf.html',
        linhas=linhas_unificadas,
        totais=totais,
        total_geral=total_geral,
        remessas=remessas,
        request=request
    )

    pdf = HTML(string=html_content).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=relatorio_planejamento.pdf'
    return response


@bp.route('/relatorio_planejamentos')
@login_required
@requer_permissao('ppcp', 'ver')
def relatorio_planejamentos():
    remessa_ids = request.args.getlist('remessa_id')
    status = request.args.get('status')

    grupos = {
        'GRUPO_REF_01': [],
        'GRUPO_REF_02': [],
        'GRUPO_REF_03': []
    }
    total_por_grupo = {
        'GRUPO_REF_01': 0,
        'GRUPO_REF_02': 0,
        'GRUPO_REF_03': 0
    }

    if remessa_ids:
        planejamentos_query = PlanejamentoProducao.query.order_by(PlanejamentoProducao.id.asc())

        if 'todas' not in remessa_ids:
            planejamentos_query = planejamentos_query.filter(
                PlanejamentoProducao.remessa_id.in_([int(rid) for rid in remessa_ids])
            )

        if status == 'fechado':
            planejamentos_query = planejamentos_query.filter_by(fechado=True)
        elif status == 'aberto':
            planejamentos_query = planejamentos_query.filter_by(fechado=False)

        planejamentos = planejamentos_query.all()

        for p in planejamentos:
            grupo = p.linha.grupo if p.linha and p.linha.grupo in grupos else 'GRUPO_REF_01'
            grupos[grupo].append(p)
            total_por_grupo[grupo] += p.quantidade

    total_geral = sum(total_por_grupo.values())

    remessas = Remessa.query.order_by(Remessa.codigo).all()

    return render_template(
        'relatorio_planejamentos.html',
        grupos=grupos,
        totais=total_por_grupo,
        total_geral=total_geral,
        remessas=remessas,
        request=request  # necessário para mostrar filtros usados
    )


@bp.route('/planejamento/ver/<int:id>')
@login_required
@requer_permissao('ppcp', 'ver')
def ver_planejamento(id):
    planejamento = PlanejamentoProducao.query.get_or_404(id)
    return render_template('ver_planejamento.html', planejamento=planejamento)


@bp.route('/planejamento/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def novo_planejamento():
    form = PlanejamentoProducaoForm()
    form.remessa_id.choices = [(r.id, r.codigo) for r in Remessa.query.order_by(Remessa.codigo).all()]
    form.linha_id.choices = [(l.id, l.nome) for l in Linha.query.order_by(Linha.nome).all()]

    if form.validate_on_submit():
        planejamento = PlanejamentoProducao(
            remessa_id = form.remessa_id.data,
            referencia=form.referencia.data,
            quantidade=form.quantidade.data,
            preco_medio=form.preco_medio.data,
            setor=form.setor.data,
            linha_id=form.linha_id.data,
            esteira=form.esteira.data,
            esteira_qtd=form.esteira_qtd.data or 0,
            fechado=form.fechado.data
        )

        if form.fechado.data:
            planejamento.data_fechado = datetime.utcnow().replace(microsecond=0)

        db.session.add(planejamento)
        db.session.commit()

        flash('Planejamento cadastrado com sucesso!', 'success')
        return redirect(url_for('routes.listar_planejamentos'))

    return render_template('novo_planejamento.html', form=form)

@bp.route('/planejamento/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('ppcp', 'editar')
def editar_planejamento(id):
    planejamento = PlanejamentoProducao.query.get_or_404(id)
    form = PlanejamentoProducaoForm(obj=planejamento)

    # Choices para selects
    form.remessa_id.choices = [(r.id, r.codigo) for r in Remessa.query.order_by(Remessa.codigo).all()]
    form.linha_id.choices = [(l.id, l.nome) for l in Linha.query.order_by(Linha.nome).all()]

    # Função para hora de Brasília
    from datetime import datetime
    import pytz
    def hora_brasilia():
        return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(microsecond=0)

    if form.validate_on_submit():
        planejamento.referencia = form.referencia.data
        planejamento.quantidade = form.quantidade.data
        planejamento.preco_medio = form.preco_medio.data
        planejamento.setor = form.setor.data
        planejamento.linha_id = form.linha_id.data
        planejamento.remessa_id = form.remessa_id.data
        planejamento.esteira = form.esteira.data
        planejamento.esteira_qtd = form.esteira_qtd.data or 0
        planejamento.fechado = form.fechado.data

        # Atualiza ou limpa a data de fechamento
        if planejamento.fechado:
            if not planejamento.data_fechado:
                planejamento.data_fechado = hora_brasilia()
        else:
            planejamento.data_fechado = None

        db.session.commit()
        flash('Planejamento atualizado com sucesso!', 'success')
        return redirect(url_for('routes.listar_planejamentos'))

    return render_template('editar_planejamento.html', form=form, planejamento=planejamento)


@bp.route('/planejamento/atualizar_campo', methods=['POST'])
@login_required
@requer_permissao('ppcp', 'editar')
def atualizar_campo_planejamento():
    from flask import request, jsonify
    from app.models import PlanejamentoProducao  # Import correto!
    from datetime import datetime

    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'erro': 'Requisição sem JSON válido'})

    planejamento_id = data.get('id')
    campo = data.get('campo')
    valor = data.get('valor')

    planejamento = PlanejamentoProducao.query.get_or_404(planejamento_id)

    if campo == 'setor':
        planejamento.setor = valor

    elif campo == 'fechado':
        planejamento.fechado = valor.lower() == 'sim'
        if planejamento.fechado:
            planejamento.data_fechado = datetime.now().replace(microsecond=0)
        else:
            planejamento.data_fechado = None

    elif campo == 'esteira':
        planejamento.esteira = bool(valor)  # ✅ apenas isso


    db.session.commit()
    return jsonify({'success': True})



@bp.route('/planejamento/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('ppcp', 'excluir')
def excluir_planejamento(id):
    planejamento = PlanejamentoProducao.query.get_or_404(id)
    db.session.delete(planejamento)
    db.session.commit()
    flash('Planejamento excluído com sucesso!', 'success')
    return redirect(url_for('routes.listar_planejamentos'))


@bp.route('/planejamento/importacao/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('ppcp', 'criar')
def nova_importacao_planejamentos():
    return render_template('importar_planejamentos.html')


@bp.route('/planejamento/importar', methods=['POST'])
@login_required
@requer_permissao('ppcp', 'criar')
def importar_planejamentos():
    arquivo = request.files.get('arquivo')
    if not arquivo:
        flash('Nenhum arquivo enviado.', 'danger')
        return redirect(url_for('routes.importar_planejamento'))

    try:
        df = pd.read_excel(arquivo)
    except Exception as e:
        flash(f'Erro ao ler a planilha: {str(e)}', 'danger')
        return redirect(url_for('routes.importar_planejamento'))

    registros_criados = 0

    for _, row in df.iterrows():
        try:
            codigo_remessa = str(row['Código da Remessa']).strip()
            referencia = str(row['Referência']).strip().upper()
            linha_nome = str(row['Linha']).strip()
            quantidade = int(row['Quantidade'])

            # 🔸 Trata preco_medio: se vazio ou inválido, assume 0
            preco_raw = str(row.get('Preco_medio', '')).replace("R$", "").replace(",", ".").strip()
            try:
                preco_medio = float(preco_raw) if preco_raw else 0
            except ValueError:
                preco_medio = 0

            # Valores padrão
            setor = "-"
            esteira = False
            esteira_qtd = 0
            fechado = False
            data_fechado = None

            # Busca ou cria remessa
            remessa = Remessa.query.filter_by(codigo=codigo_remessa).first()
            if not remessa:
                remessa = Remessa(codigo=codigo_remessa)
                db.session.add(remessa)
                db.session.flush()

            # Busca linha
            linha = Linha.query.filter_by(nome=linha_nome).first()
            if not linha:
                flash(f'Linha "{linha_nome}" não encontrada.', 'danger')
                continue

            planejamento = PlanejamentoProducao(
                remessa_id=remessa.id,
                referencia=referencia,
                preco_medio=preco_medio,
                quantidade=quantidade,
                setor=setor,
                linha_id=linha.id,
                esteira=esteira,
                esteira_qtd=esteira_qtd,
                fechado=fechado,
                data_fechado=data_fechado
            )

            db.session.add(planejamento)
            registros_criados += 1

        except Exception as e:
            flash(f'Erro ao importar linha: {str(e)}', 'danger')
            continue

    db.session.commit()
    flash(f'{registros_criados} planejamentos importados com sucesso!', 'success')
    return redirect(url_for('routes.listar_planejamentos'))



### PRODUCAO X FATURAMENTO   ##########

@bp.route('/planejamento/prodfat', methods=['GET'])
@login_required
@requer_permissao('ppcp', 'ver')
def listar_prodfat():
    resultados = []
    total_faturado = 0
    total_produzido = 0

    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    referencia = request.args.get('referencia')
    remessa_id = request.args.get('remessa_id')
    linha_id = request.args.get('linha_id')

    try:
        remessa_id = int(remessa_id) if remessa_id else None
    except ValueError:
        remessa_id = None

    try:
        linha_id = int(linha_id) if linha_id else None
    except ValueError:
        linha_id = None

    if referencia == 'None' or not referencia:
        referencia = None

    query = db.session.query(ProducaoDiaria).join(PlanejamentoProducao).filter()

    if data_inicio:
        query = query.filter(ProducaoDiaria.data_producao >= data_inicio)
    if data_fim:
        query = query.filter(ProducaoDiaria.data_producao <= data_fim)
    if referencia:
        query = query.filter(PlanejamentoProducao.referencia.ilike(f"%{referencia}%"))
    if remessa_id:
        query = query.filter(PlanejamentoProducao.remessa_id == remessa_id)
    if linha_id:
        query = query.filter(PlanejamentoProducao.linha_id == linha_id)

    resultados = query.order_by(ProducaoDiaria.data_producao.asc()).all()

    total_produzido = sum(p.quantidade for p in resultados)
    total_faturado = sum(p.faturamento for p in resultados)

    remessas = Remessa.query.order_by(Remessa.codigo).all()
    linhas = Linha.query.order_by(Linha.nome).all()

    return render_template(
        "listar_producao_diaria.html",
        resultados=resultados,
        remessas=remessas,
        linhas=linhas,
        data_inicio=data_inicio,
        data_fim=data_fim,
        referencia=referencia,
        remessa_id=remessa_id,
        linha_id=linha_id,
        total_faturado=total_faturado,
        total_produzido=total_produzido
    )

@bp.route('/planejamento/importar_prodfat', methods=['GET', 'POST'])
@login_required
@requer_permissao('ppcp', 'criar')
def importar_producao_faturamento():
    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        if not arquivo or not allowed_file(arquivo.filename):
            flash("Arquivo inválido. Envie um .xlsx", "danger")
        else:
            try:
                df = pd.read_excel(arquivo)
                df.columns = df.columns.str.strip().str.upper()

                # ✅ Corrigir remessas para sempre serem strings e evitar '2473.0'
                if 'REMESSA' in df.columns:
                    df['REMESSA'] = df['REMESSA'].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.', '', 1).isdigit() and float(x).is_integer() else str(x).strip())

                col_obrig = ['DATA', 'REMESSA', 'REF', 'QTD']
                faltando = [col for col in col_obrig if col not in df.columns]
                if faltando:
                    flash(f"Colunas obrigatórias ausentes: {', '.join(faltando)}", "danger")
                    return redirect(request.url)

                total_inseridos = 0
                total_nao_encontrados = 0
                erros_detalhados = []

                print("\n=== Iniciando importação de Produção Diária ===\n")

                for i, row in df.iterrows():
                    setor = row.get('SETOR', None)
                    if setor is not None:
                        setor = str(setor).strip()

                    referencia = str(row['REF']).strip().upper()
                    remessa_codigo = str(row['REMESSA']).strip()
                    data_producao = pd.to_datetime(row['DATA']).date()
                    qtd = int(row['QTD']) if not pd.isna(row['QTD']) else 0

                    print(f"\n--> Processando: REF={referencia} | REMESSA={remessa_codigo} | QTD={qtd} | DATA={data_producao}")

                    remessa = Remessa.query.filter(Remessa.codigo.ilike(remessa_codigo)).first()
                    if not remessa:
                        msg = f"❌ Linha {i+2}: Remessa '{remessa_codigo}' não encontrada."
                        print(msg)
                        erros_detalhados.append(msg)
                        total_nao_encontrados += 1
                        continue

                    planejamento = PlanejamentoProducao.query.filter_by(
                        referencia=referencia,
                        remessa_id=remessa.id
                    ).first()

                    if planejamento:
                        if setor:
                            planejamento.setor = setor

                        if planejamento.preco_medio:
                            faturamento = round(float(planejamento.preco_medio) * qtd, 2)
                        else:
                            faturamento = 0.0

                        prod_diaria = ProducaoDiaria(
                            planejamento_id=planejamento.id,
                            data_producao=data_producao,
                            quantidade=qtd,
                            faturamento=faturamento
                        )
                        db.session.add(prod_diaria)
                        total_inseridos += 1
                        print(f"✅ ProduçãoDiaria inserida: QTD={qtd} | FATURAMENTO={faturamento}")
                    else:
                        msg = f"❌ Linha {i+2}: Planejamento não encontrado para REF '{referencia}' na REMESSA '{remessa_codigo}'"
                        print(msg)
                        erros_detalhados.append(msg)
                        total_nao_encontrados += 1

                db.session.commit()
                print("\n=== Importação Finalizada ===\n")
                print(f"TOTAL INSERIDOS: {total_inseridos}")
                print(f"TOTAL NÃO ENCONTRADOS: {total_nao_encontrados}")

                flash(f"Importação concluída! {total_inseridos} registros inseridos. {total_nao_encontrados} não encontrados.", "success")
                
                if erros_detalhados:
                    for erro in erros_detalhados:
                        flash(erro, "warning")

            except Exception as e:
                flash(f"Erro ao importar: {str(e)}", "danger")

        return redirect(url_for('routes.importar_producao_faturamento'))

    return render_template("importar_prodfat.html")



@bp.route('/planejamento/relatorio_prodxfat_pdf')
@login_required
@requer_permissao('ppcp', 'ver')
def relatorio_prodxfat_pdf():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    referencia = request.args.get('referencia')
    remessa_id = request.args.get('remessa_id')
    linha_id = request.args.get('linha_id')

    try:
        remessa_id = int(remessa_id) if remessa_id else None
    except ValueError:
        remessa_id = None

    try:
        linha_id = int(linha_id) if linha_id else None
    except ValueError:
        linha_id = None

    if referencia == 'None' or not referencia:
        referencia = None

    resultados = []

    if any([data_inicio, data_fim, referencia, remessa_id, linha_id]):
        query = ProducaoDiaria.query.join(PlanejamentoProducao)

        if data_inicio:
            query = query.filter(ProducaoDiaria.data_producao >= data_inicio)
        if data_fim:
            query = query.filter(ProducaoDiaria.data_producao <= data_fim)
        if referencia:
            query = query.filter(PlanejamentoProducao.referencia.ilike(f"%{referencia}%"))
        if remessa_id:
            query = query.filter(PlanejamentoProducao.remessa_id == remessa_id)
        if linha_id:
            query = query.filter(PlanejamentoProducao.linha_id == linha_id)

        resultados = query.order_by(ProducaoDiaria.data_producao.asc()).all()

    # Calcular totais com segurança
    total_produzido = sum(p.quantidade for p in resultados)
    total_faturado = sum(p.faturamento_medio for p in resultados)

    html = render_template(
        "relatorio_prodxfat_pdf.html",
        resultados=resultados,
        data_inicio=data_inicio,
        data_fim=data_fim,
        referencia=referencia,
        total_faturado=total_faturado,
        total_produzido=total_produzido
    )
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "inline; filename=relatorio_prodxfat.pdf"
    return response






@bp.route('/planejamento/grafico_prodfat')
@login_required
@requer_permissao('ppcp', 'ver')
def grafico_prodfat():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    referencia = request.args.get('referencia')
    remessa_id = request.args.get('remessa_id')
    linha_id = request.args.get('linha_id')

    return render_template(
        "grafico_prodfat.html",
        data_inicio=data_inicio,
        data_fim=data_fim,
        referencia=referencia,
        remessa_id=remessa_id,
        linha_id=linha_id
    )

@bp.route('/planejamento/grafico_prodfat_img')
@login_required
@requer_permissao('ppcp', 'ver')
def grafico_prodfat_img():
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    referencia = request.args.get('referencia')
    remessa_id = request.args.get('remessa_id')
    linha_id = request.args.get('linha_id')

    try:
        remessa_id = int(remessa_id) if remessa_id else None
    except:
        remessa_id = None
    try:
        linha_id = int(linha_id) if linha_id else None
    except:
        linha_id = None
    if referencia == 'None' or not referencia:
        referencia = None

    query = db.session.query(ProducaoDiaria).join(PlanejamentoProducao).filter()

    if data_inicio:
        query = query.filter(ProducaoDiaria.data_producao >= data_inicio)
    if data_fim:
        query = query.filter(ProducaoDiaria.data_producao <= data_fim)
    if referencia:
        query = query.filter(PlanejamentoProducao.referencia.ilike(f"%{referencia}%"))
    if remessa_id:
        query = query.filter(PlanejamentoProducao.remessa_id == remessa_id)
    if linha_id:
        query = query.filter(PlanejamentoProducao.linha_id == linha_id)

    resultados = query.all()

    df = pd.DataFrame([{
        'data': r.data_producao,
        'producao': r.quantidade,
        'faturamento': r.faturamento
    } for r in resultados])

    if df.empty:
        return "Sem dados para o gráfico.", 204

    df['data'] = pd.to_datetime(df['data'])
    df = df.groupby('data').agg({
        'producao': 'sum',
        'faturamento': 'sum'
    }).reset_index()

    # Adiciona coluna de preço médio diário
    df['preco_medio'] = df.apply(
        lambda row: round(row['faturamento'] / row['producao'], 2) if row['producao'] > 0 else 0.0,
        axis=1
    )

    df['label'] = df['data'].dt.strftime('%d-%b')

    fig = Figure(figsize=(10, 5))
    ax1 = fig.add_subplot(111)

    bars = ax1.bar(df['label'], df['faturamento'], color='orange', label='Faturamento')

    for i, row in df.iterrows():
        # Faturamento (centro da barra)
        fat_label = formatar_moeda(row['faturamento'])
        ax1.text(i, row['faturamento'] * 0.5, fat_label,
                ha='center', fontsize=9, color='black')

        # Produção (embaixo da barra)
        prod_label = f"{formatar_numero(row['producao'])} pares"
        ax1.text(i, -df['faturamento'].max() * 0.05, prod_label,
                ha='center', fontsize=9, color='blue')

        # Preço médio (acima da barra)
        preco_label = formatar_moeda(row['preco_medio'])
        ax1.text(i, row['faturamento'] + df['faturamento'].max() * 0.02, preco_label,
                ha='center', fontsize=9, color='red')


    ax1.set_ylabel("Faturamento (R$)")
    ax1.set_title("Produção × Faturamento por Dia")
    ax1.set_ylim(bottom=-df['faturamento'].max() * 0.1)

    fig.tight_layout()


    canvas = FigureCanvas(fig)
    img = BytesIO()
    canvas.print_png(img)
    img.seek(0)

    return send_file(img, mimetype='image/png')

##### CRUD DE PRODUÇÃO DIÁRIA    ########


@bp.route('/producao_diaria/ver/<int:id>')
@login_required
@requer_permissao('ppcp', 'ver')
def ver_producao_diaria(id):
    producao = ProducaoDiaria.query.get_or_404(id)
    form = DeleteForm()
    return render_template('ver_producao_diaria.html', producao=producao, form=form)


@bp.route('/producao_diaria/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('ppcp', 'criar')
def nova_producao_diaria():
    form = ProducaoDiariaForm()

    # choices (mantém assim para validação do WTForms)
    form.planejamento_id.choices = [
        (p.id, f"{p.referencia} - Rem: ({p.remessa.codigo}) - {p.quantidade} pares")
        for p in PlanejamentoProducao.query.all()
    ]

    # 👇 adições leves para o template
    remessas = Remessa.query.order_by(Remessa.codigo).all()
    planejamentos = (PlanejamentoProducao.query
                     .join(PlanejamentoProducao.remessa)
                     .add_entity(Remessa)  # opcional
                     .all())

    if form.validate_on_submit():
        planejamento = PlanejamentoProducao.query.get(form.planejamento_id.data)
        if not planejamento:
            flash('Planejamento não encontrado.', 'danger')
            return render_template('nova_producao_diaria.html', form=form,
                                   remessas=remessas, planejamentos=[p for p, _ in planejamentos])

        preco = float(planejamento.preco_medio or 0)
        faturamento = (form.quantidade.data or 0) * preco

        producao = ProducaoDiaria(
            data_producao=form.data_producao.data,
            quantidade=form.quantidade.data,
            planejamento_id=planejamento.id,
            faturamento=faturamento
        )
        db.session.add(producao)
        db.session.commit()
        flash('Produção diária cadastrada com sucesso.', 'success')
        return redirect(url_for('routes.listar_prodfat'))

    # importante: enviar listas na primeira renderização
    return render_template('nova_producao_diaria.html', form=form,
                           remessas=remessas,
                           planejamentos=[p for p, _ in planejamentos])



@bp.route('/producao_diaria/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('ppcp', 'editar')
def editar_producao_diaria(id):
    producao = ProducaoDiaria.query.get_or_404(id)
    form = ProducaoDiariaForm(obj=producao)

    # Preenche as opções do SelectField
    form.planejamento_id.choices = [
        (p.id, f"{p.referencia} - Rem:({p.remessa.codigo}) - {p.quantidade} pares")
        for p in PlanejamentoProducao.query.all()
    ]

    if form.validate_on_submit():
        planejamento = PlanejamentoProducao.query.get(form.planejamento_id.data)

        if not planejamento:
            flash('Planejamento não encontrado.', 'danger')
            return render_template('editar_producao_diaria.html', form=form, producao=producao)

        preco = planejamento.preco_medio if planejamento.preco_medio else 0.0
        faturamento = form.quantidade.data * preco

        producao.data_producao = form.data_producao.data
        producao.quantidade = form.quantidade.data
        producao.planejamento_id = planejamento.id
        producao.faturamento = faturamento

        db.session.commit()
        flash('Produção diária atualizada com sucesso.', 'success')
        return redirect(url_for('routes.ver_producao_diaria', id=producao.id))

    return render_template('editar_producao_diaria.html', form=form, producao=producao)





# Excluir produção diária
@bp.route('/producao_diaria/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('ppcp', 'excluir')
def excluir_producao_diaria(id):
    producao = ProducaoDiaria.query.get_or_404(id)
    db.session.delete(producao)
    db.session.commit()
    flash('Produção diária excluída com sucesso.', 'success')
    return redirect(url_for('routes.listar_prodfat'))


@bp.route('/excluir_producao_por_data', methods=['GET', 'POST'])
@login_required
@requer_permissao('ppcp', 'excluir')
@requer_permissao('controleproducao', 'editar')
def excluir_producao_por_data():
    form = ExcluirProducaoPorDataForm()

    if form.validate_on_submit():
        data = form.data.data
        registros = ProducaoDiaria.query.filter(
            ProducaoDiaria.data_producao == data
        ).all()

        if not registros:
            flash('Nenhum registro encontrado para a data de produção informada.', 'warning')
        else:
            for r in registros:
                db.session.delete(r)
            db.session.commit()
            flash(f'{len(registros)} registro(s) com data de produção {data.strftime("%d/%m/%Y")} excluído(s) com sucesso.', 'success')

        return redirect(url_for('routes.excluir_producao_por_data'))

    return render_template('excluir_producao_por_data.html', form=form)

## TIPOS ##


@bp.route('/tipos', methods=['GET'])
@login_required
@requer_permissao('manutencao', 'ver')
def listar_tipos():
    tipos = Tipo.query.order_by(Tipo.id.desc()).all()
    return render_template('listar_tipos.html', tipos=tipos)

@bp.route('/tipo/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('manutencao', 'criar')
def novo_tipo():
    form = TipoForm()
    if form.validate_on_submit():
        tiponovo = Tipo(
            tipo = form.tipo.data
        )

        db.session.add(tiponovo)
        db.session.commit()
        flash('Tipo adicionado com sucesso!', 'success')
        return redirect(url_for('routes.listar_tipos'))
    return render_template('novo_tipo.html', form=form)



@bp.route('/tipo/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('manutencao', 'editar')
def editar_tipo(id):
    tipo = Tipo.query.get_or_404(id)
    form = TipoForm(obj=tipo)

    if form.validate_on_submit():
        tipo.tipo = form.tipo.data

        db.session.commit()
        flash('Tipo atualizado com sucesso!', 'success')
        return redirect(url_for('routes.listar_tipos'))
    
    return render_template('editar_tipo.html', form=form, tipo=tipo)


@bp.route('/tipo/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('manutencao', 'excluir')
def excluir_tipo(id):
    tipo = Tipo.query.get_or_404(id)

    try:
        db.session.delete(tipo)
        db.session.commit()
        flash('Tipo excluído com sucesso!', 'success')

    except IntegrityError:
        db.session.rollback()

        # 🔹 Mensagem genérica sem listar onde o componente é usado
        flash("Erro: Este TIPO! não pode ser excluído porque está sendo utilizado em outras tabelas do sistema.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir o TIPO: {str(e)}", "danger")

    return redirect(url_for('routes.listar_tipos'))


 ##   PEÇAS    ####


@bp.route('/pecas', methods=['GET'])
@login_required
@requer_permissao('manutencao', 'ver')
def listar_pecas():
    filtro = request.args.get('filtro', '')

    if filtro:
        pecas = Peca.query.filter(Peca.descricao.ilike(f"%{filtro}%")).order_by(Peca.id.desc()).all()
    else:
        pecas = Peca.query.order_by(Peca.id.desc()).all()

    return render_template('listar_pecas.html', pecas=pecas)


@bp.route('/peca/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('manutencao', 'criar')
def nova_peca():
    form = PecaForm()
    form.tipo_id.choices = [(t.id, t.tipo) for t in Tipo.query.order_by(Tipo.tipo).all()]

    if form.validate_on_submit():
        peca = Peca(
            codigo=form.codigo.data,
            tipo_id = form.tipo_id.data,
            descricao=form.descricao.data,
            unidade_medida=form.unidade_medida.data,
            preco=form.preco.data if form.preco.data is not None else 0
        )
        db.session.add(peca)
        db.session.commit()
        flash('Peça adicionada com sucesso!', 'success')
        return redirect(url_for('routes.listar_pecas'))
    return render_template('nova_peca.html', form=form)

@bp.route('/peca/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('manutencao', 'editar')
def editar_peca(id):
    peca = Peca.query.get_or_404(id)
    form = PecaForm(obj=peca)

    #popular o select de tipos
    form.tipo_id.choices = [(t.id, t.tipo) for t in Tipo.query.order_by(Tipo.tipo).all()]
    
    if form.validate_on_submit():
        peca.codigo = form.codigo.data
        peca.tipo_id = form.tipo_id.data
        peca.descricao = form.descricao.data
        peca.unidade_medida = form.unidade_medida.data
        peca.preco = form.preco.data
        
        db.session.commit()
        flash('Peça atualizada com sucesso!', 'success')
        return redirect(url_for('routes.listar_pecas'))
    
    return render_template('editar_peca.html', form=form, peca=peca)


@bp.route('/peca/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('manutencao', 'excluir')
def excluir_peca(id):
    peca = Peca.query.get_or_404(id)

    try:
        db.session.delete(peca)
        db.session.commit()
        flash('Peça excluída com sucesso!', 'success')

    except IntegrityError:
        db.session.rollback()

        # 🔹 Mensagem genérica sem listar onde o componente é usado
        flash("Erro: Esta Peça não pode ser excluída porque está sendo utilizada em outras tabelas do sistema.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir o componente: {str(e)}", "danger")

    return redirect(url_for('routes.listar_pecas'))


#### GRAFICOS PARA SEU GLAIDSTON

@bp.route('/monitor/margens')
@login_required
@requer_permissao('comercial', 'ver')
def monitor_margens():
    return render_template('monitor_margens.html')

## API LUCRO PEDIDOS

@bp.route('/monitor/lucro-pedidos')
@login_required
@requer_permissao('comercial', 'ver')
def monitor_lucro_pedidos():
    quantidade = int(request.args.get('quantidade', 5))
    cliente = request.args.get('cliente')
    nota = request.args.get('nota')
    inicio = request.args.get('inicio')
    fim = request.args.get('fim')
    remessa = request.args.get('remessa')

    query = MargemPorPedido.query

    if remessa:
        query = query.filter(MargemPorPedido.remessa == remessa)
    if cliente:
        query = query.filter(MargemPorPedido.cliente.ilike(f"%{cliente}%"))
    if nota:
        query = query.filter(MargemPorPedido.nota_fiscal.ilike(f"%{nota}%"))
    if inicio:
        query = query.filter(MargemPorPedido.data_criacao >= inicio)
    if fim:
        query = query.filter(MargemPorPedido.data_criacao <= fim)

    margens = query.order_by(MargemPorPedido.id.desc()).limit(quantidade).all()
    dados = [
    {
        "pedido": m.pedido,
        "lucro": float(m.lucro_total or 0),
        "faturamento": float(m.total_preco_venda or 0)  # ← esse é o campo do modelo
    }
    for m in margens
    ]

    return jsonify(dados)

@bp.route('/clientes-select2')
@login_required
def clientes_select2():
    clientes = (
        db.session.query(MargemPorPedido.cliente)
        .filter(MargemPorPedido.cliente != None)
        .distinct()
        .order_by(MargemPorPedido.cliente)
        .all()
    )
    return jsonify([{"id": c.cliente, "text": c.cliente} for c in clientes])

@bp.route('/notas-fiscais-select2')
@login_required
def notas_fiscais_select2():
    notas = (
        db.session.query(MargemPorPedido.nota_fiscal)
        .filter(MargemPorPedido.nota_fiscal != None)
        .distinct()
        .order_by(MargemPorPedido.nota_fiscal)
        .all()
    )
    return jsonify([{"id": n.nota_fiscal, "text": n.nota_fiscal} for n in notas])

@bp.route('/monitor/remessas-disponiveis')
@login_required
@requer_permissao('comercial', 'ver')
def remessas_disponiveis():
    remessas = (
        db.session.query(MargemPorPedido.remessa)
        .filter(MargemPorPedido.remessa != None)
        .distinct()
        .order_by(MargemPorPedido.remessa.desc())
        .all()
    )
    resultados = [{"id": r.remessa, "text": r.remessa} for r in remessas]
    return jsonify(resultados)



######  MATERIAIS   ####
from sqlalchemy.orm import joinedload
from decimal import Decimal, InvalidOperation


# LISTAR
@bp.route('/materiais')
@login_required
@requer_permissao('comercial', 'ver')
def listar_materiais():
    materiais = (Material.query
                 .options(joinedload(Material.cores).joinedload(MaterialCor.cor))
                 .order_by(Material.id.desc())
                 .all())
    return render_template('listar_materiais.html', materiais=materiais)


# NOVO — cria Material e (opcional) cores + quantidades num único POST
@bp.route('/material/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('comercial', 'criar')
def novo_material():
    form = MaterialForm()
    cores = Cor.query.order_by(Cor.nome.asc()).all()

    if form.validate_on_submit():
        material = Material(
            descricao=form.descricao.data.strip(),
            tipo=form.tipo.data,
            unidade_medida=form.unidade_medida.data,
            preco_unitario=form.preco_unitario.data or Decimal('0.00'),
            observacao=(form.observacao.data or '').strip() or None
        )
        db.session.add(material)
        db.session.flush()

        selecionadas = [int(x) for x in request.form.getlist('cores[]') if x.isdigit()]

        if selecionadas:
            for cor_id in selecionadas:
                db.session.add(MaterialCor(material_id=material.id, cor_id=cor_id, quantidade=Decimal('0.00')))
        else:
            sem_cor = Cor.query.filter(Cor.nome.ilike('Sem cor')).first()
            if sem_cor:
                db.session.add(MaterialCor(material_id=material.id, cor_id=sem_cor.id, quantidade=Decimal('0.00')))

        db.session.commit()
        flash('Material criado com sucesso!', 'success')
        return redirect(url_for('routes.ver_material', id=material.id))

    return render_template('novo_material.html', form=form, cores=cores)






#Editar material
@bp.route('/material/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('comercial', 'editar')
def editar_material(id):
    material = Material.query.get_or_404(id)
    form = MaterialForm(obj=material)

    cores = Cor.query.order_by(Cor.nome.asc()).all()
    existentes = {mc.cor_id: mc for mc in material.cores}
    vinculadas_ids = set(existentes.keys())

    if form.validate_on_submit():
        material.descricao = form.descricao.data.strip()
        material.tipo = form.tipo.data
        material.unidade_medida = form.unidade_medida.data
        material.preco_unitario = form.preco_unitario.data or Decimal('0.00')
        material.observacao = (form.observacao.data or '').strip() or None

        selecionadas = set()
        for cid in request.form.getlist('cores[]'):
            try:
                selecionadas.add(int(cid))
            except (TypeError, ValueError):
                pass

        # Se nenhuma cor selecionada, força "Sem cor"
        if not selecionadas:
            sem_cor = Cor.query.filter(Cor.nome.ilike('Sem cor')).first()
            if sem_cor:
                selecionadas = {sem_cor.id}

        finais = selecionadas

        # Adicionar novas
        for cor_id in finais - vinculadas_ids:
            db.session.add(MaterialCor(material_id=material.id, cor_id=cor_id, quantidade=Decimal('0.00')))

        # Remover as que saíram (só se quantidade == 0)
        bloqueadas = []
        for cor_id, mc in list(existentes.items()):
            if cor_id not in finais:
                if (mc.quantidade or Decimal('0.00')) == 0:
                    db.session.delete(mc)
                else:
                    bloqueadas.append(mc.cor.nome if mc.cor else f'Cor #{cor_id}')

        db.session.commit()

        if bloqueadas:
            flash('Material salvo, mas não removi estas cores pois possuem quantidade: ' + ', '.join(bloqueadas), 'warning')
        else:
            flash('Material atualizado com sucesso!', 'success')

        return redirect(url_for('routes.ver_material', id=material.id))

    vinculadas_ids = set(mc.cor_id for mc in material.cores)
    return render_template('editar_material.html', form=form, material=material, cores=cores, vinculadas_ids=vinculadas_ids)


# VER — detalhamento por cor
@bp.route('/material/<int:id>')
@login_required
@requer_permissao('comercial', 'ver')
def ver_material(id):
    material = (Material.query
                .options(joinedload(Material.cores).joinedload(MaterialCor.cor))
                .get_or_404(id))
    return render_template('ver_material.html', material=material)


# EXCLUIR — form simples com CSRF
@bp.route('/material/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('comercial', 'excluir')
def excluir_material(id):
    material = Material.query.get_or_404(id)
    db.session.delete(material)
    db.session.commit()
    flash('Material excluído com sucesso!', 'success')
    return redirect(url_for('routes.listar_materiais'))



#### MOVIMENTAÇÃO MATERIAIS  ####

def _get_mc(material_id, cor_id):
    mc = MaterialCor.query.filter_by(material_id=material_id, cor_id=cor_id).first()
    if not mc:
        mc = MaterialCor(material_id=material_id, cor_id=cor_id, quantidade=Decimal('0.00'))
        db.session.add(mc)
        db.session.flush()
    return mc

@bp.route('/material/<int:material_id>/movimentos')
@login_required
@requer_permissao('comercial', 'ver')
def listar_movimentos_material(material_id):
    material = (Material.query
                .options(joinedload(Material.cores).joinedload(MaterialCor.cor))
                .get_or_404(material_id))

    movimentos = (MovimentacaoMaterial.query
                  .filter_by(material_id=material.id)
                  .order_by(MovimentacaoMaterial.id.desc())
                  .limit(50)
                  .all())

    # apenas cores VINCULADAS para o select
    cores_vinculadas = sorted(
        [mc.cor for mc in material.cores if mc.cor],
        key=lambda c: c.nome.lower()
    )

    # monta linhas e totais
    preco = material.preco_unitario or Decimal('0.00')
    rows_saldo = []
    for mc in sorted(material.cores, key=lambda mc: (mc.cor.nome if mc.cor else '').lower()):
        q = mc.quantidade or Decimal('0.00')
        v = q * preco
        rows_saldo.append({
            "cor_nome": mc.cor.nome if mc.cor else "-",
            "q": q,
            "v": v,
        })

    # >>> totais calculados DEPOIS de montar as linhas
    total_q = sum((r["q"] for r in rows_saldo), Decimal('0.00'))
    total_v = sum((r["v"] for r in rows_saldo), Decimal('0.00'))

    return render_template(
        'movimentos_material.html',
        material=material,
        movimentos=movimentos,
        cores=cores_vinculadas,
        rows_saldo=rows_saldo,
        total_q=total_q,
        total_v=total_v,
    )

@bp.route('/material/<int:material_id>/movimentar', methods=['POST'])
@login_required
@requer_permissao('comercial', 'editar')
def movimentar_material(material_id):
    material = Material.query.get_or_404(material_id)

    tipo = (request.form.get('tipo') or '').upper()
    cor_id = request.form.get('cor_id', type=int)
    qtd_raw = (request.form.get('quantidade') or '').strip()
    observacao = (request.form.get('observacao') or '').strip() or None

    if tipo not in ('ENTRADA', 'SAIDA') or not cor_id:
        flash('Dados de movimentação incompletos.', 'danger')
        return redirect(url_for('routes.listar_movimentos_material', material_id=material.id))

    try:
        quantidade = Decimal(qtd_raw.replace(',', '.'))
    except InvalidOperation:
        flash('Quantidade inválida.', 'danger')
        return redirect(url_for('routes.listar_movimentos_material', material_id=material.id))

    if quantidade <= 0:
        flash('Quantidade deve ser maior que zero.', 'danger')
        return redirect(url_for('routes.listar_movimentos_material', material_id=material.id))

    # 🔒 Garante que a cor pertence ao material (não cria vínculo novo aqui)
    mc = MaterialCor.query.filter_by(material_id=material.id, cor_id=cor_id).first()
    if not mc:
        flash('Esta cor não está vinculada a este material.', 'warning')
        return redirect(url_for('routes.listar_movimentos_material', material_id=material.id))

    saldo_atual = mc.quantidade or Decimal('0.00')

    if tipo == 'SAIDA' and quantidade > saldo_atual:
        flash('Saída maior que o saldo disponível para essa cor.', 'warning')
        return redirect(url_for('routes.listar_movimentos_material', material_id=material.id))

    # Aplica
    mc.quantidade = (saldo_atual + quantidade) if tipo == 'ENTRADA' else (saldo_atual - quantidade)

    # Histórico
    db.session.add(MovimentacaoMaterial(
        material_id=material.id,
        cor_id=cor_id,
        tipo=tipo,
        quantidade=quantidade,
        observacao=observacao
    ))
    db.session.commit()

    flash(f'{tipo.title()} registrada com sucesso.', 'success')
    return redirect(url_for('routes.listar_movimentos_material', material_id=material.id))


### COLABORADOR  ###
# --------------------------------------------
# Listagem (comum)
# --------------------------------------------
@bp.route('/colaboradores')
@login_required
@requer_permissao('comercial', 'ver')
def listar_colaboradores():
    colaboradores = Colaborador.query.order_by(Colaborador.nome.asc()).all()
    tipos = TipoColaborador.query.order_by(TipoColaborador.descricao.asc()).all()  # opcional para filtro na tela
    return render_template('listar_colaboradores.html', colaboradores=colaboradores, tipos=tipos)

# --------------------------------------------
# Novo
# --------------------------------------------
@bp.route('/colaborador/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('comercial', 'criar')
def novo_colaborador():
    form = ColaboradorForm()
    # Popular o select de tipos (o Select2 é só no template)
    tipos = TipoColaborador.query.order_by(TipoColaborador.descricao.asc()).all()
    form.tipo_id.choices = [(t.id, t.descricao) for t in tipos]

    if form.validate_on_submit():
        try:
            novo = Colaborador(
                nome=form.nome.data.strip(),
                documento=(form.documento.data or '').strip() or None,
                email=(form.email.data or '').strip() or None,
                telefone=(form.telefone.data or '').strip() or None,
                cep=(form.cep.data or '').strip() or None,
                endereco=(form.endereco.data or '').strip() or None,
                numero=(form.numero.data or '').strip() or None,
                complemento=(form.complemento.data or '').strip() or None,
                bairro=(form.bairro.data or '').strip() or None,
                cidade=(form.cidade.data or '').strip() or None,
                uf=(form.uf.data or '').strip() or None,
                tipo_id=form.tipo_id.data,
            )
            db.session.add(novo)
            db.session.commit()
            flash('Colaborador cadastrado com sucesso!', 'success')
            return redirect(url_for('routes.listar_colaboradores'))
        except IntegrityError:
            db.session.rollback()
            flash('Documento (CPF/CNPJ) já cadastrado para outro colaborador.', 'danger')
        except SQLAlchemyError:
            db.session.rollback()
            flash('Erro ao salvar colaborador.', 'danger')

    return render_template('novo_colaborador.html', form=form)

# --------------------------------------------
# Editar
# --------------------------------------------
@bp.route('/colaborador/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('comercial', 'editar')
def editar_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)
    form = ColaboradorForm(obj=colaborador)

    # Popular tipos para o select (Select2 só no template)
    tipos = TipoColaborador.query.order_by(TipoColaborador.descricao.asc()).all()
    form.tipo_id.choices = [(t.id, t.descricao) for t in tipos]

    if form.validate_on_submit():
        try:
            colaborador.nome = form.nome.data.strip()
            colaborador.documento = (form.documento.data or '').strip() or None
            colaborador.email = (form.email.data or '').strip() or None
            colaborador.telefone = (form.telefone.data or '').strip() or None
            colaborador.cep = (form.cep.data or '').strip() or None
            colaborador.endereco = (form.endereco.data or '').strip() or None
            colaborador.numero = (form.numero.data or '').strip() or None
            colaborador.complemento = (form.complemento.data or '').strip() or None
            colaborador.bairro = (form.bairro.data or '').strip() or None
            colaborador.cidade = (form.cidade.data or '').strip() or None
            colaborador.uf = (form.uf.data or '').strip() or None
            colaborador.tipo_id = form.tipo_id.data

            db.session.commit()
            flash('Colaborador atualizado com sucesso!', 'success')
            return redirect(url_for('routes.listar_colaboradores'))
        except IntegrityError:
            db.session.rollback()
            flash('Documento (CPF/CNPJ) já utilizado por outro colaborador.', 'danger')
        except SQLAlchemyError:
            db.session.rollback()
            flash('Erro ao atualizar colaborador.', 'danger')

    return render_template('editar_colaborador.html', form=form, colaborador=colaborador)

# --------------------------------------------
# Ver (detalhes)
# --------------------------------------------
@bp.route('/colaborador/<int:id>')
@login_required
@requer_permissao('comercial', 'ver')
def ver_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)
    return render_template('ver_colaborador.html', colaborador=colaborador)

# --------------------------------------------
# Excluir (confirmação "excluir" + CSRF)
# --------------------------------------------
@bp.route('/colaborador/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('comercial', 'excluir')
def excluir_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)

    # Padrão do seu sistema: validação manual do CSRF vinda do modal
    token = request.form.get('csrf_token', '')
    try:
        validate_csrf(token)
    except CSRFError:
        flash('Falha no CSRF. Recarregue a página e tente novamente.', 'danger')
        return redirect(url_for('routes.listar_colaboradores'))

    confirm_text = (request.form.get('confirm_text') or '').strip().lower()
    if confirm_text != 'excluir':
        flash('Digite "excluir" para confirmar.', 'warning')
        return redirect(url_for('routes.listar_colaboradores'))

    try:
        db.session.delete(colaborador)
        db.session.commit()
        flash('Colaborador excluído com sucesso!', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('Erro ao excluir colaborador. Verifique vínculos.', 'danger')

    return redirect(url_for('routes.listar_colaboradores'))


### PRODUCAO ROTATIVA  ###


from urllib.parse import urlencode

@bp.route('/producoes_rotativas', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_producoes_rotativas():
    from sqlalchemy import func
    from datetime import datetime

    # Parâmetros de filtro
    f_turno    = (request.args.get('turno') or '').strip().upper()
    f_dia_str  = (request.args.get('dia') or '').strip()
    f_maquina  = (request.args.get('maquina_id') or '').strip()

    # Parâmetros de paginação
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        per_page = 10
    per_page = max(5, min(per_page, 100))  # sanidade

    # Query base
    query = ProducaoRotativa.query

    # Filtros
    if f_turno in ('DIA', 'NOITE'):
        query = query.filter(func.upper(ProducaoRotativa.turno) == f_turno)

    if f_dia_str:
        try:
            dia_dt = datetime.strptime(f_dia_str, '%Y-%m-%d').date()
            query = query.filter(func.date(ProducaoRotativa.data_producao) == dia_dt)
        except ValueError:
            pass

    if f_maquina.isdigit():
        query = query.filter(ProducaoRotativa.maquina_id == int(f_maquina))

    query = query.order_by(ProducaoRotativa.id.desc())

    # Paginação
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    producoes_rotativas = pagination.items


        # carregar MAQUINAS FILTRADAS ROT
    maquinas = [
    (m.id, f"{m.codigo} - {m.descricao}")
    for m in Maquina.query
        .filter(Maquina.codigo.like("ROT%"))
        .order_by(Maquina.codigo.asc())
        .all()]

    # Query string sem o parâmetro 'page' (pra montar os links)
    qs_dict = request.args.to_dict()
    qs_dict.pop('page', None)
    qs_no_page = urlencode(qs_dict)

    return render_template(
        'listar_producoes_rotativas.html',
        producoes_rotativas=producoes_rotativas,
        maquinas=maquinas,
        pagination=pagination,
        per_page=per_page,
        qs_no_page=qs_no_page  # ex.: "turno=DIA&dia=2025-08-01&maquina_id=3"
    )

@bp.route('/producaorotativa/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_producao_rotativa():
    form = ProducaoRotativaForm()
    form.maquina_id.choices = [(m.id, m.codigo) for m in Maquina.query.order_by(Maquina.codigo.asc()).all()]

    # turno livre (sem turno_fixo)
    turno_fixo = None

    if form.validate_on_submit():
        # Upload padrão do sistema (só se vier arquivo)
        imagem_filename = None
        if form.imagem.data and hasattr(form.imagem.data, 'filename') and form.imagem.data.filename:
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_filename)
            form.imagem.data.save(caminho_imagem)

        nova_producaorotativa = ProducaoRotativa(
            turno=form.turno.data,
            data_producao=form.data_producao.data,
            producao_painel=form.producao_painel.data,
            pares_bons=form.pares_bons.data,
            imagem=imagem_filename,   # None se não enviou
            observacao=form.observacao.data,
            maquina_id=form.maquina_id.data
        )
        db.session.add(nova_producaorotativa)
        db.session.commit()
        flash("Produção da Rotativa cadastrada com sucesso!", "success")
        return redirect(url_for('routes.listar_producoes_rotativas'))

    return render_template('nova_producao_rotativa.html', form=form, turno_fixo=turno_fixo)


@bp.route('/producaorotativa/nova/dia', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_producao_rotativa_dia():
    form = ProducaoRotativaForm()
    # carregar MAQUINAS FILTRADAS ROT
    form.maquina_id.choices = [
        (m.id, f"{m.codigo} - {m.descricao}")
        for m in Maquina.query
            .filter(Maquina.codigo.like("ROT%"))
            .order_by(Maquina.codigo.asc())
            .all()
    ]

    turno_fixo = "DIA"
    if request.method == 'GET':
        form.turno.data = turno_fixo  # trava visualmente no template

    if form.validate_on_submit():
        # --- valida duplicidade (máquina + data + turno) ---
        existe = ProducaoRotativa.query.filter(
            ProducaoRotativa.maquina_id == form.maquina_id.data,
            func.date(ProducaoRotativa.data_producao) == form.data_producao.data,
            func.upper(ProducaoRotativa.turno) == turno_fixo
        ).first()
        if existe:
            flash("Já existe produção cadastrada para essa Máquina/Dia/Turno (DIA).", "warning")
            return render_template('nova_producao_rotativa.html', form=form, turno_fixo=turno_fixo)

        # ---------- Regra: autocompletar produção_painel com 110% de pares_bons ----------
        painel_val = form.producao_painel.data
        pares_val  = form.pares_bons.data

        # considera "em branco" quando None ou 0
        if (painel_val is None or painel_val == 0) and (pares_val is not None and pares_val > 0):
            painel_val = int(round(pares_val * 1.10))
            flash(f"Produção do painel estava em branco. Preenchido automaticamente com 110% dos pares bons ({painel_val}).", "info")

        # Upload padrão do sistema (só se vier arquivo)
        imagem_filename = None
        if form.imagem.data and hasattr(form.imagem.data, 'filename') and form.imagem.data.filename:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(upload_folder, imagem_filename)
            form.imagem.data.save(caminho_imagem)

        nova_producaorotativa = ProducaoRotativa(
            turno=turno_fixo,  # trava o turno
            data_producao=form.data_producao.data,
            producao_painel=painel_val,
            pares_bons=pares_val,
            imagem=imagem_filename,
            observacao=form.observacao.data,
            maquina_id=form.maquina_id.data
        )

        db.session.add(nova_producaorotativa)
        try:
            db.session.commit()
            flash("Produção da Rotativa (DIA) cadastrada com sucesso!", "success")
            return redirect(url_for('routes.listar_producoes_rotativas'))
        except IntegrityError:
            db.session.rollback()
            flash("Duplicidade detectada (Máquina/Dia/Turno DIA).", "danger")

    return render_template('nova_producao_rotativa.html', form=form, turno_fixo=turno_fixo)


@bp.route('/producaorotativa/nova/noite', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_producao_rotativa_noite():
    form = ProducaoRotativaForm()
    # carregar MAQUINAS FILTRADAS ROT
    form.maquina_id.choices = [
        (m.id, f"{m.codigo} - {m.descricao}")
        for m in Maquina.query
            .filter(Maquina.codigo.like("ROT%"))
            .order_by(Maquina.codigo.asc())
            .all()
    ]

    turno_fixo = "NOITE"
    if request.method == 'GET':
        form.turno.data = turno_fixo  # trava visualmente no template

    if form.validate_on_submit():
        # --- valida duplicidade (máquina + data + turno) ---
        existe = ProducaoRotativa.query.filter(
            ProducaoRotativa.maquina_id == form.maquina_id.data,
            func.date(ProducaoRotativa.data_producao) == form.data_producao.data,
            func.upper(ProducaoRotativa.turno) == turno_fixo
        ).first()
        if existe:
            flash("Já existe produção cadastrada para essa Máquina/Dia/Turno (NOITE).", "warning")
            return render_template('nova_producao_rotativa.html', form=form, turno_fixo=turno_fixo)

        # ---------- Regra: autocompletar produção_painel com 110% de pares_bons ----------
        painel_val = form.producao_painel.data
        pares_val  = form.pares_bons.data

        if (painel_val is None or painel_val == 0) and (pares_val is not None and pares_val > 0):
            painel_val = int(round(pares_val * 1.10))
            flash(f"Produção do painel estava em branco. Preenchido automaticamente com valor de pares bons + 10%", "info")

        # Upload padrão do sistema (só se vier arquivo)
        imagem_filename = None
        if form.imagem.data and hasattr(form.imagem.data, 'filename') and form.imagem.data.filename:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(upload_folder, imagem_filename)
            form.imagem.data.save(caminho_imagem)

        nova_producaorotativa = ProducaoRotativa(
            turno=turno_fixo,  # trava o turno
            data_producao=form.data_producao.data,
            producao_painel=painel_val,
            pares_bons=pares_val,
            imagem=imagem_filename,
            observacao=form.observacao.data,
            maquina_id=form.maquina_id.data
        )

        db.session.add(nova_producaorotativa)
        try:
            db.session.commit()
            flash("Produção da Rotativa (NOITE) cadastrada com sucesso!", "success")
            return redirect(url_for('routes.listar_producoes_rotativas'))
        except IntegrityError:
            db.session.rollback()
            flash("Duplicidade detectada (Máquina/Dia/Turno NOITE).", "danger")

    return render_template('nova_producao_rotativa.html', form=form, turno_fixo=turno_fixo)

@bp.route('/producao_rotativa/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_producao_rotativa(id):
    pr = ProducaoRotativa.query.get_or_404(id)
    form = ProducaoRotativaForm(obj=pr)

    # carregar MAQUINAS FILTRADAS ROT
    form.maquina_id.choices = [
    (m.id, f"{m.codigo} - {m.descricao}")
    for m in Maquina.query
        .filter(Maquina.codigo.like("ROT%"))
        .order_by(Maquina.codigo.asc())
        .all()]

    if form.validate_on_submit():
        # Normaliza turno para comparação
        turno_val = (form.turno.data or '').upper()

        # 🔒 Validação de duplicidade (desconsidera o próprio registro)
        existe = ProducaoRotativa.query.filter(
            ProducaoRotativa.id != pr.id,
            ProducaoRotativa.maquina_id == form.maquina_id.data,
            func.date(ProducaoRotativa.data_producao) == form.data_producao.data,
            func.upper(ProducaoRotativa.turno) == turno_val
        ).first()

        if existe:
            flash("Já existe produção para essa Máquina/Dia/Turno.", "warning")
            imagem_url = url_for('static', filename=f'uploads/{pr.imagem}') if pr.imagem else None
            return render_template('editar_producao_rotativa.html', form=form, pr=pr, imagem_url=imagem_url)

        # Atualiza campos
        pr.turno = turno_val
        pr.data_producao = form.data_producao.data
        pr.producao_painel = form.producao_painel.data
        pr.pares_bons = form.pares_bons.data
        pr.observacao = form.observacao.data
        pr.maquina_id = form.maquina_id.data

        # Upload da imagem (somente se enviado novo arquivo)
        if form.imagem.data and hasattr(form.imagem.data, "filename") and form.imagem.data.filename:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(upload_folder, imagem_filename)
            form.imagem.data.save(caminho_imagem)
            pr.imagem = imagem_filename

        # Log
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou a Produção: {pr.id} da Rotativa: {pr.maquina.codigo}"
        )
        db.session.add(log)

        # Commit com proteção à constraint única do BD
        try:
            db.session.commit()
            flash("Produção atualizada!", "success")
            return redirect(url_for('routes.listar_producoes_rotativas'))
        except IntegrityError:
            db.session.rollback()
            flash("Duplicidade detectada (Máquina/Dia/Turno).", "danger")

    # URL para preview no template
    imagem_url = url_for('static', filename=f'uploads/{pr.imagem}') if pr.imagem else None
    return render_template('editar_producao_rotativa.html', form=form, pr=pr, imagem_url=imagem_url)



@bp.route('/producao_rotativa/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_producao_rotativa(id):
    pr = ProducaoRotativa.query.get_or_404(id)

    try:
        db.session.delete(pr)
        db.session.commit()
        flash('Produção da Rotativa excluída com sucesso!', 'success')

    except IntegrityError:
        db.session.rollback()
        flash("Erro ao excluir Produção!", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir a produção da rotativa: {str(e)}", "danger")

    return redirect(url_for('routes.listar_producoes_rotativas'))

@bp.route('/relatorios/rotativas/totais', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_totais_rotativas():
    from sqlalchemy import func, case
    from datetime import datetime

    # filtros
    f_inicio  = request.args.get('inicio')      # 'YYYY-MM-DD'
    f_fim     = request.args.get('fim')         # 'YYYY-MM-DD'
    f_maquina = request.args.get('maquina_id')  # id da máquina

    inicio = datetime.strptime(f_inicio, '%Y-%m-%d').date() if f_inicio else None
    fim    = datetime.strptime(f_fim, '%Y-%m-%d').date() if f_fim else None
    maquina_id = int(f_maquina) if f_maquina else None

    turno_up = func.upper(ProducaoRotativa.turno)
    prod_painel = func.coalesce(ProducaoRotativa.producao_painel, 0)
    pares_bons  = func.coalesce(ProducaoRotativa.pares_bons, 0)

    q = db.session.query(
        func.coalesce(func.sum(prod_painel), 0).label("painel_total"),
        func.coalesce(func.sum(pares_bons), 0).label("pares_total"),
        func.coalesce(func.sum(case((turno_up == 'DIA',   prod_painel), else_=0)), 0).label("painel_dia"),
        func.coalesce(func.sum(case((turno_up == 'NOITE', prod_painel), else_=0)), 0).label("painel_noite"),
        func.coalesce(func.sum(case((turno_up == 'DIA',   pares_bons),  else_=0)), 0).label("pares_dia"),
        func.coalesce(func.sum(case((turno_up == 'NOITE', pares_bons),  else_=0)), 0).label("pares_noite"),
    )

    if inicio:
        q = q.filter(ProducaoRotativa.data_producao >= inicio)
    if fim:
        q = q.filter(ProducaoRotativa.data_producao <= fim)
    if maquina_id:
        q = q.filter(ProducaoRotativa.maquina_id == maquina_id)

    totais = q.one()._asdict()

    # 🔽 máquinas para o select2
    #select de máquinas (id, codigo) FILTRO ROT
    maquinas = [(m.id, f"{m.codigo} - {m.descricao}") for m in Maquina.query
        .filter(Maquina.codigo.like("ROT%"))
        .order_by(Maquina.codigo.asc())
        .all()]

    return render_template(
        "relatorio_totais_rotativas.html",
        totais=totais,
        inicio=f_inicio, fim=f_fim,
        maquina_id=f_maquina,
        maquinas=maquinas
    )

@bp.route('/relatorios/rotativas/mapas', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_mapas_producao():
    from sqlalchemy import func, case
    from datetime import datetime

    f_inicio  = request.args.get('inicio')       # 'YYYY-MM-DD'
    f_fim     = request.args.get('fim')          # 'YYYY-MM-DD'
    f_maquina = request.args.get('maquina_id')   # opcional (mostra só 1 máquina)
    inicio = datetime.strptime(f_inicio, '%Y-%m-%d').date() if f_inicio else None
    fim    = datetime.strptime(f_fim, '%Y-%m-%d').date() if f_fim else None
    maquina_id = int(f_maquina) if f_maquina else None

    # >>> buscamos a máquina selecionada (para o cabeçalho de impressão)
    maquina_sel = Maquina.query.get(maquina_id) if maquina_id else None

    turno_up   = func.upper(ProducaoRotativa.turno)
    painel     = func.coalesce(ProducaoRotativa.producao_painel, 0)
    pares      = func.coalesce(ProducaoRotativa.pares_bons, 0)

    query = (db.session.query(
                Maquina.id.label('m_id'),
                Maquina.codigo.label('m_codigo'),
                func.coalesce(func.sum(case((turno_up == 'DIA',   painel), else_=0)), 0).label('painel_dia'),
                func.coalesce(func.sum(case((turno_up == 'NOITE', painel), else_=0)), 0).label('painel_noite'),
                func.coalesce(func.sum(painel), 0).label('painel_total'),
                func.coalesce(func.sum(case((turno_up == 'DIA',   pares), else_=0)), 0).label('pares_dia'),
                func.coalesce(func.sum(case((turno_up == 'NOITE', pares), else_=0)), 0).label('pares_noite'),
                func.coalesce(func.sum(pares), 0).label('pares_total'),
            )
            .join(Maquina, Maquina.id == ProducaoRotativa.maquina_id)
            # >>> garante que esta rota só mostre máquinas ROT
            .filter(Maquina.codigo.like("ROT%"))
    )

    if inicio:
        query = query.filter(ProducaoRotativa.data_producao >= inicio)
    if fim:
        query = query.filter(ProducaoRotativa.data_producao <= fim)
    if maquina_id:
        query = query.filter(ProducaoRotativa.maquina_id == maquina_id)

    query = query.group_by(Maquina.id, Maquina.codigo).order_by(Maquina.codigo.asc())
    rows = query.all()

    maquinas_data = [{
        "id": r.m_id,
        "codigo": r.m_codigo,
        "painel_dia":   int(r.painel_dia or 0),
        "painel_noite": int(r.painel_noite or 0),
        "painel_total": int(r.painel_total or 0),
        "pares_dia":    int(r.pares_dia or 0),
        "pares_noite":  int(r.pares_noite or 0),
        "pares_total":  int(r.pares_total or 0),
    } for r in rows]

    # opções para o filtro select2 (somente ROT)
    maquinas_opts = [(m.id, f"{m.codigo} - {m.descricao}") for m in Maquina.query
        .filter(Maquina.codigo.like("ROT%"))
        .order_by(Maquina.codigo.asc())
        .all()]

    return render_template(
        "relatorio_mapas_producao.html",
        maquinas=maquinas_data,
        maquinas_opts=maquinas_opts,
        inicio=f_inicio, fim=f_fim, maquina_id=f_maquina,
        maquina_sel=maquina_sel    # >>> novo
    )


@bp.route('/relatorios/rotativas/mapas/pdf', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_mapas_producao_pdf():
    from sqlalchemy import func, case
    from datetime import datetime
    from flask import render_template, make_response, request, url_for
    # WeasyPrint
    from weasyprint import HTML

    f_inicio  = request.args.get('inicio')       # 'YYYY-MM-DD'
    f_fim     = request.args.get('fim')          # 'YYYY-MM-DD'
    f_maquina = request.args.get('maquina_id')   # opcional

    inicio = datetime.strptime(f_inicio, '%Y-%m-%d').date() if f_inicio else None
    fim    = datetime.strptime(f_fim, '%Y-%m-%d').date() if f_fim else None
    maquina_id = int(f_maquina) if f_maquina else None

    turno_up = func.upper(ProducaoRotativa.turno)
    painel   = func.coalesce(ProducaoRotativa.producao_painel, 0)
    pares    = func.coalesce(ProducaoRotativa.pares_bons, 0)

    q = (db.session.query(
            Maquina.id.label('m_id'),
            Maquina.codigo.label('m_codigo'),
            func.coalesce(func.sum(case((turno_up == 'DIA',   painel), else_=0)), 0).label('painel_dia'),
            func.coalesce(func.sum(case((turno_up == 'NOITE', painel), else_=0)), 0).label('painel_noite'),
            func.coalesce(func.sum(painel), 0).label('painel_total'),
            func.coalesce(func.sum(case((turno_up == 'DIA',   pares), else_=0)), 0).label('pares_dia'),
            func.coalesce(func.sum(case((turno_up == 'NOITE', pares), else_=0)), 0).label('pares_noite'),
            func.coalesce(func.sum(pares), 0).label('pares_total'),
        )
        .join(Maquina, Maquina.id == ProducaoRotativa.maquina_id)
    )

    if inicio:
        q = q.filter(ProducaoRotativa.data_producao >= inicio)
    if fim:
        q = q.filter(ProducaoRotativa.data_producao <= fim)
    if maquina_id:
        q = q.filter(ProducaoRotativa.maquina_id == maquina_id)

    q = q.group_by(Maquina.id, Maquina.codigo).order_by(Maquina.codigo.asc())
    rows = q.all()

    maquinas = [{
        "id": r.m_id,
        "codigo": r.m_codigo,
        "painel_dia":   int(r.painel_dia or 0),
        "painel_noite": int(r.painel_noite or 0),
        "painel_total": int(r.painel_total or 0),
        "pares_dia":    int(r.pares_dia or 0),
        "pares_noite":  int(r.pares_noite or 0),
        "pares_total":  int(r.pares_total or 0),
    } for r in rows]

    maquina_nome = None
    if maquina_id:
        m = Maquina.query.get(maquina_id)
        maquina_nome = m.codigo if m else None

    # Renderiza HTML
    html_str = render_template(
        'relatorio_mapas_producao_pdf.html',
        maquinas=maquinas,
        inicio=f_inicio, fim=f_fim,
        maquina_id=f_maquina,
        maquina_nome=maquina_nome
    )

    # Converte para PDF
    pdf = HTML(string=html_str, base_url=request.root_url).write_pdf()

    # Resposta
    resp = make_response(pdf)
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'inline; filename=mapas_producao.pdf'
    return resp


### CONVENCIONAIS

@bp.route('/producao_convencionais', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_producoes_convencionais():
    from datetime import datetime
    from sqlalchemy import func

    # Filtros (datas no formato YYYY-MM-DD vindas do input type="date")
    f_inicio = (request.args.get('inicio') or '').strip()
    f_fim    = (request.args.get('fim') or '').strip()

    # Paginação
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 25))
    except ValueError:
        per_page = 25
    per_page = max(10, min(per_page, 100))  # sanidade

    # Query base
    query = ProducaoConvencional.query

    # Aplica filtros de data_producao (funciona para Date/DateTime)
    if f_inicio:
        try:
            dt_inicio = datetime.strptime(f_inicio, '%Y-%m-%d').date()
            query = query.filter(func.date(ProducaoConvencional.data_producao) >= dt_inicio)
        except ValueError:
            pass

    if f_fim:
        try:
            dt_fim = datetime.strptime(f_fim, '%Y-%m-%d').date()
            query = query.filter(func.date(ProducaoConvencional.data_producao) <= dt_fim)
        except ValueError:
            pass

    query = query.order_by(ProducaoConvencional.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    prod_convencionais = pagination.items

    return render_template(
        'listar_producoes_convencionais.html',
        prod_convencionais=prod_convencionais,
        pagination=pagination,
        per_page=per_page,
        inicio=f_inicio,
        fim=f_fim
    )

@bp.route('/producao_convencional/relatorio', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_producoes_convencionais():
    from datetime import datetime
    from sqlalchemy import desc
    from weasyprint import HTML, CSS
    import os

    inicio_str = request.args.get('inicio') or ""
    fim_str    = request.args.get('fim') or ""
    pdf_flag   = request.args.get('pdf', '0') == '1'

    # parse para date (ou None)
    di = None
    df = None
    try:
        if inicio_str:
            di = datetime.strptime(inicio_str, "%Y-%m-%d").date()
    except ValueError:
        di = None
    try:
        if fim_str:
            df = datetime.strptime(fim_str, "%Y-%m-%d").date()
    except ValueError:
        df = None

    # filtro
    q = ProducaoConvencional.query
    if di:
        q = q.filter(ProducaoConvencional.data_producao >= di)
    if df:
        q = q.filter(ProducaoConvencional.data_producao <= df)

    itens = q.order_by(desc(ProducaoConvencional.data_producao),
                       desc(ProducaoConvencional.id)).all()

    totais = {
        "alca": sum((i.producao_geral_alca or 0) for i in itens),
        "a":    sum((i.producao_solado_turno_a or 0) for i in itens),
        "b":    sum((i.producao_solado_turno_b or 0) for i in itens),
        "c":    sum((i.producao_solado_turno_c or 0) for i in itens),
    }
    totais["solado_total"] = totais["a"] + totais["b"] + totais["c"]

    # 🔑 passe objetos date para o template
    html = render_template(
        "relatorio_producoes_convencionais.html",
        itens=itens,
        inicio=di,
        fim=df,
        totais=totais,
    )

    if not pdf_flag:
        return html

    # PDF – importante: base_url para a logo/estáticos funcionarem
    css_path = os.path.join(current_app.root_path, "static", "css", "paginas3.css")
    styles = [CSS(filename=css_path)] if os.path.exists(css_path) else []

    pdf_bytes = HTML(string=html, base_url=request.url_root).write_pdf(stylesheets=styles)
    filename = f"relatorio_convencionais_{inicio_str or 'inicio'}_{fim_str or 'fim'}.pdf"
    return Response(pdf_bytes, mimetype="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{filename}"'})


@bp.route('/producao_convencional/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_producao_convencional():
    form = ProducaoConvencionalForm()
    
    if form.validate_on_submit():
        # 🔒 Verifica duplicidade por data
        existe = ProducaoConvencional.query.filter(
            func.date(ProducaoConvencional.data_producao) == form.data_producao.data
        ).first()
        if existe:
            flash("Já existe produção convencional cadastrada para este dia.", "warning")
            return render_template('nova_producao_convencional.html', form=form)

        # Upload padrão do sistema (só se vier arquivo)
        imagem_filename = None
        if form.imagem.data and hasattr(form.imagem.data, 'filename') and form.imagem.data.filename:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(upload_folder, imagem_filename)
            form.imagem.data.save(caminho_imagem)

        nova_prod_conv = ProducaoConvencional(
            data_producao=form.data_producao.data,
            producao_geral_alca=form.producao_geral_alca.data or 0,
            producao_solado_turno_a=form.producao_solado_turno_a.data or 0,
            producao_solado_turno_b=form.producao_solado_turno_b.data or 0,
            producao_solado_turno_c=form.producao_solado_turno_c.data or 0,
            observacao=form.observacao.data,
            imagem=imagem_filename
        )

        db.session.add(nova_prod_conv)
        try:
            db.session.commit()
            flash("Produção Convencional cadastrada com sucesso!", "success")
            return redirect(url_for('routes.listar_producoes_convencionais'))
        except IntegrityError:
            db.session.rollback()
            flash("Duplicidade detectada (Data).", "danger")
            # volta para o form mantendo os dados preenchidos
            return render_template('nova_producao_convencional.html', form=form)

    return render_template('nova_producao_convencional.html', form=form)


@bp.route('/producao_convencional/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_producao_convencional(id):
    pc = ProducaoConvencional.query.get_or_404(id)
    form = ProducaoConvencionalForm(obj=pc)

    if form.validate_on_submit():
        # 🔒 Verifica duplicidade por data (excluindo o próprio registro)
        existe = ProducaoConvencional.query.filter(
            ProducaoConvencional.id != pc.id,
            func.date(ProducaoConvencional.data_producao) == form.data_producao.data
        ).first()
        if existe:
            flash("Já existe produção convencional cadastrada para este dia.", "warning")
            return render_template('editar_producao_convencional.html', form=form, pc=pc)

        pc.data_producao = form.data_producao.data
        pc.producao_geral_alca = form.producao_geral_alca.data or 0
        pc.producao_solado_turno_a = form.producao_solado_turno_a.data or 0
        pc.producao_solado_turno_b = form.producao_solado_turno_b.data or 0
        pc.producao_solado_turno_c = form.producao_solado_turno_c.data or 0
        pc.observacao = form.observacao.data

        # só atualiza se realmente enviou novo arquivo
        if form.imagem.data and hasattr(form.imagem.data, "filename") and form.imagem.data.filename:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            imagem_filename = secure_filename(form.imagem.data.filename)
            caminho_imagem = os.path.join(upload_folder, imagem_filename)
            form.imagem.data.save(caminho_imagem)
            pc.imagem = imagem_filename
        
        log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            acao=f"Editou a Produção Convencional: {pc.id}"
        )
        db.session.add(log)

        try:
            db.session.commit()
            flash("Produção Convencional atualizada!", "success")
            return redirect(url_for('routes.listar_producoes_convencionais'))
        except IntegrityError:
            db.session.rollback()
            flash("Duplicidade detectada (Data).", "danger")
            return render_template('editar_producao_convencional.html', form=form, pc=pc)
    
    return render_template('editar_producao_convencional.html', form=form, pc=pc)


@bp.route('/producao_convencional/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_producao_convencional(id):
    pc = ProducaoConvencional.query.get_or_404(id)

    try:
        db.session.delete(pc)
        db.session.commit()
        flash('Produção Convencional excluída com sucesso!', 'success')

    except IntegrityError:
        db.session.rollback()
        flash("Erro ao excluir Produção!", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao excluir a produção Convencional: {str(e)}", "danger")

    return redirect(url_for('routes.listar_producoes_convencionais'))



### PRODUCAO FUNCIONARIOS #####
# ========== LISTAGEM (com paginação) ==========
# ------- LISTAR (Funcionários) -------
@bp.route('/producao_funcionario', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_producoes_funcionarios():
    from urllib.parse import urlencode
    from datetime import datetime

    funcionarios = [(f.id, f.nome) for f in Funcionario.query.order_by(Funcionario.nome).all()]

    # filtros
    funcionario_id   = request.args.get('funcionario_id', type=int)   
    f_inicio = (request.args.get('inicio') or '').strip()     # 'YYYY-MM-DD'
    f_fim    = (request.args.get('fim') or '').strip()        # 'YYYY-MM-DD'
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = max(5, min(per_page, 200))

    # base query
    q = (ProducaoFuncionario.query
         .join(Funcionario)
         .order_by(
            ProducaoFuncionario.data_producao.desc(),
            ProducaoFuncionario.id.desc()
         ))


    if funcionario_id:
        q = q.filter(ProducaoFuncionario.funcionario_id == funcionario_id)

    di = df = None
    if f_inicio:
        try:
            di = datetime.strptime(f_inicio, '%Y-%m-%d').date()
            q = q.filter(ProducaoFuncionario.data_producao >= di)
        except Exception:
            di = None  # opcional: flash('Data inicial inválida.', 'warning')

    if f_fim:
        try:
            df = datetime.strptime(f_fim, '%Y-%m-%d').date()
            q = q.filter(ProducaoFuncionario.data_producao <= df)
        except Exception:
            df = None  # opcional: flash('Data final inválida.', 'warning')

    # paginação compatível com Flask-SQLAlchemy 2.x e 3.x
    try:
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    except AttributeError:
        from app import db
        pagination = db.paginate(q, page=page, per_page=per_page, error_out=False)

    itens = pagination.items

    # monta querystring SEM o parâmetro page (para construir os links)
    qs_dict = request.args.to_dict(flat=True)
    qs_dict.pop('page', None)
    qs_no_page = urlencode(qs_dict)

    return render_template(
        'producao/listar_producoes_funcionarios.html',
        itens=itens,
        pagination=pagination,
        per_page=per_page,
        funcionarios=funcionarios,
        funcionario_id=funcionario_id,
        inicio=f_inicio,
        fim=f_fim,
        qs_no_page=qs_no_page
    )



# ========== CRUD (novo/editar/excluir)
@bp.route('/producao_funcionario/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_producao_funcionario():
    form = ProducaoFuncionarioForm()
    form.funcionario_id.choices = [(f.id, f.nome) for f in Funcionario.query.order_by(Funcionario.nome).all()]

    # Pré-seleciona data de hoje no GET (ou se o campo vier vazio)
    if request.method == 'GET' and not form.data_producao.data:
        form.data_producao.data = date.today()

    if form.validate_on_submit():
        # --- Checagem anti-duplicidade: (funcionario_id, data_producao) ---
        existe = (ProducaoFuncionario.query
                  .filter(
                      ProducaoFuncionario.funcionario_id == form.funcionario_id.data,
                      ProducaoFuncionario.data_producao == form.data_producao.data
                  )
                  .first())

        if existe:
            # Marca erro de validação e não insere
            form.data_producao.errors.append('Já existe produção para este funcionário nessa data.')
            # (Opcional) Link para editar o registro existente:
            flash('Já existe produção cadastrada para este funcionário nessa DATA!', 'warning')
            return render_template('producao/nova_producao_funcionario.html', form=form)

        # Se passou, cria normalmente
        pf = ProducaoFuncionario(
            data_producao=form.data_producao.data,
            quantidade=form.quantidade.data,
            funcionario_id=form.funcionario_id.data
        )
        db.session.add(pf)
        db.session.commit()
        flash('Produção do funcionário cadastrada!', 'success')
        return redirect(url_for('routes.listar_producoes_funcionarios'))

    return render_template('producao/nova_producao_funcionario.html', form=form)



@bp.route('/producao_funcionario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_producao_funcionario(id):
    pf = ProducaoFuncionario.query.get_or_404(id)
    form = ProducaoFuncionarioForm(obj=pf)
    form.funcionario_id.choices = [(f.id, f.nome) for f in Funcionario.query.order_by(Funcionario.nome).all()]

    # Pré-seleciona data de hoje no GET (ou se o campo vier vazio)
    if request.method == 'GET' and not form.data_producao.data:
        form.data_producao.data = date.today()

    if form.validate_on_submit():
        pf.data_producao  = form.data_producao.data
        pf.quantidade     = form.quantidade.data
        pf.funcionario_id = form.funcionario_id.data
        db.session.commit()
        flash('Produção do funcionário atualizada!', 'success')
        return redirect(url_for('routes.listar_producoes_funcionarios'))

    return render_template('producao/editar_producao_funcionario.html', form=form, item=pf)


@bp.route('/producao_funcionario/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_producao_funcionario(id):
    pf = ProducaoFuncionario.query.get_or_404(id)

    token = request.form.get('csrf_token', '')
    confirm_text = (request.form.get('confirm_text') or '').strip().lower()

    try:
        validate_csrf(token)
    except CSRFError:
        flash('Token CSRF inválido. Recarregue a página e tente novamente.', 'danger')
        return redirect(url_for('routes.listar_producoes_funcionarios'))

    db.session.delete(pf)
    db.session.commit()
    flash('Registro excluído com sucesso.', 'success')
    return redirect(url_for('routes.listar_producoes_funcionarios'))



# RELATÓRIO (com cálculo)
# =========================
@bp.route('/producao_funcionario/relatorio', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_producoes_funcionarios():
    """
    Regras:
      - Só mostra dados se o usuário clicar em Filtrar (filtrar=1) OU se houver filtros na URL.
      - Se clicar Filtrar com tudo vazio, traz tudo.
    """
    from datetime import datetime

    nome        = (request.args.get('nome') or '').strip()
    inicio      = (request.args.get('inicio') or '').strip()
    fim         = (request.args.get('fim') or '').strip()
    clicou_filtrar = (request.args.get('filtrar') == '1')
    tem_filtros    = any([nome, inicio, fim])

    q = (ProducaoFuncionario.query.join(Funcionario))

    if nome:
        q = q.filter(Funcionario.nome.ilike(f'%{nome}%'))

    di = df = None
    if inicio:
        try:
            di = datetime.strptime(inicio, '%Y-%m-%d').date()
            q = q.filter(ProducaoFuncionario.data_producao >= di)
        except Exception:
            di = None

    if fim:
        try:
            df = datetime.strptime(fim, '%Y-%m-%d').date()
            q = q.filter(ProducaoFuncionario.data_producao <= df)
        except Exception:
            df = None

    q = q.order_by(
        ProducaoFuncionario.data_producao.asc(),
        Funcionario.nome.asc(),
        ProducaoFuncionario.id.asc()
    )

    # 👉 Só carrega itens se clicou Filtrar OU se já vieram filtros
    if clicou_filtrar or tem_filtros:
        itens = q.all()
        total = sum(i.quantidade or 0 for i in itens)
    else:
        itens = []
        total = 0

    return render_template(
        'producao/relatorio_producoes_funcionarios.html',
        itens=itens,
        total=total,
        nome=nome,
        inicio=inicio or '',
        fim=fim or ''
    )



@bp.route('/producao_funcionario/relatorio/pdf', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_producoes_funcionarios_pdf():
    from datetime import datetime
    from flask import make_response, request, render_template, current_app
    from weasyprint import HTML

    nome   = (request.args.get('nome') or '').strip()
    inicio = request.args.get('inicio')
    fim    = request.args.get('fim')

    q = ProducaoFuncionario.query.join(Funcionario)
    di = df = None

    if nome:
        q = q.filter(Funcionario.nome.ilike(f'%{nome}%'))

    if inicio:
        try:
            di = datetime.strptime(inicio, '%Y-%m-%d').date()
            q = q.filter(ProducaoFuncionario.data_producao >= di)
        except Exception:
            di = None

    if fim:
        try:
            df = datetime.strptime(fim, '%Y-%m-%d').date()
            q = q.filter(ProducaoFuncionario.data_producao <= df)
        except Exception:
            df = None

    itens = (q.order_by(ProducaoFuncionario.data_producao.asc(),
                        Funcionario.nome.asc(),
                        ProducaoFuncionario.id.asc())
               .all())
    total = sum(i.quantidade or 0 for i in itens)

    html = render_template(
        "producao/relatorio_producoes_funcionarios_pdf.html",
        itens=itens, total=total, nome=nome, di=di, df=df
    )

    # ✅ Fundamental para a logo via url_for('static', ...)
    pdf_bytes = HTML(string=html, base_url=request.url_root).write_pdf()

    resp = make_response(pdf_bytes)
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'inline; filename=relatorio_producao_funcionarios.pdf'
    return resp

#### PRODUCAO SETOR  #####
# ------- LISTAR (com paginação, padrão Convencionais) -------
@bp.route('/producao_setor', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_producoes_setores():

    setores   = [(s.id, s.nome) for s in Setor.query.order_by(Setor.nome).all()]

    # filtros
    setor_id   = request.args.get('setor_id', type=int)   
    s_nome   = (request.args.get('nome') or '').strip()
    f_inicio = (request.args.get('inicio') or '').strip()
    f_fim    = (request.args.get('fim') or '').strip()
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = max(5, min(per_page, 200))

    q = (ProducaoSetor.query
         .join(Setor)
         .order_by(ProducaoSetor.data_producao.desc(),
                   ProducaoSetor.id.desc()))

    if setor_id:
        q = q.filter(ProducaoSetor.setor_id == setor_id)

    di = df = None
    if f_inicio:
        try:
            di = datetime.strptime(f_inicio, '%Y-%m-%d').date()
            q = q.filter(ProducaoSetor.data_producao >= di)
        except Exception:
            di = None
    if f_fim:
        try:
            df = datetime.strptime(f_fim, '%Y-%m-%d').date()
            q = q.filter(ProducaoSetor.data_producao <= df)
        except Exception:
            df = None

    # paginação compatível 2.x/3.x
    try:
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    except AttributeError:
        pagination = db.paginate(q, page=page, per_page=per_page, error_out=False)

    itens = pagination.items

    # querystring sem "page"
    qs_dict = request.args.to_dict(flat=True)
    qs_dict.pop('page', None)
    qs_no_page = urlencode(qs_dict)

    return render_template('producao/listar_producoes_setores.html',
                           setor_id=setor_id or '',
                           setores=setores,
                           itens=itens,
                           pagination=pagination,
                           per_page=per_page,
                           nome=s_nome,
                           inicio=f_inicio,
                           fim=f_fim,
                           qs_no_page=qs_no_page)


# ------- VER (Produção Setor) -------
@bp.route('/producao_setor/ver/<int:id>', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def ver_producao_setor(id):
    from app.models import ProducaoSetor
    item = ProducaoSetor.query.get_or_404(id)
    return render_template('producao/ver_producao_setor.html', item=item)


# ------- NOVO -------
@bp.route('/producao_setor/novo', methods=['GET','POST'])
@login_required
@requer_permissao('controleproducao','criar')
def nova_producao_setor():
    from datetime import date
    from app.models import (
        Setor, Solado, Alca, Remessa,
        ProducaoSetor, producao_setor_remessa
    )

    form = ProducaoSetorForm()

    # Choices
    form.setor_id.choices  = [(s.id, s.nome) for s in Setor.query.order_by(Setor.nome).all()]
    form.solado_id.choices = [(0, "-- Nenhum --")] + [(s.id, s.referencia) for s in Solado.query.order_by(Solado.referencia).all()]
    form.alca_id.choices   = [(0, "-- Nenhum --")] + [(a.id, a.referencia) for a in Alca.query.order_by(Alca.referencia).all()]
    form.remessas.choices  = [(r.id, r.codigo) for r in Remessa.query.order_by(Remessa.codigo).all()]

    # Data padrão = hoje
    if request.method == 'GET' and not form.data_producao.data:
        form.data_producao.data = date.today()

    if form.validate_on_submit():
        # Normaliza 0 -> None
        solado_val = form.solado_id.data or 0
        alca_val   = form.alca_id.data or 0
        solado_id  = None if solado_val == 0 else solado_val
        alca_id    = None if alca_val   == 0 else alca_val

        # Exclusividade: somente um dos dois
        if solado_id and alca_id:
            flash('Escolha apenas um modelo: Solado OU Alça (não ambos).', 'warning')
            return render_template("producao/nova_producao_setor.html", form=form)

        dt       = form.data_producao.data
        esteira  = form.esteira.data or None
        setor_id = form.setor_id.data
        rem_ids  = set(form.remessas.data or [])

        # ---------- Verificação de duplicidade ----------
        # Candidatos com mesma base (data/esteira/setor) e mesmo "lado" (solado vs alça)
        base_q = ProducaoSetor.query.filter(
            ProducaoSetor.data_producao == dt,
            ProducaoSetor.esteira == esteira,
            ProducaoSetor.setor_id == setor_id,
        )
        if solado_id is not None:
            base_q = base_q.filter(
                ProducaoSetor.solado_id == solado_id,
                ProducaoSetor.alca_id.is_(None)
            )
        elif alca_id is not None:
            base_q = base_q.filter(
                ProducaoSetor.alca_id == alca_id,
                ProducaoSetor.solado_id.is_(None)
            )
        else:
            # nenhum modelo selecionado: exige também que o existente não tenha modelo
            base_q = base_q.filter(
                ProducaoSetor.solado_id.is_(None),
                ProducaoSetor.alca_id.is_(None)
            )

        # Compara o CONJUNTO de remessas (ordem independente)
        candidatos = base_q.all()
        for cand in candidatos:
            cand_rem_ids = {r.id for r in (cand.remessas or [])}
            if cand_rem_ids == rem_ids:
                # duplicado 100%
                modelo_txt = "solado" if solado_id else ("alça" if alca_id else "sem modelo")
                flash(
                    f'Já existe uma produção idêntica (data/esteira/setor/{modelo_txt}/remessas).',
                    'warning'
                )
                return render_template("producao/nova_producao_setor.html", form=form)
        # ---------- fim verificação ----------

        # Cria
        novo = ProducaoSetor(
            data_producao = dt,
            quantidade    = form.quantidade.data,
            esteira       = esteira,
            setor_id      = setor_id,
            solado_id     = solado_id,
            alca_id       = alca_id,
        )
        db.session.add(novo)
        db.session.flush()  # obter novo.id

        # Associação N:N com Remessas
        if rem_ids:
            for rid in rem_ids:
                db.session.execute(
                    producao_setor_remessa.insert().values(
                        producao_setor_id=novo.id,
                        remessa_id=rid
                    )
                )

        db.session.commit()
        flash("Produção por setor registrada!", "success")
        return redirect(url_for('routes.listar_producoes_setores'))

    return render_template("producao/nova_producao_setor.html", form=form)



# ------- EDITAR -------
@bp.route('/producao_setor/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_producao_setor(id):
    from app.models import (
        Setor, Solado, Alca, Remessa,
        ProducaoSetor
    )

    item = ProducaoSetor.query.get_or_404(id)
    form = ProducaoSetorForm(obj=item)

    # Choices
    form.setor_id.choices  = [(s.id, s.nome) for s in Setor.query.order_by(Setor.nome).all()]
    form.solado_id.choices = [(0, "-- Nenhum --")] + [(s.id, s.referencia) for s in Solado.query.order_by(Solado.referencia).all()]
    form.alca_id.choices   = [(0, "-- Nenhum --")] + [(a.id, a.referencia) for a in Alca.query.order_by(Alca.referencia).all()]
    form.remessas.choices  = [(r.id, r.codigo) for r in Remessa.query.order_by(Remessa.codigo).all()]

    # Preenche multiselect com remessas atuais
    if request.method == 'GET':
        form.remessas.data = [r.id for r in item.remessas]

        # Normaliza selects de modelo para exibir "-- Nenhum --" quando None
        if item.solado_id is None:
            form.solado_id.data = 0
        if item.alca_id is None:
            form.alca_id.data = 0

    if form.validate_on_submit():
        # Normaliza 0 -> None
        solado_val = form.solado_id.data or 0
        alca_val   = form.alca_id.data or 0
        solado_id  = None if solado_val == 0 else solado_val
        alca_id    = None if alca_val   == 0 else alca_val

        # Exclusividade: só um dos dois
        if solado_id and alca_id:
            flash('Escolha apenas um modelo: Solado OU Alça (não ambos).', 'warning')
            return render_template('producao/editar_producao_setor.html', form=form, item=item)

        dt       = form.data_producao.data
        esteira  = form.esteira.data or None
        setor_id = form.setor_id.data
        rem_ids  = set(form.remessas.data or [])

        # ---------- Anti-duplicidade (ignora o próprio id) ----------
        base_q = ProducaoSetor.query.filter(
            ProducaoSetor.id != item.id,
            ProducaoSetor.data_producao == dt,
            ProducaoSetor.esteira == esteira,
            ProducaoSetor.setor_id == setor_id,
        )
        if solado_id is not None:
            base_q = base_q.filter(
                ProducaoSetor.solado_id == solado_id,
                ProducaoSetor.alca_id.is_(None)
            )
        elif alca_id is not None:
            base_q = base_q.filter(
                ProducaoSetor.alca_id == alca_id,
                ProducaoSetor.solado_id.is_(None)
            )
        else:
            base_q = base_q.filter(
                ProducaoSetor.solado_id.is_(None),
                ProducaoSetor.alca_id.is_(None)
            )

        candidatos = base_q.all()
        for cand in candidatos:
            cand_rem_ids = {r.id for r in (cand.remessas or [])}
            if cand_rem_ids == rem_ids:
                modelo_txt = "solado" if solado_id else ("alça" if alca_id else "sem modelo")
                flash(f'Já existe uma produção idêntica (data/esteira/setor/{modelo_txt}/remessas).', 'warning')
                return render_template('producao/editar_producao_setor.html', form=form, item=item)
        # ---------- fim anti-duplicidade ----------

        # Atualiza registro
        item.data_producao = dt
        item.quantidade    = form.quantidade.data
        item.esteira       = esteira
        item.setor_id      = setor_id
        item.solado_id     = solado_id
        item.alca_id       = alca_id

        # Atualiza remessas (N:N)
        item.remessas = []
        if rem_ids:
            item.remessas = Remessa.query.filter(Remessa.id.in_(rem_ids)).all()

        db.session.commit()
        flash('Produção do setor atualizada!', 'success')
        return redirect(url_for('routes.listar_producoes_setores'))

    return render_template('producao/editar_producao_setor.html', form=form, item=item)




# ------- EXCLUIR -------
@bp.route('/producao_setor/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_producao_setor(id):
    item = ProducaoSetor.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Registro excluído com sucesso.', 'success')
    return redirect(url_for('routes.listar_producoes_setores'))

# ------- RELATÓRIO (HTML)
@bp.route('/producao_setor/relatorio', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_producoes_setores():
    from datetime import datetime
    from sqlalchemy.orm import selectinload
    from app.models import ProducaoSetor, Setor, Remessa, Solado, Alca

    # --- Filtros vindos da UI ---
    setor_id   = request.args.get('setor_id', type=int)                # SELECT de setor
    inicio     = (request.args.get('inicio') or '').strip()
    fim        = (request.args.get('fim') or '').strip()
    esteira    = (request.args.get('esteira') or '').strip()
    item_tipo  = (request.args.get('item_tipo') or '').strip()         # 'solado'|'alca'|'sem'|''
    item_id    = request.args.get('item_id', type=int)                 # id conforme item_tipo
    rem_ids    = request.args.getlist('remessa_id', type=int)          # múltiplas remessas

    # Flag do clique do botão "Filtrar"
    clicou_filtrar = (request.args.get('filtrar') == '1')
    tem_filtros = any([setor_id, inicio, fim, esteira, item_tipo, item_id, rem_ids])

    # --- Query base (sem joins que multiplicam linhas) ---
    q = (ProducaoSetor.query
         .join(Setor)
         .options(
             selectinload(ProducaoSetor.setor),
             selectinload(ProducaoSetor.solado),
             selectinload(ProducaoSetor.alca),
             selectinload(ProducaoSetor.remessas),
         ))

    di = df = None

    # --- Filtros ---
    # prioridade para setor_id (select); se não vier, usa 'nome' (texto)
    if setor_id:
        q = q.filter(ProducaoSetor.setor_id == setor_id)

    if inicio:
        try:
            di = datetime.strptime(inicio, '%Y-%m-%d').date()
            q = q.filter(ProducaoSetor.data_producao >= di)
        except Exception:
            di = None

    if fim:
        try:
            df = datetime.strptime(fim, '%Y-%m-%d').date()
            q = q.filter(ProducaoSetor.data_producao <= df)
        except Exception:
            df = None

    if esteira:
        q = q.filter(ProducaoSetor.esteira == esteira)

    if item_tipo == 'solado':
        q = q.filter(ProducaoSetor.solado_id.isnot(None),
                     ProducaoSetor.alca_id.is_(None))
        if item_id:
            q = q.filter(ProducaoSetor.solado_id == item_id)
    elif item_tipo == 'alca':
        q = q.filter(ProducaoSetor.alca_id.isnot(None),
                     ProducaoSetor.solado_id.is_(None))
        if item_id:
            q = q.filter(ProducaoSetor.alca_id == item_id)
    elif item_tipo == 'sem':
        q = q.filter(ProducaoSetor.solado_id.is_(None),
                     ProducaoSetor.alca_id.is_(None))
    # item_tipo vazio => não filtra por modelo

    if rem_ids:
        q = q.filter(ProducaoSetor.remessas.any(Remessa.id.in_(rem_ids)))

    q = q.order_by(
        ProducaoSetor.data_producao.asc(),
        Setor.nome.asc(),
        ProducaoSetor.esteira.asc().nullsfirst(),
        ProducaoSetor.id.asc()
    )

    # --- Regra: só lista se clicou ou se há filtros; se clicou vazio, traz tudo ---
    if clicou_filtrar or tem_filtros:
        itens = q.all()
        total_geral = sum(i.quantidade or 0 for i in itens)
    else:
        itens = []
        total_geral = 0

    # --- Choices para selects ---
    setores   = [(s.id, s.nome) for s in Setor.query.order_by(Setor.nome).all()]   # << necessário pro select
    solados   = [(s.id, s.referencia) for s in Solado.query.order_by(Solado.referencia).all()]
    alcas     = [(a.id, a.referencia) for a in Alca.query.order_by(Alca.referencia).all()]
    remessas_choices = [(r.id, r.codigo) for r in Remessa.query.order_by(Remessa.codigo).all()]

    return render_template(
        'producao/relatorio_producoes_setores.html',
        itens=itens,
        # filtros atuais
        setor_id=setor_id or '',
        inicio=inicio, fim=fim, esteira=esteira,
        item_tipo=item_tipo, item_id=item_id or '',
        remessas_sel=rem_ids,
        # choices
        setores=setores, solados=solados, alcas=alcas, remessas=remessas_choices,
        # datas parseadas e total
        di=di, df=df, total_geral=total_geral
    )




# ------- RELATÓRIO (PDF) -------
@bp.route('/producao_setor/relatorio/pdf', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_producoes_setores_pdf():
    from weasyprint import HTML
    from datetime import datetime
    from sqlalchemy.orm import selectinload
    from app.models import ProducaoSetor, Setor, Remessa
    # Se seu template usa nomes dos itens, não precisa join; selectinload cuida.

    nome      = (request.args.get('nome') or '').strip()
    inicio    = (request.args.get('inicio') or '').strip()
    fim       = (request.args.get('fim') or '').strip()
    esteira   = (request.args.get('esteira') or '').strip()
    item_tipo = (request.args.get('item_tipo') or '').strip()
    item_id   = request.args.get('item_id', type=int)
    rem_ids   = request.args.getlist('remessa_id', type=int)

    # Flag do clique (link do PDF deve enviar ?filtrar=1)
    clicou_filtrar = (request.args.get('filtrar') == '1')
    tem_filtros = any([nome, inicio, fim, esteira, item_tipo, item_id, rem_ids])

    q = (ProducaoSetor.query
         .join(Setor)
         .options(
             selectinload(ProducaoSetor.setor),
             selectinload(ProducaoSetor.solado),
             selectinload(ProducaoSetor.alca),
             selectinload(ProducaoSetor.remessas),
         ))

    di = df = None
    if nome:
        q = q.filter(Setor.nome.ilike(f'%{nome}%'))
    if inicio:
        try:
            di = datetime.strptime(inicio, '%Y-%m-%d').date()
            q = q.filter(ProducaoSetor.data_producao >= di)
        except Exception:
            di = None
    if fim:
        try:
            df = datetime.strptime(fim, '%Y-%m-%d').date()
            q = q.filter(ProducaoSetor.data_producao <= df)
        except Exception:
            df = None
    if esteira:
        q = q.filter(ProducaoSetor.esteira == esteira)

    if item_tipo == 'solado':
        q = q.filter(ProducaoSetor.solado_id.isnot(None),
                     ProducaoSetor.alca_id.is_(None))
        if item_id:
            q = q.filter(ProducaoSetor.solado_id == item_id)
    elif item_tipo == 'alca':
        q = q.filter(ProducaoSetor.alca_id.isnot(None),
                     ProducaoSetor.solado_id.is_(None))
        if item_id:
            q = q.filter(ProducaoSetor.alca_id == item_id)
    elif item_tipo == 'sem':
        q = q.filter(ProducaoSetor.solado_id.is_(None),
                     ProducaoSetor.alca_id.is_(None))

    if rem_ids:
        q = q.filter(ProducaoSetor.remessas.any(Remessa.id.in_(rem_ids)))

    q = q.order_by(
        ProducaoSetor.data_producao.asc(),
        Setor.nome.asc(),
        ProducaoSetor.esteira.asc().nullsfirst(),
        ProducaoSetor.id.asc()
    )

    # Mesma regra: só sai PDF se clicou (ou se há filtros); se clicou vazio, traz tudo
    if clicou_filtrar or tem_filtros:
        itens = q.all()
    else:
        itens = []

    total = sum(i.quantidade or 0 for i in itens)

    html = render_template('producao/relatorio_producoes_setores_pdf.html',
                           itens=itens, total=total,
                           nome=nome, di=di, df=df,
                           esteira=esteira,
                           item_tipo=item_tipo, item_id=item_id,
                           remessas_sel=rem_ids)
    pdf_bytes = HTML(string=html, base_url=request.url_root).write_pdf()

    resp = make_response(pdf_bytes)
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'inline; filename=relatorio_producao_setores.pdf'
    return resp

### QUEBRA DE PRODUCAO  ##
# ------- LISTAR (Quebras de Alça) -------
@bp.route('/quebras_alca', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_quebras_alca():
    from urllib.parse import urlencode
    from sqlalchemy.orm import selectinload
    from app.models import QuebraAlca, Alca

    # filtros
    f_data    = (request.args.get('data') or '').strip()       # 'YYYY-MM-DD'
    f_alca_id = request.args.get('alca_id', type=int)          # id da alça
    page      = request.args.get('page', 1, type=int)
    per_page  = request.args.get('per_page', 20, type=int)
    per_page  = max(5, min(per_page, 200))

    # choices alças
    alcas = [(a.id, f'{a.referencia} — {a.descricao}') for a in Alca.query.order_by(Alca.referencia).all()]

    # base query
    q = (QuebraAlca.query
         .options(selectinload(QuebraAlca.alca), selectinload(QuebraAlca.linhas))
         .order_by(QuebraAlca.data_quebra.desc(), QuebraAlca.id.desc()))

    data_sel = None
    if f_data:
        try:
            data_sel = datetime.strptime(f_data, '%Y-%m-%d').date()
            q = q.filter(QuebraAlca.data_quebra == data_sel)
        except Exception:
            flash('Data inválida.', 'warning')

    if f_alca_id:
        q = q.filter(QuebraAlca.alca_id == f_alca_id)

    # paginação compatível 2.x/3.x
    try:
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    except AttributeError:
        from app import db
        pagination = db.paginate(q, page=page, per_page=per_page, error_out=False)

    itens = pagination.items

    # soma por cabeçalho (evita subquery; já veio com selectinload)
    totais = {it.id: sum(l.quantidade or 0 for l in it.linhas) for it in itens}

    # querystring sem page
    qs_dict = request.args.to_dict(flat=True)
    qs_dict.pop('page', None)
    qs_no_page = urlencode(qs_dict)

    return render_template(
        'producao/listar_quebras_alca.html',
        itens=itens,
        pagination=pagination,
        per_page=per_page,
        alcas=alcas,
        f_alca_id=f_alca_id or '',
        data_sel=data_sel,
        qs_no_page=qs_no_page,
        totais=totais
    )


@bp.route('/quebra_alca/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_quebra_alca():
    from app.models import Alca, TamanhoAlca
    form = QuebraAlcaForm()

    # Popular select de Alças
    form.alca_id.choices = [(0, '-- Selecione --')] + [
        (a.id, f'{a.referencia} — {a.descricao}') for a in Alca.query.order_by(Alca.referencia).all()
    ]

    # Data padrão hoje
    if request.method == 'GET' and not form.data_quebra.data:
        form.data_quebra.data = date.today()

    if form.validate_on_submit():
        if not form.alca_id.data:
            form.alca_id.errors.append('Selecione uma alça.')
            return render_template('producao/nova_quebra_alca.html', form=form)

        # Anti-duplicidade: mesma data + mesma alça
        ja_existe = (QuebraAlca.query
                     .filter(QuebraAlca.data_quebra == form.data_quebra.data,
                             QuebraAlca.alca_id == form.alca_id.data)
                     .first())
        if ja_existe:
            flash('Já existe quebra cadastrada para esta alça nesta data.', 'warning')
            return render_template('producao/nova_quebra_alca.html', form=form), 409

        # Coletar quantidades dos inputs dinamicamente gerados: qtd_<tamanho_alca_id>
        linhas = []
        for key, val in request.form.items():
            if key.startswith('qtd_'):
                try:
                    tam_id = int(key.replace('qtd_', ''))
                    qtd = int(val or 0)
                except ValueError:
                    continue
                if qtd > 0:
                    t = TamanhoAlca.query.get(tam_id)
                    if t and t.alca_id == form.alca_id.data:
                        linhas.append((t.id, t.nome, qtd))

        if not linhas:
            flash('Informe pelo menos uma quantidade de quebra em algum tamanho.', 'warning')
            return render_template('producao/nova_quebra_alca.html', form=form)

        # Persistir
        cab = QuebraAlca(
            data_quebra=form.data_quebra.data,
            observacao=form.observacao.data or None,
            alca_id=form.alca_id.data
        )
        db.session.add(cab)
        db.session.flush()

        for tam_id, nome, qtd in linhas:
            db.session.add(QuebraAlcaLinha(
                quebra_id=cab.id,
                tamanho_alca_id=tam_id,
                tamanho_nome=nome,
                quantidade=qtd
            ))

        db.session.commit()
        flash('Quebra de produção (Alça) registrada!', 'success')
        return redirect(url_for('routes.listar_quebras_alca', id=cab.id))

    return render_template('producao/nova_quebra_alca.html', form=form)

## API PARA PEGAR OS TAMANHOS DAS ALCAS
@bp.route('/quebra_alca/tamanhos', methods=['GET'])
@login_required
def api_quebra_alca_tamanhos():
    from app.models import Alca
    alca_id = request.args.get('alca_id', type=int)
    if not alca_id:
        return jsonify({'ok': False, 'msg': 'Parâmetro alca_id ausente.'}), 400

    alca = Alca.query.get(alca_id)
    if not alca:
        return jsonify({'ok': False, 'msg': 'Alça não encontrada.'}), 404

    tamanhos = [{'id': t.id, 'nome': t.nome} for t in (alca.tamanhos or [])]
    return jsonify({'ok': True, 'tamanhos': tamanhos})

@bp.route('/quebra_alca/<int:id>', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def ver_quebra_alca(id):
    qp = (QuebraAlca.query
          .options(db.selectinload(QuebraAlca.linhas), db.joinedload(QuebraAlca.alca))
          .get_or_404(id))
    return render_template('producao/ver_quebra_alca.html', it=qp)

# ------- EDITAR (Quebra de Alça) -------
@bp.route('/quebra_alca/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_quebra_alca(id):
    from sqlalchemy.orm import selectinload
    from app.models import QuebraAlca, QuebraAlcaLinha, Alca, TamanhoAlca
    qp = (QuebraAlca.query
          .options(selectinload(QuebraAlca.linhas))
          .get_or_404(id))

    form = QuebraAlcaForm(obj=qp)
    form.alca_id.choices = [(0, '-- Selecione --')] + [
        (a.id, f'{a.referencia} — {a.descricao}') for a in Alca.query.order_by(Alca.referencia).all()
    ]

    # Mapa de qtd atual por tamanho (para preencher inputs)
    qtd_por_tam = {l.tamanho_alca_id: (l.quantidade or 0) for l in qp.linhas}

    # lista de tamanhos da alça selecionada (GET mostra a atual)
    alca_id_atual = form.alca_id.data or qp.alca_id
    tamanhos = []
    if alca_id_atual:
        tamanhos = [(t.id, t.nome) for t in TamanhoAlca.query.filter_by(alca_id=alca_id_atual).order_by(TamanhoAlca.nome).all()]

    # GET
    if request.method == 'GET':
        return render_template('producao/editar_quebra_alca.html', form=form, it=qp,
                               tamanhos=tamanhos, qtd_por_tam=qtd_por_tam)

    # POST
    if form.validate_on_submit():
        # checagem anti-duplicidade (mesma data + mesma alça), ignorando o próprio id
        ja_existe = (QuebraAlca.query
                     .filter(QuebraAlca.id != qp.id,
                             QuebraAlca.data_quebra == form.data_quebra.data,
                             QuebraAlca.alca_id == form.alca_id.data)
                     .first())
        if ja_existe:
            flash('Já existe quebra cadastrada para esta alça nesta data.', 'warning')
            return render_template('producao/editar_quebra_alca.html', form=form, it=qp,
                                   tamanhos=tamanhos, qtd_por_tam=qtd_por_tam), 409

        # Atualiza cabeçalho
        qp.data_quebra = form.data_quebra.data
        qp.alca_id     = form.alca_id.data
        qp.observacao  = form.observacao.data or None

        # Recarregar tamanhos conforme alça (pode ter trocado)
        tamanhos_db = TamanhoAlca.query.filter_by(alca_id=qp.alca_id).all()

        # Substituir linhas (mais simples e seguro)
        # Remove antigas
        for l in list(qp.linhas):
            db.session.delete(l)
        db.session.flush()

        # Adiciona as novas com base no POST: qtd_<tamanho_alca_id>
        adicionou = False
        for t in tamanhos_db:
            qtd = request.form.get(f'qtd_{t.id}', '').strip()
            if qtd == '':
                continue
            try:
                v = int(qtd)
            except ValueError:
                v = 0
            if v > 0:
                adicionou = True
                db.session.add(QuebraAlcaLinha(
                    quebra_id=qp.id,
                    tamanho_alca_id=t.id,
                    tamanho_nome=t.nome,
                    quantidade=v
                ))

        if not adicionou:
            flash('Informe pelo menos uma quantidade de quebra em algum tamanho.', 'warning')
            db.session.rollback()
            # re-render mantendo a grade
            tamanhos = [(t.id, t.nome) for t in tamanhos_db]
            qtd_por_tam = {}  # após falha, zera
            return render_template('producao/editar_quebra_alca.html', form=form, it=qp,
                                   tamanhos=tamanhos, qtd_por_tam=qtd_por_tam)

        db.session.commit()
        flash('Quebra de produção (Alça) atualizada!', 'success')
        return redirect(url_for('routes.ver_quebra_alca', id=qp.id))

    # se falhar validação
    return render_template('producao/editar_quebra_alca.html', form=form, it=qp,
                           tamanhos=tamanhos, qtd_por_tam=qtd_por_tam)

# ------- EXCLUIR (Quebra de Alça) -------
@bp.route('/quebra_alca/<int:id>/excluir', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_quebra_alca(id):
    from app.models import QuebraAlca
    qp = QuebraAlca.query.get_or_404(id)

    db.session.delete(qp)
    db.session.commit()
    flash('Quebra de produção (Alça) excluída com sucesso!', 'success')
    return redirect(url_for('routes.listar_quebras_alca'))


# ------- RELATÓRIO (HTML) -------
@bp.route('/quebras_alca/relatorio', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_quebras_alca():
    from sqlalchemy.orm import selectinload
    from app.models import QuebraAlca, Alca

    # Filtros
    alca_id = request.args.get('alca_id', type=int)
    inicio  = (request.args.get('inicio') or '').strip()  # YYYY-MM-DD
    fim     = (request.args.get('fim') or '').strip()     # YYYY-MM-DD

    # Flag para só mostrar dados após clique em Filtrar
    aplicou = request.args.get('aplicar') == '1'
    di = df = None

    # Choices de alças
    alcas = [(a.id, f'{a.referencia} — {a.descricao}')
             for a in Alca.query.order_by(Alca.referencia).all()]

    q = (QuebraAlca.query
         .options(selectinload(QuebraAlca.alca),
                  selectinload(QuebraAlca.linhas))
         .order_by(QuebraAlca.data_quebra.asc(), QuebraAlca.id.asc()))

    # Se usuário clicou em "Filtrar":
    if aplicou:
        # Data início
        if inicio:
            try:
                di = datetime.strptime(inicio, '%Y-%m-%d').date()
                q = q.filter(QuebraAlca.data_quebra >= di)
            except Exception:
                flash('Data inicial inválida.', 'warning')

        # Data fim
        if fim:
            try:
                df = datetime.strptime(fim, '%Y-%m-%d').date()
                q = q.filter(QuebraAlca.data_quebra <= df)
            except Exception:
                flash('Data final inválida.', 'warning')

        # Alça
        if alca_id:
            q = q.filter(QuebraAlca.alca_id == alca_id)

        itens = q.all()
    else:
        itens = []  # Não mostrar nada até clicar em Filtrar

    # Total geral (somatório de todas as linhas)
    total = 0
    for cab in itens:
        total += sum(l.quantidade or 0 for l in cab.linhas)

    return render_template(
        'producao/relatorio_quebras_alca.html',
        itens=itens,
        total=total,
        alcas=alcas,
        alca_id=alca_id or '',
        inicio=inicio,
        fim=fim,
        di=di, df=df,
        aplicou=aplicou
    )


# ------- RELATÓRIO (PDF) -------
@bp.route('/quebras_alca/relatorio/pdf', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_quebras_alca_pdf():
    from sqlalchemy.orm import selectinload
    from app.models import QuebraAlca, Alca

    alca_id = request.args.get('alca_id', type=int)
    inicio  = (request.args.get('inicio') or '').strip()
    fim     = (request.args.get('fim') or '').strip()

    di = df = None

    q = (QuebraAlca.query
         .options(selectinload(QuebraAlca.alca),
                  selectinload(QuebraAlca.linhas))
         .order_by(QuebraAlca.data_quebra.asc(), QuebraAlca.id.asc()))

    if inicio:
        try:
            di = datetime.strptime(inicio, '%Y-%m-%d').date()
            q = q.filter(QuebraAlca.data_quebra >= di)
        except Exception:
            pass

    if fim:
        try:
            df = datetime.strptime(fim, '%Y-%m-%d').date()
            q = q.filter(QuebraAlca.data_quebra <= df)
        except Exception:
            pass

    if alca_id:
        q = q.filter(QuebraAlca.alca_id == alca_id)

    itens = q.all()

    total = 0
    for cab in itens:
        total += sum(l.quantidade or 0 for l in cab.linhas)

    # Renderiza HTML base e transforma em PDF
    html = render_template(
        'producao/relatorio_quebras_alca_pdf.html',
        itens=itens, total=total,
        di=di, df=df,
        alca=Alca.query.get(alca_id) if alca_id else None
    )

    # WeasyPrint
    from weasyprint import HTML
    pdf = HTML(string=html, base_url=request.url_root).write_pdf()

    filename = 'relatorio_quebras_alca.pdf'
    return Response(
        pdf,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'inline; filename={filename}'}
    )



# =========================
#   QUEBRA DE SOLADO
# =========================

# ------- LISTAR (Quebras de Solado) -------
@bp.route('/quebras_solado', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def listar_quebras_solado():
    from urllib.parse import urlencode
    from sqlalchemy.orm import selectinload
    from app.models import QuebraSolado, Solado

    # filtros
    f_data     = (request.args.get('data') or '').strip()      # 'YYYY-MM-DD'
    f_solado_id = request.args.get('solado_id', type=int)      # id do solado
    page       = request.args.get('page', 1, type=int)
    per_page   = request.args.get('per_page', 20, type=int)
    per_page   = max(5, min(per_page, 200))

    # choices solados
    solados = [(s.id, f'{s.referencia} — {s.descricao}') for s in Solado.query.order_by(Solado.referencia).all()]

    # base query
    q = (QuebraSolado.query
         .options(selectinload(QuebraSolado.solado), selectinload(QuebraSolado.linhas))
         .order_by(QuebraSolado.data_quebra.desc(), QuebraSolado.id.desc()))

    data_sel = None
    if f_data:
        try:
            data_sel = datetime.strptime(f_data, '%Y-%m-%d').date()
            q = q.filter(QuebraSolado.data_quebra == data_sel)
        except Exception:
            flash('Data inválida.', 'warning')

    if f_solado_id:
        q = q.filter(QuebraSolado.solado_id == f_solado_id)

    # paginação compatível 2.x/3.x
    try:
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    except AttributeError:
        from app import db
        pagination = db.paginate(q, page=page, per_page=per_page, error_out=False)

    itens = pagination.items

    # soma por cabeçalho
    totais = {it.id: sum(l.quantidade or 0 for l in it.linhas) for it in itens}

    # querystring sem page
    qs_dict = request.args.to_dict(flat=True)
    qs_dict.pop('page', None)
    qs_no_page = urlencode(qs_dict)

    return render_template(
        'producao/listar_quebras_solado.html',
        itens=itens,
        pagination=pagination,
        per_page=per_page,
        solados=solados,
        f_solado_id=f_solado_id or '',
        data_sel=data_sel,
        qs_no_page=qs_no_page,
        totais=totais
    )


# ------- NOVA (Quebra de Solado) -------
@bp.route('/quebra_solado/nova', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'criar')
def nova_quebra_solado():
    from app.models import Solado, Tamanho
    form = QuebraSoladoForm()

    # Select de Solados
    form.solado_id.choices = [(0, '-- Selecione --')] + [
        (s.id, f'{s.referencia} — {s.descricao}') for s in Solado.query.order_by(Solado.referencia).all()
    ]

    # Data padrão hoje
    if request.method == 'GET' and not form.data_quebra.data:
        form.data_quebra.data = date.today()

    if form.validate_on_submit():
        if not form.solado_id.data:
            form.solado_id.errors.append('Selecione um solado.')
            return render_template('producao/nova_quebra_solado.html', form=form)

        # Anti-duplicidade: mesma data + mesmo solado
        ja_existe = (QuebraSolado.query
                     .filter(QuebraSolado.data_quebra == form.data_quebra.data,
                             QuebraSolado.solado_id == form.solado_id.data)
                     .first())
        if ja_existe:
            flash('Já existe quebra cadastrada para este solado nesta data.', 'warning')
            return render_template('producao/nova_quebra_solado.html', form=form), 409

        # Coletar quantidades: qtd_<tamanho_id>
        linhas = []
        for key, val in request.form.items():
            if key.startswith('qtd_'):
                try:
                    tam_id = int(key.replace('qtd_', ''))
                    qtd = int(val or 0)
                except ValueError:
                    continue
                if qtd > 0:
                    t = Tamanho.query.get(tam_id)
                    if t and t.solado_id == form.solado_id.data:
                        linhas.append((t.id, t.nome, qtd))

        if not linhas:
            flash('Informe pelo menos uma quantidade de quebra em algum tamanho.', 'warning')
            return render_template('producao/nova_quebra_solado.html', form=form)

        # Persistir
        cab = QuebraSolado(
            data_quebra=form.data_quebra.data,
            observacao=form.observacao.data or None,
            solado_id=form.solado_id.data
        )
        db.session.add(cab)
        db.session.flush()

        for tam_id, nome, qtd in linhas:
            db.session.add(QuebraSoladoLinha(
                quebra_id=cab.id,
                tamanho_solado_id=tam_id,
                tamanho_nome=nome,
                quantidade=qtd
            ))

        db.session.commit()
        flash('Quebra de produção (Solado) registrada!', 'success')
        return redirect(url_for('routes.listar_quebras_solado'))

    return render_template('producao/nova_quebra_solado.html', form=form)


# ------- API: tamanhos do Solado (AJAX) -------
@bp.route('/quebra_solado/tamanhos', methods=['GET'])
@login_required
def api_quebra_solado_tamanhos():
    from app.models import Solado
    solado_id = request.args.get('solado_id', type=int)
    if not solado_id:
        return jsonify({'ok': False, 'msg': 'Parâmetro solado_id ausente.'}), 400

    solado = Solado.query.get(solado_id)
    if not solado:
        return jsonify({'ok': False, 'msg': 'Solado não encontrado.'}), 404

    # mesma estratégia de ordenação usada na Alça: numéricos primeiro, '--' por último
    def ordena_chave(nome):
        # retorna tupla para sort: (flag_non_numeric, numero_int_ou_grande, nome)
        import re
        if nome == '--':
            return (2, 10**9, nome)
        m = re.match(r'^\D*(\d+)\D*$', nome or '')
        if m:
            return (0, int(m.group(1)), nome)
        return (1, 10**9, nome or '')
    tamanhos = sorted(solado.tamanhos or [], key=lambda t: ordena_chave(t.nome))

    payload = [{'id': t.id, 'nome': t.nome} for t in tamanhos]
    return jsonify({'ok': True, 'tamanhos': payload})



# ------- VER (Quebra de Solado) -------
@bp.route('/quebra_solado/<int:id>', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def ver_quebra_solado(id):
    from sqlalchemy.orm import selectinload
    from app.models import QuebraSolado

    qp = (QuebraSolado.query
          .options(selectinload(QuebraSolado.linhas), selectinload(QuebraSolado.solado))
          .get_or_404(id))

    # 🔹 total geral (somatório das linhas)
    total_geral = sum((l.quantidade or 0) for l in (qp.linhas or []))

    return render_template('producao/ver_quebra_solado.html', it=qp, total_geral=total_geral)



# ------- EDITAR (Quebra de Solado) -------
@bp.route('/quebra_solado/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao('controleproducao', 'editar')
def editar_quebra_solado(id):
    from sqlalchemy.orm import selectinload
    from sqlalchemy import case, func, cast, Integer
    from app.models import QuebraSolado, QuebraSoladoLinha, Solado, Tamanho

    # ordenação equivalente à da Alça
    def ordenacao_tamanhos():
        return (
            case((Tamanho.nome == '--', 1), else_=0).asc(),
            case((Tamanho.nome.op('~')(r'^\d'), 0), else_=1).asc(),
            cast(func.nullif(func.regexp_replace(Tamanho.nome, r'\D', '', 'g'), ''), Integer).asc(),
            Tamanho.nome.asc()
        )

    qp = (QuebraSolado.query
          .options(selectinload(QuebraSolado.linhas))
          .get_or_404(id))

    form = QuebraSoladoForm(obj=qp)
    form.solado_id.choices = [(0, '-- Selecione --')] + [
        (s.id, f'{s.referencia} — {s.descricao}') for s in Solado.query.order_by(Solado.referencia).all()
    ]

    qtd_por_tam = {l.tamanho_solado_id: (l.quantidade or 0) for l in qp.linhas}

    solado_id_atual = form.solado_id.data or qp.solado_id
    tamanhos = []
    if solado_id_atual:
        tamanhos = [(t.id, t.nome) for t in
                    Tamanho.query
                    .filter_by(solado_id=solado_id_atual)
                    .order_by(*ordenacao_tamanhos())
                    .all()]

    if request.method == 'GET':
        return render_template('producao/editar_quebra_solado.html', form=form, it=qp,
                               tamanhos=tamanhos, qtd_por_tam=qtd_por_tam)

    if form.validate_on_submit():
        # anti-duplicidade (mesma data + mesmo solado), ignorando o próprio id
        ja_existe = (QuebraSolado.query
                     .filter(QuebraSolado.id != qp.id,
                             QuebraSolado.data_quebra == form.data_quebra.data,
                             QuebraSolado.solado_id == form.solado_id.data)
                     .first())
        if ja_existe:
            flash('Já existe quebra cadastrada para este solado nesta data.', 'warning')
            return render_template('producao/editar_quebra_solado.html', form=form, it=qp,
                                   tamanhos=tamanhos, qtd_por_tam=qtd_por_tam), 409

        # atualiza cabeçalho
        qp.data_quebra = form.data_quebra.data
        qp.solado_id   = form.solado_id.data
        qp.observacao  = form.observacao.data or None

        # recarrega tamanhos do solado escolhido
        tamanhos_db = (Tamanho.query
                       .filter_by(solado_id=qp.solado_id)
                       .order_by(*ordenacao_tamanhos())
                       .all())

        # substitui as linhas
        for l in list(qp.linhas):
            db.session.delete(l)
        db.session.flush()

        adicionou = False
        for t in tamanhos_db:
            qtd = (request.form.get(f'qtd_{t.id}', '') or '').strip()
            if qtd == '':
                continue
            try:
                v = int(qtd)
            except ValueError:
                v = 0
            if v > 0:
                adicionou = True
                db.session.add(QuebraSoladoLinha(
                    quebra_id=qp.id,
                    tamanho_solado_id=t.id,
                    tamanho_nome=t.nome,
                    quantidade=v
                ))

        if not adicionou:
            flash('Informe pelo menos uma quantidade de quebra em algum tamanho.', 'warning')
            db.session.rollback()
            tamanhos = [(t.id, t.nome) for t in tamanhos_db]
            qtd_por_tam = {}
            return render_template('producao/editar_quebra_solado.html', form=form, it=qp,
                                   tamanhos=tamanhos, qtd_por_tam=qtd_por_tam)

        db.session.commit()
        flash('Quebra de produção (Solado) atualizada!', 'success')
        return redirect(url_for('routes.ver_quebra_solado', id=qp.id))

    return render_template('producao/editar_quebra_solado.html', form=form, it=qp,
                           tamanhos=tamanhos, qtd_por_tam=qtd_por_tam)


# ------- EXCLUIR (Quebra de Solado) -------
@bp.route('/quebra_solado/<int:id>/excluir', methods=['POST'])
@login_required
@requer_permissao('controleproducao', 'excluir')
def excluir_quebra_solado(id):
    from app.models import QuebraSolado
    qp = QuebraSolado.query.get_or_404(id)

    db.session.delete(qp)
    db.session.commit()
    flash('Quebra de produção (Solado) excluída com sucesso!', 'success')
    return redirect(url_for('routes.listar_quebras_solado'))

# ------- RELATÓRIO (HTML) — Quebra de Solado -------
@bp.route('/quebras_solado/relatorio', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_quebras_solado():
    from sqlalchemy.orm import selectinload
    from app.models import QuebraSolado, Solado

    # Filtros
    solado_id = request.args.get('solado_id', type=int)
    inicio    = (request.args.get('inicio') or '').strip()  # YYYY-MM-DD
    fim       = (request.args.get('fim') or '').strip()     # YYYY-MM-DD

    # Só mostra após clicar em Filtrar
    aplicou = request.args.get('aplicar') == '1'
    di = df = None

    # Choices de solados
    solados = [(s.id, f'{s.referencia} — {s.descricao}')
               for s in Solado.query.order_by(Solado.referencia).all()]

    q = (QuebraSolado.query
         .options(selectinload(QuebraSolado.solado),
                  selectinload(QuebraSolado.linhas))
         .order_by(QuebraSolado.data_quebra.asc(), QuebraSolado.id.asc()))

    itens = []
    if aplicou:
        # Data início
        if inicio:
            try:
                di = datetime.strptime(inicio, '%Y-%m-%d').date()
                q = q.filter(QuebraSolado.data_quebra >= di)
            except Exception:
                flash('Data inicial inválida.', 'warning')
        # Data fim
        if fim:
            try:
                df = datetime.strptime(fim, '%Y-%m-%d').date()
                q = q.filter(QuebraSolado.data_quebra <= df)
            except Exception:
                flash('Data final inválida.', 'warning')
        # Solado
        if solado_id:
            q = q.filter(QuebraSolado.solado_id == solado_id)

        itens = q.all()

    # Total geral
    total = sum(
        sum(l.quantidade or 0 for l in cab.linhas)
        for cab in itens
    )

    return render_template(
        'producao/relatorio_quebras_solado.html',
        itens=itens,
        total=total,
        solados=solados,
        solado_id=solado_id or '',
        inicio=inicio,
        fim=fim,
        di=di, df=df,
        aplicou=aplicou
    )


# ------- RELATÓRIO (PDF) — Quebra de Solado -------
@bp.route('/quebras_solado/relatorio/pdf', methods=['GET'])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_quebras_solado_pdf():
    from sqlalchemy.orm import selectinload
    from app.models import QuebraSolado, Solado

    solado_id = request.args.get('solado_id', type=int)
    inicio    = (request.args.get('inicio') or '').strip()
    fim       = (request.args.get('fim') or '').strip()

    di = df = None

    q = (QuebraSolado.query
         .options(selectinload(QuebraSolado.solado),
                  selectinload(QuebraSolado.linhas))
         .order_by(QuebraSolado.data_quebra.asc(), QuebraSolado.id.asc()))

    if inicio:
        try:
            di = datetime.strptime(inicio, '%Y-%m-%d').date()
            q = q.filter(QuebraSolado.data_quebra >= di)
        except Exception:
            pass

    if fim:
        try:
            df = datetime.strptime(fim, '%Y-%m-%d').date()
            q = q.filter(QuebraSolado.data_quebra <= df)
        except Exception:
            pass

    if solado_id:
        q = q.filter(QuebraSolado.solado_id == solado_id)

    itens = q.all()

    total = sum(
        sum(l.quantidade or 0 for l in cab.linhas)
        for cab in itens
    )

    html = render_template(
        'producao/relatorio_quebras_solado_pdf.html',
        itens=itens, total=total,
        di=di, df=df,
        solado=Solado.query.get(solado_id) if solado_id else None
    )

    from weasyprint import HTML
    pdf = HTML(string=html, base_url=request.url_root).write_pdf()

    filename = 'relatorio_quebras_solado.pdf'
    return Response(
        pdf,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'inline; filename={filename}'}
    )


### REMESSAS FALTANTES  - SALDO   ####
@bp.route("/relatorios/remessas/faltantes", methods=["GET"])
@login_required
@requer_permissao('controleproducao', 'ver')
def relatorio_faltantes_remessas():
    remessa_ids = request.args.getlist("remessa_id", type=int)
    ref_query   = (request.args.get("referencia") or "").strip()
    fonte       = (request.args.get("fonte") or "diaria").lower()  # 'esteira' | 'diaria'
    somente_fechados = request.args.get("somente_fechados") == "1"

    # Carrega remessas para o filtro
    todas_remessas = (Remessa.query.order_by(Remessa.id.desc()).limit(300).all())

    # 🚫 Sem remessas selecionadas: não busca nada
    if not remessa_ids:
        return render_template(
            "relatorios/relatorio_faltantes_remessas.html",
            remessa_data={},
            todas_remessas=todas_remessas,
            filtros={
                "remessa_ids": remessa_ids,
                "referencia": ref_query,
                "fonte": fonte,
                "somente_fechados": somente_fechados
            }
        )

    # Planejamentos filtrados
    qp = (PlanejamentoProducao.query
          .options(joinedload(PlanejamentoProducao.remessa))
          .join(PlanejamentoProducao.remessa)
          .filter(PlanejamentoProducao.remessa_id.in_(remessa_ids)))

    if ref_query:
        qp = qp.filter(PlanejamentoProducao.referencia.ilike(f"%{ref_query}%"))

    if somente_fechados:
        qp = qp.filter(PlanejamentoProducao.fechado.is_(True))

    planejamentos = qp.all()

    # Agrega Produção Diária só quando for a fonte
    producao_por_planejamento = {}
    if fonte == "diaria" and planejamentos:
        pl_ids = [p.id for p in planejamentos]
        rows = (db.session.query(
                    ProducaoDiaria.planejamento_id,
                    func.coalesce(func.sum(ProducaoDiaria.quantidade), 0).label("qtd")
                )
                .filter(ProducaoDiaria.planejamento_id.in_(pl_ids))
                .group_by(ProducaoDiaria.planejamento_id)
                .all())
        producao_por_planejamento = {r.planejamento_id: int(r.qtd or 0) for r in rows}

    remessa_data = {}
    for p in planejamentos:
        rid = p.remessa_id
        if rid not in remessa_data:
            remessa_data[rid] = {
                "remessa": p.remessa,
                "total_planejado": 0,
                "total_produzido": 0,
                "faltantes": []
            }

        planejado = int(p.quantidade or 0)
        produzido = int(p.esteira_qtd or 0) if fonte == "esteira" else int(producao_por_planejamento.get(p.id, 0))
        faltando  = max(planejado - produzido, 0)

        remessa_data[rid]["total_planejado"] += planejado
        remessa_data[rid]["total_produzido"] += produzido

        # ✅ SEM FILTRO: adicionar SEMPRE, mesmo faltando = 0
        remessa_data[rid]["faltantes"].append({
            "referencia": p.referencia,
            "setor": p.setor,
            "fechado": bool(p.fechado),
            "planejado": planejado,
            "produzido": produzido,
            "faltando": faltando,
        })

    for rid, data in remessa_data.items():
        data["total_restante"] = max(data["total_planejado"] - data["total_produzido"], 0)
        # mantém as que faltam primeiro, depois as completas
        data["faltantes"].sort(key=lambda x: x["faltando"], reverse=True)

    return render_template(
        "relatorios/relatorio_faltantes_remessas.html",
        remessa_data=remessa_data,
        todas_remessas=todas_remessas,
        filtros={
            "remessa_ids": remessa_ids,
            "referencia": ref_query,
            "fonte": fonte,
            "somente_fechados": somente_fechados
        }
    )
