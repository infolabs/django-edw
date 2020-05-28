# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.utils import timezone


def years_ago(years, from_date=None):
    """
    Return datetime that was n years from some date (defaulting to right now)
    :param years:
    :param from_date: default `now`
    :return:
    """
    if from_date is None:
        from_date = datetime.now()
    return from_date - relativedelta(years=years)


def num_years(begin, end=None):
    """
    Return how many years it's been since some date
    :param begin:
    :param end: default `now`
    :return:
    """
    if end is None:
        end = datetime.now().date()
    years = int((end - begin).days / 365.2425)
    return years - 1 if begin > years_ago(years, end) else years


def num_days(begin, end=None):
    """
    Return how many days it's been since some date
    :param begin:
    :param end: default `now`
    :return:
    """
    if end is None:
        end = datetime.now().date()
    days = int((end - begin).days)
    return days


# get local timezone
local_tz = timezone.get_current_timezone()


def datetime_to_local(dt):
    """
    Return datetime in current timezone
    :param dt: datetime
    :return:
    """
    return dt.replace(tzinfo=timezone.utc).astimezone(local_tz)
