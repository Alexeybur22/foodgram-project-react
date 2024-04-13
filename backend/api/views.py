from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import Ingredient
from recipes.models import Profile as User
from recipes.models import ProfileFavorite, Recipe, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilterSet
from .mixins import TagIngredientMixin
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientinRecipeSerializer, IngredientSerializer,
                          ProfileFavoriteSerializer, ProfileSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          TagSerializer)


class ProfileViewSet(UserViewSet):

    http_method_names = ["get", "post"]
    pagination_class = LimitOffsetPagination
    serializer_class = ProfileSerializer

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
        pagination_class=LimitOffsetPagination,
    )
    def subscriptions(self, request):
        following = request.user.following.all()
        page = self.paginate_queryset(following)

        recipes_limit = request.query_params.get("recipes_limit")

        serializer = self.get_serializer(
            page, many=True, context={"user": request.user}, recipes=True
        )

        if page is not None:
            data = serializer.data
            if recipes_limit:
                for object in data:
                    recipes = object["recipes"]
                    if recipes:
                        object["recipes"] = recipes[: int(recipes_limit)]
            return self.get_paginated_response(data)

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=(IsAuthenticated,),
        http_method_names=["post", "delete"],
        pagination_class=LimitOffsetPagination,
    )
    def subscribe(self, request, id):
        follower = request.user
        user_to_follow = get_object_or_404(User, id=id)
        recipes_limit = request.query_params.get("recipes_limit")

        if follower.id == user_to_follow.id:
            return Response(
                {"error": "Нельзя подписаться или отписаться от самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            if follower.following.filter(id=user_to_follow.id).exists():
                return Response(
                    {"error": "Вы уже подписаны на данного автора."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            follower.following.add(user_to_follow)
            serializer = self.serializer_class(
                user_to_follow, context={"user": request.user}, recipes=True
            )
            data = serializer.data
            recipes = data["recipes"]
            if recipes_limit and recipes:
                data["recipes"] = recipes[: int(recipes_limit)]

            return Response(data, status=status.HTTP_201_CREATED)

        if follower.following.filter(id=user_to_follow.id).exists():
            follower.following.remove(user_to_follow)
            return Response(
                {"message": "Подписка успешно отменена."},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"error": "Невозможно отписаться от данного пользователя."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=[
            "get",
        ],
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        serializer = self.serializer_class(
            request.user, context={"user": request.user}
        )
        return Response(serializer.data)


class TagViewSet(
    TagIngredientMixin
):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(
    TagIngredientMixin
):
    queryset = Ingredient.objects.all()

    def get_serializer_class(self):
        if self.request.GET.get("recipe"):
            return IngredientinRecipeSerializer
        return IngredientSerializer

    def get_serializer_context(self):
        context = {"request": self.request}
        recipe = self.request.GET.get("recipe")
        if recipe:
            context["recipe"] = recipe
        return context


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitOffsetPagination
    serializer_class = RecipeReadSerializer
    filterset_class = RecipeFilterSet
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        else:
            return RecipeWriteSerializer

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        serializer_class=ProfileFavoriteSerializer,
    )
    def favorite(self, request, pk):
        user = request.user

        recipe = Recipe.objects.filter(id=pk).first()
        if not recipe:
            message = {"error": "Несуществующий рецепт"}
            if request.method == "POST":
                return Response(
                    message,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    message,
                    status=status.HTTP_404_NOT_FOUND,
                )

        is_favorite = ProfileFavorite.objects.filter(
            user=user, recipe=recipe
        ).exists()

        serializer = self.serializer_class(
            data={"user": user.pk, "recipe": recipe.pk}
        )
        serializer.is_valid(raise_exception=True)

        if request.method == "POST":
            if is_favorite:
                return Response(
                    {"error": "Невозможно добавить рецепт в избранное."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.favorite_recipes.add(recipe)

            message_serializer = RecipeReadSerializer(
                recipe, fields=["id", "name", "image", "cooking_time"]
            )
            return Response(
                message_serializer.data, status=status.HTTP_201_CREATED
            )

        if not is_favorite:
            return Response(
                {"error": "Невозможно удалить рецепт из избранного."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.favorite_recipes.remove(recipe)
        return Response(
            {"message": "Рецепт успешно удалён из избранного."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        serializer = RecipeReadSerializer(
            request.user.shopping_cart.all(),
            many=True,
            fields=["id", "ingredients"]
        )

        shopping_cart = {}

        for recipe in serializer.data:
            ingredients = recipe["ingredients"]

            for ingredient in ingredients:
                name = (
                    f"{ingredient.get('name')}"
                    f"({ingredient.get('measurement_unit')})"
                )
                shopping_cart[name] = shopping_cart.get(
                    ingredient.get(name), 0
                ) + ingredient.get("amount")

        content = ""
        for key, value in shopping_cart.items():
            content += f"{key} — {value}\n"

        filename = "shopping_cart.txt"
        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            "attachment; filename={0}".format(filename)
        )

        return response

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        serializer_class=RecipeReadSerializer,
    )
    def shopping_cart(self, request, pk):

        if not Recipe.objects.filter(id=pk).exists():
            message = {"error": "Несуществующий рецепт"}
            if request.method == "POST":
                return Response(
                    message,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    message,
                    status=status.HTTP_404_NOT_FOUND,
                )

        recipe = Recipe.objects.get(id=pk)
        is_in_cart = request.user.shopping_cart.filter(id=pk).exists()

        if request.method == "POST":
            if is_in_cart:
                return Response(
                    {"error": "Рецепт уже в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            request.user.shopping_cart.add(pk)
        else:
            if not is_in_cart:
                return Response(
                    {"error": "Рецепта нет в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            request.user.shopping_cart.remove(pk)
            return Response(
                {"message": "Рецепт успешно удален из списка покупок"},
                status=status.HTTP_204_NO_CONTENT,
            )

        serializer = RecipeReadSerializer(
            recipe, fields=["id", "name", "image", "cooking_time"]
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
