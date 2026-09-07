from django.db.models import Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
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
    permission_classes = (MixedResourcePermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """Создаёт рецепт."""
        serializer = RecipeCreateUpdateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(
            author=request.user,
        )

        return Response(
            RecipeReadSerializer(
                recipe,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        """Обновляет рецепт."""
        instance = self.get_object()

        serializer = RecipeCreateUpdateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        return Response(
            RecipeReadSerializer(
                recipe,
                context={'request': request},
            ).data,
        )

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        try:
            recipe = super().get_object()
        except Http404:
            raise NotFound('Страница не найдена.')

        return Response({
            'short-link': request.build_absolute_uri(
                f'/s/{recipe.id}/'
            )
        })

    @staticmethod
    def create_user_relation(
        model,
        user,
        recipe,
        error_message
    ):
        _, created = model.objects.get_or_create(
            user=user,
            recipe=recipe
        )

        if not created:
            raise serializers.ValidationError(
                f'Рецепт: {recipe.name} {error_message}'
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

    @action(
        detail=True,
        methods=['post'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()

        self.create_user_relation(
            Favorite,
            request.user,
            recipe,
            'уже есть в избранном'
        )

        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        self.delete_user_relation(
            Favorite,
            request.user,
            pk
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            id=pk
        )

        self.create_user_relation(
            ShoppingCart,
            request.user,
            recipe,
            'уже есть в корзине'
        )

        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        self.delete_user_relation(
            ShoppingCart,
            request.user,
            pk
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=request.user
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
        page = self.paginate_queryset(
            User.objects.filter(
                subscriptions__user=request.user
            )
        )

        return self.get_paginated_response(
            UserSubscriptionSerializer(
                page,
                many=True,
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get(
                        'recipes_limit'
                    )
                }
            ).data
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = get_object_or_404(
            User,
            id=id
        )

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
                'Вы уже подписаны на этого пользователя.'
            )

        return Response(
            UserSubscriptionSerializer(
                user,
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get(
                        'recipes_limit'
                    ),
                }
            ).data,
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
