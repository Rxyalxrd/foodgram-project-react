from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Ingredient, Recipe, RecipeIngredient, ShoppingCart,
                            Tag)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (CreateRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeSerializer,
                          ShoppingCartSerializer, ShowSubscriptionsSerializer,
                          SubscriptionSerializer, TagSerializer)


class SubscribeView(APIView):
    ''' Операция подписки/отписки. '''

    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        data = {
            'user': request.user.id,
            'author': id
        }
        serializer = SubscriptionSerializer(
            data=data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        author = get_object_or_404(User, id=id)
        if Subscription.objects.filter(
           user=request.user, author=author).exists():
            subscription = get_object_or_404(
                Subscription, user=request.user, author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShowSubscriptionsView(ListAPIView):
    ''' Отображение подписок. '''

    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    serializer_class = ShowSubscriptionsSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(author__user=user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    ''' Отображение тегов. '''

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    ''' Отображение ингредиентов. '''

    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    ''' Операции с рецептами: добавление/изменение/удаление/просмотр. '''

    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = CustomPagination
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @staticmethod
    def process_favorite(request, pk, serializer_class):
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        serializer = serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def add_to_favorites(self, request, pk=None):
        return self.process_favorite(
            request=request, pk=pk,
            serializer_class=FavoriteSerializer)

    @add_to_favorites.mapping.delete
    def remove_from_favorites(self, request, pk=None):
        return self.process_favorite(
            request=request, pk=pk,
            serializer_class=FavoriteSerializer
        )

    @staticmethod
    def process_shopping_cart(request, pk, serializer_class):
        data = {'user': request.user.id, 'recipe': pk}
        recipe = get_object_or_404(Recipe, id=pk)
        if not ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            serializer = serializer_class(
                data=data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def add_to_shopping_cart(self, request, pk=None):
        return self.process_shopping_cart(
            request=request, pk=pk, serializer_class=ShoppingCartSerializer
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        instance = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).first()
        if instance:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт не найден в корзине.'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(methods=['GET'], detail=False)
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        ingredient_lines = []
        for ingredient_data in ingredients:
            line = (
                f'{ingredient_data["ingredient__name"]} - '
                f'{ingredient_data["amount"]} '
                f'{ingredient_data["ingredient__measurement_unit"]}'
            )
            ingredient_lines.append(line)

        ingredient_list = ','.join(ingredient_lines)

        file_name = 'shopping_list'
        response = HttpResponse(
            ingredient_list, content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{file_name}.pdf"'
        )
        return response
