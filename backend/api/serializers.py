from collections import Counter

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipe.constants import MIN_COOKING_TIME_MINUTES, MIN_PORTION_VOLUME
from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Subscription, Tag)

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки связаной модели рецепта и ингредиента."""
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для обработки создания рецепта."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=MIN_PORTION_VOLUME)


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для обработки методов пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, profile_user):
        user = self.context['request'].user

        return (
            user.is_authenticated
            and Subscription.objects.filter(
                user=user,
                author=profile_user
            ).exists()
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки корзины и избранного."""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = fields


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    tags = TagSerializer(
        many=True,
        read_only=True,
    )
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )
        read_only_fields = fields

    def _is_user_related(self, model, recipe):
        user = self.context['request'].user

        return (
            user.is_authenticated
            and model.objects.filter(
                user=user,
                recipe=recipe
            ).exists()
        )

    def get_is_favorited(self, recipe):
        return self._is_user_related(
            Favorite,
            recipe
        )

    def get_is_in_shopping_cart(self, recipe):
        return self._is_user_related(
            ShoppingCart,
            recipe
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = RecipeIngredientCreateSerializer(
        many=True,
        write_only=True,
        required=True,
        allow_empty=False,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        allow_empty=False,
    )
    image = Base64ImageField(
        required=True,
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME_MINUTES
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data

    def validate(self, recipe_data):
        errors = {}

        if self.partial:
            if 'ingredients' not in recipe_data:
                errors['ingredients'] = 'Обязательное поле.'

            if 'tags' not in recipe_data:
                errors['tags'] = 'Обязательное поле.'

        if errors:
            raise serializers.ValidationError(errors)

        return recipe_data

    @staticmethod
    def validate_duplicates(ids, item_name):
        duplicates = {
            item_id
            for item_id, count in Counter(ids).items()
            if count > 1
        }

        if duplicates:
            raise serializers.ValidationError(
                f'Повторяющиеся {item_name}: {duplicates}.'
            )

    def validate_ingredients(self, ingredients):
        ingredient_ids = [
            ingredient['id'].id
            for ingredient in ingredients
        ]
        self.validate_duplicates(ingredient_ids, 'продукты')
        return ingredients

    def validate_tags(self, tags):
        tag_ids = [tag.id for tag in tags]
        self.validate_duplicates(tag_ids, 'теги')
        return tags

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError('Поле не может быть пустым')
        return image

    @staticmethod
    def _create_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self._create_ingredients(
            recipe,
            ingredients
        )
        return recipe

    def update(self, instance, validated_data):
        instance.tags.set(validated_data.pop('tags'))
        instance.recipe_ingredients.all().delete()
        self._create_ingredients(
            instance,
            validated_data.pop('ingredients')
        )
        return super().update(instance, validated_data)


class UserSubscriptionSerializer(UserSerializer):
    """Сериализатор пользователя с информацией о подписке."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')

    def get_recipes(self, instance):
        recipes_limit = int(
            self.context['request'].query_params.get(
                'recipes_limit',
                10**10
            )
        )
        recipes = instance.recipes.all()[:recipes_limit]

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
