from django.db import models
from django.contrib.auth.models import AbstractUser


class Profile(AbstractUser):
    '''Кастомный класс для пользователя с функционалом подписок'''

    following = models.ManyToManyField(
        "self", blank=True, related_name="followers", symmetrical=False
    )

