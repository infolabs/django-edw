from datetime import timedelta

from django_filters.filters import DateRangeFilter
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


def _truncate(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


class BeforeDateRangeFilter(DateRangeFilter):
    """
    Filter based on date range calculated before set interval.
    """
    choices = [
        # Example: created_at__before_date_range=last_week
        ('last_quarter_of_hour', _('Last quarter of an hour')),  # Объекты старше 15 минут
        ('last_half_hour', _('Last half hour')),  # Объекты старше 30 минут
        ('last_hour', _('Last hour')),  # Объекты старше 1 часа
        ('present_day', _('Present day')), # Объекты, существующие более 1 дня (архивируются на 2-й день)
        ('until_yesterday', _('Until yesterday')), # Объекты старше 2 дней
        ('last_week', _('Last week')), # Объекты старше недели
        ('last_month', _('Last month')), # Объекты старше месяца (приблизительный расчет)
        ('last_half_year', _('Last half of the year')), # Объекты старше полугода
        ('last_year', _('Last year')), # Объекты старше года
    ]

    filters = {
        'last_quarter_of_hour': lambda qs, name: qs.filter(**{
            '%s__lt' % name: now() - timedelta(minutes=15),
        }),
        'last_half_hour': lambda qs, name: qs.filter(**{
            '%s__lt' % name: now() - timedelta(minutes=30),
        }),
        'last_hour': lambda qs, name: qs.filter(**{
            '%s__lt' % name: now() - timedelta(hours=1),
        }),
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
