# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from six import with_metaclass

from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db import models

from ..models import deferred


#==============================================================================
# BaseAdditionalEntityCharacteristicOrMark
#==============================================================================
@python_2_unicode_compatible
class BaseAdditionalEntityCharacteristicOrMark(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    ManyToMany relation from the polymorphic Entity to a set of Terms.
    """
    term = deferred.ForeignKey('BaseTerm', verbose_name=_('Term'), db_index=True)
    entity = deferred.ForeignKey('BaseEntity', verbose_name=_('Entity'))
    value = models.CharField(_("Value"), max_length=255)
    view_class = models.CharField(verbose_name=_('View Class'), max_length=255, null=True, blank=True,
                                  help_text=
                                  _('Space delimited class attribute, specifies one or more classnames for an entity.'))

    class Meta:
        abstract = True
        verbose_name = _("Additional Entity Characteristic or Mark")
        verbose_name_plural = _("Additional Entity Characteristics or Marks")

    def __str__(self):
        return "{}: {}".format(self.term.name, self.value)

AdditionalEntityCharacteristicOrMarkModel = deferred.MaterializedModel(BaseAdditionalEntityCharacteristicOrMark)