from app import db
from app.models import LogAcao
from flask import current_app
from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user
from flask import request
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def formatar_moeda(valor):
    try:
        return locale.currency(valor, grouping=True, symbol=False)
    except Exception:
        return "0,00"

def formatar_numero(valor):
    try:
        numero = int(round(valor))
        return f"{numero:,}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0"


def registrar_filtros_jinja(app):
    app.jinja_env.filters['br_moeda'] = formatar_moeda
    app.jinja_env.filters['br_numero'] = formatar_numero


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


