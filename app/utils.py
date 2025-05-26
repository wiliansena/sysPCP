from app import db
from app.models import LogAcao
from flask import current_app
from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user
from flask import request


def requer_permissao(categoria, acao):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Faça login para acessar esta página.", "warning")
                return redirect(url_for('auth.login', next=request.url))  # use request.url

            if not current_user.tem_permissao(categoria, acao):
                flash("Você não tem permissão!.", "danger")
                return redirect(request.referrer or url_for('routes.home'))

            return f(*args, **kwargs)
        return wrapped
    return decorator



def registrar_log(acao):
    """
    Registra uma ação no log com o usuário autenticado.
    """
    if current_user.is_authenticated:
        novo_log = LogAcao(
            usuario_id=current_user.id,
            usuario_nome=current_user.username,
            acao=acao
        )
        db.session.add(novo_log)
        db.session.commit()

def allowed_file(filename):
    """ Verifica se o arquivo possui uma extensão permitida. """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


