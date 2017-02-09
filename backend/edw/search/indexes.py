# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.template import Context
from django.template.loader import select_template
from django.utils import translation
from django.utils.html import strip_spaces_between_tags
from django.utils.safestring import mark_safe

from haystack import indexes

from edw.models.entity import EntityModel


class EntityIndex(indexes.SearchIndex):
    """
    Abstract base class used to index all entities for this edw
    """
    text = indexes.CharField(document=True, use_template=True)
    autocomplete = indexes.EdgeNgramField(use_template=True)
    entity_name = indexes.CharField(stored=True, indexed=True, model_attr='entity_name')
    entity_url = indexes.CharField(stored=True, indexed=False, model_attr='get_absolute_url')

    def get_model(self):
        """
        Hook to refer to the used Product model. Override this to create indices of
        specialized entity models.
        """
        return EntityModel

    def prepare(self, entity):
        if hasattr(entity, 'translations'):
            entity.set_current_language(self.language)
        with translation.override(self.language):
            data = super(EntityIndex, self).prepare(entity)
        return data

    def render_html(self, prefix, entity, postfix):
        """
        Render a HTML snippet to be stored inside the index database.
        """
        app_label = entity._meta.app_label.lower()
        entity_type = entity.__class__.__name__.lower()
        params = [
            (app_label, prefix, entity_type, postfix),
            (app_label, prefix, 'entity', postfix),
            ('edw', prefix, 'entity', postfix),
        ]
        template = select_template(['{0}/entities/{1}-{2}-{3}.html'.format(*p) for p in params])
        context = Context({'entity': entity})
        content = strip_spaces_between_tags(template.render(context).strip())
        return mark_safe(content)

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        if using in dict(settings.LANGUAGES):
            self.language = using
        else:
            self.language = settings.LANGUAGE_CODE
        return self.get_model().objects.indexable()
