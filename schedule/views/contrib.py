"""Contributed code used by schedule views.

The code collected within this module has been sourced from snippets,
cookbooks etc. under the assumption that it is ok for this code to be
reproduced under the same terms as the URY website codebase.  All
known authors of the code in this module are credited where possible.

"""

from datetime import date, timedelta


## These next two functions were purloined from
## http://stackoverflow.com/q/304256

def iso_year_start(iso_year):
    """The gregorian calendar date of the first day of the given ISO
    year.
    
    """
    fourth_jan = date(iso_year, 1, 4)
    delta = timedelta(fourth_jan.isoweekday()-1)
    return fourth_jan - delta 


def iso_to_gregorian(iso_year, iso_week, iso_day):
    """Gregorian calendar date for the given ISO year, week
    and day.
    
    """
    year_start = iso_year_start(iso_year)
    return year_start + timedelta(
        days=iso_day-1,
        weeks=iso_week-1)
