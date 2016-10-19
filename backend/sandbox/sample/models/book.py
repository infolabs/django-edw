# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from edw.models.entity import BaseEntity, BaseEntityManager, BaseEntityQuerySet, ApiReferenceMixin
from edw.models.mixins.entity.add_date_terms_validation import AddedDateTermsValidationMixin
#from edw.models.mixins.entity.fsm import FSMMixin
from edw.models.defaults.mapping import EntityImage


class BookQuerySet(BaseEntityQuerySet):
    pass


class BookManager(BaseEntityManager):
    queryset_class = BookQuerySet


@python_2_unicode_compatible
class Book(AddedDateTermsValidationMixin, ApiReferenceMixin, BaseEntity):

    name = models.CharField(max_length=255, verbose_name=_("Book Name"))
    #slug = models.SlugField(verbose_name=_("Slug"), unique=True)
    description = models.TextField(verbose_name=_('Description'), blank=True, null=True)

    # controlling the catalog
    order = models.PositiveIntegerField(verbose_name=_("Sort by"), db_index=True, default=1)

    # images
    images = models.ManyToManyField('filer.Image', through=EntityImage)

    class Meta:
        ordering = ('order',)
        verbose_name = _("Book")
        verbose_name_plural = _("Books")

    class RESTMeta:
          exclude = ['images']

    objects = BookManager()

    # filter expression used to lookup for a book item using the Select2 widget
    lookup_fields = ('name__icontains',)

    @property
    def entity_name(self):
        return self.name

    def __str__(self):
        return self.name

    @property
    def sample_image(self):
        return self.images.first()



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

    class RESTMeta:
        exclude = ['age', 'images']
        include = {
            'my_age': serializers.SerializerMethodField(),
        }

        def get_my_age(serializer, entity):
            ages = dict(ChildBook.AGES)
            return ages[entity.age]


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

    class RESTMeta:
        exclude = ['genre', 'images']