"""Views and constituent functions providing daily schedule
services.

"""

from datetime import date, timedelta
from schedule.utils.range import ScheduleRange
from schedule.views.common import ury_start_on_date, get_week_day
from django.shortcuts import render
from django.utils import timezone
from schedule.models import Term


## SUPPORTING FUNCTIONS
##
## Please DON'T export these through __init__.py
## Only export the actual views that are reachable through URLconf
## Thanks!

def schedule_day_from_date(request, day_start):
    """The day-at-a-glance schedule view, with the day specfied by
    a date object (including the start time of the schedule).

    """
    ctx = common.nav_context(day_start, timedelta(days=1))

    term = Term.of(day_start)

    schedule_fail = None
    schedule = None
    if term is None:
        schedule_fail = (
            'holiday'
            if Term.before(day_start)
            else 'noterm'
        )
    available, why_not, term = schedule_available_for(
        day_start,
        timedelta(days=1)
    )
    if available:
        context['schedule'] = ScheduleRange.day(
            day_start,
            exclude_before_start=False,
            exclude_after_end=False,
            exclude_subsuming=False,
            with_filler_timeslots=True
        ).data
    else:
        context['schedule_failure'] = why_not

    return render(
        request,
        'schedule/schedule-day.html',
        context
    )



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
