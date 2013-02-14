"""The view used to create the schedule overview in the site's header.
"""

from django.shortcuts import render


def header(request, block_id=None):
    """
    View for the "On Air/Up Next" header summary of the schedule.

    """
    return render(
        request,
        'schedule/header.html',
    )
