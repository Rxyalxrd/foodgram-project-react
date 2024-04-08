from django.contrib import admin
from .models import Tag, Ingredient, Recipe, ShoppingCart, Favorite


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('tag_name', 'color', 'slug')
    search_fields = ('tag_name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('ingredient_name', 'measurement_unit')
    search_fields = ('ingredient_name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe_name', 'pub_author', 'cooking_time')
    search_fields = ('recipe_name',)
    filter_horizontal = ('ingredients', 'tags')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('recipe_name', 'cooking_time')
    search_fields = ('recipe_name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('recipe',)
