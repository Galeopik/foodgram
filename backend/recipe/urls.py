from django.urls import path

from recipe.views import redirect_to_recipe

urlpatterns = [
    path('s/<int:recipe_id>/', redirect_to_recipe, name='short-link'),
]
