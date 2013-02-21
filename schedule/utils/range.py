"""
A class representing a contiguous, linear chunk of programming,
and also containing various methods for extracting said chunks from
the schedule.

"""

from django.utils import timezone

from . import filler
from ..models import Timeslot


def between(start, end, limit=None):
    """Returns a filled schedule between start and end containing limit shows.

    This function returns
    A filled list from 'start' to 'end'
    Of slots, inclusive

    Args:
        start: the start datetime of the schedule range.
        end: the end datetime of the schedule range.
        limit: (Optional) if provided, at most 'limit' shows will be returned.

    Returns:
        A list of show timeslots from 'from' to 'to' inclusive, including
        filler shows and any timeslots straddling the boundary dates.
    """
    def trim(lst):
        return lst[:limit] if limit else lst

    return trim(
        filler.fill(
            trim(
                Timeslot.objects.public().select_related().in_range(
                    start,
                    end
                )
            ),
            start,
            end,
        )
    )


def day(today=None, limit=None):
    """Returns the schedule for the given day.

    This function returns
    One whole day of scheduled slots
    Complete with filler

    Args:
        today: a datetime representing the time that the schedule should start.
            If not provided, the current time is assumed.
        limit: (Optional) if provided, at most 'limit' shows will be returned.
    Returns:
        A list of show timeslots within 24 hours of the current date shows and
        any timeslots straddling the boundary dates.
    """
    if not today:
        today = timezone.now()

    tomorrow = dst_add(today, timezone.timedelta(days=1))
    return between(today, tomorrow, limit)


def dst_add(start_date, delta):
    """Adds a timedelta to a local date, taking DST into account.

    The result is as if the delta was interpreted in terms of local time as
    opposed to absolute time.

    In other words, the resulting date is the start data plus the delta and any
    DST offset changes in the meantime, and is thus one hour after or before
    the simple addition of start_date and delta in some cases.

    For example, if the date is the 1st of January 1pm GMT and delta is six
    months, the result will be the 1st of July 1pm BST.

    Args:
        start_date: the datetime to add delta to
        delta: a timedelta to add to start_date as well as the effects of any
            DST shifts over that delta

    Returns:
        the date delta units of local time after start_date.
    """
    if timezone.is_naive(start_date):
        return start_date + delta
        # Can't do anything to a naive datetime
    else:
        # What we do is we strip out the timezone information from
        # the start date to turn it into a naive date, add the days
        # onto it, and then re-interpret it as a date in whatever the
        # original timezone works out to be in the result.  This has
        # the nice quality of shifting the date into the correct
        # local time when DST changes between the two dates.
        #
        # If anyone can find a less hacky way of doing this,
        # PLEASE replace it.  It makes me cry just thinking about it.
        return timezone.make_aware(
            timezone.make_naive(start_date, start_date.tzinfo) + delta,
            start_date.tzinfo
        )
