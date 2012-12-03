"""Collection of views that together constitute the 'show database'.

"""

from django.views.generic import DetailView
from schedule.models import Show, Season, Timeslot
from django.shortcuts import get_object_or_404
from django.http import Http404


def relative_season(show_id, season_num):
    """Attempts to find the 'season_num'th season of the show with
    ID 'show_id', where the count starts from 0.

    """
    show = get_object_or_404(
        Show,
        pk=show_id,
        show_type__has_showdb_entry=True
    )
    return (show.season_set.all()[season_num]
            if show.season_set.count() > season_num
            else None)


def relative_timeslot(show_id, season_num, timeslot_num):
    """Attempts to find the 'timeslot_num'th timeslot of the
    'season_num'th season of the show with ID 'show_id', where the
    count starts from 0.

    """
    season = relative_season(show_id, season_num)
    return (season.timeslot_set.all()[timeslot_num]
            if (season and season.timeslot_set.count() > timeslot_num)
            else None)


def season_detail(request, pk, season_num):
    """View detailing a show season.

    The season number is relative to the show, numbering starting
    from 1.

    """
    season = relative_season(pk, int(season_num) - 1)
    if season is None:
        raise Http404('Season does not exist.')
    return DetailView.as_view(model=Season)(request, pk=season.pk)


def timeslot_detail(request, pk, season_num, timeslot_num):
    """View detailing a season timeslot.

    The season number is relative to the show, as is the timeslot
    number to the season, both sequences starting from 1.

    """
    timeslot = relative_timeslot(
        pk,
        int(season_num) - 1,
        int(timeslot_num) - 1)
    if timeslot is None:
        raise Http404('Timeslot does not exist.')
    return DetailView.as_view(model=Timeslot)(request, pk=timeslot.pk)
