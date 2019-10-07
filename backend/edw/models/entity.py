# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import types
from functools import reduce
from operator import __or__ as OR

from django.core.cache import cache
from django.core.exceptions import (
    FieldDoesNotExist,
    ObjectDoesNotExist,
    MultipleObjectsReturned
)
from django.db import models, connections, transaction
from django.db.models import Q, Count
from django.db.models.sql.datastructures import EmptyResultSet
from django.utils import six
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.functional import cached_property, lazy
from django.utils.translation import get_language_from_request
from django.utils.translation import ugettext_lazy as _
from ipware import ip
from polymorphic.base import PolymorphicModelBase
from polymorphic.manager import PolymorphicManager
from polymorphic.models import PolymorphicModel
from polymorphic.query import PolymorphicQuerySet
from rest_framework.reverse import reverse

from .cache import add_cache_key, QuerySetCachedResultMixin
from .data_mart import DataMartModel
from .mixins.group_by import CustomGroupByQuerySetMixin
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
from ..utils.circular_buffer_in_cache import RingBuffer, empty
from ..utils.hash_helpers import hash_unsorted_list
from ..utils.monkey_patching import patch_class_method
from ..utils.set_helpers import uniq


#==============================================================================
# get_polymorphic_ancestors_models
#==============================================================================
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


#==============================================================================
# BaseEntityQuerySet
#==============================================================================

def _get_terms_ids(entities_qs, tree):
    """
    RUS: Возвращает список id, актуализированного согласно выборке объектов, дерева терминов.
    """
    result = getattr(entities_qs, '_terms_ids_cache', None)
    if result is None:
        result = entities_qs._terms_ids_cache = tree.trim(entities_qs.get_related_terms_ids()).keys()
    return result


class BaseEntityQuerySet(CustomGroupByQuerySetMixin, QuerySetCachedResultMixin, PolymorphicQuerySet):
    """
    RUS: Запрос к базовой сущности базы данных.
    """

    GROUP_SIZE_ALIAS = 'group_size'

    def group_by(self, *fields):
        """
        RUS: Возвращает результат запроса, выбранный в результате группировки данных.
        """
        result = self.annotate(**{
            self.GROUP_SIZE_ALIAS: Count('id', distinct=True)
        })
        result.query.group_by = fields
        return result

    def alike(self, pk, *fields):
        """
        RUS: Возвращает отфильтрованные по первичному ключу значения из запроса.
        """
        try:
            alike = self.values(*fields).filter(pk=pk)[0]
        except IndexError:
            return self.none()
        return self.filter(**alike)

    @add_cache_key('actv')
    def active(self):
        """
        RUS: Возвращает отфильтрованные значения из запроса со статусом активен.
        """
        return self.filter(active=True)

    @add_cache_key('unactv')
    def unactive(self):
        """
        RUS: Возвращает отфильтрованные значения из запроса, у которых нет статуса активен (неактивные).
        """
        return self.filter(active=False)

    @add_cache_key('sf') # Add dummy key, not for caching. Use `result.semantic_filter_meta` if needed
    def semantic_filter(self, value, use_cached_decompress=False, field_name='terms'):
        """
        RUS: Добавляет фиктивный ключ не для кэширования. Возвращает отфильтрованные по семантическим правилам
        распакованные кэшированные данные тематической модели.
        """
        decompress = TermModel.cached_decompress if use_cached_decompress else TermModel.decompress
        tree = decompress(value, fix_it=True)
        filters = tree.root.term.make_filters(term_info=tree.root, field_name=field_name)
        if filters:
            result = self.filter(filters[0])
            for x in filters[1:]:
                result = result.filter(x)
            result = result.distinct()
        else:
            result = self
        result.semantic_filter_meta = tree
        return result

    def get_related_terms_ids(self):
        """
        # Pythonic, but working to slow, use connection.ops.quote_name monkey-path
        result = self.model.terms.through.objects.filter(**{
            "{entity}_id__in".format(
                entity_model=self.model._meta.object_name.lower()
            ): self.values_list('pk', flat=True)}).distinct().values_list('term_id', flat=True)
        RUS: Возвращает тематическую модель, сформированную в результате SQL-запроса к реляционным данным.
        """
        # Re-support subqueries by disabling the auto-quote feature with the following monkey-patch
        db_ops = connections[self.db].ops
        if not hasattr(db_ops, '_MP_quote_name'):
            db_ops._MP_quote_name = db_ops.quote_name
            db_ops.quote_name = types.MethodType(
                lambda self, name: name if name.startswith('(') else self._MP_quote_name(name), db_ops)

        # Make queryset
        model = self.model.terms.through
        inner_alias = self.query.get_initial_alias() + "_after_filtering"
        outer_qs = model.objects.distinct().values_list('term_id', flat=True)
        outer_alias = outer_qs.query.get_initial_alias()
        inner_qs = self.order_by().values_list('pk', flat=True)
        try:
            raw_subquery, subquery_params = inner_qs.query.get_compiler(self.db).as_sql()
        except EmptyResultSet:
            result = []
        else:
            result = outer_qs.extra(
                tables=['({select}) AS {alias}'.format(
                    select=raw_subquery,
                    alias=inner_alias
                )],
                where=['{outer_alias}.{entity}_id = {inner_alias}.id'.format(
                    entity=self.model._meta.object_name.lower(),
                    outer_alias=outer_alias,
                    inner_alias=inner_alias
                )],
                params=subquery_params
            )
        return result

    def _get_terms_ids_cache_key(self, tree):
        """
        RUS: Создается ключ кэширования для сформированной тематической модели и задается хэш.
        """
        return self.model.TERMS_IDS_CACHE_KEY_PATTERN.format(tree_hash=tree.get_hash())

    @add_cache_key(_get_terms_ids_cache_key)
    def get_terms_ids(self, tree):
        # отложенное вычисление
        result = lazy(_get_terms_ids, list)(self, tree)
        # примиксовываем вычислитель кэша
        result.__class__ = type(str('LazyQuerySetCachedResult'), (QuerySetCachedResultMixin, result.__class__), {})
        return result

    def get_similar(self, value, use_cached_decompress=False, fix_it=False):
        """
        ENG: Return similar entity from queryset, semantics isn't considered
        RUS: Получает максимально похожий по каким-либо критериям объект (сущность) из запроса.
        :param value: terms ids
        :param use_cached_decompress: do use cached decompress
        :param fix_it: do fix terms tree on decompress
        :return: similar entity on None
        """
        ids = TermModel.get_all_active_root_ids(use_cache=use_cached_decompress)
        ids.extend(value)
        decompress = TermModel.cached_decompress if use_cached_decompress else TermModel.decompress
        terms_tree = decompress(ids, fix_it=fix_it)
        lvl_expr = 'terms__{}'.format(TermModel._mptt_meta.level_attr)
        similar_entities_ids = self.values_list('id', flat=True)
        similar_entities = EntityModel.objects.filter(
            models.Q(id__in=similar_entities_ids) & models.Q(terms__id__in=terms_tree.keys())
        ).annotate(
            num=models.Count('terms__id'),
            avg_lvl=models.Avg(lvl_expr),
            max_lvl=models.Max(lvl_expr)
        ).order_by('-num', '-avg_lvl', '-max_lvl', 'created_at')
        try:
            result = similar_entities[0]
        except IndexError:
            result = None
        return result

    def _get_subj_cache_key(self, subj_ids):
        """
        RUS: Возвращает кэш id модели субъектов.
        """
        return self.model.SUBJECT_CACHE_KEY_PATTERN.format(subj_hash=(hash_unsorted_list(subj_ids) if subj_ids else ''))

    @add_cache_key(_get_subj_cache_key)
    def subj(self, subj_ids):
        """
        RUS: Возвращает отфильтрованные связанные id субъектов.
        :param subj_ids: subjects ids
        :return:
        """
        q_lst = [models.Q(models.Q(forward_relations__to_entity__in=subj_ids)),
                 models.Q(backward_relations__from_entity__in=subj_ids)]
        return self.filter(reduce(OR, q_lst)).distinct()

    def _get_rel_cache_key(self, rel_f_ids, rel_r_ids):
        """
        RUS: Возвращает ключ кэша связей для модели.
        """
        _hash = "{rel_f_ids}:{rel_r_ids}".format(
            rel_f_ids=hash_unsorted_list(rel_f_ids) if rel_f_ids else '',
            rel_r_ids=hash_unsorted_list(rel_r_ids) if rel_r_ids else ''
        )
        return self.model.RELATION_CACHE_KEY_PATTERN.format(rel_hash=_hash)

    @add_cache_key(_get_rel_cache_key)
    def rel(self, rel_f_ids, rel_r_ids):
        """
        RUS: Возвращает отфильтрованные id связей терминов.
        :param rel_f_ids: forward relations ids
        :param rel_r_ids: backward (reverse) relations ids
        :return:
        """
        q_lst = []
        if rel_f_ids:
            q_lst.append(models.Q(forward_relations__term__in=rel_f_ids))
        if rel_r_ids:
            q_lst.append(models.Q(backward_relations__term__in=rel_r_ids))
        return self.filter(reduce(OR, q_lst)).distinct()

    def _get_subj_and_rel_cache_key(self, subj, *rel_ids):
        """
        RUS: Возвращает ключ кэша субъекта и соответствующий ему ключ связей.
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
        RUS: Возвращает фильтр субъектов и терминов и соответствующих им связей.
        :param subj: list [subjects ids] or dict - {relation_id: [subjects ids]...}
        :param rel_f_ids: forward relations ids
        :param rel_r_ids: backward (reverse) relations ids
        :return:
        """
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
        return self.filter(reduce(OR, q_lst)).distinct()

    @cached_property
    def ids(self):
        """
        RUS: Возвращает список id.
        """
        return list(self.values_list('id', flat=True))

    @cached_property
    def additional_characteristics(self):
        """
        ENG: Return additional characteristics of current queryset.
        RUS: Возвращает дополнительные характеристики текущего запроса к базе данных.
        """
        tree_opts = TermModel._mptt_meta
        return AdditionalEntityCharacteristicOrMarkModel.objects.filter(
            entity_id__in=self.ids, term__attributes=TermModel.attributes.is_characteristic).order_by(
            'term__{}'.format(tree_opts.tree_id_attr), 'term__{}'.format(tree_opts.left_attr))

    @cached_property
    def additional_marks(self):
        """
        ENG: Return additional marks of current queryset.
        RUS: Возвращает дополнительные метки текущего запроса к базе данных.
        """
        tree_opts = TermModel._mptt_meta
        return AdditionalEntityCharacteristicOrMarkModel.objects.filter(
            entity_id__in=self.ids, term__attributes=TermModel.attributes.is_mark).order_by(
            'term__{}'.format(tree_opts.tree_id_attr), 'term__{}'.format(tree_opts.left_attr))

    @cached_property
    def _active_terms_for_characteristics(self):
        """
        ENG: Return terms for characteristics of current queryset.
        RUS: Возвращает термины для характеристик текущего запроса к базе данных.
        """
        tree_opts = TermModel._mptt_meta
        descendants_ids = TermModel.get_all_active_characteristics_descendants_ids()
        return list(TermModel.objects.filter(entities__id__in=self.ids, id__in=descendants_ids).distinct().order_by(
            tree_opts.tree_id_attr, tree_opts.left_attr))

    @cached_property
    def _active_terms_for_marks(self):
        """
        ENG: Return terms for marks of current queryset
        RUS: Возвращает термины для меток текущего запроса к базе данных.
        """
        tree_opts = TermModel._mptt_meta
        descendants_ids = TermModel.get_all_active_marks_descendants_ids()
        return list(TermModel.objects.filter(entities__id__in=self.ids, id__in=descendants_ids).distinct().order_by(
            tree_opts.tree_id_attr, tree_opts.left_attr))

    @cached_property
    def characteristics_getter(self):
        """
        RUS: Получает все характеристики объектов, включая характеристики активных терминов,
        дополнительные характеристики, характеристики атрибутов тематической модели.
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
        ENG: Return all characteristics objects of current queryset.
        RUS: Возвращает все характеристики объектов текущего запроса к базе данных.
        """
        return self.characteristics_getter.all()

    @cached_property
    def short_characteristics(self):
        """
        RUS: Возвращает короткие характеристики объектов текущего запроса к базе данных.
        """
        return self.characteristics_getter[:self.model.SHORT_CHARACTERISTICS_MAX_COUNT]

    @cached_property
    def marks_getter(self):
        """
        RUS: Получает все метки объектов, включая метки активных терминов,
        дополнительные метки, метки атрибутов тематической модели.
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
        ENG: Return all marks objects of current queryset.
        RUS: Возвращает все метки объектов текущего запроса к базе данных.
        """
        return self.marks_getter.all()

    @cached_property
    def short_marks(self):
        """
        RUS: Возвращает короткие метки объектов текущего запроса к базе данных.
        """
        return self.marks_getter[:self.model.SHORT_MARKS_MAX_COUNT]

    def stored_request(self, request):
        """
        ENG: Extract useful information about the request to be used for emulating a Django request
        during offline rendering.
        RUS: Извлекает пользовательскую информацию о запросе, который будет использоваться для эмуляции запроса Django
        во время оффлайн-рендеринга (визуализации).
        """
        return {
            'language': get_language_from_request(request),
            'absolute_base_uri': request.build_absolute_uri('/'),
            'remote_ip': ip.get_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'username': request.user.username if request.user else None,
        }


class BaseEntityManager(PolymorphicManager.from_queryset(BaseEntityQuerySet)):
    """
    ENG: A base ModelManager for all non-object manipulation needs, mostly statistics and querying.
    RUS: Базовая модель менеджера для всех необъектных запросов, в основном статистики и опросов.
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
        ENG: Return a queryset of indexable Entities.
        RUS: Возвращает запрос индексированных сущностей.
        """
        return self.active()


class PolymorphicEntityMetaclass(deferred.PolymorphicForeignKeyBuilder, RESTModelBase):
    """
    ENG: The BaseEntity class must refer to their materialized model definition, for instance when
    accessing its model manager. Since polymoriphic object classes, normally are materialized
    by more than one model, this metaclass finds the most generic one and associates its
    MaterializedModel with it.
    For instance,``EntityModel.objects.all()`` returns all available objects from the edw.
    RUS: BaseEntity класс должен ссылаться на материализованное определение модели, например, для
    доступа к менеджеру модели. Поскольку полиморфные классы объектов, как правило, материализуются
    по нескольким моделям, этот метакласс находит наиболее общий и связывает  собственную модель
    MaterializedModel с ним.
    """

    @classmethod
    def perform_model_checks(cls, Model):
        """
        ENG: Perform some safety checks on the EntityModel being created.
        RUS: Выполняет некоторые проверки безопасности в созданной модели сущности EntityModel.
        Объекты модели сущности должны наследоваться от BaseEntityManager.
        Базовый класс должен входить в модель PolymorphicModelBase.
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


#==============================================================================
# EntityCharacteristicOrMarkInfo & EntityCharacteristicOrMarkGetter cache system
#==============================================================================
class EntityCharacteristicOrMarkInfo(object):
    """
    RUS: Характеристики или метки сущности.
    """

    def __init__(self, name, path, values, view_class, tree_id, tree_left):
        """
        RUS: Конструктор класса.
        """
        self.name = name
        self.path = path
        self.values = values
        self.view_class = view_class
        self.tree_id = tree_id
        self.tree_left = tree_left

    def __cmp__(self, other):
        """
        RUS: Сравнивает id деревьев тематической модели.
        """
        if self.tree_id == other.tree_id:
            if self.tree_left == other.tree_left:
                return 0
            elif self.tree_left < other.tree_left:
                return -1
            else:
                return 1
        elif self.tree_id < other.tree_id:
            return -1
        else:
            return 1

    def __repr__(self):
        """
        RUS: Возвращает строковое представление объекта.
        """
        return repr((self.name, self.values))


class EntityCharacteristicOrMarkGetter(object):
    """
    ENG: Represents a lazy database lookup for a set of attributes.
    RUS: Представляет ленивый поиск в базе данных для набора атрибутов.
    """
    def __init__(self, terms, additional_characteristics_or_marks, attribute_mode, tree_opts,
                 attributes_ancestors_local_cache=None):
        """
        RUS: Конструктор класса.
        """
        self.terms = terms
        self.additional_characteristics_or_marks = additional_characteristics_or_marks
        self.attribute_mode = attribute_mode
        self.tree_opts = tree_opts
        self._result_cache = {}
        self.attributes_ancestors_local_cache = attributes_ancestors_local_cache

    def all(self, limit=None):
        """
        RUS: Устанавливает границу размеров результата кэша.
        """
        if limit not in self._result_cache:
            self._result_cache[limit] = result = self._get_attributes(limit)
        else:
            result = self._result_cache[limit]
        return result

    def __getitem__(self, k):
        """
        ENG: Retrieves an item or slice from the set of results.
        RUS: Извлекает элемент или срез из набора результатов.
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


#==============================================================================
# BaseEntity terms ManyRelatedManager patched methods
#==============================================================================
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


#==============================================================================
# BaseEntity
#==============================================================================
@python_2_unicode_compatible
class BaseEntity(six.with_metaclass(PolymorphicEntityMetaclass, PolymorphicModel)):
    """
    ENG: An abstract basic object model for the EDW. It is intended to be overridden by one or
    more polymorphic models, adding all the fields and relations, required to describe this
    type of object.

    Some attributes for this class are mandatory. They shall be implemented as property method.
    The following fields MUST be implemented by the inheriting class:
    `entity_name`: Return the pronounced name for this object in its localized language.

    Additionally the inheriting class MUST implement the following methods `get_absolute_url()`
    and etc. See below for details.
    RUS: Абстрактная базовая объектная модель для EDW.
    Она предназначен для переопределения одной или более полиморфной модели, добавляет все поля
    и отношения, необходимые для описания этого типа объекта.
    """
    SHORT_CHARACTERISTICS_MAX_COUNT = 3
    SHORT_MARKS_MAX_COUNT = 5

    SUBJECT_CACHE_KEY_PATTERN = 'sub:{subj_hash}'
    RELATION_CACHE_KEY_PATTERN = 'rel:{rel_hash}'

    # таймаут для кеширования при валидации, необходим при оптимазации старта сервера в несколько потоков
    VALIDATE_TERM_MODEL_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['entity_validate_term_model']

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
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
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
        ENG: Returns the polymorphic type of the object.
        RUS: Возвращает полиморфный тип объекта.
        """
        return force_text(self.polymorphic_ctype)
    entity_type.short_description = _("Entity type")

    @property
    def entity_model(self):
        """
        ENG: Returns the polymorphic model name of the object's class.
        RUS: Возвращает имя полиморфной модели класса объекта.
        """
        return self.polymorphic_ctype.model

    def get_absolute_url(self, request=None, format=None):
        """
        ENG: Hook for returning the canonical Django URL of this object.
        RUS: Возвращает абсолютные путь URL объекта.
        """
        msg = "Method get_absolute_url() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    @classmethod
    def get_ordering_modes(cls, **kwargs):
        """
        RUS: Возвращает отсортированные модели, являющиеся методами класса.
        """
        return cls.ORDERING_MODES

    @classmethod
    def get_view_components(cls, **kwargs):
        """
        RUS: Возвращает view components (компоненты представлений): табличное представление, плиточное представление.
        """
        return cls.VIEW_COMPONENTS

    @classmethod
    def get_all_subclasses(cls):
        """
        RUS: Возвращает все подклассы и их наследники.
        """
        for subclass in cls.__subclasses__():
            for subsubclass in subclass.get_all_subclasses():
                yield subsubclass
            yield subclass

    '''
    def get_price(self, request):
        """
        Hook for returning the current price of this object.
        The price shall be of type Money. Read the appropriate section on how to create a Money
        type for the chosen currency.
        Use the `request` object to vary the price according to the logged in user,
        its country code or the language.
        """
        msg = "Method get_price() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    def is_in_cart(self, cart, watched=False, **kwargs):
        """
        Checks if the object is already in the given cart, and if so, returns the corresponding
        cart_item, otherwise this method returns None.
        The boolean `watched` is used to determine if this check shall only be performed for the
        watch-list.
        Optionally one may pass arbitrary information about the object using `**kwargs`. This can
        be used to determine if a object with variations shall be considered as the same cart item
        increasing it quantity, or if it shall be considered as a separate cart item, resulting in
        the creation of a new cart item.
        """
        from .cart import CartItemModel
        cart_item_qs = CartItemModel.objects.filter(cart=cart, object=self)
        return cart_item_qs.first()
    '''

    @staticmethod
    def get_entities_types(from_cache=True):
        """
        RUS: Возвращает типы сущности.
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
        RUS: Проверяет условия создания терминов модели, создает термины и сохраняет.
        """
        if EntityModel.materialized.__subclasses__():
            parent = None
            for Model in get_polymorphic_ancestors_models(cls):
                slug = Model.__name__.lower()
                key = 'vldt:{parent_slug}:{slug}:tm'.format(parent_slug=parent.slug if parent else None, slug=slug)
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

    def need_terms_validation_after_save(self, origin, **kwargs):
        """
        RUS: Проверяет термины после сохранения, являются они оригинальными и входит Модель сущности в субкласс.
        """
        if origin is None and EntityModel.materialized.__subclasses__():
            do_validate = kwargs["context"]["validate_entity_type"] = True
        else:
            do_validate = False
        return do_validate

    def validate_terms(self, origin, **kwargs):
        """
        RUS: Создает ключ кэша терминов и добавляет термин с ключом.
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
        Normally not needed.
        This function call before `.save()` method.
        :param origin:
        :return:
        """

    def save(self, *args, **kwargs):
        """
        RUS: Сохраняет термины с использованием принудительного обновления и принудительной валидации.
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
            bulk_force_validate_terms = kwargs.pop('bulk_force_validate_terms', False)
            result = super(BaseEntity, self).save(*args, **kwargs)
            validation_context = {
                "force_validate_terms": force_validate_terms,
                "bulk_force_validate_terms": bulk_force_validate_terms
            }
            if force_validate_terms or self.need_terms_validation_after_save(origin, context=validation_context):
                if hasattr(self, '_valid_pk_set'):
                    del self._valid_pk_set
                self._during_terms_validation = True

                self.patch_terms_many_related_manager() # HACK!: monkey patch terms ManyRelatedManager instance

                self.validate_terms(origin, context=validation_context)
                del self._during_terms_validation
            entity_post_save.send(sender=self.__class__, instance=self, origin=origin)
        else:
            result = super(BaseEntity, self).save(*args, **kwargs)
        return result

    def patch_terms_many_related_manager(self):
        """
        RUS: Переопределяет методы менеджера множественных связей терминов.
        """
        patch_class_method(self.terms.__class__, 'add', _entity_terms_many_related_manager_add)

    @cached_property
    def additional_characteristics(self):
        """
        ENG: Return additional characteristics of current entity.
        RUS: Возвращает дополнительные характеристики текущей сущности.
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
        RUS: Получает характеристики объекта текущей сущности.
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
        ENG: Return all characteristics objects of current entity.
        RUS: Возвращает все характеристики объектов текущей сущности.
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
        RUS: Возвращает список id активных терминов.
        """
        return list(self.terms.active().values_list('id', flat=True))

    def get_data_mart(self):
        """
        ENG: Return entity data mart.
        RUS: Возвращает экземпляр витрины данных.
        """
        entity_terms_ids = self.active_terms_ids
        all_entity_terms_ids = TermModel.decompress(entity_terms_ids, fix_it=False).keys()
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
        RUS: Помещает ключ кэша витрины данных в кольцевой буфер.
        """
        return RingBuffer.factory(BaseEntity.DATA_MART_BUFFER_CACHE_KEY,
                                  max_size=BaseEntity.DATA_MART_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_data_mart_cache_buffer():
        """
        RUS: Очищает ключ кэша витрины данных из буфера.
        """
        buf = BaseEntity.get_data_mart_cache_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    def get_data_mart_cache_key(self):
        """
        RUS: Возвращает шаблон ключа кэша витрины данных.
        """
        return self.DATA_MART_CACHE_KEY_PATTERN.format(
            id=self.id
        )

    def get_cached_data_mart(self):
        """
        RUS: Возвращает витрину данных с ключом кэша.
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
            'group_name': self.entity_name
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
    def _set_relations(rel_id, from_entity_id, to_entities_ids, direction='f'):
        """
        ENG: Set relations
        :param rel_id: relation term `id` or `slug`
        :param from_entity_id: from entity id
        :param to_entities_ids: to entity, list of id`s
        :param direction: direction of relation, forward - `f`, backward(reverse) - `r`. default - `f`
        :return:
        RUS: Добавляет прямые и обратные связи.
        Удаляет избыточные связи.
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

        # delete excess relations
        EntityRelationModel.objects.filter(**{
            'term_id': rel_id, from_entity_id_key: from_entity_id
        }).exclude(**{
            to_entity_id__in_key: to_entities_ids
        }).delete()

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
                EntityRelationModel.objects.bulk_create(to_insert)

    def set_relations(self, rel_id, to_entities_ids, direction):
        """
        ENG: Set relations forward/backward(reverse)
        :param rel_id: relation term `id` or `slug`
        :param from_entity_id: from entity id
        :param to_entities_ids: to entity, list of id`s
        :param direction: direction of relation, forward - `f`, backward(reverse) - `r`.
        :return:
        RUS: Устанавливает прямые и обратные связи.
        """
        self._set_relations(rel_id, self.id, to_entities_ids, direction=direction)

    def set_forward_relations(self, rel_id, to_entities_ids):
        """
        ENG: Set forward relations, shortcut for set_relations(..., 'f').
        RUS: Устанавливает прямые связи, сокращенное обозначение 'f'.
        """
        self.set_relations(rel_id, to_entities_ids, 'f')

    def set_reverse_relations(self, rel_id, to_entities_ids):
        """
        ENG: Set backward(reverse) relations, shortcut for set_relations(..., 'r').
        RUS: Устанавливает обратные (реверсивные) связи, сокращенное обозначение 'r'.
        """
        self.set_relations(rel_id, to_entities_ids, 'r')

    def set_bidirectional_relations(self, rel_id, to_entities_ids):
        """
        ENG: Set bidirectional relations.
        RUS: Устанавливает двунаправленные связи (прямые и обратные (реверсивные)).
        """
        self.set_forward_relations(rel_id, to_entities_ids)
        self.set_reverse_relations(rel_id, to_entities_ids)

    @staticmethod
    def _remove_relations(from_entity_id, rel_f_ids, rel_r_ids):
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
                q_f &= Q(term_id__in=rel_f_ids)
        if rel_r_ids is None:
            q_r = None
        else:
            q_r = Q(to_entity_id=from_entity_id)
            if rel_r_ids:
                q_r &= Q(term_id__in=rel_r_ids)

        q = q_f if q_f is not None else None
        if q_r is not None:
            q = q | q_r if q is not None else q_r

        if q is not None:
            EntityRelationModel.objects.filter(q).delete()

    def remove_relations(self, rel_f_ids=empty, rel_r_ids=empty):
        """
        Remove forward and backward(reverse) relations
        :param rel_f_ids: forward relations id's filter. If `None` - relations do not delete,
        `[]` - delete all relations, else only contained in the list. Default - delete all forward relations
        :param rel_r_ids: reverse relations id's filter. If `None` - relations do not delete,
        `[]` - delete all relations, else only contained in the list. Default - delete all reverse relations
        :return:
        RUS: Удаляет прямые и обратные связи, если они являются пустыми.
        """
        if rel_f_ids == empty:
            rel_f_ids = []
        if rel_r_ids == empty:
            rel_r_ids = []
        self._remove_relations(self.id, rel_f_ids, rel_r_ids)


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
