# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import permissions


class IsReadOnly(permissions.BasePermission):
    """
    ENG: Style of permission would be to allow full access to authenticated users,
    but allow read-only access to unauthenticated users.
    RUS: Полный доступ к  любому типа объекта в моделях для аутентифицированных пользователей
    и доступ только для чтения неаутентифицированным пользователям.
    """

    def has_object_permission(self, request, view, obj):
        """
        ENG: Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        RUS: Аутентифицированные пользователи могут выполнять любой запрос.
        Запросы для неавторизованных пользователей будут разрешены, 
        только если метод запроса является одним из «безопасных» методов: GET, HEAD или OPTIONS.
        """
        return request.method in permissions.SAFE_METHODS

    def has_permission(self, request, view):
        """
        ENG: To implement a custom permission.
        Test if a request is a read operation or a write operation.
        RUS: Для реализации пользовательского разрешения.
        Проверка разрешения запроса (чтение или запись).
        """
        return request.method in permissions.SAFE_METHODS


class IsSuperuserOrReadOnly(IsReadOnly):
    """
    RUS: Правила разрешений для суперпользователей 
    """

    def has_object_permission(self, request, view, obj):
        """
        Полный доступ к  любому типа объекта в моделях для аутентифицированных суперпользователей 
        или суперпользователей со стасусом активен.
        """
        return super(IsSuperuserOrReadOnly, self).has_object_permission(request, view, obj) or (
                request.user.is_active and request.user.is_superuser)

    def has_permission(self, request, view):
        """
        Разрешает полный доступ для аутентифицированных суперпользователей
        или суперпользователей со стасусом активен на уровне представления.
        """
        return super(IsSuperuserOrReadOnly, self).has_permission(request, view) or (
                request.user.is_active and request.user.is_superuser)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    ENG: Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    RUS: Разрешение на уровне объекта, позволяющее только 
    пользователям со статусом "владелец" объекта, изменять его.
    """
    def has_object_permission(self, request, view, obj):
        """
        ENG: Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        RUS: Разрешение на чтение для любого типа запроса, 
        только если метод запроса является одним из «безопасных» методов: GET, HEAD или OPTIONS.
        """

        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        else:
            return False


class IsOwnerOrStaffOrSuperuser(permissions.BasePermission):
    """
    ENG: Object-level permission to only allow staff, superuser or owner of an object to access it.
    Assumes the model instance has an `owner` attribute.
    RUS: Разрешение на уровне объекта разрешает доступ к объекту только администратору, 
    суперпользователю или владельцу объекта
    """
    def has_object_permission(self, request, view, obj):
        """
        Полный доступ к разрешениям для каждого объекта в моделях для администратора или суперпользователя
        со стасусом активен.
        """
        if request.user.is_active and (request.user.is_staff or request.user.is_superuser):
            return True
        else:
            # Instance must have an attribute named `owner`.
            return hasattr(obj, 'owner') and obj.owner == request.user

    def has_permission(self, request, view):
        """
        Разрешает полный доступ для администратора или суперпользователя
        со стасусом активен на уровне представления.
        """
        return request.user.is_active and (request.user.is_staff or request.user.is_superuser)


 # Register class only if `filer` installed
try:
    from filer.fields.file import FilerFileField
except ImportError:
    pass
else:
    class IsFilerFileOwnerOrReadOnly(permissions.BasePermission):
        """
        ENG: Object-level permission to only allow owners of an object to edit it.
        Assumes the model instance has an `file.owner` attribute.
        RUS: Разрешение на уровне объекта, позволяющее только владельцам объекта изменять его.
        Предполагается, что у атрибута статус владельца.
        """

        def has_object_permission(self, request, view, obj):
            """
            ENG: Read permissions are allowed to any request,
            so we'll always allow GET, HEAD or OPTIONS requests.
            RUS: Разрешение на чтение для любого типа запроса, 
            только если метод запроса является одним из «безопасных» методов: GET, HEAD или OPTIONS.
            """
            if request.method in permissions.SAFE_METHODS:
                return True

            # Instance must have an attribute: `FilerFileField` object.
            for field in obj._meta.fields:
                if isinstance(field, FilerFileField):
                    f = getattr(obj, field.name)
                    return f.owner == request.user
            else:
                return False
