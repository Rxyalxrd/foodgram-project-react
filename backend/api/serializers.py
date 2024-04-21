import base64

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from api import pagination
from const import SERIALIZER_NAME_MAX_LENGTH, SERIALIZER_NAME_MIN_LENGTH
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User


class SignUpSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        read_only_fields = (
            'id',
            'is_subscribed'
        )
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_is_subscribed(self, obj) -> bool:

        user = self.context['request'].user
        if user.is_authenticated:
            return user.subscribe_user.filter(
                author=obj).exists()
        return False

    def to_representation(self, instance):

        res = super().to_representation(instance)
        if (self.context['request'].method == 'POST'
                and self.context['request'].path == '/api/users/'):
            res.pop('is_subscribed')
        return res

    def create(self, validated_data):

        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        read_only_fields = ('name', 'measurement_unit')
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeRepresentationSerializer(IngredientsSerializer):

    def to_representation(self, instance):

        return {
            'id': instance.ingredient.id,
            'name': instance.ingredient.name,
            'measurement_unit': instance.ingredient.measurement_unit,
            'amount': instance.amount
        }


class IngredientsInRecipeSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        error_messages={'does_not_exist': 'Ингридиента нет в базе'})

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class TagsSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        error_messages={'does_not_exist': 'Тега нет в базе'})

    class Meta:
        model = Tag
        read_only_fields = ('name', 'color', 'slug')
        fields = ('id', 'name', 'color', 'slug')

    def to_internal_value(self, data):

        tag = {'id': data}
        return super().to_internal_value(tag)


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeMinifiedSerializer(serializers.ModelSerializer):

    name = serializers.CharField(
        min_length=SERIALIZER_NAME_MIN_LENGTH,
        max_length=SERIALIZER_NAME_MAX_LENGTH
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class RecipesSerializer(RecipeMinifiedSerializer):

    tags = TagsSerializer(many=True)
    ingredients = IngredientsInRecipeSerializer(
        many=True,
        write_only=True
    )
    text = serializers.CharField(min_length=5)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = SignUpSerializer(read_only=True)

    class Meta:
        model = Recipe
        read_only_fields = (
            'id',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def to_representation(self, instance):

        res = super().to_representation(instance)
        res['ingredients'] = (
            IngredientRecipeRepresentationSerializer(
                instance.recipe_ingredients.all(), many=True).data
        )
        return res

    @staticmethod
    def __create_or_update_obj(recipe, tags, ingredients):

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
        return self.__create_or_update_obj(recipe, tags, ingredients)

    @transaction.atomic
    def update(self, instance, validated_data):

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        recipe = super().update(instance, validated_data)
        return self.__create_or_update_obj(recipe, tags, ingredients)

    def validate(self, attrs):

        no_uniq_recipe = (
            self.context['request'].user.recipes.
            filter(name=attrs['name']).exists()
        )
        if self.context['request'].method == 'POST' and no_uniq_recipe:
            raise serializers.ValidationError(
                {'name': 'Вы уже создали такой рецепт'}
            )
        return attrs

    @staticmethod
    def validate_tags(attrs):

        tags_id = []
        for tag in attrs:
            tag_id = tag['id'].id
            tags_id.append(tag_id)
        if len(attrs) == 0:
            raise serializers.ValidationError(
                {'errors': 'Поле не может быть пустым'}
            )
        if len(attrs) != len(set(tags_id)):
            raise serializers.ValidationError(
                {'errors': 'Теги не могут повторяться'}
            )
        return attrs

    @staticmethod
    def validate_ingredients(attrs):

        ingredients_id = []
        for ingredient in attrs:
            ingredient_id = ingredient['id'].id
            ingredients_id.append(ingredient_id)
        if len(attrs) == 0:
            raise serializers.ValidationError(
                {'errors': 'Поле не может быть пустым'}
            )
        if len(attrs) != len(set(ingredients_id)):
            raise serializers.ValidationError(
                {'errors': 'Ингридиенты не могут повторяться'}
            )
        return attrs

    def get_is_favorited(self, obj):

        user = self.context['request'].user
        if user.is_authenticated:
            return user.favoriterecipes_set.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):

        user = self.context['request'].user
        if user.is_authenticated:
            return user.shoppingcart_set.filter(recipe=obj).exists()
        return False


class SubscriptionsSerializer(SignUpSerializer):

    recipes = serializers.SerializerMethodField(
        'paginate_recipes', read_only=True
    )
    recipes_count = serializers.IntegerField(
        read_only=True
    )

    class Meta:
        model = User
        read_only_fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def paginate_recipes(self, obj):

        recipe = obj.recipes.all()
        paginator = pagination.CustomPageNumberPagination()
        paginator.page_size_query_param = 'recipes_limit'
        paginator.page_size = 3
        page = paginator.paginate_queryset(recipe, self.context['request'])
        serializer = RecipeMinifiedSerializer(
            page,
            many=True,
            context={'request': self.context['request']})
        return serializer.data


class SetPasswordSerializer(serializers.Serializer):

    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, obj):

        try:
            validate_password(obj['new_password'])
        except ValidationError as error:
            raise serializers.ValidationError(
                {'new_password': list(error.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):

        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Неправильный пароль.'}
            )
        if (validated_data['current_password']
                == validated_data['new_password']):
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль должен отличаться от текущего.'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data
