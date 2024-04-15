from django.core.validators import RegexValidator
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, IngredientAmount
from recipes.models import Profile as User
from recipes.models import ProfileFavorite, Recipe, RecipeTag, Tag
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .constants import (MAX_EMAIL_LENGTH, MAX_FIRST_NAME_LENGTH,
                        MAX_LAST_NAME_LENGTH, MAX_USERNAME_LENGTH,
                        USERNAME_REGEX)
from .mixins import IngredientMixin
from .validators import (check_amount, empty_values, nonexistent_values,
                         repetitive_values)


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
        request = self.context.get("request")
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

    tags = TagSerializer(many=True)
    author = ProfileSerializer(required=False)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)

        super().__init__(*args, **kwargs)

        if fields is not None:

            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class Meta:
        model = Recipe
        exclude = ("pub_date",)

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request:
            current_user = request.user

        return obj.is_favorited.filter(id=current_user.id).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request:
            current_user = request.user

        return obj.is_in_shopping_cart.filter(id=current_user.id).exists()

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

    @staticmethod
    def add_ingredients_tags(ingredients, tags, recipe):
        bulk_ingredientamount_list = list()
        bulk_recipetag_list = list()
        for ingredient, tag in zip(ingredients, tags):
            amount = ingredient.pop("amount")
            check_amount(amount)
            nonexistent_values(ingredient)
            current_ingredient = Ingredient.objects.get(
                id=ingredient.pop("id")
            )

            bulk_ingredientamount_list.append(
                IngredientAmount(
                    ingredient=current_ingredient, recipe=recipe, amount=amount
                )
            )
            bulk_recipetag_list.append(
                RecipeTag(tag=tag, recipe=recipe)
            )
        IngredientAmount.objects.bulk_create(bulk_ingredientamount_list)
        RecipeTag.objects.bulk_create(bulk_recipetag_list)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)
        empty_values(ingredients, tags)
        repetitive_values(ingredients, tags)

        request = self.context.get("request")
        validated_data["author_id"] = request.user.id
        recipe = Recipe.objects.create(**validated_data)

        self.add_ingredients_tags(ingredients, tags, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)

        empty_values(ingredients, tags)
        repetitive_values(ingredients, tags)

        request = self.context.get("request", None)
        validated_data["author_id"] = request.user.id

        IngredientAmount.objects.filter(recipe=instance).delete()
        RecipeTag.objects.filter(recipe=instance).delete()

        super().update(instance, validated_data)

        instance.save()

        self.add_ingredients_tags(ingredients, tags, instance)

        return instance

    def to_representation(self, data):
        return RecipeReadSerializer(
            context=self.context
        ).to_representation(data)


class ProfileFavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ("user", "recipe")
        extra_kwargs = {
            "recipe": {
                "required": False
            }
        }
        model = ProfileFavorite

    def validate(self, data):
        user = data.get("user")
        pk = self.context.get("id")
        request = self.context.get("request")
        recipe = Recipe.objects.filter(id=pk).first()
        if not recipe:
            raise serializers.ValidationError(
                {"error": "Несуществующий рецепт"}
            )
        is_favorite = ProfileFavorite.objects.filter(
            user=user, recipe=recipe
        ).exists()

        if request.method == "POST":
            if is_favorite:
                raise serializers.ValidationError(
                    {"error": "Невозможно добавить рецепт в избранное."}
                )

        elif not is_favorite:
            raise serializers.ValidationError(
                {
                    "error":
                    "Невозможно удалить рецепт из избранного."
                }
            )
        return recipe


class SubscriptionsSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes"
        )

    def get_is_subscribed(self, obj):
        return ProfileSerializer.get_is_subscribed(self, obj)

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeReadSerializer(
            recipes, many=True, read_only=True,
            fields=["id", "image", "name", "cooking_time"]
        )
        return serializer.data


class SubscribeAuthorSerializer(serializers.ModelSerializer):

    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeReadSerializer(
        many=True, read_only=True,
        fields=["id", "image", "name", "cooking_time"]
    )

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
        )

    def validate(self, data):
        if (
            self.context["request"].user
            == self.context["author"]
        ):
            raise serializers.ValidationError(
                {"errors": "Ошибка при подписке."}
            )
        return data

    def get_is_subscribed(self, obj):
        return ProfileSerializer.get_is_subscribed(self, obj)


class ShoppingCartSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    def validate(self, data):

        pk = data.get("id")

        request = self.context["request"]
        user = request.user

        recipe = Recipe.objects.filter(id=pk).first()
        if not recipe:
            message = {"error": "Несуществующий рецепт"}
            if request.method == "POST":
                raise serializers.ValidationError(
                    message,
                )
            raise serializers.ValidationError(
                message,
            )
        is_in_cart = user.shopping_cart.filter(id=pk).exists()

        if request.method == "POST":
            if is_in_cart:
                raise serializers.ValidationError(
                    {"error": "Рецепт уже в списке покупок."},
                )

        elif not is_in_cart:
            raise serializers.ValidationError(
                {"error": "Рецепта нет в списке покупок."},
            )
        return recipe
