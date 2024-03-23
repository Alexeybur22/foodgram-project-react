from recipes.models import Ingredient


class IngredientMixin:
    class Meta:
        fields = ('id', 'name', 'measurement_unit', 'amount')
        model = Ingredient
        extra_kwargs = {
            'id': {'read_only': False},
            'name': {'read_only': True},
            'measurement_unit': {'read_only': True},
        }