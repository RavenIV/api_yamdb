import re

from django.core.exceptions import ValidationError


def forbidden_usernames(value: str) -> None:
    """Валидатор username."""

    FORBIDDEN_USERNAMES = ('me',)

    if value in FORBIDDEN_USERNAMES:
        raise ValidationError(
            f'Нельзя использовать {value} как username')

    forbidden_symbols = re.sub(r'[\w.@+-]+', '', value)

    if forbidden_symbols:
        raise ValidationError(
            f'Нельзя использовать {forbidden_symbols} в username')
