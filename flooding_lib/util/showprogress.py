# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Intended to be run directly from the command line.

Usage: python showprogress.py <starttime> <nr_done> <nr_total>

Starttime is in seconds since the epoch (output of date +%s).

Calculates percentage done and ETA, and prints them.
"""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sys
import datetime
import time


def main(starttime, nr_done, nr_total):
    current_time = time.time()
    time_elapsed = current_time - starttime

    pct_done = nr_done / nr_total

    if pct_done > 0:
        time_to_go = (time_elapsed / pct_done) * (1 - pct_done)

        eta = datetime.datetime.now() + datetime.timedelta(seconds=time_to_go)
    else:
        eta = "N/A"

    print("{:2.1f}% done, ETA {}.".format(pct_done * 100, eta))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python showprogress.py <starttime> <nr_done> <nr_total>")
        sys.exit(1)

    sys.exit(main(*[float(arg) for arg in sys.argv[1:]]))
