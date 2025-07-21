from django.contrib import admin
from apps.home.models import RecipeModel, IngredientsModel
# Register your models here.

admin.site.register(RecipeModel)
admin.site.register(IngredientsModel)