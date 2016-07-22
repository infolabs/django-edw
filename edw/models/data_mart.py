# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#import operator
from six import with_metaclass
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models, IntegrityError, transaction
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, MPTTModelBase
from mptt.managers import TreeManager
from mptt.exceptions import InvalidMove

from polymorphic.manager import PolymorphicManager
from polymorphic.models import PolymorphicModel
from polymorphic.base import PolymorphicModelBase
from polymorphic.query import PolymorphicQuerySet

from bitfield import BitField

from . import deferred
from .fields import TreeForeignKey
from ..utils.hash_helpers import get_unique_slug

from .. import settings as edw_settings


class BaseDataMartQuerySet(PolymorphicQuerySet):

    def active(self):
        return self.filter(active=True)

    def hard_delete(self):
        return super(BaseDataMartQuerySet, self).delete()

    def delete(self):
        return super(BaseDataMartQuerySet, self.exclude(system_flags=self.model.system_flags.delete_restriction)).delete()


class BaseDataMartManager(TreeManager, PolymorphicManager):
    """
    Customized model manager for our DataMart model.
    """
    #: The queryset class to use.
    queryset_class = BaseDataMartQuerySet

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

class BaseDataMartMetaclass(MPTTModelBase, PolymorphicModelBase):
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

        #-----------------------------
        '''
        Model = super(BaseDataMartMetaclass, cls).__new__(cls, name, bases, attrs)
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
        '''
        #-----------------------------

        Model = super(BaseDataMartMetaclass, cls).__new__(cls, name, bases, attrs)
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

        #-----------------------------

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
        Perform some safety checks on the DataMartModel being created.
        """
        if not isinstance(Model.objects, BaseDataMartManager):
            msg = "Class `{}.objects` must provide ModelManager inheriting from `{}`"
            raise NotImplementedError(msg.format(Model.__name__, BaseDataMartManager.__name__))


@python_2_unicode_compatible
class BaseDataMart(with_metaclass(BaseDataMartMetaclass, MPTTModel, PolymorphicModel)):
    """
    The data marts for a enterprise data warehouse.
    """

    SYSTEM_FLAGS = {
        0: ('delete_restriction', _('Delete restriction')),
        1: ('change_parent_restriction', _('Change parent restriction')),
        2: ('change_slug_restriction', _('Change slug restriction')),
        3: ('has_child_restriction', _('Has child restriction')),
    }

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=_('Parent'))
    name = models.CharField(verbose_name=_('Name'), max_length=255)
    slug = models.SlugField(_("Slug"), help_text=_("Used for URLs, auto-generated from name if blank"))
    path = models.CharField(verbose_name=_("Path"), max_length=255, db_index=True, editable=False, unique=True)

    terms = deferred.ManyToManyField('BaseTerm', related_name='+', verbose_name=_('Terms'), blank=True,
                                     help_text=_("""Use "ctrl" key for choose multiple terms"""))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    view_class = models.CharField(verbose_name=_('View Class'), max_length=255, null=True, blank=True,
                                  help_text=_('Space delimited class attribute, specifies one or more classnames for an data mart.'))
    description = models.TextField(verbose_name=_('Description'), null=True, blank=True)
    active = models.BooleanField(default=True, verbose_name=_("Active"), db_index=True,
                                 help_text=_("Is this data mart active."))

    system_flags = BitField(flags=SYSTEM_FLAGS, verbose_name=_('system flags'), null=True, default=None)

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
        return super(BaseDataMart, self).clean(*args, **kwargs)

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
                    result = super(BaseDataMart, self).save(*args, **kwargs)
            except IntegrityError as e:
                if model_class._default_manager.exclude(pk=self.pk).filter(path=self.path).exists():
                    self.slug = get_unique_slug(self.slug, self.id)
                    self._make_path(ancestors + [self, ])
                    result = super(BaseDataMart, self).save(*args, **kwargs)
                else:
                    raise e
            if not origin or origin.active != self.active:
                update_id_list = [x.id for x in self.get_descendants(include_self=False)]
                if self.active:
                    update_id_list.extend([x.id for x in self.get_ancestors_list()])
                model_class._default_manager.filter(id__in=update_id_list).update(active=self.active)
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
        super(BaseDataMart, self).move_to(target, position)

DataMartModel = deferred.MaterializedModel(BaseDataMart)