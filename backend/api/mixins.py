from recipes.models import Ingredient
from rest_framework import filters, mixins, viewsets


class IngredientMixin:
    class Meta:
        fields = ("id", "name", "measurement_unit", "amount")
        model = Ingredient
        extra_kwargs = {
            "id": {"read_only": False},
            "name": {"read_only": True},
            "measurement_unit": {"read_only": True},
        }


class TagIngredientMixin(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None
