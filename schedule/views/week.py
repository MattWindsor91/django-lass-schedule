"""Views and constituent functions providing weekly schedule
services.

"""

from datetime import datetime, timedelta
from schedule.utils.range import ScheduleRange
from schedule.views.common import ury_start_on_date, get_week_start
from schedule.views.week_table import WeekTable
from django.utils import timezone
from django.shortcuts import render
from schedule.models import Term
from django.views.decorators.cache import cache_page


## SUPPORTING FUNCTIONS
##
## Please DON'T export these through __init__.py
## Only export the actual views that are reachable through URLconf
## Thanks!

@cache_page(60 * 60)  # Cache hourly
def schedule_week_from_date(request, week_start):
    """
    The week-at-a-glance schedule view, with the week specified
    by a date object denoting its starting day.

    """
    this_year, this_week, this_day = week_start.isocalendar()

    next_start = week_start + timedelta(weeks=1)
    next_year, next_week, next_day = next_start.isocalendar()

    prev_start = week_start - timedelta(weeks=1)
    prev_year, prev_week, prev_day = prev_start.isocalendar()

    # Check for query string information
    show_private = (
        request.GET.get('show_private', 'false').lower() == 'true'
    )
    iframe = (
        request.GET.get('iframe', 'false').lower() == 'true'
    )

    term = Term.of(week_start)
    schedule = None if not term else WeekTable.tabulate(
        ScheduleRange.week(
            timezone.localtime(week_start),
            split_days=True,
            exclude_before_start=False,
            exclude_after_end=False,
            exclude_subsuming=False,
            with_filler_timeslots=True,
            exclude_non_public=(not show_private)
        )
    )

    return render(
        request,
        (
            'schedule/schedule-week.html'
            if not iframe
            else 'schedule/schedule-week-iframe.html'
        ),
        {
            'week_start': week_start,
            'this_year': this_year,
            'this_week': this_week,
            'next_start': next_start,
            'next_year': next_year,
            'next_week': next_week,
            'prev_start': prev_start,
            'prev_year': prev_year,
            'prev_week': prev_week,
            'term': term,
            'schedule': schedule
        }
    )


def to_monday(date):
    """Given a date, find the date of the Monday of its week."""
    days_after_monday = date.weekday()
    return date - timedelta(days=days_after_monday)


## VIEWS
## Only actual views as referenced by URLconf should go here.
## Remember to add them to __init__.py!

def index(request):
    """The view that gets brought up if you navigate to 'schedule'.

    Currently this just gets the weekly schedule for the current
    week.
    """
    return schedule_week_from_date(
        request,
        ury_start_on_date(to_monday(datetime.utcnow())))


def schedule_week(request, year, week):
    """The week-at-a-glance schedule view.

    """
    # WEEK STARTS
    return schedule_week_from_date(
        request,
        get_week_start(int(year), int(week)),
    )
