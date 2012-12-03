"""
URLconf for the ShowDB section of the `schedule` app.

"""

from django.conf.urls import patterns, url
from django.views.generic import ListView, DetailView

from schedule.models import Show
from urysite import url_regexes as ur


# Partial regular expressions
show_regex = r'(?P<pk>(-1|\d+))'
season_regex = r'(?P<season_num>[1-9]\d*)'
timeslot_regex = r'(?P<timeslot_num>[1-9]\d*)'

# Full URL expressions in terms of the above
showdb_show_regex, \
    showdb_season_regex, \
    showdb_timeslot_regex = ur.relatives(
        (
            (show_regex,),
            (show_regex, season_regex),
            (show_regex, season_regex, timeslot_regex),
        )
    )

urlpatterns = patterns(
    'schedule.views',
    url(r'^$',
        ListView.as_view(
            queryset=Show.objects.filter(
                show_type__has_showdb_entry=True)),
        name='show_index'),
    url(showdb_show_regex,
        DetailView.as_view(
            queryset=Show.objects.filter(
                show_type__has_showdb_entry=True)),
        name='show_detail'),
    url(showdb_season_regex,
        'season_detail',
        name='season_detail'),
    url(showdb_timeslot_regex,
        'timeslot_detail',
        name='timeslot_detail'),
)
