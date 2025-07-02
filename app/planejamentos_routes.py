from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required

from app import db
from app.models import Cep, Estado, Municipio
from app.forms import CepForm, EstadoForm, MunicipioForm
from app.utils import requer_permissao

from app.routes import bp  # ← IMPORTA O MESMO BLUEPRINT DO routes.py

@bp.route('/teste')
@login_required
def teste():
    print('chegou na rota')
    return render_template('planejamento/teste.html')