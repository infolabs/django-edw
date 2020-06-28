# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

from haystack import indexes
from haystack.constants import DJANGO_CT
from haystack.utils import get_model_ct

from edw.models.entity import EntityModel


class EntityIndex(indexes.SearchIndex):
    """
    Abstract base class used to index all entities for this edw
    """

    title = indexes.CharField(
        stored=True,
        indexed=True,
        model_attr='entity_name'
    )

    entity_model = indexes.CharField(
        stored=True,
        indexed=True,
        model_attr='entity_model',
    )

    terms = indexes.MultiValueField(
        stored=True,
        indexed=True,
        model_attr='active_terms_ids',
    )

    characteristics = indexes.MultiValueField(
        stored=True,
        indexed=True,
    )

    text = indexes.CharField(
        stored=True,
        indexed=True,
        document=True,
        use_template=True,
    )

    categories = indexes.MultiValueField(
        stored=True,
        indexed=True,
    )

    autocomplete = indexes.EdgeNgramField(
        use_template=True,
    )

    def get_model(self):
        """
        Hook to refer to the used Entity model.
        Override this to create indices of specialized entity models.
        """
        return EntityModel

    def prepare(self, entity):
        """
        Fetches and adds/alters data before indexing.
        """
        prepared_data = super(EntityIndex, self).prepare(entity)
        prepared_data.update({DJANGO_CT: get_model_ct(self.get_model()())})
        return prepared_data

    def prepare_categories(self, entity):
        '''
        Базовый метод для получения категории объекта, в конкретных индексах его надо перекрыть для получения нужных данных
        :param entity:
        :return:
        Example:
        from collections import OrderedDict
        [json.dumps(OrderedDict((
            ('id', obj.id),
            ('name', obj.name)
        )), ensure_ascii=False)] if obj else []
        '''

        return []

    def prepare_characteristics(self, entity):
        return [
            '{}: {}'.format(term.name, ', '.join(term.values))
            for term in entity.characteristics
        ]

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
        return self.get_model().objects.active()
