# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import calendar

from django.utils.translation import ugettext_lazy as _

from edw.models.term import TermModel


class BaseAddedDateTermsValidationMixin(object):

    def need_terms_validation_after_save(self, origin, **kwargs):
        if origin is None or origin.created_at != self.created_at:
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
        system_flags = (TermModel.system_flags.delete_restriction |
                        TermModel.system_flags.change_parent_restriction |
                        TermModel.system_flags.change_slug_restriction |
                        TermModel.system_flags.change_semantic_rule_restriction |
                        TermModel.system_flags.has_child_restriction |
                        TermModel.system_flags.external_tagging_restriction)
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
            try:
                added_day_range = TermModel.objects.get(slug=day_range_key, parent=added_day)
            except TermModel.DoesNotExist:
                added_day_range = TermModel(
                    slug=day_range_key,
                    parent=added_day,
                    name="{} - {}".format(r[0], r[1] - 1),
                    semantic_rule=TermModel.OR_RULE,
                    system_flags=system_flags
                )
            added_day_range.save()
            for i in range(r[0], r[1]): # added day
                day_key = cls.ADDED_DAY_KEY.format(i)
                try:
                    TermModel.objects.get(slug=day_key)
                except TermModel.DoesNotExist:
                    day = TermModel(
                        slug=day_key,
                        parent=added_day_range,
                        name="{:02d}".format(i),
                        semantic_rule=TermModel.OR_RULE,
                        system_flags=system_flags
                    )
                    day.save()
        super(AddedDayTermsValidationMixin, cls).validate_term_model()


class AddedMonthTermsValidationMixin(BaseAddedDateTermsValidationMixin):

    ADDED_MONTH_ROOT_TERM_SLUG = "added-month"
    ADDED_MONTH_KEY = 'added-month-{:02d}'

    @classmethod
    def validate_term_model(cls):
        system_flags = (TermModel.system_flags.delete_restriction |
                        TermModel.system_flags.change_parent_restriction |
                        TermModel.system_flags.change_slug_restriction |
                        TermModel.system_flags.change_semantic_rule_restriction |
                        TermModel.system_flags.has_child_restriction |
                        TermModel.system_flags.external_tagging_restriction)
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
            try:
                TermModel.objects.get(slug=month_key, parent=added_month)
            except TermModel.DoesNotExist:
                month = TermModel(slug=month_key,
                                  parent=added_month,
                                  name=_(calendar.month_name[i]),
                                  semantic_rule=TermModel.OR_RULE,
                                  system_flags=system_flags)
                month.save()
        super(AddedMonthTermsValidationMixin, cls).validate_term_model()


class AddedYearTermsValidationMixin(BaseAddedDateTermsValidationMixin):

    ADDED_YEAR_ROOT_TERM_SLUG = "added-year"
    ADDED_YEAR_KEY = 'added-year-%s'

    @classmethod
    def validate_term_model(cls):
        system_flags = (TermModel.system_flags.delete_restriction |
                        TermModel.system_flags.change_parent_restriction |
                        TermModel.system_flags.change_slug_restriction |
                        TermModel.system_flags.change_semantic_rule_restriction |
                        TermModel.system_flags.has_child_restriction |
                        TermModel.system_flags.external_tagging_restriction)

        #, _('added year'))

        super(AddedYearTermsValidationMixin, cls).validate_term_model()


class AddedDateTermsValidationMixin(AddedDayTermsValidationMixin, AddedMonthTermsValidationMixin,
                                    AddedYearTermsValidationMixin):
    pass