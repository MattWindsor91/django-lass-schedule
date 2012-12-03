"""Classes representing a weekly schedule table.

The weekly schedule table is complicated to construct from the
timeslot ranges it is built up from, and as such these classes and
their constituent functions are quite voluminous.  Any intrepid
coder who can cut away swathes of this module without sacrificing its
functionality is a true hero.

"""

from datetime import timedelta
from schedule.utils import range as r
from django.utils import timezone


def time_until_next_hour(time):
    """Returns the timedelta representing the amount of
    time between the given (date)time and the start of
    the hour immediately following it.

    """
    return (timedelta(hours=1)
            - timedelta(minutes=time.minute,
                        seconds=time.second,
                        microseconds=time.microsecond))


def calculate_row_duration(time_remaining_on_shows,
                           start_date,
                           align_to_hour):
    """Decides how long, as a timedelta, the current week
    schedule row's spanned time period should be.

    The result is the amount of time until either the next
    show ends or, if align_to_hour is True, the amount of
    time until the next hour- whichever is shorter.
    """
    # Decide where to split the row, initially we'll use the
    # shortest remaining show time
    shortest_duration = min(time_remaining_on_shows)
    # However, if we're aligning to hours, we'll need to
    # prematurely split the row to accomodate it
    return (shortest_duration
            if not align_to_hour
            else min(shortest_duration,
                     time_until_next_hour(start_date)))


def initial_time_remaining(week, start_date):
    """Creates the initial list of remaining show durations.

    If a show starts exactly on the start time, then its initial
    remaining duration is its full duration; otherwise, the
    difference is taken off so the initial duration represents
    the amount of show time left at the start time.

    """
    diff_from_start = (
        lambda day, num_days:
        r.dst_add_days(timezone.localtime(start_date), num_days)
        - day[0].start_time)

    return [min(day[0].duration,
                day[0].duration - diff_from_start(day, num_days))
            for num_days, day in enumerate(week)]


def tabulate_week_lists(week,
                        start_date,
                        align_to_hour=True):
    """Creates a schedule week table from a group of seven lists.

    You should generally use 'tabulate' instead of directly
    invoking this.

    """
    assert len(week) == 7, "Must be 7 days in the week list."
    assert False not in (len(day) > 0 for day in week), \
        "All week lists must be populated."

    row_date = start_date
    time_remaining_on_shows = initial_time_remaining(week, start_date)
    table = WeekTable()

    # Assuming that either all weeks are populated or none are
    while True in (len(day) > 0 for day in week):
        # If any of the current shows' remaining durations would
        # send the schedule over 24 hours, then we take drastic
        # action by culling its remaining duration and cancelling
        # all the subsequent shows.
        # This is so each day is the same length.
        # (Note that Jukebox filling ensures each day is AT LEAST
        # 24 hours long)
        for day_index in xrange(len(time_remaining_on_shows)):
            assert len(week[day_index]) > 0, \
                "All days must be of equal length."
            assert time_remaining_on_shows[day_index] != \
                timedelta(seconds=0), \
                """A time remaining on show entry is zero.
                This show should have been dropped off the
                stack already.
                """
            if ((row_date + time_remaining_on_shows[day_index])
                - start_date > timedelta(days=1)):
                time_remaining_on_shows[day_index] = \
                    (start_date + timedelta(days=1)) - row_date
                week[day_index] = week[day_index][0:1]

        row_duration = calculate_row_duration(
            time_remaining_on_shows,
            row_date,
            align_to_hour)

        row = WeekTable.Row(row_date, row_duration)
        # Now shove shows into the row
        for day_index, day in enumerate(week):
            # Because we pick either the shortest remaining show
            # duration or something shorter than it as the row
            # duration, these assertions should hold
            assert time_remaining_on_shows[day_index] >= \
                row_duration, """Row must never be bigger than
                the amount of time remaining for a show in the
                queue."""
            assert day[0].duration >= row_duration, \
                """Row must never be bigger than a show's
                duration."""

            row.add(day[0])

            # Push spent shows off the day stacks, deduct
            # row duration from time remaining on unspent ones
            if (time_remaining_on_shows[day_index] == row_duration):
                del day[0]
                time_remaining_on_shows[day_index] = (
                    day[0].duration if len(day) > 0 else None)
            else:
                time_remaining_on_shows[day_index] -= \
                    row_duration
            assert time_remaining_on_shows[day_index] is None \
                or time_remaining_on_shows[day_index] > \
                timedelta(seconds=0), """No time remaining on
                unpopped show."""

        # Get ready for next row
        row_date += row_duration
        table.add(row)
    return table


class WeekTable(object):
    """A weekly schedule, in tabular form and ready to be outputted
    in a template.

    """

    class Row(object):
        """A row in a schedule table."""
        class IncorrectlySizedRowException(Exception):
            """Exception thrown when an add operation that would make
            a row too large occurs, or when a read operation on a row
            that is insufficiently sized happens."""
            pass

        class Entry(object):
            """An entry in a schedule table row.

            Schedule table entries depict part of a show timeslot
            that airs inside the time period of its parent row.

            The booleans is_start and is_end state whether this entry
            marks the start and/or the end of the referenced show
            respectively.

            """
            def __init__(self, timeslot):
                self.row_span = 1
                self.timeslot = timeslot

        def __init__(self, start_time, duration):
            self.start_time = start_time
            self.entries = []
            self.see_above = []
            self.duration = duration

        def add(self, timeslot):
            """Adds a timeslot to the row.

            No inter-row compressing is done at this stage.

            """
            if len(self.entries) == 7:
                # We don't want more than seven days!
                raise WeekTable.Row.IncorrectlySizedRowException
            self.entries.append(WeekTable.Row.Entry(timeslot))

        def real_column(self, column):
            """Returns the actual index of a given column in the row.

            The reason the column number and entries index may be
            different is because of row compression.

            """
            return column - \
                len([x for x in self.see_above if x < column])

        def get(self, column):
            """Gets the entry at the given column.

            If the row has been compressed (some of its contents
            removed due to being referenced in rows above it in the
            table), this method will return the item that would
            normally be in the column, or None if the column in
            question has been thus affected.

            """
            return (None if column in self.see_above
                    else self.entries[self.real_column(column)])

        def inc_row_span(self, column):
            """Increases the row span count of the given (logical)
            column.

            This should be used when compressing the row below this
            one in the table.
            """
            self.get(column).row_span += 1

    def __init__(self):
        self.rows = []

    def add(self, row):
        """Adds a new row, compressing it in the process.

        If any row entry is defined as not being the show start, and
        an entry for the same show appears in the same column of the
        previous row, then the show is deleted from the inserted row
        and the row span of the other entry is incremented.

        """
        if not isinstance(row, WeekTable.Row):
            raise TypeError("Cannot add things other than Rows.")
        # Compress row by merging where possible with above
        # row
        if len(self.rows) > 0:
            for col, show in enumerate(row.entries[:]):
                slot = show.timeslot
                # If the show was in the previous two rows, the
                # row above will already have been compressed, and
                # this manifests itself in the above show being
                # None.
                # We need to keep going through the rows until we
                # hit an actual show, then see if it's the same
                # as the one we're adding, to decide whether to
                # compress the entry in this row too.
                for above_row in reversed(self.rows):
                    above_show = above_row.get(col)
                    if above_show is None:
                        continue
                    elif slot is above_row.get(col).timeslot:
                        # Compress by adding span to previous row
                        row.entries.remove(show)
                        row.see_above.append(col)
                        above_row.inc_row_span(col)
        self.rows.append(row)

    @classmethod
    def tabulate(cls, range_list):
        """Creates a schedule week table.

        Keyword arguments:
        range_list -- the list of seven schedule ranges that
            constitute the schedule week to tabulate, as outputted by
            (for example) Timeslot.timeslots_in_week with split_days
            set to True

        """
        # Sanity check the data
        # The range needs to have very specific properties in order
        # for the schedule tabulator to work right now.
        if type(range_list) != list:
            raise ValueError(
                "Schedule table data list must be an actual list.")
        elif len(range_list) != 7:
            raise ValueError(
                """Schedule table data list must contain 7 ranges.
                Instead got {0} ranges""".format(len(range_list)))
        # Extract data while sanity checking
        range_list_pure = []
        for range_data in range_list:
            if range_data.with_jukebox_entries is False:
                raise ValueError(
                    "Schedule column data must include Jukebox.")
            elif range_data.timespan != timedelta(days=1):
                raise ValueError(
                    "Schedule column data must span one day each.")
            elif range_data.exclude_before_start:
                raise ValueError(
                    "Schedule column data must include-before-start.")
            elif range_data.exclude_after_end:
                raise ValueError(
                    "Schedule column data must include-after-end.")
            elif range_data.exclude_subsuming:
                raise ValueError(
                    "Schedule column data must include-subsuming.")
            range_list_pure.append(range_data.data[:])
        return tabulate_week_lists(
            range_list_pure,
            range_list[0].start)
