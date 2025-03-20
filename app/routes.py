from sqlite3 import IntegrityError
from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import FormulacaoSolado, FormulacaoSoladoFriso, Funcionario, LogAcao, Maquina, MargemPorPedido, MargemPorPedidoReferencia, Referencia, Componente, CustoOperacional, ReferenciaAlca, ReferenciaComponentes, ReferenciaCustoOperacional, ReferenciaEmbalagem1, ReferenciaEmbalagem2, ReferenciaEmbalagem3, ReferenciaMaoDeObra, ReferenciaSolado, Salario, MaoDeObra, Margem, TrocaHorario, TrocaMatriz
from app.forms import FuncionarioForm, MaquinaForm, MargemForm, MargemPorPedidoForm, MargemPorPedidoReferenciaForm, ReferenciaForm, ComponenteForm, CustoOperacionalForm, SalarioForm, MaoDeObraForm, TrocaMatrizForm
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
import pandas as pd
from flask import request, jsonify
from werkzeug.utils import secure_filename
from flask import current_app
from app.utils import allowed_file




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

@bp.route('/home_mobile')
@login_required
def home_mobile():
    return render_template('home_mobile.html')


    #REFERENCIAS


@bp.route('/referencias', methods=['GET'])
@login_required
def listar_referencias():
    filtro = request.args.get('filtro', '')

    if filtro:
        referencias = Referencia.query.filter(Referencia.codigo_referencia.ilike(f"%{filtro}%")).all()
    else:
        referencias = Referencia.query.order_by(Referencia.id.desc()).all()

    # 🔹 Garante que os cálculos sejam atualizados antes de exibir
    for referencia in referencias:
        referencia.calcular_totais()
        db.session.add(referencia)  # 🔹 Adiciona a referência para ser salva
    db.session.commit()  # 🔹 Salva as alterações no banco

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
    form.colecao_id.choices = [(c.id, c.codigo) for c in Colecao.query.all()]

    # Recupera os dados para os modais
    solados = Solado.query.all()
    alcas = Alca.query.all()
    componentes = Componente.query.all()
    custos_operacionais = CustoOperacional.query.all()
    mao_de_obra = MaoDeObra.query.all()
    colecoes = Colecao.query.all()

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


@bp.route('/componentes', methods=['GET'])
@login_required
def listar_componentes():
    filtro = request.args.get('filtro', '')
    
    if filtro == "TODOS":
        componentes = Componente.query.order_by(Componente.id.desc()).all()
    elif filtro:
        componentes = Componente.query.filter(Componente.descricao.ilike(f"%{filtro}%")).order_by(Componente.id.desc()).all()
    else:
        componentes = Componente.query.order_by(Componente.id.desc()).all()  # Garante a ordenação mesmo sem filtro
    
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

@bp.route('/mao_de_obra', methods=['GET'])
@login_required
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



@bp.route('/margens_pedido', methods=['GET'])
@login_required
def listar_margens_pedido():
    filtro = request.args.get('filtro', '')
    if filtro:
        margens = MargemPorPedido.query.filter(MargemPorPedido.pedido.ilike(f"%{filtro}%")).all()
    else:
        margens = MargemPorPedido.query.order_by(MargemPorPedido.id.desc()).all()
    return render_template('margens_pedido.html', margens=margens)



@bp.route('/margem_pedido/novo', methods=['GET', 'POST'])
@login_required
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
            embalagem_escolhida = request.form.get(f"embalagem_{ref_id}")
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



@bp.route('/margem_pedido/ver/<int:id>')
@login_required
def ver_margem_pedido(id):
    """ Exibe os detalhes de uma margem por pedido """
    margem = MargemPorPedido.query.get_or_404(id)
    return render_template('ver_margem_pedido.html', margem=margem)


@bp.route('/margem_pedido/excluir/<int:id>', methods=['GET', 'POST'])
@login_required
def excluir_margem_pedido(id):
    """ Exclui apenas a margem por pedido """
    margem = MargemPorPedido.query.get_or_404(id)

    try:
        db.session.delete(margem)  
        db.session.commit()
        flash("Margem por pedido excluída com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir margem: {str(e)}", "danger")

    return redirect(url_for('routes.listar_margens_pedido'))



@bp.route('/custo_remessa', methods=['GET', 'POST'])
@login_required
def custo_remessa():
    margem_pedidos = []
    totais = {
        "total_preco_venda": Decimal(0),
        "total_custo": Decimal(0),
        "lucro_total": Decimal(0),
        "margem_media": Decimal(0),
    }

    if request.method == "POST":
        codigo_remessa = request.form.get("remessa").strip()

        if codigo_remessa:
            margem_pedidos = MargemPorPedido.query.filter_by(remessa=codigo_remessa).all()

            if margem_pedidos:
                # 🔹 Calculando os totais de todas as margens filtradas
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

    return render_template("custo_remessa.html", margem_pedidos=margem_pedidos, totais=totais)



 ####  IMPORTAÇÕES   #######


@bp.route('/margem_pedido/importar', methods=['POST'])
@login_required
def importar_referencias():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado"})

    file = request.files['file']

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Arquivo inválido"})

    from werkzeug.utils import secure_filename
    import pandas as pd
    import os

    filename = secure_filename(file.filename)
    filepath = os.path.join('app/static/uploads', filename)
    file.save(filepath)

    # Lendo o arquivo e processando os dados
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            df = pd.read_csv(filepath, delimiter=";")  # Ajuste conforme necessário

        referencias = []
        for _, row in df.iterrows():
            # Buscar a referência pelo código, e **não pelo ID**
            referencia = Referencia.query.filter_by(codigo_referencia=row["Código Referência"]).first()

            if referencia:
                referencias.append({
                    "codigo": referencia.codigo_referencia,
                    "descricao": referencia.descricao,
                    "quantidade": row["Quantidade"],
                    "embalagem": row["Embalagem"],
                    "preco_venda": row["Preço Venda"]
                })

        return jsonify({"success": True, "referencias": referencias})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})





@bp.route('/importar_componentes', methods=['POST'])
@login_required
def importar_componentes():
    if 'file' not in request.files:
        flash("Nenhum arquivo enviado.", "danger")
        return redirect(url_for('routes.listar_componentes'))  # Redireciona de volta

    file = request.files['file']

    if file.filename == '':
        flash("Arquivo inválido.", "danger")
        return redirect(url_for('routes.listar_componentes'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath, dtype={'codigo': str})
        atualizados = 0
        criados = 0

        for _, row in df.iterrows():
            codigo = row['codigo']
            descricao = row['descricao']
            tipo = row['tipo']
            unidade_medida = row['unidade_medida']
            preco = Decimal(str(row['preco']).replace(',', '.'))

            componente = Componente.query.filter_by(codigo=codigo).first()

            if componente:
                # 📌 Verifica se os valores realmente mudaram antes de atualizar
                if (
                    componente.descricao != descricao or
                    componente.tipo != tipo or
                    componente.unidade_medida != unidade_medida or
                    componente.preco != preco
                ):
                    componente.descricao = descricao
                    componente.tipo = tipo
                    componente.unidade_medida = unidade_medida
                    componente.preco = preco
                    atualizados += 1
            else:
                # 📌 Cria um novo componente se não existir
                novo_componente = Componente(
                    codigo=codigo,
                    descricao=descricao,
                    tipo=tipo,
                    unidade_medida=unidade_medida,
                    preco=preco
                )
                db.session.add(novo_componente)
                criados += 1

        db.session.commit()
        flash(f"Importação concluída! {criados} componentes criados, {atualizados} atualizados.", "success")

    except Exception as e:
        flash(f"Erro ao processar arquivo: {str(e)}", "danger")

    finally:
        os.remove(filepath)  # Remove o arquivo temporário

    return redirect(url_for('routes.listar_componentes'))  # 🔹 Redireciona corretamente para listar componentes


@bp.route('/importar_solados', methods=['POST'])
@login_required
def importar_solados():
    if 'file' not in request.files:
        flash("Nenhum arquivo enviado.", "danger")
        return redirect(url_for('routes.listar_solados'))

    file = request.files['file']

    if file.filename == '':
        flash("Arquivo inválido.", "danger")
        return redirect(url_for('routes.listar_solados'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath, dtype={'referencia': str})

        atualizados = 0
        criados = 0

        for _, row in df.iterrows():
            referencia = row['referencia']
            descricao = row['descricao']
            imagem = row['imagem']
            tamanhos = row['tamanhos'].split(",")  # 🔹 Lista de tamanhos
            grades = list(map(int, row['grade'].split(",")))  # 🔹 Lista de grades como inteiros
            peso_medio = row['peso_medio']
            peso_friso = row['peso_friso']
            peso_sem_friso = row['peso_sem_friso']
            comp_friso = row['comp_friso']
            carga_friso = Decimal(str(row['carga_friso']).replace(',', '.'))
            comp_sem_friso = row['comp_sem_friso']
            carga_sem_friso = Decimal(str(row['carga_sem_friso']).replace(',', '.'))

            # Verifica se o solado já existe
            solado = Solado.query.filter_by(referencia=referencia).first()

            if solado:
                # Atualiza os dados existentes
                solado.descricao = descricao
                solado.imagem = imagem
                solado.tamanhos.clear()  # 🔹 Remove tamanhos antigos

                for tamanho, grade in zip(tamanhos, grades):
                    novo_tamanho = Tamanho(
                        solado_id=solado.id, nome=tamanho, quantidade=grade,
                        peso_medio=peso_medio, peso_friso=peso_friso, peso_sem_friso=peso_sem_friso
                    )
                    db.session.add(novo_tamanho)

                atualizados += 1
            else:
                # Criando um novo solado
                novo_solado = Solado(
                    referencia=referencia,
                    descricao=descricao,
                    imagem=imagem
                )
                db.session.add(novo_solado)
                db.session.flush()  # Obtém o ID antes de salvar

                for tamanho, grade in zip(tamanhos, grades):
                    novo_tamanho = Tamanho(
                        solado_id=novo_solado.id, nome=tamanho, quantidade=grade,
                        peso_medio=peso_medio, peso_friso=peso_friso, peso_sem_friso=peso_sem_friso
                    )
                    db.session.add(novo_tamanho)

                criados += 1

            # **Tratamento da formulação**
            if comp_friso:
                componente_friso = Componente.query.filter_by(codigo=comp_friso).first()
                if componente_friso:
                    formulacao_friso = FormulacaoSoladoFriso(
                        solado_id=solado.id if solado else novo_solado.id,
                        componente_id=componente_friso.id,
                        carga=carga_friso
                    )
                    db.session.add(formulacao_friso)

            if comp_sem_friso:
                componente_sem_friso = Componente.query.filter_by(codigo=comp_sem_friso).first()
                if componente_sem_friso:
                    formulacao_sem_friso = FormulacaoSolado(
                        solado_id=solado.id if solado else novo_solado.id,
                        componente_id=componente_sem_friso.id,
                        carga=carga_sem_friso
                    )
                    db.session.add(formulacao_sem_friso)

        db.session.commit()
        flash(f"Importação concluída! {criados} solados criados, {atualizados} atualizados.", "success")

    except Exception as e:
        flash(f"Erro ao processar arquivo: {str(e)}", "danger")

    finally:
        os.remove(filepath)

    return redirect(url_for('routes.listar_solados'))





#########  CONTROLE DE PRODUÇÃO ##########

@bp.route('/maquinas', methods=['GET'])
@login_required
def listar_maquinas():
    """ Lista todas as máquinas cadastradas """
    filtro = request.args.get('filtro', '')
    maquinas = Maquina.query.filter(Maquina.descricao.ilike(f"%{filtro}%")).order_by(Maquina.id.desc()).all()
    return render_template('maquinas.html', maquinas=maquinas)




@bp.route('/maquina/nova', methods=['GET', 'POST'])
@login_required
def nova_maquina():
    form = MaquinaForm()
    if form.validate_on_submit():
        maquina = Maquina(
            codigo=form.codigo.data,
            descricao=form.descricao.data,
            tipo=form.tipo.data,
            status=form.status.data,
            preco=form.preco.data
            
        )
        db.session.add(maquina)
        db.session.commit()
        flash('Maquina adicionada com sucesso!', 'success')
        return redirect(url_for('routes.listar_maquinas'))
    return render_template('nova_maquina.html', form=form)


@bp.route('/maquina/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_maquina(id):
    """ Edita uma máquina existente """
    maquina = Maquina.query.get_or_404(id)
    form = MaquinaForm(obj=maquina)

    if form.validate_on_submit():
        maquina.codigo = form.codigo.data
        maquina.descricao = form.descricao.data
        maquina.tipo = form.tipo.data
        maquina.status = form.status.data
        maquina.preco = form.preco.data

        db.session.commit()
        flash('Máquina atualizada com sucesso!', 'success')
        return redirect(url_for('routes.listar_maquinas'))

    return render_template('editar_maquina.html', form=form, maquina=maquina)

@bp.route('/maquina/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_maquina(id):
    """ Exclui uma máquina do sistema """
    maquina = Maquina.query.get_or_404(id)

    db.session.delete(maquina)
    db.session.commit()

    flash('Máquina excluída com sucesso!', 'success')
    return redirect(url_for('routes.listar_maquinas'))


@bp.route('/trocas_matriz', methods=['GET'])
@login_required
def listar_trocas_matriz():
    trocas = TrocaMatriz.query.order_by(TrocaMatriz.id.desc()).all()
    return render_template('trocas_matriz.html', trocas=trocas)


from datetime import datetime, time  # 🔹 Importando time corretamente

def parse_time(value):
    """ Converte string para time ou retorna 00:00 se vazia. """
    if value:
        return datetime.strptime(value, "%H:%M").time()  # Converte string para TIME
    return time(0, 0)  # 🔹 Correção: agora retorna 00:00 corretamente


@bp.route('/troca_matriz/ver/<int:id>', methods=['GET'])
@login_required
def ver_troca_matriz(id):
    troca = TrocaMatriz.query.get_or_404(id)
    return render_template('ver_troca_matriz.html', troca=troca)

from datetime import datetime, time

def parse_time(value):
    """ Converte strings para objetos time ou retorna 00:00 se vazio. """
    return datetime.strptime(value, "%H:%M").time() if value else time(0, 0)


@bp.route('/troca_matriz/nova', methods=['GET', 'POST'])
@login_required
def nova_troca_matriz():
    form = TrocaMatrizForm()

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
            nova_troca = TrocaHorario(
                troca_matriz_id=troca_matriz.id,
                horario=horarios[i],  # 🔹 Usa os horários fixos
                pares=troca.form.pares.data or 0,  # 🔹 Se não for preenchido, fica 0

                # 🔹 Captura horários e converte corretamente
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
                fim_7=parse_time(troca.form.fim_7.data)
            )

            # 🔹 Calcula automaticamente o tempo total da troca
            nova_troca.atualizar_tempo_total()
            db.session.add(nova_troca)

        # 🔹 Atualiza os cálculos gerais da troca matriz
        troca_matriz.atualizar_tempo_total_geral()
        troca_matriz.calcular_total_pares()

        db.session.commit()
        flash('Troca de matriz registrada com sucesso!', 'success')
        return redirect(url_for('routes.listar_trocas_matriz'))

    return render_template('nova_troca_matriz.html', form=form)


@bp.route('/troca_matriz/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_troca_matriz(id):
    troca_matriz = TrocaMatriz.query.get_or_404(id)
    form = TrocaMatrizForm(obj=troca_matriz)
    
        # 🔹 Carregar os funcionários cadastrados por funções, só aparece na tela se for da função
    form.trocador_id.choices = [(f.id, f.nome) for f in Funcionario.query.
                                filter_by(funcao="Trocador").order_by(Funcionario.nome).all()]
    form.operador_id.choices = [(f.id, f.nome) for f in Funcionario.query.
                                filter_by(funcao="Operador").order_by(Funcionario.nome).all()]


    # 🔹 Carregar as máquinas cadastradas
    form.maquina_id.choices = [(m.id, f"{m.codigo} - {m.descricao}") for m in Maquina.query.order_by(Maquina.codigo).all()]

    
    # 🔹 Horários fixos
    horarios = ["7h às 8h", "8h às 9h", "9h às 10h", "10h às 11h", "11h às 12h",
                "12h às 13h", "13h às 14h", "14h às 15h", "15h às 16h", "16h às 17h"]

    # 🔹 Ordenar os horários para garantir a exibição correta
    troca_matriz.horarios.sort(key=lambda x: horarios.index(x.horario))

    if request.method == 'GET':
        for i, troca in enumerate(troca_matriz.horarios):
            if i < len(form.trocas.entries):  # Evita erro de índice
                form.trocas[i].horario.data = troca.horario
                form.trocas[i].pares.data = troca.pares
                form.trocas[i].inicio_1.data = troca.inicio_1.strftime("%H:%M") if troca.inicio_1 else ""
                form.trocas[i].fim_1.data = troca.fim_1.strftime("%H:%M") if troca.fim_1 else ""
                form.trocas[i].inicio_2.data = troca.inicio_2.strftime("%H:%M") if troca.inicio_2 else ""
                form.trocas[i].fim_2.data = troca.fim_2.strftime("%H:%M") if troca.fim_2 else ""
                form.trocas[i].inicio_3.data = troca.inicio_3.strftime("%H:%M") if troca.inicio_3 else ""
                form.trocas[i].fim_3.data = troca.fim_3.strftime("%H:%M") if troca.fim_3 else ""
                form.trocas[i].inicio_4.data = troca.inicio_4.strftime("%H:%M") if troca.inicio_4 else ""
                form.trocas[i].fim_4.data = troca.fim_4.strftime("%H:%M") if troca.fim_4 else ""
                form.trocas[i].inicio_5.data = troca.inicio_5.strftime("%H:%M") if troca.inicio_5 else ""
                form.trocas[i].fim_5.data = troca.fim_5.strftime("%H:%M") if troca.fim_5 else ""
                form.trocas[i].inicio_6.data = troca.inicio_6.strftime("%H:%M") if troca.inicio_6 else ""
                form.trocas[i].fim_6.data = troca.fim_6.strftime("%H:%M") if troca.fim_6 else ""
                form.trocas[i].inicio_7.data = troca.inicio_7.strftime("%H:%M") if troca.inicio_7 else ""
                form.trocas[i].fim_7.data = troca.fim_7.strftime("%H:%M") if troca.fim_7 else ""

    if form.validate_on_submit():
        troca_matriz.data = form.data.data
        troca_matriz.trocador_id = form.trocador_id.data
        troca_matriz.maquina_id = form.maquina_id.data
        troca_matriz.operador_id = form.operador_id.data
        


        for i, troca in enumerate(troca_matriz.horarios):
            if i < len(form.trocas.entries):  # Evita erro de índice
                troca.pares = form.trocas[i].pares.data or 0
                troca.inicio_1 = parse_time(form.trocas[i].inicio_1.data)
                troca.fim_1 = parse_time(form.trocas[i].fim_1.data)
                troca.inicio_2 = parse_time(form.trocas[i].inicio_2.data)
                troca.fim_2 = parse_time(form.trocas[i].fim_2.data)
                troca.inicio_3 = parse_time(form.trocas[i].inicio_3.data)
                troca.fim_3 = parse_time(form.trocas[i].fim_3.data)
                troca.inicio_4 = parse_time(form.trocas[i].inicio_4.data)
                troca.fim_4 = parse_time(form.trocas[i].fim_4.data)
                troca.inicio_5 = parse_time(form.trocas[i].inicio_5.data)
                troca.fim_5 = parse_time(form.trocas[i].fim_5.data)
                troca.inicio_6 = parse_time(form.trocas[i].inicio_6.data)
                troca.fim_6 = parse_time(form.trocas[i].fim_6.data)
                troca.inicio_7 = parse_time(form.trocas[i].inicio_7.data)
                troca.fim_7 = parse_time(form.trocas[i].fim_7.data)

                # 🔹 Recalcula o tempo total da troca
                troca.atualizar_tempo_total()

        # 🔹 Atualiza os cálculos gerais da troca matriz
        troca_matriz.atualizar_tempo_total_geral()
        troca_matriz.calcular_total_pares()

        db.session.commit()
        flash('Troca de matriz editada com sucesso!', 'success')
        return redirect(url_for('routes.listar_trocas_matriz'))

    return render_template('editar_troca_matriz.html', form=form, troca_matriz=troca_matriz)




@bp.route('/troca_matriz/excluir/<int:id>', methods=['POST'])
@login_required
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


@bp.route('/funcionarios', methods=['GET'])
@login_required
def listar_funcionarios():
    funcionarios = Funcionario.query.order_by(Funcionario.nome).all()
    return render_template('funcionarios.html', funcionarios=funcionarios)

@bp.route('/funcionario/novo', methods=['GET', 'POST'])
@login_required
def novo_funcionario():
    form = FuncionarioForm()
    if form.validate_on_submit():
        novo_funcionario = Funcionario(
            nome=form.nome.data,
            funcao=form.funcao.data
        )
        db.session.add(novo_funcionario)
        db.session.commit()
        flash("Funcionário cadastrado com sucesso!", "success")
        return redirect(url_for('routes.listar_funcionarios'))
    return render_template('novo_funcionario.html', form=form)

@bp.route('/funcionario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    form = FuncionarioForm(obj=funcionario)

    if form.validate_on_submit():
        funcionario.nome = form.nome.data
        funcionario.funcao = form.funcao.data
        db.session.commit()
        flash("Funcionário atualizado!", "success")
        return redirect(url_for('routes.listar_funcionarios'))
    
    return render_template('editar_funcionario.html', form=form, funcionario=funcionario)

@bp.route('/funcionario/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    db.session.delete(funcionario)
    db.session.commit()
    flash("Funcionário removido!", "success")
    return redirect(url_for('routes.listar_funcionarios'))



