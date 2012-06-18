"""A place to collect common functions for manipulating dates within
Flooding"""

import math
import re


def get_intervalstring_from_dayfloat(dayfloat):
    """Given a number of days as a float, return a string of the form
    "x d hh:mm", with x the number of days, hh the number of hours, mm
    the number of minutes."""

    days = int(math.floor(dayfloat))
    hoursfloat = (dayfloat - days) * 24
    hours = int(math.floor(hoursfloat))
    minutesfloat = (hoursfloat - hours) * 60
    minutes = int(math.floor(minutesfloat))

    return "%d d %02d:%02d" % (days, hours, minutes)


def get_dayfloat_from_intervalstring(intervalstring):
    """Return a time interval of a string with days, hours and minutes
    as a float amount of days.

    Input format is 'x d hh:mm', with the 'd', spaces and leading
    zeros optional."""

    intervalstring = str(intervalstring)
    match = (re.compile('(-?\d+)\s*d?\s*(\d{1,2}):(\d{1,2})').
             match(intervalstring))

    if match:
        try:
            day = float(match.group(1))
            hours = float(match.group(2))
            minutes = float(match.group(3))

            if (0 <= hours < 24) and (0 <= minutes < 60):
                return day + hours / 24 + minutes / (60 * 24)
        except ValueError:
            pass

    raise ValueError(
        "Interval input format is 'x d hh:mm'. Error on input '%s'" %
        input)
