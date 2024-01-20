from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, DestroyModelMixin
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from reviews.models import Category, Genre, Title, Review
from .filters import TitleFilter
from .permissions import (IsAdminOrReadOnly, IsAdmin, IsAdminOrSuperuser,
                          IsAuthorNotUserOrReadOnlyPermission)
from .serializers import (CategorySerializer, GenreSerializer, TitleSerializer,
                          ReviewSerializer, CommentSerializer,
                          UserSerializer, UserMeSerializer,
                          CustomTokenObtainSerializer, RegisterSerializer)


class CreateListDestroyViewSet(CreateModelMixin,
                               ListModelMixin,
                               DestroyModelMixin,
                               GenericViewSet):
    """Вьюсет для получения списка, создания и удаления объектов."""


class CategoryViewSet(CreateListDestroyViewSet):
    """Вьюсет для получения списка, создания и удаления категорий."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class GenreViewSet(CreateListDestroyViewSet):
    """Вьюсет для получения списка, создания и удаления жанров."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class TitleViewSet(ModelViewSet):
    """Вьюсет для произведений."""
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TitleFilter


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_title(self):
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(Title, id=title_id)

    def get_queryset(self):
        return self.get_title().review.all()

    def perform_create(self, serializer):
        title = self.get_title()
        author = self.request.user

        if Review.objects.filter(author=author, title=title).exists():
            raise ValidationError(
                'Отзыв от данного автора на это произведение уже существует')

        serializer.save(author=author, title=title)

    def get_permissions(self):
        if self.request.method in ['GET']:
            self.permission_classes = [IsAuthorNotUserOrReadOnlyPermission,]
        elif self.request.method in ['POST']:
            self.permission_classes = [IsAuthorNotUserOrReadOnlyPermission,]
        elif self.request.method in ['PATCH', 'DELETE']:
            if (self.request.user.is_authenticated
                    and self.request.user.role == 'admin'):
                self.permission_classes = [IsAdmin,]
            else:
                self.permission_classes = [
                    IsAuthorNotUserOrReadOnlyPermission,
                ]
        return super().get_permissions()


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_review(self):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        title = get_object_or_404(Title, id=title_id)
        return get_object_or_404(Review, id=review_id, title=title)

    def get_queryset(self):
        return self.get_review().comment.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())

    def get_permissions(self):
        if self.request.method in ['GET']:
            self.permission_classes = [IsAuthorNotUserOrReadOnlyPermission,]
        elif self.request.method in ['POST']:
            self.permission_classes = [IsAuthorNotUserOrReadOnlyPermission,]
        elif self.request.method in ['PATCH', 'DELETE']:
            if (self.request.user.is_authenticated
                    and self.request.user.role == 'admin'):
                self.permission_classes = [IsAdmin,]
            else:
                self.permission_classes = [
                    IsAuthorNotUserOrReadOnlyPermission,
                ]
        return super().get_permissions()


User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrSuperuser,)

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=UserMeSerializer
    )
    def me(self, request, pk=None):
        if request.method == 'PATCH':
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(self.get_serializer(request.user).data)


class RegisterModelViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenObtainView(TokenObtainPairView):
    serializer_class = CustomTokenObtainSerializer
