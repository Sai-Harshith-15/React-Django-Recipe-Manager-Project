from django.urls import path
from apps.home.views import *
urlpatterns = [
   path('recipes/', RecipeListCreateApiView.as_view(), name='recipe-list-create'),
    path('recipes/<str:recipe_id>/', RecipeRetrieveUpdateDestroyApiView.as_view(), name='recipe-detail'),
]