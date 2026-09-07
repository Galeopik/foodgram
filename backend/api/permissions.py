from rest_framework.permissions import SAFE_METHODS, BasePermission


class MixedResourcePermission(BasePermission):
    """
    Политика доступа:
    - GET: любой пользователь.
    - POST: только авторизованный.
    - PATCH/DELETE: только автор объекта.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.method == 'POST':
            return request.user.is_authenticated
        if request.method in ('PUT', 'PATCH', 'DELETE'):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
