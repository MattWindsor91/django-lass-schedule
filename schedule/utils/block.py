"""Functions for annotating schedules (lists of timeslots) with their schedule
blocks in bulk.

The block system is arranged in this way (whole schedules annotated at once)
primarily for efficiency (no need to run queries for each timeslot).
"""

from django.conf import settings
from django.utils import timezone

from .. import models
from . import nltime


DAY = timezone.timedelta(days=1)


def annotate(slotlist):
    """Annotates a list of timeslots with their schedule blocks.

    This injects a new field 'block' into each timeslot that contains its
    associated Block object.

    Args:
        slotlist: a list of timeslots

    Returns:
        the same list of timeslots wherein each timeslot has a new attribute,
        'block', that contains the Block the timeslot is matched to.

    """
    blocks = {b.id: b for b in models.Block.objects.all()}
    prepared_hooks = [hook() for hook in HOOKS]

    return [annotate_slot(slot, blocks, prepared_hooks) for slot in slotlist]


def annotate_slot(slot, blocks, hooks):
    """Annotates a timeslot with its block."""
    for hook in hooks:
        match = hook(slot)
        if match:
            slot.block = blocks[match]
            break
    return slot


def hook_range():
    """Block matching hook that matches a timeslot if its start time is within
    the rule's defined range.
    """
    rules = models.BlockRangeRule.objects.values(
        'block', 'start_time', 'end_time'
    ).order_by('start_time')

    def h(ts):
        match = False
        for rule in rules:
            # Due to possibly matching over day boundaries, we have to check to
            # see if we match ranges by projecting the slot start delta
            # forwards a day too.
            # If anyone can think of a clearer way of doing this, change
            # please.
            dtime = delta(ts.start_time)
            for slot_time in [dtime, dtime + DAY]:
                if rule['start_time'] <= slot_time < rule['end_time']:
                    match = rule['block']
                    break
            if match:
                break
        return match

    return h


def hook_show():
    """Block matching hook that matches a timeslot if there is an explicit rule
    binding the timeslot's show to a block.
    """
    rules = models.BlockShowRule.objects.values('block', 'show')

    def h(ts):
        match = False
        for rule in rules:
            if rule['show'] == ts.season.show.pk:
                match = rule['block']
                break
        return match

    return h


def hook_default():
    """Block matching hook that matches any block to the default block."""
    return lambda _: getattr(settings, 'DEFAULT_SHOW_BLOCK', 2)

# List of hooks: delayed computation style functions that compute and return
# functions to apply, in turn, to a timeslot to attempt to determine its block.
# Returns a primary key if a block match was made, or False if not.
# Each is run in turn, in the order given here, until a primary key is found.
HOOKS = [
    hook_show,
    hook_range,
    hook_default,
]


###############################################################################
# Utilities

def delta(date):
    """Converts a datetime into a timedelta of seconds elapsed since
    midnight local time.

    Args:
        date: the datetime whose time is to be converted.

    Returns:
        a timedelta measuring the time difference between midnight and date.
    """
    midnight = date.replace(hour=0, minute=0, second=0, microsecond=0)
    return nltime.nldiff(date, midnight)
