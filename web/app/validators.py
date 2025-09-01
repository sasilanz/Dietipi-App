"""
Enhanced validation classes for the IT-Kurs application.

This module provides comprehensive validation for forms and user input,
including custom validators for Swiss phone numbers and extended email validation.
"""

import re
from wtforms.validators import ValidationError, Regexp
from wtforms import validators
from .security import validate_email


class SwissPhoneValidator:
    """
    Validator for Swiss phone numbers.
    
    Accepts formats like:
    - +41 76 123 45 67
    - 076 123 45 67  
    - 0761234567
    - +41761234567
    """
    
    def __init__(self, message=None):
        if not message:
            message = 'Bitte geben Sie eine gültige Schweizer Telefonnummer ein.'
        self.message = message
    
    def __call__(self, form, field):
        if not field.data:
            return  # Optional field
            
        # Remove all spaces, dashes, and parentheses
        phone = re.sub(r'[\s\-\(\)]', '', field.data)
        
        # Swiss mobile patterns
        patterns = [
            r'^(\+41|0041)?0?7[6-9]\d{7}$',  # Mobile numbers
            r'^(\+41|0041)?0?[2-5]\d{8}$',   # Landline numbers
        ]
        
        if not any(re.match(pattern, phone) for pattern in patterns):
            raise ValidationError(self.message)


class EnhancedEmailValidator:
    """
    Enhanced email validator with domain verification and common typo detection.
    """
    
    def __init__(self, message=None, check_deliverability=False):
        if not message:
            message = 'Bitte geben Sie eine gültige E-Mail-Adresse ein.'
        self.message = message
        self.check_deliverability = check_deliverability
    
    def __call__(self, form, field):
        if not field.data:
            return
            
        if not validate_email(field.data):
            raise ValidationError(self.message)
        
        # Check for common typos in domains
        common_typos = {
            'gmial.com': 'gmail.com',
            'gmai.com': 'gmail.com', 
            'yahooo.com': 'yahoo.com',
            'hotmial.com': 'hotmail.com',
            'outlok.com': 'outlook.com'
        }
        
        domain = field.data.split('@')[-1].lower()
        if domain in common_typos:
            suggestion = f"{field.data.split('@')[0]}@{common_typos[domain]}"
            raise ValidationError(f'Meinten Sie: {suggestion}?')


class NameValidator:
    """
    Validator for names (first name, last name).
    
    - Allows letters, spaces, hyphens, apostrophes
    - Minimum 2 characters
    - Maximum 50 characters
    """
    
    def __init__(self, message=None):
        if not message:
            message = 'Name muss 2-50 Zeichen lang sein und darf nur Buchstaben, Leerzeichen, Bindestriche und Apostrophe enthalten.'
        self.message = message
    
    def __call__(self, form, field):
        if not field.data:
            return
            
        name = field.data.strip()
        
        # Length check
        if len(name) < 2 or len(name) > 50:
            raise ValidationError(self.message)
        
        # Character check (allow letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-ZäöüÄÖÜß\s\-']+$", name):
            raise ValidationError(self.message)


class CourseSelectionValidator:
    """
    Validator to ensure selected course exists and is available.
    """
    
    def __init__(self, course_loader_func, message=None):
        self.course_loader_func = course_loader_func
        if not message:
            message = 'Bitte wählen Sie einen verfügbaren Kurs aus.'
        self.message = message
    
    def __call__(self, form, field):
        if not field.data:
            raise ValidationError(self.message)
            
        try:
            courses = self.course_loader_func()
            visible_course_ids = [c['id'] for c in courses if c.get('visible', False)]
            
            if field.data not in visible_course_ids:
                raise ValidationError('Der gewählte Kurs ist nicht verfügbar.')
        except Exception:
            raise ValidationError('Fehler beim Überprüfen der Kursverfügbarkeit.')
