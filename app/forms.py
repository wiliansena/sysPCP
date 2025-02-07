from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, FileField
from wtforms.validators import DataRequired
from wtforms import SelectField

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
    consumo = FloatField('Consumo', validators=[DataRequired()])
    preco_unitario = FloatField('Preço Unitário', validators=[DataRequired()])
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
