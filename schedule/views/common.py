from datetime import date, time, datetime, timedelta
from schedule.models import Timeslot
from django.utils import timezone

from schedule.views.contrib import iso_to_gregorian

# Changing this will change the starting time of the schedule
# views.
# NOTE: This time is taken to be in local time, NOT UTC!
URY_START = time(
    hour=7,
    minute=0,
    second=0)


def ury_start_on_date(date):
    """Returns a new datetime representing the nominal start of URY
    programming on the given date (timezone-aware).

    """
    return timezone.make_aware(
        datetime.combine(date, URY_START),
        timezone.get_current_timezone())


def get_week_day(year, week, day):
    """Given a year, a week number inside that year and a day number
    inside that day (from 1 to 7), finds the corresponding time
    period that represents the start of that URY day.

    """
    return ury_start_on_date(iso_to_gregorian(year, week, day))


def get_week_start(year, week):
    """Given a year and a week number inside that year, finds the
    date of the Monday of that week.

    See get_week_day for details on how this function works.

    """
    return get_week_day(year, week, 1)

