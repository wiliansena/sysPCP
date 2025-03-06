from decimal import Decimal
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from app import db
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from datetime import date, datetime



class Referencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo_referencia = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(200))
    linha = db.Column(db.String(50), nullable=True)

    # Totais calculados individuais
    total_solado = db.Column(db.Numeric(10,4), default=Decimal(0))
    total_alcas = db.Column(db.Numeric(10,4), default=Decimal(0))
    total_componentes = db.Column(db.Numeric(10,4), default=Decimal(0))
    total_embalagem1 = db.Column(db.Numeric(10,4), default=Decimal(0))
    total_embalagem2 = db.Column(db.Numeric(10,4), default=Decimal(0))
    total_embalagem3 = db.Column(db.Numeric(10,4), default=Decimal(0))
    total_operacional = db.Column(db.Numeric(10,4), default=Decimal(0))
    total_mao_de_obra = db.Column(db.Numeric(10,4), default=Decimal(0))
    
    # 🔹 Custo total separado por embalagem
    custo_total_embalagem1 = db.Column(db.Numeric(10,4), default=Decimal(0))
    custo_total_embalagem2 = db.Column(db.Numeric(10,4), default=Decimal(0))
    custo_total_embalagem3 = db.Column(db.Numeric(10,4), default=Decimal(0))

    # Relacionamentos com os itens da referência
    solados = db.relationship("ReferenciaSolado", backref="referencia", lazy=True, cascade="all, delete-orphan")
    alcas = db.relationship("ReferenciaAlca", backref="referencia", lazy=True, cascade="all, delete-orphan")
    componentes = db.relationship("ReferenciaComponentes", backref="referencia", lazy=True, cascade="all, delete-orphan")
    embalagem1 = db.relationship("ReferenciaEmbalagem1", backref="referencia", lazy=True, cascade="all, delete-orphan")
    embalagem2 = db.relationship("ReferenciaEmbalagem2", backref="referencia", lazy=True, cascade="all, delete-orphan")
    embalagem3 = db.relationship("ReferenciaEmbalagem3", backref="referencia", lazy=True, cascade="all, delete-orphan")
    custos_operacionais = db.relationship("ReferenciaCustoOperacional", backref="referencia", lazy=True, cascade="all, delete-orphan")
    mao_de_obra = db.relationship("ReferenciaMaoDeObra", backref="referencia", lazy=True, cascade="all, delete-orphan")

    def calcular_totais(self):
        """Calcula os totais individuais e os custos totais por embalagem."""
        self.total_solado = sum(solado.custo_total for solado in self.solados)
        self.total_alcas = sum(alca.custo_total for alca in self.alcas)
        self.total_componentes = sum(componente.custo_total for componente in self.componentes)
        self.total_embalagem1 = sum(embalagem.custo_total for embalagem in self.embalagem1)
        self.total_embalagem2 = sum(embalagem.custo_total for embalagem in self.embalagem2)
        self.total_embalagem3 = sum(embalagem.custo_total for embalagem in self.embalagem3)

        # 🔹 Ajuste no cálculo dos custos operacionais
        self.total_operacional = sum(custo.consumo * custo.preco_unitario for custo in self.custos_operacionais)
        
        self.total_mao_de_obra = sum(mao.custo_total for mao in self.mao_de_obra)

        # 🔹 Cálculo do custo total para cada embalagem
        self.custo_total_embalagem1 = (self.total_solado + self.total_alcas + self.total_componentes +
                                    self.total_embalagem1 + self.total_operacional + self.total_mao_de_obra)

        self.custo_total_embalagem2 = (self.total_solado + self.total_alcas + self.total_componentes +
                                    self.total_embalagem2 + self.total_operacional + self.total_mao_de_obra)

        self.custo_total_embalagem3 = (self.total_solado + self.total_alcas + self.total_componentes +
                                    self.total_embalagem3 + self.total_operacional + self.total_mao_de_obra)






class ReferenciaSolado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id'), nullable=False)
    solado_id = db.Column(db.Integer, db.ForeignKey('solado.id'), nullable=False)
    consumo = db.Column(db.Numeric(10,4), nullable=False)
    preco_unitario = db.Column(db.Numeric(10,4), nullable=False)

    solado = db.relationship("Solado")

    @property
    def custo_total(self):
        """Calcula o custo total do solado baseado no consumo, convertendo os valores para Decimal."""
        consumo_decimal = Decimal(self.consumo)
        # Se self.solado.custo_total já for Decimal, esta conversão é redundante; caso contrário, garante a consistência.
        custo_solado = Decimal(self.solado.custo_total)
        return consumo_decimal * custo_solado

class ReferenciaAlca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id'), nullable=False)
    alca_id = db.Column(db.Integer, db.ForeignKey('alca.id'), nullable=False)
    consumo = db.Column(db.Numeric(10,4), nullable=False)
    preco_unitario = db.Column(db.Numeric(10,4), nullable=False)

    alca = db.relationship("Alca")

    @property
    def custo_total(self):
        """Calcula o custo total da alça baseado no consumo"""
        consumo_decimal = Decimal(self.consumo)
        custo_alca = Decimal(self.alca.preco_total)
        return consumo_decimal * custo_alca

class ReferenciaComponentes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id'), nullable=False)
    consumo = db.Column(db.Numeric(10,4), nullable=False)
    preco_unitario = db.Column(db.Numeric(10,4), nullable=False)

    componente = db.relationship("Componente")

    @property
    def custo_total(self):
        """Calcula o custo total dos componentes baseado no consumo"""
        consumo_decimal = Decimal(self.consumo)
        custo_componente = Decimal(self.componente.preco)
        return consumo_decimal * custo_componente


class ReferenciaEmbalagem1(db.Model):
    __tablename__ = 'referencia_embalagem1'
    id = db.Column(db.Integer, primary_key=True)
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id'), nullable=False)
    consumo = db.Column(db.Numeric(10,4), nullable=False)
    preco_unitario = db.Column(db.Numeric(10,4), nullable=False)

    componente = db.relationship("Componente")

    @property
    def custo_total(self):
        """Calcula o custo total baseado no consumo e preço unitário"""
        consumo_decimal = Decimal(self.consumo)  # 🔹 Converte para Decimal
        custo_componente = Decimal(self.componente.preco)  # 🔹 Pega o preço do componente
        return consumo_decimal * custo_componente

class ReferenciaEmbalagem2(db.Model):
    __tablename__ = 'referencia_embalagem2'
    id = db.Column(db.Integer, primary_key=True)
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id'), nullable=False)
    consumo = db.Column(db.Numeric(10,4), nullable=False)
    preco_unitario = db.Column(db.Numeric(10,4), nullable=False)

    componente = db.relationship("Componente")

    @property
    def custo_total(self):
        consumo_decimal = Decimal(self.consumo)
        custo_componente = Decimal(self.componente.preco)
        return consumo_decimal * custo_componente

class ReferenciaEmbalagem3(db.Model):
    __tablename__ = 'referencia_embalagem3'
    id = db.Column(db.Integer, primary_key=True)
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id'), nullable=False)
    consumo = db.Column(db.Numeric(10,4), nullable=False)
    preco_unitario = db.Column(db.Numeric(10,4), nullable=False)

    componente = db.relationship("Componente")

    @property
    def custo_total(self):
        consumo_decimal = Decimal(self.consumo)
        custo_componente = Decimal(self.componente.preco)
        return consumo_decimal * custo_componente



class ReferenciaCustoOperacional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id'), nullable=False)
    custo_id = db.Column(db.Integer, db.ForeignKey('custo_operacional.id'), nullable=False)
    consumo = db.Column(db.Numeric(10,4), nullable=False)
    preco_unitario = db.Column(db.Numeric(10,4), nullable=False)

    custo = db.relationship("CustoOperacional")

    @property
    def custo_total(self):
        """Calcula o custo total dos custos operacionais baseado no consumo"""
        consumo_decimal = Decimal(self.consumo)
        custo = Decimal(self.custo.preco)
        return consumo_decimal * custo

class ReferenciaMaoDeObra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id'), nullable=False)
    mao_de_obra_id = db.Column(db.Integer, db.ForeignKey('mao_de_obra.id'), nullable=False)
    consumo = db.Column(db.Numeric(10,4), nullable=False)
    producao = db.Column(db.Numeric(10,4), nullable=False)
    preco_unitario = db.Column(db.Numeric(10,4), nullable=False)

    mao_de_obra = db.relationship("MaoDeObra")

    @property
    def custo_total(self):
        """Calcula o custo total da mão de obra baseado no consumo e produção, utilizando Decimal."""
        consumo_decimal = Decimal(self.consumo)
        producao_decimal = Decimal(self.producao)
        diaria = Decimal(self.mao_de_obra.diaria)
        divisor = producao_decimal if producao_decimal > Decimal(0) else Decimal(1)
        return (consumo_decimal * diaria) / divisor




class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Numeric(10,1), unique=True, nullable=False)
    

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
    
    @property
    def diaria(self):
        """ Calcula a diária como preco_bruto / 21, garantindo que não ocorra divisão por zero. """
        return (self.preco_bruto / Decimal(21)).quantize(Decimal('0.0001'),
                                                         rounding=ROUND_HALF_UP) if self.preco_bruto > 0 else Decimal(0)

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
    formulacao_friso = db.relationship("FormulacaoSoladoFriso", backref="solado", lazy="joined", cascade="all, delete-orphan")  # 🔹 Adicionada aqui!

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
    
    def calcular_peso_friso_total(self):
        """ Apenas retorna o peso médio sem friso total já calculado. """
        return self.calcular_totais()[2]  # O índice 2 corresponde ao peso_friso_total
    
    @property
    def preco_total(self):
        """ Calcula o custo total da formulação sem friso. """
        return sum(f.preco_unitario for f in self.formulacao) if self.formulacao else Decimal(0)

    @property
    def preco_total_friso(self):
        """ Calcula o custo total da formulação com friso. """
        return sum(f.preco_unitario for f in self.formulacao_friso) if self.formulacao_friso else Decimal(0)

    @property
    def custo_total(self):
        """ Calcula o custo total da sola (com friso + sem friso). """
        return self.preco_total + self.preco_total_friso


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
    
    
    #SOLADO FRISO
    
class FormulacaoSoladoFriso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solado_id = db.Column(db.Integer, db.ForeignKey('solado.id'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id'), nullable=False)
    carga = db.Column(db.Numeric(10, 4), nullable=False)  # 🔹 Numeric com 4 casas decimais

    componente = db.relationship("Componente")

    @property
    def carga_total(self):
        """Soma de todas as cargas dos componentes do solado."""
        return sum(Decimal(f.carga) for f in self.solado.formulacao_friso) if self.solado.formulacao_friso else Decimal(0)

    @property
    def porcentagem(self):
        carga_total = self.carga_total
        return (Decimal(str(self.carga)) / carga_total) * 100 if carga_total > 0 else Decimal(0)
    
    @property
    def pares_por_carga(self):
        """ Calcula a quantidade de pares por carga usando peso_friso_total arredondado. """
        peso_friso_total = Decimal(str(self.solado.calcular_peso_friso_total()))  # ✅ Pegamos já arredondado
        carga_total = self.carga_total  # ✅ Já em Decimal

        if peso_friso_total > 0:
            pares_por_carga = carga_total / peso_friso_total
            return pares_por_carga.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # 🔹 Arredondamos o resultado

        return Decimal(0)

    @property
    def consumo(self):
        """ Calcula o consumo baseado na carga e pares por carga. """
        return Decimal(str(self.carga)) / self.pares_por_carga if self.pares_por_carga > 0 else Decimal(0)

    @property
    def preco_unitario(self):
        """ Calcula o preço unitário do componente. """
        return self.consumo * Decimal(str(self.componente.preco))  # ✅ Convertemos para Decimal

    
    @property
    def preco_total(self):
        """Calcula o preço total arredondando para cima."""
        if not self.solado.formulacao_friso:
            return Decimal(0)

        preco_total = sum(f.preco_unitario for f in self.solado.formulacao_friso)

        # 🔹 Arredondamento para cima
        return preco_total.quantize(Decimal('0.01'), rounding=ROUND_CEILING)

 #ALCAS

class Alca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    imagem = db.Column(db.String(200), nullable=True)

    tamanhos = db.relationship('TamanhoAlca', backref='alca', cascade="all, delete-orphan")
    formulacao = db.relationship('FormulacaoAlca', backref='alca', cascade="all, delete-orphan")

    def calcular_totais(self):
        """ Calcula os valores totais de grade e pesos médios ponderados. """
        total_grade = sum(t.quantidade for t in self.tamanhos)

        peso_medio_total = sum(Decimal(str(t.peso_medio)) * Decimal(str(t.quantidade)) for t in self.tamanhos) / total_grade if total_grade else Decimal(0)
        
        return total_grade, round(peso_medio_total, 6)
    
    def calcular_peso_medio_total(self):
        """ Apenas retorna o peso médio total já calculado. """
        return self.calcular_totais()[1]  # O índice 1 corresponde ao peso_medio
        
    @property
    def preco_total(self):
        """ Calcula o custo total da formulação. """
        return sum(f.preco_unitario for f in self.formulacao) if self.formulacao else Decimal(0)

class TamanhoAlca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alca_id = db.Column(db.Integer, db.ForeignKey('alca.id', ondelete='CASCADE'), nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    peso_medio = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))

class FormulacaoAlca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alca_id = db.Column(db.Integer, db.ForeignKey('alca.id', ondelete='CASCADE'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id', ondelete='CASCADE'), nullable=False)
    carga = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))

    componente = db.relationship('Componente')

    @property
    def carga_total(self):
        """Soma de todas as cargas dos componentes da alca."""
        return sum(Decimal(f.carga) for f in self.alca.formulacao) if self.alca.formulacao else Decimal(0)

    @property
    def porcentagem(self):
        carga_total = self.carga_total
        return (Decimal(str(self.carga)) / carga_total) * 100 if carga_total > 0 else Decimal(0)

    @property
    def pares_por_carga(self):
        """ Calcula a quantidade de pares por carga usando peso medio arredondado. """
        peso_medio_total = Decimal(str(self.alca.calcular_peso_medio_total()))  # ✅ Pegamos já arredondado
        carga_total = self.carga_total  # ✅ Já em Decimal

        if peso_medio_total > 0:
            pares_por_carga = carga_total / peso_medio_total
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
        if not self.alca.formulacao:
            return Decimal(0)

        preco_total = sum(f.preco_unitario for f in self.alca.formulacao)

        # 🔹 Arredondamento para cima
        return preco_total.quantize(Decimal('0.01'), rounding=ROUND_CEILING)


from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model, UserMixin):
    __tablename__ = "usuario"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    permissao = db.Column(db.String(50), nullable=False, default='usuario')

    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)  # 🔹 Gera o hash corretamente

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)  # 🔹 Verifica a senha


class LogAcao(db.Model):
    __tablename__ = "log_acao"  # 🔹 Nome da tabela no banco

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)  # 🔹 Corrigido para "usuario.id"
    usuario_nome = db.Column(db.String(100), nullable=False)  # 🔹 Tamanho ajustado para compatibilidade
    acao = db.Column(db.String(255), nullable=False)
    data_hora = db.Column(db.DateTime, default=lambda: datetime.now().replace(microsecond=0))  # 🔹 Adicionando data e hora exata

    usuario = db.relationship('Usuario', backref=db.backref('logs', lazy=True))  # 🔹 Relacionamento com a tabela Usuario


class Margem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    preco_venda = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    cliente = db.Column(db.String(60), nullable=True)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now().replace(microsecond=0))
    
    embalagem_escolhida = db.Column(db.String(10), nullable=False)

    # Despesas de venda
    comissao_porcentagem = db.Column(db.Numeric(10,2), default=Decimal(0))
    comissao_valor = db.Column(db.Numeric(10,2), default=Decimal(0))
    financeiro_porcentagem = db.Column(db.Numeric(10,2), default=Decimal(0))
    financeiro_valor = db.Column(db.Numeric(10,2), default=Decimal(0))
    duvidosos_porcentagem = db.Column(db.Numeric(10,2), default=Decimal(0))
    duvidosos_valor = db.Column(db.Numeric(10,2), default=Decimal(0))
    frete_porcentagem = db.Column(db.Numeric(10,2), default=Decimal(0))
    frete_valor = db.Column(db.Numeric(10,2), default=Decimal(0))
    tributos_porcentagem = db.Column(db.Numeric(10,2), default=Decimal(0))
    tributos_valor = db.Column(db.Numeric(10,2), default=Decimal(0))
    outros_porcentagem = db.Column(db.Numeric(10,2), default=Decimal(0))
    outros_valor = db.Column(db.Numeric(10,2), default=Decimal(0))

    # Custos FIXOS armazenados no banco
    custo_total = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    total_despesas_valor = db.Column(db.Numeric(10,2), default=Decimal(0))
    total_despesas_porcentagem = db.Column(db.Numeric(10,2), default=Decimal(0))
    despesas_venda = db.Column(db.Numeric(10,2), default=Decimal(0))
    
    # Novos campos para armazenar valores fixos
    preco_embalagem_escolhida = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    lucro_unitario = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    margem = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    
    # Campos para armazenar preços sugeridos
    preco_sugerido_5 = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    preco_sugerido_7 = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    preco_sugerido_10 = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    preco_sugerido_12 = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    preco_sugerido_15 = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    preco_sugerido_20 = db.Column(db.Numeric(10,2), nullable=False, default=Decimal(0))
    
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id', ondelete='CASCADE'), nullable=False)
    referencia = db.relationship('Referencia', backref=db.backref('margens', lazy=True, cascade="all, delete-orphan"))

    def calcular_custos(self):
        """ Calcula as despesas fixas da margem e armazena no banco """
        self.total_despesas_valor = (
            self.comissao_valor + self.financeiro_valor + self.duvidosos_valor +
            self.frete_valor + self.tributos_valor + self.outros_valor
        )
        
        self.total_despesas_porcentagem = (
            (self.preco_venda * (self.comissao_porcentagem / 100)) +
            (self.preco_venda * (self.financeiro_porcentagem / 100)) +
            (self.preco_venda * (self.duvidosos_porcentagem / 100)) +
            (self.preco_venda * (self.frete_porcentagem / 100)) +
            (self.preco_venda * (self.tributos_porcentagem / 100)) +
            (self.preco_venda * (self.outros_porcentagem / 100))
        )
        
        self.despesas_venda = self.total_despesas_valor + self.total_despesas_porcentagem

        if self.referencia:
            custo_embalagem = Decimal(0)

            if self.embalagem_escolhida.lower() == "cartucho":
                custo_embalagem = self.referencia.custo_total_embalagem1 or Decimal(0)
            elif self.embalagem_escolhida.lower() == "colmeia":
                custo_embalagem = self.referencia.custo_total_embalagem2 or Decimal(0)
            elif self.embalagem_escolhida.lower() == "saco":
                custo_embalagem = self.referencia.custo_total_embalagem3 or Decimal(0)
            
            # Agora armazenamos os valores fixos no banco
            self.preco_embalagem_escolhida = custo_embalagem
            self.custo_total = custo_embalagem + self.despesas_venda
            self.lucro_unitario = self.preco_venda - self.custo_total
            self.margem = self.lucro_unitario / (self.preco_venda / 100) if self.preco_venda > 0 else Decimal(0)
            
            # Cálculo dos preços sugeridos
            for margem in [5, 7, 10, 12, 15, 20]:
                percentual = Decimal(margem) / 100
                divisor = Decimal(1) - percentual - (self.total_despesas_porcentagem / self.preco_venda)
                preco_sugerido = (self.preco_embalagem_escolhida + self.total_despesas_valor) / divisor if divisor > 0 else Decimal(0)
                
                setattr(self, f'preco_sugerido_{margem}', round(preco_sugerido, 2))
                
                
    def calcular_lucros_sugeridos(self):
        """ Calcula o lucro baseado nos preços sugeridos armazenados no banco."""
        return {
            5: round(self.preco_sugerido_5 - self.custo_total, 2),
            7: round(self.preco_sugerido_7 - self.custo_total, 2),
            10: round(self.preco_sugerido_10 - self.custo_total, 2),
            12: round(self.preco_sugerido_12 - self.custo_total, 2),
            15: round(self.preco_sugerido_15 - self.custo_total, 2),
            20: round(self.preco_sugerido_20 - self.custo_total, 2)
        }





