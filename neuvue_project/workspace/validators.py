from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_submission_value(value):
    if value in ['start', 'stop', 'skip', 'flag', 'remove', 'submit']:
        raise ValidationError(
            _(f'{value} is not an valid submission value'),
            params={'value': value},
        )