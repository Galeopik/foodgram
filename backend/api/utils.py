import secrets
import string

from rest_framework.response import Response


def generate_short_link():
    characters = string.ascii_letters + string.digits

    return ''.join(
        secrets.choice(characters)
        for _ in range(3)
    )


def paginate_response(
    view,
    queryset,
    serializer_class,
    **context
):
    page = view.paginate_queryset(queryset)

    context['request'] = view.request

    if page is not None:
        serializer = serializer_class(
            page,
            many=True,
            context=context
        )
        return view.get_paginated_response(serializer.data)

    serializer = serializer_class(
        queryset,
        many=True,
        context=context
    )
    return Response(serializer.data)
