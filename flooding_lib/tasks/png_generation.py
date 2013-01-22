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

import gdal
import os
import stat
import shutil
import sys

from django import db

from flooding_base.models import Setting
from flooding_lib.models import Scenario
from flooding_lib.util import colormap
from flooding_lib.util import files
from flooding_lib.util import flshinc


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

        result_location = os.path.join(destination_dir, result.resultloc)
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
        if (result.resulttype.id == 0 and
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

    inc_files = [i for i in input_files if i.endswith('.inc')]
    if inc_files:
        logger.debug("first candidate is a .inc file.")
        input_files = inc_files[:1]
        basename = os.path.basename(input_files[0]).replace('_', '')[:4]
    else:
        logger.debug("no .inc files, use all .asc files.")
        input_files = [i for i in input_files if i.endswith('.asc')]
        logger.debug('input files are: %s' % str(input_files))
        if len(input_files) == 1:
            basename = os.path.basename(input_files[0])[:8]
        elif len(input_files) > 1:
            basename = os.path.basename(input_files[0])[:4]
        else:
            logger.warning('no files found to generate pngs')
            return None

    logger.debug("sort input files alfabetically.")
    input_files.sort()
    logger.info("produce images from %s." % input_files)

    logger.debug(
        "there are %s input files, basename for output files is '%s'"
        % (len(input_files), basename))

    colormapobject = colormap.ColorMap(colormapping)

    i = 0
    i_in_filename = False

    for filename in input_files:
        only_one = filename.endswith('.asc') and len(input_files) == 1

        if only_one:
            output_file = os.path.join(output_dir_name, basename + ".png")
        else:
            output_file = os.path.join(
                output_dir_name, basename[:4] + "%04d.png")
            i_in_filename = True

        if i_in_filename:
            real_filename = output_file % i
        else:
            real_filename = output_file

        if filename.endswith('.asc'):
            dataset = gdal.Open(str(filename))
            colormapobject = colormap.ColorMap(colormapping)
            colored_grid = colormapobject.apply_to_grid(
                dataset.ReadAsArray())
            files.save_geopng(
                real_filename, colored_grid, dataset.GetGeoTransform())
            i += 1
            if i_in_filename:
                real_filename = output_file % i
        elif filename.endswith('.inc'):
            logger.debug("Generating PNGs from {0}.".format(filename))
            inc = flshinc.Flsh(filename, one_per_hour=True)
            classes = inc.get_classes()
            geo_transform = inc.geo_transform()

            for timestamp, grid in inc:
                logger.debug(
                    "saving {1} for {0}".format(timestamp, real_filename))
                flshinc.save_grid_to_image(
                    grid, real_filename, classes,
                    colormapobject, geo_transform)
                i += 1
                if i_in_filename:
                    real_filename = output_file % i

    result.firstnr = 0
    result.lastnr = i
    logger.debug("saved %d files." % (i + 1))

    return (basename + "####")[:8]


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
