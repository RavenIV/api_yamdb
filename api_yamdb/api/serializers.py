from rest_framework import serializers
from django.db.models import Avg


from reviews.models import Category, Genre, Title


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