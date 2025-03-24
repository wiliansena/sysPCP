from flask import render_template, redirect, session, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Permissao, Usuario
from app.auth.forms import LoginForm  # Importa o formulário
from app.auth import bp  # Importa o Blueprint

from flask import request

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))

    form = LoginForm()

    if form.validate_on_submit():
        user = Usuario.query.filter_by(nome=form.nome.data).first()

        if user and user.check_password(form.senha.data):
            login_user(user)
            
            # FORÇAR O CARREGAMENTO DAS PERMISSÕES CORRETAMENTE NA SESSÃO
            session["permissoes"] = list(user.todas_permissoes)  # 🔹 Salvar permissões na sessão
            
            session.permanent = True
            session.modified = True  

            
            flash('Login realizado com sucesso!', 'success')
            print("Permissões do usuário:", user.todas_permissoes)
            return redirect(url_for('routes.home'))

        else:
            flash('Nome ou senha incorretos.', 'danger')

    return render_template('auth/login.html', form=form)



@bp.route('/logout')
@login_required
def logout():
    logout_user()  # 🔹 Remove a sessão do usuário
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('auth.login'))  # 🔹 Redireciona para a tela de login


from app.auth.forms import TrocarSenhaForm  # Precisamos criar esse formulário
@bp.route('/trocar_senha', methods=['GET', 'POST'])
@login_required
def trocar_senha():
    """Permite que o usuário troque a senha, se tiver permissão."""
    if not current_user.pode_trocar_senha():
        flash("Você não tem permissão para alterar sua senha.", "danger")
        return redirect(url_for('routes.home'))  # Redireciona para a home

    form = TrocarSenhaForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.senha_atual.data):
            flash("Senha atual incorreta.", "danger")
        elif form.nova_senha.data != form.confirmar_senha.data:
            flash("As senhas não coincidem.", "danger")
        else:
            try:
                current_user.set_password(form.nova_senha.data)
                db.session.commit()
                flash("Senha alterada com sucesso!", "success")
                return redirect(url_for('routes.home'))
            except Exception as e:
                flash(f"Ocorreu um erro ao salvar a senha: {str(e)}", "danger")

    # 🔹 Exibe os erros do formulário caso existam
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Erro no campo {getattr(form, field).label.text}: {error}", "danger")

    return render_template('auth/trocar_senha.html', form=form)
