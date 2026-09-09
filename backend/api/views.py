from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import MixedResourcePermission
from api.serializers import (AvatarSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeReadSerializer, RecipeShortSerializer,
                             TagSerializer, UserSubscriptionSerializer)
from api.utils import create_shopping_list
from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Subscription, Tag, User)


class RecipeViewSet(viewsets.ModelViewSet):
    """Обрабатывает рецепты и связанные с ними действия пользователя."""
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        MixedResourcePermission
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise NotFound('Страница не найдена.')

        return Response({
            'short-link': request.build_absolute_uri(
                reverse('short-link', kwargs={'recipe_id': pk})
            )
        })

    @staticmethod
    def create_user_relation(
        model,
        user,
        pk
    ):
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model.objects.get_or_create(
            user=user,
            recipe=recipe
        )

        if not created:
            raise serializers.ValidationError(
                f'{model._meta.verbose_name}'
                f'Рецепт: {recipe.name}'
            )

        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def delete_user_relation(
        model,
        user,
        pk
    ):
        get_object_or_404(
            model,
            user=user,
            recipe_id=pk
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self.create_user_relation(
            Favorite,
            request.user,
            pk
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.delete_user_relation(
            Favorite,
            request.user,
            pk
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        return self.create_user_relation(
            ShoppingCart,
            request.user,
            pk
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.delete_user_relation(
            ShoppingCart,
            request.user,
            pk
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart_set__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total=Sum('amount')
        ).order_by(
            'ingredient__name'
        )

        return FileResponse(
            create_shopping_list(ingredients),
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain'
        )


class UserViewSet(DjoserUserViewSet):
    """Обрабатывает пользователей и связанные с ними действия."""
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipes_limit'] = self.request.query_params.get(
            'recipes_limit'
        )
        return context

    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        return super().me(request)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        if request.method == 'DELETE':
            request.user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = AvatarSerializer(
            request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        return self.get_paginated_response(
            UserSubscriptionSerializer(
                self.paginate_queryset(
                    User.objects.filter(
                        subscriptions_received__user=request.user
                    )
                ),
                many=True,
                context=self.get_serializer_context()).data
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = self.get_object()
        if request.user == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )

        _, created = Subscription.objects.get_or_create(
            user=request.user,
            author=user
        )

        if not created:
            raise serializers.ValidationError(
                f'Вы уже подписаны на пользователя {user.username}.'
            )

        return Response(
            UserSubscriptionSerializer(
                user,
                context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        get_object_or_404(
            Subscription,
            user=request.user,
            author_id=id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
