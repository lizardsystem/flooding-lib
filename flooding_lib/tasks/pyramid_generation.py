import gdal
import os
import stat
import sys

from django import db

from flooding_base.models import Setting
from flooding_lib.models import Scenario
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.tools.pyramids import models as pyramidmodels
from flooding_lib.util import files
from flooding_lib.util import flshinc

import logging
logger = logging.getLogger(__name__)

INPUTFIELD_STARTMOMENT_BREACHGROWTH_ID = 9


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

if __name__ == '__main__':
    sys.path.append('..')

    from django.core.management import setup_environ
    import lizard.settings
    setup_environ(lizard.settings)


def common_generation(scenario_id, source_programs, tmp_dir):
    """
    loop on all results computed for the given scenario_id, unpack
    them into a temporary directory, save as a pyramid, set in the
    results record the resultpngloc field.
    """

    scenario = Scenario.objects.get(pk=scenario_id)

    logger.debug("select results relative to scenario %s" % scenario_id)
    results = list(scenario.result_set.filter(
            resulttype__program__in=source_programs,
            resulttype__color_mapping_name__isnull=False)
                   .exclude(resulttype__color_mapping_name=""))

    logger.debug("selected results for scenario: %s" % str(results))

    logger.debug("starting the loop on all previously computed results")
    results_dir = (
        Setting.objects.get(key='DESTINATION_DIR').value.replace('\\', '/'))

    for result in results:
        logger.debug("examining results record: '%s'" % str(result))

        result_location = os.path.join(
            results_dir, result.resultloc.replace('\\', '/'))
        logger.debug("Result location: " + result_location)

        # Check for empty result file
        if os.stat(result_location)[stat.ST_SIZE] == 0:
            logger.warning("input file '%s' is empty" % result.resultloc)
            continue

        result_to_correct_gridta = (
            result if result.resulttype.name == 'gridta'
            else None)

        if result_location.endswith('.zip'):
            # Unpack zip file
            with files.temporarily_unzipped(
                result_location, rezip=False, tmp_dir=tmp_dir) as unzipped:
                pyramid_or_animation = compute_pyramids(
                    result, unzipped, result_to_correct_gridta)
        else:
            # Just use the file itself
            pyramid_or_animation = compute_pyramids(
                result, [result_location], result_to_correct_gridta)

        if hasattr(pyramid_or_animation, 'frames'):
            result.animation = pyramid_or_animation
        else:
            result.raster = pyramid_or_animation
        result.save()

    return True


def compute_pyramids(result, input_files, result_to_correct_gridta):
    # If we have an inc file, use that
    inc_file = next(
        (i for i in input_files if i.lower().endswith('.inc')), None)

    if inc_file:
        # amount, basename = generate_from_inc(inc_file)
        return animation_from_inc(inc_file)
    elif len(input_files) == 1:
        return pyramid_from_single_asc(
            input_files[0], result_to_correct_gridta)
    else:
        return animation_from_ascs(input_files)


def animation_from_inc(inc_file):
    """Create a temporary GDAL DataSet; loop over the .inc file and
    save the grids to the DataSet; add them to an Animation."""
    fls = flshinc.Flsh(inc_file, one_per_hour=True, mutate=False)
    animation = pyramidmodels.Animation.objects.create()
    dataset = GDAL_MEM_DRIVER.Create(
        b'',  # Dummy path name
        fls.ncols, fls.nrows, 1, gdal.GDT_Float64)
    dataset.SetGeoTransform(fls.geo_transform())
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(0.0)

    for timestamp, array in fls:
        band.WriteArray(array)
        animation.add(dataset)

    return animation


def animation_from_ascs(input_files):
    animation = pyramidmodels.Animation.objects.create()
    for input_file in input_files:
        dataset = gdal.Open(input_file)
        if dataset is not None:
            animation.add(dataset)

    return animation


def pyramid_from_single_asc(input_file, result_to_correct_gridta):
    dataset = gdal.Open(input_file)
    if dataset is not None:
        pyramid = pyramidmodels.Raster.objects.create()
        if result_to_correct_gridta is None:
            pyramid.add(dataset)
        else:
            # Correct for startmoment bresgroei
            fixed_dataset = GDAL_MEM_DRIVER.CreateCopy('', dataset)
            grid = fixed_dataset.GetRasterBand(1).ReadAsArray()
            correct_gridta(grid, result_to_correct_gridta)
            fixed_dataset.GetRasterBand(1).WriteArray(grid)
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

if __name__ == '__main__':
    pass
