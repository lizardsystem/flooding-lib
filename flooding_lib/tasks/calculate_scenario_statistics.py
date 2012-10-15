"""
Calculate scenario statistics:
- Total inundated area
- Total water volume
"""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from osgeo import gdal
import logging
import numpy
import numpy.ma as ma
import os

from flooding_base import models as basemodels
from flooding_lib import models
from flooding_lib.util import files

logger = logging.getLogger(__name__)


def result_zip(scenario, resulttype_id):
    destination_dir = basemodels.Setting.objects.get(
        key='DESTINATION_DIR').value
    destination_dir = destination_dir.replace('\\', '/')
    resultloc = scenario.result_set.get(
        resulttype__id=resulttype_id).resultloc
    return os.path.join(destination_dir, resultloc)


def calculate_statistics(scenario_id):
    scenario = models.Scenario.objects.get(pk=scenario_id)

    # We need the max water depth .asc file, which is in the results
    # of resulttype 1.
    arr = None
    with files.temporarily_unzipped(result_zip(scenario, 1)) as names:
        for name in names:
            if os.path.basename(name) == 'dm1maxd0.asc':
                dataset = gdal.Open(name)
                # Read the data into a masked array
                arr = dataset.ReadAsArray()
                ndv = dataset.GetRasterBand(1).GetNoDataValue()
                masked_array = ma.array(arr, mask=(arr == ndv))
                geo_transform = dataset.GetGeoTransform()
                del dataset  # This closes the file, so that the
                             # directory can be deleted in Windows
                break

    if arr is None:
        raise AssertionError(
            "Zip file for resulttype 1 didn't include a dm1maxd0.asc.")

    # If we assume that the asc's projection is RD, then the absolute
    # PixelSize gives the width of a pixel in m
    widthx = abs(geo_transform[1])
    widthy = abs(geo_transform[5])
    cellsize_in_m2 = widthx * widthy

    # We assume some things, probably need to check for them, namely
    # that the projection is RD and that pixels are aligned with the
    # projection (geo_transform[2] and [4] are 0)

    # Inundated area is the number of cells that have a max depth > 0,
    # multiplied by each cell's area
    total_inundated_area = (
        numpy.greater(masked_array, 0).sum() * cellsize_in_m2)

    # Total volume is the total depth of all cells multiplied by the area
    # of one cell
    total_inundation_volume = (
        masked_array.sum() * cellsize_in_m2)

    # Save values in Results for this scenario
    resulttype_inundated_area = models.ResultType.objects.get(
        shortname_dutch="overstroomd gebied")
    resulttype_inundation_volume = models.ResultType.objects.get(
        shortname_dutch="inundatievolume")

    for resulttype, value in (
        (resulttype_inundated_area, total_inundated_area),
        (resulttype_inundation_volume, total_inundation_volume)):
        try:
            result = models.Result.objects.get(
                scenario=scenario, resulttype=resulttype)
        except models.Result.DoesNotExist:
            result = models.Result(
                scenario=scenario, resulttype=resulttype)

        result.value = value
        result.resultloc = 'dm1maxd0.asc'
        result.unit = resulttype.unit
        result.save()
