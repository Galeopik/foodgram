import django_filters

from recipe.models import Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )
    author = django_filters.NumberFilter(field_name='author')

    def filter_is_favorited(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset

        if value == 1:
            return queryset.filter(
                favorites__user=self.request.user
            )

        return queryset.exclude(
            favorites__user=self.request.user
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset

        if value == 1:
            return queryset.filter(
                is_in_shopping_cart__user=self.request.user
            )

        return queryset.exclude(
            is_in_shopping_cart__user=self.request.user
        )

    class Meta:
        model = Recipe
        fields = ('tags', 'is_favorited', 'is_in_shopping_cart', 'author')
