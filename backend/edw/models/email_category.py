# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.six import with_metaclass
from django.utils.translation import ugettext_lazy as _

from .term import TermModel
from .. import deferred


#==============================================================================
# BaseEmailCategoryQuerySet
#==============================================================================
class BaseEmailCategoryQuerySet(models.QuerySet):
    """
    RUS: Запрос к базе почтовых категорий.
    """
    def active(self):
        """
        RUS: Возвращает все активные элементы.
        """
        return self.filter(active=True)


class BaseEmailCategoryManager(models.Manager):
    """
    RUS: Менеджер почтовых категорий.
    """

    def get_queryset(self):
        """
        RUS: Возвращает запрос к базе почтовых категорий.
        """
        return BaseEmailCategoryQuerySet(self.model, using=self._db)

    def active(self):
        """
        RUS: Возвращает запрос к базе почтовых категорий с активными элементами.
        """
        return self.get_queryset().active()


# =========================================================================================================
#  BaseEmailCategory
# =========================================================================================================
@python_2_unicode_compatible
class BaseEmailCategory(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    '''
    Related to Term email category
    RUS: Класс базовая почтовая категория, связанная с термином.
    Определяет поля (Термин, Маска почтового адреса, статус Активен).
    '''
    term = models.ForeignKey(TermModel, verbose_name=_('Term'), related_name='+', db_index=True)
    email_masks = models.TextField(verbose_name=_('Email Address Masks'), null=True, blank=True, help_text=_(
        """You enter on one mask in line. Use '?' and '*' as universal substitutes. """
        """'?' replaces any symbol, '*' replaces any sequence of symbols (including I am empty). """
        """Gaps are ignored. """
        """Example: *@mail.ru, admin@*.??, *.edu.ru, smith????@yahoo.com."""))

    active = models.BooleanField(verbose_name=_('Active'), default=True, db_index=True)

    objects = BaseEmailCategoryManager()

    class Meta:
        """
        RUS: Переопределяет метаданные модели.
        """
        abstract = True
        verbose_name = _("Email category")
        verbose_name_plural = _("Email categories")
        unique_together = (('term', 'active'),)
        ordering = ('term__{}'.format(TermModel._mptt_meta.tree_id_attr), 'term__{}'.format(TermModel._mptt_meta.left_attr))

    def __str__(self):
        """
        RUS: Переопределяет имя в строковом формате.
        """
        return self.name

    @property
    def name(self):
        if self.term.parent_id is not None:
            return "{} - {}".format(self.term.parent.name, self.term.name)
        else:
            return "{}".format(self.term.name)
    name.fget.short_description = _('Name')

    @cached_property
    def email_pattern(self):
        raw_patterns = re.split(r'\s+', self.email_masks.strip())
        patterns = [re.sub(r'\*', '.*?', re.sub(r'\?', '.', x)) for x in raw_patterns]
        return r'^(?:%s)$' % '|'.join(patterns)

    def is_email_pattern_match(self, code):
        return re.match(self.email_pattern, code) is not None


EmailCategoryModel = deferred.MaterializedModel(BaseEmailCategory)


def get_email_category(email):
    tree_opts = TermModel._mptt_meta
    categories = EmailCategoryModel.objects.active().order_by(
        '-' + 'term__{}'.format(tree_opts.level_attr),
        'term__{}'.format(tree_opts.tree_id_attr), 'term__{}'.format(tree_opts.left_attr))
    for category in categories:
        if category.is_email_pattern_match(email):
            break
    else:
        category = None
    return category


def get_all_email_category_terms_ids():
    return EmailCategoryModel.objects.all().values_list('term_id', flat=True)
