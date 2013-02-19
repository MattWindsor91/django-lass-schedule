"""
Common functions for schedule views.

"""

import datetime

from django import shortcuts
from django.utils import timezone

from ..models import Timeslot
from ..utils import object

# Changing this will change the starting time of the schedule
# views.
# NOTE: This time is taken to be in local time, NOT UTC!
URY_START = datetime.time(
    hour=7,
    minute=0,
    second=0
)


# Jump table of schedule types to constructors.
SCHED_CONSTRUCTORS = {
    'week': object.WeekSchedule,
    'day': object.DaySchedule,
}


def ury_start_on_date(date):
    """Returns a new datetime representing the nominal start of URY
    programming on the given date (timezone-aware).

    """
    return timezone.make_aware(
        datetime.datetime.combine(date, URY_START),
        timezone.get_current_timezone()
    )


def schedule_view(request, type, start):
    """Renders a view of the given schedule.

    This function passes the schedule file to the template:

    inner_view - the name of the view to call to render the schedule
                 proper

    It also takes the following GET parameters:

    show_private - if 'true', then private shows are included on the
                   schedule; otherwise they are hidden
    iframe - if 'true', the base template will be changed to one that
             allows the schedule to stand alone as an iframe;
             otherwise a full page will be rendered

    Args:
        request: the HTTPRequest to respond to with this view.
        type: a string that identifies the type of schedule to the template
            and/or schedule builder.  Acceptable values at the moment include
            'week' and 'day'.
        start: the start date or datetime, which may be modified to fit the
            schedule type.

    Returns:
        None
    """
    start = ury_start_on_date(start)

    # Check for query string information
    show_private = (
        request.GET.get('show_private', 'false').lower() == 'true'
    )
    iframe = (
        request.GET.get('iframe', 'false').lower() == 'true'
    )

    to = Timeslot.objects
    timeslots = (to.all() if show_private else to.public())

    ctx = {}

    sched = SCHED_CONSTRUCTORS[type.lower()]
    ctx['schedule'] = sched(
        start,
        lambda s: object.range_builder(s, timeslots)
    )

    return shortcuts.render(
        request,
        'schedule/schedule-{}.html'.format(
            'iframe' if iframe else 'base'
        ),
        ctx
    )
