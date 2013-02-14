"""
Views and constituent functions providing weekly schedule
services.

"""

from datetime import timedelta
from schedule.utils import object
from schedule.views import common


## VIEWS
## Only actual views as referenced by URLconf should go here.
## Remember to add them to __init__.py!

@common.date_normalise
def schedule_week(request, start):
    """A view outputting a weekly schedule.

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

def to_monday(date):
    """Given a date, find the date of the Monday of its week."""
    days_after_monday = date.weekday()
    return date - timedelta(days=days_after_monday)
