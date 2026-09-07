from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, Tag, User)


class IngredientUsedFilter(admin.SimpleListFilter):
    title = 'Есть в рецептах'
    parameter_name = 'used'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть в рецептах'),
            ('no', 'Нет в рецептах'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes_count__gt=0)

        if self.value() == 'no':
            return queryset.filter(recipes_count=0)

        return queryset


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Настройки отображения пользователей в админке."""
    list_display = (
        'id',
        'username',
        'get_full_name',
        'email',
        'get_avatar',
        'get_recipe_count',
        'get_subscribers_count',
        'get_subscriptions_count',
    )
    search_fields = ('username', 'email')
    list_filter = (
        'recipes',
        'subscribers',
        'subscriptions'
    )

    @admin.display(description='ФИО')
    def get_full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def get_avatar(self, user):
        if not user.avatar:
            return 'Нет аватарки'
        return f'<img src="{user.avatar.url}" width="50" height="50">'

    @admin.display(description='Число рецептов')
    def get_recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписок')
    def get_subscribers_count(self, user):
        return user.subscribers.count()

    @admin.display(description='Подписчиков')
    def get_subscriptions_count(self, user):
        return user.subscriptions.count()



@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    search_fields = (
        'name',
        'author__username',
        'author__email',
        'tags__name',
        'ingredients__name'
    )
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'get_favorites_count',
        'ingredients__name',
        'tags__name',
        'get_image'
    )
    list_filter = ('tags', 'author')

    @admin.display(description='В избранном')
    def get_favorites_count(self, recipe):
        return recipe.favorite.count()

    @admin.display(description='Изображение')
    @mark_safe
    def get_image(self, recipe):
        if not recipe.image:
            return 'Нет изображения'
        return f'<img src="{recipe.image.url}" width="50" height="50">'


@admin.register(Ingredient)
class IngredienteAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = (
        'id',
        'name',
        'measurement_unit',
        'get_recipes_count'
    )
    list_filter = ('measurement_unit', IngredientUsedFilter)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_count=Count('recipe_ingredients')
        )

    @admin.display(description='Число рецептов')
    def get_recipes_count(self, ingredients):
        return ingredients.recipes_count


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        'get_recipes_count'
    )
    search_fields = ('name', 'slug')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_count=Count('Tag')
        )

    @admin.display(description='Количество рецептов')
    def get_recipes_count(self, tag):
        return tag.recipes_count


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    search_fields = ('user',)
    list_display = ('user_name', 'recipe_name')

    @admin.display(description='Автор')
    def user_name(self, favorite):
        return favorite.user

    @admin.display(description='Рецепт')
    def recipe_name(self, favorite):
        return favorite.recipe


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    search_fields = ('user',)
    list_display = ('user_name', 'recipe_name')

    @admin.display(description='Автор')
    def user_name(self, cart):
        return cart.user

    @admin.display(description='Рецепт')
    def recipe_name(self, cart):
        return cart.recipe


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    search_fields = ('user',)
    list_display = ('user_name', 'author_name')

    @admin.display(description='Подписчик')
    def user_name(self, subscription):
        return subscription.user

    @admin.display(description='Автор')
    def author_name(self, subscription):
        return subscription.author
