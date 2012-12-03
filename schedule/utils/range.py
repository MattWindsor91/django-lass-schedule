"""A class representing a contiguous, linear chunk of programming,
and also containing various methods for extracting said chunks from
the schedule.

"""

from schedule.models import Timeslot
from schedule.utils import filler
from datetime import timedelta
from django.utils import timezone
from metadata.utils.date_range import in_range


def dst_add_days(start_date, num_days):
    """
    Given an aware date, calculates the same (local) time `num_days`
    days in the future.

    Note that this may not actually be exactly `num_days` days later
    """
    if timezone.is_naive(start_date):
        return start_date + timedelta(days=num_days)
        # Can't do anything to a naive datetime
    else:
        # What we do is we strip out the timezone information from
        # the start date to turn it into a naive date, add the days
        # onto it, and then re-interpret it as a date in whatever the
        # original timezone works out to be in the result.  This has
        # the nice quality of shifting the date into the correct
        # local time when DST changes between the two dates.
        #
        # If anyone can find a less hacky way of doing this,
        # PLEASE replace it.  It makes me cry just thinking about it.
        return timezone.make_aware(
            (
                timezone.make_naive(start_date, start_date.tzinfo)
                + timedelta(days=num_days)
            ),
            start_date.tzinfo
        )


class ScheduleRange(object):
    """Class of the result of timeslots-in-range queries.

    Range is a thin wrapper around a QuerySet containing
    timeslot results that includes information about the start
    of the range, the end of the range, and which parameters were
    used in the making of the range.

    """
    def __init__(self,
                 data,
                 start,
                 end,
                 exclude_before_start=False,
                 exclude_after_end=False,
                 exclude_subsuming=False,
                 with_jukebox_entries=True):
        self.data = data
        self.start = start
        self.end = end
        self.timespan = end - start
        self.exclude_before_start = exclude_before_start
        self.exclude_after_end = exclude_after_end
        self.exclude_subsuming = exclude_subsuming
        self.with_jukebox_entries = with_jukebox_entries

    def __repr__(self):
        """Returns a debug representation of the range."""
        return self.data.__repr__()

    def __getattr__(self, attr):
        """Ensures that any attempts to get an attribute that isn't
        in the Range class are sent to the data object it wraps.

        """
        return self.data.__getattr__(attr)

    @classmethod
    def between(cls,
                start,
                end,
                exclude_before_start=False,
                exclude_after_end=False,
                exclude_subsuming=False,
                with_filler_timeslots=True,
                exclude_non_public=True):
        """
        Returns all the timeslots within a range defined by two
        datetime objects.

        Keyword arguments:
        start -- the start of the range, as a datetime
        end -- the end of the range, as a datetime
        exclude_before_start -- if True, the list will exclude all
            shows that start before the range, but end within it
            (default: False)
        exclude_after_end -- if True, the list will exclude all shows
            that start within the range, but end after it
            (default: False)
        exclude_subsuming -- if True, the list will exclude all shows
            that start before, but end after, the range (that is,
            they "subsume" the range)
            (default: False)
        with_filler_timeslots -- if True, gaps within the range will be
            filled with references to the filler pseudo-show
            (default: True)
        exclude_non_public -- if True, only public shows will be
            added to the range
            (default: True)

        """
        timeslots = in_range(
            Timeslot,
            start,
            end,
            None,
            exclude_before_start,
            exclude_after_end,
            exclude_subsuming).order_by('start_time')

        if exclude_non_public:
            timeslots = timeslots.exclude(
                season__show__show_type__public=False
            )

        if with_filler_timeslots:
            # Can't do add_filler_timeslots if this is a queryset
            # so force it to be a list
            timeslots = filler.fill(
                list(timeslots),
                start,
                end)

        # For all intents and purposes, this is just the queryset
        # with some added metadata on which range it actually
        # represents
        return cls(
            timeslots,
            start,
            end,
            exclude_before_start,
            exclude_after_end,
            exclude_subsuming,
            with_filler_timeslots)

    @classmethod
    def within(cls, date=None, offset=None, **keywords):
        """Lists all schedule timeslots occuring within a given
        duration of the given moment in time.

        That moment defaults to the current time.

        All keyword arguments beyond date (the aforementioned moment
        in time) and offset (the aforementioned time delta) are
        passed to 'timeslots_in_range' unmolested; see that
        function's docstring for details on what the allowed
        arguments are.

        """
        if date is None:
            date = timezone.now()
        if offset is None:  # Default to 0 (eg, get current show)
            offset = timedelta.timedelta(days=0)

        return cls.between(
            date,
            date + offset,
            **keywords)

    @classmethod
    def day(cls, date=None, **keywords):
        """Lists all schedule timeslots occurring between the given
        moment in time and the moment exactly one day after it.

        All keyword arguments beyond date (the aforementioned moment
        in time) are passed to 'timeslots_in_offset' unmolested; see
        that function's docstring for details on what the allowed
        arguments are.

        'date' defaults to the current moment in time.

        """
        return cls.within(
            date,
            timedelta(days=1),
            **keywords)

    @classmethod
    def week(cls,
             date=None,
             split_days=False,
             dst_compensate=True,
             **keywords):
        """Lists all schedule timeslots occurring between the given
        moment in time and the moment exactly one week after it.

        All keyword arguments beyond date (the aforementioned moment
        in time) and split_days are passed to 'timeslots_in_offset'
        unmolested; see that function's docstring for details on what
        the allowed arguments are.

        If 'split_days' is True, the result will be equivalent to
        listing the result of 'timeslots_in_day' applied to each day
        of the week with the given arguments; otherwise the result
        will be 'timeslots_in_offset' where the offset is one week.

        If 'dst_compensate' is True and 'split_days' is True, the
        start time will be adjusted to compensate for changes in DST
        through the week; that is, the actual start time will be
        shifted to match any UTC offset changes during the week.

        'date' defaults to the current moment in time.

        """
        add_days = (
            lambda x: dst_add_days(date, x)
            if dst_compensate
            else lambda x: date + timedelta(days=x)
        )

        if split_days:
            result = [
                cls.day(
                    add_days(day),
                    **keywords
                ) for day in xrange(0, 7)
            ]
        else:
            result = cls.within(
                date,
                timedelta(weeks=1),
                **keywords)
        return result
