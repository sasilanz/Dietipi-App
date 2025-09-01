from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SelectField
from wtforms.validators import DataRequired, Optional, Length
from .validators import SwissPhoneValidator, EnhancedEmailValidator, NameValidator, CourseSelectionValidator

class RegisterForm(FlaskForm):
    first_name = StringField(
        "Vorname", 
        validators=[
            DataRequired(message="Vorname ist erforderlich."), 
            NameValidator()
        ]
    )
    last_name = StringField(
        "Nachname", 
        validators=[
            DataRequired(message="Nachname ist erforderlich."), 
            NameValidator()
        ]
    )
    email = EmailField(
        "E-Mail", 
        validators=[
            Optional(), 
            EnhancedEmailValidator()
        ]
    )
    phone = StringField(
        "Telefon", 
        validators=[
            Optional(), 
            SwissPhoneValidator()
        ]
    )
    course_id = SelectField(
        "Kurs", 
        validators=[
            DataRequired(message="Bitte wählen Sie einen Kurs aus.")
        ]
    )
    
    def __init__(self, course_loader_func=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if course_loader_func:
            # Add course validation after initialization
            self.course_id.validators.append(CourseSelectionValidator(course_loader_func))
