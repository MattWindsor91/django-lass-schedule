"""
Provides the :class:`Schedule` class and its :class:`WeekSchedule` and
:class:`DaySchedule` implementations.

"""


class Schedule(object):
    """
    A show schedule.

    :class:`Schedule` is a high-level abstraction over the details of how a
    schedule is stored and retrieved.  It is a lazy object, in that it defers
    the act of compiling the schedule from model queries until the moment its
    contents are required.

    """
    def __init__(self, start, range, builder):
        """
        Creates a new :class:`Schedule`.

        This does *not* start processing the schedule; the schedule itself is
        calculated when required and stored thereafter.


        """
        self.start = start
        self.range = range

        self._data = None
        self.builder = lambda: builder(self)

    def previous(self):
        """
        Returns a schedule object representing the schedule period immediately
        before this one.

        """
        return Schedule(self.start - self.range, self.range, self.builder)

    def next(self):
        """
        Returns a schedule object representing the schedule period immediately
        after this one.

        """
        return Schedule(self.start + self.range, self.range, self.builder)

    @property
    def data(self):
        """
        Returns the schedule data, evaluating it if the schedule has not yet
        been computed.

        """
        if self._data is None:
            self._data = self.builder()

        return self._data
