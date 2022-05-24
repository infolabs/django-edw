# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from six import with_metaclass, python_2_unicode_compatible

from django.utils.translation import ugettext_lazy as _
from django.db import models

from filer.fields import image

from edw import deferred


#==============================================================================
# BaseBaseDataMartImage
#==============================================================================
@python_2_unicode_compatible
class BaseDataMartImage(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    ENG: ManyToMany relation from the polymorphic Datamart to a set of images.
    RUS: Связь многие-ко многим от полиморфной Витрины данных к изображениям.
    """
    image = image.FilerImageField(on_delete=models.CASCADE, verbose_name=_('Image'))
    data_mart = deferred.ForeignKey('BaseDataMart', on_delete=models.CASCADE, verbose_name=_('DataMart'))
    order = models.SmallIntegerField(default=0, blank=False, null=False, db_index=True)

    class Meta:
        """
        RUS: Метаданные класса.
        """
        abstract = True
        verbose_name = _("DataMart Image")
        verbose_name_plural = _("DataMart Images")
        ordering = ('order',)

    def __str__(self):
        """
        RUS: Строковое представление данных.
        """
        return "{}".format(self.image)


DataMartImageModel = deferred.MaterializedModel(BaseDataMartImage)
