from __future__ import unicode_literals

import os
import stat
import sys

import numpy as np
from osgeo import gdal

from django.conf import settings
from django import db

from flooding_base.models import Setting
from flooding_lib import models
from flooding_lib.models import Scenario
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.tools.pyramids import models as pyramidmodels
from flooding_lib.tasks import calculate_export_maps
from flooding_lib.util import files
from flooding_lib.util import flshinc

import logging
logger = logging.getLogger(__name__)

INPUTFIELD_STARTMOMENT_BREACHGROWTH_ID = 9

__revision__ = "1.0"  # perform_task wants this


def gdal_open(f):
    if isinstance(f, unicode):
        f = f.encode('utf8')
    try:
        dataset = gdal.Open(f)
    except RuntimeError:
        dataset = None
    return dataset


def set_broker_logging_handler(broker_handler=None):
    """
    """
    if broker_handler is not None:
        logger.addHandler(broker_handler)
    else:
        logger.warning("Broker logging handler does not set.")

SOBEK_PROGRAM_ID = 1
HISSSM_PROGRAM_ID = 2
IMPORT_PROGRAM_ID = 3

GDAL_MEM_DRIVER = gdal.GetDriverByName(b'mem')
GDAL_TIFF_DRIVER = gdal.GetDriverByName(b'gtiff')

if __name__ == '__main__':
    sys.path.append('..')

    from django.core.management import setup_environ
    import lizard.settings
    setup_environ(lizard.settings)


def common_generation(scenario_id, source_programs, tmp_dir):
    """
    loop on all results computed for the given scenario_id, unpack
    them into a temporary directory, save as a pyramid, set in the
    results record.
    """

    scenario = Scenario.objects.get(pk=scenario_id)

    maxwaterdepth_geotransform = (
        calculate_export_maps.maxwaterdepth_geotransform(scenario))

    logger.debug("select results relative to scenario %s" % scenario_id)

    # The Generation for some results creates new results. In
    # particular, creating animations for max water depth generates
    # results for arrival time maps. So first we generate the results
    # that generate others, then the rest.

    all_results = (
        scenario.result_set.filter(
            resulttype__program__in=source_programs,
            resulttype__color_mapping_name__isnull=False)
        .exclude(resulttype__color_mapping_name=""))

    generate_for_result_queryset(
        scenario, all_results.filter(
            resulttype__use_to_compute_arrival_times=True),
        tmp_dir, maxwaterdepth_geotransform)

    generate_for_result_queryset(
        scenario, all_results.filter(
            resulttype__use_to_compute_arrival_times=False),
        tmp_dir, maxwaterdepth_geotransform)

    return True


def standalone_generation_for_result(result):
    """Call this function from scripts and so on."""
    scenario = result.scenario
    maxwaterdepth_geotransform = (
        calculate_export_maps.maxwaterdepth_geotransform(scenario))
    results_dir = (
        Setting.objects.get(key='DESTINATION_DIR').value.replace('\\', '/'))
    # Destination dir -- same as the old PNGs were saved to
    destination_dir = (
        Setting.objects.get(key='DESTINATION_DIR').value.replace('\\', '/'))
    base_output_dir = os.path.join(destination_dir, scenario.get_rel_destdir())
    base_output_dir = base_output_dir.encode('utf8')  # Gdal wants byte strings

    return generate_for_result(
        result, results_dir, base_output_dir, settings.TMP_DIR,
        maxwaterdepth_geotransform)


def generate_for_result_queryset(
    scenario, results, tmp_dir, maxwaterdepth_geotransform):

    results = list(results)

    logger.debug("selected results for scenario: %s" % str(results))

    logger.debug("starting the loop on all previously computed results")
    results_dir = (
        Setting.objects.get(key='DESTINATION_DIR').value.replace('\\', '/'))

    # Destination dir -- same as the old PNGs were saved to
    destination_dir = (
        Setting.objects.get(key='DESTINATION_DIR').value.replace('\\', '/'))
    base_output_dir = os.path.join(destination_dir, scenario.get_rel_destdir())
    base_output_dir = base_output_dir.encode('utf8')  # Gdal wants byte strings

    for result in results:
        generate_for_result(result, results_dir, base_output_dir, tmp_dir,
                            maxwaterdepth_geotransform)


def generate_for_result(result, results_dir, base_output_dir, tmp_dir,
                        maxwaterdepth_geotransform):
    logger.debug("examining results record: '%s'" % str(result))
    output_dir = os.path.join(base_output_dir, result.resulttype.name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    result_location = os.path.join(
        results_dir, result.resultloc.replace('\\', '/'))
    logger.debug("Result location: " + result_location)

    # Check for empty result file
    if not os.path.exists(result_location):
        logger.warning("input file '%s' missing" % result_location)
        return

    if os.stat(result_location)[stat.ST_SIZE] == 0:
        logger.warning("input file '%s' is empty" % result.resultloc)
        return

    result_to_correct_gridta = (
        result if result.resulttype.name == 'gridta'
        else None)

    if result_location.endswith('.zip'):
        # Unpack zip file
        with files.temporarily_unzipped(
            result_location, rezip=False, tmp_dir=tmp_dir) as unzipped:
            pyramid_or_animation = compute_pyramids(
                result, unzipped, result_to_correct_gridta, output_dir,
                maxwaterdepth_geotransform)
    else:
        # Just use the file itself
        pyramid_or_animation = compute_pyramids(
            result, [result_location], result_to_correct_gridta,
            output_dir, maxwaterdepth_geotransform)

    if hasattr(pyramid_or_animation, 'frames'):
        if result.animation:
            result.animation.delete()  # Delete the old object
            # Doesn't delete the old files, they're already overwritten
        result.animation = pyramid_or_animation
    else:
        if result.raster:
            # Delete the old one (and its pyramid!)
            logger.debug("Deleting old pyramid")
            result.raster.delete()
        result.raster = pyramid_or_animation

    result.save()


def compute_pyramids(
    result, input_files, result_to_correct_gridta, output_dir,
    maxwaterdepth_geotransform):
    # If we have an inc file, use that
    inc_file = next(
        (i for i in input_files if i.lower().endswith('.inc')), None)

    # arrival times computability
    arrival_compatible_result = result.resulttype.use_to_compute_arrival_times
    is_not_3di_scenario = result.scenario.modeller_software() != '3di'
    compute_arrival_times = arrival_compatible_result and is_not_3di_scenario

    # For arrival times
    startmoment_breachgrowth_inputfield = InputField.objects.get(
        pk=INPUTFIELD_STARTMOMENT_BREACHGROWTH_ID)
    startmoment_days = result.scenario.value_for_inputfield(
            startmoment_breachgrowth_inputfield)
    startmoment_hours = int(startmoment_days * 24 + 0.5)

    if inc_file:
        # amount, basename = generate_from_inc(inc_file)
        animation = animation_from_inc(
            inc_file, output_dir, maxwaterdepth_geotransform,
            compute_arrival_times, startmoment_hours)
        if compute_arrival_times:
            generate_arrival_times_results(result.scenario, output_dir)
        return animation
    elif len(input_files) == 1:
        return pyramid_from_single_asc(
            input_files[0], result_to_correct_gridta)
    else:
        animation = animation_from_ascs(
            input_files, output_dir,
            compute_arrival_times, startmoment_hours)
        if compute_arrival_times:
            generate_arrival_times_results(result.scenario, output_dir)
        return animation


def generate_arrival_times_results(scenario, output_dir):
    # Destination dir -- same as the old PNGs were saved to
    destination_dir = (
        Setting.objects.get(key='DESTINATION_DIR').value.replace('\\', '/'))

    names = [
        f for f in (
            'computed_arrival_time',
            'computed_difference',
            'computed_time_of_max')
        if os.path.exists(os.path.join(output_dir, '{}.tiff'.format(f)))]

    if output_dir.startswith(destination_dir):
        if not destination_dir.endswith('/'):
            destination_dir += '/'

        output_dir = output_dir[len(destination_dir):]

    for name in names:
        try:
            resulttype = models.ResultType.objects.get(name=name)
        except models.ResultType.DoesNotExist:
            continue

        try:
            newresult = models.Result.objects.get(
                scenario=scenario,
                resulttype=resulttype)
        except models.Result.DoesNotExist:
            newresult = models.Result(
                scenario=scenario,
                resulttype=resulttype)

        newresult.resultloc = os.path.join(
            output_dir, '{}.tiff'.format(name))
        newresult.unit = resulttype.unit
        newresult.save()


def save_to_tiff(filepath, grid, geotransform):
    rows, cols = grid.shape
    if isinstance(filepath, unicode):
        filepath = filepath.encode('utf8')
    dataset = GDAL_TIFF_DRIVER.Create(
        filepath,
        cols, rows, 1, gdal.GDT_Float64, [
            'BIGTIFF=YES', 'TILED=YES', 'SPARSE_OK=YES',
            'COMPRESS=DEFLATE'])
    dataset.SetGeoTransform(geotransform)
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(0.0)
    band.WriteArray(grid)


def animation_from_inc(inc_file, output_dir, maxwaterdepth_geotransform,
                       use_to_compute_arrival_times, startmoment_hours):
    """Save each grid as a geotiff dataset so that images can be
    quickly created on the fly from it."""
    fls = flshinc.Flsh(
        inc_file, one_per_hour=True, mutate=False,
        helper_geotransform=maxwaterdepth_geotransform)
    logger.debug("Generating animation from {}".format(inc_file))

    geotransform = fls.geo_transform()

    maxvalue = None

    gridta_gridtd_recorder = GridtaGridtdRecorder(
        output_dir, geotransform, startmoment_hours)

    for i, (timestamp, array) in enumerate(fls):
        filename = b'dataset{:04d}.tiff'.format(i)
        filepath = os.path.join(output_dir, filename)
        logger.debug("Writing {}.".format(filepath))
        if i == 0:
            maxvalue = np.amax(array)
        else:
            maxvalue = max(maxvalue, np.amax(array))

        gridta_gridtd_recorder.register(i, array)

        save_to_tiff(filepath, array, geotransform)

    rows, cols = array.shape

    animation = pyramidmodels.Animation.objects.create(
        frames=i + 1, cols=cols, rows=rows,
        geotransform={'geotransform': geotransform},
        basedir=output_dir,
        maxvalue=maxvalue)

    if use_to_compute_arrival_times:
        gridta_gridtd_recorder.save()

    return animation


def animation_from_ascs(
    input_files, output_dir, use_to_compute_arrival_times,
    startmoment_hours):
    logger.debug("Animation from ascs...")
    maxvalue = None

    gridta_gridtd_recorder = None
    array = None
    for i, input_file in enumerate(input_files):
        filename = b'dataset{:04d}.tiff'.format(i)
        filepath = os.path.join(output_dir, filename)

        logger.debug("- {} -> {}".format(input_file, filepath))

        dataset = gdal_open(input_file)
        if dataset is None:
            continue
        array = dataset.GetRasterBand(1).ReadAsArray()
        if maxvalue is None:
            maxvalue = np.amax(array)
        else:
            maxvalue = max(maxvalue, np.amax(array))
        geotransform = dataset.GetGeoTransform()

        if gridta_gridtd_recorder is None:
            gridta_gridtd_recorder = GridtaGridtdRecorder(
                output_dir, geotransform, startmoment_hours)
        gridta_gridtd_recorder.register(i, array)

        save_to_tiff(
            filepath,
            array,
            geotransform)

    if array is None:
        # No input files
        return None

    rows, cols = array.shape
    animation = pyramidmodels.Animation.objects.create(
        frames=i + 1, cols=cols, rows=rows,
        geotransform={'geotransform': geotransform},
        basedir=output_dir,
        maxvalue=maxvalue)

    if use_to_compute_arrival_times:
        gridta_gridtd_recorder.save()

    return animation


def pyramid_from_single_asc(input_file, result_to_correct_gridta):
    logger.debug("Pyramid from {}".format(input_file))
    dataset = gdal_open(input_file)
    if dataset is not None:
        pyramid = pyramidmodels.Raster.objects.create()

        # Correct some things
        fixed_dataset = GDAL_MEM_DRIVER.CreateCopy(b'', dataset)
        band = fixed_dataset.GetRasterBand(1)
        grid = band.ReadAsArray()

        if result_to_correct_gridta is not None:
            correct_gridta(grid, result_to_correct_gridta)

        # Make all values below the LIMIT NoData
        grid[grid < pyramidmodels.LIMIT] = 0.0

        if len(np.flatnonzero(grid)) == 0:
            return  # No nodata values

        band.SetNoDataValue(0.0)
        band.WriteArray(grid)

        pyramid.add(fixed_dataset)
        return pyramid


def correct_gridta(grid, result):
    """Wavefront grids (gridta) count the hours from t = 0. However,
    in many scenarios the actual wave only starts much later. We need
    to subtract the breach's start time, which is stored in the
    'Startmoment bresgroei' inputfield of the scenario."""
    startmoment_breachgrowth_inputfield = InputField.objects.get(
        pk=INPUTFIELD_STARTMOMENT_BREACHGROWTH_ID)
    startmoment_days = result.scenario.value_for_inputfield(
        startmoment_breachgrowth_inputfield)
    startmoment_hours = int(startmoment_days * 24 + 0.5)

    # Subtract 'startmoment_hours' from every number in the
    # grid that is higher than it
    if startmoment_hours > 0:
        where = (startmoment_hours <= grid)
        grid -= where * startmoment_hours  # Use fact that True == 1


def sobek(scenario_id, tmp_dir):
    success = common_generation(
        scenario_id, [SOBEK_PROGRAM_ID, IMPORT_PROGRAM_ID], tmp_dir)
    logger.debug("Finish task.")
    logger.debug("close db connection to avoid an idle process.")
    db.close_connection()
    return success


def his_ssm(scenario_id, tmp_dir):
    success = common_generation(scenario_id, [HISSSM_PROGRAM_ID], tmp_dir)
    logger.debug("Finish task.")
    logger.debug("close db connection to avoid an idle process.")
    db.close_connection()
    return success


class GridtaGridtdRecorder(object):
    def __init__(self, output_dir, geotransform, startmoment_hours):
        # If they don't exist yet, we also create a
        # 'computed_arrival_time.tiff' and 'computed_time_of_max.tiff'

        self.output_dir = output_dir
        self.geotransform = geotransform
        self.startmoment_hours = startmoment_hours

        self.arrival_time = None
        self.time_of_max = None
        self.max_seen = None
        self.first_moment_15m = None
        self.max_timestep = 0

    def register(self, timestep, grid):
        # Grid is an array of values. Wherever it is greater than 0.01,
        # we record its value.

        timestep += 1  # 1-based, so that 0 is no data

        self.max_timestep = timestep

        if self.arrival_time is None:
            self.arrival_time = np.zeros(grid.shape, dtype=np.uint)
            self.time_of_max = np.zeros(grid.shape, dtype=np.uint)
            self.max_seen = np.zeros(grid.shape, dtype=np.float)
            self.first_moment_15m = np.zeros(grid.shape, dtype=np.float)

        copy = grid.copy()
        copy[grid < 0.01] = 0

        where_greater_than_max = copy > self.max_seen
        self.max_seen[where_greater_than_max] = copy[where_greater_than_max]
        self.time_of_max[where_greater_than_max] = timestep

        self.first_moment_15m[
            (self.first_moment_15m == 0) & (copy >= 1.5)] = timestep

        where_arrival = (copy > 0) & (self.arrival_time == 0)
        self.arrival_time[where_arrival] = timestep

    def save(self):
        # Fix grids

        difference = self.time_of_max - self.arrival_time

        logger.debug("Saving")
        logger.debug("Startmoment_hours = {}".format(self.startmoment_hours))

        # From the absolute times, we need to subtract 1 (artificially added
        # in register(), and the start moment of the breach growth. All values
        # under that number was be 0.
        subtract = 1 + self.startmoment_hours
        self.arrival_time[self.arrival_time <= subtract] = 0
        self.arrival_time[self.arrival_time > subtract] -= subtract
        self.time_of_max[self.time_of_max <= subtract] = 0
        self.time_of_max[self.time_of_max > subtract] -= subtract
        self.first_moment_15m[self.first_moment_15m <= subtract] = 0
        self.first_moment_15m[self.first_moment_15m > subtract] -= subtract

        # The arrival time grid functions as a mask -- where it has no data,
        # the other grids must have no data either.
        difference[self.arrival_time == 0] = 0
        self.time_of_max[self.arrival_time == 0] = 0

        save_to_tiff(
            os.path.join(self.output_dir, 'computed_arrival_time.tiff'),
            self.arrival_time, self.geotransform)

        save_to_tiff(
            os.path.join(self.output_dir, 'computed_time_of_max.tiff'),
            self.time_of_max, self.geotransform)

        save_to_tiff(
            os.path.join(self.output_dir, 'computed_difference.tiff'),
            difference, self.geotransform)

        save_to_tiff(
            os.path.join(self.output_dir, 'computed_time_15m.tiff'),
            self.first_moment_15m, self.geotransform)

if __name__ == '__main__':
    pass
