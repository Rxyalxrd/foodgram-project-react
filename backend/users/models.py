from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint

from const import (
    EMAIL_LENGTH, FIRST_NAME_LENGTH, LAST_NAME_LENGTH, USERNAME_LENGTH
)
from .validators import validate_username


class User(AbstractUser):
    """ Кастомная модель пользователя. """

    email = models.EmailField(
        'Почта',
        max_length=EMAIL_LENGTH,
        unique=True
    )
    first_name = models.CharField(
        'Имя',
        max_length=FIRST_NAME_LENGTH,
        blank=False
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=LAST_NAME_LENGTH,
        blank=False
    )
    username = models.CharField(
        'Юзернейм',
        max_length=USERNAME_LENGTH,
        validators=[validate_username]
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """ Модель подписок. """

    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        related_name='author',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='user_author_unique'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на {self.author}'
