"""Functions for building a weekly schedule table.

You will probably want 'tabulate' specifically.
"""

from django.utils import timezone

from .. import utils
from ..utils import nltime


###############################################################################
# Internal constants

# Common timedeltas
HOUR = timezone.timedelta(hours=1)
DAY = timezone.timedelta(days=1)


# The amount to add to the day number to get the schedule table column
# representing that day.
SCHEDULE_DAY_OFFSET = 1


# The column of the schedule table holding the time.
SCHEDULE_TIME_COL = 0


###############################################################################
# Public interface

def tabulate(schedule):
    """Takes a list of slots and converts it into a week schedule table.

    Args:
        schedule: the (Week)Schedule to pull data from.

    Returns:
        a list of schedule rows; each row begins with the row start and
        duration, then consists of tuples of shows active during that row, and
        the number of rows they span.  Duplicated entries (those that carry on
        from the previous row) are marked with None.
    """
    data = schedule.data
    if isinstance(data, basestring):
        # This is just an error signifier, pass it through.
        table = data
    else:
        nlstart = nltime.nld(schedule.start)
        data_lists, partitions = split_days(nlstart, schedule.data)
        table = empty_table(nlstart, partitions, len(data_lists))
        populate_table(table, data_lists)
    return table


###############################################################################
# Internals

# 1. Day splitting and partitioning #

def split_days(nlstart, data):
    """Takes a list of slots and splits it into many lists of one day each.

    This function also creates a set of times representing the starts of
    timeslots across the day lists, as local-time deltas between the schedule
    start and the timeslot start.  This is useful for dividing the schedule
    into rows later.

    Args:
        nlstart: the naive local datetime representing the schedule start.
        data: the schedule data, as a fully filled list of timeslots spanning
            the schedule's full range and starting at the schedule's designated
            start

    Returns:
        a tuple containing the result of splitting the data into day lists, and
        the set of observed show start times for dividing the schedule up into
        rows later
    """
    done_day_lists = []
    day_list = []
    partitions = set([])

    day_start = nlstart
    day_end = day_start + DAY

    for slot in data:
        nlslot = nltime.nld(slot.start_time)
        # If the next slot is outside the day we're looking at. rotate it.
        # To deal with shows straddling multiple days, check for multiple
        # rotations (hence the while loop).
        while day_end <= nlslot:
            day_list = rotate_day(day_end, day_list, done_day_lists)
            day_start, day_end = day_end, day_end + DAY

        day_list.append(slot)
        add_partitions(day_start, day_end, slot, partitions)

    # Finish off by pushing the last day onto the list, as nothing else will
    done_day_lists.append(day_list)
    return done_day_lists, partitions


def add_partitions(day_start, day_end, slot, partitions):
    """Add row boundaries arising from this slot to the partition list.

    Whether or not the timeslot emits row boundaries depends on its type;
    generally filler slots will not emit full row boundaries, causing the
    schedule to 'fold up' where no shows are scheduled at that time for an
    entire week.

    Args:
        day_start: the naive local time of the start of the day currently being
            split.
        day_end: the naive local time of the end of the day currently being
            split.
        slot: the timeslot whose start and end times may be added as row
            partitions.
        partitions: the set of partitions that may be modified by this
            function.
    """
    if not slot.is_collapsible:
        # Prevent negative partitions if the show started on a previous day.
        start_p = max(day_start, nltime.nld(slot.start_time)) - day_start
        # And overly large ones if the show ends on another day.
        end_p = min(day_end, nltime.nld(slot.end_time)) - day_start

        # Don't add end_p - if our schedule is sound, then there should be no
        # need to partition on it (all the ends are starts of other shows, or
        # the ends of days which we don't want to be partitioned on).
        partitions.add(start_p)

        # Now add all the exact hours between start_p and end_p, if any
        # (hour_p is set to the next hour after start_p)
        hour_p = timezone.timedelta(
            days=start_p.days,
            seconds=(
                start_p.seconds - (start_p.seconds % (60 * 60))
            ) + (60 * 60)
        )
        while hour_p < end_p:
            partitions.add(hour_p)
            hour_p += HOUR


def rotate_day(day_end, day_list, done_day_lists):
    """Ends the current day and sets things up ready to process the next day.

    Args:
        day_end: the (naive local) datetime of the end of the day that is about
            to finish (and the start of the next day)
        day_list: the completed list of timeslots for the day being finished.
        done_day_lists: the list of completed day lists (in chronological
            order) to push the new day onto
    Returns:
        the initial list for the new day, which may or may not be empty
        depending on show day crossover.
    """
    # We should NEVER be storing an empty list, as every day should at least
    # have one show (the filler show).
    if not day_list:
        raise utils.exceptions.ScheduleInconsistencyError(
            'split_days encountered empty day list, is filler working? '
            '(day_end={} day_list={} done_day_lists={})'.format(
                day_end,
                day_list,
                done_day_lists
            )
        )

    done_day_lists.append(day_list)

    # We need to see if the last show we processed straddles the boundary
    # between the two days and, if so, make sure it appears at the start of the
    # new list too.
    last_show = day_list[-1]
    return [last_show] if nltime.nld(last_show.end_time) > day_end else []


# 2. Empty table generation #

def empty_table(start, partitions, n_cols):
    """Creates an empty schedule table.

    Args:
        start: the (naive local) schedule start datetime. See nld().
        partitions: the set of row starts, as offsets from nlstart.
        n_cols: the number of schedule columns (days), usually 7.

    Returns:
        an empty schedule table ready for population with show data,
        implemented as a list of row lists.
        The table will contain len(partitions) rows, each containing the naive
        time of their occurrence (on the first day of the schedule; add day
        offsets for the other days), their offset from nlstart, and then
        num_cols instances of None ready to be filled with schedule data.
    """
    return [[(start + i)] + ([None] * n_cols) for i in sorted(partitions)]


# 3. Population #

def populate_table(table, data_lists):
    """Populates empty schedule tables with data from the given lists.

    Args:
        table: the empty table (generally created by empty_table) to populate
            with schedule data; this is potentially mutated in-place.
        data_lists: a list of lists, each representing one day of consecutive
            timeslots.

    Returns:
        the populated table, which may or may not be the same object as table
        depending on implementation.
    """
    for i, day in enumerate(data_lists):
        populate_table_day(
            make_row_date(table, i),
            make_add_to_table(table, i),
            day
        )
    return table


def populate_table_day(row_date, add_to_table, day):
    """Adds a day of slots into the table using the given functions.

    Args:
        row_date: a function taking a table row index and returning the naive
            local datetime of its start on this day.
        add_to_table: a function taking a table row index, a timeslot whose
            record starting on that row and the number of rows it spans, and
            adding it into the schedule table.
    """
    current_row = 0
    for slot in day:
        start_row = current_row
        hit_bottom = False

        # How much local time does this slot take up?
        nlend = nltime.nld(slot.end_time)

        # Work out how many rows this slot fits into.
        try:
            while row_date(current_row) < nlend:
                current_row += 1
        except IndexError:
            # This usually means this show crosses over the day boundary;
            # this is normal.
            hit_bottom = True
        else:
            # If our partitioning is sound and we haven't run off the end
            # of a day, then the slot must fit exactly into one or more
            # rows.
            if not hit_bottom and row_date(current_row) > nlend:
                raise utils.exceptions.ScheduleInconsistencyError(
                    'Partitioning unsound - show exceeds partition bounds.'
                    ' (Row {}, show {}, date {} > {} < {})'.format(
                        current_row,
                        slot,
                        row_date(current_row),
                        nlend,
                        row_date(current_row + 1)
                    )
                )

        add_to_table(start_row, slot, current_row - start_row)


###############################################################################
# Higher-order functions

def make_row_date(table, days):
    """A function that makes a function mapping rows to their starting
    datetimes.

    Args:
        table: the schedule table the returned function will look-up dates in.
        days: the number of days since the start of the schedule.

    Returns:
        a function closed over table and day_offset that takes a row and
        returns its datetime for the day being considered.
    """
    offset = timezone.timedelta(days=days)
    return lambda row: table[row][SCHEDULE_TIME_COL] + offset


def make_add_to_table(table, days):
    """A function that makes a function that adds a slot into a table.

    Args:
        table: the schedule table the returned function will add entries into.
        days: the number of days since the start of the schedule.

    Returns:
        a function closed over table and day_offset that takes a row, timeslot
        to place on that row and that timeslot's row occupacy, and inserts the
        data into the schedule table.
    """
    col = SCHEDULE_DAY_OFFSET + days

    # Not an expression, therefore cannot be a lambda.
    def f(row, slot, rows):
        if rows > 0:
            table[row][col] = slot, rows

    return f
