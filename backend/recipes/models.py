from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser

from api.constants import (
    MAX_HEX_COLOR_LENGTH,
    MAX_NAME_LENGTH,
    MIN_COOKING_TIME
)


class Profile(AbstractUser):
    """Кастомный класс для пользователя с функционалом подписок"""

    following = models.ManyToManyField(
        "self", blank=True, related_name="followers", symmetrical=False
    )

    favorite_recipes = models.ManyToManyField(
        'Recipe',
        related_name='is_favorited',
        blank=True,
    )
    shopping_cart = models.ManyToManyField(
        'Recipe',
        related_name='in_shopping_cart',
        blank=True,
    )

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']


class Recipe(models.Model):
    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="recipes",
    )

    name = models.CharField(max_length=MAX_NAME_LENGTH)

    image = models.ImageField()

    text = models.TextField(
        "Описание рецепта",
        help_text="Добавьте описание рецепта"
    )

    ingredients = models.ManyToManyField(
        "Ingredient",
        verbose_name="Ингредиенты",
        related_name='used_in_recipes',
    )

    tags = models.ManyToManyField(
        "Tag",
        verbose_name="Теги",
        related_name='used_in_recipes',
    )

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления, минут",
        validators=[MinValueValidator(MIN_COOKING_TIME)],
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH)

    measurement_unit = models.CharField(max_length=MAX_NAME_LENGTH)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH)

    color = models.CharField(max_length=MAX_HEX_COLOR_LENGTH)

    slug = models.SlugField(max_length=MAX_NAME_LENGTH)



#class RecipeIngredient(models.Model):
#
#    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
#
#    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)


#class RecipeTag(models.Model):
#
#    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
#
#    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


#class UserFavorite(models.Model):
#    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
#
#    recipe = models.ForeignKey(
#        Recipe, on_delete=models.CASCADE, related_name="favorited_by"
#    )