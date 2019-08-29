# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import calendar

from django.db import transaction
from django.utils.timezone import make_aware, is_naive
from django.utils.translation import ugettext_lazy as _

from edw.models.entity import EntityModel
from edw.models.term import TermModel

_default_system_flags_restriction = (TermModel.system_flags.delete_restriction |
                                     TermModel.system_flags.change_parent_restriction |
                                     TermModel.system_flags.change_slug_restriction |
                                     TermModel.system_flags.change_semantic_rule_restriction |
                                     TermModel.system_flags.has_child_restriction |
                                     TermModel.system_flags.external_tagging_restriction)


class BaseAddedDateTermsValidationMixin(object):
    """
    RUS: Миксин управления терминами даты.
    """

    REQUIRED_FIELDS = ('created_at',)

    def need_terms_validation_after_save(self, origin, **kwargs):
        """
        RUS: Проставляет метки в термин Дата после сохранеия объекта.
        """
        if origin is None or (
                make_aware(origin.created_at) if is_naive(origin.created_at) else origin.created_at) != (
                make_aware(self.created_at) if is_naive(self.created_at) else self.created_at):
            do_validate = kwargs["context"]["validate_added_date"] = True
        else:
            do_validate = False
        return super(BaseAddedDateTermsValidationMixin, self).need_terms_validation_after_save(
            origin, **kwargs) or do_validate


class AddedDayTermsValidationMixin(BaseAddedDateTermsValidationMixin):

    ADDED_DAY_ROOT_TERM_SLUG = "added-day"
    ADDED_DAY_KEY = 'added-day-{:02d}'
    ADDED_DAY_RANGE_KEY = 'added-day-{0:02d}-{1:02d}'

    @classmethod
    def validate_term_model(cls):
        """
        RUS: Добавляет день в модель терминов. Проверяет, есть ли день в модели TermModel,
        и при его отсутствии создает диапазон дат и разбивку по дням в этих диапазонах.
        """
        system_flags = _default_system_flags_restriction
        with transaction.atomic():
            try: # added day
                added_day = TermModel.objects.get(slug=cls.ADDED_DAY_ROOT_TERM_SLUG, parent=None)
            except TermModel.DoesNotExist:
                added_day = TermModel(
                    slug=cls.ADDED_DAY_ROOT_TERM_SLUG,
                    parent=None,
                    name=_('Added day'),
                    semantic_rule=TermModel.OR_RULE,
                    system_flags=system_flags
                )
                added_day.save()
        day_ranges = ((1, 11), (11, 21), (21, 32))
        for r in day_ranges: # added day range
            day_range_key = cls.ADDED_DAY_RANGE_KEY.format(r[0], r[1] - 1)
            with transaction.atomic():
                try:
                    added_day_range = TermModel.objects.get(slug=day_range_key, parent=added_day)
                except TermModel.DoesNotExist:
                    added_day_range = TermModel(
                        slug=day_range_key,
                        parent_id=added_day.id,
                        name="{} - {}".format(r[0], r[1] - 1),
                        semantic_rule=TermModel.OR_RULE,
                        system_flags=system_flags
                    )
                added_day_range.save()
            for i in range(r[0], r[1]): # added day
                day_key = cls.ADDED_DAY_KEY.format(i)
                with transaction.atomic():
                    try:
                        TermModel.objects.get(slug=day_key)
                    except TermModel.DoesNotExist:
                        day = TermModel(
                            slug=day_key,
                            parent_id=added_day_range.id,
                            name="{:02d}".format(i),
                            semantic_rule=TermModel.OR_RULE,
                            system_flags=system_flags
                        )
                        day.save()
        super(AddedDayTermsValidationMixin, cls).validate_term_model()

    def validate_terms(self, origin, **kwargs):
        """
        RUS: Проставляет по данным объектам соответствующий термин День создания.
        """
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_added_date", False):
            added_days = self.get_added_days()
            if origin is not None:
                term = added_days[self.ADDED_DAY_KEY.format(origin.created_at.day)]
                self.terms.remove(term)
            term = added_days[self.ADDED_DAY_KEY.format(self.created_at.day)]
            self.terms.add(term)
        super(AddedDayTermsValidationMixin, self).validate_terms(origin, **kwargs)

    @staticmethod
    def get_added_days():
        """
        RUS: Возвращает дни. Если дни отсутствуют в TermModel, то возвращает дни из EntityModel.
        """
        added_days = getattr(EntityModel, "_added_days_cache", None)
        if added_days is None:
            added_days = {}
            try:
                root = TermModel.objects.get(slug=AddedDayTermsValidationMixin.ADDED_DAY_ROOT_TERM_SLUG, parent=None)
                for term in root.get_descendants(include_self=True):
                    added_days[term.slug] = term
            except TermModel.DoesNotExist:
                pass
            EntityModel._added_days_cache = added_days
        return added_days


class AddedMonthTermsValidationMixin(BaseAddedDateTermsValidationMixin):

    ADDED_MONTH_ROOT_TERM_SLUG = "added-month"
    ADDED_MONTH_KEY = 'added-month-{:02d}'

    @classmethod
    def validate_term_model(cls):
        """
        RUS: Добавляет месяц в модель терминов TermModel. Проверяет, есть ли месяц в модели TermModel,
        и при его отсутствии создает диапазон месяцев (1-12) и разбивку по месяцам в этих диапазонах.
        """
        system_flags = _default_system_flags_restriction
        with transaction.atomic():
            try: # added month
                added_month = TermModel.objects.get(slug=cls.ADDED_MONTH_ROOT_TERM_SLUG, parent=None)
            except TermModel.DoesNotExist:
                added_month = TermModel(
                    slug=cls.ADDED_MONTH_ROOT_TERM_SLUG,
                    parent=None,
                    name=_('Added month'),
                    semantic_rule=TermModel.OR_RULE,
                    system_flags=system_flags)
                added_month.save()
        for i in range(1, 13):
            month_key = cls.ADDED_MONTH_KEY.format(i)
            with transaction.atomic():
                try:
                    TermModel.objects.get(slug=month_key, parent=added_month)
                except TermModel.DoesNotExist:
                    month = TermModel(slug=month_key,
                                      parent_id=added_month.id,
                                      name=_(calendar.month_name[i]),
                                      semantic_rule=TermModel.OR_RULE,
                                      system_flags=system_flags)
                    month.save()
        super(AddedMonthTermsValidationMixin, cls).validate_term_model()

    def validate_terms(self, origin, **kwargs):
        """
        RUS: Проставляет по данным объектам соответствующий термин Месяц создания.
        """
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_added_date", False):
            added_months = self.get_added_months()
            if origin is not None:
                term = added_months[self.ADDED_MONTH_KEY.format(origin.created_at.month)]
                self.terms.remove(term)
            term = added_months[self.ADDED_MONTH_KEY.format(self.created_at.month)]
            self.terms.add(term)
        super(AddedMonthTermsValidationMixin, self).validate_terms(origin, **kwargs)

    @staticmethod
    def get_added_months():
        """
        RUS: добавляет месяцы в модель EntityModel, если они отсутствуют.
        """
        added_months = getattr(EntityModel, "_added_months_cache", None)
        if added_months is None:
            added_months = {}
            try:
                root = TermModel.objects.get(slug=AddedMonthTermsValidationMixin.ADDED_MONTH_ROOT_TERM_SLUG, parent=None)
                for term in root.get_descendants(include_self=True):
                    added_months[term.slug] = term
            except TermModel.DoesNotExist:
                pass
            else:
                EntityModel._added_months_cache = added_months
        return added_months


class AddedYearTermsValidationMixin(BaseAddedDateTermsValidationMixin):

    ADDED_YEAR_ROOT_TERM_SLUG = "added-year"
    ADDED_YEAR_KEY = 'added-year-{}'

    @classmethod
    def validate_term_model(cls):
        """
        RUS: Добавляет год в модель терминов TermModel.
        """
        system_flags = _default_system_flags_restriction
        with transaction.atomic():
            try: # added year
                TermModel.objects.get(slug=cls.ADDED_YEAR_ROOT_TERM_SLUG)
            except TermModel.DoesNotExist:
                added_year = TermModel(
                    slug=cls.ADDED_YEAR_ROOT_TERM_SLUG,
                    parent=None,
                    name=_('Added year'),
                    semantic_rule=TermModel.XOR_RULE,
                    system_flags=system_flags)
                added_year.save()
        super(AddedYearTermsValidationMixin, cls).validate_term_model()

    def validate_terms(self, origin, **kwargs):
        """
        RUS: Проставляет по данным объектам соответствующий термин Год создания.
        """
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_added_date", False):
            added_year = self.created_at.year
            added_years = self.get_added_years(added_year)
            if origin is not None:
                term = added_years.get(self.ADDED_YEAR_KEY.format(origin.created_at.year), None)
                if term is not None:
                    self.terms.remove(term)
            term = added_years[self.ADDED_YEAR_KEY.format(added_year)]
            self.terms.add(term)
        super(AddedYearTermsValidationMixin, self).validate_terms(origin, **kwargs)

    @staticmethod
    def get_added_years(year):
        """
        RUS: Возвращает термин Год, если его нет в TermModel, то из списка наследников.
        Если синонима нет в годах, снимаем ограничения из системных флагов
         и если не находим в модели TermModel, то создаем его.
        """
        year_key = EntityModel.ADDED_YEAR_KEY.format(year)
        added_years = getattr(EntityModel, "_added_years_cache", {})
        if year_key not in added_years:
            try:
                root = TermModel.objects.get(slug=AddedYearTermsValidationMixin.ADDED_YEAR_ROOT_TERM_SLUG, parent=None)
            except TermModel.DoesNotExist:
                pass
            else:
                if not added_years:
                    for term in root.get_descendants(include_self=False):
                        added_years[term.slug] = term
                    EntityModel._added_years_cache = added_years
                if year_key not in added_years:
                    system_flags = _default_system_flags_restriction
                    (term, is_create) = TermModel.objects.get_or_create(
                        slug=year_key,
                        parent_id=root.id,
                        defaults={
                            'name': "{}".format(year),
                            'semantic_rule': TermModel.OR_RULE,
                            'system_flags': system_flags
                        }
                    )
                    added_years[year_key] = term
        return added_years


class AddedDateTermsValidationMixin(AddedYearTermsValidationMixin, AddedMonthTermsValidationMixin,
                                    AddedDayTermsValidationMixin):
    pass
