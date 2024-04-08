from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from djoser.views import UserViewSet
from recipes.models import Ingredient, Recipe, Tag
from users.models import User
from .serializers import (
    TagSerializer, IngredientSerializer, RecipeSerializer,
    CustomUserSerializer
)
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для объектов класса Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для объектов класса Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для объектов класса Recipe."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)


class CustomUserViewSet(UserViewSet):
    """ViewSet для объектов класса CustomUser."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
