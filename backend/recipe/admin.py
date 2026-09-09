from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, Tag, User)


class RecipeCountMixin:
    recipe_count_relation = 'recipes'

    @admin.display(description='рецептов')
    def get_recipes_count(self, user):
        return user.recipes.count()

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_count=Count(self.recipe_count_relation)
        )


class HasObjectsFilter(admin.SimpleListFilter):
    USED_LOOKUPS = (
        ('yes', 'Есть'),
        ('no', 'Нет'),
    )

    def lookups(self, request, model_admin):
        return self.USED_LOOKUPS

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                **{f'{self.relation_name}__isnull': False}
            ).distinct()

        if self.value() == 'no':
            return queryset.filter(
                **{f'{self.relation_name}__isnull': True}
            ).distinct()

        return queryset


class HasRecipeFilter(HasObjectsFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'
    relation_name = 'recipes'


class HasSubscriptionsFilter(HasObjectsFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'
    relation_name = 'subscriptions_made'


class HasSubscribersFilter(HasObjectsFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_subscribers'
    relation_name = 'subscriptions_received'


class IngredientUsedFilter(admin.SimpleListFilter):
    title = 'Есть в рецептах'
    parameter_name = 'used'

    USED_LOOKUPS = (
        ('yes', 'Есть в рецептах'),
        ('no', 'Нет в рецептах'),
    )

    def lookups(self, request, model_admin):
        return self.USED_LOOKUPS

    def queryset(self, request, queryset):

        if self.value == 'yes':
            return queryset.filter(recipes_count__gt=0)

        if self.value == 'no':
            return queryset.filter(recipes_count=0)

        return queryset


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(User)
class UserAdmin(RecipeCountMixin, BaseUserAdmin):
    """Настройки отображения пользователей в админке."""
    list_display = (
        'id',
        'username',
        'get_full_name',
        'email',
        'get_avatar',
        'get_recipes_count',
        'get_subscriptions_made_count',
        'get_subscriptions_received_count',
    )
    search_fields = ('username', 'email')
    list_filter = (
        HasRecipeFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter
    )

    @admin.display(description='ФИО')
    def get_full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def get_avatar(self, user):
        if not user.avatar:
            return ''
        return f'<img src="{user.avatar.url}" width="50" height="50">'

    @admin.display(description='Подписок')
    def get_subscriptions_made_count(self, user):
        return user.subscriptions_made.count()

    @admin.display(description='Подписчиков')
    def get_subscriptions_received_count(self, user):
        return user.subscriptions_received.count()


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
        return recipe.favorite_set.count()

    @admin.display(description='Изображение')
    @mark_safe
    def get_image(self, recipe):
        if not recipe.image:
            return ''
        return f'<img src="{recipe.image.url}" width="50" height="50">'


@admin.register(Ingredient)
class IngredienteAdmin(RecipeCountMixin, admin.ModelAdmin):
    recipes_count_relation = 'recipe_ingredients'

    search_fields = ('name',)
    list_display = (
        'id',
        'name',
        'measurement_unit',
        'get_recipes_count'
    )
    list_filter = ('measurement_unit', IngredientUsedFilter)


@admin.register(Tag)
class TagAdmin(RecipeCountMixin, admin.ModelAdmin):
    recipes_count_relation = 'Tag'
    list_display = (
        'id',
        'name',
        'slug',
        'get_recipes_count'
    )
    search_fields = ('name', 'slug')


@admin.register(Favorite, ShoppingCart)
class FavoriteShoppingCartAdmin(admin.ModelAdmin):
    search_fields = ('user',)
    list_display = ('id', 'user', 'recipe')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    search_fields = ('user',)
    list_display = ('id', 'user', 'author')
