from django.conf.urls import patterns, url, include

from urysite import url_regexes as ur


urlpatterns = patterns(
    'schedule.views',
    url(
        r'^$',
        'schedule_week',
        name='schedule_index'
    ),
    # DAY SCHEDULES
    url(
        r'^today/',
        'schedule_day',
        name='today'
    ),
    url(
        ur.DAY_REGEX,
        'schedule_day',
        name='schedule_day'
    ),
    url(
        ur.WEEKDAY_REGEX,
        'schedule_day',
        name='schedule_weekday'
    ),
    # WEEK SCHEDULES
    url(
        r'^thisweek/',
        'schedule_week',
        name='this_week'
    ),
    url(
        ur.WEEK_REGEX,
        'schedule_week',
        name='schedule_week'
    ),
    url(r'^shows/', include('schedule.urls_showdb')),
)
