import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Ingredient, IngredientAmount, ProfileFavorite,
                            Recipe, RecipeTag, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .constants import (MAX_EMAIL_LENGTH, MAX_FIRST_NAME_LENGTH,
                        MAX_LAST_NAME_LENGTH, MAX_USERNAME_LENGTH,
                        USERNAME_REGEX)
from .mixins import IngredientMixin
from .validators import (check_amount, empty_values, nonexistent_values,
                         repetitive_values)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_representation(self, data):
        return super().to_representation(data)

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class ProfileSerializer(UserSerializer):

    def __init__(self, *args, **kwargs):
        recipes = kwargs.pop("recipes", False)

        super().__init__(*args, **kwargs)

        if not recipes:
            self.fields.pop("recipes")
            self.fields.pop("recipes_count")

    is_subscribed = serializers.SerializerMethodField(required=False)

    recipes = serializers.SerializerMethodField(required=False)
    recipes_count = serializers.SerializerMethodField(required=False)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            "username",
            "email",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def get_is_subscribed(self, obj):
        request = self.context.get("request", None)
        if request:
            current_user = request.user
        else:
            current_user = self.context["user"]

        return obj.followers.filter(id=current_user.id).exists()

    def get_recipes(self, obj):
        recipes = RecipeReadSerializer(
            obj.recipes, many=True,
            fields=["id", "name", "image", "cooking_time"]
        ).data
        return recipes

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class ProfileCreateSerializer(UserCreateSerializer):

    email = serializers.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
        ],
    )

    username = serializers.CharField(
        max_length=MAX_USERNAME_LENGTH,
        required=True,
        validators=[
            RegexValidator(
                regex=USERNAME_REGEX,
            ),
            UniqueValidator(queryset=User.objects.all()),
        ],
    )

    first_name = serializers.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
        required=True,
    )

    last_name = serializers.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
        required=True,
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("username", "email")


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = "__all__"
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Ingredient


class IngredientinRecipeSerializer(
    serializers.ModelSerializer, IngredientMixin
):

    amount = serializers.SerializerMethodField()

    def get_amount(self, obj):
        recipe_id = self.context.get("recipe_id")
        return IngredientAmount.objects.get(
            recipe_id=recipe_id, ingredient_id=obj.id
        ).amount


class IngredientWriteSerializer(serializers.ModelSerializer, IngredientMixin):

    amount = serializers.IntegerField(required=True, write_only=True)


class RecipeReadSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)

        super().__init__(*args, **kwargs)

        if fields is not None:

            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    tags = TagSerializer(many=True)
    author = ProfileSerializer(required=False)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        exclude = ("pub_date",)

    def get_is_favorited(self, obj):
        request = self.context.get("request", None)
        if request:
            current_user = request.user
        try:
            obj.is_favorited.get(id=current_user.id)
            return True
        except Exception:
            return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request", None)
        if request:
            current_user = request.user
        try:
            obj.is_in_shopping_cart.get(id=current_user.id)
            return True
        except Exception:
            return False

    def get_ingredients(self, obj):
        context = {"recipe_id": obj.id}
        if self.context.get("request"):
            context.update({"method": self.context.get("request").method})

        return IngredientinRecipeSerializer(
            obj.ingredients.all(), many=True, context=context
        ).data


class RecipeWriteSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    ingredients = IngredientWriteSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time"
        )

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)
        empty_values(ingredients, tags)
        repetitive_values(ingredients, tags)

        request = self.context.get("request", None)
        validated_data["author_id"] = request.user.id
        recipe = Recipe.objects.create(**validated_data)

        for ingredient, tag in zip(ingredients, tags):
            amount = ingredient.pop("amount")
            check_amount(amount)
            nonexistent_values(ingredient)
            current_ingredient = Ingredient.objects.get(
                id=ingredient.pop("id")
            )
            IngredientAmount.objects.create(
                ingredient=current_ingredient, recipe=recipe, amount=amount
            )
            RecipeTag.objects.create(tag=tag, recipe=recipe)

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)

        empty_values(ingredients, tags)
        repetitive_values(ingredients, tags)

        request = self.context.get("request", None)
        validated_data["author_id"] = request.user.id

        IngredientAmount.objects.filter(recipe=instance).delete()
        RecipeTag.objects.filter(recipe=instance).delete()

        instance.image = validated_data["image"]
        instance.name = validated_data["name"]
        instance.text = validated_data["text"]
        instance.cooking_time = validated_data["cooking_time"]

        instance.save()

        for ingredient, tag in zip(ingredients, tags):
            amount = ingredient.pop("amount")
            check_amount(amount)
            nonexistent_values(ingredient)
            current_ingredient = Ingredient.objects.get(
                id=ingredient.pop("id")
            )
            IngredientAmount.objects.create(
                ingredient=current_ingredient, recipe=instance, amount=amount
            )
            RecipeTag.objects.create(tag=tag, recipe=instance)

        return instance

    def to_representation(self, data):
        return RecipeReadSerializer(
            context=self.context
        ).to_representation(data)


class ProfileFavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ("user", "recipe")
        model = ProfileFavorite
