# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import operator

from six import with_metaclass

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.cache import cache
from django.db import models, IntegrityError, transaction
from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from mptt.models import MPTTModel, MPTTModelBase
from mptt.managers import TreeManager
from mptt.querysets import TreeQuerySet
from mptt.exceptions import InvalidMove

from bitfield import BitField

from . import deferred
from .cache import add_cache_key, QuerySetCachedResultMixin
from .fields import TreeForeignKey
from ..utils.hash_helpers import get_unique_slug, hash_unsorted_list
from ..utils.set_helpers import uniq
from ..utils.circular_buffer_in_cache import RingBuffer
from ..signals.mptt import MPTTModelSignalSenderMixin

from .. import settings as edw_settings


#==============================================================================
# BaseTermQuerySet
#==============================================================================
class BaseTermQuerySet(QuerySetCachedResultMixin, TreeQuerySet):

    @add_cache_key('actv')
    def active(self):
        return self.filter(active=True)

    def hard_delete(self):
        return super(BaseTermQuerySet, self).delete()

    def delete(self):
        return super(BaseTermQuerySet, self.exclude(system_flags=self.model.system_flags.delete_restriction)).delete()

    @add_cache_key('toplvl')
    def toplevel(self):
        """
        :return: all nodes which have no parent
        """
        return self.filter(parent__isnull=True)

    def attribute_is_characteristic_or_mark(self):
        return self.filter(Q(attributes=self.model.attributes.is_characteristic) |
                           Q(attributes=self.model.attributes.is_mark))

    def _get_attribute_filter_cache_key(self, attribute_mode):
        return self.model.ATTRIBUTE_FILTER_CACHE_KEY_PATTERN.format(
            mode=int(attribute_mode)
        )

    @add_cache_key(_get_attribute_filter_cache_key)
    def attribute_filter(self, attribute_mode):
        return self.filter(attributes=attribute_mode)

    def _get_select_related_cache_key(self, *fields):
        return self.model.SELECT_RELATED_CACHE_KEY_PATTERN.format(
            fields=':'.join(fields)
        )

    @add_cache_key(_get_select_related_cache_key)
    def select_related(self, *fields):
        return super(BaseTermQuerySet, self).select_related(*fields)

    def attribute_is_relation(self):
        return self.filter(attributes=self.model.attributes.is_relation)


#==============================================================================
# BaseTermManager
#==============================================================================
class BaseTermManager(TreeManager.from_queryset(BaseTermQuerySet)):
    """
    Customized model manager for our Term model.
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
# SemanticRuleFilterMixin
#==============================================================================
class SemanticRuleFilterMixin(object):

    def make_filters(self, *args, **kwargs):
        '''
        :return: queryset filters
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


#==============================================================================
# BaseTermMetaclass
#==============================================================================
class BaseTermMetaclass(MPTTModelBase):
    """
    The BaseTerm class must refer to their materialized model definition, for instance when
    accessing its model manager.
    """
    def __new__(cls, name, bases, attrs):

        class Meta:
            app_label = edw_settings.APP_LABEL

        attrs.setdefault('Meta', Meta)
        if not hasattr(attrs['Meta'], 'app_label') and not getattr(attrs['Meta'], 'abstract', False):
            attrs['Meta'].app_label = Meta.app_label
        attrs.setdefault('__module__', getattr(bases[-1], '__module__'))

        Model = super(BaseTermMetaclass, cls).__new__(cls, name, bases, attrs)
        if Model._meta.abstract:
            return Model
        for baseclass in bases:
            # classes which materialize an abstract model are added to a mapping dictionary
            basename = baseclass.__name__
            try:
                if not issubclass(Model, baseclass) or not baseclass._meta.abstract:
                    raise ImproperlyConfigured("Base class %s is not abstract." % basename)
            except (AttributeError, NotImplementedError):
                pass
            else:
                if basename in deferred.ForeignKeyBuilder._materialized_models:
                    if Model.__name__ != deferred.ForeignKeyBuilder._materialized_models[basename]:
                        raise AssertionError("Both Model classes '%s' and '%s' inherited from abstract"
                            "base class %s, which is disallowed in this configuration." %
                            (Model.__name__, deferred.ForeignKeyBuilder._materialized_models[basename], basename))
                elif isinstance(baseclass, cls):
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
        Perform some safety checks on the TermModel being created.
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
    The fundamental parts of a enterprise data warehouse. In detail focused hierarchical dictionary of terms.
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
    name = models.CharField(verbose_name=_('Name'), max_length=255)
    slug = models.SlugField(_("Slug"), help_text=_("Used for URLs, auto-generated from name if blank."))
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
        abstract = True
        verbose_name = _("Term")
        verbose_name_plural = _("Topic model")

    class MPTTMeta:
        order_insertion_by = ['created_at']

    def __str__(self):
        return self.name

    def make_filters(self, *args, **kwargs):
        if self.semantic_rule == self.AND_RULE:
            return AndRuleFilterMixin.make_filters(self, *args, **kwargs)
        else:
            return OrRuleFilterMixin.make_filters(self, *args, **kwargs)

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
                if self.system_flags.change_semantic_rule_restriction and origin.semantic_rule != self.semantic_rule:
                    raise ValidationError(self.messages['change_semantic_rule_restriction'])
        if self.parent_id is not None and self.parent.system_flags.has_child_restriction:
            if origin is None or origin.parent_id != self.parent_id:
                raise ValidationError(self.messages['has_child_restriction'])
        return super(BaseTerm, self).clean(*args, **kwargs)

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
            self._make_path(ancestors + [self, ])
            try:
                with transaction.atomic():
                    result = super(BaseTerm, self).save(*args, **kwargs)
            except IntegrityError as e:
                if model_class._default_manager.exclude(pk=self.pk).filter(path=self.path).exists():
                    self.slug = get_unique_slug(self.slug, self.id)
                    self._make_path(ancestors + [self, ])
                    result = super(BaseTerm, self).save(*args, **kwargs)
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
        if not self.system_flags.delete_restriction:
            super(BaseTerm, self).delete()

    def hard_delete(self):
        super(BaseTerm, self).delete()

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
        super(BaseTerm, self).move_to(target, position)

    def get_children_cache_key(self):
        return self.CHILDREN_CACHE_KEY_PATTERN.format(
            parent_id=self.id
        )

    @add_cache_key(get_children_cache_key)
    def get_children(self):
        return super(BaseTerm, self).get_children()

    def get_ancestors_cache_key(self, ascending=False, include_self=False):
        return self.ANCESTORS_CACHE_KEY_PATTERN.format(
            id=self.id,
            ascending=ascending,
            include_self=include_self
        )

    @add_cache_key(get_ancestors_cache_key)
    def get_ancestors(self, ascending=False, include_self=False):
        return super(BaseTerm, self).get_ancestors(ascending, include_self)
    
    @staticmethod
    def decompress(*args, **kwars):
        """
        Shortcut to TermInfo.decompress method
        """
        return TermInfo.decompress(TermModel, *args, **kwars)

    @staticmethod
    def get_decompress_buffer():
        return RingBuffer.factory(BaseTerm.DECOMPRESS_BUFFER_CACHE_KEY,
                                  max_size=BaseTerm.DECOMPRESS_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_decompress_buffer():
        buf = BaseTerm.get_decompress_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    @staticmethod
    def cached_decompress(value=None, fix_it=False):
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
        return RingBuffer.factory(BaseTerm.CHILDREN_BUFFER_CACHE_KEY,
                                  max_size=BaseTerm.CHILDREN_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_children_buffer():
        buf = BaseTerm.get_children_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    @staticmethod
    def get_attribute_ancestors_buffer():
        return RingBuffer.factory(BaseTerm.ATTRIBUTE_ANCESTORS_BUFFER_CACHE_KEY,
                                  max_size=BaseTerm.ATTRIBUTE_ANCESTORS_BUFFER_CACHE_SIZE)

    @staticmethod
    def clear_attribute_ancestors_buffer():
        buf = BaseTerm.get_attribute_ancestors_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

    @staticmethod
    def get_all_active_characteristics_descendants_ids():
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


#==============================================================================
# TermModel
#==============================================================================
TermModel = deferred.MaterializedModel(BaseTerm)


#==============================================================================
# get_queryset_descendants
#==============================================================================
def get_queryset_descendants(nodes, include_self=False):
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
    """
    def __init__(self, root=None, *args, **kwargs):
        self.root = root
        super(TermTreeInfo, self).__init__(*args, **kwargs)

    def get_hash(self):
        keys = [x.term.id for x in self.values() if x.is_leaf]
        return hash_unsorted_list(keys) if keys else ''

    def trim(self, ids=None):
        tree = self.deepcopy()
        tree._expand()
        return tree._trim(ids)

    def _expand(self):
        terms = [x.term for x in self.values() if x.is_leaf]
        if terms:
            for term in get_queryset_descendants(terms, include_self=False).filter(active=True):
                ancestor = self.get(term.parent_id)
                child = self[term.id] = TermInfo(term=term, is_leaf=True)
                ancestor.is_leaf = False
                ancestor.append(child)

    def _trim(self, ids=None):
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
        node = self[src_node.term.id] = TermInfo(term=src_node.term, is_leaf=src_node.is_leaf)
        for src_child in src_node:
            node.append(self._copy_recursively(src_child))
        return node

    def deepcopy(self):
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
    """
    def __init__(self, term=None, is_leaf=False, children=(), attrs=None):
        super(TermInfo, self).__init__(children)
        self.attrs = attrs or {}
        self.term, self.is_leaf = term, is_leaf

    def get_children_dict(self):
        result = {}
        for child in self:
            result[child.term.id] = child
        return result

    def get_descendants_ids(self):
        result = []
        for child in self:
            result.append(child.term.id)
            result.extend(child.get_descendants_ids())
        return result

    @staticmethod
    def decompress(model_class, value=None, fix_it=False): # todo: root_pk=None
        if value is None:
            value = []
        value = uniq(value)

        # todo: make soft root
        # ____________________

        root = TermInfo(term=model_class(semantic_rule=model_class.ROOT_RULE, active=True))

        # ____________________

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

        if fix_it:
            invalid_ids = []
            for x in [x for x in tree.values() if not x.is_leaf]:
                if len(x) > 1 and (x.term.semantic_rule == BaseTerm.XOR_RULE):
                    invalid_ids.extend(x.get_descendants_ids())
                    x.is_leaf = True
                    del x[:]
            for id in invalid_ids:
                del tree[id]

        return tree

