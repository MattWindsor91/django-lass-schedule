"""
Views and constituent functions providing daily schedule
services.

"""

from datetime import timedelta
from ..utils import range
from ..utils import object
from . import common


## VIEWS
## Only actual views as referenced by URLconf should go here.
## Remember to add them to __init__.py!
@common.date_normalise
def schedule_day(request, start):
    """A view outputting a daily schedule.

    Args:
        request: the HTTP request this view is responding to
        start: a date representing the start of the week schedule.
    """
    return object.Schedule(
        'Day',
        start,
        timedelta(days=1),
        common.builder_from_request(request)
    ).as_view()


## SUPPORTING FUNCTIONS
##
## Please DON'T export these through __init__.py
## Only export the actual views that are reachable through URLconf
## Thanks!

def make_day_schedule(start, step, timeslots):
    return range.day(start)
