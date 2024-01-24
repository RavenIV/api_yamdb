from django.db import models


class Role(models.TextChoices):
    """Пользовательские роли."""

    USER = 'user', 'user'
    MODERATOR = 'moderator', 'moderator'
    ADMIN = 'admin', 'admin'


MIN_RATING = 1
MAX_RATING = 10
EMAIL_MAX_LENGTH = 254
USERNAME_MAX_LENGTH = 150
FIRST_NAME_MAX_LENGTH = 150
LAST_NAME_MAX_LENGTH = 150
FORBIDDEN_USERNAMES = ('me',)