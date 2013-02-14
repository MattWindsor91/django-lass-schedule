# Only import actual URLconfed views here!
# It keeps things tidier.
from schedule.views.day import schedule_day
schedule_day = schedule_day

from schedule.views.week import schedule_week
schedule_week = schedule_week

from schedule.views.header import header
header = header

from schedule.views.showdb import season_detail
season_detail = season_detail

from schedule.views.showdb import timeslot_detail
timeslot_detail = timeslot_detail

from schedule.views.home import home_schedule
home_schedule = home_schedule
