# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import permissions

from filer.fields.file import FilerFileField


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