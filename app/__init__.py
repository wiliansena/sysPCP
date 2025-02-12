import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

# 🔹 Inicializa a aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)  # Carrega as configurações do config.py

# 🔹 Configuração do banco de dados
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 🔹 Proteção CSRF
csrf = CSRFProtect(app)

# 🔹 Configuração do diretório de upload
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

# 🔹 Importação de Blueprints (rotas)
from app.routes import bp as routes_bp
app.register_blueprint(routes_bp)

# 🔹 Criação do diretório de uploads, se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
