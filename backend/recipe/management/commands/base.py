import json

from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    """Базовая команда для загрузки данных из JSON."""

    model = None
    file_path = None

    def handle(self, *args, **options):
        try:
            with open(
                self.file_path,
                encoding='utf-8'
            ) as file:
                data = json.load(file)

            objects = [
                self.model(**item)
                for item in data
            ]

            created = self.model.objects.bulk_create(
                objects,
                ignore_conflicts=True,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Фикстура: {self.file_path}\n'
                    f'Добавлено новых записей: {len(created)}'
                )
            )
        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка загрузки: {error}'
                )
            )
