from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, EmailValidator
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'user'),
        ('moderator', 'moderator'),
        ('admin', 'admin'),
    ]

    username_validator = RegexValidator(
        r'^[\w.@+-]+\Z',
        'Введите корректное имя пользователя. '
        'Это значение может содержать только буквы,'
        'цифры и символы @/./+/-/_ .'
    )

    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.', },
    )
    email = models.EmailField(
        'Адресс электронной почты',
        unique=True,
        validators=[EmailValidator(
            message='Введите корректный адрес электронной почты.')],
        error_messages={
            'unique': 'Пользователь с таким адресом'
                      'электронной почты уже существует.',
        },
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    bio = models.TextField('О себе', blank=True)
    role = models.CharField(
        'Тип пользователя', max_length=16,
        choices=ROLE_CHOICES, default='user')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
