from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Recipe(models.Model):

    author = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='recipes'
    )

    title = models.CharField()

    image = models.ImageField(
        upload_to='recipes/images/',
    )

    description = models.TextField(
        'Описание рецепта',
        help_text='Добавьте описание рецепта'
    )

    ingredients = models.ForeignKey(
        'Ingredient',
        verbose_name='Ингредиенты'
    )

    tags = models.ManyToManyField(
        'Tag',
        through='RecipeTag',
        verbose_name='Теги'
    )

    time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления, минут',
    )

    favorite = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorites"
    )


    def __str__(self):
        return self.title


class Ingredient(models.Model):
    
    title = models.CharField()

    quantity = models.PositiveSmallIntegerField()

    measurement_units = models.CharField()


class Tag(models.Model):
    
    title = models.CharField()

    color = models.CharField(max_length=7)

    slug = models.SlugField()



class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(
        Recipe
    )

    ingredient = models.ForeignKey(
        Ingredient
    )


class RecipeTag(models.Model):

    recipe = models.ForeignKey(
        Recipe
    )

    tag = models.ForeignKey(
        Tag
    )
