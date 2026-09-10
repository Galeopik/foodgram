from django_filters import rest_framework as filters

from recipe.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """Фильтрация продуктов."""
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтрация рецептов."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )
    author = filters.NumberFilter(field_name='author')

    def filter_is_favorited(self, recipes, name, value):
        if not self.request.user.is_authenticated:
            return recipes

        if value == 1:
            return recipes.filter(
                favorites__user=self.request.user
            )

        return recipes.exclude(
            favorites__user=self.request.user
        )

    def filter_is_in_shopping_cart(self, recipes, name, value):
        if not self.request.user.is_authenticated:
            return recipes

        if value == 1:
            return recipes.filter(
                shoppingcarts__user=self.request.user
            )

        return recipes.exclude(
            shoppingcarts__user=self.request.user
        )

    class Meta:
        model = Recipe
        fields = ('tags', 'is_favorited', 'is_in_shopping_cart', 'author')
