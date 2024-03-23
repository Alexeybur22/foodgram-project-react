from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins, viewsets, status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response


from .serializers import ProfileSerializer, TagSerializer, IngredientSerializer, RecipeReadSerializer, ProfileFavoriteSerializer, RecipeWriteSerializer
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

    def get_serializer_context(self):
        context = {'request': self.request}
        recipe = self.request.GET.get('recipe')
        if recipe:
            context['recipe'] = recipe
        return context


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeReadSerializer
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        else:
            return RecipeWriteSerializer

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,),
            serializer_class=ProfileFavoriteSerializer)
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        print(recipe)
        recipe_serializer = RecipeReadSerializer(data=recipe)
        recipe_serializer.is_valid(raise_exception=True)
        is_favorite = recipe_serializer.data['is_favorite']

        serializer = self.get_serializer(data={'user': user.pk, 'recipe': recipe.pk})
        serializer.is_valid(raise_exception=True)

        if request.method == 'POST':
            if is_favorite:
                return Response(
                    {'error': 'Невозможно добавить рецепт в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(
                    {
                        'id': recipe_serializer.data['id'],
                        'name': recipe_serializer.data['name'],
                        'image': recipe_serializer.data['image'],
                        'cooking_time': recipe_serializer.data['cooking_time']
                    },
                    status=status.HTTP_201_CREATED
                )
        
        if not is_favorite:
            return Response(
                    {'error': 'Невозможно удалить рецепт из избранного.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        serializer.delete()

        return Response(
            {'message':'Рецепт успешно удалён из избранного.'},
            status=status.HTTP_204_NO_CONTENT
        )

