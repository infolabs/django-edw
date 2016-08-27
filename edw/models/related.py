# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from six import with_metaclass

from django.utils.translation import ugettext_lazy as _
from django.db import models

from ..models import deferred


#==============================================================================
# BaseAdditionalEntityCharacteristicOrMark
#==============================================================================
class BaseAdditionalEntityCharacteristicOrMark(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    ManyToMany relation from the polymorphic Entity to a set of Terms.
    """
    entity = deferred.ForeignKey('BaseEntity', verbose_name=_('Entity'),
                                 related_name='additional_characteristics_or_marks')
    term = deferred.ForeignKey('BaseTerm', verbose_name=_('Term'), db_index=True,
                               related_name='entity_additional_characteristics_or_marks')
    view_class = models.CharField(verbose_name=_('View Class'), max_length=255, null=True, blank=True,
                                  help_text=
                                  _('Space delimited class attribute, specifies one or more classnames for an entity.'))

    class Meta:
        abstract = True
        verbose_name = _("Additional Entity Characteristic or Mark")
        verbose_name_plural = _("Additional Entity Characteristics or Marks")

AdditionalEntityCharacteristicOrMarkModel = deferred.MaterializedModel(BaseAdditionalEntityCharacteristicOrMark)