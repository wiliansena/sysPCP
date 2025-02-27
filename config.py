from datetime import timedelta
import os

class Config:
    SECRET_KEY = '123'  # 🔹 Chave secreta fixa para segurança
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost/syspcp'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🔹 Tempo de expiração da sessão do usuário
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # 🔒 Usuários inativos por 30 min serão deslogados

    # 🔹 Configuração do diretório de upload de imagens
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')

    # 🔹 Configuração do CSRF (proteção contra ataques de formulários maliciosos)
    WTF_CSRF_ENABLED = False  # 🔒 Recomendo manter ativado
