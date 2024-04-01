from django.shortcuts import get_object_or_404

from recipes.models import Ingredient, Recipe, Tag
from users.models import User, Follow


class IngredientViewSet():
    queryset = Ingredient.objects.all()
    serializers_class = ...
    permission_classes = ...


class TagViewSet():
    queryset = Tag.objects.all()
    serializers_class = ...
    permission_classes = ...


class RecipeViewSet():
    queryset = Recipe.objects.all()
    serializers_class = ...
    permission_classes = ...
