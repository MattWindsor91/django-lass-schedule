"""Classes representing a weekly schedule table.

The weekly schedule table is complicated to construct from the
timeslot ranges it is built up from, and as such these classes and
their constituent functions are quite voluminous.  Any intrepid
coder who can cut away swathes of this module without sacrificing its
functionality is a true hero.

"""

from django.utils import timezone

from .. import utils


# This is a very common timedelta, so we use it as a constant.
DAY = timezone.timedelta(days=1)


# The amount to add to the day number to get the schedule table column
# representing that day.
SCHEDULE_DAY_OFFSET = 1


# The column of the schedule table holding the time.
SCHEDULE_TIME_COL = 0


def un_nld(nldate):
    """Converts naive dates of local times into their aware date versions.

    This is the inverse of nld.

    Args:
        nldate: the naive datetime representing a local time

    Returns:
        the aware datetime equivalent
    """
    return timezone.make_aware(nldate, timezone.get_current_timezone())


def nldiff(a, b):
    """Takes the local-time difference between an aware datetime object
    pair.

    This is equivalent to nld(a) - nld(b).

    Args:
        a: the datetime minuend.
        b: the datetime subtrahend.

    Returns:
        the local-time timedelta between the two (in other words, the
        amount of "local time" in between the two dates, which may not be the
        same as the amount of actual time due to DST shifting).
    """
    return nld(a) - nld(b)


def nld(date):
    """Converts aware dates to their naive local time representation.

    In other words, converts the timezone from the aware date timezone (usually
    UTC) to the current local timezone, then immediately strips the timezone
    data.

    Args:
        date: the active datetime to convert to naive local

    Returns:
        the naive local datetime equivalent
    """
    local = timezone.localtime(date)
    return timezone.make_naive(local, local.tzinfo)


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
        nlstart = nld(schedule.start)
        data_lists, partitions = split_days(nlstart, schedule.data)
        table = empty_table(nlstart, partitions, len(data_lists))
        populate_table(table, data_lists)
    return table


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
    def row_date(row, day_offset):
        return table[row][SCHEDULE_TIME_COL] + day_offset

    for i, day in enumerate(data_lists):
        day_offset = timezone.timedelta(days=i)
        current_row = 0
        for slot in day:
            # How much local time does this slot take up?
            nlend = nld(slot.end_time())

            # Work out how many rows this slot fits into.
            add_rows = 0
            try:
                while row_date(current_row + add_rows, day_offset) < nlend:
                    add_rows += 1
            except IndexError:
                # This usually means this show crosses over the day boundary;
                # this is normal.
                pass

            # If our partitioning is sound, then the slot must fit exactly into
            # one or more rows.
            if row_date(current_row + add_rows, day_offset) >= nlend:
                raise utils.exceptions.ScheduleInconsistencyError(
                    'Partitioning unsound - show exceeds partition bounds.'
                )

            # Mark the slot at the top of its row-span
            table[current_row] = slot, add_rows
            current_row += add_rows

    return table


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
    partitions = set([timezone.timedelta(days=0)])

    day_start = nlstart
    day_end = day_start + DAY

    for slot in data:
        nlslot = nld(slot.start_time)
        # If the next slot is outside the day we're looking at. rotate it.
        # To deal with shows straddling multiple days, check for multiple
        # rotations (hence the while loop).
        while day_end <= nlslot:
            day_start, day_end = day_end, day_start + DAY
            day_list = rotate_day(day_start, day_list, done_day_lists)

        day_list.append(slot)
        partitions.add(nlslot - day_start)

    # Finish off by pushing the last day onto the list, as nothing else will
    done_day_lists.append(day_list)
    return done_day_lists, partitions


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
    return [last_show] if nld(last_show.end_time()) > day_end else []


def empty_table(nlstart, partitions, n_cols):
    """Creates an empty schedule table.

    Args:
        nlstart: the start of the schedule, as a naive local datetime.  See
            nld().
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
    return [[(nlstart + i)] + ([None] * n_cols) for i in partitions]
