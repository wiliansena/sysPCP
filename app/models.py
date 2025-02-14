from decimal import Decimal
from sqlalchemy.orm import relationship
from app import db
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING

class Referencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo_referencia = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(200))
    total_componentes = db.Column(db.Numeric(10,4), default=Decimal(0))
    total_operacional = db.Column(db.Numeric(10,4), default=Decimal(0))

class CustoOperacional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    unidade_medida = db.Column(db.String(10), nullable=False)
    preco = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))

class Salario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    preco = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))
    encargos = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))

class MaoDeObra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    salario_id = db.Column(db.Integer, db.ForeignKey('salario.id', ondelete='RESTRICT'), nullable=False)
    multiplicador = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))
    preco_liquido = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))
    preco_bruto = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))

    # Relacionamento com Salario
    salario = db.relationship('Salario', backref=db.backref('mao_de_obra', lazy=True))


class Componente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    unidade_medida = db.Column(db.String(10), nullable=False)
    preco = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))


#SOLADO
class Solado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.String(200), nullable=False)
    imagem = db.Column(db.String(200), nullable=True)

    tamanhos = db.relationship("Tamanho", backref="solado", lazy="joined", cascade="all, delete-orphan")
    formulacao = db.relationship("FormulacaoSolado", backref="solado", lazy="joined", cascade="all, delete-orphan")

    def calcular_totais(self):
        """ Calcula os valores totais de grade e pesos médios ponderados. """
        total_grade = sum(t.quantidade for t in self.tamanhos)

        peso_medio_total = sum(Decimal(str(t.peso_medio)) * Decimal(str(t.quantidade)) for t in self.tamanhos) / total_grade if total_grade else Decimal(0)
        peso_friso_total = sum(Decimal(str(t.peso_friso)) * Decimal(str(t.quantidade)) for t in self.tamanhos) / total_grade if total_grade else Decimal(0)
        peso_sem_friso_total = sum(Decimal(str(t.peso_sem_friso)) * Decimal(str(t.quantidade)) for t in self.tamanhos) / total_grade if total_grade else Decimal(0)
        
            # 🔹 Arredonda peso_sem_friso_total para **três casas decimais**
        peso_sem_friso_total = peso_sem_friso_total.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

        return total_grade, round(peso_medio_total, 6), round(peso_friso_total, 6), round(peso_sem_friso_total, 6)

    def calcular_peso_sem_friso_total(self):
        """ Apenas retorna o peso médio sem friso total já calculado. """
        return self.calcular_totais()[3]  # O índice 3 corresponde ao peso_sem_friso_total


class Tamanho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=True)  # Nome do tamanho
    quantidade = db.Column(db.Integer, nullable=True)  # GRADE
    peso_medio = db.Column(db.Numeric(10,4), nullable=True, default=Decimal(0))
    peso_friso = db.Column(db.Numeric(10,4), nullable=True, default=Decimal(0))
    peso_sem_friso = db.Column(db.Numeric(10,4), nullable=True, default=Decimal(0))

    solado_id = db.Column(db.Integer, db.ForeignKey("solado.id"), nullable=False)


class FormulacaoSolado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solado_id = db.Column(db.Integer, db.ForeignKey('solado.id'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id'), nullable=False)
    carga = db.Column(db.Numeric(10, 4), nullable=False)  # 🔹 Numeric com 4 casas decimais

    componente = db.relationship("Componente")

    @property
    def carga_total(self):
        """Soma de todas as cargas dos componentes do solado."""
        return sum(Decimal(f.carga) for f in self.solado.formulacao) if self.solado.formulacao else Decimal(0)

    @property
    def porcentagem(self):
        carga_total = self.carga_total
        return (Decimal(str(self.carga)) / carga_total) * 100 if carga_total > 0 else Decimal(0)

    @property
    def pares_por_carga(self):
        """ Calcula a quantidade de pares por carga usando peso_sem_friso_total arredondado. """
        peso_sem_friso_total = Decimal(str(self.solado.calcular_peso_sem_friso_total()))  # ✅ Pegamos já arredondado
        carga_total = self.carga_total  # ✅ Já em Decimal

        if peso_sem_friso_total > 0:
            pares_por_carga = carga_total / peso_sem_friso_total
            return pares_por_carga.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # 🔹 Arredondamos o resultado

        return Decimal(0)

    @property
    def consumo(self):
        return Decimal(str(self.carga)) / self.pares_por_carga if self.pares_por_carga > 0 else Decimal(0)

    @property
    def preco_unitario(self):
        """Calcula o preço unitário e garante que valores muito pequenos sejam pelo menos 0.01."""
        preco = self.consumo * Decimal(str(self.componente.preco))

        # 🔹 Se o valor for menor que 0.01, ajustado para 0.01
        return max(preco.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), Decimal('0.01'))

    @property
    def preco_total(self):
        """Calcula o preço total arredondando para cima."""
        if not self.solado.formulacao:
            return Decimal(0)

        preco_total = sum(f.preco_unitario for f in self.solado.formulacao)

        # 🔹 Arredondamento para cima
        return preco_total.quantize(Decimal('0.01'), rounding=ROUND_CEILING)
