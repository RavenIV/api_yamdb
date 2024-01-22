import uuid

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, permissions
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, DestroyModelMixin
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt import tokens

from reviews.models import Category, Genre, Title, Review
from .filters import TitleFilter
from .permissions import (IsAdminOrReadOnly, IsAdmin,
                          IsAuthorOrAdminOrReadOnly)
from .serializers import (CategorySerializer, GenreSerializer, TitleSerializer,
                          ReviewSerializer, CommentSerializer,
                          UserSerializer, UserMeSerializer,
                          RegisterCodObtainSerializer)
from api_yamdb.constants import YAMDB_EMAIL


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


class GenreViewSet(CategoryViewSet):
    """Вьюсет для получения списка, создания и удаления жанров."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(ModelViewSet):
    """Вьюсет для произведений."""
    queryset = Title.objects.all()
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TitleReadSerializer
        if self.action in ['create', 'partial_update']:
            return TitleCreateUpdateSerializer


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
            self.permission_classes = [IsAuthorOrAdminOrReadOnly,]
        elif self.request.method in ['POST']:
            self.permission_classes = [IsAuthorOrAdminOrReadOnly,]
        elif self.request.method in ['PATCH', 'DELETE']:
            if (self.request.user.is_authenticated
                    and self.request.user.role == 'admin'):
                self.permission_classes = [IsAdmin,]
            else:
                self.permission_classes = [
                    IsAuthorOrAdminOrReadOnly,
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
            self.permission_classes = [IsAuthorOrAdminOrReadOnly,]
        elif self.request.method in ['POST']:
            self.permission_classes = [IsAuthorOrAdminOrReadOnly,]
        elif self.request.method in ['PATCH', 'DELETE']:
            if (self.request.user.is_authenticated
                    and self.request.user.role == 'admin'):
                self.permission_classes = [IsAdmin,]
            else:
                self.permission_classes = [
                    IsAuthorOrAdminOrReadOnly,
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
    permission_classes = (IsAdmin,)

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=UserMeSerializer,
        url_path='me'
    )
    def user_info(self, request, pk=None):
        if request.method == 'PATCH':
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(self.get_serializer(request.user).data)


class RegisterCodObtainViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterCodObtainSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_mail(
            subject='YAmdb confirmation code',
            message=str(uuid.uuid4),
            from_email=YAMDB_EMAIL,
            recipient_list=[request.data['email']]
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def token_obtain(request):
    if 'username' not in request.data:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    username = request.data['username']
    user = User.objects.filter(username=username).first()

    if not user:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if str(user.confirmation_code) != request.data['confirmation_code']:
        raise ValidationError(
            {'confirmation_code': f'Неверный код подтверждения '
                                  f'{user.confirmation_code} != '
                                  f'{request.data["confirmation_code"]}'},
            code='invalid_confirmation_code',
        )

    user.last_login = timezone.now()
    user.save()
    return Response({
        'token': str(tokens.RefreshToken.for_user(user).access_token)})
