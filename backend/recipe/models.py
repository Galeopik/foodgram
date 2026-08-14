from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Почта'
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Никнейм'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField('Аватар', upload_to='avatar_photo')


class Ingredient(models.Model):
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

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('Название', max_length=256, unique=True)
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; разрешены символы '
                  'латиницы, цифры, дефис и подчёркивание.',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.TextField('Автор')
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
    cooking_time = models.IntegerField('Время приготовления')

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
