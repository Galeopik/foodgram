from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, Tag, User)

admin.site.unregister(Group)


class RecipeIngredientInlineForm(forms.ModelForm):

    class Meta:
        model = RecipeIngredient
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['ingredient'].label_from_instance = (
            lambda obj: f'{obj.name} ({obj.measurement_unit})'
        )


class RecipeCountMixin:
    list_display = ('get_recipes_count',)

    @admin.display(description='рецептов')
    def get_recipes_count(self, user):
        return user.recipes_count

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_count=Count('recipes')
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
    relation_name = 'subscriptions'


class HasSubscribersFilter(HasObjectsFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_subscribers'
    relation_name = 'author_subscriptions'


class IngredientUsedFilter(HasObjectsFilter):
    title = 'Есть в рецептах'
    parameter_name = 'used'
    relation_name = 'recipes'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    form = RecipeIngredientInlineForm
    extra = 1
    verbose_name = 'Продукт'
    verbose_name_plural = 'Продукты'
    fields = (
        'ingredient',
        'amount',
        'get_measurement_unit',
    )
    readonly_fields = ('get_measurement_unit',)

    @admin.display(description='Единица измерения')
    def get_measurement_unit(self, obj):
        if not obj.ingredient:
            return ''
        return obj.ingredient.measurement_unit


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    FAST_TIME = 15
    MEDIUM_TIME = 30
    MAX_TIME = 999999

    TIME_RANGES = {
        'fast': (0, FAST_TIME),
        'medium': (FAST_TIME + 1, MEDIUM_TIME),
        'long': (MEDIUM_TIME + 1, MAX_TIME),
    }

    def lookups(self, request, model_admin):
        return (
            ('fast', f'Быстрые (до {self.FAST_TIME} мин.)'),
            (
                'medium',
                f'Средние ({self.FAST_TIME + 1}–'
                f'{self.MEDIUM_TIME} мин.)',
            ),
            ('long', f'Долгие (более {self.MEDIUM_TIME} мин.)'),
        )

    def queryset(self, request, times):
        time_range = self.TIME_RANGES.get(self.value())

        if time_range is None:
            return times

        return times.filter(cooking_time__range=time_range)


@admin.register(User)
class UserAdmin(RecipeCountMixin, BaseUserAdmin):
    """Настройки отображения пользователей в админке."""
    list_display = (
        'id',
        'username',
        'get_full_name',
        'email',
        'get_avatar',
        *RecipeCountMixin.list_display,
        'get_subscriptions_count',
        'get_author_subscriptions_count',
    )
    search_fields = ('username', 'email')
    list_filter = (
        HasRecipeFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter
    )

    readonly_fields = ('get_avatar',)

    fieldsets = (
        (None, {
            'fields': (
                'username',
                'password',
            ),
        }),
        ('Личная информация', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'get_avatar',
                'avatar',
            ),
        }),
        ('Права доступа', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'user_permissions',
            ),
        }),
    )

    @admin.display(description='ФИО')
    def get_full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def get_avatar(self, user):
        if not user.avatar:
            return ''
        return (
            f'<img src="{user.avatar.url}" '
            f'style="width: 50px; height: 50px; object-fit: contain;">'
        )

    @admin.display(description='Подписок')
    def get_subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчиков')
    def get_author_subscriptions_count(self, user):
        return user.author_subscriptions.count()


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
        'get_cooking_time',
        'author',
        'get_favorites_count',
        'get_ingredients',
        'get_tags',
        'get_image'
    )
    list_filter = ('tags', 'author__username', CookingTimeFilter)

    readonly_fields = ('get_image',)

    fieldsets = (
        ('О рецепте', {
            'fields': (
                'name',
                'author',
                'get_image',
                'image',
                'text',
                'tags',
                'cooking_time',
            ),
        }),
    )

    @admin.display(description=mark_safe('Время<br>(мин)'))
    def get_cooking_time(self, recipe):
        return recipe.cooking_time

    @admin.display(description='В избранном')
    def get_favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, recipe):
        return mark_safe(
            '<br>'.join(
                f'{item.ingredient.name} - '
                f'{item.ingredient.measurement_unit}: '
                f'{item.amount}'
                for item in recipe.recipe_ingredients.all()
            )
        )

    @admin.display(description='Теги')
    def get_tags(self, recipe):
        return mark_safe(
            '<br>'.join(tag.name for tag in recipe.tags.all())
        )

    @admin.display(description='Изображение')
    @mark_safe
    def get_image(self, recipe):
        if not recipe.image:
            return ''
        return (
            f'<img src="{recipe.image.url}" '
            f'style="width: 50px; height: 50px; object-fit: contain;">'
        )


@admin.register(Ingredient)
class IngredienteAdmin(RecipeCountMixin, admin.ModelAdmin):

    search_fields = ('name',)
    list_display = (
        'id',
        'name',
        'measurement_unit',
        *RecipeCountMixin.list_display
    )
    list_filter = ('measurement_unit', IngredientUsedFilter)


@admin.register(Tag)
class TagAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        *RecipeCountMixin.list_display
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


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    search_fields = ('recipe',)
    list_display = ('id', 'recipe', 'ingredient')
