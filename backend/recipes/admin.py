from django.contrib import admin

from .models import Tag, Ingredient, Profile, Recipe, IngredientAmount, RecipeTag, ProfileFavorite


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    pass


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    pass


@admin.register(IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    pass


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    pass

@admin.register(ProfileFavorite)
class ProfileFavorite(admin.ModelAdmin):
    pass
