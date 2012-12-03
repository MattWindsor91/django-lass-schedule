# Only import actual URLconfed views here!
# It keeps things tidier.
from schedule.views.day import schedule_weekday, schedule_day, today
from schedule.views.week import schedule_week, index
from schedule.views.header import header

from schedule.views.showdb import season_detail
from schedule.views.showdb import timeslot_detail

from schedule.views.home import home_schedule
