# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import permissions


class IsReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        return request.method in permissions.SAFE_METHODS

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsSuperuserOrReadOnly(IsReadOnly):

    def has_object_permission(self, request, view, obj):
        return super(IsSuperuserOrReadOnly, self).has_object_permission(request, view, obj) or (
                request.user.is_active and request.user.is_superuser)

    def has_permission(self, request, view):
        return super(IsSuperuserOrReadOnly, self).has_permission(request, view) or (
                request.user.is_active and request.user.is_superuser)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        else:
            return False


class IsOwnerOrStaffOrSuperuser(permissions.BasePermission):
    """
    Object-level permission to only allow staff, superuser or owner of an object to access it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_active and (request.user.is_staff or request.user.is_superuser):
            return True
        else:
            # Instance must have an attribute named `owner`.
            return hasattr(obj, 'owner') and obj.owner == request.user

    def has_permission(self, request, view):
        return request.user.is_active and (request.user.is_staff or request.user.is_superuser)


class IsOwnerOrStaffOrSuperuserOrReadOnly(IsReadOnly):

    def has_object_permission(self, request, view, obj):
        if super(IsOwnerOrStaffOrSuperuserOrReadOnly, self).has_object_permission(request, view, obj):
            return True

        if request.user.is_active and (request.user.is_staff or request.user.is_superuser):
            return True
        else:
            # Instance must have an attribute named `owner`.
            return hasattr(obj, 'owner') and obj.owner == request.user

    def has_permission(self, request, view):
        if super(IsOwnerOrStaffOrSuperuserOrReadOnly, self).has_permission(request, view):
            return True
        return request.user.is_active and (request.user.is_staff or request.user.is_superuser)


# Register class only if `filer` installed
try:
    from filer.fields.file import FilerFileField
except ImportError:
    pass
else:
    class IsFilerFileOwnerOrReadOnly(permissions.BasePermission):
        """
        Object-level permission to only allow owners of an object to edit it.
        Assumes the model instance has an `file.owner` attribute.
        """

        def has_object_permission(self, request, view, obj):
            # Read permissions are allowed to any request,
            # so we'll always allow GET, HEAD or OPTIONS requests.
            if request.method in permissions.SAFE_METHODS:
                return True

            # Instance must have an attribute: `FilerFileField` object.
            for field in obj._meta.fields:
                if isinstance(field, FilerFileField):
                    f = getattr(obj, field.name)
                    return f.owner == request.user
            else:
                return False