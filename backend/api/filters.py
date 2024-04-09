import django_filters
from django.db.models import Q
from django.forms.fields import MultipleChoiceField
from django_filters.filters import Filter

from recipes.models import Recipe, Tag

known_tags = Tag.objects.values_list("slug", flat=True).distinct()
TAG_CHOICES = [(tag, tag) for tag in known_tags]


class MultipleValueField(MultipleChoiceField):
    def __init__(self, *args, field_class, **kwargs):
        self.inner_field = field_class()
        super().__init__(*args, **kwargs)

    def valid_value(self, value):
        return self.inner_field.validate(value)

    def clean(self, values):
        return values and [self.inner_field.clean(value) for value in values]


class MultipleValueFilter(Filter):
    field_class = MultipleValueField

    def __init__(self, *args, field_class, **kwargs):
        kwargs.setdefault("lookup_expr", "in")
        super().__init__(*args, field_class=field_class, **kwargs)


class RecipeFilterSet(django_filters.FilterSet):

    tags = django_filters.MultipleChoiceFilter(
        field_name="tags__slug", choices=TAG_CHOICES
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
