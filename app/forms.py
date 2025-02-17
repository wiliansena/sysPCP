from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectMultipleField, StringField, SubmitField, FloatField, FileField
from wtforms.validators import DataRequired
from wtforms import SelectField
#SOLADO
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, FileField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired

class ReferenciaForm(FlaskForm):
    codigo_referencia = StringField('Código de Referência', validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    imagem = FileField('Imagem do Produto')
    submit = SubmitField('Salvar')

class ComponenteForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('PINTURA/SERIGRAFIA', 'PINTURA/SERIGRAFIA'),
                                        ('ENFEITE E ADEREÇOS', 'ENFEITE E ADEREÇOS'),
                                        ('EMBALAGENS', 'EMBALAGENS')], validators=[DataRequired()])
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








