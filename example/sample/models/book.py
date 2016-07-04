# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFieldsModel
from parler.fields import TranslatedField
from parler.managers import TranslatableManager, TranslatableQuerySet
from polymorphic.query import PolymorphicQuerySet
from edw.models.entity import BaseEntity, BaseEntityManager


class BookQuerySet(TranslatableQuerySet, PolymorphicQuerySet):
    pass


class BookManager(BaseEntityManager, TranslatableManager):
    queryset_class = BookQuerySet


@python_2_unicode_compatible
class Book(BaseEntity, TranslatableModel):
    name = models.CharField(max_length=255, verbose_name=_("Book Name"))
    slug = models.SlugField(verbose_name=_("Slug"), unique=True)
    description = TranslatedField()

    # controlling the catalog
    order = models.PositiveIntegerField(verbose_name=_("Sort by"), db_index=True, default=1)

    class Meta:
        ordering = ('order',)

    objects = BookManager()

    # filter expression used to lookup for a book item using the Select2 widget
    lookup_fields = ('name__icontains',)

    @property
    def entity_name(self):
        return self.name

    def __str__(self):
        return self.name


class BookTranslation(TranslatedFieldsModel):
    master = models.ForeignKey(Book, related_name='translations', null=True)
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True,
                            help_text=_("Description for the list view of books."))


    class Meta:
        unique_together = [('language_code', 'master')]


class ChildBook(Book):
    AGES = (
        (1, "0-6 month"),
        (2, "6-12 month"),
        (3, "1+ year"),
    )

    age = models.PositiveSmallIntegerField(_("Age"), choices=AGES)

    class Meta:
        verbose_name = _("Child book")
        verbose_name_plural = _("Child books")


class AdultBook(Book):
    GENRES = (
        (1, "Fantastic"),
        (2, "Drama"),
        (3, "Mistics"),
    )

    genre = models.PositiveSmallIntegerField(_("Genre"), choices=GENRES)

    class Meta:
        verbose_name = _("Adult book")
        verbose_name_plural = _("Adult books")