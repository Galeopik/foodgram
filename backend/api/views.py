from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from recipe.models import Recipe, Tag, User
from .serializers import RecipeSerializer, TagSerializer, UserSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@api_view(['GET'])
def tag(request, pk=None):
    if pk is not None:
        tag_obj = get_object_or_404(Tag, pk=pk)
        serializer = TagSerializer(tag_obj)
        return Response(serializer.data)

    tags = Tag.objects.all()
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)
