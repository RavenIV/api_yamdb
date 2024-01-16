from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, DestroyModelMixin
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import (
    GenericViewSet,
)

from reviews.models import Category, Genre
from .serializers import CategorySerializer, GenreSerializer


class CreateListDestroyViewSet(CreateModelMixin,
                               ListModelMixin,
                               DestroyModelMixin,
                               GenericViewSet):
    """Вьюсет для получения списка, создания и удаления объектов."""


class CategoryViewSet(CreateListDestroyViewSet):
    """Вьюсет для получения списка, создания и удаления категорий."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = PageNumberPagination
    lookup_field = 'slug'


class GenreViewSet(CreateListDestroyViewSet):
    """Вьюсет для получения списка, создания и удаления жанров."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'
