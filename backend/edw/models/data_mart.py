# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from bitfield import BitField
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, IntegrityError, transaction
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from mptt.exceptions import InvalidMove
from mptt.managers import TreeManager
from mptt.models import MPTTModel, MPTTModelBase
from polymorphic.base import PolymorphicModelBase
try:
    from polymorphic.manager import PolymorphicManager
except ImportError:
    from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel
from polymorphic.query import PolymorphicQuerySet
from rest_framework.reverse import reverse
from six import with_metaclass

from .cache import add_cache_key, QuerySetCachedResultMixin
from .fields.tree import TreeForeignKey
from .mixins.rebuild_tree import RebuildTreeMixin
from .related import DataMartRelationModel, DataMartPermissionModel
from .rest import RESTModelBase
from .term import TermModel
from .. import deferred
from .. import settings as edw_settings
from ..signals.mptt import MPTTModelSignalSenderMixin
from ..utils.circular_buffer_in_cache import RingBuffer
from ..utils.hash_helpers import get_unique_slug


class BaseDataMartQuerySet(QuerySetCachedResultMixin, PolymorphicQuerySet):
    """
    RUS: Запрос к базе данных витрины данных.
    """

    @add_cache_key('actv')
    def active(self):
        """
        RUS: Возвращает объекты запроса, являющимися активными.
        """
        return self.filter(active=True)

    def hard_delete(self):
        """
        RUS: Принудительное удаление объекта.
        """
        return super(BaseDataMartQuerySet, self).delete()

    def delete(self):
        """
        RUS: Удаляет объект, если нет системного флага ограничения на удаление.
        """
        return super(BaseDataMartQuerySet,
                     self.exclude(system_flags=self.model.system_flags.delete_restriction)).delete()

    @add_cache_key('toplvl')
    def toplevel(self):
        """
        ENG: Return all nodes which have no parent.
        RUS: Возвращает витрины данных вехнего уровня, у которых нет родителей.
        """
        return self.filter(parent__isnull=True)


class TreePolymorphicManager(TreeManager, PolymorphicManager):
    """
    ENG: Combine TreeManager & PolymorphicManager
    RUS: Объединяет TreeManager и PolymorphicManager, создает комбинированый запрос к витрине данных.
    """
    queryset_class = BaseDataMartQuerySet


class BaseDataMartManager(RebuildTreeMixin, TreePolymorphicManager.from_queryset(BaseDataMartQuerySet)):
    """
    ENG: Customized model manager for our DataMart model.
    RUS: Адаптированный менеджер модели для витрины данных.
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


class BaseDataMartMetaclass(deferred.ForeignKeyBuilder, MPTTModelBase, PolymorphicModelBase, RESTModelBase):
    """
    ENG: The BaseDataMart class must refer to their materialized model definition, for instance when
    accessing its model manager.
    RUS: Базовый метакласс витрины данных.
    """
    @classmethod
    def perform_model_checks(cls, Model):
        """
        ENG: Perform some safety checks on the DataMartModel being created.
        RUS: Выполняет проверку целосности класса.
        """
        # Если это - не экземпляр класса BaseDataMartManager, вызывается исключение.
        if not isinstance(Model.objects, BaseDataMartManager):
            msg = "Class `{}.objects` must provide ModelManager inheriting from `{}`"
            raise NotImplementedError(msg.format(Model.__name__, BaseDataMartManager.__name__))


@python_2_unicode_compatible
class BaseDataMart(with_metaclass(BaseDataMartMetaclass, MPTTModelSignalSenderMixin, MPTTModel, PolymorphicModel)):
    """
    ENG: The data marts for a enterprise data warehouse.
    RUS: Витрина данных для MDM – системы (корпоративного хранилища),
    Системы управления мастер-данными (MDM – Master Data Management)
    применяются для согласования данных различных информационных систем и создания целостного представления о клиентах,
    поставщиках, партнерах, продуктах, услугах или учетных записях.
    """
    ALL_ACTIVE_TERMS_COUNT_CACHE_KEY = 'dm_act_t_cnt'
    ALL_ACTIVE_TERMS_IDS_CACHE_KEY = 'dm_act_t_ids'
    ALL_ACTIVE_TERMS_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['data_mart_all_active_terms']

    CHILDREN_BUFFER_CACHE_KEY = 'dm_ch_bf'
    CHILDREN_BUFFER_CACHE_SIZE = edw_settings.CACHE_BUFFERS_SIZES['data_mart_children']
    CHILDREN_CACHE_KEY_PATTERN = '{parent_id}:chld'
    CHILDREN_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['data_mart_children']

    # таймаут для кеширования при валидации, необходим при оптимазации старта сервера в несколько потоков
    VALIDATE_TERM_MODEL_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['data_mart_validate_term_model']

    messages = {
        'delete_restriction': _('Delete restriction'),
        'change_parent_restriction': _('Change parent restriction'),
        'change_slug_restriction': _('Change slug restriction'),
        'has_child_restriction': _('Has child restriction'),
        'change_terms_restriction': _('Change terms restriction'),

        'parent_not_active': _('Parent node not active')
    }

    ENTITIES_ORDER_BY_CREATED_AT_DESC = '-created_at'

    ENTITIES_VIEW_COMPONENT_LIST = 'list'

    SYSTEM_FLAGS = {
        0: ('delete_restriction', messages['delete_restriction']),
        1: ('change_parent_restriction', messages['change_parent_restriction']),
        2: ('change_slug_restriction', messages['change_slug_restriction']),
        3: ('has_child_restriction', messages['has_child_restriction']),
        4: ('change_terms_restriction', messages['change_terms_restriction'])
    }

    TERMS_M2M_VERBOSE_NAME = _("Data mart term")
    TERMS_M2M_VERBOSE_NAME_PLURAL = _("Data marts terms")

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=_('Parent'))
    name = models.CharField(verbose_name=_('Name'), max_length=255)
    slug = models.SlugField(_("Datamart slug"), help_text=_("Used for URLs, auto-generated from name if blank."))
    path = models.CharField(verbose_name=_("Path"), max_length=255, db_index=True, editable=False, unique=True)

    terms = deferred.ManyToManyField('BaseTerm', related_name='+', verbose_name=_('Terms'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    ordering = models.CharField(verbose_name=_('Ordering'), max_length=255,
                                default=ENTITIES_ORDER_BY_CREATED_AT_DESC,
                                help_text=_('Default data mart entities ordering mode.'))

    view_component = models.CharField(verbose_name=_('View component'), max_length=255,
                                default=ENTITIES_VIEW_COMPONENT_LIST,
                                help_text=_('Default data mart entities view component.'))

    limit = models.IntegerField(verbose_name=_('Limit'), null=True, blank=True, validators=[MinValueValidator(1)],
        help_text=_('Entities per page. Leave empty for default (by default: {}).').format(
            edw_settings.REST_PAGINATION['entity_default_limit']))

    view_class = models.CharField(verbose_name=_('View Class'), max_length=255, null=True, blank=True,
        help_text=_('Space delimited class attribute, specifies one or more classnames for an data mart.'))
    description = models.TextField(verbose_name=_('Description'), null=True, blank=True)
    active = models.BooleanField(default=True, verbose_name=_("Active"), db_index=True,
                                 help_text=_("Is this data mart active."))

    system_flags = BitField(flags=SYSTEM_FLAGS, verbose_name=_('system flags'), null=True, default=None)

    _relations = deferred.ManyToManyField('BaseTerm', through=DataMartRelationModel,
                                         through_fields=('data_mart', 'term'))

    objects = BaseDataMartManager()

    # Whether the node type allows to have children.
    can_have_children = True

    class Meta:
        """
        RUS: Метакласс для определения специальных параметров модели.
        """
        abstract = True
        verbose_name = _("Data mart")
        verbose_name_plural = _("Data marts")

    class MPTTMeta:
        """
        RUS: Метакласс Django MPTT для определения параметров дерева.
        """
        order_insertion_by = ['created_at']

    class RESTMeta:
        """
        RUS: Метакласс для определения параметров сериалайзера.
        """
        lookup_fields = ('id', 'slug')

    def __str__(self):
        # Возвращаем наименование витрины данных.
        return self.name

    def __cmp__(self, other):
        """
        RUS: Сравнивает узлы витрины данных для организации сортировки согласно структуре дерева.
        """
        tree_opts = self._mptt_meta
        self_tree_id, other_tree_id = getattr(self, tree_opts.tree_id_attr), getattr(other, tree_opts.tree_id_attr)
        self_tree_left, other_tree_left = getattr(self, tree_opts.left_attr), getattr(other, tree_opts.left_attr)

        if self_tree_id == other_tree_id:
            if self_tree_left == other_tree_left:
                return 0
            elif self_tree_left < other_tree_left:
                return -1
            else:
                return 1
        elif self_tree_id < other_tree_id:
            return -1
        else:
            return 1

    def data_mart_type(self):
        """
        ENG: Returns the polymorphic type of the object.
        RUS: Возвращает полиморфный тип объекта
        """
        return force_text(self.polymorphic_ctype)
    data_mart_type.short_description = _("Data mart type")

    @property
    def data_mart_model(self):
        """
        ENG: Returns the polymorphic model name of the object's class.
        RUS: Возвращает полиморфную модель имени класса объекта
        """
        return self.polymorphic_ctype.model

    def get_absolute_url(self, request=None, format=None):
        """
        ENG: Hook for returning the canonical Django URL of this object.
        RUS: Вычисляет URL объекта, который должен быть реализован подклассом.
        """
        msg = "Method get_absolute_url() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    @classmethod
    def get_all_subclasses(cls):
        """
        ENG: Helper function to get all the subclasses of a class.
        RUS: Вспомогательная функция для получения всех подклассов текущего класса.
        """
        for subclass in cls.__subclasses__():
            for subsubclass in subclass.get_all_subclasses():
                yield subsubclass
            yield subclass

    @cached_property
    def ancestors_list(self):
        """
        ENG: Creates a QuerySet containing the ancestors of the model instance 
        (root ancestor first, immediate parent last).
        RUS: Получает список родительских элементов (предков) указанного экземпляра, включая сам экземпляр модели.
        """
        return list(self.parent.get_ancestors(include_self=True)) if self.parent else []

    def clean(self, *args, **kwargs):
        """
        ENG: Validate the model as a whole.
        RUS: Проверка всей модели на уникальность. 
        Первичный ключ должен быть равен id объекта.
        """
        model_class = self.__class__
        try:
            origin = model_class._default_manager.get(pk=self.id)
        except model_class.DoesNotExist:
            origin = None
        if self.system_flags:
            if origin is not None:
                if self.system_flags.change_slug_restriction and origin.slug != self.slug:
                    raise ValidationError(self.messages['change_slug_restriction'])
                if self.system_flags.change_parent_restriction and origin.parent_id != self.parent_id:
                    raise ValidationError(self.messages['change_parent_restriction'])
        if self.parent_id is not None and self.parent.system_flags.has_child_restriction:
            if origin is None or origin.parent_id != self.parent_id:
                raise ValidationError(self.messages['has_child_restriction'])
        return super(BaseDataMart, self).clean(*args, **kwargs)

    def need_terms_validation(self, origin, **kwargs):
        """
        RUS: Тест на необходимость проведения валидации терминов.
        """
        return origin is None

    def validate_terms(self, origin, **kwargs):
        """
        RUS: Валидация терминов.
        """
        pass

    def _make_path(self, items):

        def join_path(joiner, field, ancestors):
            """
            RUS: Формирует путь к объекту (витрине данных).
            """
            return joiner.join([force_text(getattr(i, field)) for i in ancestors])

        self.path = join_path('/', 'slug', items)
        path_max_length = self._meta.get_field('path').max_length
        if len(self.path) > path_max_length:
            slug_max_length = self._meta.get_field('slug').max_length
            short_path = self.path[:path_max_length - slug_max_length - 1]
            self.path = '/'.join([short_path.rstrip('/'), get_unique_slug(self.slug, self.id)])

    def save(self, *args, **kwargs):
        force_update = kwargs.get('force_update', False)
        if not force_update:
            model_class = self.__class__
            ancestors = self.ancestors_list
            # determine whether this instance is already in the db
            try:
                origin = model_class._default_manager.get(pk=self.id)
            except model_class.DoesNotExist:
                origin = None
            if not origin or origin.view_class != self.view_class:
                self.view_class = ' '.join([x.lower() for x in self.view_class.split()]) if self.view_class else None
            self._make_path(ancestors + [self])
            try:
                with transaction.atomic():
                    result = super(BaseDataMart, self).save(*args, **kwargs)
            except IntegrityError as e:
                if model_class._default_manager.exclude(pk=self.pk).filter(path=self.path).exists():
                    self.slug = get_unique_slug(self.slug, self.id)
                    self._make_path(ancestors + [self])
                    result = super(BaseDataMart, self).save(*args, **kwargs)
                else:
                    raise e
            if not origin or origin.active != self.active:
                if self.active:
                    update_id_list = list(self.get_family().values_list('id', flat=True))
                else:
                    update_id_list = list(self.get_descendants(include_self=False).values_list('id', flat=True))
                model_class._default_manager.filter(id__in=update_id_list).update(active=self.active)
            force_validate_terms = kwargs.get('force_validate_terms', False)
            validation_context = {}
            if force_validate_terms or self.need_terms_validation(origin, context=validation_context):
                if hasattr(self, '_valid_pk_set'):
                    del self._valid_pk_set
                self._during_terms_validation = True
                self.validate_terms(origin, context=validation_context)
                del self._during_terms_validation
        else:
            result = super(BaseDataMart, self).save(*args, **kwargs)
        return result

    def delete(self):
        """
        RUS: Удаляет объекты, если не проставлен системный флаг с ограничением на удаление.
        """
        if not self.system_flags.delete_restriction:
            super(BaseDataMart, self).delete()

    def hard_delete(self):
        """
        RUS: Принудительное удаление объекта из витрины данных.
        """
        super(BaseDataMart, self).delete()

    def move_to(self, target, position='first-child'):
        """
        RUS: Перемещает объект по дереву витрины данных с возможностью изменения родителя или добавления потомка, 
        если непроставлен системный флаг на ограничение.
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
        super(BaseDataMart, self).move_to(target, position)

    def get_children_cache_key(self):
        """
        RUS: Получает ключ кэша для объекта запроса, содержащего дочерние элементы.
        """
        return self.CHILDREN_CACHE_KEY_PATTERN.format(
            parent_id=self.id
        )

    @add_cache_key(get_children_cache_key)
    def get_children(self):
        """
        RUS: Возвращает объект запроса, содержащий дочерние элементы, хранящиеся в кэше.
        """
        return super(BaseDataMart, self).get_children()

    @staticmethod
    def get_children_buffer():
        """
        RUS: Помещает в буффер результат запроса, содержащий дочерние элементы.
        """
        return RingBuffer.factory(BaseDataMart.CHILDREN_BUFFER_CACHE_KEY,
                                  max_size=BaseDataMart.CHILDREN_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_children_buffer():
        """
        RUS: Очищает из буффера результат запроса, содержащий дочерние элементы.
        """
        buf = BaseDataMart.get_children_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    @staticmethod
    def get_all_active_terms_ids():
        """
        RUS: Возвращает id всех активных терминов из кэша и добавляет в кэш, если их там нет.
        """
        key = BaseDataMart.ALL_ACTIVE_TERMS_IDS_CACHE_KEY
        result = cache.get(key, None)
        if result is None:
            active_terms_ids = DataMartModel.terms.through.objects.distinct().filter(term__active=True).values_list(
                'term__id', flat=True)
            result = TermModel.decompress(active_terms_ids, fix_it=False).keys()
            cache.set(key, list(result), BaseDataMart.ALL_ACTIVE_TERMS_CACHE_TIMEOUT)
        return result

    @staticmethod
    def get_all_active_terms_count():
        """
        RUS: Возвращает id всех активных терминов из кэша с вычислением их количества 
        и добавляет в кэш, если их там нет.
        """
        key = BaseDataMart.ALL_ACTIVE_TERMS_COUNT_CACHE_KEY
        result = cache.get(key, None)
        if result is None:
            terms_info = DataMartModel.objects.distinct().filter(terms__active=True).annotate(
                num=models.Count('terms__id')).values('id', 'num')
            result = {}
            for obj in terms_info:
                result[obj['id']] = obj['num']
            cache.set(key, result, BaseDataMart.ALL_ACTIVE_TERMS_CACHE_TIMEOUT)
        return result

    @cached_property
    def active_terms_ids(self):
        """
        RUS: Возвращает кэш id всех активных терминов.
        """
        return list(self.terms.active().values_list('id', flat=True))

    @staticmethod
    def get_base_entity_model():
        """
        RUS: Возвращает базовую модель объекта (сущности).
        """
        base_entity_model = getattr(DataMartModel, "_base_entity_model_cache", None)
        if base_entity_model is None:
            from .entity import EntityModel

            base_entity_model = EntityModel.materialized
            DataMartModel._base_entity_model_cache = base_entity_model
        return base_entity_model

    @staticmethod
    def get_entities_model(terms_ids):
        """
        RUS: Создает модель сущности со связанными с ней терминами, унаследованную от базовой модели сущности.
        """
        base_entity_model = DataMartModel.get_base_entity_model()
        entities_types = dict([(term.id, term) for term in base_entity_model.get_entities_types().values()])
        entities_types_terms_ids = entities_types.keys()
        crossing_terms_ids = list(set(entities_types_terms_ids) & set(terms_ids))
        try:
            return entities_types[crossing_terms_ids[0]]._entity_model_class
        except IndexError:
            return base_entity_model

    @cached_property
    def is_subjective(self):
        """
        RUS: Возвращает запрос со связанными субъектами сущности.
        ENG: Returns a QuerySet with entity objects.
        """
        return self.relations.all().exists()

    @cached_property
    def entities_model(self):
        """
        ENG: Return Data Mart entities collection Model.
        RUS: Возвращает витрины данных модели сущности с активными терминами.
        """
        return self.get_entities_model(self.active_terms_ids)

    def get_summary_extra(self, context):
        """
        RUS: Возвращает дополнительные данные для итогового сериалайзера.
        ENG: Return extra data for summary serializer.
        """
        return None

    def get_tree_extra(self):
        """
        ENG: Return extra data for tree serializer.
        RUS: Возвращает дополнительные данные для дерева сериалайзера.
        """
        return None

    @classmethod
    def validate_term_model(cls):
        """
        RUS: Проверка соответствия модели терминов.
        """
        pass

    @staticmethod
    def separate_relations(relations):
        """
        ENG: Separate data mart relations into forward and backward (reverse) relations ids.
        RUS: Разделяет связи объектов витрины данных на прямые и обратные связи с созданием реляционного ключа. 
        """
        rel_f_ids, rel_r_ids = [], []
        for relation in relations:
            if relation.direction == 'f':
                rel_f_ids.append(relation.term_id)
            elif relation.direction == 'r':
                rel_r_ids.append(relation.term_id)
            else:
                rel_f_ids.append(relation.term_id)
                rel_r_ids.append(relation.term_id)
        return rel_f_ids, rel_r_ids

    @staticmethod
    def get_relations_subjects(relations):
        """
        ENG: Get data mart relations subjects. 
        RUS: Получает список связанных субъектов витрин данных. 
        """
        return {relation.term_id: list(
            relation.subjects.values_list('id', flat=True)
        ) for relation in relations}

    def get_permissions_from_request(self, request):
        """
        Get data mart permissions from request.
        """
        result = {
            'can_add': False,
            'can_change': False,
            'can_delete': False,
            'has_owner': False
        }
        user = request.user
        if user.is_authenticated() and user.is_active:
            if user.is_superuser or not DataMartPermissionModel.objects.filter(data_mart_id=self.id).exists():
                result = {
                    'can_add': True,
                    'can_change': True,
                    'can_delete': True,
                    'has_owner': False
                }
            else:
                try:
                    result = DataMartPermissionModel.objects.values('can_add', 'can_change', 'can_delete').get(
                        customer__user_id=user.id, data_mart_id=self.id)
                except DataMartPermissionModel.DoesNotExist:
                    pass
                result['has_owner'] = True
        return result


DataMartModel = deferred.MaterializedModel(BaseDataMart)


class ApiReferenceMixin(object):
    """
    ENG: Add this mixin to DataMart classes to add a ``get_absolute_url()`` method.
    RUS: Добавляет данный миксин в витрину данных для добавления метода get_absolute_url().
    """
    def get_absolute_url(self, request=None, format=None):
        """
        ENG: Return the absolute URL of a entity. 
        RUS: Возвращает абсолютный путь URL данной сущности.
        """
        return reverse('edw:{}-detail'.format(DataMartModel._meta.model_name), kwargs={'pk': self.pk}, request=request,
                       format=format)
