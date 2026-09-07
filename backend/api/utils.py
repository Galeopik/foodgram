from datetime import date


def create_shopping_list(ingredients):
    return '\n'.join([
        'Список покупок',
        f'Дата составления: {date.today():%d.%m.%Y}',
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
