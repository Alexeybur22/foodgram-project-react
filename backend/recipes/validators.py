from django.core.exceptions import ValidationError


def validate_nonzero(value):
    if value == 0:
        raise ValidationError(
            _('Количество ингредиента %(value)s запрещено'),
            params={'value': value},
        )