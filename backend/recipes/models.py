from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from const import (
    INGREDIENT_NAME_LENGTH, MEASUREMENT_UNIT_LENGTH,
    TAG_NAME_LENGTH, HEX_MAX_LENGTH, SLUG_MAX_LENGTH,
    RECIPE_MAX_LENGTH, MIN_COOKING_TIME, MAX_COOKING_TIME,
    MIN_AMOUNT, MAX_AMOUNT)
from users.models import User


class Ingredient(models.Model):
    """ Модель ингредиента. """

    name = models.CharField(
        'Название ингредиента',
        max_length=INGREDIENT_NAME_LENGTH
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MEASUREMENT_UNIT_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='ingredient_name_unit_unique'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Tag(models.Model):
    """ Модель тега. """

    name = models.CharField(
        'Название тега',
        unique=True,
        max_length=TAG_NAME_LENGTH
    )
    color = ColorField(
        format='hex',
        default='#FF0000',

    )
    slug = models.SlugField(
        'Slug',
        unique=True,
        max_length=SLUG_MAX_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """ Модель рецепта. """

    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги',
        related_name='tags'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/'
    )
    name = models.CharField(
        'Название рецепта',
        max_length=RECIPE_MAX_LENGTH
    )
    text = models.TextField(
        'Описание рецепта',
        help_text='Введите описание рецепта'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f'Время приготовления должно быть '
                f'не менее {MIN_COOKING_TIME} минуты!'
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=f'Время приготовления должно быть '
                f'не более {MAX_COOKING_TIME} минуты!'
            )
        ]
    )
    pub_date = models.DateTimeField(
        'Время публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """ Модель связи ингредиента и рецепта. """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message=f'Минимальное кол-во должно быть {MIN_AMOUNT}'
            ),
            MaxValueValidator(
                MAX_AMOUNT,
                message=f'Максимальное кол-во должно быть {MAX_AMOUNT}')
        ]
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient_unique'
            )
        ]


class RecipeTag(models.Model):
    """ Модель связи тега и рецепта. """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'tag'],
                name='recipe_tag_unique'
            )
        ]


class ShoppingCart(models.Model):
    """ Модель корзины. """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_cart',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_shoppingcart_unique'
            )
        ]


class Favorite(models.Model):
    """ Модель избранного. """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_unique'
            )
        ]
