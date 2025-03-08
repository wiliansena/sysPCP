from flask import render_template, redirect, session, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario
from app.auth.forms import LoginForm  # Importa o formulário
from app.auth import bp  # Importa o Blueprint

from flask import request

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))  # 🔹 Se já estiver logado, redireciona

    form = LoginForm()

    if form.validate_on_submit():  # 🔹 Verifica se o formulário foi enviado
        user = Usuario.query.filter_by(nome=form.nome.data).first()

        if user and user.check_password(form.senha.data):
            login_user(user)

            # 🔹 Configura a expiração da sessão após login
            session.permanent = True
            session.modified = True  # 🔹 Atualiza a sessão ao fazer login
            
            flash('Login realizado com sucesso!', 'success')

            # 🔹 Detecta se o usuário está em um dispositivo móvel
            user_agent = request.user_agent.string.lower()
            is_mobile = "mobile" in user_agent

            # 🔹 Decide para onde redirecionar com base no dispositivo
            return redirect(url_for('routes.home_mobile' if is_mobile else 'routes.home'))
        
        else:
            flash('Nome ou senha incorretos.', 'danger')  # 🔥 Só mostra o erro se houve tentativa de login

    return render_template('auth/login.html', form=form)  # 🔹 Não adiciona flash se não houve submissão


@bp.route('/logout')
@login_required
def logout():
    logout_user()  # 🔹 Remove a sessão do usuário
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('auth.login'))  # 🔹 Redireciona para a tela de login
