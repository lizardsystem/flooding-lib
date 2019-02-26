# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Task for exporting all data of a set of scenarios."""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from stat import S_IRUSR, S_IWUSR, S_IRGRP, S_IROTH
import csv
import os
import shutil
import tempfile

from flooding_lib.conf import settings

from flooding_lib.tools.exporttool.models import ExportRun

import logging
logger = logging.getLogger(__name__)

__revision__ = "1.0"  # perform_task wants this


def utf8ify(s):
    if isinstance(s, unicode):
        s = s.encode('utf8')
    return s


def writerow(csvwriter, row):
    csvwriter.writerow([utf8ify(s) for s in row])


def set_broker_logging_handler(broker_handler=None):
    """perform_task.py sets the logging handler using this."""
    if broker_handler is not None:
        logger.addHandler(broker_handler)
    else:
        logger.warning("Broker logging handler does not set.")


def calculate_export_data(export_run_id):
    """Main function of this task."""
    logger.info("Calculating export data for export run {}"
                .format(export_run_id))

    # Get export scenarios
    export_run = ExportRun.objects.get(pk=export_run_id)
    scenarios = export_run.scenarios.all()

    tempdir = tempfile.mkdtemp()
    create_data_directories(scenarios, tempdir)

    # Put data into a zipfile
    zipf = dirs_into_zipfile(tempdir, export_run.generate_dst_path())

    # Make the zipfile readable for the Web server
    make_file_readable_for_all(zipf)
    # Record this zipfile as the result of the export run
    logger.info("Storing zip file as export run result.")
    export_run.save_result_file(zipf)

    # Cleanup
    logger.info("Cleanup.")
    shutil.rmtree(tempdir)

    # Done
    logger.info("Marking export run as done.")
    export_run.done()


def create_data_directories(scenarios, directory):
    """Create the required data in a directory structure. We have
    one main CSV file containg a list of scenarios, and one subdirectory
    for each scenario containing a metadata CSV file and all the result
    files."""
    logger.info("Gathering data in {}.".format(directory))

    create_main_csv_file(scenarios, directory)

    for scenario in scenarios:
        create_scenario_dir(scenario, directory)


def create_main_csv_file(scenarios, directory):
    logger.info("Creating scenarios.csv.")

    csvpath = os.path.join(directory, 'scenarios.csv')
    # Create export data in directory structure
    with open(csvpath, 'wb') as csvfile:
        # Use '|' as delimiter because we need ',' below, and '|'
        # is less likely to occur in the data.
        writer = csv.writer(csvfile, delimiter=b"|")

        # Choosing to leave the header in Dutch and not translated,
        # because this is a background task that runs without knowing
        # what the user's preferred language is.
        writerow(writer, [
            "Scenario ID", "Scenarionaam", "Overschrijdingsfrequentie",
            "Buitenwater", "Buitenwatertype #", "Buitenwatertype",
            "Regio", "Bres"])

        for scenario in scenarios:
            # A scenario will almost always have a single breach, but the
            # data model allows multiple breaches. Therefore most of the
            # fields below have to consider the possibility where multiple
            # values occur, and join them with a "," in that case. Which
            # is why the CSV file is "|" separated.

            breaches = scenario.breaches.all()
            writerow(writer, [
                # Scenario id
                str(scenario.id),

                # Scenario name
                scenario.name,

                # Repeat time
                ",".join(str(scenariobreach.extwrepeattime)
                         for scenariobreach in
                         scenario.scenariobreach_set.all()),

                # External water name
                ",".join(breach.externalwater.name
                         for breach in breaches),

                # External water type #
                ",".join(str(breach.externalwater.type)
                         for breach in breaches),

                # External water type string
                ",".join(breach.externalwater.type_str()
                         for breach in breaches),

                # Region name
                ",".join(breach.region.name for breach in breaches),

                # Breach name
                ",".join(breach.name for breach in breaches)
                ])


def create_scenario_dir(scenario, directory):
    """Each scenario gets a subdirectory, with the scenario ID as name.
    In it we create one CSV file with metadata, and all the result files."""
    scenario_path = os.path.join(directory, str(scenario.id))
    os.mkdir(scenario_path)

    create_scenario_csv_file(scenario, scenario_path)
    copy_scenario_files(scenario, scenario_path)


def create_scenario_csv_file(scenario, directory):
    logger.info("Creating metadata.csv for scenario {}."
                .format(scenario.id))

    csvpath = os.path.join(directory, 'metadata.csv')

    data = scenario.grouped_scenario_information()

    with open(csvpath, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=b"|")

        for header in data:
            writerow(csvwriter, [header['title']])
            for field in header['fields']:
                writerow(csvwriter, [field.name, field.value_str])


def copy_scenario_files(scenario, directory):
    logger.info("Copying result files for scenario {}."
                .format(scenario.id))

    for result in scenario.result_set.all():
        resultloc = result.resultloc.replace('\\', '/')
        file_path = os.path.join(
            settings.EXTERNAL_RESULT_MOUNTED_DIR, resultloc)
        if not os.path.exists(file_path):
            # Skip
            logger.info("Result file does not exist: {}".format(file_path))
            continue

        shutil.copy(file_path, directory)


def dirs_into_zipfile(tempdir, zipfile_path):
    """Pack the created subdirectory structure into a zipfile."""
    logger.info("Zipping {} into {}".format(tempdir, zipfile_path))

    # Zipfile_path should end with ".zip", but shutil.make_archive wants
    # to add that itself.
    if zipfile_path.endswith(".zip"):
        zipfile_path = zipfile_path[:-4]

    return shutil.make_archive(zipfile_path, "zip", tempdir)


def make_file_readable_for_all(filepath):
    """This must be done to make the file readable to Nginx.

    The same goal could be achieved by changing the group of
    the file to 'www-data' and giving only the group read
    permissions, but user buildout is not part of www-data and
    therefore isn't allowed to do that. The below seems to be
    the lesser evil."""

    try:
        os.chmod(filepath, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)
    except OSError as e:
        # Only log
        logger.error(
            'OSError as we tried to change export result permissions:',
            str(e))
