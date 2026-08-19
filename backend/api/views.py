from rest_framework import viewsets, status, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import Http404
from rest_framework.exceptions import NotFound

from recipe.models import Recipe, Tag, Ingredient, Favorite
from .serializers import (
    AvatarSerializer, RecipeSerializer, TagSerializer, IngredientSerializer
)
from .permissions import IsAuthorOrReadOnly


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthorOrReadOnly,)

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise NotFound('Рецепт не найден.')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()

        return Response({
            'short-link': request.build_absolute_uri(
                f'/s/{recipe.short_link}/'
            )
        })

    @action(
        detail=True,
        methods=['post'],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()

        if Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в избранное.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Favorite.objects.create(
            user=request.user,
            recipe=recipe
        )

        return Response(
            {'is_favorited': True},
            status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()

        Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(DjoserUserViewSet):
    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [AllowAny()]

        return super().get_permissions()

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        if request.method == 'PUT':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        elif request.method == 'DELETE':
            request.user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def tag(request, pk=None):
    if pk is not None:
        tag_obj = get_object_or_404(Tag, pk=pk)
        serializer = TagSerializer(tag_obj)
        return Response(serializer.data)

    tags = Tag.objects.all()
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def ingredient(request, pk=None):
    if pk is not None:
        ingredient_obj = get_object_or_404(Ingredient, pk=pk)
        serializer = IngredientSerializer(ingredient_obj)
        return Response(serializer.data)

    ingredients = Ingredient.objects.all()
    name = request.query_params.get('name')
    if name:
        ingredients = ingredients.filter(name__icontains=name)

    serializer = IngredientSerializer(ingredients, many=True)
    return Response(serializer.data)
