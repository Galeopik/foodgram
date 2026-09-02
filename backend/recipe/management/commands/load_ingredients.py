import json

from django.core.management.base import BaseCommand

from recipe.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов'

    def handle(self, *args, **options):
        with open('data/ingredients.json', encoding='utf-8') as file:
            ingredients = json.load(file)

        for ingredient in ingredients:
            Ingredient.objects.create(
                name=ingredient['name'],
                measurement_unit=ingredient['measurement_unit'],
            )
        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено ингредиентов: {len(ingredients)}'
            )
        )