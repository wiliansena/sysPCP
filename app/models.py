from app import db

class Referencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo_referencia = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(200))
    total_componentes = db.Column(db.Float, default=0)
    total_operacional = db.Column(db.Float, default=0)

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


class Componente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    unidade_medida = db.Column(db.String(10), nullable=False)
    preco = db.Column(db.Float, nullable=False)


    #SOLADO
class Solado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.String(200), nullable=False)
    imagem = db.Column(db.String(200), nullable=True)
    
    tamanhos = db.relationship("Tamanho", backref="solado", lazy="joined", cascade="all, delete-orphan")
    formulacao = db.relationship("FormulacaoSolado", backref="solado", lazy="joined", cascade="all, delete-orphan")

    def calcular_totais(self):
        total_quantidade = sum(t.quantidade for t in self.tamanhos)
        peso_medio_total = sum(t.peso_medio for t in self.tamanhos)
        peso_friso_total = sum(t.peso_friso for t in self.tamanhos)
        peso_sem_friso_total = sum(t.peso_sem_friso for t in self.tamanhos)
        return total_quantidade, peso_medio_total, peso_friso_total, peso_sem_friso_total
    
    def calcular_total_formula(self):
        """
        Calcula o custo total da formulação do solado somando os preços unitários.
        """
        return sum(item.preco_unitario for item in self.formulacao if item.preco_unitario is not None)


class Tamanho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=False)  # Nome do tamanho
    quantidade = db.Column(db.Integer, nullable=False)  # Grade
    peso_medio = db.Column(db.Float, nullable=False)
    peso_friso = db.Column(db.Float, nullable=False)
    peso_sem_friso = db.Column(db.Float, nullable=False)

    solado_id = db.Column(db.Integer, db.ForeignKey("solado.id"), nullable=False)


class FormulacaoSolado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solado_id = db.Column(db.Integer, db.ForeignKey('solado.id'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id'), nullable=False)
    carga = db.Column(db.Float, nullable=False)
    
        # 🔹 RELACIONAMENTO CORRIGIDO:
    componente = db.relationship("Componente", backref="formulacoes", lazy="joined")

    # Cálculos automáticos
    @property
    def porcentagem(self):
        carga_total = sum(f.carga for f in self.solado.formulacao)
        return (self.carga / carga_total) * 100 if carga_total > 0 else 0

    @property
    def pares_por_carga(self):
        peso_medio_total = sum(t.peso_sem_friso for t in self.solado.tamanhos)
        return self.carga / peso_medio_total if peso_medio_total > 0 else 0

    @property
    def consumo(self):
        return self.carga / self.pares_por_carga if self.pares_por_carga > 0 else 0

    @property
    def preco_unitario(self):
        componente = Componente.query.get(self.componente_id)
        return self.consumo * componente.preco if componente else 0



