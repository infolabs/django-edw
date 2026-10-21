# -*- coding: utf-8 -*-
from __future__ import unicode_literals



from django.utils.translation import gettext_lazy as _
from django.db import models

from filer.fields import image

from edw import deferred


#==============================================================================
# BaseEntityImage
#==============================================================================
class BaseEntityImage(models.Model, metaclass=deferred.ForeignKeyBuilder):
    """
    ENG: ManyToMany relation from the polymorphic Entity to a set of images.
    RUS: Связь многие-ко многим от полиморфной Сущности к изображениям.
    """
    image = image.FilerImageField(on_delete=models.CASCADE, verbose_name=_('Image'))
    entity = deferred.ForeignKey('BaseEntity', on_delete=models.CASCADE, verbose_name=_('Entity'))
    order = models.SmallIntegerField(default=0, blank=False, null=False, db_index=True)

    class Meta:
        """
        RUS: Метаданные класса.
        """
        abstract = True
        verbose_name = _("Entity Image")
        verbose_name_plural = _("Entity Images")
        ordering = ('order',)
        unique_together = (('image', 'entity'),)

    def __str__(self):
        """
        RUS: Строковое представление данных.
        """
        return "{}".format(self.image)


EntityImageModel = deferred.MaterializedModel(BaseEntityImage)
