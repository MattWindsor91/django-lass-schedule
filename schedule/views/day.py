"""Views and constituent functions providing daily schedule services."""


from lass_utils import view_decorators

from . import common


## VIEWS
## Only actual views as referenced by URLconf should go here.
## Remember to add them to __init__.py!

@view_decorators.date_normalise
def schedule_day(request, start):
    """A view outputting a daily schedule.

    Args:
        request: the HTTP request this view is responding to
        start: a date representing the start of the week schedule.
    """
    return common.schedule_view(
        request=request,
        type='day',
        start=start
    )
