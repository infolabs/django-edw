# -*- coding: utf-8 -*-
"""
Form components for working with trees.
"""
import hashlib

from django import forms
from django.core.cache import cache
from django.forms.fields import ChoiceField

try:
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_unicode as smart_text

from django.utils.html import conditional_escape, mark_safe
from django.db.utils import ProgrammingError

from edw.models.mptt_info import TermInfo


__all__ = ('FullPathTreeNodeChoiceField',)


class FullPathTreeNodeChoiceFieldMixin(object):

    CHOICES_CACHE_TIMEOUT = 60

    def __init__(self, queryset, *args, **kwargs):

        self.joiner = kwargs.pop('joiner', ' / ')
        self.to_field_name = kwargs.pop('to_field_name', None)

        # if a queryset is supplied, enforce ordering
        if hasattr(queryset.model, '_mptt_meta'):
            mptt_opts = queryset.model._mptt_meta
            queryset = queryset.order_by(mptt_opts.tree_id_attr, mptt_opts.left_attr)

        super(FullPathTreeNodeChoiceFieldMixin, self).__init__(queryset, *args, **kwargs)

    def _get_choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        hash = hashlib.md5()

        try:
            ids = list(self.queryset.values_list('id', flat=True))
        except ProgrammingError as e:
            # initial migrations hack
            print e.args
            return []

        hash.update(';'.join(str(x) for x in ids))

        required = self.empty_label is not None and self.initial is not None

        key = "flPthTrNdChFld:{hash}:{required}".format(hash=hash.hexdigest(), required=required)

        if hasattr(self.queryset, '_queryset_hash') and self.queryset._queryset_hash == key:
            return self.queryset._choices_cache

        choices = cache.get(key, None)
        if choices is None:
            tree = TermInfo.decompress(self.queryset.model(), ids)

            choices = [] if required else [("", self.empty_label)]
            for id in ids:
                term = tree[id].term
                path = [term]
                parent_id = term.parent_id
                while parent_id is not None:
                    term = tree[parent_id].term
                    path.insert(0, term)
                    parent_id = term.parent_id
                choices.append((id, mark_safe(self.joiner.join([conditional_escape(smart_text(i)) for i in path]))))

            self.queryset._queryset_hash = key
            self.queryset._choices_cache = choices
            cache.set(key, choices, self.CHOICES_CACHE_TIMEOUT)

        return choices

    choices = property(_get_choices, ChoiceField._set_choices)


class FullPathTreeNodeChoiceField(FullPathTreeNodeChoiceFieldMixin, forms.ModelChoiceField):
    """
    A ModelChoiceField for tree nodes.
    """
