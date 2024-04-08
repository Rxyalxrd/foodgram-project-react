from rest_framework import serializers
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Tag, Ingredient, Recipe, ShoppingCart, Favorite
)

from users.models import (
    User, Follow
)

from const import USER_LENGTH


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    image = Base64ImageField(
        read_only=False,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'pub_author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'recipe_name',
            'image',
            'description',
            'cooking_time'
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart."""
    ...

    class Meta:
        model = ShoppingCart


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Favorite."""
    ...

    class Meta:
        model = Favorite


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Follow."""

    class Meta:
        model = Follow
        fields = '__all__'


class CustomUserSerializer(UserSerializer):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    username = serializers.CharField(max_length=USER_LENGTH)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return object.author.filter(subscriber=request.user).exists()

    def validate(self, data):
        """Запрещает пользователям присваивать себе username me
        и использовать повторные username и email."""
        if data.get('username') == 'me':
            raise serializers.ValidationError(
                'Использовать имя me запрещено'
            )
        if User.objects.filter(username=data.get('username')):
            raise serializers.ValidationError(
                'Пользователь с таким username уже существует'
            )
        if User.objects.filter(email=data.get('email')):
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует'
            )
        return data
