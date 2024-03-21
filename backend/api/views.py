from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins, viewsets


from .serializers import ProfileSerializer, TagSerializer, IngredientSerializer, RecipeSerializer
from recipes.models import Tag, Ingredient, Recipe

User = get_user_model()


class ProfileViewSet(UserViewSet):
    serializer_class = ProfileSerializer

    permission_classes = (IsAuthenticated,)

    http_method_names = ['get', 'post']


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
