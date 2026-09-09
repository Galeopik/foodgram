from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from foodgram_backend.settings import USERNAME_VALIDATE
from recipe.constants import MIN_COOKING_TIME_MINUTES, MIN_PORTION_VOLUME


class User(AbstractUser):
    """Описание модели пользователя."""
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Почта'
    )
    username = models.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=USERNAME_VALIDATE,
            )
        ],
        verbose_name='Никнейм',
        unique=True
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='avatar_photo',
        blank=True,
        verbose_name='Аватар'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return self.email


class Ingredient(models.Model):
    """Описание модели продукта."""
    name = models.CharField('Название', max_length=128, unique=True)
    measurement_unit = models.CharField(
        'единица измерения',
        max_length=64
    )

    class Meta:
        verbose_name = 'продукт'
        verbose_name_plural = 'продукты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('Название', max_length=32, unique=True)
    slug = models.SlugField(
        'Идентификатор',
        max_length=32,
        unique=True,
        help_text='Идентификатор страницы для URL; разрешены символы '
                  'латиницы, цифры, дефис и подчёркивание.',
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=256)
    image = models.ImageField('Изображение', upload_to='recipe_photo')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='Tag',
        verbose_name='Теги'
    )
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(MIN_COOKING_TIME_MINUTES)
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'
        ordering = ('-created_at',)
        default_related_name = 'recipes'

    def __str__(self):
        return self.name


class UserRecipeRelation(models.Model):
    """Базовая модель связи пользователя с рецептом."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(app_label)s_%(class)s_unique_user_recipe',
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(UserRecipeRelation):
    """Описание модели избранного."""
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'


class ShoppingCart(UserRecipeRelation):
    """Описание модели корзины."""
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'корзина'
        verbose_name_plural = 'корзины'


class RecipeIngredient(models.Model):
    """Связанная модель рецепта и ингредиента."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Продукт'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_PORTION_VOLUME)],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'ингредиенты рецепта'
        default_related_name = 'recipe_ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return str(self.ingredient)


class Subscription(models.Model):
    """Описание модели с подписками."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_made'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_received'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]
