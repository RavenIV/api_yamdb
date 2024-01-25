from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet, GenreViewSet, TitleViewSet,
    ReviewViewSet, CommentViewSet, UserViewSet,
    token_obtain, register_code_obtain
)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register(r'users', UserViewSet, basename='user')
router_v1.register(r'categories', CategoryViewSet, basename='category')
router_v1.register(r'genres', GenreViewSet, basename='genre')
router_v1.register(r'titles', TitleViewSet, basename='title')
router_v1.register(r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet,
                   basename='reviews')
router_v1.register(r'titles/(?P<title_id>\d+)/reviews/'
                   r'(?P<review_id>\d+)/comments',
                   CommentViewSet, basename='comments')

auth = [
    path('token/', token_obtain, name='token_obtain'),
    path('signup/', register_code_obtain, name='signup'),
]

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/auth/', include(auth)),
]
