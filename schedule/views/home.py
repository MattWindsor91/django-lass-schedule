"""Home page schedule view."""

from django.shortcuts import render


def home_schedule(request, block_id=None):
    """Renders a view of the approaching schedule for the home page.

    """
    # Uses template context now
    return render(
        request,
        'schedule/home-schedule.html',
    )
