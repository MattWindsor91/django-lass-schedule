from django.conf.urls import patterns, url, include

from urysite import url_regexes as ur


urlpatterns = patterns(
    'schedule.views',
    url(
        r'^$',
        'schedule_week',
        name='index'
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
    # WEEK SCHEDULES
    url(
        ur.WEEK_REGEX,
        'schedule_week',
        name='schedule_week'
    ),
    url(
        ur.WEEKDAY_REGEX,
        'schedule_week',
        name='schedule_weekday'
    ),
    url(r'^shows/', include('schedule.urls_showdb')),
)
