from recipe.management.commands.base import BaseImportCommand
from recipe.models import Tag


class Command(BaseImportCommand):
    """Загрузка тегов."""

    model = Tag
    file_path = '../data/tags.json'
