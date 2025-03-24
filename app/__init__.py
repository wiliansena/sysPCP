from datetime import timedelta
import os
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, logout_user, current_user
from config import Config

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Carrega as configurações do config.py

    # 🔹 Configuração do tempo de sessão
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    # 🔹 Inicialização do banco de dados
    db.init_app(app)
    migrate.init_app(app, db)

    # 🔹 Proteção CSRF
    csrf.init_app(app)

    # 🔹 Configuração do diretório de upload
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

    # 🔹 Configuração do Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Você precisa estar logado para acessar esta página."

    @login_manager.user_loader
    def load_user(user_id):
        """Carrega o usuário ao fazer login e garante que as permissões são carregadas corretamente."""
        from app.models import Usuario  # Importação dentro da função para evitar problemas de importação circular
        usuario = Usuario.query.get(int(user_id))
        
        if usuario:
            _ = usuario.todas_permissoes  # 🔹 Garante que as permissões são carregadas corretamente
        
        return usuario

    # 🔹 Antes de cada requisição, manter a sessão ativa e garantir permissões
    @app.before_request
    def verificar_sessao():
        if current_user.is_authenticated:
            session.permanent = True
            session.modified = True
            
            # 🔹 Garante que as permissões estão carregadas corretamente no usuário
            _ = current_user.todas_permissoes
        else:
            logout_user()

    # 🔹 Importação de Blueprints (módulos de rotas)
    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    from app.auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # 🔹 Criação do diretório de uploads, se não existir
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    return app
