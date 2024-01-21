from datetime import date
import uuid

from django.db import models
from django.core.validators import (
    MinValueValidator, MaxValueValidator, EmailValidator
)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from api_yamdb.constants import MIN_RATING, MAX_RATING


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'user'),
        ('moderator', 'moderator'),
        ('admin', 'admin'),
    ]
    email = models.EmailField(
        'Адресс электронной почты',
        unique=True,
        validators=[EmailValidator(
            message='Введите корректный адрес электронной почты.')
        ],
        error_messages={
            'unique': 'Пользователь с таким адресом'
                      'электронной почты уже существует.',
        },
    )
    bio = models.TextField('О себе', blank=True)
    role = models.CharField(
        'Тип пользователя', max_length=16,
        choices=ROLE_CHOICES, default='user'
    )
    confirmation_code = models.UUIDField(
        primary_key=False, default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('date_joined',)

    def __str__(self):
        return (
            f'{self.username=:.20}, '
            f'{self.email=}, '
            f'{self.role=}, '
            f'{self.first_name=:.20}, '
            f'{self.last_name=:.20}, '
            f'{self.is_staff=}, '
            f'{self.is_active=}, '
            f'{self.bio=:.20}'
        )


User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(unique=True, max_length=50)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    def __str__(self):
        return (
            f'{self.name=:20}, '
            f'{self.slug=}'
        )


class Genre(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(unique=True, max_length=50)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ('name',)

    def __str__(self):
        return (
            f'{self.name=:20}, '
            f'{self.slug=}'
        )


class Title(models.Model):
    name = models.CharField(max_length=256)
    year = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(date.today().year)]
    )
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, blank=False, null=True
    )
    genre = models.ManyToManyField(Genre, through='GenreTitle')

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        default_related_name = 'titles'
        ordering = ('year',)

    def __str__(self):
        return (
            f'{self.name=:.20}, '
            f'{self.year=}, '
            f'{self.description=:.20}, '
            f'{self.category=}, '
            f'{self.genre=}'
        )


class Post(models.Model):
    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор')
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True,
                                    verbose_name='Дата публикации')

    class Meta:
        abstract = True
        ordering = ('pub_date',)

    def __str__(self):
        return (
            f'{self.text=:.20}, '
            f'{self.author=}, '
            f'{self.pub_date=}'
        )


class Review(Post):
    title = models.ForeignKey(Title, on_delete=models.CASCADE,
                              verbose_name='Произведение')
    score = models.IntegerField(
        validators=[MinValueValidator(MIN_RATING), MaxValueValidator(MAX_RATING)],
        verbose_name='Оценка'
    )

    class Meta(Post.Meta):
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        default_related_name = 'review'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'title'], name='unique_review'
            )
        ]

    def __str__(self):
        return (
            super().__str__() +
            f', {self.title=}, '
            f'{self.score=}'
        )


class Comment(Post):
    review = models.ForeignKey(Review, on_delete=models.CASCADE,
                               verbose_name='Отзыв')

    class Meta(Post.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comment'

    def __str__(self):
        return (
            super().__str__() +
            f', {self.review=:.20}'
        )


class GenreTitle(models.Model):
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
