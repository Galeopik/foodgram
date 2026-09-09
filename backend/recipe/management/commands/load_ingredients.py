from recipe.management.commands.base import BaseImportCommand
from recipe.models import Ingredient


class Command(BaseImportCommand):
    """Загрузка ингредиентов."""

    model = Ingredient
    file_path = '../data/ingredients.json'
