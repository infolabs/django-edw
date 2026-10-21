# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.cache import cache


class ContractsAppConfig(AppConfig):
    name = 'edw.tests.contract.app'
    label = 'edw_contracts'
    verbose_name = 'EDW contracts (synthetic test app)'

    def ready(self):
        """
        EDW в AppConfig.ready() прогревает кэш и сразу валидирует дерево
        терминов, обращаясь к БД. В тестах БД ещё пуста (таблиц нет), поэтому
        заранее ставим те же cache-флаги: ready() ядра пропустит запросы,
        а тесты создадут термин-дерево явно (fixture).
        """
        from edw.models.data_mart import DataMartModel
        from edw.models.entity import EntityModel

        for materialized in (EntityModel, DataMartModel):
            root = materialized.materialized
            classes = [root] + list(root.get_all_subclasses())
            for clazz in classes:
                cls_key = clazz.__name__.lower()
                cache.set('vldt:{}:tr'.format(cls_key), True, 60)
                cache.set('vldt:{}:dm'.format(cls_key), True, 60)
