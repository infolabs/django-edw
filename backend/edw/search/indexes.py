# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.encoding import force_text

from haystack import indexes
from haystack.constants import DJANGO_CT, DJANGO_ID, ID
from haystack.fields import *
from haystack.utils import get_identifier, get_model_ct

from edw.models.entity import EntityModel


class EntityIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Abstract base class used to index all entities for this edw
    """
    entity_name = indexes.CharField(stored=True, indexed=True, model_attr='entity_name')
    entity_model = indexes.CharField(stored=True, indexed=True, model_attr='entity_model')
    entity_url = indexes.CharField(stored=True, indexed=False, model_attr='get_absolute_url')

    text = indexes.CharField(document=True, use_template=True)

    # autocomplete = indexes.EdgeNgramField(use_template=True)

    def get_model(self):
        """
        Hook to refer to the used Product model. Override this to create indices of
        specialized entity models.
        """
        return EntityModel

    def prepare(self, obj):
        """
        Fetches and adds/alters data before indexing.
        """
        self.prepared_data = {
            ID: get_identifier(obj),
            DJANGO_CT: get_model_ct(EntityModel()),
            DJANGO_ID: force_text(obj.pk),
        }

        for field_name, field in self.fields.items():
            # Use the possibly overridden name, which will default to the
            # variable name of the field.
            self.prepared_data[field.index_fieldname] = field.prepare(obj)

            if hasattr(self, "prepare_%s" % field_name):
                value = getattr(self, "prepare_%s" % field_name)(obj)
                self.prepared_data[field.index_fieldname] = value

        t = loader.select_template(('search/indexes/edw/entity_text.txt', ))

        self.prepared_data['text'] = t.render(Context({'object': obj}))

        return self.prepared_data

    '''
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
    '''

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        if using in dict(settings.LANGUAGES):
            self.language = using
        else:
            self.language = settings.LANGUAGE_CODE
        return self.get_model().objects.all()

