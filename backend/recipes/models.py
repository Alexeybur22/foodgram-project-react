from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from api.constants import (MAX_HEX_COLOR_LENGTH, MAX_NAME_LENGTH,
                           MIN_COOKING_TIME)

User = get_user_model()


class Recipe(models.Model):
    author = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
    )

    name = models.CharField(max_length=MAX_NAME_LENGTH)

    image = models.URLField()

    text = models.TextField("Описание рецепта", help_text="Добавьте описание рецепта")

    ingredients = models.ForeignKey(
        "Ingredient", verbose_name="Ингредиенты", on_delete=models.SET_NULL, null=True
    )

    tags = models.ManyToManyField("Tag", through="RecipeTag", verbose_name="Теги")

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления, минут",
        validators=[MinValueValidator(MIN_COOKING_TIME)],
    )

    favorite = models.ManyToManyField(User, through="UserFavorite")

    def __str__(self):
        return self.title


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH)

    measurement_unit = models.CharField(max_length=MAX_NAME_LENGTH)


class Tag(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH)

    color = models.CharField(max_length=MAX_HEX_COLOR_LENGTH)

    slug = models.SlugField(max_length=MAX_NAME_LENGTH)


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)


class RecipeTag(models.Model):

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class UserFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorited_by"
    )
