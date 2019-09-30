# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import inspect
import operator
from functools import reduce

from bitfield import BitField
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError, transaction
from django.db.models import Q, F
from django.db.models.query import EmptyQuerySet
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from mptt.exceptions import InvalidMove
from mptt.managers import TreeManager
from mptt.models import MPTTModel, MPTTModelBase
from mptt.querysets import TreeQuerySet
from rest_framework.reverse import reverse
from six import with_metaclass

from .cache import add_cache_key, QuerySetCachedResultMixin
from .fields.tree import TreeForeignKey
from .mixins.rebuild_tree import RebuildTreeMixin
from .mixins.term.semantic_rule import (OrRuleFilterMixin, AndRuleFilterMixin, )
from .. import deferred
from .. import settings as edw_settings
from ..signals.mptt import MPTTModelSignalSenderMixin
from ..utils.circular_buffer_in_cache import RingBuffer
from ..utils.hash_helpers import get_unique_slug, hash_unsorted_list
from ..utils.set_helpers import uniq


#==============================================================================
# TermUniqueError
#==============================================================================
class TermUniqueError(IntegrityError):
    pass


#==============================================================================
# BaseTermQuerySet
#==============================================================================
class BaseTermQuerySet(QuerySetCachedResultMixin, TreeQuerySet):

    @add_cache_key('actv')
    def active(self):
        """
        RUS: Запрос к терминам.
        Возвращает только активные элементы.
        """
        return self.filter(active=True)

    def hard_delete(self):
        """
        RUS: Запрос на принудительное удаление терминов.
        """
        return (BaseTermQuerySet, self).delete()

    def delete(self):
        """
        RUS: Запрос на удаление терминов. за исключением объектов с запретом на удаление.
        """
        return super(BaseTermQuerySet, self.exclude(system_flags=self.model.system_flags.delete_restriction)).delete()

    @add_cache_key('toplvl')
    def toplevel(self):
        """
        :return: all nodes which have no parent
        RUS: Возвращает все узлы дерева, у которых нет родителя, в результате применения фильтра.
        """
        return self.filter(parent__isnull=True)

    def leaf_only(self):
        """
        :return: all leaf nodes
        RUS: Возвращает все конечные узлы, в результате применения фильтра,
        где левый узел равен правому узлу, уменьшив значение поля на 1.
        """
        return self.filter(lft=F('rght')-1)

    def attribute_is_characteristic_or_mark(self):
        """
        RUS: Фильтр возвращает атрибуты с характеристиками или атрибуты с метками.
        """
        return self.filter(Q(attributes=self.model.attributes.is_characteristic) |
                           Q(attributes=self.model.attributes.is_mark))

    def _get_attribute_filter_cache_key(self, attribute_mode):
        """
        RUS: Создает закэшированные атрибуты с фильтрацией в целочисленном формате.
        """
        return self.model.ATTRIBUTE_FILTER_CACHE_KEY_PATTERN.format(
            mode=int(attribute_mode)
        )

    @add_cache_key(_get_attribute_filter_cache_key)
    def attribute_filter(self, attribute_mode):
        """
        RUS: Возвращает закэшированные атрибуты с применением фильтра в целочисленном формате.
        """
        return self.filter(attributes=attribute_mode)

    def _get_select_related_cache_key(self, *fields):
        """
        RUS: Получает закэшированные связанные объекты.
        """
        return self.model.SELECT_RELATED_CACHE_KEY_PATTERN.format(
            fields=':'.join(fields)
        )

    @add_cache_key(_get_select_related_cache_key)
    def select_related(self, *fields):
        """
        RUS: Возвращает связанные объекты запроса к терминам с применением кэша.
        """
        return super(BaseTermQuerySet, self).select_related(*fields)

    def attribute_is_relation(self):
        """
        RUS: Возвращает связанные атрибуты с применением кэша.
        """
        return self.filter(attributes=self.model.attributes.is_relation)

    def no_external_tagging_restriction(self):
        """
        RUS: Возвращает атрибуты, у которых нет ограничения на внешние теги.
        """
        return self.exclude(system_flags=self.model.system_flags.external_tagging_restriction)


#==============================================================================
# BaseTermManager
#==============================================================================
class BaseTermManager(RebuildTreeMixin, TreeManager.from_queryset(BaseTermQuerySet)):
    """
    ENG: Customized model manager for our Term model.
    RUS: Адаптированная модель менеджера для модели Терминов.
    """

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


#==============================================================================
# BaseTermMetaclass
#==============================================================================
class BaseTermMetaclass(deferred.ForeignKeyBuilder, MPTTModelBase):
    """
    ENG: The BaseTerm class must refer to their materialized model definition, for instance when
    accessing its model manager.
    RUS: Метакласс базовых терминов
    """
    @classmethod
    def perform_model_checks(cls, Model):
        """
        ENG: Perform some safety checks on the TermModel being created.
        RUS: Выполняет некоторые проверки безопасности для создаваемой модели терминов TermModel.
        Создаваемый класс должен являться объектом ModelManager, наследуемой от BaseTermManager.
        """
        if not isinstance(Model.objects, BaseTermManager):
            msg = "Class `{}.objects` must provide ModelManager inheriting from BaseTermManager"
            raise NotImplementedError(msg.format(Model.__name__))


#==============================================================================
# BaseTerm
#==============================================================================
@python_2_unicode_compatible
class BaseTerm(with_metaclass(BaseTermMetaclass, AndRuleFilterMixin, OrRuleFilterMixin,
                              MPTTModelSignalSenderMixin, MPTTModel)):
    """
    ENG: The fundamental parts of a enterprise data warehouse. In detail focused hierarchical dictionary of terms.
    RUS: Основные части корпоративного хранилища данных. Иерархический словарь терминов.
    """
    DECOMPRESS_BUFFER_CACHE_KEY = 'dc_bf'
    DECOMPRESS_BUFFER_CACHE_SIZE = edw_settings.CACHE_BUFFERS_SIZES['term_decompress']
    DECOMPRESS_CACHE_KEY_PATTERN = 't_i:{value_hash}:{fix_it}'
    DECOMPRESS_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['term_decompress']

    CHILDREN_BUFFER_CACHE_KEY = 't_ch_bf'
    CHILDREN_BUFFER_CACHE_SIZE = edw_settings.CACHE_BUFFERS_SIZES['term_children']
    CHILDREN_CACHE_KEY_PATTERN = '{parent_id}:chld'
    CHILDREN_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['term_children']

    ANCESTORS_CACHE_KEY_PATTERN = '{id}:anc:{ascending:d}:{include_self:d}'
    ANCESTORS_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['term_ancestors']

    ALL_ACTIVE_CHARACTERISTICS_DESCENDANTS_IDS_CACHE_KEY = 't_chr_ds_ids'
    ALL_ACTIVE_MARKS_DESCENDANTS_IDS_CACHE_KEY = 't_mrk_ds_ids'
    ALL_ATTRIBUTE_DESCENDANTS_IDS_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['term_all_attribute_descendants_ids']

    ALL_ACTIVE_ROOT_IDS_CACHE_KEY = 't_a_r_ids'
    ALL_ACTIVE_ROOT_IDS_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['term_all_active_root_ids']

    SELECT_RELATED_CACHE_KEY_PATTERN = '{fields}:sr'

    ATTRIBUTE_ANCESTORS_BUFFER_CACHE_KEY = 't_a_anc_bf'
    ATTRIBUTE_ANCESTORS_BUFFER_CACHE_SIZE = edw_settings.CACHE_BUFFERS_SIZES['term_attribute_ancestors']
    ATTRIBUTE_FILTER_CACHE_KEY_PATTERN = '{mode}:atf'
    ATTRIBUTE_ANCESTORS_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['term_attribute_ancestors']

    OR_RULE = 10
    XOR_RULE = 20
    AND_RULE = 30
    SEMANTIC_RULES = (
        (OR_RULE, _('OR')),
        (XOR_RULE, _('XOR')),
        (AND_RULE, _('AND')),
    )
    ROOT_RULE = AND_RULE

    ATTRIBUTES = {
        0: ('is_characteristic', _('Is characteristic')),
        1: ('is_mark', _('Is mark')),
        2: ('is_relation', _('Is relation')),
    }

    STANDARD_SPECIFICATION = 10
    EXPANDED_SPECIFICATION = 20
    REDUCED_SPECIFICATION = 30
    SPECIFICATION_MODES = (
        (STANDARD_SPECIFICATION, _('Standard')),
        (EXPANDED_SPECIFICATION, _('Expanded')),
        (REDUCED_SPECIFICATION, _('Reduced')),
    )

    messages = {
        'delete_restriction': _('Delete restriction'),
        'change_parent_restriction': _('Change parent restriction'),
        'change_slug_restriction': _('Change slug restriction'),
        'change_semantic_rule_restriction': _('Change semantic rule restriction'),
        'has_child_restriction': _('Has child restriction'),
        'external_tagging_restriction': _('External tagging restriction'),

        'parent_not_active': _('Parent node not active')
    }

    SYSTEM_FLAGS = {
        0: ('delete_restriction', messages['delete_restriction']),
        1: ('change_parent_restriction', messages['change_parent_restriction']),
        2: ('change_slug_restriction', messages['change_slug_restriction']),
        3: ('change_semantic_rule_restriction', messages['change_semantic_rule_restriction']),
        4: ('has_child_restriction', messages['has_child_restriction']),
        5: ('external_tagging_restriction', messages['external_tagging_restriction'])
    }


    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=_('Parent'))
    name = models.CharField(verbose_name=_('Name'), max_length=255, db_index=True)
    slug = models.SlugField(_("Term slug"), help_text=_("Used for URLs, auto-generated from name if blank."))
    path = models.CharField(verbose_name=_("Path"), max_length=255, db_index=True, editable=False, unique=True)
    semantic_rule = models.PositiveSmallIntegerField(verbose_name=_('Semantic Rule'),
                                                          choices=SEMANTIC_RULES, default=OR_RULE)
    attributes = BitField(flags=ATTRIBUTES, verbose_name=_('attributes'), null=True, default=None,
                          help_text=_("Specifying attributes of term."))
    specification_mode = models.PositiveSmallIntegerField(verbose_name=_('Specification Mode'),
                                                          choices=SPECIFICATION_MODES, default=STANDARD_SPECIFICATION)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    view_class = models.CharField(verbose_name=_('View Class'), max_length=255, null=True, blank=True,
                                  help_text=_('Space delimited class attribute, specifies one or more classnames for an entity.'))
    description = models.TextField(verbose_name=_('Description'), null=True, blank=True)
    active = models.BooleanField(default=True, verbose_name=_("Active"), db_index=True,
                                 help_text=_("Is this term active."))

    system_flags = BitField(flags=SYSTEM_FLAGS, verbose_name=_('system flags'), null=True, default=None)

    objects = BaseTermManager()

    # Whether the node type allows to have children.
    can_have_children = True

    class Meta:
        """
        RUS: Метахарактеристики объекта.
        """
        abstract = True
        verbose_name = _("Term")
        verbose_name_plural = _("Topic model")

    class MPTTMeta:
        """
        RUS: Определяет порядок данных в дереве.
        """
        order_insertion_by = ['created_at']

    def __str__(self):
        return self.name

    def make_filters(self, *args, **kwargs):
        """
        RUS: Если семантическое правило «И», применяется миксин фильтра для семантического правила «И»,
        иначе применяется миксин фильтра для правила «ИЛИ».
        """
        if self.semantic_rule == self.AND_RULE:
            return AndRuleFilterMixin.make_filters(self, *args, **kwargs)
        else:
            return OrRuleFilterMixin.make_filters(self, *args, **kwargs)

    @cached_property
    def ancestors_list(self):
        """
        RUS: Возвращает список предков объекта.
        """
        return list(self.parent.get_ancestors(include_self=True)) if self.parent else []

    def clean(self, *args, **kwargs):
        """
        RUS: Проверка уникальности тега и ограничения в системных флагах.
        """
        model_class = self.__class__
        origin = None
        if bool(self.pk) and not inspect.isclass(self.pk) or self.pk == 0:
            try:
                origin = model_class._default_manager.get(pk=self.pk)
            except model_class.DoesNotExist:
                pass
        if self.system_flags:
            if origin is not None:
                if self.system_flags.change_slug_restriction and origin.slug != self.slug:
                    raise ValidationError(self.messages['change_slug_restriction'])
                if self.system_flags.change_parent_restriction and origin.parent_id != self.parent_id:
                    raise ValidationError(self.messages['change_parent_restriction'])
                if self.system_flags.change_semantic_rule_restriction and origin.semantic_rule != self.semantic_rule:
                    raise ValidationError(self.messages['change_semantic_rule_restriction'])
        if self.parent_id is not None and self.parent.system_flags.has_child_restriction:
            if origin is None or origin.parent_id != self.parent_id:
                raise ValidationError(self.messages['has_child_restriction'])
        return super(BaseTerm, self).clean(*args, **kwargs)

    def _make_path(self, items):

        def join_path(joiner, field, ancestors):
            """
            RUS: Создает путь термина.
            """
            return joiner.join([force_text(getattr(i, field)) for i in ancestors])

        self.path = join_path('/', 'slug', items)
        path_max_length = self._meta.get_field('path').max_length
        if len(self.path) > path_max_length:
            slug_max_length = self._meta.get_field('slug').max_length
            short_path = self.path[:path_max_length - slug_max_length - 1]
            self.path = '/'.join([short_path.rstrip('/'), get_unique_slug(self.slug, self.id)])

    def save(self, *args, **kwargs):
        # determine whether this instance is already in the db
        """
        RUS: Определяет, создан ли объект в базе данных и сохраняет, если является уникальным,
        обновляя список id.
        """
        force_update = kwargs.get('force_update', False)
        do_correct_term_unique_error = kwargs.pop('do_correct_term_unique_error', True)
        if not force_update:
            model_class = self.__class__
            ancestors = self.ancestors_list
            try:
                origin = model_class._default_manager.get(pk=self.pk)
            except model_class.DoesNotExist:
                origin = None
            if not origin or origin.view_class != self.view_class:
                self.view_class = ' '.join([x.lower() for x in self.view_class.split()]) if self.view_class else None
            self._make_path(ancestors + [self, ])
            try:
                with transaction.atomic():
                    result = super(BaseTerm, self).save(*args, **kwargs)
            except IntegrityError as e:
                if model_class._default_manager.exclude(pk=self.pk).filter(path=self.path).exists():
                    if do_correct_term_unique_error:
                        self.slug = get_unique_slug(self.slug, self.id)
                        self._make_path(ancestors + [self, ])
                        result = super(BaseTerm, self).save(*args, **kwargs)
                    else:
                        raise TermUniqueError(e)
                else:
                    raise e
            if not origin or origin.active != self.active:
                if self.active:
                    update_id_list = list(self.get_family().values_list('id', flat=True))
                else:
                    update_id_list = list(self.get_descendants(include_self=False).values_list('id', flat=True))
                model_class._default_manager.filter(id__in=update_id_list).update(active=self.active)
        else:
            result = super(BaseTerm, self).save(*args, **kwargs)
        return result

    def delete(self):
        """
        RUS: Удаляет объект, если нет системного флага с ограничением на удаление.
        """
        if not self.system_flags.delete_restriction:
            super(BaseTerm, self).delete()

    def hard_delete(self):
        """
        RUS: Принудительно удаляет объект.
        """
        super(BaseTerm, self).delete()

    def move_to(self, target, position='first-child'):
        """
        RUS: Перемещает термин, являющийся потомком, по дереву, если нет ограничений на перемещение.
        """
        if position in ('left', 'right'):
            if target.parent_id != self.parent_id:
                if self.system_flags.change_parent_restriction:
                    raise InvalidMove(self.messages['change_parent_restriction'])
                if target.parent_id is not None:
                    if target.parent.system_flags.has_child_restriction:
                        raise InvalidMove(self.messages['has_child_restriction'])
                    if self.active and not target.parent.active:
                        raise InvalidMove(self.messages['parent_not_active'])
        elif position in ('first-child', 'last-child'):
            if target.id != self.parent_id:
                if self.system_flags.change_parent_restriction:
                    raise InvalidMove(self.messages['change_parent_restriction'])
                if target.system_flags.has_child_restriction:
                    raise InvalidMove(self.messages['has_child_restriction'])
                if not target.active and self.active:
                    raise InvalidMove(self.messages['parent_not_active'])
        super(BaseTerm, self).move_to(target, position)

    def get_children_cache_key(self):
        """
        RUS: Получает ключ кэша детей терминов.
        """
        return self.CHILDREN_CACHE_KEY_PATTERN.format(
            parent_id=self.id
        )

    @add_cache_key(get_children_cache_key)
    def get_children(self):
        """
        RUS: Применяет ключ кэша детей терминов.
        """
        return super(BaseTerm, self).get_children()

    def get_ancestors_cache_key(self, ascending=False, include_self=False):
        """
        RUS: Получает ключ кэша предков терминов.
        """
        return self.ANCESTORS_CACHE_KEY_PATTERN.format(
            id=self.id,
            ascending=ascending,
            include_self=include_self
        )

    @add_cache_key(get_ancestors_cache_key)
    def get_ancestors(self, ascending=False, include_self=False):
        """
        RUS: Применяет ключ кэша предков терминов.
        """
        return super(BaseTerm, self).get_ancestors(ascending, include_self)
    
    @staticmethod
    def decompress(*args, **kwars):
        """
        Shortcut to TermInfo.decompress method
        RUS: Собирает дерево из класса TermInfo.
        """
        return TermInfo.decompress(TermModel, *args, **kwars)

    @staticmethod
    def get_decompress_buffer():
        """
        RUS: Собирает кольцевой буфер с ключом кэша и указанием максимального размера.
        """
        return RingBuffer.factory(BaseTerm.DECOMPRESS_BUFFER_CACHE_KEY,
                                  max_size=BaseTerm.DECOMPRESS_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_decompress_buffer():
        """
        RUS: Очищает буфер, удаляя по указанным ключам.
        """
        buf = BaseTerm.get_decompress_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    @staticmethod
    def cached_decompress(value=None, fix_it=False):
        """
        RUS: Собирает дерево из терминов, применяя к нему ключ кэша и удаляя старый кэш по ключу,
        если он не является акутуальным.
        """
        key = BaseTerm.DECOMPRESS_CACHE_KEY_PATTERN.format(**{
            "value_hash": hash_unsorted_list(value) if value else '',
            "fix_it": 'Y' if fix_it else 'N'
        })
        tree = cache.get(key, None)
        if tree is None:
            tree = BaseTerm.decompress(value=value, fix_it=fix_it)
            cache.set(key, tree, BaseTerm.DECOMPRESS_CACHE_TIMEOUT)
            buf = BaseTerm.get_decompress_buffer()
            old_key = buf.record(key)
            if old_key != buf.empty:
                cache.delete(old_key)
        return tree

    @staticmethod
    def get_children_buffer():
        """
        RUS: Собирает буфер детей с ключом кэша и ограничением максимального размера.
        """
        return RingBuffer.factory(BaseTerm.CHILDREN_BUFFER_CACHE_KEY,
                                  max_size=BaseTerm.CHILDREN_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_children_buffer():
        """
        RUS: Очищает буфер детей, удаляет кэш по ключам.
        """
        buf = BaseTerm.get_children_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    @staticmethod
    def get_attribute_ancestors_buffer():
        """
        RUS: Собирает буфер предков с ключом кэша и ограничением максимального размера.
        """
        return RingBuffer.factory(BaseTerm.ATTRIBUTE_ANCESTORS_BUFFER_CACHE_KEY,
                                  max_size=BaseTerm.ATTRIBUTE_ANCESTORS_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_attribute_ancestors_buffer():
        """
        RUS: Очищает буфер атрибутов предков, удаляет кэш по ключам.
        """
        buf = BaseTerm.get_attribute_ancestors_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    @staticmethod
    def get_all_active_characteristics_descendants_ids():
        """
        RUS: Получает кэшированные id всех характеристик потомков со статусом активен.
        """
        key = BaseTerm.ALL_ACTIVE_CHARACTERISTICS_DESCENDANTS_IDS_CACHE_KEY
        descendants_ids = cache.get(key, None)
        if descendants_ids is None:
            characteristics_queryset = TermModel.objects.active().filter(
                attributes=TermModel.attributes.is_characteristic)
            if characteristics_queryset:
                descendants_ids = list(get_queryset_descendants(
                    characteristics_queryset).active().order_by().values_list('id', flat=True).distinct())
            else:
                descendants_ids = []
            cache.set(key, descendants_ids, BaseTerm.ALL_ATTRIBUTE_DESCENDANTS_IDS_CACHE_TIMEOUT)
        return descendants_ids

    @staticmethod
    def get_all_active_marks_descendants_ids():
        """
        RUS: Получает кэшированные id всех меток потомков со статусом активен.
        """
        key = BaseTerm.ALL_ACTIVE_MARKS_DESCENDANTS_IDS_CACHE_KEY
        descendants_ids = cache.get(key, None)
        if descendants_ids is None:
            marks_queryset = TermModel.objects.active().filter(attributes=TermModel.attributes.is_mark)
            if marks_queryset:
                descendants_ids = list(get_queryset_descendants(
                    marks_queryset).active().order_by().values_list('id', flat=True).distinct())
            else:
                descendants_ids = []
            cache.set(key, descendants_ids, BaseTerm.ALL_ATTRIBUTE_DESCENDANTS_IDS_CACHE_TIMEOUT)
        return descendants_ids

    @staticmethod
    def get_all_active_root_ids(use_cache=True):
        """
        RUS: Получает кэшированные id всех пользователей со статусом активен.
        """
        key = BaseTerm.ALL_ACTIVE_ROOT_IDS_CACHE_KEY
        root_ids = cache.get(key, None) if use_cache else None
        if root_ids is None:
            root_ids = list(TermModel.objects.active().filter(parent=None).order_by().values_list('id', flat=True))
            cache.set(key, root_ids, BaseTerm.ALL_ACTIVE_ROOT_IDS_CACHE_TIMEOUT)
        return root_ids

    def get_absolute_url(self, request=None, format=None):
        """
        ENG: Return the absolute URL of a entity.
        RUS: Возвращает абсолютный URL сущности.
        """
        return reverse('edw:{}-detail'.format(self.__class__._meta.model_name.lower()), kwargs={'pk': self.pk},
                       request=request, format=format)


#==============================================================================
# TermModel
#==============================================================================
TermModel = deferred.MaterializedModel(BaseTerm)


#==============================================================================
# get_queryset_descendants
#==============================================================================
def get_queryset_descendants(nodes, include_self=False):
    """
    RUS: Запрос к базе данных потомков. Если нет узлов,
    то возвращается пустой запрос.
    """
    if not nodes:
        #HACK: Emulate MPTTModel.objects.none(), because MPTTModel is abstract
        return EmptyQuerySet(MPTTModel)
    filters = []
    Model = nodes[0].__class__
    if include_self:
        for n in nodes:
            lft, rght = n.lft - 1, n.rght + 1
            filters.append(Q(tree_id=n.tree_id, lft__gt=lft, rght__lt=rght))
    else:
        for n in nodes:
            if n.get_descendant_count():
                lft, rght = n.lft, n.rght
                filters.append(Q(tree_id=n.tree_id, lft__gt=lft, rght__lt=rght))
    if filters:
        return Model.objects.filter(reduce(operator.or_, filters))
    else:
        #HACK: Emulate Model.objects.none()
        return Model.objects.filter(id__isnull=True)


#==============================================================================
# TermTreeInfo
#==============================================================================
class TermTreeInfo(dict):
    """
    Helper class TermTreeInfo
    RUS: Вспомогательный класс
    """
    def __init__(self, root=None, *args, **kwargs):
        self.root = root
        super(TermTreeInfo, self).__init__(*args, **kwargs)

    def get_hash(self):
        """
        RUS: Получает список захэшированных неупорядоченных ключей,
        если они несозданы.
        """
        keys = [x.term.id for x in self.values() if x.is_leaf]
        return hash_unsorted_list(keys) if keys else ''

    def trim(self, ids=None):
        """
        RUS: Создает копию дерева. Расширяет его. Возвращает дерево, у которого удалены id лишних узлов.
        """
        tree = self.deepcopy()
        tree._expand()
        return tree._trim(ids)

    def expand(self):
        """
        RUS: Добавляет в дерево ребенка к предкам.
        """
        tree = self.deepcopy()
        tree._expand()
        return tree

    def _expand(self):
        """
        RUS: Приватный метод, добавляет в дерево ребенка к предкам.
        """
        terms = [x.term for x in self.values() if x.is_leaf]
        if terms:
            for term in get_queryset_descendants(terms, include_self=False).filter(active=True):
                ancestor = self.get(term.parent_id)
                child = self[term.id] = TermInfo(term=term, is_leaf=True)
                ancestor.is_leaf = False
                ancestor.append(child)

    def _trim(self, ids=None):
        """
        RUS: Создает дерево, у которого удалены id лишних узлов.
        """
        if ids is None:
            ids = []
        # ids = uniq(ids)
        root_model_class = self.root.term.__class__
        root = TermInfo(term=root_model_class())
        tree = TermTreeInfo(root)
        for id in ids:
            src_node = self.get(id)
            if src_node is not None:
                if not id in tree:
                    node = tree[id] = TermInfo(term=src_node.term, is_leaf=True)
                    src_ancestor = self.get(node.term.parent_id)
                    while src_ancestor:
                        ancestor = tree.get(src_ancestor.term.id)
                        if not ancestor:
                            node = tree[src_ancestor.term.id] = TermInfo(term=src_ancestor.term, is_leaf=False, children=[node])
                            if node.term.parent_id is None:
                                root.append(node)
                                break
                        else:
                            ancestor.is_leaf = False
                            ancestor.append(node)
                            break
                        src_ancestor = self.get(src_ancestor.term.parent_id)
                    else:
                        root.append(node)
        for ancestor in [x for x in tree.values() if x.is_leaf]:
            src_ancestor = self[ancestor.term.id]
            if len(src_ancestor):
                ancestor.is_leaf = False
                for src_node in src_ancestor:
                    ancestor.append(tree._copy_recursively(src_node))
        return tree

    def _copy_recursively(self, src_node):
        """
        RUS: Рекурсивно создает копию узла и его элементов.
        """
        node = self[src_node.term.id] = TermInfo(term=src_node.term, is_leaf=src_node.is_leaf)
        for src_child in src_node:
            node.append(self._copy_recursively(src_child))
        return node

    def deepcopy(self):
        """
        RUS: Создает копию дерева.
        """
        root_model_class = self.root.term.__class__
        root = TermInfo(term=root_model_class())
        tree = TermTreeInfo(root)
        for src_node in self.root:
            root.append(tree._copy_recursively(src_node))
        return tree


#==============================================================================
# TermInfo
#==============================================================================
class TermInfo(list):
    """
    Class TermInfo
    Usage: tree = TermInfo.decompress(term_model, term_ids_set, fix_it=True), result type is TermTreeInfo
    Для собирания дерева терминов TermTreeInfo.
    """
    def __init__(self, term=None, is_leaf=False, children=(), attrs=None):
        """
        RUS: Конструктор класса объекта.
        """
        super(TermInfo, self).__init__(children)
        self.attrs = attrs or {}
        self.term, self.is_leaf = term, is_leaf

    def get_children_dict(self):
        """
        RUS: Возвращает по id термина ребенка значение.
        """
        result = {}
        for child in self:
            result[child.term.id] = child
        return result

    def get_descendants_ids(self):
        """
        RUS: Возвращает список из id термина ребенка и id его предков.
        """
        result = []
        for child in self:
            result.append(child.term.id)
            result.extend(child.get_descendants_ids())
        return result

    @staticmethod
    def decompress(model_class, value=None, fix_it=False):
    # todo:
    # def decompress(root_term, value=None, fix_it=False):
        """
        RUS: Собирает дерево.
        """
        if value is None:
            value = []
        value = uniq(value)
        root = TermInfo(term=model_class(semantic_rule=model_class.ROOT_RULE, active=True))
        # root = TermInfo(term=root_term)
        # model_class = root_term.__class__

        tree = TermTreeInfo(root)
        for term in model_class._default_manager.filter(pk__in=value).select_related('parent'):
            if not term.id in tree:
                node = tree[term.id] = TermInfo(term=term, is_leaf=True)
                term_parent = term.parent
                if term_parent:
                    ancestor = tree.get(term_parent.id)
                    if ancestor is not None:
                        ancestor.is_leaf = False
                        ancestor.append(node)
                    else:
                        node = tree[term_parent.id] = TermInfo(term=term_parent, is_leaf=False, children=[node])
                        if term_parent.parent_id is not None:
                            for term_ancestor in term_parent.get_ancestors(ascending=True).exclude(pk__in=tree.keys()):
                                node = tree[term_ancestor.id] = TermInfo(term=term_ancestor, is_leaf=False, children=[node])
                            ancestor = tree.get(node.term.parent_id)
                            if ancestor is not None:
                                ancestor.is_leaf = False
                                ancestor.append(node)
                            else:
                                root.append(node)
                        else:
                            root.append(node)
                else:
                    root.append(node)

        # todo:
        if fix_it:
            invalid_ids = []
            for x in [x for x in tree.values() if not x.is_leaf]:
                if len(x) > 1 and (x.term.semantic_rule == BaseTerm.XOR_RULE):
                    invalid_ids.extend(x.get_descendants_ids())
                    x.is_leaf = True
                    del x[:]
            if invalid_ids:
                for id in uniq(invalid_ids):
                    del tree[id]

        return tree

