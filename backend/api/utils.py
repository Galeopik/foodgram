from datetime import date

from django.utils import formats
from django.utils.translation import override

UNIT_FORMS = {
    'банка': ('банка', 'банки', 'банок'),
    'батон': ('батон', 'батона', 'батонов'),
    'веточка': ('веточка', 'веточки', 'веточек'),
    'горсть': ('горсть', 'горсти', 'горстей'),
    'капля': ('капля', 'капли', 'капель'),
    'кусок': ('кусок', 'куска', 'кусков'),
    'стакан': ('стакан', 'стакана', 'стаканов'),
    'щепотка': ('щепотка', 'щепотки', 'щепоток'),
}


def get_unit_form(number, unit):
    forms = UNIT_FORMS.get(unit)

    if not forms:
        return unit

    number = abs(int(number))

    if 11 <= number % 100 <= 19:
        return forms[2]

    remainder = number % 10

    if remainder == 1:
        return forms[0]

    if 2 <= remainder <= 4:
        return forms[1]

    return forms[2]


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
                f'{get_unit_form(
                    ingredient["total"],
                    ingredient["ingredient__measurement_unit"]
                )}'
            )
            for number, ingredient in enumerate(
                ingredients,
                start=1,
            )
        ],
    ])
