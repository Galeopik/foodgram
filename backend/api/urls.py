from rest_framework import routers
from django.urls import include, path

from .views import RecipeViewSet, UserViewSet, tag

router_v1 = routers.DefaultRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('users', UserViewSet, basename='users')

tag_urls = [
    path('tags/', tag, name='tag'),
    path('tags/<int:pk>/', tag, name='tag-detail'),
]

urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include(tag_urls)),
]
