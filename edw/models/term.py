# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import operator

from six import with_metaclass

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models, IntegrityError, transaction
from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, MPTTModelBase
from mptt.managers import TreeManager
from mptt.querysets import TreeQuerySet
from mptt.exceptions import InvalidMove

from bitfield import BitField

from . import deferred
from .fields import TreeForeignKey
from ..utils.hash_helpers import get_unique_slug, hash_unsorted_list
from ..utils.set_helpers import uniq

from .. import settings as edw_settings


class BaseTermQuerySet(TreeQuerySet):

    def active(self):
        return self.filter(active=True)

    def hard_delete(self):
        return super(BaseTermQuerySet, self).delete()

    def delete(self):
        return super(BaseTermQuerySet, self.exclude(system_flags=self.model.system_flags.delete_restriction)).delete()

    def toplevel(self):
        """
        :return: all nodes which have no parent
        """
        return self.filter(parent__isnull=True)


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
            mapmodel = deferred.ForeignKeyBuilder._materialized_models.get(member.abstract_model)
            if mapmodel:
                field = member.MaterializedField(mapmodel, **member.options)
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


@python_2_unicode_compatible
class BaseTerm(with_metaclass(BaseTermMetaclass, MPTTModel)):
    """
    The fundamental parts of a enterprise data warehouse. In detail focused hierarchical dictionary of terms.
    """
    OR_RULE = 10
    XOR_RULE = 20
    AND_RULE = 30
    SEMANTIC_RULES = (
        (OR_RULE, _('OR')),
        (XOR_RULE, _('XOR')),
        (AND_RULE, _('AND')),
    )

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

    SYSTEM_FLAGS = {
        0: ('delete_restriction', _('Delete restriction')),
        1: ('change_parent_restriction', _('Change parent restriction')),
        2: ('change_slug_restriction', _('Change slug restriction')),
        3: ('change_semantic_rule_restriction', _('Change semantic rule restriction')),
        4: ('has_child_restriction', _('Has child restriction')),
        5: ('external_tagging_restriction', _('External tagging restriction')),
    }

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=_('Parent'))
    name = models.CharField(verbose_name=_('Name'), max_length=255)
    slug = models.SlugField(_("Slug"), help_text=_("Used for URLs, auto-generated from name if blank"))
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
        verbose_name_plural = _("Terms")

    class MPTTMeta:
        order_insertion_by = ['created_at']

    def __str__(self):
        return self.name

    def get_ancestors_list(self):
        if not hasattr(self, '_ancestors_cache'):
            self._ancestors_cache = []
            if self.parent:
                self._ancestors_cache = list(self.parent.get_ancestors(include_self=True))
        return self._ancestors_cache

    def clean(self, *args, **kwargs):
        model_class = self.__class__
        try:
            origin = model_class._default_manager.get(pk=self.pk)
        except model_class.DoesNotExist:
            origin = None
        if self.system_flags:
            if not origin is None:
                if self.system_flags.change_slug_restriction and origin.slug != self.slug:
                    raise ValidationError(self.system_flags.get_label('change_slug_restriction'))
                if self.system_flags.change_parent_restriction and origin.parent_id != self.parent_id:
                    raise ValidationError(self.system_flags.get_label('change_parent_restriction'))
        if not self.parent_id is None and self.parent.system_flags.has_child_restriction:
            if origin is None or origin.parent_id != self.parent_id:
                raise ValidationError(self.system_flags.get_label('has_child_restriction'))
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
            ancestors = self.get_ancestors_list()
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
                update_id_list = [x.id for x in self.get_descendants(include_self=False)]
                if self.active:
                    update_id_list.extend([x.id for x in self.get_ancestors_list()])
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
            if self.system_flags.change_parent_restriction and target.parent_id != self.parent_id:
                raise InvalidMove(self.system_flags.get_label('change_parent_restriction'))
            if not target.parent_id is None and target.parent.system_flags.has_child_restriction and target.parent_id != self.parent_id:
                raise InvalidMove(self.system_flags.get_label('has_child_restriction'))
        elif position in ('first-child', 'last-child'):
            if target.id != self.parent_id:
                if self.system_flags.change_parent_restriction:
                    raise InvalidMove(self.system_flags.get_label('change_parent_restriction'))
                if target.system_flags.has_child_restriction:
                    raise InvalidMove(self.system_flags.get_label('has_child_restriction'))
        super(BaseTerm, self).move_to(target, position)

    '''
    @models.permalink
    def get_absolute_url(self):
        return "edw:api:{}-detail".format(self.__class__.__name__.lower()), (), {'pk': self.pk}
    '''

    @staticmethod
    def decompress(value=None, fix_it=False):
        """
        Shortcut to TermInfo.decompress method
        """
        return TermInfo.decompress(TermModel, value, fix_it)


TermModel = deferred.MaterializedModel(BaseTerm)


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
        #ids = uniq(ids)
        root_model_class = self.root.term.__class__
        root = TermInfo(term=root_model_class())
        tree = TermTreeInfo(root)
        for id in ids:
            src_node = self.get(id)
            if not src_node is None:
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
    def decompress(model_class, value=None, fix_it=False):
        if value is None:
            value = []
        value = uniq(value)
        root = TermInfo(term=model_class())
        tree = TermTreeInfo(root)
        for term in model_class._default_manager.filter(pk__in=value).select_related('parent'):
            if not term.id in tree:
                node = tree[term.id] = TermInfo(term=term, is_leaf=True)
                term_parent = term.parent
                if term_parent:
                    ancestor = tree.get(term_parent.id)
                    if not ancestor is None:
                        ancestor.is_leaf = False
                        ancestor.append(node)
                    else:
                        node = tree[term_parent.id] = TermInfo(term=term_parent, is_leaf=False, children=[node])
                        if not term_parent.parent_id is None:
                            for term_ancestor in term_parent.get_ancestors(ascending=True).exclude(pk__in=tree.keys()):
                                node = tree[term_ancestor.id] = TermInfo(term=term_ancestor, is_leaf=False, children=[node])
                            ancestor = tree.get(node.term.parent_id)
                            if not ancestor is None:
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



'''
class CachedTermInfo(TermInfo):

    CACHE_TIMEOUT = 3600

    DECOMPRESS_BUFFER_CACHE_KEY = 'dc_bf'
    DECOMPRESS_BUFFER_CACHE_SIZE = 500
    DECOMPRESS_TREE_CACHE_KEY_PATTERN = 'tr_i::%(model_name)s:%(value_hash)s:%(fix_it)s'

    @staticmethod
    def cached_decompress(model_class, value=None, fix_it=False):
        key = RubricInfo.DECOMPRESS_TREE_CACHE_KEY_PATTERN % {
            "model_name": model_class.__name__,
            "value_hash": hash_unsorted_list(value) if value else '',
            "fix_it": 'Y' if fix_it else 'N'
        }
        tree = cache.get(key, None)
        if tree is None:
            tree = RubricInfo.decompress(model_class, value, fix_it)
            cache.set(key, tree, RubricInfo.CACHE_TIMEOUT)
            buf = RubricInfo.get_decompress_buffer()
            old_key = buf.record(key)
            if not old_key is None:
                cache.delete(old_key)
        return tree

    @staticmethod
    def get_decompress_buffer():
        return RingBuffer.factory(RubricInfo.DECOMPRESS_BUFFER_CACHE_KEY,
                                  max_size=RubricInfo.DECOMPRESS_BUFFER_CACHE_SIZE, empty=None)

    @staticmethod
    def clear_decompress_buffer():
        buf = RubricInfo.get_decompress_buffer()
        keys = buf.get_all()
        buf.clear()
        cache.delete_many(keys)

'''