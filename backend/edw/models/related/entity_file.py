# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from six import with_metaclass

from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db import models

from filer.fields.file import FilerFileField

from edw.models import deferred


#==============================================================================
# BaseEntityFile
#==============================================================================
@python_2_unicode_compatible
class BaseEntityFile(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    ManyToMany relation from the polymorphic Entity to a set of files.
    """
    file = FilerFileField(verbose_name=_('File'))
    entity = deferred.ForeignKey('BaseEntity', verbose_name=_('Entity'))
    order = models.SmallIntegerField(default=0, blank=False, null=False)

    class Meta:
        abstract = True
        verbose_name = _("Entity File")
        verbose_name_plural = _("Entity Files")
        ordering = ('order',)

    def __str__(self):
        return "{}".format(self.file)


EntityFileModel = deferred.MaterializedModel(BaseEntityFile)