from datetime import date

from django.utils import formats
from django.utils.translation import override


def create_shopping_list(ingredients):
    with override('ru'):
        shopping_date = formats.date_format(
            date.today(),
            'j E Y'
        )

    return '\n'.join([
        'Список покупок',
        f'Дата составления: {shopping_date}',
        '',
        'Продукты:',
        *[
            (
                f'{number}. '
                f'{ingredient["ingredient__name"].capitalize()} — '
                f'{ingredient["total"]} '
                f'{ingredient["ingredient__measurement_unit"]}'
            )
            for number, ingredient in enumerate(
                ingredients,
                start=1,
            )
        ],
    ])
