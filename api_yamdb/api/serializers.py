from datetime import date

from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.validators import (RegexValidator, MinValueValidator,
                                    MaxValueValidator)
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.validators import UniqueValidator

from reviews.models import Category, Genre, Title, Review, Comment
from api_yamdb.constants import MIN_RATING, MAX_RATING


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class CustomSlugRelatedField(serializers.SlugRelatedField):

    def to_representation(self, obj):
        return {
            "name": obj.name,
            "slug": obj.slug
        }


class TitleSerializer(serializers.ModelSerializer):
    genre = CustomSlugRelatedField(
        many=True, queryset=Genre.objects.all(), slug_field='slug'
    )
    category = CustomSlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )
        read_only_fields = ('id',)

    def get_rating(self, obj):
        avg_score = Review.objects.filter(title=obj).aggregate(
            Avg('score'))['score__avg']
        return round(avg_score) if avg_score is not None else None

    def validate_year(self, year):
        if year > date.today().year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего.'
            )
        return year


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    score = serializers.IntegerField(
        validators=[
            MinValueValidator(MIN_RATING),
            MaxValueValidator(MAX_RATING)
        ]
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def create(self, validated_data):
        author = validated_data.get('author')
        title = validated_data.get('title')
        if (author.is_authenticated
                and Review.objects.filter(author=author,
                                          title=title).exists()):
            raise serializers.ValidationError('Отзыв от данного автора на это '
                                              'произведение уже существует')
        return super().create(validated_data)

    # def get_serializer(self, *args, **kwargs):
    #     serializer_class = self.get_serializer_class()
    #     kwargs['context'] = self.get_serializer_context()
    #     kwargs['context'].update({'title': self.get_title()})
    #     return serializer_class(*args, **kwargs)

    # def get_serializer(self, *args, **kwargs):
    #     serializer_class = self.get_serializer_class()
    #     kwargs['context'] = self.get_serializer_context()
    #     kwargs['context'].update({'title': TitleSerializer(self.get_object().title).data})
    #     # kwargs['data']['title'] = TitleSerializer(self.get_object().title).data
    #     return serializer_class(*args, **kwargs)

    # def validate(self, attrs):
    #     author = attrs.get('author')
    #     title_id = self.context.get('title_id')
    #     if Review.objects.filter(author=author, title__id=title_id).exists():
    #         raise serializers.ValidationError('Отзыв от данного автора на это произведение уже существует')
    #     return attrs

    # def validate(self, attrs):
    #     author = attrs.get('author')
    #     title = attrs.get('title')
    #     if author.is_authenticated and Review.objects.filter(author=author,
    #                                                          title=title).exists():
    #         raise serializers.ValidationError(
    #             'Отзыв от данного автора на это произведение уже существует')
    #     return attrs


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        # read_only_fields = ('id', 'pub_date')


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=254, required=True, validators=[
            UniqueValidator(queryset=User.objects.all())])

    username = serializers.CharField(
        max_length=150, required=True,
        validators=[UniqueValidator(queryset=User.objects.all()),
                    RegexValidator(
                        regex=r"^[\w.@+-]+$",
                        message='Имя пользователя может содержать '
                        'только буквы, цифры и следующие символы: '
                        '@/./+/-/_',)])

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role')

    def validate(self, attrs):
        data = super().validate(attrs)
        if 'username' in data:
            if data['username'].lower() == 'me':
                raise serializers.ValidationError(
                    'Нельзя использовать me/Me/mE/ME как username')
        return data


class UserMeSerializer(UserSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role')
        read_only_fields = ('role',)


class RegisterSerializer(UserSerializer):
    """
    Регистрация по username и email с получением confirmation_code на почту.
    """

    email = serializers.EmailField(max_length=254, required=True)

    username = serializers.CharField(
        max_length=150, required=True,
        validators=[RegexValidator(
                    regex=r"^[\w.@+-]+$",
                    message='Имя пользователя может содержать '
                    'только буквы, цифры и следующие символы: '
                    '@/./+/-/_',)])

    class Meta:
        model = User
        fields = ('username', 'email')

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']

        user_email_username = User.objects.filter(
            username=username, email=email).first()

        if user_email_username:
            return user_email_username

        user_username = User.objects.filter(username=username).first()
        user_email = User.objects.filter(email=email).first()

        if user_username:
            if user_username and user_email:
                raise serializers.ValidationError(
                    {'username': [f'username {user_username} уже занят'],
                     'email': [f'email {user_email} уже занят']},
                    code='duplicate_username_email')
            raise serializers.ValidationError(
                {'username': [f'username {user_username} уже занят']},
                code='duplicate_username')

        if user_email:
            raise serializers.ValidationError(
                {'email': [f'email {user_email} уже занят']},
                code='duplicate_email'
            )

        user_new = User.objects.create(username=username, email=email)

        send_mail(
            subject='YAmdb confirmation code',
            message=str(user_new.confirmation_code),
            from_email='yamdb@ya.ru',
            recipient_list=[email]
        )

        return user_new


class CustomTokenObtainSerializer(TokenObtainSerializer):
    """Получение токена по username и confirmation_code."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields['confirmation_code'] = serializers.CharField()
        self.fields.pop('password', None)

    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        username = attrs[self.username_field]
        user = User.objects.filter(username=username).first()

        if not user:
            raise NotFound(
                {'username': f'Пользователь с username'
                 f'{username} не существует'},
                code='user_not_found',
            )

        if not user.is_active:
            raise ValidationError(
                {'is_active': f'Аккаунт {username} неактивен'},
                code='inactive_account',
            )

        if str(user.confirmation_code) != attrs['confirmation_code']:
            raise ValidationError(
                {'confirmation_code': f'Неверный код подтверждения '
                                      f'{user.confirmation_code} != '
                                      f'{attrs["confirmation_code"]}'},
                code='invalid_confirmation_code',
            )

        self.user = user

        user.last_login = timezone.now()
        user.save()
        return {'token': str(self.get_token(self.user).access_token)}
