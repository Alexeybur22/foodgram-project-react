from django.contrib.auth.models import AbstractUser
from django.db import models

from api.constants import MAX_EMAIL_LENGTH


class Profile(AbstractUser):
    """Кастомный класс для пользователя с функционалом подписок"""

    following = models.ManyToManyField(
        "self", blank=True, related_name="followers", symmetrical=False
    )

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

#    email = models.EmailField(
#        verbose_name="Адрес электронной почты", max_length=MAX_EMAIL_LENGTH, unique=True
#    )

#    USERNAME_FIELD = 'email'
#    EMAIL_FIELD = 'email'
#    REQUIRED_FIELDS = ['username']
