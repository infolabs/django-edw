# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from classytags.core import Options
from classytags.arguments import MultiKeywordArgument, Argument

from edw.models.term import TermModel
from edw.rest.templatetags import BaseRetrieveDataTag
from edw.rest.serializers.term import TermTreeSerializer

from typing import Any, Dict, List, Optional

# todo: Сделать темлейттег для получения id терминов + cached=False
# todo: Прокидываем в request_params из витрины



class GetTermTree(BaseRetrieveDataTag):
    name = 'get_term_tree'
    queryset = TermModel.objects.toplevel()
    serializer_class = TermTreeSerializer
    action = 'tree'

    options = Options(
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, kwargs, varname):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context=context)
        data = serializer.data
        if varname:
            context[varname] = data
            return ''
        else:
            return self.to_json(data)


def attributes_has_view_class(value, arg):
    if value and isinstance(value, (tuple, list)):
        getter = (lambda x: x['view_class']) if isinstance(value[0], dict) else lambda x: x.view_class
        for attr in value:
            view_class = getter(attr)
            if arg in view_class:
                return True
    return False


class GetTermIdsBySlugs(BaseRetrieveDataTag):
    """
    Тег шаблона для получения списка id терминов по строке slug, разделённой запятыми.

    Параметры:
        slugs (str): Строка с терминами-слугами, разделёнными запятыми.
        cached (bool): Использовать кэш (по умолчанию False).
        return_type (str): 'str' — вернуть строку id через separator, 'list' — вернуть список (по умолчанию).
        separator (str): Разделитель для строки (по умолчанию ',').
        varname (str): Необязательное имя переменной для сохранения результата в контексте.

    Если cached=True, ids собираются через get_cached_ids_by_slug для каждого slug. Иначе ids запрашиваются напрямую из БД.
    Пример:
        {% get_term_ids_by_slugs slugs='slug1,slug2' cached=True return_type='str' separator=';' as ids %}
    """
    name = 'get_term_ids_by_slugs'

    options = Options(
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(
        self,
        context: dict,
        kwargs: dict = None,
        varname: str = None
    ) -> str:
        """
        Получить список id терминов по строке slug через запятую.
        :param context: Контекст шаблона.
        :param kwargs: Аргументы, поддерживаются slugs (str), cached (bool), return_type (str), separator (str).
        :param varname: Имя переменной для сохранения результата.
        :return: JSON-строка, строка id или '' если используется as varname.
        """
        kwargs = kwargs or {}
        slugs = kwargs.get('slugs', '')
        cached = kwargs.get('cached', False)
        return_type = kwargs.get('return_type', 'list')
        separator = kwargs.get('separator', ',')
        slug_list = [s.strip() for s in (slugs or '').split(',') if s.strip()]
        if cached:
            ids = set()
            for slug in slug_list:
                ids.update(TermModel.get_cached_ids_by_slug(slug))
            ids = list(ids)
        else:
            ids = list(TermModel.objects.filter(slug__in=slug_list).values_list('id', flat=True))
        result = ids
        if return_type == 'str':
            result = separator.join(str(i) for i in ids)
        if varname:
            context[varname] = result
            return ''
        else:
            return self.to_json(result)
