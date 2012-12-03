"""Home page schedule view."""

from django.shortcuts import render
from schedule.utils.list import coming_up
from django.views.decorators.cache import cache_page


@cache_page(60, key_prefix="home_schedule")  # Cache minutely
def home_schedule(request, num_shows=10, block_id=None):
    """Renders a view of the approaching schedule for the home page.

    """
    return render(
        request,
        'schedule/home-schedule.html',
        {
            'schedule': coming_up(quantity=num_shows)
        }
    )
