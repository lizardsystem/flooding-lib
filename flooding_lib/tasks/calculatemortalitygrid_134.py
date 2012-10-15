#!/usr/bin/env python
# -*- coding: utf-8 -*-
#* $Id: calculatemortalitygrid_134.py 9979 2010-03-15 08:53:08Z Mario $

__revision__ = "$Rev: 9979 $"[6:-2]

import logging
from django import db
log = logging.getLogger('nens.lizard.kadebreuk.lognormal')


def set_broker_logging_handler(broker_handler=None):
    """
    """
    if broker_handler is not None:
        log.addHandler(broker_handler)
    else:
        log.warning("Broker logging handler does not set.")

from nens.numeric import norm_cdf
import math
from nens.asc import AscGrid

from zipfile import ZipFile, ZIP_DEFLATED
from flooding_lib.models import Scenario, Result, ResultType
from flooding_base.models import Setting
import os


def oolognormdist(x, m, s):
    """same as openoffice LOGNORMDIST
    """
    return norm_cdf((math.log(x) - m) / s)


def combine(w, x, m1, s1, m2, s2, lower, upper):
    """returns oolognormdist(x, m1, s1) if w < lower
    oolognormdist(x, m2, s2) if w > upper
    and a linear interpolation if lower < w < upper

    >>> combine(0.1, 1, 7.6, 2.75, 1.46, 0.28, 0.5, 4.0)# doctest: +ELLIPSIS
    0.00285811...
    >>> combine(0.5, 1, 7.6, 2.75, 1.46, 0.28, 0.5, 4.0)# doctest: +ELLIPSIS
    0.00285811...
    >>> combine(0.9, 1, 7.6, 2.75, 1.46, 0.28, 0.5, 4.0)# doctest: +ELLIPSIS
    0.00253148...
    >>> combine(3.1, 1, 7.6, 2.75, 1.46, 0.28, 0.5, 4.0)# doctest: +ELLIPSIS
    0.00073501...
    >>> combine(4.0, 1, 7.6, 2.75, 1.46, 0.28, 0.5, 4.0)# doctest: +ELLIPSIS
    9.24417...e-08
    >>> combine(4.9, 1, 7.6, 2.75, 1.46, 0.28, 0.5, 4.0)# doctest: +ELLIPSIS
    9.24417...e-08
    >>> combine(4.0, 4.0, 7.6, 2.75, 1.46, 0.28, 0.5, 4.0)# doctest: +ELLIPSIS
    0.396185...
    """
    if not x > 0:
        return 0

    if not w > 0:
        return 0

    if w < upper:
        oolower = oolognormdist(x, m1, s1)
        if w <= lower:
            return oolower
    if w > lower:
        ooupper = oolognormdist(x, m2, s2)
        if w >= upper:
            return ooupper
    fraction = (upper - w) / (upper - lower)

    return fraction * oolower + (1.0 - fraction) * ooupper


def calc_mortality_grid(stijg, depth):

    result = stijg.copy()
    for col in range(len(stijg)):
        for row in range(len(stijg[0])):
            stijg_value = stijg[col][row]
            depth_value = depth[col][row]
            try:
                result[col][row] = combine(
                    stijg_value, depth_value, 7.6, 2.75, 1.46, 0.28, 0.5, 4.0)
            except TypeError:
                result[col][row] = 0
                pass
    return result


def perform_calculation(scenario_id, tmp_location, timeout=0):

    log.debug("step 0a: get settings")
    scenario = Scenario.objects.get(pk=scenario_id)
    destination_dir = Setting.objects.get(key='DESTINATION_DIR').value

    log.debug("step 0c: get temp location: resetting to forward-slash")
    location = tmp_location.replace("\\", "/")
    if not location.endswith("/"):
        location += "/"

    log.debug("0f: restore the files from the database.")
    for resulttype, names in [
        (1, ['dm1maxd0.asc']),
        (19, ['grid_dh.asc', 'Grid_dh.asc']),
        ]:
        try:
            resultloc = scenario.result_set.get(
                resulttype=ResultType.objects.get(pk=resulttype)).resultloc
            input_file = ZipFile(os.path.join(destination_dir, resultloc), "r")

            for name in names:
                try:
                    content = input_file.read(name)
                    temp = file(os.path.join(location + name.lower()), "wb")
                    temp.write(content)
                    temp.close()
                except KeyError:
                    log.debug('file %s not found in archive' % name)
        except Result.DoesNotExist as e:
            log.error('inputfile of resulttype %i not found' % resulttype)
            log.error(','.join(map(str, e.args)))
            return False

    log.debug("step 3: use the fls_h.inc (sequence of water levels) " \
                  "into grid_dh.asc (maximum water raise speed)")

    grid_dh = AscGrid(file(os.path.join(location, 'grid_dh.asc')))
    dm1maxd0 = AscGrid(file(os.path.join(location, 'dm1maxd0.asc')))

    result = AscGrid.apply(calc_mortality_grid, grid_dh, dm1maxd0)

    temp = file(os.path.join(location, 'mortality.asc'), 'wb')
    result.writeToStream(temp)
    temp.close()

    log.debug("step 5: store the output files and the fact that they exist")

    for dirname, filename, zipfilename, resulttype, unit, value in [
        ('.', 'mortality.asc', 'gridmortality.zip', 20, None, None), ]:

        resultloc = os.path.join(scenario.get_rel_destdir(), zipfilename)

        content = file(
            os.path.join(location, dirname, filename), 'rb').read()
        output_file = ZipFile(os.path.join(destination_dir, resultloc),
                              mode="w", compression=ZIP_DEFLATED)
        output_file.writestr(filename, content)
        output_file.close()

        result, new = scenario.result_set.get_or_create(
            resulttype=ResultType.objects.get(pk=resulttype))
        result.resultloc = resultloc
        result.unit = unit
        result.value = value
        result.save()

    log.debug("finish task")
    log.debug("close db connection to avoid an idle process.")
    db.close_connection()
    return True

if __name__ == '__main__':
    import doctest
    doctest.testmod()
