import os

class Config:
    SECRET_KEY = '123'  # Troque por uma chave segura
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost/syspcp'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
