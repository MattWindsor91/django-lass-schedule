"""The view used to create the schedule overview in the site's header.

"""

from schedule.utils import list
from django.shortcuts import render


def header(request, block_id=None):
    """
    View for the "On Air/Up Next" header summary of the schedule.

    """
    coming_up_list = list.coming_up(quantity=2)
    length = len(coming_up_list)
    if length == 1:
        on_air = coming_up_list[0]
        up_next = None
    elif length == 2:
        on_air, up_next = coming_up_list
    else:
        raise ValueError(
            "Coming up list is incorrect size, got |{0}|".format(
                length))
    return render(
        request,
        'schedule/header.html',
        {'on_air': on_air,
            'up_next': up_next})
