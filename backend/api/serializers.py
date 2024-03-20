from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from rest_framework import serializers, status
from rest_framework.validators import UniqueValidator
from djoser.serializers import UserSerializer

from recipes.models import Ingredient, Tag

from .constants import (MAX_EMAIL_LENGTH, MAX_FIRST_NAME_LENGTH,
                        MAX_LAST_NAME_LENGTH, MAX_PASSWORD_LENGTH,
                        MAX_USERNAME_LENGTH, USERNAME_REGEX)

User = get_user_model()



class ProfileSerializer(UserSerializer):

    email = serializers.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        required=True,
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

    password = serializers.CharField(
        max_length=MAX_PASSWORD_LENGTH,
        required=True,
        write_only=True,
    )

    is_subscribed = serializers.SerializerMethodField(required=False)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "password",
        )

    def get_is_subscribed(self, obj):

        request = self.context.get("request", None)
        if request:
            current_user = request.user

        try:
            obj.following.get(id=current_user.id)
            return True
        except Exception:
            return False

    def create(self, validated_data):
        email = validated_data["email"]
        username = validated_data["username"]

        existing_user_by_email = User.objects.filter(email=email).first()

        if existing_user_by_email:
            if existing_user_by_email.username != username:
                raise serializers.ValidationError(
                    {
                        "error": "Такая почта уже использована,"
                        "но при регистрации использован другой логин."
                    },
                    code=status.HTTP_400_BAD_REQUEST,
                )
            return existing_user_by_email

        existing_user_by_username = User.objects.filter(username=username).first()

        if existing_user_by_username:
            if existing_user_by_username.email != email:
                raise serializers.ValidationError(
                    {
                        "error": "Такой пользователь уже существует, "
                        "но при регистрации использована другая почта."
                    },
                    code=status.HTTP_400_BAD_REQUEST,
                )
            return existing_user_by_username

        user = User.objects.create(**validated_data)

        return user


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = "__all__"
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ("id", "name", "measurement_unit")
        model = Ingredient


class RecipeSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True)
