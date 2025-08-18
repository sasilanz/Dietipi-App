from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SelectField
from wtforms.validators import DataRequired, Optional, Email

class RegisterForm(FlaskForm):
    first_name = StringField("Vorname", validators=[DataRequired()])
    last_name = StringField("Nachname", validators=[DataRequired()])
    email = EmailField("E-Mail", validators=[Optional(), Email()])
    phone = StringField("Telefon", validators=[Optional()])
    course_id = SelectField("Kurs", validators=[DataRequired()])