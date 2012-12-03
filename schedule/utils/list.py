"""Functions for creating non-timerange lists of timeslots.

"""

from schedule.models import Timeslot
from schedule.utils import filler
from django.utils import timezone
from django.db.models import F


def coming_up(date=None,
              quantity=10,
              with_filler_timeslots=True,
              with_private_shows=False):
    """Retrieves the next 'quantity' timeslots, relative to 'date'.

    If there are not enough timeslots to make up 'quantity', the
    resulting list may be smaller.

    If 'with_filler_timeslots' is True, these are included in the
    total.

    Keyword arguments:
    date -- the reference point from which the list is made; the
        first listed timeslot is the timeslot active at the moment
        of time 'date' refers to (default: now)
    quantity -- the maximum amount of slots to retrieve, as a
        positive integer (default: 10)
    with_filler_timeslots -- if True, non-contiguous entries in the
        list will cause the resulting gap to be filled in with a
        filler timeslot; filler timeslots count towards 'quantity'
        (default: True)
    with_private_shows -- if True, even shows marked as private
        will be shown (these usually denote non-broadcast events such
        as demos and recordings).
    """
    if quantity <= 0:
        raise ValueError("'quantity' must be positive.")
    if date is None:
        date = timezone.now()

    query = Timeslot.objects.filter(
        duration__gte=date - F('start_time')
    ).order_by('start_time')

    if not with_private_shows:
        query = query.exclude(
            season__show__show_type__public=False
        )

    coming_up_unfilled = list(query)[:quantity]

    if with_filler_timeslots:
        end = (date
               if not coming_up_unfilled
               else coming_up_unfilled[-1].end_time())
        filled_up = filler.fill(
            coming_up_unfilled,
            date,
            end)
        # Filling might have added some more slots, so we need to
        # re-trim
        coming_up = filled_up[:quantity]
    else:
        coming_up = coming_up_unfilled
    return coming_up
