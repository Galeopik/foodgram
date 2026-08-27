from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag, User


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ('username', 'email')

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    search_fields = ('name', 'author__username', 'author__email')
    list_display = ('name', 'author', 'favorites_count')
    list_filter = ('tags',)

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredienteAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass
