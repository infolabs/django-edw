# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db import models


#==============================================================================
# SemanticRuleFilterMixin
#==============================================================================
class SemanticRuleFilterMixin(object):
    """
    RUS: Миксин фильтр Семантическое правило.
    """

    def make_filters(self, *args, **kwargs):
        '''
        :return: queryset filters
        RUS: Возбуждает исключение, метод make_filters должен быть переопределен в дочерних классах.
        '''
        raise NotImplementedError(
            '{cls}.make_filters must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    def make_leaf_filters(self, field_name):
        if self.active and self.pk is not None:
            ids = list(self.get_descendants(include_self=True).active().values_list('id', flat=True))
            return [models.Q(**{field_name + '__in': ids})] if len(ids) > 1 else [models.Q(**{field_name: ids[0]})]
        else:
            return []


#==============================================================================
# OrRuleFilterMixin
#==============================================================================
class OrRuleFilterMixin(SemanticRuleFilterMixin):

    def make_filters(self, *args, **kwargs):
        term_info = kwargs.pop('term_info')
        field_name = kwargs.get('field_name')
        filters = filter(None, (x.term.make_filters(term_info=x, *args, **kwargs) for x in term_info))
        if term_info.is_leaf or not filters:
            result = self.make_leaf_filters(field_name)
        else:
            result = filters[0]
            for z in filters[1:]:
                r = []
                for x in result:
                    for y in z:
                        r.append(x | y)
                result = r
            if self.pk is not None:
                result = [models.Q(**{field_name: self.pk}) | x for x in result]
        return result


#==============================================================================
# AndRuleFilterMixin
#==============================================================================
class AndRuleFilterMixin(SemanticRuleFilterMixin):

    def make_filters(self, *args, **kwargs):
        term_info = kwargs.pop('term_info')
        field_name = kwargs.get('field_name')
        filters = filter(None, (x.term.make_filters(term_info=x, *args, **kwargs) for x in term_info if not x.is_leaf))
        if term_info.is_leaf or not filters:
            result = self.make_leaf_filters(field_name)
        else:
            result = []
            for x in filters:
                for y in x:
                    result.append(y)
        return result
