from datetime import timedelta
import os 
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, logout_user, current_user
from config import Config

# 🔹 Inicializa a aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)  # Carrega as configurações do config.py

# 🔹 Configuração do tempo de sessão
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # 🔹 Define o tempo de expiração da sessão

# 🔹 Configuração do banco de dados
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 🔹 Proteção CSRF
csrf = CSRFProtect(app)

# 🔹 Configuração do diretório de upload
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

# 🔹 Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"  # Define a tela de login padrão
login_manager.login_message = "Você precisa estar logado para acessar esta página."

@login_manager.user_loader
def load_user(user_id):
    from app.models import Usuario  # 🔹 Importação dentro da função para evitar erro de importação circular
    return Usuario.query.get(int(user_id))

# 🔹 Antes de cada requisição, tornar a sessão permanente e resetar o tempo
@app.before_request
def verificar_sessao():
    if current_user.is_authenticated:
        session.permanent = True  # 🔹 Garante que a sessão seja permanente
        session.modified = True   # 🔹 Reseta o tempo de expiração com cada requisição
    else:
        logout_user()  # 🔹 Faz logout se a sessão expirou

# 🔹 Importação de Blueprints (rotas)
from app.routes import bp as routes_bp
app.register_blueprint(routes_bp)

from app.auth.routes import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

# 🔹 Criação do diretório de uploads, se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
