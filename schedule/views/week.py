"""
Views and constituent functions providing weekly schedule
services.

"""

import datetime

from lass_utils import view_decorators

from . import common


## VIEWS
## Only actual views as referenced by URLconf should go here.
## Remember to add them to __init__.py!

@view_decorators.date_normalise
def schedule_week(request, start):
    """A view outputting a weekly schedule.

    Args:
        request: the HTTP request this view is responding to
        start: a date representing the start of the week schedule.
    """
    return common.schedule_view(
        request=request,
        type='week',
        start=start
    )


## SUPPORTING FUNCTIONS
##
## Please DON'T export these through __init__.py
## Only export the actual views that are reachable through URLconf
## Thanks!

def to_monday(date):
    """Given a date, find the date of the Monday of its week."""
    days_after_monday = date.weekday()
    return date - datetime.timedelta(days=days_after_monday)
