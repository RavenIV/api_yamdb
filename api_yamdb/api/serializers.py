from datetime import date

from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from reviews.models import Category, Genre, Title, Review, Comment
from api_yamdb.constants import (
    USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH)
from api_yamdb.validators import forbidden_usernames


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

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        read_only_fields = ('id', 'pub_date')

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


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH, required=True,
        validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role')

    def validate_username(self, value):
        if forbidden_usernames(value) is None:
            return value


class UserMeSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)


class RegisterCodObtainSerializer(serializers.Serializer):
    """
    Регистрация по username и email и получение confirmation_code на почту.
    """

    email = serializers.EmailField(
        max_length=EMAIL_MAX_LENGTH, required=True, )

    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH, required=True)

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']

        user_email_or_username_list = User.objects.filter(
            Q(username=username) | Q(email=email))

        if not user_email_or_username_list:
            return User.objects.create(
                username=username, email=email)

        user_email_username = user_email_or_username_list.filter(
            username=username, email=email).first()

        if user_email_username:
            return user_email_username

        user_username = user_email_or_username_list.filter(
            username=username).first()
        user_email = user_email_or_username_list.filter(email=email).first()

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

    def validate_username(self, value):
        if forbidden_usernames(value) is None:
            return value
