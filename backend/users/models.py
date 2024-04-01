from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, F


class User(AbstractUser):
    email = models.EmailField(_("email address"))
    first_name = models.CharField(_("first name"))
    last_name = models.CharField(_("last name"))
    password = models.CharField(
        "Пароль",
        max_length=150,
    )
    is_admin = models.BooleanField(
        "Администратор",
        default=False
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "password"]

    class Meta(AbstractUser.Meta):
        ordering = ["id"]


class Follow(models.Model):
    user = models.ForeignKey(
        "Пользователь",
        User,
        related_name="follower",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        "Автор",
        User,
        related_name="following",
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_follow"
            ),
            models.CheckConstraint(
                check=~Q(user=F("author")),
                name="user_not_equal_author"
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на: {self.author}'
