from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipe.models import Recipe, RecipeIngredient, Ingredient, Tag

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки методов ингредиента."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки методов тега."""
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки связаной модели."""
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки методов рецепта."""
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    tags = TagSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки методов пользователя."""
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar')
