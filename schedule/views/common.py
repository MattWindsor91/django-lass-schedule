"""
Common functions for schedule views.

"""

from datetime import time, datetime, date
from schedule.models import Timeslot, Term

from django import shortcuts
from django.utils import timezone

from schedule.views.contrib import iso_to_gregorian

# Changing this will change the starting time of the schedule
# views.
# NOTE: This time is taken to be in local time, NOT UTC!
URY_START = time(
    hour=7,
    minute=0,
    second=0
)


def date_normalise(view):
    """
    Given a view function, returns another function that converts a
    range of possible date formats coming in over keyword arguments
    into a :class:`datetime` and passes it to the original view
    function.

    If no arguments whatsoever besides the request are given, the
    (station start of the) current day is used.

    """
    def new_view(request,
                 start=None,
                 year=None,
                 week=None,
                 weekday=None,
                 month=None,
                 day=None,
                 full_week=None):
        if start:
            # Strip any time information
            start = start.date()
        else:
            if year and month and day:
                start = date(int(year), int(month), int(day))
            elif year and week and weekday:
                start = get_week_day(
                    int(year),
                    int(week),
                    int(weekday)
                )
            elif year and week:
                start = get_week_start(int(year), int(week))
            elif not any([start, year, week, weekday, month, day]):
                start = date.today()
            else:
                raise ValueError(
                    "Incorrect combination of arguments to view."
                )
            return view(request, ury_start_on_date(start))
    return new_view


def ury_start_on_date(date):
    """Returns a new datetime representing the nominal start of URY
    programming on the given date (timezone-aware).

    """
    return timezone.make_aware(
        datetime.combine(date, URY_START),
        timezone.get_current_timezone()
    )


def nav_context(start, step):
    """
    Creates a template context with this/prev/next variables set up
    to allow navigating through 'step'-sized chunks of the schedule
    starting at 'start'.

    """
    ctx = {}
    ctx.update(nav_context_entry('prev', start - step))
    ctx.update(nav_context_entry('this', start))
    ctx.update(nav_context_entry('next', start + step))
    return ctx


def nav_context_entry(prefix, date):
    """
    Creates an entry for the schedule navigation context allowing
    a hop to the given date, with the variables entered into the
    context being *prefix*_year, *prefix*_week and *prefix*_date.

    """
    return dict(
        zip(
            ['_'.join((prefix, x)) for x in 'year', 'week', 'day'],
            date.isocalendar()
        )
    )


def schedule_view(request, schedule):
    """Renders a view of the given schedule.

    This function passes the schedule file to the 
    template:

    inner_view - the name of the view to call to render the schedule
                 proper

    It also takes the following GET parameters:

    show_private - if 'true', then private shows are included on the
                   schedule; otherwise they are hidden
    iframe - if 'true', the base template will be changed to one that
             allows the schedule to stand alone as an iframe;
             otherwise a full page will be rendered

    :param request: the HTTPRequest to respond to with this view
    :type request: HTTPRequest
    :param start: the start of the schedule to render
    :type start: datetime
    :param step: the period the schedule covers
    :type step: timedelta
    :rtype: HttpResponse

    """
    # Check for query string information
    show_private = (
        request.GET.get('show_private', 'false').lower() == 'true'
    )
    iframe = (
        request.GET.get('iframe', 'false').lower() == 'true'
    )
    to = Timeslot.objects

    ctx = nav_context(start, step)
    ctx['inner_view'] = inner_view
    ctx['timeslots'] = (to.all() if show_private else to.public())

    return shortcuts.render(
        request,
        'schedule/schedule-frame-{}.html'.format(
            'iframe' if iframe else 'full'
        ),
        ctx
    )


def schedule_view_raw(request, name, start, step, timeslots, builder):
    """
    Renders a "raw" view of the schedule, without navigation context.

    Usually you don't want this function, but rather one of the
    wrappers to it (:func:`schedule.views.schedule_week` or
    :func:`schedule.views.schedule_day` for instance), and in most
    cases you'll want to pass through :func:`schedule_view` first.

    This function passes a number of context variables to the
    template:

    schedule - the actual schedule data if a schedule is available,
               or None if the schedule is unavailable
    reason - the reason, if any, for the schedule being unavailable

    :param request: the HTTPRequest to respond to with this view
    :type request: HTTPRequest
    :param name: the name of the schedule view type, used to
                 calculate the template etc.
    :type name: basestring
    :param start: the start of the schedule to render
    :type start: datetime
    :param step: the period the schedule covers
    :type step: timedelta
    :param timeslots: the allowed set of timeslots this schedule can
                      display, preferably as an unevaluated queryset
    :type timeslots: QuerySet
    :param builder: the function that, given start, step and a
                    QuerySet giving the range of Timeslots that can
                    be shown in the schedule, will create the schedule
                    data in a format the target template can understand
    :type builder: func

    """
    ctx = {}
    can_schedule, why_not = schedule_available_for(
        start,
        step
    )
    if can_schedule:
        ctx['schedule'] = builder(start, step, timeslots)
    else:
        ctx['schedule'] = None
        ctx['reason'] = why_not

    return shortcuts.render(
        request,
        'schedule/schedule-raw-{}.html'.format(name),
        ctx
    )


def schedule_available_for(start, step):
    """
    Determines whether we can display a schedule slice starting on
    `start` and lasting for `step`.

    Returns a 2-tuple containing a boolean stating whether or not a
    schedule can be shown, and a string encoding the reason why not if
    the previous entry is False (None otherwise).

    """
    why_not = None

    if Term.of(start) is None:
        why_not = 'holiday' if Term.before(start) else 'notermdata'

    return why_not is None, why_not
