# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from six import with_metaclass

from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db import models

from filer.fields import image

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

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if not force_update:
            self.view_class = ' '.join([x.lower() for x in self.view_class.split()]) if self.view_class else None
        return super(BaseAdditionalEntityCharacteristicOrMark, self).save(force_insert, force_update, *args, **kwargs)


AdditionalEntityCharacteristicOrMarkModel = deferred.MaterializedModel(BaseAdditionalEntityCharacteristicOrMark)


#==============================================================================
# BaseEntityRelation
#==============================================================================
@python_2_unicode_compatible
class BaseEntityRelation(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    Allows to be attached related entities.
    """
    from_entity = deferred.ForeignKey('BaseEntity', related_name='forward_relations', verbose_name=_('From Entity'))
    to_entity = deferred.ForeignKey('BaseEntity', related_name='backward_relations', verbose_name=_('To Entity'))
    term = deferred.ForeignKey('BaseTerm', verbose_name=_('Term'), related_name='+', db_index=True)

    class Meta:
        abstract = True
        verbose_name = _("Entity Relation")
        verbose_name_plural = _("Entity Relations")
        unique_together = ('term', 'from_entity', 'to_entity',)

    def __str__(self):
        return "{} → {} → {}".format(self.from_entity.entity_name, self.term.name, self.to_entity.entity_name)


EntityRelationModel = deferred.MaterializedModel(BaseEntityRelation)


#==============================================================================
# BaseEntityRelatedDataMart
#==============================================================================
@python_2_unicode_compatible
class BaseEntityRelatedDataMart(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    Entity related data marts
    """
    entity = deferred.ForeignKey('BaseEntity', verbose_name=_('Entity'), related_name='+')
    data_mart = deferred.ForeignKey('BaseDataMart', verbose_name=_('Data mart'), related_name='+')

    class Meta:
        abstract = True
        verbose_name = _("Related data mart")
        verbose_name_plural = _("Entity related data marts")

    def __str__(self):
        return "{} → {}".format(self.entity.entity_name, self.data_mart.name)


EntityRelatedDataMartModel = deferred.MaterializedModel(BaseEntityRelatedDataMart)


#==============================================================================
# BaseEntityImage
#==============================================================================
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


EntityImageModel = deferred.MaterializedModel(BaseEntityImage)
