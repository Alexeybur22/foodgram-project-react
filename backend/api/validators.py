from rest_framework import serializers, status

from recipes.models import Ingredient, Recipe


class NotFoundError(serializers.ValidationError):
    def __init__(self, detail):
        super().__init__(detail, code=404)


def repetitive_values(ingredients, tags):

    ingredient_ids = [ingredient["id"] for ingredient in ingredients]
    tag_ids = [tag.id for tag in tags]
    repetitive_ingredient = len(set(ingredient_ids)) < len(ingredient_ids)
    repetitive_tag = len(set(tag_ids)) < len(tag_ids)

    if repetitive_ingredient or repetitive_tag:
        raise serializers.ValidationError(
            {"error": "Повторяющиеся ингредиенты и/или теги"},
            code=status.HTTP_400_BAD_REQUEST,
        )


def nonexistent_values(ingredient):
    existent_ingredient = Ingredient.objects.filter(
        id=ingredient["id"]
    ).exists()

    if not existent_ingredient:
        raise serializers.ValidationError(
            {"error": "Несуществующий ингредиент."},
            code=status.HTTP_400_BAD_REQUEST
        )


def nonexistent_recipe(pk):
    if not Recipe.objects.filter(id=pk).exists():
        raise serializers.ValidationError(
            {"error": "Несуществующий рецепт."},
            code=status.HTTP_400_BAD_REQUEST,
        )


def delete_nonexistent_recipe(pk):
    if not Recipe.objects.filter(id=pk).exists():
        raise NotFoundError({"detail": "Несуществующий рецепт."})


def check_amount(amount):
    if amount < 1:
        raise serializers.ValidationError(
            {"error": "Количество ингредиента меньше 1 недопустимо"},
            code=status.HTTP_400_BAD_REQUEST,
        )


def empty_values(ingredients, tags):
    if not (ingredients and tags):
        raise serializers.ValidationError(
            {"error": "Отсутствуют теги и/или ингредиенты"},
            code=status.HTTP_400_BAD_REQUEST,
        )
