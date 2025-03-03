from typing import Optional
from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, HiddenField, SelectMultipleField, StringField, SubmitField, FloatField, FileField
from wtforms.validators import DataRequired
from wtforms import SelectField
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, FileField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from datetime import date


class ColecaoForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired()])
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



from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Optional
from datetime import date

class MargemForm(FlaskForm):
    referencia_id = HiddenField('Referência', validators=[DataRequired()])
    cliente = StringField('Cliente', validators=[Optional()])
    
    # 🔹 Seleção da Embalagem
    embalagem_escolhida = SelectField(
        'Embalagem Escolhida', 
        choices=[('Cartucho', 'Cartucho'), ('Colmeia', 'Colmeia'), ('Saco', 'Saco')],
        validators=[DataRequired()]
    )

    preco_venda = DecimalField('Preço de Venda', places=2, validators=[DataRequired(), NumberRange(min=0)])
    
    # 🔹 Despesas de Venda
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
    
    # 🔹 Campos ocultos para cálculo automático
    custo_venda = HiddenField()
    custo_margem_embalagem = HiddenField()
    lucro_unitario = HiddenField()
    margem = HiddenField()
    
    # 🔹 Data de Criação (oculta no formulário, mas preenchida automaticamente)
    data_criacao = HiddenField(default=date.today())

    submit = SubmitField('Salvar Margem')












