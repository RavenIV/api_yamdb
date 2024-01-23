import uuid

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, permissions
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, DestroyModelMixin
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt import tokens

from api_yamdb.settings import YAMDB_EMAIL
from reviews.models import Category, Genre, Title, Review
from .filters import TitleFilter
from .permissions import (IsAdminOrReadOnly, IsAdmin,
                          IsAuthorOrAdminOrReadOnly)
from .serializers import (CategorySerializer, GenreSerializer,
                          TitleReadSerializer, TitleCreateUpdateSerializer,
                          ReviewSerializer, CommentSerializer,
                          UserSerializer, UserMeSerializer,
                          RegisterCodObtainSerializer)


class BaseClassificationViewSet(CreateModelMixin,
                                ListModelMixin,
                                DestroyModelMixin,
                                GenericViewSet):
    lookup_field = 'slug'
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class CategoryViewSet(BaseClassificationViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(BaseClassificationViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(ModelViewSet):
    """Вьюсет для произведений."""
    queryset = Title.objects.annotate(
        rating=Avg('review__score')
    ).order_by('name')
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TitleReadSerializer
        if self.action in ['create', 'partial_update']:
            return TitleCreateUpdateSerializer


class BaseContentViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAuthorOrAdminOrReadOnly,)


class ReviewViewSet(BaseContentViewSet):
    serializer_class = ReviewSerializer

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_title().review.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(BaseContentViewSet):
    serializer_class = CommentSerializer

    def get_review(self):
        return get_object_or_404(Review, id=self.kwargs.get('review_id'),
                                 title__id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_review().comment.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())


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
