from datetime import date

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import (MinValueValidator, MaxValueValidator,
                                    RegexValidator, EmailValidator)

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(unique=True, max_length=50)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(unique=True, max_length=50)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(max_length=256)
    year = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(date.today().year)]
    )
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=False,
        null=True
    )
    genre = models.ManyToManyField(Genre)

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        default_related_name = 'titles'

    def __str__(self):
        return self.name


class Review(models.Model):
    text = models.TextField()
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name='review'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='review'
    )
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


class Comment(models.Model):
    text = models.TextField()
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='comment'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comment'
    )
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

# class CustomUser(AbstractUser):
# ROLE_CHOICES = [
#     ('user', 'user'),
#     ('moderator', 'moderator'),
#     ('admin', 'admin'),
# ]
#
# username_validator = RegexValidator(
#     r'^[\w.@+-]+\Z',
#     'Введите корректное имя пользователя. '
#     'Это значение может содержать только буквы,'
#     'цифры и символы @/./+/-/_ .'
# )
#
# username = models.CharField(
#     max_length=150,
#     unique=True,
#     validators=[username_validator],
#     error_messages={'unique': 'Пользователь с таким именем'
#                               'уже существует.', },
# )
# email = models.EmailField(
#     unique=True,
#     validators=[EmailValidator(message='Введите корректный адрес'
#                                        'электронной почты.')],
#     error_messages={
#         'unique': 'Пользователь с таким адресом'
#                   'электронной почты уже существует.',
#     },
# )
# first_name = models.CharField(max_length=150)
# last_name = models.CharField(max_length=150)
# bio = models.TextField(blank=True)
# role = models.CharField(choices=ROLE_CHOICES, default='user')
#
# class Meta:
#     verbose_name = 'Пользователь'
#     verbose_name_plural = 'Пользователи'
