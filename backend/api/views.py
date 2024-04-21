from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from foodgram.settings import STATIC_ROOT
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (IngredientSerializer, RecipeSerializer,
                          ShowSubscriptionsSerializer, SubscriptionSerializer,
                          TagSerializer)


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


def post_delete_method(self, request, pk, model):
    recipe = get_object_or_404(Recipe, id=pk)
    user = self.request.user
    if request.method == 'POST':
        favorite_recipes, create = (
            model.objects.get_or_create(
                user=user,
                recipe=recipe
            )
        )
        if create:
            return Response(
                Recipe(recipe).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'errors': 'Рецепт уже добален'},
            status=status.HTTP_400_BAD_REQUEST
        )
    favorite_recipes = model.objects.filter(user=user, recipe=recipe)
    if favorite_recipes.exists():
        favorite_recipes.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        {'errors': 'Рецепт не был добален'},
        status=status.HTTP_400_BAD_REQUEST
    )


class RecipesViewSet(viewsets.ModelViewSet):
    """
    Класс обработки выдачи рецептов.
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter
    http_method_names = [
        'get',
        'post',
        'patch',
        'delete',
        'head',
        'options',
        'trace'
    ]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite_recipe(self, request, pk):
        """
        Функция добавления/удаления рецепта из избранного.
        """
        return post_delete_method(self, request, pk, Favorite)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        """
        Функция добавления/удаления рецепта из списка покупок.
        """
        return post_delete_method(self, request, pk, ShoppingCart)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """
        Функция выдает PDF файл со списком покупок.
        """
        ing = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart__user=self.request.user
            )
        )
        if not ing.exists():
            raise ValidationError(
                {'errors': 'У вас нет рецептов с списке покупок'}
            )
        res = {}
        for i in ing:
            value = res.get(i.ingredient.name)
            if value is not None:
                value[1] += i.amount
            else:
                res.update(
                    {
                        i.ingredient.name:
                            [i.ingredient.measurement_unit, i.amount]
                    }
                )
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="file.pdf"'

        p = canvas.Canvas(response)
        my_font_object = ttfonts.TTFont(
            'Arial', f'{STATIC_ROOT}/fonts/arial.ttf'
        )
        pdfmetrics.registerFont(my_font_object)
        p.setFont('Arial', 24)
        p.drawString(100, 700, 'Список покупок:')
        p.setFont('Arial', 14)
        x = 680
        num = 1
        for key, val in res.items():
            p.drawString(120, x, f'{num}. {key} {val[1]} {val[0]}')
            x -= 20
            num += 1
        p.showPage()
        p.save()
        return response
