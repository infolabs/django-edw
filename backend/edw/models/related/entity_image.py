# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from six import with_metaclass

from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db import models

from filer.fields import image

from edw.models import deferred



#==============================================================================
# BaseEntityImage
#==============================================================================
@python_2_unicode_compatible
class BaseEntityImage(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    ManyToMany relation from the polymorphic Entity to a set of images.
    """
    image = image.FilerImageField(verbose_name=_('Image'))
    entity = deferred.ForeignKey('BaseEntity', verbose_name=_('Entity'))
    order = models.SmallIntegerField(default=0, blank=False, null=False)

    class Meta:
        abstract = True
        verbose_name = _("Entity Image")
        verbose_name_plural = _("Entity Images")
        ordering = ('order',)

    def __str__(self):
        return "{}".format(self.image)


EntityImageModel = deferred.MaterializedModel(BaseEntityImage)