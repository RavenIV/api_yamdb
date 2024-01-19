from datetime import date

from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.models import Category, Genre, Title, Review, Comment


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
        return Review.objects.filter(title=obj).aggregate(
            Avg('score'))['score__avg']

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

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        read_only_fields = ('id', 'pub_date')
        validators = [
            UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=('author', 'title'),
                message='Вы уже оставили отзыв на это произведение.'
            )
        ]

    def validate_score(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError('Оценка должна быть в диапазоне '
                                              'от 1 до 10.')
        return value


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('id', 'pub_date')


User = get_user_model()


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

        # if str(user.confirmation_code) != attrs['confirmation_code']:
        #     raise ValidationError(
        #         {'confirmation_code': f'Неверный код подтверждения '
        #                               f'{user.confirmation_code} != '
        #                               f'{attrs["confirmation_code"]}'},
        #         code='invalid_confirmation_code',
        #     )

        self.user = user

        user.last_login = timezone.now()
        user.save()
        return {'token': str(self.get_token(self.user).access_token)}


class RegisterSerializer(serializers.ModelSerializer):
    """
    Регистрация по username и email с
    получением confirmation_code на почту.
    """

    email = serializers.EmailField(
        max_length=254,
        required=True,
    )

    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message='Имя пользователя может содержать '
                'только буквы, цифры и следующие символы: '
                '@/./+/-/_',
            )
        ],
    )

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
                    {'username': ['Данный username уже занят'],
                     'email': ['Данный email уже занят']},
                    code='duplicate_email')
            raise serializers.ValidationError(
                {'username': ['Данный username уже занят']},
                code='duplicate_username')

        if user_email:
            raise serializers.ValidationError(
                {'email': ['Данный email уже занят']},
                code='duplicate_email')

        user_new = User.objects.create(username=username, email=email)
        send_mail(
            subject='YAmdb confirmation code',
            message=str(user_new.confirmation_code),
            from_email='yamdb@ya.ru',
            recipient_list=[email]
        )
        return user_new

    def validate(self, attrs):
        data = super().validate(attrs)
        if 'username' in data:
            if data['username'].lower() == 'me':
                raise serializers.ValidationError(
                    'Нельзя использовать me/Me/mE/ME как username')
        return data
