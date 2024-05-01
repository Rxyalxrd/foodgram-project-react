from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import Subscription, User


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя."""

    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        ]


class CustomUserSerializer(UserSerializer):
    """Сериализатор модели пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра модели Тег."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        error_messages={'does_not_exist': 'Такого тега не существует!'})

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']

    def to_internal_value(self, data):

        tag = {'id': data}
        return super().to_internal_value(tag)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели, связывающей ингредиенты и рецепт."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'amount', 'measurement_unit']


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра модели Ингредиенты."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра модели Рецепт."""

    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)

    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор добавления ингредиента в рецепт."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор создания/обновления рецепта."""

    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(many=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        ]

    @staticmethod
    def validate_unique(values):
        values_set = set()
        for value in values:
            if value in values_set:
                return True
            values_set.add(value)
        return False

    def validate_ingredients(self, data):
        ingredients = data
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент!'
            })
        ingredients = self.initial_data.get('ingredients')
        if self.validate_unique(ingredients):
            raise serializers.ValidationError(
                {'ingredient': 'Ингредиенты должны быть уникальными!'}
            )
        for item in ingredients:
            if int(item['amount']) <= 0:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0!'
                })
        return data

    def validate_tags(self, data):
        tags = data
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно выбрать хотя бы один тег!'
            })
        if self.validate_unique(tags):
            raise serializers.ValidationError({
                'tags': 'Теги должны быть уникальными!'
            })
        return data

    @staticmethod
    def create_or_update_obj(recipe, tags, ingredients):

        for tag in tags:
            recipe.tags.add(tag['id'])
        ingredients_in_recipe = []
        for ingredient in ingredients:
            ingredients_in_recipe.append(
                RecipeIngredient(
                    ingredient=ingredient['id'],
                    recipe=recipe,
                    amount=ingredient['amount']
                )
            )
        recipe.recipe_ingredients.bulk_create(ingredients_in_recipe)
        return recipe

    @transaction.atomic
    def create(self, validated_data):

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        return self.create_or_update_obj(recipe, tags, ingredients)

    @transaction.atomic
    def update(self, instance, validated_data):

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        recipe = super().update(instance, validated_data)
        return self.create_or_update_obj(recipe, tags, ingredients)


class ShowFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения избранного."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return ShowFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели Избранное."""

    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return ShowFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class ShowSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = Recipe.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        else:
            recipes = recipes.all()
        return ShowFavoriteSerializer(
            recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""

    class Meta:
        model = Subscription
        fields = ['user', 'author']
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
            )
        ]

    def to_representation(self, instance):
        return ShowSubscriptionsSerializer(instance.author, context={
            'request': self.context.get('request')
        }).data
