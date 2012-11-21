"""
Calculate scenario statistics:
- Total inundated area
- Total water volume
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
import nens.asc
import scipy

from flooding_base import models as basemodels
from flooding_lib import models
from flooding_lib.util import files
from flooding_lib.util import flshinc

logger = logging.getLogger(__name__)


def result_zip(scenario, resulttype_id):
    destination_dir = basemodels.Setting.objects.get(
        key='DESTINATION_DIR').value
    destination_dir = destination_dir.replace('\\', '/')
    resultloc = scenario.result_set.get(
        resulttype__id=resulttype_id).resultloc
    return os.path.join(destination_dir, resultloc)


def get_masked_array(dataset):
    arr = dataset.ReadAsArray()
    ndv = dataset.GetRasterBand(1).GetNoDataValue()
    masked_array = ma.array(arr, mask=(arr == ndv))
    return masked_array


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


def calculate_statistics(scenario_id):
    scenario = models.Scenario.objects.get(pk=scenario_id)

    # We need the max water depth .asc file, which is in the results
    # of resulttype 1.
    masked_array = None
    with files.temporarily_unzipped(result_zip(scenario, 1)) as names:
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


def to_color_tuple(colorcode):
    return (
        int(colorcode[0:2], 16),
        int(colorcode[2:4], 16),
        int(colorcode[4:6], 16),
        0
        )


def get_color_mapping():
    source_dir = basemodels.Setting.objects.get(key='SOURCE_DIR').value
    cm_location = os.path.join(source_dir, "colormappings")
    color_mapping_name = 'mapping_d.csv'

    cm_path = '/home/remcogerlich/src/git/flooding/mapping_d.csv'

    mapping = []
    for line in file(cm_path):
        if line.startswith('leftbound'):
            continue
        leftbound, colorcode = line.strip().split(',')
        leftbound = float(leftbound)
        color_tuple = to_color_tuple(colorcode)
        mapping.append((leftbound, color_tuple))

    return mapping


def test_new_flshinc():
    flsh_path = (
        ('/p-flod-fs-00-d1.external-nens.local/flod-share/Flooding/'
         'resultaten/Dijkring 09 - Vollenhove/13042/fls_h.inc.zip')
        .encode('utf8'))

    flsh = flshinc.Flsh(flsh_path, one_per_hour=True)
    geo_transform = flsh.geo_transform()

    for i, (timestamp, grid) in enumerate(flsh):
        flshinc.save_grid_to_image(
            grid,
            'tmp/flsh%04d.png' % int(i),
            flsh.get_classes(),
            get_color_mapping(),
            geo_transform)
