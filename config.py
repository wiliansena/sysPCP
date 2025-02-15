import os

class Config:
    SECRET_KEY = '123'  # 🔹 Defina uma chave segura aqui
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost/syspcp'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🔹 Configuração do diretório de upload de imagens
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')

    # 🔹 Configurações para CSRF
    WTF_CSRF_ENABLED = False
