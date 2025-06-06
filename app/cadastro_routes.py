# app/cadastro_routes.py

from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required

from app import db
from app.models import Cep, Estado, Municipio
from app.forms import CepForm, EstadoForm, MunicipioForm
from app.utils import requer_permissao

from app.routes import bp  # ← IMPORTA O MESMO BLUEPRINT DO routes.py

@bp.route('/estados', methods=['GET'])
@login_required
@requer_permissao('cadastro', 'ver')
def listar_estados():
    estados = Estado.query.order_by(Estado.id).all()
    return render_template('cadastro/listar_estados.html', estados=estados)


@bp.route('/estado/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('cadastro', 'criar')
def novo_estado():
    form = EstadoForm()
    if form.validate_on_submit():
        novo_estado = Estado(
            nome=form.nome.data,
            sigla=form.sigla.data
        )
        db.session.add(novo_estado)
        db.session.commit()
        flash("Estado cadastrado com sucesso!", "success")
        return redirect(url_for('routes.listar_estados'))
    return render_template('cadastro/novo_estado.html', form=form)



@bp.route('/estado/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('cadastro', 'editar')
def editar_estado(id):
    estado = Estado.query.get_or_404(id)
    form = EstadoForm(obj=estado)

    if form.validate_on_submit():
        estado.nome = form.nome.data
        estado.sigla = form.sigla.data

        db.session.commit()
        flash("Estado atualizado!", "success")
        return redirect(url_for('routes.listar_estados'))
    
    return render_template('cadastro/editar_estado.html', form=form, estado=estado)

@bp.route('/estado/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('cadastro', 'excluir')
def excluir_estado(id):
    estado = Estado.query.get_or_404(id)

    db.session.delete(estado)
    db.session.commit()

    flash("Estado removido!", "success")
    return redirect(url_for('routes.listar_estados'))


### MUNICIPIO #####

@bp.route('/municipios', methods=['GET'])
@login_required
@requer_permissao('cadastro', 'ver')
def listar_municipios():
    municipios = Municipio.query.order_by(Municipio.id).all()
    return render_template('cadastro/listar_municipios.html', municipios=municipios)

@bp.route('/municipio/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('cadastro', 'criar')
def novo_municipio():
    form = MunicipioForm()

    form.estado_id.choices = [(e.id, e.nome) for e in Estado.query.order_by(Estado.nome).all()]

    if form.validate_on_submit():
        novo_municipio = Municipio(
            nome=form.nome.data,
            estado_id = form.estado_id.data
        )
        db.session.add(novo_municipio)
        db.session.commit()
        flash("Município cadastrado com sucesso!", "success")
        return redirect(url_for('routes.listar_municipios'))
    return render_template('cadastro/novo_municipio.html', form=form)



@bp.route('/municipio/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('cadastro', 'editar')
def editar_municipio(id):
    municipio = Municipio.query.get_or_404(id)
    form = MunicipioForm(obj=municipio)

    form.estado_id.choices = [(e.id, e.nome) for e in Estado.query.order_by(Estado.nome).all()]

    if form.validate_on_submit():
        municipio.nome = form.nome.data
        municipio.estado_id = form.estado_id.data

        db.session.commit()
        flash("Municipio atualizado!", "success")
        return redirect(url_for('routes.listar_municipios'))
    
    return render_template('cadastro/editar_municipio.html', form=form, municipio=municipio)

@bp.route('/municipio/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('cadastro', 'excluir')
def excluir_municipio(id):
    municipio = Municipio.query.get_or_404(id)

    db.session.delete(municipio)
    db.session.commit()

    flash("Município removido!", "success")
    return redirect(url_for('routes.listar_municipios'))


### CEP #####

@bp.route('/ceps', methods=['GET'])
@login_required
@requer_permissao('cadastro', 'ver')
def listar_ceps():
    ceps = Cep.query.order_by(Cep.id).all()
    return render_template('cadastro/listar_ceps.html', ceps=ceps)

@bp.route('/cep/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('cadastro', 'criar')
def novo_cep():
    form = CepForm()

    form.municipio_id.choices = [(m.id, m.nome) for m in Municipio.query.order_by(Municipio.nome).all()]
    form.estado_id.choices = [(e.id, e.nome) for e in Estado.query.order_by(Estado.nome).all()]

    if form.validate_on_submit():
        novo_cep = Cep(
            cep=form.cep.data,
            logradouro=form.logradouro.data,
            numero=form.numero.data,
            bairro=form.bairro.data,
            municipio_id=form.municipio_id.data,
            estado_id = form.estado_id.data
        )
        db.session.add(novo_cep)
        db.session.commit()
        flash("Cep cadastrado com sucesso!", "success")
        return redirect(url_for('routes.listar_ceps'))
    return render_template('cadastro/novo_cep.html', form=form)



@bp.route('/cep/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requer_permissao('cadastro', 'editar')
def editar_cep(id):
    cep = Cep.query.get_or_404(id)
    form = CepForm(obj=cep)
   
    form.municipio_id.choices = [(m.id, m.nome) for m in Municipio.query.order_by(Municipio.nome).all()]
    form.estado_id.choices = [(e.id, e.nome) for e in Estado.query.order_by(Estado.nome).all()]

    if form.validate_on_submit():
        cep.cep = form.cep.data
        cep.logradouro = form.logradouro.data
        cep.numero = form.numero.data
        cep.bairro = form.bairro.data
        cep.municipio_id = form.municipio_id.data
        cep.estado_id = form.estado_id.data

        db.session.commit()
        flash("Cep atualizado!", "success")
        return redirect(url_for('routes.listar_ceps'))
    
    return render_template('cadastro/editar_cep.html', form=form, cep=cep)

@bp.route('/cep/excluir/<int:id>', methods=['POST'])
@login_required
@requer_permissao('cadastro', 'excluir')
def excluir_cep(id):
    cep = Cep.query.get_or_404(id)

    db.session.delete(cep)
    db.session.commit()

    flash("Cep removido!", "success")
    return redirect(url_for('routes.listar_ceps'))