# -*- coding: utf-8 -*-
"""
Form components for working with trees.
"""
from django import forms

from django.forms.fields import ChoiceField
from django.forms.models import ModelChoiceIterator

try:
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_unicode as smart_text

from django.utils.html import conditional_escape, mark_safe
from django.db.utils import ProgrammingError

import hashlib

__all__ = ('FullPathTreeNodeChoiceField',)


class FullPathTreeNodeChoiceFieldMixin(object):

    def __init__(self, queryset, *args, **kwargs):

        self.joiner = kwargs.pop('joiner', ' / ')
        self.to_field_name = kwargs.pop('to_field_name', None)

        # if a queryset is supplied, enforce ordering
        if hasattr(queryset, 'model'):
            mptt_opts = queryset.model._mptt_meta
            queryset = queryset.order_by(mptt_opts.tree_id_attr, mptt_opts.left_attr)

        super(FullPathTreeNodeChoiceFieldMixin, self).__init__(queryset, *args, **kwargs)

    def label_from_instance(self, obj):
        """
        Creates labels which represent full path of each node when
        generating option labels.
        """
        ancestors = list(obj.get_ancestors(include_self=True))
        return mark_safe(self.joiner.join([conditional_escape(smart_text(i)) for i in ancestors])) # todo: limit label length

    def _get_choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        hash = hashlib.md5()

        try:
            hash.update(';'.join(str(x) for x in self.queryset.values_list('id', flat=True)))
        except ProgrammingError as e:
            # initial migrations hack
            print e.args
            return []

        current_queryset_hash = hash.hexdigest()

        if hasattr(self.queryset, '_queryset_hash') and self.queryset._queryset_hash == current_queryset_hash:
            return self.queryset._choices_cache

        self.queryset._queryset_hash = current_queryset_hash
        self.queryset._choices_cache = list(ModelChoiceIterator(self))

        return self.queryset._choices_cache

    choices = property(_get_choices, ChoiceField._set_choices)


class FullPathTreeNodeChoiceField(FullPathTreeNodeChoiceFieldMixin, forms.ModelChoiceField):
    """
    A ModelChoiceField for tree nodes.
    """
