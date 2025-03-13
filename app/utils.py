from app import db
from app.models import LogAcao
from flask_login import current_user
from flask import current_app

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
