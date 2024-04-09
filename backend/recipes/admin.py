from django.contrib import admin

from .models import (Ingredient, IngredientAmount, Profile, ProfileFavorite,
                     Recipe, RecipeTag, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_filter = ("name",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_filter = ("email", "username")


class IngredientAmountInline(admin.StackedInline):
    model = IngredientAmount
    extra = 0


class RecipeTagInline(admin.StackedInline):
    model = RecipeTag
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientAmountInline, RecipeTagInline)
    list_filter = ("author", "name", "tags")
    list_display = (
        "author",
        "name",
        "image",
        "text",
        "cooking_time",
        "show_number_favorite",
    )
    list_display_links = ("name",)

    def show_number_favorite(self, obj):
        return obj.is_favorited.count()

    show_number_favorite.short_description = "Добавлено в избранное"


@admin.register(IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    pass


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    pass


@admin.register(ProfileFavorite)
class ProfileFavorite(admin.ModelAdmin):
    pass
