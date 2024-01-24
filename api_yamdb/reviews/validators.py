import re

from django.core.exceptions import ValidationError
from .constants import FORBIDDEN_USERNAMES


def forbidden_usernames(value: str) -> None:
    """Валидатор username."""
    if value in FORBIDDEN_USERNAMES:
        raise ValidationError(
            f'Нельзя использовать {value} как username')
    forbidden_symbols = ''.join(set(re.sub(r'[\w.@+-]+', '', value)))
    if forbidden_symbols:
        raise ValidationError(
            f'Нельзя использовать {forbidden_symbols} в username')
