from datetime import date
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator, MaxValueValidator, EmailValidator
)
from django.db import models
from django.db.models import Avg

from api_yamdb.constants import Role, USERNAME_MAX_LENGTH, MIN_RATING, MAX_RATING
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
    genre = models.ManyToManyField(Genre, verbose_name='Жанр')
    rating = models.IntegerField('Рейтинг', blank=True, null=True)

    def update_rating(self):
        avg_score = self.review.aggregate(Avg('score'))['score__avg']
        self.rating = round(avg_score) if avg_score is not None else None
        self.save()

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
        validators=[
            MinValueValidator(MIN_RATING), MaxValueValidator(MAX_RATING)
        ],
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.title.update_rating()

    def delete(self, *args, **kwargs):
        title = self.title
        super().delete(*args, **kwargs)
        title.update_rating()

    def __str__(self):
        return (
            f'{super().__str__()}, '
            f'{self.title=}, '
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
            f'{super().__str__()}, '
            f'{self.review=:.20}'
        )
