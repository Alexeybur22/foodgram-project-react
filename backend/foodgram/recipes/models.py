from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Recipe(models.Model):
    favorite = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorites"
    )


class Ingredient(models.Model):
    pass


class Tag(models.Model):
    pass


class RecipeIngredient(models.Model):
    pass


class RecipeTag(models.Model):
    pass
