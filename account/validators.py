from django.core.exceptions import ValidationError
import re

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not (len(password) >= 8 and
                re.search(r'[A-Z]', password) and
                re.search(r'[a-z]', password) and
                re.search(r'\d', password)):
            raise ValidationError(
                'Password must be at least 8 characters, contain uppercase, lowercase, and digit.'
            )
    def get_help_text(self):
        return 'Password must be at least 8 characters, contain uppercase, lowercase, and digit.'