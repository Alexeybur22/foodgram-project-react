import django_filters
from django.db.models import Q
from recipes.models import Recipe, Tag


def get_tag_choices():
    choices = [
        (tag, tag) for tag in Tag.objects.values_list(
            "slug", flat=True
        ).distinct()
    ]
    return choices


class RecipeFilterSet(django_filters.FilterSet):

    tags = django_filters.MultipleChoiceFilter(
        field_name="tags__slug",
        queryset=Tag.objects.all()
    )
    is_favorited = django_filters.NumberFilter(
        field_name="is_favorited", method="get_is_favorited"
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        field_name="is_in_shopping_cart", method="get_is_in_shopping_cart"
    )

    def get_is_favorited(self, queryset, name, value):
        user_id = self.request.user.id
        if not user_id:
            user_id = 0
        if value:
            return queryset.filter(is_favorited=user_id)
        else:
            return queryset.filter(~Q(is_favorited=user_id))

    def get_is_in_shopping_cart(self, queryset, name, value):
        user_id = self.request.user.id
        if not user_id:
            user_id = 0
        if value:
            return queryset.filter(is_in_shopping_cart=user_id)
        else:
            return queryset.filter(~Q(is_in_shopping_cart=user_id))

    class Meta:
        model = Recipe
        fields = (
            "is_favorited",
            "is_in_shopping_cart",
            "author",
            "tags",
            "name"
        )
