from decimal import Decimal
from typing import Optional
from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, HiddenField, SelectMultipleField, StringField, SubmitField, FloatField, FileField
from wtforms.validators import DataRequired
from wtforms import SelectField
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, FileField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from datetime import date
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo



class UsuarioForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(min=3, max=100)])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6, max=100)])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('senha', message='As senhas devem coincidir.')])
    permissao = SelectField('Permissão', choices=[('admin', 'Administrador'), ('usuario', 'Usuário Padrão')], validators=[DataRequired()])
    submit = SubmitField('Salvar')


class ColecaoForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Salvar')

class ComponenteForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('PINTURA/SERIGRAFIA', 'PINTURA/SERIGRAFIA'),
                                        ('ENFEITE E ADEREÇOS', 'ENFEITE E ADEREÇOS'),
                                        ('EMBALAGENS', 'EMBALAGENS'),
                                        ('QUIMICOS', 'QUIMICOS'),
                                        ('CADARÇOS', 'CADARÇOS'),
                                        ('CAIXA', 'CAIXA'),
                                        ('BOTÕES-PINOS-REBITE', 'BOTÕES-PINOS-REBITE'),
                                        ('EMBALAGENS', 'EMBALAGENS'),
                                        ('INFORMATICA', 'INFORMATICA'),
                                        ('ESCRITORIO', 'ESCRITORIO')], validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    unidade_medida = SelectField('Unidade de Medida', choices=[('KQ', 'KQ'), ('L', 'L'), ('M', 'M'), ('UND', 'UND')], validators=[DataRequired()])
    preco = FloatField('Preço', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class CustoOperacionalForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('OPERACIONAL', 'OPERACIONAL'),
                                        ('FIXO', 'FIXO'),
                                        ('INDIRETO', 'INDIRETO')], validators=[DataRequired()])
    unidade_medida = SelectField('Unidade de Medida', choices=[('KQ', 'KQ'), ('L', 'L'), ('M', 'M'), ('UND', 'UND')], validators=[DataRequired()])
    preco = FloatField('Preço', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class SalarioForm(FlaskForm):
    preco = FloatField('Salário', validators=[DataRequired()])
    encargos = FloatField('Encargos', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class MaoDeObraForm(FlaskForm):
    descricao = StringField('Descrição', validators=[DataRequired()])
    salario_id = SelectField('Salário', coerce=int, validators=[DataRequired()])
    multiplicador = FloatField('Multiplicador', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class TamanhoForm(FlaskForm):
    nome = StringField('Tamanho')
    quantidade = IntegerField('Quantidade')
    peso_medio = FloatField('Peso Médio')
    peso_friso = FloatField('Peso Friso')
    peso_sem_friso = FloatField('Peso Sem Friso')

class SoladoForm(FlaskForm):
    referencia = StringField('Referência', validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    imagem = FileField('Imagem do Solado')
    tamanhos = FieldList(FormField(TamanhoForm), min_entries=8, max_entries=8)  # Permite até 8 tamanhos
    submit = SubmitField('Salvar')

class FormulacaoSoladoForm(FlaskForm):
    componente_id = IntegerField('ID do Componente', validators=[DataRequired()])
    carga = FloatField('Carga (kg)', default=0.0)


    #ALCAS

class TamanhoAlcaForm(FlaskForm):
    nome = StringField('Nome')
    quantidade = IntegerField('Quantidade')
    peso_medio = FloatField('Peso Médio')
    
    
class AlcaForm(FlaskForm):
    referencia = StringField('Referência', validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    imagem = FileField('Imagem da Alça')

    tamanhos = FieldList(FormField(TamanhoAlcaForm), min_entries=8)
    componentes = SelectMultipleField('Componentes', coerce=int)

    submit = SubmitField('Salvar')

class FormulacaoAlcaForm(FlaskForm):
    componente_id = SelectField('Componente', coerce=int)
    carga = DecimalField('Carga (Kg)', default=0.0)



class ReferenciaForm(FlaskForm):
    codigo_referencia = StringField('Código da Referência', validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    linha = SelectField('Linha', choices=[('MASCULINO', 'MASCULINO'),
                                          ('FEMININO', 'FEMININO'),
                                          ('BABY', 'BABY')], validators=[DataRequired()])
    colecao_id = SelectField('Coleção', coerce=int)
    imagem = FileField('Imagem', validators=[Optional()])
    
    total_solado = HiddenField("total_solado")
    total_alcas = HiddenField("total_alcas")
    total_componentes = HiddenField("total_componentes")
    total_operacional = HiddenField("total_operacional")
    total_mao_de_obra = HiddenField("total_mao_obra")
    
    solados = SelectMultipleField('Solados', coerce=int)
    alcas = SelectMultipleField('Alças', coerce=int)
    componentes = SelectMultipleField('Componentes', coerce=int)
    custos_operacionais = SelectMultipleField('Custos Operacionais', coerce=int)
    mao_de_obra = SelectMultipleField('Mão de Obra', coerce=int)
    
    submit = SubmitField('Salvar')

class ReferenciaSoladoForm(FlaskForm):
    solado_id = SelectField('Solado', coerce=int, validators=[DataRequired()])
    consumo = DecimalField('Consumo', places=4, validators=[DataRequired()])
    submit = SubmitField('Adicionar Solado')

class ReferenciaAlcaForm(FlaskForm):
    alca_id = SelectField('Alça', coerce=int, validators=[DataRequired()])
    consumo = DecimalField('Consumo', places=4, validators=[DataRequired()])
    submit = SubmitField('Adicionar Alça')

class ReferenciaComponentesForm(FlaskForm):
    componente_id = SelectField('Componente', coerce=int, validators=[DataRequired()])
    consumo = DecimalField('Consumo', places=4, validators=[DataRequired()])
    submit = SubmitField('Adicionar Componente')

class ReferenciaCustoOperacionalForm(FlaskForm):
    custo_id = SelectField('Custo Operacional', coerce=int, validators=[DataRequired()])
    consumo = DecimalField('Consumo', places=4, validators=[DataRequired()])
    submit = SubmitField('Adicionar Custo Operacional')

class ReferenciaMaoDeObraForm(FlaskForm):
    mao_de_obra_id = SelectField('Mão de Obra', coerce=int, validators=[DataRequired()])
    consumo = DecimalField('Consumo', places=4, validators=[DataRequired()])
    producao = IntegerField('Produção', validators=[DataRequired()])
    submit = SubmitField('Adicionar Mão de Obra')



class MargemForm(FlaskForm):
    referencia_id = HiddenField('Referência', validators=[DataRequired()])
    cliente = StringField('Cliente', validators=[Optional()])
    
    embalagem_escolhida = SelectField(
        'Embalagem Escolhida', 
        choices=[('Cartucho', 'Cartucho'), ('Colmeia', 'Colmeia'), ('Saco', 'Saco')],
        validators=[DataRequired()]
    )

    preco_venda = DecimalField('Preço de Venda', places=2, validators=[DataRequired(), NumberRange(min=0)])
    
    # Despesas de Venda
    comissao_porcentagem = DecimalField('Comissão (%)', places=2, default=0, validators=[Optional()])
    comissao_valor = DecimalField('Comissão (R$)', places=2, default=0, validators=[Optional()])
    financeiro_porcentagem = DecimalField('Financeiro (%)', places=2, default=0, validators=[Optional()])
    financeiro_valor = DecimalField('Financeiro (R$)', places=2, default=0, validators=[Optional()])
    duvidosos_porcentagem = DecimalField('Duvidosos (%)', places=2, default=0, validators=[Optional()])
    duvidosos_valor = DecimalField('Duvidosos (R$)', places=2, default=0, validators=[Optional()])
    frete_porcentagem = DecimalField('Frete (%)', places=2, default=0, validators=[Optional()])
    frete_valor = DecimalField('Frete (R$)', places=2, default=0, validators=[Optional()])
    tributos_porcentagem = DecimalField('Tributos (%)', places=2, default=0, validators=[Optional()])
    tributos_valor = DecimalField('Tributos (R$)', places=2, default=0, validators=[Optional()])
    outros_porcentagem = DecimalField('Outros (%)', places=2, default=0, validators=[Optional()])
    outros_valor = DecimalField('Outros (R$)', places=2, default=0, validators=[Optional()])
    
    # Campos ocultos para cálculos automáticos
    custo_total = HiddenField()
    preco_embalagem_escolhida = HiddenField()
    lucro_unitario = HiddenField()
    margem = HiddenField()
    
    # Campos para armazenar preços sugeridos
    preco_sugerido_5 = HiddenField()
    preco_sugerido_7 = HiddenField()
    preco_sugerido_10 = HiddenField()
    preco_sugerido_12 = HiddenField()
    preco_sugerido_15 = HiddenField()
    preco_sugerido_20 = HiddenField()
    
    data_criacao = HiddenField()
    
    submit = SubmitField('Salvar Margem')


class MargemPorPedidoForm(FlaskForm):
    """ Formulário para criar uma nova Margem por Pedido """
    pedido = StringField('Pedido', validators=[DataRequired()])
    nota_fiscal = StringField('Nota Fiscal', validators=[Optional()])
    cliente = StringField('Cliente', validators=[Optional()])
    remessa = StringField('Remessa', validators=[Optional()])

    # Campos das despesas de venda
    comissao_porcentagem = DecimalField('Comissão (%)', places=2, default=Decimal(0))
    comissao_valor = DecimalField('Comissão (R$)', places=2, default=Decimal(0))
    financeiro_porcentagem = DecimalField('Financeiro (%)', places=2, default=Decimal(0))
    financeiro_valor = DecimalField('Financeiro (R$)', places=2, default=Decimal(0))
    duvidosos_porcentagem = DecimalField('Duvidosos (%)', places=2, default=Decimal(0))
    duvidosos_valor = DecimalField('Duvidosos (R$)', places=2, default=Decimal(0))
    frete_porcentagem = DecimalField('Frete (%)', places=2, default=Decimal(0))
    frete_valor = DecimalField('Frete (R$)', places=2, default=Decimal(0))
    tributos_porcentagem = DecimalField('Tributos (%)', places=2, default=Decimal(0))
    tributos_valor = DecimalField('Tributos (R$)', places=2, default=Decimal(0))
    outros_porcentagem = DecimalField('Outros (%)', places=2, default=Decimal(0))
    outros_valor = DecimalField('Outros (R$)', places=2, default=Decimal(0))

    # 🔹 Campos de totais calculados no modelo
    total_porcentagem = DecimalField('Total Porcentagem', places=2, default=Decimal(0))
    total_valor = DecimalField('Total Valor', places=2, default=Decimal(0))
    total_despesas_venda = DecimalField('Total Despesas Venda', places=2, default=Decimal(0))
    total_custo = DecimalField('Total Custo', places=2, default=Decimal(0))
    total_preco_venda = DecimalField('Total Preço Venda', places=2, default=Decimal(0))
    lucro_total = DecimalField('Lucro Total', places=2, default=Decimal(0))
    margem_media = DecimalField('Margem Média (%)', places=2, default=Decimal(0))
    
    data_criacao = HiddenField()

    submit = SubmitField('Salvar Margem por Pedido')


class MargemPorPedidoReferenciaForm(FlaskForm):
    """ Formulário para adicionar referências a um Pedido """
    referencia_id = SelectMultipleField('Referências', coerce=int)
    embalagem_escolhida = SelectField(
        'Embalagem Escolhida', 
        choices=[('Cartucho', 'Cartucho'), ('Colmeia', 'Colmeia'), ('Saco', 'Saco')],
        validators=[DataRequired()]
    )
    quantidade = IntegerField('Quantidade', validators=[DataRequired()])
    preco_venda = DecimalField('Preço de Venda', places=2, validators=[DataRequired()])

    submit = SubmitField('Adicionar Referência')


##### CONTROLE DE PRODUÇÃO    #########

class MaquinaForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('INJETORA/ROTATIVA', 'INJETORA/ROTATIVA'),
                                        ('INJETORA/CONVENCIONAL', 'INJETORA/CONVENCIONAL'),
                                        ('PINTURA', 'EMBALAGENS'),
                                        ('CONFORMAÇÃO', 'CONFORMAÇÃO'),
                                        ('EMBALADOR', 'EMBALADOR')], validators=[DataRequired()])
    status = SelectField('Tipo', choices=[('ATIVA', 'ATIVA'),
                                          ('INATIVA', 'INATIVA')
                                          ], validators=[DataRequired()])
    preco = FloatField('Preço')
    
    submit = SubmitField('Salvar')

class TrocaForm(FlaskForm):
    horario = StringField("Horário", render_kw={"readonly": True})
    pares = IntegerField("Pares Produzidos", validators=[Optional()])
    inicio_1 = StringField("1ª Troca - Início", validators=[Optional()])
    fim_1 = StringField("1ª Troca - Fim", validators=[Optional()])
    inicio_2 = StringField("2ª Troca - Início", validators=[Optional()])
    fim_2 = StringField("2ª Troca - Fim", validators=[Optional()])
    inicio_3 = StringField("3ª Troca - Início", validators=[Optional()])
    fim_3 = StringField("3ª Troca - Fim", validators=[Optional()])
    inicio_4 = StringField("4ª Troca - Início", validators=[Optional()])
    fim_4 = StringField("4ª Troca - Fim", validators=[Optional()])
    inicio_5 = StringField("5ª Troca - Início", validators=[Optional()])
    fim_5 = StringField("5ª Troca - Fim", validators=[Optional()])
    inicio_6 = StringField("6ª Troca - Início", validators=[Optional()])
    fim_6 = StringField("6ª Troca - Fim", validators=[Optional()])
    inicio_7 = StringField("7ª Troca - Início", validators=[Optional()])
    fim_7 = StringField("7ª Troca - Fim", validators=[Optional()])


class TrocaMatrizForm(FlaskForm):
    data = DateField("Data", format='%Y-%m-%d', validators=[DataRequired()])
    trocador_id = SelectField("Trocador", coerce=int, validators=[DataRequired()])
    operador_id = SelectField("Operador", coerce=int, validators=[DataRequired()])
    maquina_id = SelectField("Máquina", coerce=int, validators=[DataRequired()])
    
    # 🔹 Define corretamente a lista de trocas com 10 linhas padrão
    trocas = FieldList(FormField(TrocaForm), min_entries=10)
    
    submit = SubmitField("Salvar")


class FuncionarioForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired()])
    funcao = SelectField("Função", choices=[("Operador", "Operador"), ("Trocador", "Trocador"), ("Técnico", "Técnico")])
    submit = SubmitField("Salvar")







