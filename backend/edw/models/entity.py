# -*- coding: utf-8 -*-
from __future__ import unicode_literals

'''
from datetime import datetime
from functools import reduce
import operator
'''

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import six
from django.utils.functional import cached_property
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.translation import ugettext_lazy as _

from polymorphic.manager import PolymorphicManager
from polymorphic.models import PolymorphicModel
from polymorphic.query import PolymorphicQuerySet
from polymorphic.base import PolymorphicModelBase

from . import deferred
from .term import TermModel
from .related import AdditionalEntityCharacteristicOrMarkModel
from ..utils.set_helpers import uniq
from .. import settings as edw_settings


#==============================================================================
# BaseEntityQuerySet
#==============================================================================
class BaseEntityQuerySet(PolymorphicQuerySet):

    def active(self):
        return self.filter(active=True)

    def semantic_filter(self, value, use_cached_decompress=False, field_name='terms'):
        decompress = TermModel.cached_decompress if use_cached_decompress else TermModel.decompress
        tree = decompress(value, fix_it=True)
        filters = tree.root.term.make_filters(term_info=tree.root, field_name=field_name)
        if filters:
            result = self.filter(filters[0])
            for x in filters[1:]:
                result = result.filter(x)
            return result.distinct()
        else:
            return self


class BaseEntityManager(PolymorphicManager.from_queryset(BaseEntityQuerySet)):
    """
    A base ModelManager for all non-object manipulation needs, mostly statistics and querying.
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
        Return a queryset of indexable Entities.
        """
        return self.active()


class PolymorphicEntityMetaclass(PolymorphicModelBase):
    """
    The BaseEntity class must refer to their materialized model definition, for instance when
    accessing its model manager. Since polymoriphic object classes, normally are materialized
    by more than one model, this metaclass finds the most generic one and associates its
    MaterializedModel with it.
    For instance,``EntityModel.objects.all()`` returns all available objects from the shop.
    """
    def __new__(cls, name, bases, attrs):

        class Meta:
            app_label = edw_settings.APP_LABEL

        attrs.setdefault('Meta', Meta)
        if not hasattr(attrs['Meta'], 'app_label') and not getattr(attrs['Meta'], 'abstract', False):
            attrs['Meta'].app_label = Meta.app_label
        attrs.setdefault('__module__', getattr(bases[-1], '__module__'))

        Model = super(PolymorphicEntityMetaclass, cls).__new__(cls, name, bases, attrs)
        if Model._meta.abstract:
            return Model
        for baseclass in bases:
            # since an abstract base class does not have no valid model.Manager,
            # refer to it via its materialized Entity model.
            if not isinstance(baseclass, cls):
                continue
            try:
                if issubclass(baseclass._materialized_model, Model):
                    # as the materialized model, use the most generic one
                    baseclass._materialized_model = Model
                elif not issubclass(Model, baseclass._materialized_model):
                    raise ImproperlyConfigured("Abstract base class {} has already been associated "
                        "with a model {}, which is different or not a submodel of {}."
                        .format(name, Model, baseclass._materialized_model))
            except (AttributeError, TypeError):
                baseclass._materialized_model = Model
            deferred.ForeignKeyBuilder.process_pending_mappings(Model, baseclass.__name__)

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
        cls.perform_model_checks(Model)
        return Model

    @classmethod
    def perform_model_checks(cls, Model):
        """
        Perform some safety checks on the EntityModel being created.
        """
        if not isinstance(Model.objects, BaseEntityManager):
            msg = "Class `{}.objects` must provide ModelManager inheriting from BaseEntityManager"
            raise NotImplementedError(msg.format(Model.__name__))

        if not isinstance(getattr(Model, 'lookup_fields', None), (list, tuple)):
            msg = "Class `{}` must provide a tuple of `lookup_fields` so that we can easily lookup for Entities"
            raise NotImplementedError(msg.format(Model.__name__))

        try:
            Model().entity_name
        except AttributeError:
            msg = "Class `{}` must provide a model field or property implementing `entity_name`"
            raise NotImplementedError(msg.format(Model.__name__))

        #if not callable(getattr(Model, 'get_price', None)):
        #    msg = "Class `{}` must provide a method implementing `get_price(request)`"
        #    raise NotImplementedError(msg.format(cls.__name__))


#==============================================================================
# EntityCharacteristicOrMarkInfo & EntityCharacteristicOrMarkSet cache system
#==============================================================================
class EntityCharacteristicOrMarkInfo(object):

    def __init__(self, name, path, values, view_class, tree_id, tree_left):
        self.name = name
        self.path = path
        self.values = values
        self.view_class = view_class
        self.tree_id = tree_id
        self.tree_left = tree_left

    def __cmp__(self, other):
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
        return repr((self.name, self.values))


class ProductCharacteristicOrMarkSet(object):
    """
    Represents a lazy database lookup for a set of attributes.
    """
    def __init__(self, terms, additional_characteristics_or_marks, attribute_mode, tree_opts):
        self.terms = terms
        self.additional_characteristics_or_marks = additional_characteristics_or_marks
        self.attribute_mode = attribute_mode
        self.tree_opts = tree_opts
        self._result_cache = {}

    def all(self, limit=None):
        if limit not in self._result_cache:
            self._result_cache[limit] = result = self._get_attributes(limit)
        else:
            result = self._result_cache[limit]
        return result

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
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
    def on_attridute_ancestors_cache_set(key):

        print "\n\n\n**** on_attridute_ancestors_cache_set", key

        # buf = TermModel.get_children_buffer()
        # old_key = buf.record(key)
        # if old_key != buf.empty:
        #     cache.delete(old_key)

    @staticmethod
    def _get_attridute_ancestors(term, attribute_mode):
        # key = Rubric.RUBRIC_ATTRIBUTES_ANCESTORS_CACHE_KEY_PATTERN % {'id': term.id, 'attribute_mode': attribute_mode}
        # ancestors = cache.get(key, None)
        # if ancestors is None:
        #     ancestors = list(term.get_ancestors(ascending=True, include_self=False).filter(attributes=attribute_mode).select_related('parent'))
        #     cache.set(key, ancestors, Rubric.CACHE_TIMEOUT)

        ancestors = term.get_ancestors(ascending=True, include_self=False).attribute_filter(
            attribute_mode=attribute_mode).select_related('parent').cache(
            on_cache_set=ProductCharacteristicOrMarkSet.on_attridute_ancestors_cache_set,
            timeout=TermModel.ATTRIBUTE_ANCESTORS_CACHE_TIMEOUT)

        # try:
        #     print dir(ancestors.attribute_filter(attribute_mode=attribute_mode))
        # except Exception as e:
        #     print "________________________________"
        #     print e
        #
        # ancestors = list(term.get_ancestors(ascending=True, include_self=False).filter(
        #     attributes=attribute_mode).select_related('parent'))

        return ancestors

    def _get_attributes(self, limit=None):
        """
        Return attributes objects of product
        """
        attrs0 = []
        cnt = 0
        seen_attrs = {}
        for term in self.terms:
            if limit and cnt > limit:
                break
            ancestors = ProductCharacteristicOrMarkSet._get_attridute_ancestors(term, self.attribute_mode)
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
                if not (term.attributes & self.attribute_mode):
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


@python_2_unicode_compatible
class BaseEntity(six.with_metaclass(PolymorphicEntityMetaclass, PolymorphicModel)):
    """
    An abstract basic object model for the EDW. It is intended to be overridden by one or
    more polymorphic models, adding all the fields and relations, required to describe this
    type of object.

    Some attributes for this class are mandatory. They shall be implemented as property method.
    The following fields MUST be implemented by the inheriting class:
    `entity_name`: Return the pronounced name for this object in its localized language.

    Additionally the inheriting class MUST implement the following methods `get_absolute_url()`
    and etc. See below for details.
    """
    terms = deferred.ManyToManyField('BaseTerm', related_name='entities', verbose_name=_('Terms'), blank=True,
                                     help_text=_("""Use "ctrl" key for choose multiple terms"""))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    active = models.BooleanField(default=True, verbose_name=_("Active"),
        help_text=_("Is this object publicly visible."))

    additional_characteristics_or_marks = deferred.ManyToManyField(
        'BaseTerm',
        through=AdditionalEntityCharacteristicOrMarkModel)

    class Meta:
        abstract = True
        verbose_name = _("Entity")
        verbose_name_plural = _("Entities")

    def __str__(self):
        return self.entity_name

    def entity_type(self):
        """
        Returns the polymorphic type of the object.
        """
        return force_text(self.polymorphic_ctype)
    entity_type.short_description = _("Entity type")

    @property
    def entity_model(self):
        """
        Returns the polymorphic model name of the object's class.
        """
        return self.polymorphic_ctype.model

    def get_absolute_url(self):
        """
        Hook for returning the canonical Django URL of this object.
        """
        msg = "Method get_absolute_url() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

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

    def get_availability(self, request):
        """
        Hook for checking the availability of a object. It returns a list of tuples with this
        notation:
        - Number of items available for this object until the specified period expires.
          If this value is ``True``, then infinitely many items are available.
        - Until which timestamp, in UTC, the specified number of items are available.
        This function can return more than one tuple. If the list is empty, then the object is
        considered as not available.
        Use the `request` object to vary the availability according to the logged in user,
        its country code or language.
        """
        return [(True, datetime.max)]  # Infinite number of objects available until eternity

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

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        result = super(BaseEntity, self).save(force_insert, force_update, *args, **kwargs)
        return result

    @cached_property
    def additional_characteristics(self):
        """
        Return additional characteristics of current entity
        """
        tree_opts = TermModel._mptt_meta
        return AdditionalEntityCharacteristicOrMarkModel.objects.filter(
            entity=self, term__attributes=TermModel.attributes.is_characteristic).order_by(
            'term__{}'.format(tree_opts.tree_id_attr), 'term__{}'.format(tree_opts.left_attr))

    @cached_property
    def additional_marks(self):
        """
        Return additional marks of current entity
        """
        tree_opts = TermModel._mptt_meta
        return AdditionalEntityCharacteristicOrMarkModel.objects.filter(
            entity=self, term__attributes=TermModel.attributes.is_mark).order_by(
            'term__{}'.format(tree_opts.tree_id_attr), 'term__{}'.format(tree_opts.left_attr))

    @cached_property
    def active_terms_for_characteristics(self):
        """
        Return terms for characteristics of current entity
        """
        tree_opts = TermModel._mptt_meta
        descendants_ids = TermModel.get_all_active_characteristics_descendants_ids()
        return list(self.terms.filter(id__in=descendants_ids).order_by(tree_opts.tree_id_attr, tree_opts.left_attr))

    @cached_property
    def active_terms_for_marks(self):
        """
        Return terms for marks of current entity
        """
        tree_opts = TermModel._mptt_meta
        descendants_ids = TermModel.get_all_active_marks_descendants_ids()
        return list(self.terms.filter(id__in=descendants_ids).order_by(tree_opts.tree_id_attr, tree_opts.left_attr))

    @cached_property
    def characteristics(self):
        """
        Return all characteristics objects of current entity
        """
        tree_opts = TermModel._mptt_meta
        result = ProductCharacteristicOrMarkSet(
            self.active_terms_for_characteristics,
            self.additional_characteristics,
            TermModel.attributes.is_characteristic,
            tree_opts).all()

        print "c>>>>>", result

        return result

        '''
        result = [
            {
                "path": "kategoriya/kondicionirovanie/moshnost",
                "name": "Мощность",
                "value": "до 2,3 кВт",
                "view_class": ""
            },
            {
                "path": "base/proizvoditelnost\u002Dv\u002Drezhime\u002Dohlazhdeniya\u002Dkvt",
                "name": "Производительность в режиме охлаждения, кВт",
                "value": "2,2",
                "view_class": "red only-group"
            }
        ]

        return result
        '''

    @cached_property
    def marks(self):
        """
        Return all marks objects of current entity
        """
        tree_opts = TermModel._mptt_meta
        result = ProductCharacteristicOrMarkSet(
                self.active_terms_for_marks,
                self.additional_marks,
                TermModel.attributes.is_mark,
                tree_opts).all()

        print "m>>>>>", result

        return result


EntityModel = deferred.MaterializedModel(BaseEntity)