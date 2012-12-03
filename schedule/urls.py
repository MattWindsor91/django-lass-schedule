from django.conf.urls import patterns, url, include

from urysite import url_regexes as ur


urlpatterns = patterns(
    'schedule.views',
    url(r'^$',
        'index',
        name='schedule_index'),
    url(r'^today/',
        'today',
        name='today'),
    url(ur.WEEK_REGEX,
        'schedule_week',
        name='schedule_week'),
    url(ur.WEEKDAY_REGEX,
        'schedule_weekday',
        name='schedule_weekday'),
    url(ur.DAY_REGEX,
        'schedule_day',
        name='schedule_day'),
    url(r'^shows/', include('schedule.urls_showdb')),
)
