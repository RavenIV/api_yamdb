import uuid

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
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
                          UserSerializer, UserInfoSerializer,
                          RegisterSerializer, TokenObtainSerializer)


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
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).order_by('name')
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TitleReadSerializer
        return TitleCreateUpdateSerializer


class BaseContentViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAuthorOrAdminOrReadOnly,)


class ReviewViewSet(BaseContentViewSet):
    serializer_class = ReviewSerializer

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(BaseContentViewSet):
    serializer_class = CommentSerializer

    def get_review(self):
        return get_object_or_404(Review, id=self.kwargs.get('review_id'),
                                 title__id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_review().comments.all()

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
        serializer_class=UserInfoSerializer,
        url_path='me'
    )
    def user_info(self, request, pk=None):
        if request.method == 'PATCH':
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(self.get_serializer(request.user).data)


@api_view(['POST'])
def register_code_obtain(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    user.confirmation_code = str(uuid.uuid4())
    user.save()
    send_mail(
        subject='YAmdb confirmation code',
        message=user.confirmation_code,
        from_email=YAMDB_EMAIL,
        recipient_list=[serializer.data['email']]
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def token_obtain(request):
    serializer = TokenObtainSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.data['username']
    user = get_object_or_404(User, username=username)
    check_code = bool(
        user.confirmation_code == serializer.data['confirmation_code']
    )
    user.confirmation_code = str(uuid.uuid4())
    user.save()
    if check_code:
        return Response(
            {'token': str(tokens.RefreshToken.for_user(user).access_token)}
        )
    raise ValidationError(
        {'confirmation_code': 'Неверный код подтверждения'},
        code='invalid_confirmation_code',
    )
