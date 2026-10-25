# -*- coding: utf-8 -*-
"""
E11/R3/R5: test-only probe views and serializers.

Mounted on separate routers in ``urls.py``.  They record whether a state-aware
hook ran and they expose deliberately vulnerable router shapes, without
patching a product hook.  They are used to prove ordering (admission before
validators) and the single-write-alias policy.
"""
from __future__ import unicode_literals

from rest_framework.permissions import BasePermission

from edw.models.defaults.term import Term
from edw.rest.permissions import IsSuperuserOrReadOnly
from edw.rest.serializers.term import TermDetailSerializer
from edw.views.data_mart import DataMartViewSet
from edw.views.entity import EntityViewSet
from edw.views.term import TermViewSet

MARKERS = []
HOOK_EVENTS = []


class RecordingTermSerializer(TermDetailSerializer):
    def run_validation(self, data=None):
        MARKERS.append('run_validation')
        return super(RecordingTermSerializer, self).run_validation(data)

    def validate(self, attrs):
        MARKERS.append('validate')
        return super(RecordingTermSerializer, self).validate(attrs)


class RecordingTermViewSet(TermViewSet):
    custom_serializer_classes = dict(TermViewSet.custom_serializer_classes)
    custom_serializer_classes['create'] = RecordingTermSerializer
    custom_serializer_classes['update'] = RecordingTermSerializer
    custom_serializer_classes['partial_update'] = RecordingTermSerializer
    custom_serializer_classes['bulk_update'] = RecordingTermSerializer
    custom_serializer_classes['partial_bulk_update'] = RecordingTermSerializer


class HookProbeTermSerializer(TermDetailSerializer):
    """Field-level dynamic hook shape: resolves the supplied slug globally."""

    def validate_slug(self, value):
        existing = Term.objects.filter(slug=value).values_list('pk', flat=True).first()
        HOOK_EVENTS.append({'slug': value, 'existing_pk': existing})
        return value


class HookProbeTermViewSet(TermViewSet):
    custom_serializer_classes = dict(TermViewSet.custom_serializer_classes)
    custom_serializer_classes['create'] = HookProbeTermSerializer


class MutatingTermSerializer(TermDetailSerializer):
    """A dynamic validator that changes a validated identity field."""

    mutate_to_slug = None

    def validate(self, attrs):
        attrs = super(MutatingTermSerializer, self).validate(attrs)
        if self.mutate_to_slug is not None:
            attrs['slug'] = self.mutate_to_slug
            attrs.pop('id', None)
        return attrs


class MutatingTermViewSet(TermViewSet):
    custom_serializer_classes = dict(TermViewSet.custom_serializer_classes)
    custom_serializer_classes['create'] = MutatingTermSerializer

    def get_serializer(self, *args, **kwargs):
        serializer = super(MutatingTermViewSet, self).get_serializer(*args, **kwargs)
        value = self.request.query_params.get('_e10_mutate_to')
        serializer.mutate_to_slug = value
        child = getattr(serializer, 'child', None)
        if child is not None:
            child.mutate_to_slug = value
        return serializer


class DenySlugPermission(BasePermission):
    """Allow every object except the one named ``r3-denied``."""

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'slug', None) != 'r3-denied'


class PermissionProbeTermViewSet(RecordingTermViewSet):
    permission_classes = [DenySlugPermission]


class QuerysetBoundTermViewSet(TermViewSet):
    """A view whose queryset is bound to ``second`` while routers say default.

    ``queryset._db`` must not silently replace the router-selected authority.
    """

    queryset = Term.objects.using('second')


class WritableEntityViewSet(EntityViewSet):
    """Test-only writable entity endpoint on the synthetic materialized model.

    The production default is read-only; allowing a superuser write here does
    not add a write capability to the normal configuration.
    """

    permission_classes = [IsSuperuserOrReadOnly]


class DenyMartSlugPermission(BasePermission):
    """Allow every data mart except the one named ``denied-mart``."""

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'slug', None) != 'denied-mart'


class PermissionProbeDataMartViewSet(DataMartViewSet):
    """DataMart write endpoint whose per-object permission denies one mart."""

    permission_classes = [DenyMartSlugPermission]
