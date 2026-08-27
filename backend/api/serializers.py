from django.contrib.auth import get_user_model
from djoser.serializers import \
    UserCreateSerializer as DjoserUserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки связаной модели рецепта и ингредиента."""
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для обработки создания рецепта."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        coerce_to_string=False
    )


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки методов пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user

        if user.is_anonymous:
            return False

        return Subscription.objects.filter(
            user=user,
            author=obj
        ).exists()


class RecipeShopFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки корзины и избранного."""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецептов
    с обработкой ингредиентов и тегов.
    """
    ingredients = RecipeIngredientCreateSerializer(
        many=True,
        write_only=True,
        required=True,
        allow_empty=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        allow_empty=False
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    author = UserSerializer(
        read_only=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('short_link', 'created_at')
        read_only_fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def validate(self, attrs):
        errors = {}

        if self.partial:
            if 'ingredients' not in attrs:
                errors['ingredients'] = 'Обязательное поле.'

            if 'tags' not in attrs:
                errors['tags'] = 'Обязательное поле.'

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def validate_ingredients(self, value):
        ingredient_ids = [ingredient['id'].id for ingredient in value]

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Нельзя указывать один ингредиент несколько раз.'
            )

        return value

    def validate_tags(self, value):
        tag_ids = [tag.id for tag in value]

        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Нельзя указывать один тег несколько раз.'
            )

        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Поле не может быть пустым')
        return value

    def create(self, recipe_data):
        ingredients = recipe_data.pop('ingredients')
        tags = recipe_data.pop('tags')

        recipe = Recipe.objects.create(**recipe_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient in ingredients:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['ingredients'] = RecipeIngredientSerializer(
            instance.recipe_ingredients.all(),
            many=True
        ).data
        data['tags'] = TagSerializer(
            instance.tags.all(),
            many=True
        ).data

        return data

    def get_is_favorited(self, obj):
        user = self.context['request'].user

        if not user.is_authenticated:
            return False

        return Favorite.objects.filter(
            user=user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user

        if user.is_anonymous:
            return False

        return ShoppingCart.objects.filter(
            user=user,
            recipe=obj
        ).exists()


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для обработки действий с подписками."""
    recipes = RecipeShopFavoriteSerializer(
        many=True,
        read_only=True
    )
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        recipes_limit = self.context.get('recipes_limit')

        if recipes_limit is not None:
            data['recipes'] = data['recipes'][:int(recipes_limit)]

        return data


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
