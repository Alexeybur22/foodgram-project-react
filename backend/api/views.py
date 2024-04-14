from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import Ingredient
from recipes.models import Profile as User
from recipes.models import Recipe, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilterSet
from .mixins import TagIngredientMixin
from .paginators import PageNumberAsLimitOffset
from .permissions import IsAuthorOrReadOnly, IsUserOrReadOnly
from .serializers import (IngredientinRecipeSerializer, IngredientSerializer,
                          ProfileFavoriteSerializer, ProfileSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShoppingCartSerializer, SubscribeAuthorSerializer,
                          SubscriptionsSerializer, TagSerializer)


class ProfileViewSet(UserViewSet):

    http_method_names = ["get", "post"]
    pagination_class = LimitOffsetPagination
    serializer_class = ProfileSerializer
    permission_classes = (IsUserOrReadOnly,)

    @action(
        detail=False, methods=["get"],
        permission_classes=(IsAuthenticated,),
        pagination_class=LimitOffsetPagination
    )
    def subscriptions(self, request):
        queryset = request.user.following.all()
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            page, many=True,
            context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        http_method_names=["post", "delete"],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)

        if request.method == "POST":
            serializer = SubscribeAuthorSerializer(
                author, data=request.data,
                context={
                    "request": request,
                    "author": author
                }
            )
            serializer.is_valid(raise_exception=True)
            request.user.following.add(author)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        if request.method == "DELETE":
            get_object_or_404(
                User, id=request.user.id, following=author
            )
            request.user.following.remove(author)
            return Response(
                {"detail": "Вы отписались от данного пользователя."},
                status=status.HTTP_204_NO_CONTENT
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
    pagination_class = PageNumberAsLimitOffset
    serializer_class = RecipeReadSerializer
    filterset_class = RecipeFilterSet
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        else:
            return RecipeWriteSerializer

    @staticmethod
    def post_or_delete(
        request, pk, serializer_class,
        data=None, context=None
    ):
        if not data:
            data = {"id": pk}
        if not context:
            context = {"request": request}
        serializer = serializer_class(
            data=data,
            context=context
        )
        serializer.is_valid(raise_exception=True)

        return serializer.validated_data

    @action(
        detail=True,
        methods=("post",),
        permission_classes=(IsAuthenticated,),
        serializer_class=ProfileFavoriteSerializer,
    )
    def favorite(self, request, pk):
        user = request.user

        recipe = self.post_or_delete(
            request, pk, self.serializer_class,
            data={"user": user.pk},
            context={
                "id": pk,
                "request": request
            }
        )

        user.favorite_recipes.add(recipe)

        message_serializer = RecipeReadSerializer(
            recipe, fields=["id", "name", "image", "cooking_time"]
        )
        return Response(
            message_serializer.data, status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def delete_from_favorite(self, request, pk):
        user = request.user

        recipe = self.post_or_delete(
            request, pk, self.serializer_class,
            data={"user": user.pk},
            context={
                "id": pk,
                "request": request
            }
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
        methods=("post",),
        permission_classes=(IsAuthenticated,),
        serializer_class=RecipeReadSerializer,
    )
    def shopping_cart(self, request, pk):

        recipe = self.post_or_delete(
            request, pk, ShoppingCartSerializer
        )

        request.user.shopping_cart.add(pk)

        serializer = RecipeReadSerializer(
            recipe, fields=["id", "name", "image", "cooking_time"]
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk):

        self.post_or_delete(
            request, pk, ShoppingCartSerializer
        )

        request.user.shopping_cart.remove(pk)

        return Response(
            {"message": "Рецепт успешно удален из списка покупок"},
            status=status.HTTP_204_NO_CONTENT,
        )
