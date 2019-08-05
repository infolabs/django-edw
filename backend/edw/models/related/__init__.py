# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from six import with_metaclass

from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db import models

from edw import deferred


#==============================================================================
# BaseAdditionalEntityCharacteristicOrMark
#==============================================================================
@python_2_unicode_compatible
class BaseAdditionalEntityCharacteristicOrMark(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    ENG: ManyToMany relation from the polymorphic Entity to a set of Terms.
    RUS: Связь многие-ко многим от полиморфной Сущности к Терминам.
    """
    term = deferred.ForeignKey('BaseTerm', verbose_name=_('Term'), related_name='+', db_index=True)
    entity = deferred.ForeignKey('BaseEntity', verbose_name=_('Entity'), related_name='+')
    value = models.CharField(_("Value"), max_length=255)
    view_class = models.CharField(verbose_name=_('View Class'), max_length=255, null=True, blank=True,
                                  help_text=
                                  _('Space delimited class attribute, specifies one or more classnames for an entity.'))

    class Meta:
        """
        RUS: Метаданные класса.
        """
        abstract = True
        verbose_name = _("Additional Entity Characteristic or Mark")
        verbose_name_plural = _("Additional Entity Characteristics or Marks")

    def __str__(self):
        """
        RUS: Строковое представление данных.
        """
        return "{}: {}".format(self.term.name, self.value)

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        """
        RUS: Сохраняет объект в базе данных.
        """
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
    ENG: Allows to be attached related entities.
    RUS: Позволяет присоединять связанные сущности.
    """
    from_entity = deferred.ForeignKey('BaseEntity', related_name='forward_relations', verbose_name=_('From Entity'))
    to_entity = deferred.ForeignKey('BaseEntity', related_name='backward_relations', verbose_name=_('To Entity'))
    term = deferred.ForeignKey('BaseTerm', verbose_name=_('Term'), related_name='+', db_index=True)

    class Meta:
        """
        RUS: Метаданные класса.
        """
        abstract = True
        verbose_name = _("Entity Relation")
        verbose_name_plural = _("Entity Relations")
        unique_together = (('term', 'from_entity', 'to_entity'),)

    def __str__(self):
        """
        RUS: Строковое представление данных.
        """
        return "{} → {} → {}".format(self.from_entity.get_real_instance().entity_name, self.term.name,
                                     self.to_entity.get_real_instance().entity_name)


EntityRelationModel = deferred.MaterializedModel(BaseEntityRelation)


#==============================================================================
# BaseEntityRelatedDataMart
#==============================================================================
@python_2_unicode_compatible
class BaseEntityRelatedDataMart(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    ENG: Entity related data marts.
    RUS: Сущность связанных витрин данных.
    """
    entity = deferred.ForeignKey('BaseEntity', verbose_name=_('Entity'), related_name='+')
    data_mart = deferred.ForeignKey('BaseDataMart', verbose_name=_('Data mart'), related_name='+')

    class Meta:
        """
        RUS: Метаданные класса.
        """
        abstract = True
        verbose_name = _("Related data mart")
        verbose_name_plural = _("Entity related data marts")

    def __str__(self):
        """
        RUS: Строковое представление данных.
        """
        return "{} → {}".format(self.entity.get_real_instance().entity_name, self.data_mart.name)


EntityRelatedDataMartModel = deferred.MaterializedModel(BaseEntityRelatedDataMart)


#==============================================================================
# BaseDataMartRelation
#==============================================================================
@python_2_unicode_compatible
class BaseDataMartRelation(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    ENG: Entity related data marts.
    RUS: Сущность связанных витрин данных.
    """
    RELATION_BIDIRECTIONAL = "b"
    RELATION_FORWARD = "f"
    RELATION_REVERSE = "r"

    RELATION_DIRECTIONS = (
        (RELATION_BIDIRECTIONAL, _('Bidirectional')),
        (RELATION_FORWARD, _('Forward')),
        (RELATION_REVERSE, _('Reverse')),
    )

    data_mart = deferred.ForeignKey('BaseDataMart', verbose_name=_('Data mart'), related_name='relations')
    term = deferred.ForeignKey('BaseTerm', verbose_name=_('Term'), related_name='+')
    direction = models.CharField(_("Relation direction"),
                                 max_length=1,
                                 choices=RELATION_DIRECTIONS,
                                 default=RELATION_BIDIRECTIONAL,
                                 help_text=_('Defines the direction of relation on which selection is carried out'))
    subjects = deferred.ManyToManyField('BaseEntity', related_name='+', verbose_name=_('Subjects'), blank=True)

    class Meta:
        """
        RUS: Метаданные класса.
        """
        abstract = True
        verbose_name = _("Data mart relation")
        verbose_name_plural = _("Data mart relations")
        unique_together = (('data_mart', 'term'),)

    def __str__(self):
        """
        RUS: Строковое представление данных.
        """
        relation_directions = dict(self.RELATION_DIRECTIONS)
        return "{} `{}{}` ← {}: {}".format(
            self.data_mart.name,
            self.term_id,
            self.direction,
            relation_directions[self.direction],
            self.term.name
        )


DataMartRelationModel = deferred.MaterializedModel(BaseDataMartRelation)



