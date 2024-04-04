from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins, viewsets, status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse


from .serializers import ProfileSerializer, TagSerializer, IngredientSerializer, IngredientinRecipeSerializer,  RecipeReadSerializer, ProfileFavoriteSerializer, RecipeWriteSerializer, FollowSerializer
from recipes.models import Tag, Ingredient, Recipe

User = get_user_model()


class ProfileViewSet(UserViewSet):
    serializer_class = ProfileSerializer

    permission_classes = (IsAuthenticated,)

    http_method_names = ['get', 'post']

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        following = request.user.following
        data = ProfileSerializer(following, many=True, context={'user': request.user}).data
        for obj in data:
            user_id = obj['id']
            user = User.objects.get(id=user_id)
            recipes = RecipeReadSerializer(
                user.recipes, many=True,
                fields=['id', 'name', 'image', 'cooking_time']
            ).data
            obj.update({'recipes': recipes, 'recipes_count': len(recipes)})

        return Response(data)
    
    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        follower = request.user
        user_to_follow = get_object_or_404(User, id=id)

        if request.method == 'POST':
            if follower.following.filter(id=user_to_follow.id):
                return Response(
                        {'error': 'Вы уже подписаны на данного автора.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            if follower.id == user_to_follow.id:
                return Response(
                        {'error': 'Нельзя подписаться на самого себя.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            follower.following.add(user_to_follow)
            return Response(
                        {'message': 'Подписка успешно создана.'},
                        status=status.HTTP_201_CREATED
                    )
        #TODO add delete method and user info in response
        return Response({'message':'OK'})


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
    queryset = Ingredient.objects.all()
    pagination_class = None

    def get_serializer_class(self):
        if self.request.GET.get('recipe'):
            return IngredientinRecipeSerializer
        else:
            return IngredientSerializer

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
    
    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        serializer = RecipeReadSerializer(
            request.user.shopping_cart.all(), many=True
        )

        shopping_cart = dict()

        for recipe in serializer.data:
            ingredients = recipe['ingredients']

            for ingredient in ingredients:
                name = f"{ingredient.get('name')} ({ingredient.get('measurement_unit')})"
                shopping_cart[name] = (
                    shopping_cart.get(ingredient.get(name), 0) + ingredient.get('amount')
                )

        content = ''
        for key, value in shopping_cart.items():
            content += f'{key} — {value}\n'

        filename = "shopping_cart.txt"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)

        return response
    
    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        serializer_class=RecipeReadSerializer
    )
    def shopping_cart(self, request, pk):
        recipe = Recipe.objects.get(id=pk)
        is_in_cart = request.user.shopping_cart.filter(id=pk).exists()

        if request.method == 'POST':
            if is_in_cart:
                return Response({
                    'error': 'Рецепт уже в списке покупок.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.user.shopping_cart.add(pk)
        else:
            if not is_in_cart:
                return Response(
                    {'error': 'Рецепта нет в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.user.shopping_cart.remove(pk)
            return Response(
                {'message': 'Рецепт успешно удален из списка покупок'},
                status=status.HTTP_204_NO_CONTENT
            )

        serializer = RecipeReadSerializer(recipe)

        return Response({
            'id': pk,
            'name': recipe.name,
            'image': serializer.data['image'],
            'cooking_time': recipe.cooking_time
        })
