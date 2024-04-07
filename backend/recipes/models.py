from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from datetime import datetime

from api.constants import (MAX_HEX_COLOR_LENGTH, MAX_NAME_LENGTH,
                           MIN_COOKING_TIME, MIN_AMOUNT)
from .validators import validate_nonzero


class Profile(AbstractUser):
    """Кастомный класс для пользователя с функционалом подписок"""

    following = models.ManyToManyField(
        "self",
        blank=True,
        related_name="followers",
        symmetrical=False,
        verbose_name="Подписки",
    )

    favorite_recipes = models.ManyToManyField(
        "Recipe",
        related_name="is_favorited",
        blank=True,
        through="ProfileFavorite",
        verbose_name="Избранные рецепты",
    )
    shopping_cart = models.ManyToManyField(
        "Recipe",
        related_name="in_shopping_cart",
        blank=True,
        verbose_name="Корзина покупок",
    )

    REQUIRED_FIELDS = ["email", "first_name", "last_name", "password"]

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Recipe(models.Model):
    author = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="recipes", verbose_name="Автор"
    )

    pub_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
        db_index=True,
    )

    name = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name="Название")

    image = models.ImageField(verbose_name="Картинка")

    text = models.TextField(
        help_text="Добавьте описание рецепта", verbose_name="Описание рецепта"
    )

    ingredients = models.ManyToManyField(
        "Ingredient",
        verbose_name="Ингредиенты",
        related_name="used_in_recipes",
        through="IngredientAmount",
        blank=False
    )

    tags = models.ManyToManyField(
        "Tag",
        verbose_name="Теги",
        related_name="used_in_recipes",
        through="RecipeTag",
        blank=False,
    )

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления, минут",
        validators=[MinValueValidator(MIN_COOKING_TIME)],
    )

    def __str__(self):
        return f'{self.name} от {self.author}'

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ('pub_date',)


class Ingredient(models.Model):

    name = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name="Название")

    measurement_unit = models.CharField(
        max_length=MAX_NAME_LENGTH, verbose_name="Единицы измерения"
    )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class Tag(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name="Название")

    color = models.CharField(
        max_length=MAX_HEX_COLOR_LENGTH, verbose_name="Цветовой код"
    )

    slug = models.SlugField(max_length=MAX_NAME_LENGTH, verbose_name="Слаг")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class ProfileFavorite(models.Model):
    user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, verbose_name="Пользователь"
    )

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")

    def __str__(self):
        return f"{self.user}-{self.recipe}"

    class Meta:
        verbose_name = "Профиль — избранный рецепт"
        verbose_name_plural = "Профили — избранные рецепты"


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, blank=True, verbose_name="Рецепт"
    )

    amount = models.PositiveSmallIntegerField(
        blank=True, default=1, verbose_name="Количество",
        validators=[MinValueValidator(MIN_AMOUNT)]
    )

    def __str__(self):
        return f"{self.ingredient}-{self.recipe}-{self.amount}"

    class Meta:
        unique_together = ('recipe', 'ingredient')
        verbose_name = "Ингредиент — рецепт — количество"
        verbose_name_plural = "Ингредиенты — рецепты — количества"


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name="Тег")

    def __str__(self):
        return f"{self.recipe}-{self.tag}"

    class Meta:
        unique_together = ('recipe', 'tag')
        verbose_name = "Рецепт — тег"
        verbose_name_plural = "Рецепты — теги"
