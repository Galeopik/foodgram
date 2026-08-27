from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from api.utils import generate_short_link


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
                regex=r'^[\w.@+-]+\Z',
                message='Введите корректный username.',
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

    def __str__(self):
        return self.email


class Ingredient(models.Model):
    """Описание модели ингредиента"""
    class Unit(models.TextChoices):
        GRAM = 'г', 'г'
        KILOGRAM = 'кг', 'кг'
        MILLILITER = 'мл', 'мл'
        LITER = 'л', 'л'
        PIECE = 'шт', 'шт'
        TABLESPOON = 'ст.л.', 'ст.л.'
        TEASPOON = 'ч.л.', 'ч.л.'
        DROP = 'капля', 'капля'
        PIECE_OF = 'кусок', 'кусок'
        CAN = 'банка', 'банка'
        GLASS = 'стакан', 'стакан'
        PINCH = 'щепотка', 'щепотка'
        HANDFUL = 'горсть', 'горсть'
        SPRIG = 'веточка', 'веточка'
        LOAF = 'батон', 'батон'

    name = models.CharField('Название', max_length=256, unique=True)
    measurement_unit = models.CharField(
        'Измерение',
        max_length=40,
        choices=Unit.choices
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('Название', max_length=256, unique=True)
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; разрешены символы '
                  'латиницы, цифры, дефис и подчёркивание.',
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=256)
    image = models.ImageField('Фото', upload_to='recipe_photo')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='Tag',
        verbose_name='Теги'
    )
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(1)
        ]
    )

    short_link = models.CharField(
        'Короткая ссылка',
        max_length=3,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = generate_short_link()

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'рецепт',
        verbose_name_plural = 'рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Описание модели избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]


class RecipeIngredient(models.Model):
    """Связанная модель рецепта и ингредиента."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'ингредиенты рецепта'

    def __str__(self):
        return str(self.ingredient)


class ShoppingCart(models.Model):
    """Описание модели корзины."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]


class Subscription(models.Model):
    """Описание модели с подписками."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )
