from decimal import Decimal
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from app import db
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from datetime import date, datetime, time
from datetime import datetime
import pytz

def hora_brasilia():
    return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(microsecond=0)





class Referencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo_referencia = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(200))
    linha = db.Column(db.String(50), nullable=False)
    colecao_id = db.Column(db.Integer, db.ForeignKey('colecao.id'), nullable=False)
    
    #relacionamento com a tabela coleção
    colecao = relationship("Colecao", back_populates="referencias")

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

    def calcular_totais(self, commit=True):
        """Calcula os totais individuais e os custos totais por embalagem."""
        self.total_solado = sum(solado.custo_total for solado in self.solados)
        self.total_alcas = sum(alca.custo_total for alca in self.alcas)
        self.total_componentes = sum(componente.custo_total for componente in self.componentes)
        self.total_embalagem1 = sum(embalagem.custo_total for embalagem in self.embalagem1)
        self.total_embalagem2 = sum(embalagem.custo_total for embalagem in self.embalagem2)
        self.total_embalagem3 = sum(embalagem.custo_total for embalagem in self.embalagem3)

        # 🔹 Agora garantimos que os custos operacionais sejam recalculados
        self.total_operacional = sum(custo.consumo * custo.custo.preco for custo in self.custos_operacionais)

        self.total_mao_de_obra = sum(mao.custo_total for mao in self.mao_de_obra)

        # 🔹 Cálculo do custo total para cada embalagem
        self.custo_total_embalagem1 = (self.total_solado + self.total_alcas + self.total_componentes +
                                    self.total_embalagem1 + self.total_operacional + self.total_mao_de_obra)

        self.custo_total_embalagem2 = (self.total_solado + self.total_alcas + self.total_componentes +
                                    self.total_embalagem2 + self.total_operacional + self.total_mao_de_obra)

        self.custo_total_embalagem3 = (self.total_solado + self.total_alcas + self.total_componentes +
                                    self.total_embalagem3 + self.total_operacional + self.total_mao_de_obra)
        
        db.session.add(self)  # 🔹 Adiciona a referência à sessão do banco
        if commit:
            db.session.commit()  # 🔹 Salva no banco se a flag estiver ativada







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
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    referencias = relationship("Referencia", back_populates="colecao")
    

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
    diaria = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))  # 🔹 Agora a diária será salva!

    # Relacionamento com Salario
    salario = db.relationship('Salario', backref=db.backref('mao_de_obra', lazy=True))

    def calcular_valores(self):
        """ Calcula preco_liquido, preco_bruto e diária automaticamente. """
        salario = Salario.query.get(self.salario_id)
        if not salario:
            raise ValueError("Salário não encontrado!")

        # ✅ Converte multiplicador explicitamente para Decimal
        multiplicador = Decimal(str(self.multiplicador))  

        self.preco_liquido = (multiplicador * salario.preco).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        encargos = Decimal(str(salario.encargos)) if salario.encargos else Decimal(1)
        self.preco_bruto = (self.preco_liquido * encargos).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # 🔹 Cálculo da diária (salva no banco)
        self.diaria = (self.preco_bruto / Decimal(21)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP) if self.preco_bruto > 0 else Decimal(0)





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
        
            # 🔹 Arredonda para **três casas decimais**
        peso_sem_friso_total = peso_sem_friso_total.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        peso_medio_total = peso_medio_total.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

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



 ####   USUÁRIO    ######
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model, UserMixin):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)

    permissoes = db.relationship("Permissao", backref="usuario", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def todas_permissoes(self):
        """Carrega todas as permissões do usuário como um conjunto de tuplas."""
        return {(p.categoria, p.acao) for p in self.permissoes.all()}

    def tem_permissao(self, categoria, acao):
        """Verifica se o usuário tem permissão para acessar determinada ação."""
        return (categoria, acao) in self.todas_permissoes
    
    def pode_trocar_senha(self):
        """Verifica se o usuário tem permissão para trocar senha."""
        return self.tem_permissao('trocar_senha', 'editar')  # 🔹 Nova verificação de permissão


class Permissao(db.Model):
    __tablename__ = "permissao"
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  # Ex: 'margens', 'custoproducao'
    acao = db.Column(db.String(20), nullable=False)  # Ex: 'ver', 'editar', 'excluir'

    __table_args__ = (db.UniqueConstraint('usuario_id', 'categoria', 'acao', name='unique_permissao_usuario'),)






class LogAcao(db.Model):
    __tablename__ = "log_acao"  # 🔹 Nome da tabela no banco

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)  # 🔹 Corrigido para "usuario.id"
    usuario_nome = db.Column(db.String(100), nullable=False)  # 🔹 Tamanho ajustado para compatibilidade
    acao = db.Column(db.String(255), nullable=False)
    data_hora = db.Column(db.DateTime, default=lambda: datetime.now().replace(microsecond=0))  # 🔹 Adicionando data e hora exata

    usuario = db.relationship('Usuario', backref=db.backref('logs', lazy=True))  # 🔹 Relacionamento com a tabela Usuario



#####   MARGEM   #########

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

    #DOLAR
    dolar = db.Column(db.Numeric(10,2), nullable=True)
    preco_venda_dolar = db.Column(db.Numeric(10,2), nullable=True, default=Decimal(0))


    #RELACIONAMENTOS
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

        self.total_despesas_porcentagem_decimal = (
            (self.comissao_porcentagem + self.financeiro_porcentagem
              + self.duvidosos_porcentagem + self.frete_porcentagem + 
               self.tributos_porcentagem + self.outros_porcentagem
              )/100

        )

        #DOLAR calculo do preço de venda em dolar

        if self.dolar and self.dolar > 0:
            self.preco_venda_dolar = round(self.preco_venda / self.dolar, 2)
        else:
            self.preco_venda_dolar = Decimal(0)

            ####

        print(f"[DEBUG] Despesas Porcentagem Decimal: {self.total_despesas_porcentagem_decimal}")
        
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
                divisor = Decimal(1) - Decimal(percentual + self.total_despesas_porcentagem_decimal)
                print(f"[DEBUG] Divisor: {divisor}")
                preco_sugerido = (self.preco_embalagem_escolhida + self.total_despesas_valor) / divisor if divisor > 0 else Decimal(0)
                
                setattr(self, f'preco_sugerido_{margem}', round(preco_sugerido, 2))
                
                
    def calcular_lucros_sugeridos(self):
        """ Calcula o lucro baseado nos preços sugeridos armazenados no banco."""
        return {
            5: round(self.preco_sugerido_5 * Decimal(0.05), 2),
            7: round(self.preco_sugerido_7 * Decimal(0.07), 2),
            10: round(self.preco_sugerido_10 * Decimal(0.10), 2),
            12: round(self.preco_sugerido_12 * Decimal(0.12), 2),
            15: round(self.preco_sugerido_15 * Decimal(0.15), 2),
            20: round(self.preco_sugerido_20 * Decimal(0.20), 2)
        }



class MargemPorPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido = db.Column(db.String(50), nullable=False)  # Número do pedido
    nota_fiscal = db.Column(db.String(50), nullable=True)
    cliente = db.Column(db.String(100), nullable=True)
    remessa = db.Column(db.String(20), nullable=True)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now().replace(microsecond=0))

    referencias = db.relationship('MargemPorPedidoReferencia', backref='margem_pedido', cascade="all, delete-orphan")

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

    # Totais calculados
    total_porcentagem = db.Column(db.Numeric(10,2), default=Decimal(0))  # 🔹 Agora será calculado corretamente em R$
    total_valor = db.Column(db.Numeric(10,2), default=Decimal(0))
    total_despesas_venda = db.Column(db.Numeric(10,2), default=Decimal(0))
    total_custo = db.Column(db.Numeric(10,2), default=Decimal(0))
    total_preco_venda = db.Column(db.Numeric(10,2), default=Decimal(0))
    lucro_total = db.Column(db.Numeric(10,2), default=Decimal(0))
    margem_media = db.Column(db.Numeric(10,2), default=Decimal(0))

    def calcular_totais(self):
        """ 
        Calcula os totais corretamente, incluindo total_porcentagem baseado em total_preco_venda.
        """
        # 🔹 Calculamos primeiro o total_preco_venda para poder usá-lo no cálculo de total_porcentagem
        self.total_preco_venda = sum(ref.total_preco_venda for ref in self.referencias)

        # 🔹 Agora, total_porcentagem é calculado em reais com base no total_preco_venda
        self.total_porcentagem = (
            (self.total_preco_venda * (self.comissao_porcentagem / 100)) +
            (self.total_preco_venda * (self.financeiro_porcentagem / 100)) +
            (self.total_preco_venda * (self.duvidosos_porcentagem / 100)) +
            (self.total_preco_venda * (self.frete_porcentagem / 100)) +
            (self.total_preco_venda * (self.tributos_porcentagem / 100)) +
            (self.total_preco_venda * (self.outros_porcentagem / 100))
        )

        # 🔹 Agora calculamos total_valor (valores já informados pelo usuário)
        self.total_valor = (
            self.comissao_valor + self.financeiro_valor + self.duvidosos_valor +
            self.frete_valor + self.tributos_valor + self.outros_valor
        )

        # 🔹 Agora, total_despesas_venda é a soma correta de total_porcentagem e total_valor
        self.total_despesas_venda = self.total_porcentagem + self.total_valor

        # 🔹 Agora, total_custo inclui as despesas de venda corretamente
        self.total_custo = sum(ref.total_custo for ref in self.referencias) + self.total_despesas_venda

        # 🔹 Cálculo do lucro total
        self.lucro_total = self.total_preco_venda - self.total_custo

        # 🔹 Cálculo da margem média
        self.margem_media = (self.lucro_total / self.total_preco_venda * 100) if self.total_preco_venda > 0 else 0


class MargemPorPedidoReferencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    margem_pedido_id = db.Column(db.Integer, db.ForeignKey('margem_por_pedido.id'), nullable=False)
    referencia_id = db.Column(db.Integer, db.ForeignKey('referencia.id'), nullable=False)

    quantidade = db.Column(db.Integer, nullable=False)
    preco_venda = db.Column(db.Numeric(10,2), nullable=False)  # 🔹 Usuário digita o preço de venda
    embalagem_escolhida = db.Column(db.String(20), nullable=False)

    total_custo = db.Column(db.Numeric(10,2), nullable=False)  # 🔹 Agora sem despesas de venda
    total_preco_venda = db.Column(db.Numeric(10,2), nullable=False)  # 🔹 Calculado por referência

    referencia = db.relationship("Referencia")

    def calcular_totais(self):
        """ 
        Calcula o custo e preço de venda da referência no pedido.
        """
        # 🔹 Verifica se a referência está associada corretamente
        if not self.referencia:
            self.referencia = Referencia.query.get(self.referencia_id)  # 🔹 Tenta carregar manualmente
            if not self.referencia:
                print(f"⚠️ ERRO: Referência ID {self.referencia_id} não encontrada no banco!")
                return  # 🔹 Sai da função sem fazer cálculos se a referência não for encontrada

        custo_unitario = Decimal(0)

        # 🔹 Usa os preços de acordo com a embalagem escolhida
        if self.embalagem_escolhida.lower() == "cartucho":
            custo_unitario = self.referencia.custo_total_embalagem1 or Decimal(0)
        elif self.embalagem_escolhida.lower() == "colmeia":
            custo_unitario = self.referencia.custo_total_embalagem2 or Decimal(0)
        elif self.embalagem_escolhida.lower() == "saco":
            custo_unitario = self.referencia.custo_total_embalagem3 or Decimal(0)

        # 🔹 Total custo = custo da embalagem * quantidade
        self.total_custo = custo_unitario * self.quantidade

        # 🔹 Total preço venda = preço unitário digitado * quantidade
        self.total_preco_venda = self.preco_venda * self.quantidade

        print(f"✔️ Cálculo feito: Ref {self.referencia_id} | Total Custo: {self.total_custo} | Total Preço Venda: {self.total_preco_venda}")



#### CONTROLE DE PRODUÇÃO   ########

class Maquina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Ativa")  # Ativa/Inativa
    preco = db.Column(db.Numeric(10,4), nullable=False, default=Decimal(0))


class TrocaHorario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    troca_matriz_id = db.Column(db.Integer, db.ForeignKey('troca_matriz.id'), nullable=False)
    horario = db.Column(db.String(20), nullable=False)
    pares = db.Column(db.Integer, default=0)
    producao_esperada = db.Column(db.Integer, default=0)  # pares esperados nesse horário
    

        # Relação com a matriz utilizada nesse horário
    matriz_id = db.Column(db.Integer, db.ForeignKey('matriz.id'), nullable=True)
    matriz = db.relationship("Matriz", backref=db.backref("usos", lazy=True))


    # Horários das trocas
    inicio_1 = db.Column(db.Time, nullable=True)
    fim_1 = db.Column(db.Time, nullable=True)
    inicio_2 = db.Column(db.Time, nullable=True)
    fim_2 = db.Column(db.Time, nullable=True)
    inicio_3 = db.Column(db.Time, nullable=True)
    fim_3 = db.Column(db.Time, nullable=True)
    inicio_4 = db.Column(db.Time, nullable=True)
    fim_4 = db.Column(db.Time, nullable=True)
    inicio_5 = db.Column(db.Time, nullable=True)
    fim_5 = db.Column(db.Time, nullable=True)
    inicio_6 = db.Column(db.Time, nullable=True)
    fim_6 = db.Column(db.Time, nullable=True)
    inicio_7 = db.Column(db.Time, nullable=True)
    fim_7 = db.Column(db.Time, nullable=True)

    # motivo
    motivo_1 = db.Column(db.String(50), nullable=True)
    motivo_2 = db.Column(db.String(50), nullable=True)
    motivo_3 = db.Column(db.String(50), nullable=True)
    motivo_4 = db.Column(db.String(50), nullable=True)
    motivo_5 = db.Column(db.String(50), nullable=True)
    motivo_6 = db.Column(db.String(50), nullable=True)
    motivo_7 = db.Column(db.String(50), nullable=True)


    # Campos de duração para cada troca
    duracao_1 = db.Column(db.Integer, default=0)  # Minutos
    duracao_2 = db.Column(db.Integer, default=0)
    duracao_3 = db.Column(db.Integer, default=0)
    duracao_4 = db.Column(db.Integer, default=0)
    duracao_5 = db.Column(db.Integer, default=0)
    duracao_6 = db.Column(db.Integer, default=0)
    duracao_7 = db.Column(db.Integer, default=0)

    # Tempo total das trocas nesse intervalo
    tempo_total_troca = db.Column(db.Integer, default=0)

    def calcular_duracao(self, inicio, fim):
        """Calcula a duração em minutos entre os horários"""
        if inicio and fim:
            delta = datetime.combine(datetime.today(), fim) - datetime.combine(datetime.today(), inicio)
            return delta.total_seconds() // 60  # Converte para minutos
        return 0

    def atualizar_tempo_total(self):
        """Atualiza os tempos de todas as trocas"""
        self.duracao_1 = self.calcular_duracao(self.inicio_1, self.fim_1)
        self.duracao_2 = self.calcular_duracao(self.inicio_2, self.fim_2)
        self.duracao_3 = self.calcular_duracao(self.inicio_3, self.fim_3)
        self.duracao_4 = self.calcular_duracao(self.inicio_4, self.fim_4)
        self.duracao_5 = self.calcular_duracao(self.inicio_5, self.fim_5)
        self.duracao_6 = self.calcular_duracao(self.inicio_6, self.fim_6)
        self.duracao_7 = self.calcular_duracao(self.inicio_7, self.fim_7)

        self.tempo_total_troca = (
            self.duracao_1 + self.duracao_2 + self.duracao_3 +
            self.duracao_4 + self.duracao_5 + self.duracao_6 + self.duracao_7
        )
        
    
    def eficiencia_por_tempo(self):
        tempo_util = 60 - self.tempo_total_troca
        if tempo_util <= 0:
            return 0  # Evita divisão por zero ou tempo negativo
        return round(self.pares / tempo_util, 2)  # 2 casas decimais
    
    @property
    def diferenca(self):
        return (self.pares or 0) - (self.producao_esperada or 0)




class TrocaMatriz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    trocador_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    operador_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    maquina_id = db.Column(db.Integer, db.ForeignKey('maquina.id'), nullable=False)

    #RELACIONAMENTOS
    trocador = db.relationship("Funcionario", foreign_keys=[trocador_id])
    operador = db.relationship("Funcionario", foreign_keys=[operador_id])
    maquina = db.relationship("Maquina", backref=db.backref("trocas", lazy=True))
    horarios = db.relationship("TrocaHorario", backref="troca", lazy=True, cascade="all, delete-orphan")

    # 🔹 Novo campo para armazenar tempo total gasto em todas as trocas
    tempo_total_geral = db.Column(db.Integer, nullable=False, default=0)
    total_pares_produzidos = db.Column(db.Integer, nullable=False, default=0)  # 🔹 Novo campo para armazenar o total

    def atualizar_tempo_total_geral(self):
        """ Soma o tempo total de todas as trocas dessa matriz e salva no banco. """
        for horario in self.horarios:
            horario.atualizar_tempo_total()  # Garante que todas as trocas estão atualizadas
        self.tempo_total_geral = sum(horario.tempo_total_troca for horario in self.horarios)

    def calcular_total_pares(self):
        """Calcula a quantidade total de pares produzidos e atualiza o campo."""
        self.total_pares_produzidos = sum(h.pares for h in self.horarios)

    def calcular_eficiencia_geral(self):
        tempo_produtivo = self.calcular_tempo_produtivo_real()
        if tempo_produtivo > 0:
            return round(self.total_pares_produzidos / tempo_produtivo, 2)
        return 0.00

    
    def calcular_total_esperado(self):
        return sum(h.producao_esperada for h in self.horarios)
    
    
    def calcular_tempo_produtivo_real(self):
        """
        Retorna o tempo produtivo real com base nos horários preenchidos,
        subtraindo o tempo de troca dentro desses blocos.
        """
        tempo_produtivo = 0
        for horario in self.horarios:
            if horario.pares > 0 or horario.tempo_total_troca > 0:
                tempo_util_bloco = 60 - horario.tempo_total_troca
                if tempo_util_bloco > 0:
                    tempo_produtivo += tempo_util_bloco
        return tempo_produtivo




class Matriz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    descricao = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='Ativa')  # Ativa ou Inativa
    capacidade = db.Column(db.Integer, nullable=True)
    quantidade = db.Column(db.Integer, default=0)
    imagem = db.Column(db.String(200), nullable=True)

    # Relacionamentos
    linha_id = db.Column(db.Integer, db.ForeignKey('linha.id'))
    linha = db.relationship('Linha', backref='matrizes')

    cores = db.relationship('Cor', secondary='matriz_cor', backref='matrizes')

    tamanhos = db.relationship('TamanhoMatriz', back_populates='matriz', cascade='all, delete-orphan')

    def calcular_total_grade(self):
        return sum(t.quantidade for t in self.tamanhos)


class TamanhoMatriz(db.Model):
    __tablename__ = "tamanho_matriz"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=False)  # Ex: 25/26
    quantidade = db.Column(db.Integer, nullable=False, default=0)

    matriz_id = db.Column(db.Integer, db.ForeignKey('matriz.id'))
    matriz = db.relationship("Matriz", back_populates="tamanhos")


# Tabela associativ a para cores
matriz_cor = db.Table('matriz_cor',
    db.Column('matriz_id', db.Integer, db.ForeignKey('matriz.id'), primary_key=True),
    db.Column('cor_id', db.Integer, db.ForeignKey('cor.id'), primary_key=True)
)


class Funcionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    funcao = db.Column(db.String(50), nullable=False)  # Exemplo: Operador, Trocador, Técnico

# Modelo correto

class OrdemCompra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_inicio = db.Column(db.DateTime, default=lambda: datetime.now().replace(microsecond=0))
    data_fim = db.Column(db.DateTime, nullable=True)
    titulo = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Aberto")
    setor = db.Column(db.String(20), nullable=False)
    prioridade = db.Column(db.String(20), nullable=False, default="Baixa")
    solicitante_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=True)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=True)
    descricao = db.Column(db.String(150), nullable=False)
    nota_fiscal = db.Column(db.String(50), nullable=True)
    valor = db.Column(db.Numeric(10,2), default=Decimal(0))

    #RELAÇÕES
    solicitante = db.relationship("Funcionario", foreign_keys=[solicitante_id])
    responsavel = db.relationship("Funcionario", foreign_keys=[responsavel_id])



class Manutencao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_inicio = db.Column(db.DateTime, default=lambda: datetime.now().replace(microsecond=0))
    data_fim = db.Column(db.DateTime, nullable=True)
    titulo = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Aberto")
    tipo = db.Column(db.String(20), nullable=False, default="Corretiva")
    prioridade = db.Column(db.String(20), nullable=False, default="Baixa")
    solicitante_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=True)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=True)
    descricao = db.Column(db.String(150), nullable=False)

    #RELAÇÕES
    solicitante = db.relationship("Funcionario", foreign_keys=[solicitante_id])
    responsavel = db.relationship("Funcionario", foreign_keys=[responsavel_id])
    maquinas = db.relationship("ManutencaoMaquina", backref="manutencao", cascade="all, delete-orphan", lazy="joined")
    componentes = db.relationship("ManutencaoComponente", backref="manutencao", cascade="all, delete-orphan", lazy="joined")

class ManutencaoMaquina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manutencao_id = db.Column(db.Integer, db.ForeignKey('manutencao.id'))
    maquina_id = db.Column(db.Integer, db.ForeignKey('maquina.id'))

    maquina = db.relationship("Maquina")


class ManutencaoComponente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manutencao_id = db.Column(db.Integer, db.ForeignKey('manutencao.id'))
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id'))

    componente = db.relationship("Componente")

class Cor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=False)

class Linha(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=False)
    grupo = db.Column(db.String(20), nullable=True)


class MovimentacaoMatriz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=lambda: datetime.now().replace(microsecond=0))
    tipo = db.Column(db.String(10), nullable=False)  # 'Entrada' ou 'Saída'
    motivo = db.Column(db.String(100), nullable=False)
    posicao_estoque = db.Column(db.String(50), nullable=True)

    matriz_id = db.Column(db.Integer, db.ForeignKey('matriz.id'), nullable=False)
    cor_id = db.Column(db.Integer, db.ForeignKey('cor.id'), nullable=False)

    matriz = db.relationship('Matriz', backref='movimentacoes')
    cor = db.relationship('Cor')

    tamanhos_movimentados = db.relationship('TamanhoMovimentacao', backref='movimentacao', cascade='all, delete-orphan')


class TamanhoMovimentacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=False)  # Ex: 25/26
    quantidade = db.Column(db.Integer, nullable=False, default=0)

    movimentacao_id = db.Column(db.Integer, db.ForeignKey('movimentacao_matriz.id'), nullable=False)

    
    
class Grade(db.Model):
    __tablename__ = 'grade'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)

    tamanhos = db.relationship('TamanhoGrade', back_populates='grade', cascade='all, delete-orphan')

class TamanhoGrade(db.Model):
    __tablename__ = 'tamanho_grade'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=False)
    quantidade = db.Column(db.Integer, default=0)

    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'))
    grade = db.relationship('Grade', back_populates='tamanhos')

    
class Remessa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    data_criacao = db.Column(db.DateTime, default=hora_brasilia)
    data_fechamento = db.Column(db.DateTime, nullable=True)

    planejamentos = db.relationship("PlanejamentoProducao", back_populates="remessa", cascade="all, delete-orphan")

    def verificar_fechamento(self):
        if all(p.fechado for p in self.planejamentos):
            if not self.data_fechamento:
                self.data_fechamento = hora_brasilia()

class PlanejamentoProducao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    setor = db.Column(db.String(100), nullable=False)

    esteira = db.Column(db.Boolean, default=False)
    esteira_qtd = db.Column(db.Integer, default=0)

    fechado = db.Column(db.Boolean, default=False)
    data_fechado = db.Column(db.DateTime)

    data_criacao = db.Column(db.DateTime, default=hora_brasilia)

    linha_id = db.Column(db.Integer, db.ForeignKey("linha.id"))
    linha = db.relationship("Linha")

    remessa_id = db.Column(db.Integer, db.ForeignKey("remessa.id"))
    remessa = db.relationship("Remessa", back_populates="planejamentos")

    @property
    def faltando(self):
        return max(self.quantidade - self.esteira_qtd, 0)






