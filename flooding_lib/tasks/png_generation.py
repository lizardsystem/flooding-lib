#!c:/python25/python.exe
# -*- coding: utf-8 -*-
#***********************************************************************
#*
#***********************************************************************
#*                      All rights reserved                           **
#*
#*
#*                                                                    **
#*
#*
#*
#***********************************************************************
#* Library    : png_generation
#* Purpose    : convert a set of asc files into png
#* Function   : png_generation.sobek/his_ssm
#*
#* Project    : J0005
#*
#* $Id$
#*
#* initial programmer :  Mario Frasca
#* initial date       :  20080909
#**********************************************************************

__revision__ = "$Rev$"[6:-2]

import os
import stat
import shutil
import sys

from django import db

from osgeo import gdal

from flooding_base.models import Setting
from flooding_lib.models import Scenario
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.util import colormap
from flooding_lib.util import files
from flooding_lib.util import flshinc

INPUTFIELD_STARTMOMENT_BREACHGROWTH_ID = 9

if sys.version_info < (2, 4):
    print("I think I need version python2.4 and I was called from %d.%d" %
          sys.version_info[:2])

import logging

logger = logging.getLogger(__name__)


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

if __name__ == '__main__':
    sys.path.append('..')

    from django.core.management import setup_environ
    import lizard.settings
    setup_environ(lizard.settings)


def common_generation(scenario_id, source_programs, tmp_dir):
    """invokes compute_png_files for all grids

    loop on all results computed for the given scenario_id, unpack
    them into a temporary directory, get the corresponding color
    mapping, convert to png, set in the results record the
    resultpngloc field.
    """

    scenario = Scenario.objects.get(pk=scenario_id)
    destination_dir = (
        Setting.objects.get(key='DESTINATION_DIR').value.replace('\\', '/'))
    source_dir = (
        Setting.objects.get(key='SOURCE_DIR').value.replace('\\', '/'))

    logger.debug("select results relative to scenario %s" % scenario_id)
    results = list(scenario.result_set.filter(
            resulttype__program__in=source_programs,
            resulttype__color_mapping_name__isnull=False)
                   .exclude(resulttype__color_mapping_name=""))

    logger.debug("selected results for scenario: %s" % str(results))

    output_dir_name = os.path.join(destination_dir, scenario.get_rel_destdir())

    logger.debug("starting the loop on all previously computed results")

    for result in results:
        logger.debug("examining results record: '%s'" % str(result))

        result_location = os.path.join(
            destination_dir, result.resultloc.replace('\\', '/'))
        logger.debug("Result location: " + result_location)
        result_output_dir = os.path.join(
            output_dir_name, result.resulttype.name)

        # Check for empty result file
        if os.stat(result_location)[stat.ST_SIZE] == 0:
            logger.warning("input file '%s' is empty" % result.resultloc)
            continue

        # Make sure destination directory exists
        if not os.path.isdir(result_output_dir):
            os.makedirs(result_output_dir)

        # Figure out the color mapping name
        if (result.resulttype.id in [0, 1] and
            scenario.main_project.color_mapping_name):
            color_mapping_name = scenario.main_project.color_mapping_name
        else:
            color_mapping_name = result.resulttype.color_mapping_name

        colormapping_abs = os.path.join(
            source_dir, "colormappings", color_mapping_name)
        # Copy color mapping
        shutil.copy(
            colormapping_abs,
            os.path.join(result_output_dir, "colormapping.csv"))

        if result_location.endswith('.zip'):
            # Unpack zip file
            with files.temporarily_unzipped(
                result_location, rezip=False, tmp_dir=tmp_dir) as unzipped:
                infile_asc = compute_png_files(
                    result, result_output_dir,
                    unzipped,
                    colormapping_abs)
        else:
            # Just use the file itself
            infile_asc = compute_png_files(
                result, result_output_dir,
                [result_location],
                colormapping_abs)

        # Set pngloc to result
        result.resultpngloc = os.path.join(
            result_output_dir, infile_asc + ".png")
        result.save()

    return True


def compute_png_files(
    result, output_dir_name, input_files, colormapping):
    """subroutine isolating the png computing logic.

    it assumes all data is in place.
    it does not remove (temporary) input data.
    it saves the files into the abs_output_dir_name

    the 'result' dictionary holds all relevant data, in particular the
    fields 're', 'basename', 'min_nr', 'max_nr'.

    returns the common part of the name of the images produced.
    """

    colormapobject = colormap.ColorMap(colormapping)

    # If we have an inc file, use that
    inc_file = next(
        (i for i in input_files if i.lower().endswith('.inc')), None)

    if inc_file:
        amount, basename = generate_from_inc(
            output_dir_name, inc_file, colormapobject)
    else:
        amount, basename = generate_from_asc(
            output_dir_name, input_files, colormapobject, result)

    result.firstnr = 0
    result.lastnr = amount

    return (basename + "####")[:8]


def generate_from_inc(output_dir_name, inc_file, colormapobject):
    basename = os.path.basename(inc_file).replace('_', '')[:4]
    output_file = os.path.join(
        output_dir_name, basename + "{:04d}.png")

    inc = flshinc.Flsh(inc_file, one_per_hour=True)
    classes = inc.get_classes()
    geo_transform = inc.geo_transform()

    for i, (timestamp, grid) in enumerate(inc):
        real_filename = output_file.format(i)

        flshinc.save_grid_to_image(
            grid, real_filename, classes,
            colormapobject, geo_transform)

    return i + 1, basename


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


def generate_from_asc(
    output_dir_name, input_files, colormapobject, result):
    input_files = sorted(i for i in input_files if i.lower().endswith('.asc'))

    amount = len(input_files)

    if amount == 1:
        basename = os.path.basename(input_files[0])[:8]
        output_file = os.path.join(output_dir_name, basename + ".png")
    elif amount > 1:
        basename = os.path.basename(input_files[0])[:4]
        output_file = os.path.join(
            output_dir_name, basename[:4] + "{:04d}.png")
    else:
        logger.warning('no files found to generate pngs')
        return 0, None

    for i, filename in enumerate(input_files):
        real_filename = output_file.format(i)

        try:
            dataset = gdal.Open(str(filename))
            if dataset is None:
                logger.debug("Dataset None: " + str(filename))
            else:
                grid = dataset.ReadAsArray()

                # Hack -- correct grid_ta for start moment of breach
                if result.resulttype.name == 'gridta':
                    correct_gridta(grid, result)

                colored_grid = colormapobject.apply_to_grid(grid)

                files.save_geopng(
                    real_filename, colored_grid, dataset.GetGeoTransform())
        finally:
            del dataset  # Closes the file object so that it can be
                         # deleted on Windows

    return amount, basename


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
