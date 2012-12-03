"""The ``filler`` module provides functions for manipulating and
inserting *filler slots*.

Filler slots are fake timeslots, tied to a fake season (which is
assigned to a real show), that are optionally used to pad out gaps
in timeslot ranges.

This allows functions further up the chain to work with the
assumption that timeslot ranges are contiguous (that is, there are
no gaps between one timeslot's end and another timeslot's start).

Branding filler shows
=====================

At the time of writing, the filler slots correspond to URY Jukebox
programming, but the filler show is stored in the show database
as an actual show and thus the branding of the filler programming may
vary via the show metadata system.

Defining the filler show
========================

The filler show must exist in the database as the only show with the
show type named 'filler'.

.. WARNING:
   This show type obviously must also exist.

"""

# NOTE: A lot of this module involves subversion of the schedule
# system in order to make filler slots appear to be real shows to
# the higher levels of the website.  As always, improvements are
# very welcome.

from schedule.models import Term, Show, Season, Timeslot
from django.db.models import F
from django.core.cache import cache


FILLER_SHOW_CACHE_TIME = 60 * 60 * 24  # One day


def show(start_time, duration):
    """
    Retrieves a parent show usable for filler timeslots.

    Keyword arguments:
    start_time -- the start time of the filler timeslot being
        created, as an aware datetime
    duration -- the duration of the filler timeslot being
        created, as a timedelta
    """
    cached = cache.get('filler-show')
    if cached:
        show = cached
    else:
        show = Show.objects.get(show_type__name__iexact='filler')
        cache.set('filler-show', show, FILLER_SHOW_CACHE_TIME)
    return show


def term(start_time, duration):
    """
    Retrieves a university term that is usable for a filler slot
    with the given start time and duration (or, more specifically,
    the pseudo-season thereof).

    Keyword arguments:
    start_time -- the start time of the filler timeslot being
        created, as an aware datetime
    duration -- the duration of the filler timeslot being
        created, as a timedelta
    """
    term = Term.of(start_time)
    return term if term else Term.before(start_time)
    # It's better to return a term that only slightly makes
    # sense over not returning a term at all


def season(start_time, duration):
    """
    Retrieves a parent season usable for filler timeslots.

    Keyword arguments:
    start_time -- the start time of the filler timeslot being
        created, as an aware datetime
    duration -- the duration of the filler timeslot being
        created, as a timedelta
    """
    this_term = term(start_time, duration)
    if this_term is None:
        raise ValueError(
            "Tried to create filler show outside a term.")
    return Season(
        show=show(start_time, duration),
        term=this_term,
        date_submitted=this_term.start_date)


def timeslot(start_time, end_time=None, duration=None):
    """
    Creates a new timeslot that is bound to the URY Jukebox.

    Keyword arguments:
    start_time -- the start time of the filler timeslot being
        created, as an aware datetime
    end_time -- the end time of the filler timeslot being
        created, as an aware datetime; this must be None if
        duration is used
    duration -- the duration of the filler timeslot being
        created, as a timedelta; this must be None if end_time
        is used
     """
    if duration is None:
        if end_time is None:
            raise ValueError('Specify end or duration.')
        else:
            duration = end_time - start_time
    elif end_time is not None:
        raise ValueError('Do not specify both end and duration.')

    return Timeslot(
        season=season(start_time, end_time),
        start_time=start_time,
        duration=duration)


## FILLING ALGORITHM HELPERS

def end_before(time):
    """
    Attempts to find the end of the last (real) timeslot that was
    on before the given time.

    If there was no such timeslot, the original time is returned.

    """
    slots = Timeslot.objects.filter(
        start_time__lte=time - F('duration'))
    try:
        result = slots.latest().end_time()
    except Timeslot.DoesNotExist:
        result = time
    return result


def start_after(time):
    """
    Attempts to find the start of the first (real) timeslot that is
    on after the given time.

    If there is no such timeslot, the original time is returned.

    """
    slots = Timeslot.objects.filter(start_time__gte=time)
    try:
        result = slots.order_by('start_time')[0].start_time
    except IndexError:
        result = time
    return result


## FILLING ALGORITHM

def fill(timeslots, start_time, end_time):
    """
    Fills any gaps in the given timeslot list with filler slots,
    such that the list is fully populated from the given start time
    to the given end time.

    Keyword arguments:
    timeslots -- the list of timeslots, may be empty
    start_time -- the start date/time
    end_time -- the end date/time

    """
    if start_time > end_time:
        raise ValueError('Start time is after end time.')

    if not timeslots:
        filled_timeslots = [
            timeslot(
                end_before(start_time),
                start_after(end_time))]
    else:
        filled_timeslots = []
        # Fill in any gap before the first item
        if timeslots[0].start_time > start_time:
            filled_timeslots.append(
                timeslot(
                    end_before(start_time),
                    timeslots[0].start_time)
            )
        # Next, fill in everything else
        # We're doing this by comparing each new show to the
        # last inserted show (if any) to see if they follow on from
        # each other; if they don't then we add a filler slot before
        # adding the next show
        for ts in timeslots:
            if filled_timeslots and (
                    filled_timeslots[-1].end_time()
                    < ts.start_time
            ):
                filled_timeslots.append(
                    timeslot(
                        filled_timeslots[-1].end_time(),
                        ts.start_time
                    )
                )
            filled_timeslots.append(ts)
        # Finally fill the end
        if filled_timeslots[-1].end_time() < end_time:
            filled_timeslots.append(
                timeslot(
                    filled_timeslots[-1].end_time(),
                    start_after(end_time)
                )
            )
    return filled_timeslots
