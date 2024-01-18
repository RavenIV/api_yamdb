from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import CategoryViewSet, GenreViewSet


app_name = 'api'

router_v1 = SimpleRouter()
router_v1.register(r'categories', CategoryViewSet, basename='category')
router_v1.register(r'genres', GenreViewSet, basename='genre')


urlpatterns = [
    path('v1/', include(router_v1.urls)),
]
