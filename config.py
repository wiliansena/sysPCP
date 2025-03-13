from datetime import timedelta
import os
from dotenv import load_dotenv

# 🔹 Obter caminho absoluto do arquivo .env
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

# 🔹 Carregar o .env explicitamente
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"⚠️ Arquivo .env não encontrado no caminho: {dotenv_path}")

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-secreta-padrao')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 'postgresql://postgres:postgres@localhost/syspcp'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

    WTF_CSRF_ENABLED = False

