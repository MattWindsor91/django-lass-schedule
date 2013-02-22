"""
URLconf for the ShowDB section of the `schedule` app.

"""

from django.conf.urls import patterns, url
from django.views.generic import ListView, DetailView

from schedule import models
from urysite import url_regexes as ur


# Partial regular expressions
pk_regex = r'(?P<pk>(-1|\d+))'
show_regex = pk_regex
season_regex = r'(?P<season_num>[1-9]\d*)'
timeslot_regex = r'(?P<timeslot_num>[1-9]\d*)'

# Full URL expressions in terms of the above
showdb_show_regex, \
    showdb_season_regex, \
    showdb_timeslot_regex, \
    showdb_season_relative_regex, \
    showdb_timeslot_relative_regex = ur.relatives(
        (
            (show_regex,),
            ('seasons', pk_regex),
            ('timeslots', pk_regex),
            (show_regex, season_regex),
            (show_regex, season_regex, timeslot_regex),
        )
    )

urlpatterns = patterns(
    'schedule.views',
    url(
        r'^$',
        ListView.as_view(queryset=models.Show.objects.listable()),
        name='show_index'
    ),
    url(
        showdb_show_regex,
        DetailView.as_view(queryset=models.Show.objects.listable()),
        name='show_detail'
    ),
    url(
        showdb_season_regex,
        DetailView.as_view(queryset=models.Season.objects.public()),
        name='season_detail'
    ),
    url(
        showdb_timeslot_regex,
        DetailView.as_view(queryset=models.Timeslot.objects.public()),
        name='timeslot_detail'
    ),
    url(
        showdb_season_relative_regex,
        'season_detail',
        name='season_detail_relative'
    ),
    url(
        showdb_timeslot_relative_regex,
        'timeslot_detail',
        name='timeslot_detail_relative'
    ),
)
