from app import create_app, db
from app.models import Usuario, Permissao

app = create_app()

with app.app_context():
    db.create_all()

    # Verifica se o usuário admin já existe
    if not Usuario.query.filter_by(nome='admin').first():
        admin = Usuario(nome='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário admin criado: nome=admin / senha=admin123")

        permissoes = [
            ('usuarios', 'ver'), ('usuarios', 'editar'), ('usuarios', 'excluir'), ('usuarios', 'criar'),
            ('referencias', 'ver'), ('referencias', 'editar'), ('referencias', 'excluir'), ('referencias', 'criar'),
            ('controleproducao', 'ver'), ('controleproducao', 'editar'), ('controleproducao', 'excluir'), ('controleproducao', 'criar'),
            ('desenvolvimento', 'ver'), ('desenvolvimento', 'editar'), ('desenvolvimento', 'excluir'), ('desenvolvimento', 'criar'),
            ('margens', 'ver'), ('margens', 'editar'), ('margens', 'criar'), ('margens', 'excluir'),
            ('trocar_senha', 'editar'),
            ('administracao', 'ver'), ('administracao', 'editar')
        ]

        for categoria, acao in permissoes:
            p = Permissao(usuario_id=admin.id, categoria=categoria, acao=acao)
            db.session.add(p)

        db.session.commit()
        print("✅ Permissões atribuídas ao usuário admin.")
    else:
        print("ℹ️ Usuário admin já existe. Nenhuma ação foi tomada.")
