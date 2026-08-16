import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

EGYPT_PHONE_REGEX = r'^(\+201|01)[0125]\d{8}$'

def validate_egyptian_phone(value):
    """
    Validates that a phone number matches standard Egyptian mobile carrier prefixes:
    Vodafone (010), Etisalat (011), Orange (012), WE (015), or with international prefix +20.
    Example valid formats: 01012345678, +201112345678, 01555555555.
    """
    if not value:
        return
    cleaned_value = value.strip().replace(' ', '')
    if not re.match(EGYPT_PHONE_REGEX, cleaned_value):
        raise ValidationError(
            _('Please enter a valid Egyptian mobile phone number (e.g. 01012345678 or +201123456789).'),
            code='invalid_egyptian_phone'
        )
