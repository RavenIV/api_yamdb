from datetime import date
import uuid

from django.db import models
from django.core.validators import (
    MinValueValidator, MaxValueValidator, EmailValidator
)
from django.contrib.auth.models import AbstractUser

from api_yamdb.constants import Role, USERNAME_MAX_LENGTH
from api_yamdb.validators import forbidden_usernames


class User(AbstractUser):
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
    username = models.CharField(
        'Имя пользователя',
        unique=True, max_length=USERNAME_MAX_LENGTH,
        validators=[forbidden_usernames],
    )
    bio = models.TextField('О себе', blank=True)
    role = models.CharField(
        'Тип пользователя',
        max_length=max(len(role[0]) for role in Role.choices),
        choices=Role.choices, default=Role.USER
    )
    confirmation_code = models.UUIDField(
        primary_key=False, default=uuid.uuid4, editable=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id', 'date_joined')

    @property
    def is_moderator(self):
        return self.role == Role.MODERATOR

    @property
    def is_admin(self):
        return self.role == Role.ADMIN or self.is_staff

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


class Base(models.Model):
    name = models.CharField('Название', max_length=256)
    slug = models.SlugField('Слаг', unique=True, max_length=50)

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return (
            f'{self.name=:20}, '
            f'{self.slug=}'
        )


class Category(Base):

    class Meta(Base.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(Base):

    class Meta(Base.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


def current_year():
    return date.today().year


class Title(models.Model):
    name = models.CharField('Название', max_length=256)
    year = models.IntegerField(
        'Год создания',
        validators=[MaxValueValidator(current_year),]
    )
    description = models.TextField('Описание', blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        verbose_name='Категория'
    )
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle',
        verbose_name='Жанр'
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        default_related_name = 'titles'
        ordering = ('name',)

    def __str__(self):
        return (
            f'{self.name=:.20}, '
            f'{self.year=}, '
            f'{self.description=:.20}, '
            f'{self.category=}, '
            f'{self.genre=}'
        )


class Review(models.Model):
    text = models.TextField()
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        default_related_name = 'review'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'title'], name='unique_review'
            )
        ]
        ordering = ('pub_date',)

    def __str__(self):
        return (
            f'{self.text=:.20}, '
            f'{self.title=}, '
            f'{self.author=}, '
            f'{self.score=}, '
            f'{self.pub_date=}'
        )


class Comment(models.Model):
    text = models.TextField()
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comment'
        ordering = ('pub_date',)

    def __str__(self):
        return (
            f'{self.text=:.20}, '
            f'{self.review=:.20}, '
            f'{self.author=}, '
            f'{self.pub_date=}'
        )


class GenreTitle(models.Model):
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
