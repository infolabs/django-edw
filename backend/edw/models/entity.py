# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import re
import six
import math

from six import python_2_unicode_compatible
from functools import reduce
from operator import __or__ as OR

from typing import (
    Union,
    Type,
    Iterable,
)
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from django.core.cache import cache
from django.core.exceptions import (
    FieldDoesNotExist,
    ObjectDoesNotExist,
    MultipleObjectsReturned
)
from django.db import models, transaction, connections
from django.db.models import (
    Q,
    Count,
    Max,
    OuterRef,
    Subquery,
    Exists,
    # QuerySet
)
try:
    from django.db.models.sql.datastructures import EmptyResultSet
except ImportError:
    from django.core.exceptions import EmptyResultSet

from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.functional import cached_property, lazy
from django.utils.translation import get_language_from_request
from django.utils.translation import ugettext_lazy as _
from ipware import ip
from polymorphic.base import PolymorphicModelBase
try:  # six.PY2
    from polymorphic.manager import PolymorphicManager
except ImportError:
    from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel
from polymorphic.query import PolymorphicQuerySet
from rest_framework.reverse import reverse

from .sql.datastructures import CustomJoin
from .cache import add_cache_key, QuerySetCachedResultMixin
from .data_mart import DataMartModel
from .mixins.query import (
    CustomGroupByQuerySetMixin,
    CustomCountQuerySetMixin,
    JoinQuerySetMixin,
    inner_join_to,
)
from .utils import get_db_vendor
from .related import (
    AdditionalEntityCharacteristicOrMarkModel,
    EntityRelationModel,
    EntityRelatedDataMartModel
)
from .rest import RESTModelBase
from .term import TermModel
from .. import deferred
from .. import settings as edw_settings
from ..signals.entity import post_save as entity_post_save
from ..signals.entity import (
    post_add_relations,
    pre_delete_relations
)
from ..utils.circular_buffer_in_cache import RingBuffer, empty
from ..utils.hash_helpers import hash_unsorted_list
from ..utils.monkey_patching import patch_class_method
from ..utils.set_helpers import uniq


# округление в стиле python 3
if six.PY2:
    _round = round
    round = lambda x: int(_round(x))


# ==============================================================================
# get_polymorphic_ancestors_models
# ==============================================================================
def get_polymorphic_ancestors_models(ChildModel):
    """
    ENG: Inheritance chain that inherited from the PolymorphicModel include self model.
    RUS: Наследуется от PolymorphicModel, включая self.
    """
    ancestors = []
    for Model in ChildModel.mro():
        if isinstance(Model, PolymorphicModelBase):
            if not Model._meta.abstract:
                ancestors.append(Model)
    return reversed(ancestors)


# ==============================================================================
# BaseEntityQuerySet
# ==============================================================================

def _get_terms_ids(entities_qs, tree):
    """
    RUS: Возвращает список id, актуализированного согласно выборке объектов, дерева терминов.
    """
    result = getattr(entities_qs, '_terms_ids_cache', None)
    if result is None:
        result = entities_qs._terms_ids_cache = list(tree.trim(entities_qs.get_related_terms_ids(tree)).keys())
    return result


class BaseEntityQuerySet(JoinQuerySetMixin, CustomCountQuerySetMixin, CustomGroupByQuerySetMixin,
                         QuerySetCachedResultMixin, PolymorphicQuerySet):
    """
    RUS: Запрос к базовой сущности базы данных.
    """
    # SEMANTIC_FILTERS_CHUNK_LIMIT = edw_settings.SEMANTIC_FILTER['filters_chunk_limit']
    GROUP_SIZE_ALIAS = 'group_size'
    GROUP_ID_ALIAS = '__group_id'
    _JOIN_INDEX_KEY = '_join_idx'

    def group_by(self, *fields):
        """
        Возвращает результат запроса, сгруппированный по указанным полям.
        
        Создает SQL-запрос с GROUP BY, который группирует записи по указанным полям.
        Дополнительно аннотирует результат размером группы (group_size) и идентификатором группы.
        
        Args:
            *fields: Поля, по которым нужно группировать данные.
            
        Returns:
            QuerySet: Клонированный QuerySet с примененной группировкой.
        """
        group_by_annotation = {
            self.GROUP_SIZE_ALIAS: Count('id'),
            self.GROUP_ID_ALIAS: Max('id')
        }

        pk_alias = self.model._meta.pk.get_attname_column()[1]

        result = self._clone() # clone query

        # TODO: оптимизировать запрос за счёт удаления лишних JOIN'ов
        custom_joins = {alias for alias, table in result.query.alias_map.items() if (
            isinstance(table, CustomJoin) and table.join_field.related_model._meta.db_table != alias)}
        # delete custom joins from result query, it already contains in inner joins
        for alias in custom_joins:
            del result.query.alias_map[alias]

        # delete where case from result query
        result.query.where.children = []

        # make inner query
        base_qs = self.annotate(**group_by_annotation).values(*group_by_annotation.keys())
        base_qs.query.group_by = fields

        try:
            base_raw_sql, sql_params = base_qs.query.get_compiler(self.db).as_sql()
        except EmptyResultSet:
            result = []
        else:
            idx = getattr(self.query, self._JOIN_INDEX_KEY, 1)

            model = base_qs.model
            table = base_qs.query.get_initial_alias()

            # Make safe names
            db_ops = connections[self.db].ops
            qn = db_ops.quote_name
            safe_table, sk_alias = [
                qn(x) for x in (table, self.GROUP_ID_ALIAS)
            ]

            # Aliases for inner subquery and nested first table
            s = model._meta.object_name.upper()
            table_alias = "{}{}".format(s, idx)
            join_alias = "{}_IJ{}".format(s, idx)

            # Black magic, transform queryset
            regex = re.compile("(.+?\s+FROM\s+){}(\s+)".format(
                safe_table), re.IGNORECASE)

            raw_sql = regex.sub(r'\1{} AS {}\2'.format( safe_table, table_alias
            ), base_raw_sql, 1).replace('{}.'.format(safe_table), '{}.'.format(table_alias))

            # Make inner queryset
            inner_qs = model.objects.raw(raw_sql, sql_params)

            # Make queryset
            result = result.inner_join(inner_qs, pk_alias, sk_alias, join_alias)

            # Add annotation
            result.query.extra = {self.GROUP_SIZE_ALIAS: (qn(self.GROUP_SIZE_ALIAS), [])}

            # Add join index for future
            setattr(result.query, self._JOIN_INDEX_KEY, idx + 1)

        return result

    def alike(self, pk, *fields):
        """
        Возвращает объекты с такими же значениями полей, как у объекта с указанным primary key.
        
        Args:
            pk: Первичный ключ объекта, подобные которому нужно найти.
            *fields: Поля, по которым проверяется совпадение.
            
        Returns:
            QuerySet: Отфильтрованный QuerySet с объектами, у которых значения указанных полей 
                     совпадают со значениями у исходного объекта.
        """
        try:
            alike = self.values(*fields).filter(pk=pk)[0]
        except IndexError:
            return self.none()
        return self.filter(**alike)

    @add_cache_key('actv')
    def active(self):
        """
        Возвращает только активные объекты.
        
        Фильтрует QuerySet, оставляя только записи со значением active=True.
        Результат кэшируется с ключом 'actv'.
        
        Returns:
            QuerySet: QuerySet, содержащий только активные объекты.
        """
        return self.filter(active=True)

    @add_cache_key('unactv')
    def unactive(self):
        """
        Возвращает только неактивные объекты.
        
        Фильтрует QuerySet, оставляя только записи со значением active=False.
        Результат кэшируется с ключом 'unactv'.
        
        Returns:
            QuerySet: QuerySet, содержащий только неактивные объекты.
        """
        return self.filter(active=False)

    @add_cache_key('sf')  # Add dummy key, not for caching. Use `result.semantic_filter_meta` if needed
    def semantic_filter(self, value, use_cached_decompress=False, field_name='term', fix_it=False, trim_ids=None):
        """
        Применяет семантическую фильтрацию к QuerySet на основе древовидной структуры терминов.
        
        Декомпрессирует значение в дерево терминов и строит фильтры на основе семантических правил.
        Результат может быть кэширован и обрезан при необходимости.
        
        Args:
            value: Значение для декомпрессии в дерево терминов.
            use_cached_decompress: Использовать ли кэшированную декомпрессию.
            field_name: Имя поля для фильтрации.
            fix_it: Исправлять ли дерево терминов при декомпрессии.
            trim_ids: Список ID для обрезки дерева терминов.
            
        Returns:
            QuerySet: Отфильтрованный QuerySet согласно семантическим правилам.
        """
        decompress = TermModel.cached_decompress if use_cached_decompress else TermModel.decompress
        tree = decompress(value, fix_it)
        if trim_ids is not None:
            # "обрезаем" дерево в случаи необходимости
            tree = tree.soft_trim(trim_ids)
        result = self
        # формируем фильтры
        filters = tree.root.term.make_filters(term_info=tree.root, field_name=field_name)
        filters_cnt = len(filters)
        if filters_cnt:
            # save semantic filters flag for future use
            setattr(tree, '_has_semantic_filters', True)
            """
            # Pythonic, but working to slow, try refactor queryset
            filters = tree.root.term.make_filters(term_info=tree.root, field_name='terms')
            result = self.filter(filters[0])
            for x in filters[1:]:
                result = result.filter(x)
            result = result.distinct()
            """
            inner_model = self.model.terms.through
            base_qs = inner_model.objects.values('entity')
            for x in filters:
                subquery = base_qs.filter(entity=OuterRef('pk')).filter(x)
                result = result.filter(Exists(Subquery(subquery[:1])))

            # Old code, for history
            #
            # base_model = next(get_polymorphic_ancestors_models(self.model))
            # pk_alias = self.model._meta.pk.get_attname_column()[1]
            #
            # # формируем пачки из фильтров, это позволяет СУБД формировать более оптимальный план запроса
            # j = i = filters_cnt / ceil(filters_cnt / self.SEMANTIC_FILTERS_CHUNK_LIMIT)
            # chunked_filters = []
            # start = 0
            # while j < filters_cnt:
            #     stop = round(j)
            #     chunked_filters.append(filters[start:stop])
            #     j += i
            #     start = stop
            # chunked_filters.append(filters[start:])
            #
            # # формируем запрос
            # for filters_chunk in chunked_filters:
            #     base_qs = base_model.objects.all().filter(filters_chunk[0])
            #     for x in filters_chunk[1:]:
            #         base_qs = base_qs.filter(x)
            #
            #     base_qs = base_qs.distinct().values_list('id', flat=True)
            #
            #     try:
            #         base_raw_sql, sql_params = base_qs.query.get_compiler(self.db).as_sql()
            #     except EmptyResultSet:
            #         result = []
            #     else:
            #         idx = getattr(result.query, self._JOIN_INDEX_KEY, 1)
            #
            #         inner_model = getattr(base_qs.model, field_name).through
            #         outer_table = base_qs.query.get_initial_alias()
            #         inner_table = inner_model.objects.all().query.get_initial_alias()
            #
            #         entity_alias = "{}_id".format(base_model._meta.object_name.lower())
            #
            #         # Make safe names
            #         db_ops = connections[self.db].ops
            #         qn = db_ops.quote_name
            #         safe_inner_table, safe_outer_table, safe_entity_alias = [
            #             qn(x) for x in (inner_table, outer_table, entity_alias)
            #         ]
            #
            #         # Aliases for inner subquery and nested first table
            #         sk_alias = qn("sk{}".format(idx))
            #         s = inner_model._meta.object_name.upper()
            #         inner_table_alias = "{}{}".format(s, idx)
            #         join_alias = "{}_IJ{}".format(s, idx)
            #
            #         # Black magic, transform queryset
            #         regex = re.compile("{}.+?(\s+FROM\s+){}(.+?)INNER\s+JOIN\s+{}\s+ON.+?\)\s*".format(
            #             safe_outer_table, safe_outer_table, safe_inner_table), re.IGNORECASE)
            #         raw_sql = regex.sub(r'{}.{} AS {}\1{} AS {}\2'.format(
            #             inner_table_alias, safe_entity_alias, sk_alias, safe_inner_table, inner_table_alias
            #         ), base_raw_sql, 1).replace(
            #             '{}.{}'.format(safe_outer_table, qn("id")), '{}.{}'.format(inner_table_alias, safe_entity_alias)
            #         ).replace('{}.'.format(safe_inner_table), '{}.'.format(inner_table_alias))
            #
            #         # Make inner queryset
            #         inner_qs = inner_model.objects.raw(raw_sql, sql_params)
            #
            #         # cursor = connection.cursor()
            #         # cursor.execute("{} LIMIT {}".format(raw_sql, self.SEMANTIC_FILTER_FAST_SUBQUERY_RESULTS_LIMIT),
            #         #                sql_params)
            #         # ids = [item[0] for item in cursor.fetchall()]
            #         # ids_cnt = len(ids)
            #         # if ids_cnt < self.SEMANTIC_FILTER_FAST_SUBQUERY_RESULTS_LIMIT:
            #         #     result = result.filter(id__in=ids) if ids_cnt else self.filter(id=None)
            #         # else:
            #         #     result = result.inner_join(inner_qs, pk_alias, sk_alias, join_alias)
            #
            #         # Make queryset
            #         result = result.inner_join(inner_qs, pk_alias, sk_alias, join_alias)
            #
            #         setattr(result.query, self._JOIN_INDEX_KEY, idx + 1)

        result.semantic_filter_meta = tree
        return result

    def force_index(self, index_name=None):
        """
        Принудительно использует указанный индекс в SQL-запросе для MySQL.
        
        Модифицирует SQL-запрос, добавляя USE INDEX для оптимизации производительности запроса.
        Работает только для MySQL, для других СУБД возвращает неизмененный QuerySet.
        
        Args:
            index_name: Имя индекса для использования. По умолчанию 'PRIMARY'.
            
        Returns:
            QuerySet: QuerySet с принудительным использованием индекса (для MySQL) 
                     или исходный QuerySet (для других СУБД).
        """
        vendor = get_db_vendor()
        if vendor == 'mysql':
            try:
                base_raw_sql, sql_params = self.query.get_compiler(self.db).as_sql()
            except EmptyResultSet:
                result = self
            else:
                # Для MySQL: USE INDEX
                # FORCE INDEX is going to be deprecated after MySQL 8
                if index_name is None:
                    index_name = 'PRIMARY'

                # Make safe names
                db_ops = connections[self.db].ops
                qn = db_ops.quote_name

                safe_table = qn(self.model._meta.db_table)

                # Black magic, transform queryset
                regex = re.compile("({}.+?\s+FROM\s+{})(.*?)".format(safe_table, safe_table), re.IGNORECASE)

                raw_sql = regex.sub(r'\1 USE INDEX ({})\2'.format(
                            index_name,
                        ), base_raw_sql, 1)

                # Make queryset
                result = self.model.objects.raw(raw_sql, sql_params)
            return result

        # elif vendor == 'postgresql':
        #     # Для PostgreSQL: pg_hint_plan через комментарий - /*+ IndexScan(myapp_mymodel my_custom_index) */
        #     return self......

        return self  # Для других СУБД игнорируем

    def get_related_terms_ids(self, tree=None, min_limit=10000, limit_log_base=10):
        """
        Возвращает список ID связанных терминов для объектов в QuerySet.
        
        Выполняет SQL-запрос к реляционным данным, оптимизированный для
        больших наборов данных с использованием INNER JOIN.
        
        Args:
            tree: Дерево терминов для определения границ выборки.
            min_limit: Минимальное количество объектов для применения ограничения запроса.
            limit_log_base: База логарифма для расчета размера страницы при ограничении.
            
        Returns:
            list: Список ID связанных терминов.
        """
        # try find related terms boundary ids
        has_semantic_filters = getattr(tree, '_has_semantic_filters', False) if tree else False
        terms_boundary_ids = set(tree.expand().keys()) if has_semantic_filters else set()

        # `_count` - sets early in `edw.rest.serializers.entity.EntitySummaryMetadataSerializer.get_potential_terms_ids`
        count = getattr(self, '_count', None)
        if count is not None and count > min_limit:
            limit = round(count / math.log(count, limit_log_base))
            i = count // limit
        else:
            limit = 0
            i = 1

        outer_model = self.model.terms.through
        inner_model_name = self.model._meta.object_name

        idx = getattr(self.query, self._JOIN_INDEX_KEY, 1)

        last_id = None
        result = set()
        offset = 0

        with transaction.atomic():
            for j in range(1, i + 1):
                entities_ids, terms_ids = set(), set()

                inner_qs = self.order_by('id').values_list('pk', flat=True)

                if last_id is not None:
                    inner_qs = inner_qs.filter(id__gt=last_id)

                if limit and i != j:
                    inner_qs = inner_qs[offset:offset + limit]

                # use index for maximum performance
                inner_qs = inner_qs.force_index()

                join_alias = "{}_IJ{}".format(inner_model_name.upper(), idx)
                entity_alias = "{}_id".format(inner_model_name.lower())

                outer_qs = outer_model.objects.values_list('term_id').annotate(last_id=Max("entity_id"))

                # Make "slow" queryset
                result_qs = inner_join_to(outer_qs, inner_qs, entity_alias, 'id', join_alias)

                if terms_boundary_ids:
                    # Make "little fast" queryset
                    result_qs = result_qs.filter(term__in=terms_boundary_ids)
                elif result:
                    result_qs = result_qs.exclude(term__in=result)

                # split result
                [(terms_ids.add(x), entities_ids.add(y)) for x, y in result_qs]

                if entities_ids:
                    last_id = max(entities_ids)
                    offset = 0
                else:
                    offset += limit
                    continue

                terms_boundary_ids -= terms_ids
                result.update(terms_ids)

        return list(result)

    def _get_terms_ids_cache_key(self, tree):
        """
        Создает ключ кэширования для дерева терминов.
        
        Формирует уникальный ключ кэша на основе хэша дерева терминов.
        
        Args:
            tree: Дерево терминов.
            
        Returns:
            str: Ключ кэша для хранения ID терминов.
        """
        return self.model.TERMS_IDS_CACHE_KEY_PATTERN.format(tree_hash=tree.get_hash())

    @add_cache_key(_get_terms_ids_cache_key)
    def get_terms_ids(self, tree):
        """
        Возвращает список ID терминов для текущего QuerySet с учетом дерева терминов.
        
        Использует отложенное вычисление и кэширование результата.
        
        Args:
            tree: Дерево терминов для фильтрации.
            
        Returns:
            list: Кэшированный список ID терминов.
        """
        # отложенное вычисление
        result = lazy(_get_terms_ids, list)(self, tree)
        # примиксовываем вычислитель кэша
        result.__class__ = type(str('LazyQuerySetCachedResult'), (QuerySetCachedResultMixin, result.__class__), {})
        return result

    def get_similar(self, value, use_cached_decompress=False, fix_it=False, many=False):
        """
        Находит объекты, семантически похожие на заданные параметры.
        
        Ищет объекты в QuerySet, которые максимально похожи по сходству терминов,
        без учета семантических правил.
        
        Args:
            value: Список ID терминов для поиска похожих объектов.
            use_cached_decompress: Использовать ли кэшированную декомпрессию.
            fix_it: Исправлять ли дерево терминов при декомпрессии.
            many: Возвращать ли список похожих объектов (True) или только первый (False).
            
        Returns:
            Entity/list/None: Похожий объект, список похожих объектов или None, если ничего не найдено.
        """
        ids = TermModel.get_all_active_root_ids(use_cache=use_cached_decompress)
        ids.extend(value)
        decompress = TermModel.cached_decompress if use_cached_decompress else TermModel.decompress
        terms_tree = decompress(ids, fix_it=fix_it)
        lvl_expr = 'terms__{}'.format(TermModel._mptt_meta.level_attr)
        similar_entities_ids = self.values_list('id', flat=True)
        similar_entities = EntityModel.objects.filter(
            models.Q(id__in=similar_entities_ids) & models.Q(terms__id__in=list(terms_tree.keys()))
        ).annotate(
            num=models.Count('terms__id'),
            avg_lvl=models.Avg(lvl_expr),
            max_lvl=models.Max(lvl_expr)
        ).order_by('-num', '-avg_lvl', '-max_lvl', 'created_at')
        try:
            result = similar_entities[0]
        except IndexError:
            result = [] if many else None
        else:
            if many:
                result = [result] + list(similar_entities.filter(
                    num=result.num,
                    avg_lvl=result.avg_lvl,
                    max_lvl=result.max_lvl
                ).order_by('created_at')[1:])
        return result

    def _get_subj_cache_key(self, subj_ids):
        """
        Формирует ключ кэша для фильтрации по субъектам.
        
        Args:
            subj_ids: Список ID субъектов.
            
        Returns:
            str: Ключ кэша для фильтрации по субъектам.
        """
        return self.model.SUBJECT_CACHE_KEY_PATTERN.format(subj_hash=(hash_unsorted_list(subj_ids) if subj_ids else ''))

    def _alias_is_true_or_reducer(self, aliases):
        """
        Создает и применяет фильтр на основе OR-объединения нескольких полей-псевдонимов.
        
        Метод используется внутренними методами фильтрации для создания эффективных запросов
        с использованием псевдонимов и объединения их через OR.
        
        Args:
            aliases: Словарь псевдонимов для аннотирования.
            
        Returns:
            QuerySet: Отфильтрованный QuerySet с примененным OR-редуктором.
        """
        q_lst = []
        aliases_keys = aliases.keys()
        for key in aliases_keys:
            q_lst.append(models.Q(**{key: True}))
        qs = self.alias(**aliases).filter(reduce(OR, q_lst))
        for key in aliases_keys:
            del qs.query.annotations[key]
        return qs

    @add_cache_key(_get_subj_cache_key)
    def subj(self, subj_ids):
        """
        Фильтрует объекты, связанные с указанными субъектами.
        
        Находит объекты, которые имеют прямые или обратные связи с указанными субъектами.
        Результат кэшируется.
        
        Args:
            subj_ids: Список ID субъектов для фильтрации.
            
        Returns:
            QuerySet: Отфильтрованный QuerySet объектов, связанных с субъектами.
        """
        base_manager = EntityRelationModel.objects
        forward_relations = base_manager.values('from_entity').filter(from_entity=OuterRef('pk')).filter(to_entity__in=subj_ids)
        backward_relations = base_manager.values('to_entity').filter(to_entity=OuterRef('pk')).filter(from_entity__in=subj_ids)
        aliases = {
            'exist_forward': Exists(Subquery(forward_relations[:1])),
            'exist_backward': Exists(Subquery(backward_relations[:1]))
        }
        qs = self._alias_is_true_or_reducer(aliases)
        '''
        # Pythonic, but working to slow, try refactor queryset ^
        q_lst = [models.Q(models.Q(forward_relations__to_entity__in=subj_ids)),
                 models.Q(backward_relations__from_entity__in=subj_ids)]
        qs = self.filter(reduce(OR, q_lst)).distinct()
        '''
        return qs

    def _get_rel_cache_key(self, rel_f_ids, rel_r_ids):
        """
        Формирует ключ кэша для фильтрации по связям.
        
        Args:
            rel_f_ids: Список ID прямых связей.
            rel_r_ids: Список ID обратных связей.
            
        Returns:
            str: Ключ кэша для фильтрации по связям.
        """
        _hash = "{rel_f_ids}:{rel_r_ids}".format(
            rel_f_ids=hash_unsorted_list(rel_f_ids) if rel_f_ids else '',
            rel_r_ids=hash_unsorted_list(rel_r_ids) if rel_r_ids else ''
        )
        return self.model.RELATION_CACHE_KEY_PATTERN.format(rel_hash=_hash)

    @add_cache_key(_get_rel_cache_key)
    def rel(self, rel_f_ids, rel_r_ids):
        """
        Фильтрует объекты на основе прямых и обратных связей.
        
        Находит объекты, которые имеют указанные типы прямых или обратных связей.
        Результат кэшируется.
        
        Args:
            rel_f_ids: Список ID прямых связей для фильтрации.
            rel_r_ids: Список ID обратных связей для фильтрации.
            
        Returns:
            QuerySet: Отфильтрованный QuerySet объектов с указанными связями.
        """
        base_manager = EntityRelationModel.objects
        aliases = {}
        if rel_f_ids:
            forward_relations = base_manager.values('from_entity').filter(from_entity=OuterRef('pk')).filter(term__in=rel_f_ids)
            aliases['exist_forward'] = Exists(Subquery(forward_relations[:1]))
        if rel_r_ids:
            backward_relations = base_manager.values('to_entity').filter(to_entity=OuterRef('pk')).filter(term__in=rel_r_ids)
            aliases['exist_backward'] = Exists(Subquery(backward_relations[:1]))
        qs = self._alias_is_true_or_reducer(aliases)
        '''
        # Pythonic, but working to slow, try refactor queryset ^
        q_lst = []
        if rel_f_ids:
            q_lst.append(models.Q(forward_relations__term__in=rel_f_ids))
        if rel_r_ids:
            q_lst.append(models.Q(backward_relations__term__in=rel_r_ids))
        qs = self.filter(reduce(OR, q_lst)).distinct()
        # print(qs.query.__str__())
        '''
        return qs

    def _get_subj_and_rel_cache_key(self, subj, *rel_ids):
        """
        Формирует ключ кэша для фильтрации по субъектам и связям.
        
        Args:
            subj: Список ID субъектов или словарь {relation_id: [subjects_ids]}.
            *rel_ids: Списки ID прямых и обратных связей.
            
        Returns:
            str: Ключ кэша для фильтрации по субъектам и связям.
        """
        if isinstance(subj, (tuple, list)):
            subj_key=self._get_subj_cache_key(subj),
        else:
            subj_key = self.model.SUBJECT_CACHE_KEY_PATTERN.format(subj_hash=",".join(["{}.{}".format(
                rel_id, hash_unsorted_list(subj_ids) if subj_ids else '') for rel_id, subj_ids in sorted(subj.items())]))
        return "{subj_key}:{rel_key}".format(
            subj_key=subj_key,
            rel_key=self._get_rel_cache_key(*rel_ids)
        )

    @add_cache_key(_get_subj_and_rel_cache_key)
    def subj_and_rel(self, subj, rel_f_ids, rel_r_ids):
        """
        Фильтрует объекты на основе субъектов и их связей.
        
        Находит объекты, которые связаны с указанными субъектами определенными типами связей.
        Позволяет указать разные субъекты для разных типов связей.
        
        Args:
            subj: Список ID субъектов или словарь {relation_id: [subjects_ids]}.
            rel_f_ids: Список ID прямых связей для фильтрации.
            rel_r_ids: Список ID обратных связей для фильтрации.
            
        Returns:
            QuerySet: Отфильтрованный QuerySet объектов с указанными связями с субъектами.
        """
        base_manager = EntityRelationModel.objects
        aliases = {}
        if isinstance(subj, (tuple, list)):
            # субъекты представлены списком для прямых и обратных связей, он общий для всех связей
            if rel_f_ids:
                forward_relations = base_manager.values('from_entity').filter(from_entity=OuterRef('pk')).filter(
                    to_entity__in=subj, term__in=rel_f_ids)
                aliases['exist_forward'] = Exists(Subquery(forward_relations[:1]))
            if rel_r_ids:
                backward_relations = base_manager.values('to_entity').filter(to_entity=OuterRef('pk')).filter(
                    from_entity__in=subj, term__in=rel_r_ids)
                aliases['exist_backward'] = Exists(Subquery(backward_relations[:1]))
        else:
            # отдельные списки под каждый вид связей
            i = -1
            for i, rel_id in enumerate(rel_f_ids):
                subj_ids = subj[rel_id]
                if subj_ids:
                    forward_relation = base_manager.values('from_entity').filter(from_entity=OuterRef('pk')).filter(
                        to_entity__in=subj_ids, term=rel_id)
                    aliases[f"exist_forward_{i}"] = Exists(Subquery(forward_relation[:1]))
                else:
                    backward_relation = base_manager.values('to_entity').filter(to_entity=OuterRef('pk')).filter(
                        term=rel_id)
                    aliases[f"exist_backward_{i}"] = Exists(Subquery(backward_relation[:1]))
            for i, rel_id in enumerate(rel_r_ids, start=i + 1):
                subj_ids = subj[rel_id]
                if subj_ids:
                    backward_relation = base_manager.values('to_entity').filter(to_entity=OuterRef('pk')).filter(
                        from_entity__in=subj_ids, term=rel_id)
                    aliases[f"exist_backward_{i}"] = Exists(Subquery(backward_relation[:1]))
                else:
                    forward_relation = base_manager.values('from_entity').filter(from_entity=OuterRef('pk')).filter(
                        term=rel_id)
                    aliases[f"exist_forward_{i}"] = Exists(Subquery(forward_relation[:1]))
        qs = self._alias_is_true_or_reducer(aliases)

        '''
        # Pythonic, but working to slow, try refactor queryset ^
        q_lst = []
        if isinstance(subj, (tuple, list)):
            # субъекты представлены списком для прямых и обратных связей. он общий для всех связей
            if rel_f_ids:
                q_lst.append(models.Q(forward_relations__to_entity__in=subj) &
                             models.Q(forward_relations__term__in=rel_f_ids))
            if rel_r_ids:
                q_lst.append(models.Q(backward_relations__from_entity__in=subj) &
                             models.Q(backward_relations__term__in=rel_r_ids))
        else:
            # отдельные списки под каждый вид связей
            for rel_id in rel_f_ids:
                subj_ids = subj[rel_id]
                if subj_ids:
                    q_lst.append(models.Q(forward_relations__to_entity__in=subj_ids) &
                                 models.Q(forward_relations__term=rel_id))
                else:
                    q_lst.append(models.Q(backward_relations__term=rel_id))
            for rel_id in rel_r_ids:
                subj_ids = subj[rel_id]
                if subj_ids:
                    q_lst.append(models.Q(backward_relations__from_entity__in=subj_ids) &
                                 models.Q(backward_relations__term=rel_id))
                else:
                    q_lst.append(models.Q(forward_relations__term=rel_id))

        qs = self.filter(reduce(OR, q_lst)).distinct()
        # print(qs.query.__str__())
        '''
        return qs

    @cached_property
    def ids(self):
        """
        Возвращает список ID всех объектов в QuerySet.
        
        Returns:
            list: Список идентификаторов объектов.
        """
        return list(self.values_list('id', flat=True))

    @cached_property
    def additional_characteristics(self):
        """
        Возвращает дополнительные характеристики текущей сущности.
        
        Метод получает из базы данных все дополнительные характеристики, связанные с текущей сущностью.
        Характеристики фильтруются по признаку is_characteristic в атрибутах термина и сортируются 
        в соответствии с древовидной структурой терминов.
        
        Returns:
            QuerySet: Набор объектов AdditionalEntityCharacteristicOrMarkModel, представляющих
                     дополнительные характеристики сущности.
        """
        tree_opts = TermModel._mptt_meta
        return AdditionalEntityCharacteristicOrMarkModel.objects.filter(
            entity_id__in=self.ids, term__attributes=TermModel.attributes.is_characteristic).order_by(
            'term__{}'.format(tree_opts.tree_id_attr), 'term__{}'.format(tree_opts.left_attr))

    @cached_property
    def additional_marks(self):
        """
        Возвращает дополнительные метки текущей сущности.
        
        Метод получает из базы данных все дополнительные метки, связанные с текущей сущностью.
        Метки фильтруются по признаку is_mark в атрибутах термина и сортируются 
        в соответствии с древовидной структурой терминов.
        
        Returns:
            QuerySet: Набор объектов AdditionalEntityCharacteristicOrMarkModel, представляющих
                     дополнительные метки сущности.
        """
        tree_opts = TermModel._mptt_meta
        return AdditionalEntityCharacteristicOrMarkModel.objects.filter(
            entity_id__in=self.ids, term__attributes=TermModel.attributes.is_mark).order_by(
            'term__{}'.format(tree_opts.tree_id_attr), 'term__{}'.format(tree_opts.left_attr))

    @cached_property
    def _active_terms_for_characteristics(self):
        """
        Возвращает активные термины для характеристик текущей сущности.
        
        Получает список активных терминов, которые являются характеристиками
        и связаны с данной сущностью.
        
        Returns:
            list: Список терминов-характеристик, связанных с сущностью.
        """
        tree_opts = TermModel._mptt_meta
        descendants_ids = TermModel.get_all_active_characteristics_descendants_ids()
        return list(TermModel.objects.filter(entities__id__in=self.ids, id__in=descendants_ids).distinct().order_by(
            tree_opts.tree_id_attr, tree_opts.left_attr))

    @cached_property
    def _active_terms_for_marks(self):
        """
        Возвращает активные термины для меток текущей сущности.
        
        Получает список активных терминов, которые являются метками
        и связаны с данной сущностью.
        
        Returns:
            list: Список терминов-меток, связанных с сущностью.
        """
        tree_opts = TermModel._mptt_meta
        descendants_ids = TermModel.get_all_active_marks_descendants_ids()
        return list(TermModel.objects.filter(entities__id__in=self.ids, id__in=descendants_ids).distinct().order_by(
            tree_opts.tree_id_attr, tree_opts.left_attr))

    @cached_property
    def characteristics_getter(self):
        """
        Возвращает объект для получения характеристик объектов в QuerySet.
        
        Создает и настраивает экземпляр EntityCharacteristicOrMarkGetter для
        получения характеристик объектов.
        
        Returns:
            EntityCharacteristicOrMarkGetter: Объект для получения характеристик.
        """
        tree_opts = TermModel._mptt_meta
        return EntityCharacteristicOrMarkGetter(
            self._active_terms_for_characteristics,
            self.additional_characteristics,
            TermModel.attributes.is_characteristic,
            tree_opts,
            attributes_ancestors_local_cache=getattr(self, 'attributes_ancestors_local_cache', None)
        )

    @cached_property
    def characteristics(self):
        """
        Возвращает все характеристики объектов в QuerySet.
        
        Returns:
            list: Полный список характеристик для объектов.
        """
        return self.characteristics_getter.all()

    @cached_property
    def short_characteristics(self):
        """
        Возвращает сокращенный список характеристик объектов в QuerySet.
        
        Ограничивает количество характеристик до максимального значения,
        определенного в модели.
        
        Returns:
            list: Сокращенный список характеристик для объектов.
        """
        return self.characteristics_getter[:self.model.SHORT_CHARACTERISTICS_MAX_COUNT]

    @cached_property
    def marks_getter(self):
        """
        Возвращает объект для получения меток объектов в QuerySet.
        
        Создает и настраивает экземпляр EntityCharacteristicOrMarkGetter для
        получения меток объектов.
        
        Returns:
            EntityCharacteristicOrMarkGetter: Объект для получения меток.
        """
        tree_opts = TermModel._mptt_meta
        return EntityCharacteristicOrMarkGetter(
            self._active_terms_for_marks,
            self.additional_marks,
            TermModel.attributes.is_mark,
            tree_opts,
            attributes_ancestors_local_cache=getattr(self, 'attributes_ancestors_local_cache', None)
        )

    @cached_property
    def marks(self):
        """
        Возвращает все метки объектов в QuerySet.
        
        Returns:
            list: Полный список меток для объектов.
        """
        return self.marks_getter.all()

    @cached_property
    def short_marks(self):
        """
        Возвращает сокращенный список меток объектов в QuerySet.
        
        Ограничивает количество меток до максимального значения,
        определенного в модели.
        
        Returns:
            list: Сокращенный список меток для объектов.
        """
        return self.marks_getter[:self.model.SHORT_MARKS_MAX_COUNT]

    def stored_request(self, request):
        """
        Извлекает полезную информацию из запроса для эмуляции запроса Django.
        
        Сохраняет данные о языке, базовом URI, IP-адресе, User-Agent и пользователе
        для последующего использования при оффлайн-рендеринге.
        
        Args:
            request: Объект запроса Django.
            
        Returns:
            dict: Словарь с извлеченной информацией о запросе.
        """
        get_ip = getattr(ip, 'get_ip', lambda r: ip.get_client_ip(r)[0])
        return {
            'language': get_language_from_request(request),
            'absolute_base_uri': request.build_absolute_uri('/'),
            'remote_ip': get_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'username': request.user.username if request.user else None,
        }


class BaseEntityManager(PolymorphicManager.from_queryset(BaseEntityQuerySet)):
    """
    Базовый менеджер моделей для работы с сущностями EDW.
    
    Предоставляет функциональность для запросов, статистики и неманипулятивных 
    операций с сущностями. Наследуется от PolymorphicManager и использует
    BaseEntityQuerySet для расширенных возможностей запросов.
    
    Основные функции:
    - Обработка запросов к базе данных для сущностей
    - Предоставление методов для фильтрации сущностей по различным критериям
    - Поддержка полиморфных запросов для работы с разными типами сущностей
    
    Все пользовательские модели сущностей должны иметь менеджер, 
    наследуемый от этого класса.
    """
    queryset_class = BaseEntityQuerySet

    '''
    def select_lookup(self, search_term):
        """
        Returning a queryset containing the objects matching the declared lookup fields together
        with the given search term. Each object can define its own lookup fields using the
        member list or tuple `lookup_fields`.
        """
        filter_by_term = (models.Q((sf, search_term)) for sf in self.model.lookup_fields)
        queryset = self.get_queryset().filter(reduce(operator.or_, filter_by_term))
        return queryset
    '''

    def indexable(self):
        """
        Возвращает QuerySet активных сущностей, доступных для индексации.
        
        Метод используется поисковыми системами и другими компонентами,
        которым требуется индексировать только активные объекты.
        
        Returns:
            QuerySet: QuerySet, содержащий только активные сущности.
        """
        return self.active()


class PolymorphicEntityMetaclass(deferred.PolymorphicForeignKeyBuilder, RESTModelBase):
    """
    Метакласс для полиморфных сущностей, обеспечивающий правильную материализацию моделей.
    
    Назначение:
    - Создает связь между полиморфными классами и их материализованными моделями
    - Обеспечивает корректную работу с моделями при полиморфном наследовании
    - Выполняет проверки безопасности для создаваемых сущностей
    
    Принцип работы:
    Поскольку полиморфные классы объектов обычно материализуются несколькими моделями,
    данный метакласс находит наиболее общую модель и связывает её MaterializedModel
    с соответствующими классами. Это позволяет, например, получить все доступные
    объекты из базы данных через EntityModel.objects.all().
    
    Пример:
        EntityModel.objects.all() - возвращает все доступные объекты из EDW,
        благодаря правильной материализации моделей через этот метакласс.
    """

    @classmethod
    def perform_model_checks(cls, Model):
        """
        Выполняет проверки безопасности и корректности для создаваемой модели сущности.
        
        Метод проверяет, что модель сущности соответствует всем требованиям:
        1. Объект manager (objects) должен быть наследником BaseEntityManager
        2. Модель должна иметь атрибут или свойство entity_name
        3. Модель должна иметь все обязательные поля, указанные в REQUIRED_FIELDS 
           в каждом из абстрактных базовых классов
        
        Args:
            Model: Класс модели для проверки
            
        Raises:
            NotImplementedError: Если модель не соответствует требованиям безопасности или
                                 не реализует необходимые поля и методы
        """
        if not isinstance(Model.objects, BaseEntityManager):
            msg = "Class `{}.objects` must provide ModelManager inheriting from BaseEntityManager"
            raise NotImplementedError(msg.format(Model.__name__))

        """
        if not isinstance(getattr(Model, 'lookup_fields', None), (list, tuple)):
            msg = "Class `{}` must provide a tuple of `lookup_fields` so that we can easily lookup for Entities"
            raise NotImplementedError(msg.format(Model.__name__))
        """

        try:
            Model().entity_name
        except AttributeError:
            msg = "Class `{}` must provide a model field or property implementing `entity_name`"
            raise NotImplementedError(msg.format(Model.__name__))

        for baseclass in Model.mro():
            if not isinstance(baseclass, PolymorphicModelBase) or baseclass._meta.abstract:
                required_fields = getattr(baseclass, 'REQUIRED_FIELDS', None)
                if required_fields is not None:
                    for required_field in required_fields:
                        try:
                            Model._meta.get_field(required_field)
                        except FieldDoesNotExist:
                            msg = "Class `{}` must provide a model field `{}`"
                            raise NotImplementedError(msg.format(Model.__name__, required_field))

        # if not callable(getattr(Model, 'get_some_data', None)):
        #    msg = "Class `{}` must provide a method implementing `get_some_data(request)`"
        #    raise NotImplementedError(msg.format(Model.__name__))


# ==============================================================================
# EntityCharacteristicOrMarkInfo & EntityCharacteristicOrMarkGetter cache system
# ==============================================================================
class EntityCharacteristicOrMarkInfo(object):
    """
    Класс для хранения и обработки информации о характеристиках или метках сущности.
    
    Представляет собой контейнер для хранения структурированной информации 
    о характеристиках или метках сущности, включая название, путь в дереве терминов,
    значения и представления.
    
    Attributes:
        name: Название характеристики или метки.
        path: Путь в дереве терминов.
        values: Список значений характеристики или метки.
        view_class: Список классов представления.
        tree_id: Идентификатор дерева терминов.
        tree_left: Левая граница в дереве терминов (для MPTT).
    """

    def __init__(self, name, path, values, view_class, tree_id, tree_left):
        """
        Инициализирует объект характеристики или метки сущности.
        
        Args:
            name: Название характеристики/метки.
            path: Путь в иерархии терминов.
            values: Список значений характеристики/метки.
            view_class: Список классов представления для UI.
            tree_id: Идентификатор дерева для MPTT.
            tree_left: Левая граница в дереве MPTT для сортировки.
        """
        self.name = name
        self.path = path
        self.values = values
        self.view_class = view_class
        self.tree_id = tree_id
        self.tree_left = tree_left

    def __lt__(self, other):
        """
        Сравнивает два объекта для сортировки по дереву MPTT.
        
        Сравнение происходит сначала по tree_id, а затем по tree_left,
        что соответствует порядку обхода дерева MPTT.
        
        Args:
            other: Другой объект EntityCharacteristicOrMarkInfo для сравнения.
            
        Returns:
            bool: True, если текущий объект должен быть размещен перед other.
        """
        if self.tree_id == other.tree_id:
            return self.tree_left < other.tree_left
        else:
            return self.tree_id < other.tree_id

    def __eq__(self, other):
        """
        Проверяет равенство двух объектов по их позиции в дереве MPTT.
        
        Args:
            other: Другой объект EntityCharacteristicOrMarkInfo для сравнения.
            
        Returns:
            bool: True, если объекты находятся в одной позиции дерева.
        """
        return self.tree_id == other.tree_id and self.tree_left == other.tree_left

    def __repr__(self):
        """
        Возвращает строковое представление объекта.
        
        Представляет объект в виде кортежа (name, values) для отладки и логирования.
        
        Returns:
            str: Строковое представление объекта.
        """
        return repr((self.name, self.values))

    def view_class_findall(self, pattern):
        """
        Ищет совпадения в массиве классов представления по регулярному выражению.
        
        Метод перебирает все классы представления и находит в них фрагменты,
        соответствующие заданному регулярному выражению.
        
        Args:
            pattern: Регулярное выражение для поиска в классах представления.
            
        Returns:
            list: Список найденных совпадений.
        """
        result = []
        for x in self.view_class:
            result += re.findall(pattern, x)
        return result


class EntityCharacteristicOrMarkGetter(object):
    """
    Класс для ленивого получения и кэширования характеристик или меток сущности.
    
    Обеспечивает эффективное извлечение характеристик или меток сущности из базы данных
    с использованием стратегии ленивой загрузки и кэширования. Позволяет получать
    данные в ограниченном количестве и использовать индексирование для доступа.
    
    Особенности:
    - Кэширование результатов для повторного использования
    - Поддержка ограничения количества возвращаемых элементов
    - Извлечение данных из базовых терминов и дополнительных характеристик/меток
    - Поддержка индексации и срезов для удобного доступа
    
    Attributes:
        terms: Список терминов для обработки.
        additional_characteristics_or_marks: Дополнительные характеристики или метки.
        attribute_mode: Режим атрибута (характеристика или метка).
        tree_opts: Параметры дерева терминов для MPTT.
        _result_cache: Кэш результатов для разных ограничений.
        attributes_ancestors_local_cache: Локальный кэш предков атрибутов.
    """
    def __init__(self, terms, additional_characteristics_or_marks, attribute_mode, tree_opts,
                 attributes_ancestors_local_cache=None):
        """
        Инициализирует получатель характеристик или меток сущности.
        
        Args:
            terms: Список терминов, связанных с сущностью.
            additional_characteristics_or_marks: Дополнительные характеристики или метки сущности.
            attribute_mode: Режим атрибута (TermModel.attributes.is_characteristic или 
                           TermModel.attributes.is_mark).
            tree_opts: Параметры MPTT для дерева терминов.
            attributes_ancestors_local_cache: Опциональный локальный кэш предков атрибутов.
        """
        self.terms = terms
        self.additional_characteristics_or_marks = additional_characteristics_or_marks
        self.attribute_mode = attribute_mode
        self.tree_opts = tree_opts
        self._result_cache = {}
        self.attributes_ancestors_local_cache = attributes_ancestors_local_cache

    def all(self, limit=None):
        """
        Возвращает все характеристики или метки, опционально ограниченные по количеству.
        
        Использует кэширование для оптимизации повторных запросов с одинаковым
        ограничением. При первом запросе вычисляет и кэширует результат.
        
        Args:
            limit: Максимальное количество возвращаемых элементов или None для всех.
            
        Returns:
            list: Список объектов EntityCharacteristicOrMarkInfo.
        """
        if limit not in self._result_cache:
            self._result_cache[limit] = result = self._get_attributes(limit)
        else:
            result = self._result_cache[limit]
        return result

    def __getitem__(self, k):
        """
        Обеспечивает доступ к элементам по индексу или срезу.
        
        Позволяет использовать синтаксис индексации и срезов для получения
        характеристик или меток. Преобразует индекс или срез в соответствующий
        вызов метода all() с ограничением.
        
        Args:
            k: Индекс или срез для доступа к элементам.
            
        Returns:
            object/list: Элемент или список элементов EntityCharacteristicOrMarkInfo.
            
        Raises:
            TypeError: Если k не является целым числом или срезом.
            AssertionError: Если используется отрицательное индексирование.
        """
        if not isinstance(k, (slice,) + six.integer_types):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0)) or
                (isinstance(k, slice) and (k.start is None or k.start >= 0) and
                 (k.stop is None or k.stop >= 0))), \
            "Negative indexing is not supported."
        limit = None
        if isinstance(k, slice):
            if k.stop is not None:
                limit = int(k.stop)
        return self.all(limit)[k]

    @staticmethod
    def on_attribute_ancestors_cache_set(key):
        """
        RUS: Удаляет старый ключ кэша из буфера атрибутов предков.
        """
        buf = TermModel.get_attribute_ancestors_buffer()
        old_key = buf.record(key)
        if old_key != buf.empty:
            cache.delete(old_key)

    @staticmethod
    def _get_attribute_ancestors(term, attribute_mode, local_cache):
        """
        RUS: Получает родительские термины содержащие заданный режим атрибута.
        """
        ancestors = term.get_ancestors(ascending=True, include_self=False).attribute_filter(
            attribute_mode=attribute_mode).select_related('parent').cache(
            on_cache_set=EntityCharacteristicOrMarkGetter.on_attribute_ancestors_cache_set,
            timeout=TermModel.ATTRIBUTE_ANCESTORS_CACHE_TIMEOUT,
            local_cache=local_cache
        )
        return ancestors

    @staticmethod
    def _get_no_attribute_ancestor(term, attribute_mode, local_cache):
        """
        RUS: Получает родительский термин у которого отсудствует заданный режим атрибута.
        """
        try:
            term = term.get_ancestors(ascending=True, include_self=False).attribute_exclude(
                attribute_mode=attribute_mode).slice_first().cache(
                on_cache_set=EntityCharacteristicOrMarkGetter.on_attribute_ancestors_cache_set,
                timeout=TermModel.ATTRIBUTE_ANCESTORS_CACHE_TIMEOUT,
                local_cache=local_cache
            )[0]
        except IndexError:
            term = None
        return term

    def _get_attributes(self, limit=None):
        """
        ENG: Return attributes objects of product.
        RUS: Возвращает атрибуты объектов.
        Самые старые объекты перемещаются в буфер.
        Очищает неуникальные значения атрибутов.
        """
        attrs0 = []
        cnt = 0
        seen_attrs = {}
        for term in self.terms:
            if limit and cnt > limit:
                break
            ancestors = EntityCharacteristicOrMarkGetter._get_attribute_ancestors(term, self.attribute_mode,
                                                                                  self.attributes_ancestors_local_cache)
            if ancestors:
                attr0 = ancestors.pop(0)
                prev_attr = attr0
                buffer = []
                for ancestor in ancestors:
                    index = seen_attrs.get(ancestor.id)
                    if index is None:
                        if prev_attr.parent_id != ancestor.id:
                            buffer.insert(0, {
                                'attr': ancestor,
                                'term': prev_attr.parent
                            })
                        prev_attr = ancestor
                    else:
                        if prev_attr.parent_id != ancestor.id:
                            attr_info = attrs0[index]
                            attr_info.values.append(prev_attr.parent.name)
                            if prev_attr.parent.view_class:
                                attr_info.view_class.extend(prev_attr.parent.view_class.split())
                        break
                for obj in buffer:
                    attr = obj['attr']
                    seen_attrs[attr.id] = len(attrs0)
                    view_class = attr.view_class.split() if attr.view_class else []
                    if obj['term'].view_class:
                        view_class.extend(obj['term'].view_class.split())
                    attrs0.append(EntityCharacteristicOrMarkInfo(attr.name, attr.path, [obj['term'].name],
                                                                  view_class,
                                                                  getattr(attr, self.tree_opts.tree_id_attr),
                                                                  getattr(attr, self.tree_opts.left_attr)))
                    cnt += 1
                if term.attributes & self.attribute_mode:
                    term = EntityCharacteristicOrMarkGetter._get_no_attribute_ancestor(term, self.attribute_mode,
                                                                                  self.attributes_ancestors_local_cache)
                if term is not None:
                    index = seen_attrs.get(attr0.id)
                    if index is None:
                        seen_attrs[attr0.id] = len(attrs0)
                        view_class = attr0.view_class.split() if attr0.view_class else []
                        if term.view_class:
                            view_class.extend(term.view_class.split())
                        attrs0.append(EntityCharacteristicOrMarkInfo(attr0.name, attr0.path, [term.name],
                                                                      view_class,
                                                                      getattr(attr0, self.tree_opts.tree_id_attr),
                                                                      getattr(attr0, self.tree_opts.left_attr)))
                        cnt += 1
                    else:
                        attr_info = attrs0[index]
                        attr_info.values.append(term.name)
                        if term.view_class:
                            attr_info.view_class.extend(term.view_class.split())
        attrs1 = []
        prev_id = None
        cnt = 0
        for additional_attribute in self.additional_characteristics_or_marks.select_related('term'):
            if limit and cnt > limit:
                break
            attribute = additional_attribute.term
            if attribute.id != prev_id:
                view_class = attribute.view_class.split() if attribute.view_class else []
                if additional_attribute.view_class:
                    view_class.extend(additional_attribute.view_class.split())
                attrs1.append(EntityCharacteristicOrMarkInfo(attribute.name, attribute.path, [additional_attribute.value],
                                                              view_class,
                                                              getattr(attribute, self.tree_opts.tree_id_attr),
                                                              getattr(attribute, self.tree_opts.left_attr)))
                cnt += 1
                prev_id = attribute.id
            else:
                attr_info = attrs1[-1]
                attr_info.values.append(additional_attribute.value)
                if additional_attribute.view_class:
                    attr_info.view_class.extend(additional_attribute.view_class.split())
        # merge attributes
        attrs = []
        while attrs0 and attrs1:
            if attrs0[0] == attrs1[0]:
                attrs.append(attrs1.pop(0))
                attrs0.pop(0)
            elif attrs0[0] < attrs1[0]:
                attrs.append(attrs0.pop(0))
            else:
                attrs.append(attrs1.pop(0))
        if attrs0:
            attrs.extend(attrs0)
        elif attrs1:
            attrs.extend(attrs1)
        # clean not uniq values and view_class
        for attr in attrs:
            if len(attr.values) > 1:
                attr.values = uniq(attr.values)
            if len(attr.view_class) > 1:
                attr.view_class = uniq(attr.view_class)
        # sort values
        for attr in attrs:
            for v in attr.values:
                if not v.isdigit():
                    attr.values.sort()
                    break
            else:
                attr.values.sort(key=int)
        return attrs if limit is None else attrs[:limit]


# ==============================================================================
# BaseEntity terms ManyRelatedManager patched methods
# ==============================================================================
def _entity_terms_many_related_manager_add(self, *objs, **kwargs):
    self._origin_add(*objs, **kwargs)

    if getattr(self.instance, '_during_terms_validation', False) and objs:
        source_field = self.through._meta.get_field(self.source_field_name)
        new_ids = set()
        for obj in objs:
            if isinstance(obj, self.model):
                fk_val = source_field.get_foreign_related_value(obj)[0]
                if fk_val is not None:
                    new_ids.add(fk_val)
            else:
                new_ids.add(obj)

        self.instance._valid_pk_set.update(new_ids) # add ids to _valid_pk_set


# ==============================================================================
# BaseEntity
# ==============================================================================
@python_2_unicode_compatible
class BaseEntity(six.with_metaclass(PolymorphicEntityMetaclass, PolymorphicModel)):
    """
    Абстрактная базовая модель для сущностей в EDW.
    
    Представляет собой основу для всех типов сущностей в системе.
    Класс предназначен для переопределения полиморфными моделями, которые добавляют
    необходимые поля и отношения для конкретных типов сущностей.
    
    Обязательные атрибуты:
    - entity_name: должен возвращать локализованное название сущности
    
    Обязательные методы:
    - get_absolute_url(): должен возвращать канонический URL сущности
    
    Attributes:
        SHORT_CHARACTERISTICS_MAX_COUNT: Максимальное количество характеристик в сокращенном списке.
        SHORT_MARKS_MAX_COUNT: Максимальное количество меток в сокращенном списке.
        terms: ManyToMany связь с терминами для классификации сущностей.
        created_at: Дата и время создания сущности.
        updated_at: Дата и время последнего обновления сущности.
        active: Флаг, указывающий, является ли сущность активной и видимой.
    """
    SHORT_CHARACTERISTICS_MAX_COUNT = edw_settings.ENTITY_ATTRIBUTES['short_characteristics_max_count']
    SHORT_MARKS_MAX_COUNT = edw_settings.ENTITY_ATTRIBUTES['short_marks_max_count']

    SUBJECT_CACHE_KEY_PATTERN = 'sub:{subj_hash}'
    RELATION_CACHE_KEY_PATTERN = 'rel:{rel_hash}'

    # таймаут для кеширования при валидации, необходим при оптимазации старта сервера в несколько потоков
    VALIDATE_TERM_MODEL_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['entity_validate_term_model']
    VALIDATE_DATA_MART_MODEL_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['entity_validate_data_mart_model']

    TERMS_BUFFER_CACHE_KEY = 'e_t_bf'
    TERMS_BUFFER_CACHE_SIZE = edw_settings.CACHE_BUFFERS_SIZES['entity_terms_ids']
    TERMS_IDS_CACHE_KEY_PATTERN = 'e_t_ids:{tree_hash}'
    TERMS_IDS_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['entity_terms_ids']

    DATA_MART_BUFFER_CACHE_KEY = 'e_dm_bf'
    DATA_MART_BUFFER_CACHE_SIZE = edw_settings.CACHE_BUFFERS_SIZES['entity_data_mart']
    DATA_MART_CACHE_KEY_PATTERN = 'e_dm:{id}'
    DATA_MART_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['entity_data_mart']

    # ORDER_BY_CREATED_AT_ASC = 'created_at'
    ORDER_BY_CREATED_AT_DESC = DataMartModel.ENTITIES_ORDER_BY_CREATED_AT_DESC

    ORDERING_MODES = (
        # (ORDER_BY_CREATED_AT_ASC, _('Created at: old first')),
        (ORDER_BY_CREATED_AT_DESC, _('Created at: new first')),
    )

    VIEW_COMPONENT_LIST = DataMartModel.ENTITIES_VIEW_COMPONENT_LIST
    # VIEW_COMPONENT_TILE = 'tile'
    # VIEW_COMPONENT_TABLE = 'table'

    VIEW_COMPONENTS = (
        (VIEW_COMPONENT_LIST, _('List view')),
        # (VIEW_COMPONENT_TILE, _('Tile view')),
        # (VIEW_COMPONENT_TABLE, _('Table view')),
    )

    RELATED_DATA_MARTS_REGEX = re.compile(r"^rdm-(\d+)$")

    TERMS_M2M_VERBOSE_NAME = _("Entity term")
    TERMS_M2M_VERBOSE_NAME_PLURAL = _("Entities terms")

    terms = deferred.ManyToManyField('BaseTerm', related_name='entities', verbose_name=_('Terms'), blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, db_index=True, verbose_name=_("Updated at"))
    active = models.BooleanField(default=True, verbose_name=_("Active"), db_index=True,
        help_text=_("Is this object publicly visible."))

    additional_characteristics_or_marks = deferred.ManyToManyField('BaseTerm',
                                                                   through=AdditionalEntityCharacteristicOrMarkModel)

    _relations = deferred.ManyToManyField('BaseEntity', through=EntityRelationModel,
                                         through_fields=('from_entity', 'to_entity'))

    related_data_marts = deferred.ManyToManyField('BaseDataMart', related_name='+', blank=True,
                                                  through=EntityRelatedDataMartModel,
                                                  through_fields=('entity', 'data_mart'),
                                                  verbose_name=_("Related data marts"))

    class Meta:
        abstract = True
        verbose_name = _("Entity")
        verbose_name_plural = _("Entities")

    def __str__(self):
        return self.entity_name

    def entity_type(self):
        """
        Возвращает полиморфный тип объекта.
        
        Полиморфный тип определяется типом контента (ContentType) для конкретного
        экземпляра модели и используется для различения разных типов сущностей.
        
        Returns:
            str: Строковое представление типа полиморфной модели.
        """
        return force_text(self.polymorphic_ctype)
    entity_type.short_description = _("Entity type")

    @cached_property
    def entity_model(self):
        """
        Возвращает имя полиморфной модели класса объекта.
        
        Получает модель из кэша типов контента для оптимизации производительности.
        
        Returns:
            str: Имя модели сущности.
        """
        # init in `edw/signals/handlers/entity.py`
        content_type_cache = self._content_type_cache
        polymorphic_ctype_id = self.polymorphic_ctype_id
        model = content_type_cache.get(polymorphic_ctype_id, None)
        if model is None:
            # todo: если делать вставку дампа в entity через loaddata то в этом месте выдает ошибку, потому что нет еще
            #  self.polymorphic_ctype до сохранения
            model = content_type_cache[polymorphic_ctype_id] = self.polymorphic_ctype.model
        return model

    def get_absolute_url(self, request=None, format=None):
        """
        Возвращает канонический URL объекта.
        
        Этот метод должен быть переопределен в дочерних классах для генерации
        правильного URL адреса для конкретного типа сущности.
        
        Args:
            request: Опциональный объект запроса Django.
            format: Опциональный формат URL.
            
        Returns:
            str: Абсолютный URL объекта.
            
        Raises:
            NotImplementedError: Если метод не реализован в дочернем классе.
        """
        msg = "Method get_absolute_url() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    @classmethod
    def get_ordering_modes(cls, **kwargs):
        """
        Возвращает доступные режимы сортировки для сущностей.
        
        Определяет, какие режимы сортировки доступны при отображении 
        списка сущностей.
        
        Args:
            **kwargs: Дополнительные параметры для настройки режимов сортировки.
            
        Returns:
            tuple: Кортеж кортежей (код_сортировки, описание).
        """
        return cls.ORDERING_MODES

    @classmethod
    def get_view_components(cls, **kwargs):
        """
        Возвращает доступные компоненты представления для сущностей.
        
        Определяет, какие варианты отображения доступны при просмотре 
        списка сущностей (список, плитка, таблица и т.д.).
        
        Args:
            **kwargs: Дополнительные параметры для настройки компонентов представления.
            
        Returns:
            tuple: Кортеж кортежей (код_компонента, описание).
        """
        return cls.VIEW_COMPONENTS

    @classmethod
    def get_all_subclasses(cls):
        """
        Возвращает все подклассы и их наследников рекурсивно.
        
        Метод рекурсивно находит все классы, наследующие от текущего класса,
        включая вложенные уровни наследования.
        
        Yields:
            class: Классы-наследники текущего класса.
        """
        for subclass in cls.__subclasses__():
            for subsubclass in subclass.get_all_subclasses():
                yield subsubclass
            yield subclass

    @staticmethod
    def get_entities_types(from_cache=True):
        """
        Возвращает типы сущностей, связанные с терминами.
        
        Создает словарь, связывающий слаги терминов с соответствующими 
        терминами, представляющими типы сущностей в системе.
        
        Args:
            from_cache: Использовать ли кэшированные типы сущностей.
            
        Returns:
            dict: Словарь {slug: term} с типами сущностей.
        """
        entities_types = getattr(EntityModel, "_entities_types_cache", None)
        if entities_types is None or not from_cache:
            entities_types = {}
            clazz = EntityModel.materialized
            try:
                root = TermModel.objects.get(slug=clazz.__name__.lower(), parent=None)
                root._entity_model_class = clazz
                entities_types[root.slug] = root
                subclasses = dict(
                    [(Model.__name__.lower(), Model) for Model in EntityModel.materialized.get_all_subclasses()])
                for term in root.get_descendants(include_self=True):
                    clazz = subclasses.get(term.slug, None)
                    if clazz is not None:
                        term._entity_model_class = clazz
                        entities_types[term.slug] = term
            except TermModel.DoesNotExist:
                pass
            EntityModel._entities_types_cache = entities_types
        return entities_types

    @classmethod
    def validate_term_model(cls):
        """
        Валидирует модель терминов и создает структуру терминов согласно иерархии классов.
        
        Добавляет термины класса объекта в дерево в соответствии со структурой наследования.
        Для каждого класса в иерархии наследования создается соответствующий термин,
        если он еще не существует.
        
        Термины создаются с ограничениями на изменение, чтобы сохранить целостность системы.
        """
        if EntityModel.materialized.__subclasses__():
            parent = None
            for Model in get_polymorphic_ancestors_models(cls):
                slug = Model.__name__.lower()
                key = 'vldt:{parent_slug}:{slug}:tr'.format(parent_slug=parent.slug if parent else None, slug=slug)
                # EntityModel._validate_term_model_cache init in `edw/signals/handlers/entity.py`
                term = EntityModel._validate_term_model_cache.get(key, None)
                if term is None:
                    with transaction.atomic():
                        try:
                            if parent is None:
                                term = TermModel.objects.get(slug=slug, parent=parent)
                            else:
                                try:
                                    parent = TermModel.objects.get(id=parent.id)
                                except TermModel.DoesNotExist:
                                    pass
                                term = TermModel.objects.get(slug=slug, id__in=list(
                                    parent.get_descendants(include_self=False).values_list('id', flat=True)))
                        except TermModel.DoesNotExist:
                            term = TermModel(slug=slug,
                                             parent_id=parent.id if parent else None,
                                             name=force_text(Model._meta.verbose_name),
                                             semantic_rule=TermModel.XOR_RULE,
                                             system_flags=(TermModel.system_flags.delete_restriction |
                                                           TermModel.system_flags.change_parent_restriction |
                                                           TermModel.system_flags.change_slug_restriction |
                                                           TermModel.system_flags.change_semantic_rule_restriction |
                                                           TermModel.system_flags.has_child_restriction |
                                                           TermModel.system_flags.external_tagging_restriction))
                            term.save(do_correct_term_unique_error=False)
                    EntityModel._validate_term_model_cache[key] = term
                parent = term

    @classmethod
    def validate_data_mart_model(cls):
        """
        Валидирует модель витрины данных.
        
        Заглушка, предназначенная для переопределения в дочерних классах
        для валидации модели витрины данных.
        """
        pass

    def need_terms_validation_after_save(self, origin, **kwargs):
        """
        Определяет, требуется ли валидация терминов после сохранения.
        
        Проверяет, является ли объект новым (origin=None) и входит ли модель
        сущности в подклассы EntityModel.materialized.
        
        Args:
            origin: Оригинальный объект до сохранения или None для новых объектов.
            **kwargs: Словарь контекста с дополнительными параметрами.
            
        Returns:
            bool: True, если требуется валидация терминов, иначе False.
        """
        if origin is None and EntityModel.materialized.__subclasses__():
            do_validate = kwargs["context"]["validate_entity_type"] = True
        else:
            do_validate = False
        return do_validate

    def validate_terms(self, origin, **kwargs):
        """
        Валидирует термины сущности и добавляет термины по типу сущности.
        
        Находит термин, соответствующий классу сущности, и добавляет его к сущности.
        Выполняется только при создании нового объекта или при принудительной валидации.
        
        Args:
            origin: Оригинальный объект до сохранения или None для новых объектов.
            **kwargs: Словарь контекста с дополнительными параметрами.
        """
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_entity_type", False):
            key = self.__class__.__name__.lower()
            try:
                term = self.get_entities_types()[key]
            except KeyError:
                term = self.get_entities_types(from_cache=False)[key]
            self.terms.add(term)

    def pre_save_entity(self, origin, *args, **kwargs):
        """
        Выполняет действия перед сохранением сущности.
        
        Метод вызывается перед методом save() и может быть переопределен
        в дочерних классах для реализации дополнительной логики.
        
        Args:
            origin: Оригинальный объект до сохранения или None для новых объектов.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.
        """
        pass

    def save(self, *args, **kwargs):
        """
        Сохраняет сущность с дополнительной логикой валидации терминов.
        
        При создании нового объекта или при принудительной валидации терминов
        выполняет валидацию и добавление необходимых терминов.
        
        Args:
            *args: Позиционные аргументы для метода save().
            **kwargs: Именованные аргументы для метода save(), включая
                     force_update - принудительное обновление,
                     force_validate_terms - принудительная валидация терминов.
                     
        Returns:
            object: Результат выполнения метода save() родительского класса.
        """
        force_update = kwargs.get('force_update', False)
        if not force_update:
            model_class = self.__class__
            try:
                origin = model_class._default_manager.get(pk=self.id)
            except model_class.DoesNotExist:
                origin = None
            self.pre_save_entity(origin, *args, **kwargs)
            force_validate_terms = kwargs.pop('force_validate_terms', False)
            validation_context = {
                'force_validate_terms': force_validate_terms
            }
            for key in list(kwargs.keys()):
                if key.find('validate') != -1:
                    validation_context[key] = kwargs.pop(key)
            result = super(BaseEntity, self).save(*args, **kwargs)
            if force_validate_terms or self.need_terms_validation_after_save(origin, context=validation_context):
                if hasattr(self, '_valid_pk_set'):
                    del self._valid_pk_set
                self._during_terms_validation = True

                self.patch_terms_many_related_manager()  # HACK!: monkey patch terms ManyRelatedManager instance

                self.validate_terms(origin, context=validation_context)
                del self._during_terms_validation
            entity_post_save.send(sender=self.__class__, instance=self, origin=origin)
        else:
            result = super(BaseEntity, self).save(*args, **kwargs)
        return result

    def patch_terms_many_related_manager(self):
        """
        Переопределяет методы менеджера множественных связей терминов.
        
        Производит патчинг метода add() ManyRelatedManager для терминов,
        чтобы реализовать дополнительную логику при добавлении терминов.
        """
        patch_class_method(self.terms.__class__, 'add', _entity_terms_many_related_manager_add)

    @cached_property
    def additional_characteristics(self):
        """
        Возвращает дополнительные характеристики текущей сущности.
        
        Метод получает из базы данных все дополнительные характеристики, связанные с текущей сущностью.
        Характеристики фильтруются по признаку is_characteristic в атрибутах термина и сортируются 
        в соответствии с древовидной структурой терминов.
        
        Returns:
            QuerySet: Набор объектов AdditionalEntityCharacteristicOrMarkModel, представляющих
                     дополнительные характеристики сущности.
        """
        tree_opts = TermModel._mptt_meta
        return AdditionalEntityCharacteristicOrMarkModel.objects.filter(
            entity=self, term__attributes=TermModel.attributes.is_characteristic).order_by(
            'term__{}'.format(tree_opts.tree_id_attr), 'term__{}'.format(tree_opts.left_attr))

    @cached_property
    def additional_marks(self):
        """
        ENG: Return additional marks of current entity.
        RUS: Возвращает дополнительные метки текущей сущности.
        """
        tree_opts = TermModel._mptt_meta
        return AdditionalEntityCharacteristicOrMarkModel.objects.filter(
            entity=self, term__attributes=TermModel.attributes.is_mark).order_by(
            'term__{}'.format(tree_opts.tree_id_attr), 'term__{}'.format(tree_opts.left_attr))

    @cached_property
    def _active_terms_for_characteristics(self):
        """
        ENG: Return terms for characteristics of current entity.
        RUS: Возвращает активные термины характеристик потомков текущей сущности.
        """
        tree_opts = TermModel._mptt_meta
        descendants_ids = TermModel.get_all_active_characteristics_descendants_ids()
        return list(self.terms.filter(id__in=descendants_ids).order_by(tree_opts.tree_id_attr, tree_opts.left_attr))

    @cached_property
    def _active_terms_for_marks(self):
        """
        ENG: Return terms for marks of current entity.
        RUS: Возвращает термины потомков для меток текущей сущности.
        """
        tree_opts = TermModel._mptt_meta
        descendants_ids = TermModel.get_all_active_marks_descendants_ids()
        return list(self.terms.filter(id__in=descendants_ids).order_by(tree_opts.tree_id_attr, tree_opts.left_attr))

    @cached_property
    def characteristics_getter(self):
        """
        Возвращает объект для получения характеристик объектов в QuerySet.
        
        Создает и настраивает экземпляр EntityCharacteristicOrMarkGetter для
        получения характеристик объектов.
        
        Returns:
            EntityCharacteristicOrMarkGetter: Объект для получения характеристик.
        """
        tree_opts = TermModel._mptt_meta
        return EntityCharacteristicOrMarkGetter(
            self._active_terms_for_characteristics,
            self.additional_characteristics,
            TermModel.attributes.is_characteristic,
            tree_opts,
            attributes_ancestors_local_cache=getattr(self, 'attributes_ancestors_local_cache', None)
        )

    @cached_property
    def characteristics(self):
        """
        Возвращает все характеристики объектов в QuerySet.
        
        Returns:
            list: Полный список характеристик для объектов.
        """
        return self.characteristics_getter.all()

    @cached_property
    def short_characteristics(self):
        """
        RUS: Возвращает короткие характеристики с ограничением максимального размера.
        """
        return self.characteristics_getter[:self.SHORT_CHARACTERISTICS_MAX_COUNT]

    @cached_property
    def marks_getter(self):
        """
        RUS: Получает все метки объектов текущей сущности.
        """
        tree_opts = TermModel._mptt_meta
        return EntityCharacteristicOrMarkGetter(
            self._active_terms_for_marks,
            self.additional_marks,
            TermModel.attributes.is_mark,
            tree_opts,
            attributes_ancestors_local_cache=getattr(self, 'attributes_ancestors_local_cache', None)
        )

    @cached_property
    def marks(self):
        """
        ENG: Return all marks objects of current entity.
        RUS: Возвращает все метки объектов текущей сущности.
        """
        return self.marks_getter.all()

    @cached_property
    def short_marks(self):
        """
        RUS: Возвращает короткие характеристики с ограничением максимального размера.
        """
        return self.marks_getter[:self.SHORT_MARKS_MAX_COUNT]

    @cached_property
    def active_terms_ids(self):
        """
        Возвращает список идентификаторов активных терминов сущности.
        
        Получает идентификаторы всех активных терминов, связанных с сущностью.
        
        Returns:
            list: Список идентификаторов активных терминов.
        """
        return list(self.terms.active().values_list('id', flat=True))

    def get_data_mart(self):
        """
        Возвращает витрину данных, соответствующую текущей сущности.
        
        Находит витрину данных на основе пересечения терминов сущности и терминов
        всех витрин данных. Выбирает витрину с наибольшим числом совпадающих терминов.
        
        Returns:
            DataMartModel/None: Экземпляр витрины данных или None, если подходящая витрина не найдена.
        """
        entity_terms_ids = self.active_terms_ids
        all_entity_terms_ids = list(TermModel.decompress(entity_terms_ids, fix_it=False).keys())
        all_data_mart_terms_ids = DataMartModel.get_all_active_terms_ids()
        crossing_terms_ids = list(set(all_entity_terms_ids) & set(all_data_mart_terms_ids))
        tree_opts = DataMartModel._mptt_meta
        crossing_data_marts_info = DataMartModel.objects.distinct().filter(
            terms__id__in=crossing_terms_ids).annotate(num=models.Count('terms__id')).values('id', 'num').order_by(
            '-num', '-' + tree_opts.level_attr, tree_opts.tree_id_attr, tree_opts.left_attr)
        all_data_marts_active_terms_count = DataMartModel.get_all_active_terms_count()
        for obj in crossing_data_marts_info:
            id = obj['id']
            num = all_data_marts_active_terms_count.get(id, None)
            if num is not None and num == obj['num']:
                result = DataMartModel.objects.get(id=id)
                break
        else:
            result = None
        return result

    @staticmethod
    def get_data_mart_cache_buffer():
        """
        Возвращает кольцевой буфер для кэширования ключей витрин данных.
        
        Создает или возвращает существующий кольцевой буфер с ограниченным размером
        для хранения ключей кэша витрин данных.
        
        Returns:
            RingBuffer: Объект кольцевого буфера для ключей кэша.
        """
        return RingBuffer.factory(BaseEntity.DATA_MART_BUFFER_CACHE_KEY,
                                  max_size=BaseEntity.DATA_MART_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_data_mart_cache_buffer():
        """
        Очищает буфер кэша витрин данных и удаляет связанные ключи из кэша.
        
        Получает все ключи из буфера, очищает буфер и удаляет значения из кэша.
        """
        buf = BaseEntity.get_data_mart_cache_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    def get_data_mart_cache_key(self):
        """
        Возвращает ключ кэша для витрины данных текущей сущности.
        
        Формирует ключ кэша на основе идентификатора сущности и шаблона ключа.
        
        Returns:
            str: Ключ кэша для витрины данных.
        """
        return self.DATA_MART_CACHE_KEY_PATTERN.format(
            id=self.id
        )

    def get_cached_data_mart(self):
        """
        Retrieves the cached data mart for the current entity.
        
        Attempts to get the data mart from cache. If not found,
        computes it, saves to cache, and records the key in the buffer.
        
        Returns:
            DataMartModel/None: Instance of data mart or None.
        """
        key = self.get_data_mart_cache_key()
        data_mart = cache.get(key, empty)
        if data_mart == empty:
            data_mart = self.get_data_mart()
            cache.set(key, data_mart, self.DATA_MART_CACHE_TIMEOUT)
            buf = self.get_data_mart_cache_buffer()
            old_key = buf.record(key)
            if old_key != buf.empty:
                cache.delete(old_key)
        return data_mart
    
    @cached_property
    def data_mart(self):
        """
        RUS: Возвращает витрину данных с ключом кэша с применением декоратора.
        """
        return self.get_cached_data_mart()

    @staticmethod
    def get_terms_cache_buffer():
        """
        RUS: Помещает ключ кэша терминов базовой сущности в кольцевой буфер.
        """
        return RingBuffer.factory(BaseEntity.TERMS_BUFFER_CACHE_KEY,
                                  max_size=BaseEntity.TERMS_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_terms_cache_buffer():
        """
        RUS: Очищает ключ кэша терминов из буфера.
        """
        buf = BaseEntity.get_terms_cache_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    @classmethod
    def get_related_data_marts_ids_from_attributes(cls, *attrs):
        """
        :return: Related data marts ids from characteristics or marks.
        RUS: Возвращает связанные id витрин данных с характеристиками или метками.
        """
        result = []
        for attr in attrs:
            for text in reduce(lambda c, x: c + x, [x.view_class for x in attr], []):
                m = cls.RELATED_DATA_MARTS_REGEX.search(text)
                if m:
                    result.append(int(m.group(1)))
        return uniq(result)

    def get_summary_extra(self, context):
        """
        ENG: Return extra data for summary serializer.
        RUS: Возвращает дополнительные данные для сводного сериалайзера.
        """
        return None

    def get_group_extra(self, context):
        """
        ENG: Return extra data for group.
        RUS: Возвращает дополнительные данные для группы.
        """
        return {
            'group_name': self.entity_name,
            'group_terms_ids': None
        }

    @classmethod
    def get_summary_annotation(cls, request):
        """
        ENG: Return annotate data for summary serializer.
        Example:
            from django.db.models import ExpressionWrapper, F
            from edw.models.expressions import ToSeconds
            ...
            return {
                'duration': (
                    ExpressionWrapper(ToSeconds(F('updated_at')) - ToSeconds(F('created_at')),
                                      output_field=models.BigIntegerField()),
                    'rest_framework.serializers.IntegerField',
                    # _("Duration in seconds")
                ),
                'duration_null2zero': (
                    'duration',
                    'edw.rest.fields.IntegerFieldNull2Zero',
                    _("Duration in seconds not null")
                ),
            }

            Or, if serialization not needed...

            return {
                'duration': ExpressionWrapper(F('updated_at') - F('created_at'), output_field=models.DurationField())
            }
        RUS: Возвращает аннотированные данные для сводного сериалайзера.
        """
        return None

    @classmethod
    def get_summary_aggregation(cls, request):
        """
        ENG: Return aggregate data for summary serializer.
        Example:
            from django.db.models import ExpressionWrapper, Avg
            ...
            return {
                'avg_duration': (
                    ExpressionWrapper(Avg('duration'), output_field=models.FloatField()),
                    'rest_framework.serializers.FloatField',
                    _("Mean value of duration")
                )
            }
        RUS: Возвращает агрегированные данные для сводного сериалайзера.
        """
        return None

    @classmethod
    def get_serializer_context(cls, context):
        """
        Позволяет модифицировать контекст сериалайзера в зависимости от класса модели,
        метод вызывается при всех обращениях к сериалайзиру ('retrieve', 'update', 'partial_update', 'destroy',
        'create', 'list', 'bulk_update', 'partial_bulk_update', 'bulk_destroy'). Тип обращения можно получить из
        context["view"].action. Объект Request доступен через context["request"], формат через context["format"].
        Так-же в контексте содержится дополнительные данные о фильтрации, группировке, сортировке и т.д. в зависимости
        от контекста вызова.

        Пример: Модификация объекта сериалайзера 'extra' в модели MyEntity

        context = super(MyEntity, cls).get_serializer_context(context)
        if context["view"].action == 'list':
            extra = context.get("extra", None)
            if extra is None:
                extra = context["extra"] = {}

            extra["MyModel"] = cls.__name__

        """
        return context

    def get_common_terms_ids(self):
        """
        ENG: Return common terms ids.
        RUS: Возвращает id общих терминов.
        """
        return self.terms.exclude(system_flags=TermModel.system_flags.external_tagging_restriction).values_list(
            'id', flat=True)

    @cached_property
    def common_terms_ids(self):
        """
        RUS: Возвращает список id общих терминов.
        """
        return list(self.get_common_terms_ids())

    @staticmethod
    def _get_related_entities_ids(rel_id, from_entity_id, direction='f'):
        """
        Get related entities ids
        :param rel_id: relation term `id` or `slug`
        :param from_entity_id: from entity id
        :param direction: direction of relation, forward - `f`, backward(reverse) - `r`. default - `f`
        :return:
        """
        if direction == 'f':
            from_entity_param, to_entity_param = 'from_entity', 'to_entity'
        else:
            from_entity_param, to_entity_param = 'to_entity', 'from_entity'

        # it was a string, not an int. Try find object by `slug`
        try:
            rel_id = int(rel_id)
        except ValueError:
            term_id_key = 'term__slug'
        else:
            term_id_key = 'term_id'

        from_entity_id_key = '{}_id'.format(from_entity_param)
        to_entity_id_key = '{}_id'.format(to_entity_param)

        return EntityRelationModel.objects.filter(**{
            term_id_key: rel_id, from_entity_id_key: from_entity_id
        }).values_list(to_entity_id_key, flat=True)

    @staticmethod
    def _get_related_entities(rel_id, from_entity_id, direction):
        """
        Get related entities
        """
        return EntityModel.objects.filter(
            id__in=EntityModel._get_related_entities_ids(rel_id, from_entity_id, direction=direction))

    def get_related_entities(self, rel_id, direction):
        """
        ENG: Get related entities, forward/backward(reverse)
        :param rel_id: relation term id
        :param direction: direction of relation, forward - `f`, backward(reverse) - `r`.
        :return:
        RUS: Получаем связаные объекты, прямыя или обратная связи.
        """
        return self._get_related_entities(rel_id, self.id, direction)

    def get_forward_related_entities(self, rel_id):
        """
        ENG: Get related entities for forward relations, shortcut for get_related_entities(..., 'f').
        RUS: Получаем объекты связанные прямым отношением.
        """
        return self.get_related_entities(rel_id, 'f')

    def get_reverse_related_entities(self, rel_id):
        """
        ENG: Get related entities for backward(reverse) relations, shortcut for get_related_entities(..., 'r').
        RUS: Получаем объекты связанные обратным отношением.
        """
        return self.get_related_entities(rel_id, 'r')

    @staticmethod
    def _set_relations(rel_id: Union[int, str], from_entity_id: int, to_entities_ids: Iterable[int],
                       direction: Literal['f', 'r'] = 'f', rewrite=True) -> None:
        """
        ENG: Set relations
        :param rel_id: relation term `id` or `slug`
        :param from_entity_id: from entity id
        :param to_entities_ids: to entity, list of id`s
        :param direction: direction of relation, forward - `f`, backward(reverse) - `r`. default - `f`
        :param rewrite: if value is False - don't delete excess relations, default - True
        :return:
        RUS: Добавляет прямые и обратные связи.
        По умолчанию удаляет избыточные связи.
        """
        if direction == 'f':
            from_entity_param, to_entity_param = 'from_entity', 'to_entity'
        else:
            from_entity_param, to_entity_param = 'to_entity', 'from_entity'

        # it was a string, not an int. Try find object by `slug`
        try:
            rel_id = int(rel_id)
        except ValueError:
            try:
                rel_id = TermModel.objects.get(slug=rel_id).id
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                # do nothing
                return

        from_entity_id_key = '{}_id'.format(from_entity_param)
        to_entity_id_key = '{}_id'.format(to_entity_param)
        to_entity_id__in_key = '{}_id__in'.format(to_entity_param)

        if rewrite:
            # delete excess relations
            instances = EntityRelationModel.objects.filter(**{
                'term_id': rel_id, from_entity_id_key: from_entity_id
            }).exclude(**{
                to_entity_id__in_key: to_entities_ids
            })
            if instances.exists():
                pre_delete_relations.send(sender=EntityRelationModel, instances=instances, rel_ids=[rel_id, ])
                instances.delete()

        # add relations
        if to_entities_ids:
            in_db_ids = EntityRelationModel.objects.filter(**{
                'term_id': rel_id,
                from_entity_id_key: from_entity_id,
                to_entity_id__in_key: to_entities_ids
            }).values_list(to_entity_id_key, flat=True)

            not_in_db_ids = list(set(to_entities_ids) - set(in_db_ids))
            if not_in_db_ids:
                to_insert = [EntityRelationModel(**{
                    'term_id': rel_id,
                    from_entity_id_key: from_entity_id,
                    to_entity_id_key: x
                }) for x in not_in_db_ids]
                instances = EntityRelationModel.objects.bulk_create(to_insert)
                post_add_relations.send(sender=EntityRelationModel, instances=instances,
                                        rel_id=rel_id, direction=direction)

    def set_relations(self, rel_id: Union[int, str], to_entities_ids: Iterable[int],
                      direction: Literal['f', 'r'], rewrite=True) -> None:
        """
        ENG: Set relations forward/backward(reverse)
        :param rel_id: relation term `id` or `slug`
        :param to_entities_ids: to entity, list of id`s
        :param direction: direction of relation, forward - `f`, backward(reverse) - `r`.
        :param rewrite: if value is False - don't delete excess relations, default - True
        :return:
        RUS: Устанавливает прямые и обратные связи.
        """
        self._set_relations(rel_id, self.id, to_entities_ids, direction=direction, rewrite=rewrite)

    def set_forward_relations(self, rel_id: Union[int, str], to_entities_ids: Iterable[int], rewrite=True) -> None:
        """
        ENG: Set forward relations, shortcut for set_relations(..., 'f').
        RUS: Устанавливает прямые связи, сокращенние для set_relations(..., 'f').
        """
        self.set_relations(rel_id, to_entities_ids, 'f', rewrite=rewrite)

    def set_reverse_relations(self, rel_id: Union[int, str], to_entities_ids: Iterable[int], rewrite=True) -> None:
        """
        ENG: Set backward(reverse) relations, shortcut for set_relations(..., 'r').
        RUS: Устанавливает обратные (реверсивные) связи, сокращенние для set_relations(..., 'r').
        """
        self.set_relations(rel_id, to_entities_ids, 'r', rewrite=rewrite)

    def set_bidirectional_relations(self, rel_id: Union[int, str], to_entities_ids: Iterable[int],
                                    rewrite=True) -> None:
        """
        ENG: Set bidirectional relations.
        RUS: Устанавливает двунаправленные связи (прямые и обратные (реверсивные)).
        """
        self.set_forward_relations(rel_id, to_entities_ids, rewrite=rewrite)
        self.set_reverse_relations(rel_id, to_entities_ids, rewrite=rewrite)

    @staticmethod
    def __make_relations_filter(values: Iterable[Union[int, str]]) -> models.Q:
        """
        Split values list to ids & slugs
        """
        ids, slugs = [], []
        for x in values:
            try:
                rel_id = int(x)
            except ValueError:
                # it was a string, not an int. Add value to slugs
                slugs.append(x)
            else:
                ids.append(rel_id)
        q_lst = []
        if ids:
            q_lst.append(models.Q(term_id__in=ids))
        if slugs:
            q_lst.append(models.Q(term__slug__in=slugs))
        return reduce(OR, q_lst)

    @staticmethod
    def _remove_relations(from_entity_id: int, rel_f_ids: Iterable[Union[int, str]],
                          rel_r_ids: Iterable[Union[int, str]]) -> None:
        """
        ENG: Remove forward and backward(reverse) relations.
        :param from_entity_id: from entity id
        :param rel_f_ids: forward relations id's filter. If `None` - relations do not delete,
        `[]` - delete all relations, else only contained in the list.
        :param rel_r_ids: reverse relations id's filter. If `None` - relations do not delete,
        `[]` - delete all relations, else only contained in the list.
        :return:
        RUS: Удаляет прямые и обратные связи в зависимости от их статуса,
        если у них нет статуса `None`.
        """
        if rel_f_ids is None:
            q_f = None
        else:
            q_f = Q(from_entity_id=from_entity_id)
            if rel_f_ids:
                q_f &= BaseEntity.__make_relations_filter(rel_f_ids)
        if rel_r_ids is None:
            q_r = None
        else:
            q_r = Q(to_entity_id=from_entity_id)
            if rel_r_ids:
                q_r &= BaseEntity.__make_relations_filter(rel_r_ids)

        if q_f is not None:
            q = q_f
            instances = EntityRelationModel.objects.filter(q_f)
            pre_delete_relations.send(sender=EntityRelationModel, instances=instances, rel_ids=rel_f_ids)
        else:
            q = None

        if q_r is not None:
            q = q | q_r if q is not None else q_r
            instances = EntityRelationModel.objects.filter(q_r)
            pre_delete_relations.send(sender=EntityRelationModel, instances=instances, rel_ids=rel_r_ids)

        if q is not None:
            EntityRelationModel.objects.filter(q).delete()

    def remove_relations(self, rel_f_ids: Union[Iterable[Union[int, str]], Type[empty]] = empty,
                         rel_r_ids: Union[Iterable[Union[int, str]], Type[empty]] = empty) -> None:
        """
        Remove forward and backward(reverse) relations
        :param rel_f_ids: forward relations id's filter (`id` or `slug` list). If `None` - relations do not delete,
        `[]` - delete all relations, else only contained in the list. Default - delete all forward relations
        :param rel_r_ids: reverse relations id's filter (`id` or `slug` list). If `None` - relations do not delete,
        `[]` - delete all relations, else only contained in the list. Default - delete all reverse relations
        :return:
        RUS: Удаляет прямые и обратные связи, если они являются пустыми.
        """
        if rel_f_ids == empty:
            rel_f_ids = []
        if rel_r_ids == empty:
            rel_r_ids = []
        self._remove_relations(self.id, rel_f_ids, rel_r_ids)

    def clean_terms(self, terms):
        """
        Метод вызывается при валидации поля `terms` в `EntityAdminForm`,
        необходим для обеспечения валидации "не системных" терминов в модуле администрирования
        """
        return terms

    @classmethod
    def get_search_query(cls, request):
        """
        Формируем поисковый запрос из объета Request
        """
        result = {
            'like': request.GET.get('q', ''),
            'unlike': request.GET.get('u', None),
            'ignore_like': request.GET.get('iq', None),
            'ignore_unlike': request.GET.get('iu', None)
        }
        return result


EntityModel = deferred.MaterializedModel(BaseEntity)


class ApiReferenceMixin(object):
    """
    ENG: Add this mixin to Entity classes to add a ``get_absolute_url()`` method.
    RUS: Добавляет миксин ApiReferenceMixin к классам сущности для метода ``get_absolute_url()``.
    """
    def get_absolute_url(self, request=None, format=None):
        """
        ENG: Return the absolute URL of a entity.
        RUS: Возвращает абсолютный URL сущности.
        """
        return reverse('edw:{}-detail'.format(EntityModel._meta.model_name.lower()), kwargs={'pk': self.pk}, request=request,
                       format=format)


