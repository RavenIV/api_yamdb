from datetime import date

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from rest_framework import serializers

from api_yamdb.validators import forbidden_usernames
from reviews.constants import (
    USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH, MIN_RATING, MAX_RATING
)
from reviews.models import Category, Genre, Title, Review, Comment


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )
        read_only_fields = ('name', 'year', 'description')


class TitleCreateUpdateSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        many=True, queryset=Genre.objects.all(), slug_field='slug'
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'description', 'genre', 'category'
        )

    def validate_year(self, year):
        current_year = date.today().year
        if year > current_year:
            raise serializers.ValidationError(
                f'Год выпуска {year} больше текущего: {current_year}.'
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

    def validate(self, attrs):
        author = self.context['request'].user
        title_id = self.context['view'].kwargs.get('title_id')
        if self.instance is None:
            if Review.objects.filter(author=author,
                                     title__id=title_id).exists():
                raise serializers.ValidationError('Отзыв от данного автора на '
                                                  'это произведение уже '
                                                  'существует')
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )

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
