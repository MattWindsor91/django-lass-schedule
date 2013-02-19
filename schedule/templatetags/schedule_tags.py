"""Template tags for the schedule system including ones for ShowDB."""

from django import template


register = template.Library()


@register.inclusion_tag('schedule/timeslot_link.html')
def timeslot_link(timeslot):
    """Renders link to slot if slot is in ShowDB, else just its title."""
    return {'timeslot': timeslot}


@register.inclusion_tag('schedule/schedule_contents.html')
def show_schedule(schedule):
    """Renders a schedule."""
    return {
        'schedule': schedule,
        # Why do we use the class for the template name like this?
        # Convention over configuration!
        'template': 'schedule/schedule_{}.html'.format(
            schedule.__class__.__name__.lower()
        )
    }
