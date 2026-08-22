from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Subscription, Tag, User)

from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeShopSerializer,
                          SubscriptionSerializer, TagSerializer)
from .utils import paginate_response


def delete_user_relation(model, user, **filters):
    relation = model.objects.filter(
        user=user,
        **filters
    )

    if not relation.exists():
        return False

    relation.delete()
    return True


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

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

        if not delete_user_relation(
            Favorite,
            request.user,
            recipe=recipe
        ):
            return Response(
                {'errors': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
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
        if ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Рецепт уже есть в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(
            user=request.user,
            recipe=recipe
        )

        serializer = RecipeShopSerializer(recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()

        if not delete_user_relation(
            ShoppingCart,
            request.user,
            recipe=recipe
        ):
            return Response(
                {'errors': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def dowload_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total=Sum('amount')
        )
        shopping_list = ['Список покупок', '']
        for ingredient in ingredients:
            shopping_list.append(
                f"{ingredient['ingredient__name']} — "
                f"{ingredient['total']} "
                f"{ingredient['ingredient__measurement_unit']}"
            )
        response = HttpResponse(
            '\n'.join(shopping_list),
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response


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

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        users = User.objects.filter(
            subscribers__user=request.user
        )
        recipes_limit = request.query_params.get('recipes_limit')

        return paginate_response(
            self,
            users,
            SubscriptionSerializer,
            recipes_limit=recipes_limit
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
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Subscription.objects.filter(
            user=request.user,
            author=user
        ).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Subscription.objects.create(
            user=request.user,
            author=user
        )
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                return Response(
                    {'recipes_limit': 'Должно быть целым числом.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if recipes_limit < 0:
                return Response(
                    {'recipes_limit': 'Не может быть отрицательным.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = SubscriptionSerializer(
            user,
            context={
                'request': request,
                'recipes_limit': recipes_limit,
            }
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        user = self.get_object()

        if not delete_user_relation(
            Subscription,
            request.user,
            author=user
        ):
            return Response(
                {'errors': 'Вы не были подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
