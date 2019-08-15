from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
from wtforms import ValidationError
from ..models import Student


class AddStudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(0, 64)])
    role = SelectField('Role')
    # referrer = IntegerField('Referrer_ID', validators=[DataRequired(), Length(0, 64)])
    referrer = StringField('referrer_name', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(AddStudentForm, self).__init__(*args, **kwargs)
        self.role.choices = [('student', 'student'), ('partner', 'partner'), ('leader', 'leader')]

    def validate_name(self, field):
        if Student.query.filter_by(name=field.data).first():
            raise ValidationError('Name already in use.')


class QueryStudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('Submit')


class QueryTeamForm(FlaskForm):
    leader = StringField('Name', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('Submit')

