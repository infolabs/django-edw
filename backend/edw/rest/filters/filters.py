from datetime import timedelta

from django_filters.filters import DateRangeFilter, _truncate
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


class BeforeDateRangeFilter(DateRangeFilter):
    """
    Filter based on date range calculated before set interval.
    """
    choices = [
        ('present_day', _('Present day')), # Example: created_at__before_date_range=last_week
        ('until_yesterday', _('Until yesterday')),
        ('last_week', _('Last week')),
        ('last_month', _('Last month')),
        ('last_half_year', _('Last half of the year')),
        ('last_year', _('Last year')),

    ]

    filters = {
        'present_day': lambda qs, name: qs.filter(**{
            '%s__lt' % name: _truncate(now() - timedelta(days=1)),
        }),
        'until_yesterday': lambda qs, name: qs.filter(**{
            '%s__lt' % name: _truncate(now() - timedelta(days=2)),
        }),
        'last_week': lambda qs, name: qs.filter(**{
            '%s__lt' % name: _truncate(now() - timedelta(days=7)),
        }),
        # Вычитаем один месяц (используя timedelta для дней, примерно 30 дней)
        # Если нужно точно учитывать разное количество дней в месяцах, можно использовать:
        # bash: pip install python - dateutil
        # from dateutil.relativedelta import relativedelta
        # one_month_ago_exact = current_date - relativedelta(months=1)
        'last_month': lambda qs, name: qs.filter(**{
            '%s__lt' % name: _truncate(now() - timedelta(days=30)),
        }),
        'last_half_year': lambda qs, name: qs.filter(**{
            '%s__lt' % name: _truncate(now() - timedelta(days=182)),
        }),
        'last_year': lambda qs, name: qs.filter(**{
            '%s__lt' % name: _truncate(now() - timedelta(days=365)),
        }),
    }
