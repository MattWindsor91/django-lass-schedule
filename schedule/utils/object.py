"""
Provides the :class:`Schedule` class and its :class:`WeekSchedule` and
:class:`DaySchedule` implementations.

"""

from .. import utils
from .. import models


class Schedule(object):
    """A show schedule.

    :class:`Schedule` is a high-level abstraction over the details of how a
    schedule is stored and retrieved.  It is a lazy object, in that it defers
    the act of compiling the schedule from model queries until the moment its
    contents are required.
    """
    def __init__(self, type, start, range, builder):
        """Creates a new :class:`Schedule`.

        This does *not* start processing the schedule; the schedule itself is
        calculated when required and stored thereafter.

        Args:
            type: A string naming the type of schedule data held within this
                schedule;  this is a hint to the schedule renderer for
                formatting the schedule context interface.
            start: A datetime representing the start of the period this
                schedule covers.
            range: A timedelta representing the duration of the period this
                schedule covers.
            builder: A function, taking this schedule object, that returns the
                actual schedule data (or an object representing a lack of
                schedule).
        """
        self.type = type
        self.start = start
        self.range = range

        self._data = None
        self.builder = lambda: builder(self)

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
            for key in ['type', 'start', 'range', 'builder']
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
            self._data = self.builder()

        return self._data


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
    end = start + schedule.step

    term = models.Term.of(start)
    if not term:
        result = 'empty' if not models.Term.before(start) else 'not_in_term'
    else:
        if not timeslots:
            timeslots = models.Timeslot.objects.public()

        slots = list(timeslots.in_range(start, end))
        result = utils.filler.fill(slots, start, end) if slots else 'empty'
    return result