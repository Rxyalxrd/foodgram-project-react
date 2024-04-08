from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, F


class User(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=30)
    last_name = models.CharField(_("last name"), max_length=150)
    password = models.CharField(_("password"), max_length=150)
    is_admin = models.BooleanField(_("admin status"), default=False)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Изменение related_name для groups
        blank=True,
        verbose_name=_('groups'),
        help_text=_('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',  # Изменение related_name для user_permissions
        blank=True,
        verbose_name=_('user permissions'),
        help_text=_('Specific permissions for this user.'),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "password"]

    class Meta(AbstractUser.Meta):
        ordering = ["id"]

    def __str__(self):
        return self.username


class Follow(models.Model):
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "author"],  # Изменено на subscriber и author
                name="unique_follow"
            ),
            models.CheckConstraint(
                check=~Q(subscriber=F("author")),  # Изменено на subscriber и author
                name="subscriber_not_equal_author"
            )
        ]

    def __str__(self):
        return f'{self.subscriber} подписан на: {self.author}'
