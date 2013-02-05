"""
Exceptions that the schedule system can throw.

"""


# Prefab message templates
MSG_NO_TERM_WHILE_FILLING = (
    "Schedule inconsistency: Attempting to fill a schedule gap "
    "starting at {time}, but there is no term on or before that "
    "time.  This generally means that the schedule filler is being "
    "asked to fill a gap that starts before any terms are defined, "
    "which could mean your term database is insufficiently populated "
    "or you have a show somewhere it shouldn't be."
)


class ScheduleInconsistencyError(Exception):
    """
    Exception thrown when the schedule system detects an internal
    inconsistency.

    """
    pass
