import re

from django.core.exceptions import ValidationError
from .constants import FORBIDDEN_USERNAMES


def forbidden_usernames(value: str):
    """Валидатор username."""
    if value in FORBIDDEN_USERNAMES:
        raise ValidationError(
            f'Нельзя использовать {value} как username')
    forbidden_symbols = re.sub(r'[\w.@+-]+', '', value)
    if forbidden_symbols:
        raise ValidationError(
            f'Нельзя использовать {"".join(set(forbidden_symbols))} '
            f'в username'
        )
    return value
