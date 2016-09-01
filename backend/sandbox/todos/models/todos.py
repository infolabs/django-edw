# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from edw.models.entity import BaseEntity, BaseEntityManager, BaseEntityQuerySet


class TodoQuerySet(BaseEntityQuerySet):
    pass


class TodoManager(BaseEntityManager):
    queryset_class = TodoQuerySet


@python_2_unicode_compatible
class Todo(BaseEntity):
    PRIORITIES = (
        (1, _("Low")),
        (2, _("Middle")),
        (3, _("High")),
    )
    DIRECTIONS = (
        (1, _("Health")),
        (2, _("Family")),
        (3, _("Finance")),
        (4, _("Hobby")),
    )

    name = models.CharField(max_length=255, verbose_name=_("Todo Name"))
    slug = models.SlugField(verbose_name=_("Slug"), unique=True)
    marked = models.BooleanField(verbose_name=_('Marked'), default=False)
    priority = models.PositiveSmallIntegerField(_("Priority"), choices=PRIORITIES, blank=True, null=True)
    direction = models.PositiveSmallIntegerField(_("Direction"), choices=DIRECTIONS, blank=True, null=True)
    description = models.TextField(verbose_name=_('Description'), blank=True, null=True)

    # controlling the catalog
    order = models.PositiveIntegerField(verbose_name=_("Sort by"), db_index=True, default=1)

    class Meta:
        ordering = ('order',)
        verbose_name = _("Todo")
        verbose_name_plural = _("Todos")

    objects = TodoManager()

    # filter expression used to lookup for a Todo item using the Select2 widget
    lookup_fields = ('name__icontains',)

    @property
    def entity_name(self):
        return self.name

    def __str__(self):
        return self.name