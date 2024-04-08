from django.db import models
from django.core.validators import (
    MinValueValidator, MaxValueValidator, RegexValidator
)

from const import (
    RECIPE_LENGTH, MIN_COOKING_TIME, MAX_COOKING_TIME,
    MEASUREMENT_UNIT_LENGTH, TAG_NAME_LENGTH, SLUG_LENGTH,
    INGREDIENT_NAME_LENGTH, HEX_MAX_LENGTH
)

from users.models import User


class Tag(models.Model):
    """Модель Тэга."""

    tag_name = models.CharField(
        verbose_name="Название тэга",
        max_length=TAG_NAME_LENGTH,
        unique=True,
    )

    color = models.CharField(
        verbose_name='Цветовой код',
        max_length=HEX_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Введенное значение не является цветом в формате HEX!'
            )
        ]
    )

    slug = models.SlugField(
        verbose_name="Слаг",
        max_length=SLUG_LENGTH,
        unique=True,
        db_index=True,
    )

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"

    def __str__(self) -> str:
        return self.tag_name


class Ingredient(models.Model):
    """Модель Ингредиента."""

    ingredient_name = models.CharField(
        verbose_name="Название",
        max_length=INGREDIENT_NAME_LENGTH,
        db_index=True,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MEASUREMENT_UNIT_LENGTH,
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self) -> str:
        return self.ingredient_name


class Recipe(models.Model):
    """Модель Рецепта."""

    pub_author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.SET_NULL,
        null=True,
    )
    recipe_name = models.CharField(
        verbose_name="Название",
        max_length=RECIPE_LENGTH,
    )
    image = models.ImageField(
        verbose_name="Изображение",
        upload_to="recipes/",
        null=True,
        default=None,
    )
    description = models.TextField(
        verbose_name="Текстовое описание",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Тэги",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления в минутах",
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message="Минимальное время приготовления 1 минута."
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message="Максимальное время приготовления 1024 минуты."
            )
        ]
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self) -> str:
        return self.recipe_name


class ShoppingCart(models.Model):
    """Модель для добавления рецепта в список покупок."""

    recipe_name = models.CharField(
        verbose_name="Название",
        max_length=RECIPE_LENGTH,
    )
    image = models.ImageField(
        verbose_name="Изображение",
        upload_to="recipes/",
        null=True,
        default=None,
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления в минутах",
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message="Минимальное время приготовления 1 минута."
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message="Максимальное время приготовления 1024 минуты."
            )
        ]
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self) -> str:
        return f'"{self.recipe_name}" добавлен в Корзину покупок'


class Favorite(models.Model):
    """Модель избранных рецептов."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"

    def __str__(self) -> str:
        return f'"{self.recipe.recipe_name}" добавлен в Избранное'
