"""Functions for working with naive local times.

The schedule is heavily based on local time interpretations of dates, so we
have a lot of functions for working with them in (hopefully) a DST-tolerant
manner.

TODO: test these?
"""

from django.utils import timezone


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
