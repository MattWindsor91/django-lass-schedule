"""
Provides the :class:`Schedule` class and its :class:`WeekSchedule` and
:class:`DaySchedule` implementations.

"""

import datetime

from django.db import models as d_models

from .. import utils
from .. import models
from ..utils import block
from ..utils import range as r
from ..utils import week_table


class Schedule(object):
    """A show schedule.

    :class:`Schedule` is a high-level abstraction over the details of how a
    schedule is stored and retrieved.  It is a lazy object, in that it defers
    the act of compiling the schedule from model queries until the moment its
    contents are required.
    """
    def __init__(self, start, range, builder):
        """Creates a new :class:`Schedule`.

        This does *not* start processing the schedule; the schedule itself is
        calculated when required and stored thereafter.

        Args:
            start: A datetime representing the start of the period this
                schedule covers.
            range: A timedelta representing the duration of the period this
                schedule covers.  This is reinterpreted as a local time step.
            builder: A function, taking this schedule object, that returns the
                actual schedule data (or an object representing a lack of
                schedule).
        """
        self.start = start
        self.end = r.dst_add(start, range)
        self.range = self.end - self.start

        self._data = None
        self.builder = builder

    def replace(self, **kwargs):
        """Returns a copy of this schedule with the given replacements.

        The data will not be copied over, and will thus need to be recomputed.

        Args:
            kwargs: a set of keyword arguments that correspond to the
                parameters of __init__ to replace in the new object; any
                unspecified arguments are copied from this schedule.

        Returns:
            a new Schedule with the directed replacements made.
        """
        initargs = {
            key: getattr(self, key)
            for key in ['start', 'range', 'builder']
        }
        initargs.update(kwargs)

        return self.__class__(**initargs)

    def previous(self):
        """Returns the previous schedule.

        Returns:
            A schedule object representing the schedule period immediately
            before this one.
        """
        return self.replace(start=self.start - self.range)

    def next(self):
        """Returns the next schedule.

        Returns:
            A schedule object representing the schedule period immediately
            after this one.
        """
        return self.replace(start=self.start + self.range)

    @property
    def data(self):
        """Returns the schedule data.

        Because Schedule is lazy, this will evaluate the schedule data if not
        already computed.

        Returns:
            The schedule data.  The type of this is dependent on the builder
            function.
        """
        if self._data is None:
            self._data = self.builder(self)

        return self._data


# Note: These two classes accept range as an optional argument primarily to
# accommodate Schedule's replace method.

class DaySchedule(Schedule):
    """A schedule type that specifically works for day schedule ranges."""
    type = 'Day'

    def __init__(self, start, builder, range=None):
        """Initialises a DaySchedule."""
        super(DaySchedule, self).__init__(
            start=start,
            range=range if range else datetime.timedelta(days=1),
            builder=builder
        )

    def up(self):
        """Returns the full week schedule that this day schedule is contained
        within.
        """
        return WeekSchedule(start=self.start, builder=self.builder)

    def __unicode__(self):
        """Representation of this schedule object, in Unicode format."""
        return u'{:%A, %d %b %Y}'.format(self.start)

    @d_models.permalink
    def get_absolute_url(self):
        """Returns a URL representing this schedule."""
        return (
            'schedule.views.schedule_day',
            (),
            dict(zip(['year', 'week', 'weekday'], self.start.isocalendar()))
        )


class WeekSchedule(Schedule):
    """A schedule type that specifically works for week schedule ranges."""
    type = 'Week'

    def __init__(self, start, builder, range=None):
        """Initialises a WeekSchedule."""
        super(WeekSchedule, self).__init__(
            start=to_monday(start),
            range=range if range else datetime.timedelta(weeks=1),
            builder=builder
        )

    def tabulate(self):
        """Returns a processed form of the schedule data ready to render."""
        return week_table.tabulate(self)

    def __unicode__(self):
        """Representation of this schedule object, in Unicode format."""
        return u'Week commencing {:%d %b %Y}'.format(self.start)

    def days(self):
        """Returns a list of DaySchedules corresponding to days of this week.

        Returns:
            A list of seven DaySchedules in ascending chronological order
            from Monday to Friday, each starting at the same time as this
            WeekSchedule.
        """
        return [
            DaySchedule(
                start=self.start + datetime.timedelta(days=i),
                builder=self.builder
            )
            for i in range(0, 7)
        ]

    @d_models.permalink
    def get_absolute_url(self):
        """Returns a URL representing this schedule."""
        return (
            'schedule.views.schedule_week',
            (),
            dict(zip(['year', 'week'], self.start.isocalendar()[:2]))
        )


# Utility functions and miscellanea

def to_monday(date):
    """Takes a date object / Returns a date in its week / Day set to Monday"""
    # isocalendar()[2] is number of days since Monday plus one (Monday is #1)
    return date - datetime.timedelta(days=(date.isocalendar()[2] - 1))


def range_builder(schedule, timeslots=None):
    """A simple schedule data builder.

    Args:
        schedule: The Schedule object that this function is building data for.
        timeslots: An optional parameter allowing the Timeslot QuerySet from
            which the schedules are built to be changed from the default of
            Timeslot.objects.public().

    Returns:
        Either a list of schedule data, or one of the following strings
        representing excuses for not retrieving any:
            'empty' - The requested schedule point was outside of the bounds of
                known schedule data.
            'not_in_term' - The requested schedule point was in between two
                terms.  This usually represents a break in programming.
        These strings are distinct from any exceptions the builder might raise,
        which relate to schedule inconsistencies whereas these results are
        natural features of the schedule.
    """
    start = schedule.start
    end = schedule.end

    term = models.Term.of(start)
    if not term:
        result = 'empty' if not models.Term.before(start) else 'not_in_term'
    else:
        # Not 'if timeslots', that might evaluate the query!
        if timeslots is None:
            timeslots = models.Timeslot.objects.public()

        slots = list(timeslots.select_related().in_range(start, end))
        result = (
            block.annotate(utils.filler.fill(slots, start, end))
            if slots else 'empty'
        )
    return result
