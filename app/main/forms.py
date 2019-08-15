from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
from wtforms import ValidationError
from ..models import Student


class AddStudentForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired(), Length(0, 64)])
    role = SelectField('角色')
    # referrer = IntegerField('Referrer_ID', validators=[DataRequired(), Length(0, 64)])
    referrer = StringField('引荐人', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(AddStudentForm, self).__init__(*args, **kwargs)
        self.role.choices = [('学员', '学员'), ('合伙人', '合伙人'), ('团队领导', '团队领导')]

    def validate_name(self, field):
        if Student.query.filter_by(name=field.data).first():
            raise ValidationError('此学员姓名已经存在.')

    def validate_referrer(self, field):
        if not Student.query.filter_by(name=field.data).first():
            raise ValidationError('引荐人不存在')


class QueryStudentForm(FlaskForm):
    name = StringField('学员姓名', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('提交')


class QueryTeamForm(FlaskForm):
    leader = StringField('团队领导姓名', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('提交')

