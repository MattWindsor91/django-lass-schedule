"""Views and constituent functions providing daily schedule
services.

"""

from datetime import date, timedelta
from schedule.utils.range import ScheduleRange
from schedule.views.common import ury_start_on_date, get_week_day
from django.shortcuts import render
from django.utils import timezone
from schedule.models import Term
from django.views.decorators.cache import cache_page


## SUPPORTING FUNCTIONS
##
## Please DON'T export these through __init__.py
## Only export the actual views that are reachable through URLconf
## Thanks!

@cache_page(60 * 60)  # Cache hourly
def schedule_day_from_date(request, day_start):
    """The day-at-a-glance schedule view, with the day specfied by
    a date object (including the start time of the schedule).

    """
    this_year, this_week, this_day = day_start.isocalendar()

    next_start = day_start + timedelta(days=1)
    next_year, next_week, next_day = next_start.isocalendar()

    prev_start = day_start - timedelta(days=1)
    prev_year, prev_week, prev_day = prev_start.isocalendar()

    term = Term.of(day_start)
    schedule = None if not term else ScheduleRange.day(
        day_start,
        exclude_before_start=False,
        exclude_after_end=False,
        exclude_subsuming=False,
        with_filler_timeslots=True).data

    return render(
        request,
        'schedule/schedule-day.html',
        {'day_start': day_start,
            'this_year': this_year,
            'this_week': this_week,
            'next_start': next_start,
            'next_year': next_year,
            'next_week': next_week,
            'next_day': next_day,
            'prev_start': prev_start,
            'prev_year': prev_year,
            'prev_week': prev_week,
            'prev_day': prev_day,
            'term': term,
            'schedule': schedule})


## VIEWS
## Only actual views as referenced by URLconf should go here.
## Remember to add them to __init__.py!

def schedule_weekday(request, year, week, weekday):
    """The day-in-detail schedule view, with the day provided in
    Year/Week/Day format.

    """
    return schedule_day_from_date(
        request,
        get_week_day(int(year), int(week), int(weekday)))


def schedule_day(request, year, month, day):
    """The day-in-detail schedule view, with the day provided in
    Year/Month/Day format.

    """
    return schedule_day_from_date(
        request,
        ury_start_on_date(date(
            year=int(year),
            month=int(month),
            day=int(day))))


def today(request):
    """A view that shows the day schedule for today."""
    return schedule_day_from_date(
        request,
        ury_start_on_date(timezone.now()))
