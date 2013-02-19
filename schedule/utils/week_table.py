"""Classes representing a weekly schedule table.

The weekly schedule table is complicated to construct from the
timeslot ranges it is built up from, and as such these classes and
their constituent functions are quite voluminous.  Any intrepid
coder who can cut away swathes of this module without sacrificing its
functionality is a true hero.

"""

import datetime

from django.utils import timezone

from .. import utils


EMPTY_DELTA = datetime.timedelta(days=0)


# This is a very common timedelta, so we use it as a constant.
DAY = datetime.timedelta(days=1)


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
    nlstart = nld(schedule.start)

    data_lists, partitions = split_days(nlstart, schedule.data)

    table = empty_table(nlstart, partitions, len(data_lists))

    return populate_table(table, data_lists)


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
        current_row = 0
        for slot in day:
            # How much local time does this slot take up?
            nlend = nld(slot.end_time())

            # Work out how many rows this slot fits into.
            add_rows = 0
            try:
                while table[current_row + add_rows][SCHEDULE_TIME_COL] < nlend:
                    add_rows += 1
            except IndexError:
                # This usually means this show crosses over the day boundary;
                # this is normal.
                pass

            # If our partitioning is sound, then the slot must fit exactly into
            # one or more rows.
            if table[current_row + add_rows][SCHEDULE_TIME_COL] >= nlend:
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
    partitions = set()

    day_start = data[0].start_date

    for slot in data:
        # This is a while so it deals properly with the case of shows
        # straddling multiple days; each day will be populated in turn.
        while utils.range.dst_add(day_start, DAY) >= slot.start_date:
            day, current_list = rotate_day(day_start, done_day_lists, day_list)
            # Make sure that day boundaries are marked as partitions too
            partitions.add(nld(day))

        current_list.append(slot)
        partitions.add(nld(slot.start_time) - nlstart)

    # Finish off by pushing the last day onto the list, as nothing else will
    done_day_lists.append(day_list)
    return done_day_lists, partitions


def rotate_day(day_start, day_list, done_day_lists):
    """Ends the current day and sets things up ready to process the next day.

    Args:
        day_start: the (aware) datetime of the start of the day that is about
            to finish
        day_list: the completed list of timeslots for the day being finished.
        done_day_lists: the list of completed day lists (in chronological
            order) to push the new day onto
    Returns:
        a tuple containing the new day start and the new day list, which may or
        may not be empty depending on show day crossover.
    """
    # We should NEVER be storing an empty list, as every day should at least
    # have one show (the filler show).
    if not day_list:
        raise utils.exceptions.ScheduleInconsistencyError(
            'split_days encountered empty day list, is filler working?'
        )

    done_day_lists.append(day_list)

    # We need to see if the last show we processed straddles the boundary
    # between the two days and, if so, make sure it appears at the start of the
    # new list too.
    last_show = done_day_lists[-1][-1]
    new_list = [last_show] if last_show.end_time().date() > day_start else []

    return utils.range.dst_add(day_start, DAY), new_list


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
        time of their occurrence, their offset from nlstart, and then num_cols
        instances of None ready to be filled with schedule data.
    """
    return [[(nlstart + i).time()] + ([None] * n_cols) for i in partitions]
