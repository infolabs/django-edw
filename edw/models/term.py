# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import with_metaclass
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, MPTTModelBase
from mptt.managers import TreeManager

from . import deferred
from .fields import TreeForeignKey


class BaseTermManager(TreeManager):
    """
    Customized model manager for our Term model.
    """
    pass


class BaseTermMetaclass(MPTTModelBase):
    """
    The BaseTerm class must refer to their materialized model definition, for instance when
    accessing its model manager.
    """
    def __new__(cls, name, bases, attrs):
        Model = super(BaseTermMetaclass, cls).__new__(cls, name, bases, attrs)
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

            # check for pending mappings in the ForeignKeyBuilder and in case, process them
            deferred.ForeignKeyBuilder.process_pending_mappings(Model, baseclass.__name__)

        cls.perform_model_checks(Model)
        return Model

    @classmethod
    def perform_model_checks(cls, Model):
        """
        Perform some safety checks on the TermModel being created.
        """
        if not isinstance(Model.objects, BaseTermManager):
            msg = "Class `{}.objects` must provide ModelManager inheriting from BaseTermManager"
            raise NotImplementedError(msg.format(Model.__name__))


class BaseTerm(with_metaclass(BaseTermMetaclass, MPTTModel)):
    """
    The fundamental parts of a enterprise data warehouse. In detail focused hierarchical dictionary of terms.
    """
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=_('parent'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    active = models.BooleanField(default=True, verbose_name=_("Active"), db_index=True,
                                 help_text=_("Is this term active."))

    objects = BaseTermManager()

    # Whether the node type allows to have children.
    can_have_children = True

    class Meta:
        abstract = True
        verbose_name = _("Term")
        verbose_name_plural = _("Terms")


TermModel = deferred.MaterializedModel(BaseTerm)