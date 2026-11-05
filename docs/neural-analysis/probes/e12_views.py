# -*- coding: utf-8 -*-
"""E12.residualcheck: independent probe serializers/views/permissions.

These are *check-owned* fixtures mounted on separate routers.  They exercise
the real product consumer path (TermViewSet / DataMartViewSet / EntityViewSet,
real Dynamic RESTMeta hook patching) without importing the author's test
modules, assertions or probe views.
"""
from __future__ import unicode_literals

from rest_framework.fields import empty
from rest_framework.permissions import BasePermission

from edw.models.defaults.term import Term
from edw.rest.permissions import IsSuperuserOrReadOnly
from edw.rest.serializers.data_mart import DataMartDetailSerializer
from edw.rest.serializers.entity import EntityDetailSerializer
from edw.rest.serializers.term import TermDetailSerializer
from edw.views.data_mart import DataMartViewSet
from edw.views.entity import EntityViewSet
from edw.views.term import TermViewSet

STATE = {
    'events': [],
    'mutate_to': None,
    'mutate_field': None,
    'deny_slugs': set(),
}


def reset_state():
    STATE['events'] = []
    STATE['mutate_to'] = None
    STATE['mutate_field'] = None
    STATE['deny_slugs'] = set()


# --------------------------------------------------------------------------- #
# Term probes
# --------------------------------------------------------------------------- #
class RecordingTermSerializer(TermDetailSerializer):
    """Records the state-aware validation pass (after whole-batch admission)."""

    def run_validation(self, data=empty):
        STATE['events'].append(
            ('run_validation', getattr(getattr(self, 'instance', None), 'pk', None)))
        return super(RecordingTermSerializer, self).run_validation(data)

    def validate_slug(self, value):
        STATE['events'].append(
            ('validate_slug', getattr(getattr(self, 'instance', None), 'pk', None), value))
        return value

    def validate(self, attrs):
        STATE['events'].append(
            ('validate', getattr(getattr(self, 'instance', None), 'pk', None)))
        attrs = super(RecordingTermSerializer, self).validate(attrs)
        field = STATE['mutate_field']
        if field is not None and STATE['mutate_to'] is not None:
            attrs = dict(attrs)
            attrs[field] = STATE['mutate_to']
        return attrs


def _custom(serializer_class):
    classes = dict(TermViewSet.custom_serializer_classes)
    for action in ('create', 'update', 'partial_update', 'bulk_update',
                   'partial_bulk_update'):
        classes[action] = serializer_class
    return classes


class RecordingTermViewSet(TermViewSet):
    custom_serializer_classes = _custom(RecordingTermSerializer)


class HookTermViewSet(RecordingTermViewSet):
    """Same recording serializer mounted on its own URL prefix."""


class MutateTermViewSet(RecordingTermViewSet):
    """The serializer mutates a lookup field only when a check asks it to."""


class RecordingDenyPermission(BasePermission):
    def has_permission(self, request, view):
        STATE['events'].append(('perm', None, None))
        return True

    def has_object_permission(self, request, view, obj):
        slug = getattr(obj, 'slug', None)
        STATE['events'].append(('obj_perm', getattr(obj, 'pk', None), slug))
        return slug not in STATE['deny_slugs']


class PermissionTermViewSet(RecordingTermViewSet):
    permission_classes = [RecordingDenyPermission]


class BoundTermViewSet(TermViewSet):
    """Queryset explicitly bound to ``second`` while routers say default."""

    queryset = Term.objects.using('second')
    custom_serializer_classes = _custom(RecordingTermSerializer)


# --------------------------------------------------------------------------- #
# Data-mart probe (actual DataMartDynamicMetaMixin + real RESTMeta hooks)
# --------------------------------------------------------------------------- #
class RecordingDataMartSerializer(DataMartDetailSerializer):
    def run_validation(self, data=empty):
        STATE['events'].append(
            ('dm_run_validation', getattr(getattr(self, 'instance', None), 'pk', None)))
        return super(RecordingDataMartSerializer, self).run_validation(data)

    def validate(self, attrs):
        STATE['events'].append(
            ('dm_validate', getattr(getattr(self, 'instance', None), 'pk', None)))
        attrs = super(RecordingDataMartSerializer, self).validate(attrs)
        field = STATE['mutate_field']
        if field is not None and STATE['mutate_to'] is not None:
            attrs = dict(attrs)
            attrs[field] = STATE['mutate_to']
        return attrs


class RecordingDataMartViewSet(DataMartViewSet):
    custom_serializer_classes = dict(DataMartViewSet.custom_serializer_classes)
    for _action in ('create', 'update', 'partial_update', 'bulk_update',
                    'partial_bulk_update'):
        custom_serializer_classes[_action] = RecordingDataMartSerializer


# --------------------------------------------------------------------------- #
# Writable entity probe on the existing synthetic materialized model
# --------------------------------------------------------------------------- #
class WritableEntitySerializer(EntityDetailSerializer):
    def run_validation(self, data=empty):
        STATE['events'].append(
            ('entity_run_validation',
             getattr(getattr(self, 'instance', None), 'pk', None)))
        return super(WritableEntitySerializer, self).run_validation(data)

    def validate(self, attrs):
        STATE['events'].append(
            ('entity_validate', getattr(getattr(self, 'instance', None), 'pk', None)))
        attrs = super(WritableEntitySerializer, self).validate(attrs)
        field = STATE['mutate_field']
        if field is not None and STATE['mutate_to'] is not None:
            attrs = dict(attrs)
            attrs[field] = STATE['mutate_to']
        return attrs


class WritableEntityViewSet(EntityViewSet):
    """Test-only writable endpoint; the production default stays read-only."""

    permission_classes = [IsSuperuserOrReadOnly]
    custom_serializer_classes = dict(EntityViewSet.custom_serializer_classes)
    for _action in ('create', 'update', 'partial_update', 'bulk_update',
                    'partial_bulk_update'):
        custom_serializer_classes[_action] = WritableEntitySerializer
