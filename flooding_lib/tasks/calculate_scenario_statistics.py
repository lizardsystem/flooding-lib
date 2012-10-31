"""
Calculate scenario statistics:
- Total inundated area
- Total water volume

For the max water depth situation, and also go through the fls_h.inc
file and calculate the same for each hour (stored as JSON).
"""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from osgeo import gdal
import json
import logging
import numpy
import numpy.ma as ma
import os

from flooding_base import models as basemodels
from flooding_lib import models
from flooding_lib.util import files
from flooding_lib.util import flshinc

logger = logging.getLogger(__name__)

MAX_WATER_DEPTH_RESULT_ID = 1
WATERDEPTH_ANIM_IMPORT_RESULT_ID = 18
WATERDEPTH_ANIM_SOBEK_RESULT_ID = 15


def result_zip(scenario, resulttype_id):
    destination_dir = basemodels.Setting.objects.get(
        key='DESTINATION_DIR').value
    destination_dir = destination_dir.replace('\\', '/')
    result = scenario.result_set.get(resulttype__id=resulttype_id)
    resultloc = result.resultloc
    result_zip = os.path.join(destination_dir, resultloc)

    return result_zip


def get_masked_array(dataset):
    arr = dataset.ReadAsArray()
    ndv = dataset.GetRasterBand(1).GetNoDataValue()
    masked_array = ma.array(arr, mask=(arr == ndv))
    return masked_array


def calculate_statistics(scenario_id):
    scenario = models.Scenario.objects.get(pk=scenario_id)

    inundation_based_on_max_depth(scenario)
    inundation_based_on_flsh(scenario)


def calculate_inundation_and_area(masked_array, cellsize):
    # If we assume that the asc's projection is RD, then the absolute
    # PixelSize gives the width of a pixel in m
    cellsize_in_m2 = cellsize * cellsize

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

    return (total_inundation_volume, total_inundated_area)


def inundation_based_on_max_depth(scenario):
    # We need the max water depth .asc file, which is in the results
    # of resulttype 1.
    masked_array = None
    with files.temporarily_unzipped(
        result_zip(scenario, MAX_WATER_DEPTH_RESULT_ID)) as names:
        for name in names:
            if os.path.basename(name) == b'dm1maxd0.asc':
                dataset = gdal.Open(name.encode('utf8'))
                # Read the data into a masked array
                masked_array = get_masked_array(dataset)
                geo_transform = dataset.GetGeoTransform()
                del dataset  # This closes the file, so that the
                             # directory can be deleted in Windows
                break
        else:
            raise AssertionError(
               "Zip file for resulttype 1 ({0}) didn't include a dm1maxd0.asc."
                .format(result_zip(scenario, 1)))

    total_inundation_volume, total_inundated_area = (
        calculate_inundation_and_area(masked_array, geo_transform[1]))

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


def inundation_based_on_flsh(scenario):
    for result_type_id in (
        WATERDEPTH_ANIM_IMPORT_RESULT_ID,
        WATERDEPTH_ANIM_SOBEK_RESULT_ID):
        if scenario.result_set.filter(resulttype__id=result_type_id).exists():
            use_result_type_id = result_type_id
            break
        else:
            raise AssertionError("Neither resulttype for fls_h.inc found!")

    with files.temporarily_unzipped(
        result_zip(scenario, use_result_type_id)) as names:
        for name in names:
            if os.path.basename(name) == 'fls_h.inc':
                j = process_flsh(name)
                save_inundation_json(scenario, j)
                break


def process_flsh(flsh_path):
    flsh = flshinc.Flsh(flsh_path, one_per_hour=True)
    geo_transform = flsh.geo_transform()

    calculated_inundations = []

    for timestamp, grid in flsh:
        total_inundation_volume, total_inundated_area = (
            calculate_inundation_and_area(
                grid, geo_transform[1]))
        calculated_inundations.append({
            'timestamp': timestamp,
            'inundation_volume': total_inundation_volume,
            'inundated_area': total_inundated_area
            })

    return json.dumps(calculated_inundations)


def save_inundation_json(scenario, j):
    resultloc = os.path.join(
        scenario.get_rel_destdir(),
        'inundation_statistics.json')

    destination = os.path.join(
        basemodels.Setting.objects.get(
            key='DESTINATION_DIR').value.replace('\\', '/'),
        resultloc)

    f = file(destination, 'w')
    f.write(j)
    f.close()

    # Save values in Results for this scenario
    resulttype = models.ResultType.objects.get(
        shortname_dutch="inundatie per uur")

    try:
        result = models.Result.objects.get(
            scenario=scenario, resulttype=resulttype)
    except models.Result.DoesNotExist:
        result = models.Result(
            scenario=scenario, resulttype=resulttype)

    result.resultloc = resultloc
    result.save()

