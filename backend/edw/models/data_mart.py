# -*- coding: utf-8 -*-
from __future__ import unicode_literals


#import operator
from six import with_metaclass
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.cache import cache
from django.core.validators import MinValueValidator
from django.db import models, IntegrityError, transaction
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from mptt.models import MPTTModel, MPTTModelBase
from mptt.managers import TreeManager
from mptt.exceptions import InvalidMove

from polymorphic.manager import PolymorphicManager
from polymorphic.models import PolymorphicModel
from polymorphic.base import PolymorphicModelBase
from polymorphic.query import PolymorphicQuerySet

from bitfield import BitField

from rest_framework.reverse import reverse

from . import deferred
from .rest import RESTModelBase
from .term import TermModel

from .related import DataMartRelationModel
from .cache import add_cache_key, QuerySetCachedResultMixin
from .fields import TreeForeignKey
from ..utils.hash_helpers import get_unique_slug
from ..utils.circular_buffer_in_cache import RingBuffer
from ..signals.mptt import MPTTModelSignalSenderMixin

from .. import settings as edw_settings


class BaseDataMartQuerySet(QuerySetCachedResultMixin, PolymorphicQuerySet):

    @add_cache_key('actv')
    def active(self):
        return self.filter(active=True)

    def hard_delete(self):
        return super(BaseDataMartQuerySet, self).delete()

    def delete(self):
        return super(BaseDataMartQuerySet,
                     self.exclude(system_flags=self.model.system_flags.delete_restriction)).delete()

    @add_cache_key('toplvl')
    def toplevel(self):
        """
        Return all nodes which have no parent.
        """
        return self.filter(parent__isnull=True)


class TreePolymorphicManager(TreeManager, PolymorphicManager):
    """
    Combine TreeManager & PolymorphicManager
    """
    queryset_class = BaseDataMartQuerySet


class BaseDataMartManager(TreePolymorphicManager.from_queryset(BaseDataMartQuerySet)):
    """
    Customized model manager for our DataMart model.
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


class BaseDataMartMetaclass(MPTTModelBase, PolymorphicModelBase, RESTModelBase):
    """
    The BaseDataMart class must refer to their materialized model definition, for instance when
    accessing its model manager.
    """
    def __new__(cls, name, bases, attrs):

        class Meta:
            app_label = edw_settings.APP_LABEL

        attrs.setdefault('Meta', Meta)
        if not hasattr(attrs['Meta'], 'app_label') and not getattr(attrs['Meta'], 'abstract', False):
            attrs['Meta'].app_label = Meta.app_label
        attrs.setdefault('__module__', getattr(bases[-1], '__module__'))

        Model = super(BaseDataMartMetaclass, cls).__new__(cls, name, bases, attrs)
        if Model._meta.abstract:
            return Model
        for baseclass in bases:
            # since an abstract base class does not have no valid model.Manager,
            # refer to it via its materialized Entity model.
            if not isinstance(baseclass, cls):
                continue
            basename = baseclass.__name__
            try:
                if issubclass(baseclass._materialized_model, Model):
                    # as the materialized model, use the most generic one
                    baseclass._materialized_model = Model
                elif not issubclass(Model, baseclass._materialized_model):
                    raise ImproperlyConfigured("Abstract base class {} has already been associated "
                        "with a model {}, which is different or not a submodel of {}."
                        .format(name, Model, baseclass._materialized_model))
            except (AttributeError, TypeError):
                deferred.ForeignKeyBuilder._materialized_models[basename] = Model.__name__
                # remember the materialized model mapping in the base class for further usage
                baseclass._materialized_model = Model
            deferred.ForeignKeyBuilder.process_pending_mappings(Model, basename)

        # search for deferred foreign fields in our Model
        for attrname in dir(Model):
            try:
                member = getattr(Model, attrname)
            except AttributeError:
                continue
            if not isinstance(member, deferred.DeferredRelatedField):
                continue
            map_model = deferred.ForeignKeyBuilder._materialized_models.get(member.abstract_model)
            if map_model:
                field = member.MaterializedField(map_model, **member.options)
                field.contribute_to_class(Model, attrname)
            else:
                deferred.ForeignKeyBuilder._pending_mappings.append((Model, attrname, member,))
        Model.perform_model_checks(Model)
        return Model

    @classmethod
    def perform_model_checks(cls, Model):
        """
        Perform some safety checks on the DataMartModel being created.
        """
        if not isinstance(Model.objects, BaseDataMartManager):
            msg = "Class `{}.objects` must provide ModelManager inheriting from `{}`"
            raise NotImplementedError(msg.format(Model.__name__, BaseDataMartManager.__name__))


@python_2_unicode_compatible
class BaseDataMart(with_metaclass(BaseDataMartMetaclass, MPTTModelSignalSenderMixin, MPTTModel, PolymorphicModel)):
    """
    The data marts for a enterprise data warehouse.
    """
    ALL_ACTIVE_TERMS_COUNT_CACHE_KEY = 'dm_act_t_cnt'
    ALL_ACTIVE_TERMS_IDS_CACHE_KEY = 'dm_act_t_ids'
    ALL_ACTIVE_TERMS_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['data_mart_all_active_terms']

    CHILDREN_BUFFER_CACHE_KEY = 'dm_ch_bf'
    CHILDREN_BUFFER_CACHE_SIZE = edw_settings.CACHE_BUFFERS_SIZES['data_mart_children']
    CHILDREN_CACHE_KEY_PATTERN = '{parent_id}:chld'
    CHILDREN_CACHE_TIMEOUT = edw_settings.CACHE_DURATIONS['data_mart_children']

    messages = {
        'delete_restriction': _('Delete restriction'),
        'change_parent_restriction': _('Change parent restriction'),
        'change_slug_restriction': _('Change slug restriction'),
        'has_child_restriction': _('Has child restriction'),
        'change_terms_restriction': _('Change terms restriction'),

        'parent_not_active': _('Parent node not active')
    }

    ENTITIES_ORDER_BY_CREATED_AT_DESC = '-created_at'

    ENTITIES_LIST_VIEW_COMPONENT = 'list'
    # ENTITIES_TILE_VIEW_COMPONENT = 'tile'

    ENTITIES_VIEW_COMPONENTS = (
        (ENTITIES_LIST_VIEW_COMPONENT, _('List view')),
        # (ENTITIES_TILE_VIEW_COMPONENT, _('Tile view')),
    )

    SYSTEM_FLAGS = {
        0: ('delete_restriction', messages['delete_restriction']),
        1: ('change_parent_restriction', messages['change_parent_restriction']),
        2: ('change_slug_restriction', messages['change_slug_restriction']),
        3: ('has_child_restriction', messages['has_child_restriction']),
        4: ('change_terms_restriction', messages['change_terms_restriction'])
    }

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=_('Parent'))
    name = models.CharField(verbose_name=_('Name'), max_length=255)
    slug = models.SlugField(_("Slug"), help_text=_("Used for URLs, auto-generated from name if blank."))
    path = models.CharField(verbose_name=_("Path"), max_length=255, db_index=True, editable=False, unique=True)

    terms = deferred.ManyToManyField('BaseTerm', related_name='+', verbose_name=_('Terms'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    ordering = models.CharField(verbose_name=_('Ordering'), max_length=50,
                                default=ENTITIES_ORDER_BY_CREATED_AT_DESC,
                                help_text=_('Default data mart entities ordering mode.'))

    view_component = models.CharField(verbose_name=_('View component'), max_length=50,
                                default=ENTITIES_LIST_VIEW_COMPONENT,
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
        abstract = True
        verbose_name = _("Data mart")
        verbose_name_plural = _("Data marts")

    class MPTTMeta:
        order_insertion_by = ['created_at']

    def __str__(self):
        return self.name

    def data_mart_type(self):
        """
        Returns the polymorphic type of the object.
        """
        return force_text(self.polymorphic_ctype)
    data_mart_type.short_description = _("Data mart type")

    @property
    def data_mart_model(self):
        """
        Returns the polymorphic model name of the object's class.
        """
        return self.polymorphic_ctype.model

    def get_absolute_url(self, request=None, format=None):
        """
        Hook for returning the canonical Django URL of this object.
        """
        msg = "Method get_absolute_url() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    @classmethod
    def get_all_subclasses(cls):
        for subclass in cls.__subclasses__():
            for subsubclass in subclass.get_all_subclasses():
                yield subsubclass
            yield subclass

    @cached_property
    def ancestors_list(self):
        return list(self.parent.get_ancestors(include_self=True)) if self.parent else []

    def clean(self, *args, **kwargs):
        model_class = self.__class__
        try:
            origin = model_class._default_manager.get(pk=self.pk)
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
        return origin is None

    def validate_terms(self, origin, **kwargs):
        pass

    def _make_path(self, items):

        def join_path(joiner, field, ancestors):
            return joiner.join([force_text(getattr(i, field)) for i in ancestors])

        self.path = join_path('/', 'slug', items)
        path_max_length = self._meta.get_field('path').max_length
        if len(self.path) > path_max_length:
            slug_max_length = self._meta.get_field('slug').max_length
            short_path = self.path[:path_max_length - slug_max_length - 1]
            self.path = '/'.join([short_path.rstrip('/'), get_unique_slug(self.slug, self.id)])

    def save(self, *args, **kwargs):
        # determine whether this instance is already in the db
        force_update = kwargs.get('force_update', False)
        if not force_update:
            model_class = self.__class__
            ancestors = self.ancestors_list
            try:
                origin = model_class._default_manager.get(pk=self.pk)
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
        if not self.system_flags.delete_restriction:
            super(BaseDataMart, self).delete()

    def hard_delete(self):
        super(BaseDataMart, self).delete()

    def move_to(self, target, position='first-child'):
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
        return self.CHILDREN_CACHE_KEY_PATTERN.format(
            parent_id=self.id
        )

    @add_cache_key(get_children_cache_key)
    def get_children(self):
        return super(BaseDataMart, self).get_children()

    @staticmethod
    def get_children_buffer():
        return RingBuffer.factory(BaseDataMart.CHILDREN_BUFFER_CACHE_KEY,
                                  max_size=BaseDataMart.CHILDREN_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_children_buffer():
        buf = BaseDataMart.get_children_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    @staticmethod
    def get_all_active_terms_ids():
        key = BaseDataMart.ALL_ACTIVE_TERMS_IDS_CACHE_KEY
        result = cache.get(key, None)
        if result is None:
            active_terms_ids = DataMartModel.terms.through.objects.distinct().filter(term__active=True).values_list(
                'term__id', flat=True)
            result = TermModel.decompress(active_terms_ids, fix_it=False).keys()
            cache.set(key, result, BaseDataMart.ALL_ACTIVE_TERMS_CACHE_TIMEOUT)
        return result

    @staticmethod
    def get_all_active_terms_count():
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
        return list(self.terms.active().values_list('id', flat=True))

    @staticmethod
    def get_base_entity_model():
        base_entity_model = getattr(DataMartModel, "_base_entity_model_cache", None)
        if base_entity_model is None:
            from .entity import EntityModel

            base_entity_model = EntityModel.materialized
            DataMartModel._base_entity_model_cache = base_entity_model
        return base_entity_model

    @cached_property
    def entities_model(self):
        """
        Return Data Mart entities collection Model
        """
        base_entity_model = self.get_base_entity_model()
        entities_types = dict([(term.id, term) for term in base_entity_model.get_entities_types().values()])
        entities_types_terms_ids = entities_types.keys()
        crossing_terms_ids = list(set(entities_types_terms_ids) & set(self.active_terms_ids))
        try:
            return entities_types[crossing_terms_ids[0]]._entity_model_class
        except IndexError:
            return base_entity_model

    def get_summary_extra(self):
        """
        Return extra data for summary serializer
        """
        return None

    def get_tree_extra(self):
        """
        Return extra data for tree serializer
        """
        return None


DataMartModel = deferred.MaterializedModel(BaseDataMart)


class ApiReferenceMixin(object):
    """
    Add this mixin to DataMart classes to add a ``get_absolute_url()`` method.
    """
    def get_absolute_url(self, request=None, format=None):
        """
        Return the absolute URL of a entity
        """
        return reverse('edw:{}-detail'.format(DataMartModel._meta.model_name), kwargs={'pk': self.pk}, request=request,
                       format=format)
