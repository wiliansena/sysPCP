from app import db

class Referencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo_referencia = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(200))
    total_componentes = db.Column(db.Float, default=0)
    total_operacional = db.Column(db.Float, default=0)

class Componente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    unidade_medida = db.Column(db.String(10), nullable=False)
    consumo = db.Column(db.Float, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)

class CustoOperacional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    unidade_medida = db.Column(db.String(10), nullable=False)
    preco = db.Column(db.Float, nullable=False)

class Salario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    preco = db.Column(db.Float, nullable=False)
    encargos = db.Column(db.Float, nullable=False)

class MaoDeObra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    salario_id = db.Column(db.Integer, db.ForeignKey('salario.id', ondelete='RESTRICT'), nullable=False)
    multiplicador = db.Column(db.Float, nullable=False)
    preco_liquido = db.Column(db.Float, nullable=False)
    preco_bruto = db.Column(db.Float, nullable=False)

    # Relacionamento com Salario
    salario = db.relationship('Salario', backref=db.backref('mao_de_obra', lazy=True))
