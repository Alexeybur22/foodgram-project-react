from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProfileViewSet, TagViewSet, IngredientViewSet, RecipeViewSet

router_version1 = DefaultRouter()
router_version1.register("users", ProfileViewSet, basename="user")
router_version1.register("tags", TagViewSet, basename="tag")
router_version1.register(
    "ingredients", IngredientViewSet, basename="ingredient"
)
router_version1.register(
    "recipes", RecipeViewSet, basename="recipe"
)

urlpatterns = [
    path('', include(router_version1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
