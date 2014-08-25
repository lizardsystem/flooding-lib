# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Task for exporting all data of a set of scenarios."""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import csv
import os
import shutil
import tempfile

from flooding_lib.conf import settings

from flooding_lib.tools.exporttool.models import ExportRun


def calculate_export_data(export_run_id):
    # Get export scenarios
    export_run = ExportRun.objects.get(pk=export_run_id)
    scenarios = export_run.scenarios.all()

    # Create export data in directory structure
    tempdir = create_data_directories(scenarios)

    # Put data into a zipfile
    zipf = dirs_into_zipfile(tempdir, export_run.generate_dst_path())

    # Record this zipfile as the result of the export run
    export_run.save_result_file(zipf)

    # Cleanup
    shutil.rmtree(tempdir)

    # Done
    export_run.done()


def create_data_directories(scenarios):
    directory = tempfile.mkdtemp()

    create_main_csv_file(scenarios, directory)

    for scenario in scenarios:
        create_scenario_dir(scenario, directory)

    return directory


def create_main_csv_file(scenarios, directory):
    csvpath = os.path.join(directory, 'scenarios.csv')
    with open(csvpath, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=b"|")

        for scenario in scenarios:
            # A scenario will almost always have a single breach, but the
            # data model allows multiple breaches. Therefore most of the
            # fields below have to consider the possibility where multiple
            # values occur, and join them with a "," in that case. Which
            # is why the CSV file is ";" separated.

            breaches = scenario.breaches.all()
            writer.writerow([
                # Scenario id
                str(scenario.id),

                # Scenario name
                scenario.name,

                # Repeat time
                ", ".join(str(scenariobreach.extwrepeattime)
                          for scenariobreach in
                          scenario.scenariobreach_set.all()),

                # External water name
                ", ".join(breach.externalwater.name
                          for breach in breaches),

                # External water type #
                ", ".join(str(breach.externalwater.type)
                          for breach in breaches),

                # External water type string
                ", ".join(breach.externalwater.type_str()
                          for breach in breaches),

                # Region name
                ", ".join(breach.region.name
                          for breach in breaches),

                # Breach name
                ", ".join(breach.name
                          for breach in breaches)
                ])


def create_scenario_dir(scenario, directory):
    scenario_path = os.path.join(directory, str(scenario.id))
    os.mkdir(scenario_path)

    create_scenario_csv_file(scenario, scenario_path)
    copy_scenario_files(scenario, scenario_path)


def create_scenario_csv_file(scenario, directory):
    csvpath = os.path.join(directory, 'metadata.csv')

    data = scenario.grouped_scenario_information()

    with open(csvpath, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=b"|")

        for header in data:
            csvwriter.writerow([header['title']])
            for field in header['fields']:
                csvwriter.writerow([field.name, field.value_str])


def copy_scenario_files(scenario, directory):
    for result in scenario.result_set.all():
        resultloc = result.resultloc.replace('\\', '/')
        file_path = os.path.join(
            settings.EXTERNAL_RESULT_MOUNTED_DIR, resultloc)
        if not os.path.exists(file_path):
            # Skip
            print("Does not exist: {}".format(file_path))
            continue

        shutil.copy(file_path, directory)


def dirs_into_zipfile(tempdir, zipfile_path):
    # Zipfile_path should end with ".zip", but shutil.make_archive wants
    # to add that itself.
    print("Zip {} into {}".format(tempdir, zipfile_path))
    if zipfile_path.endswith(".zip"):
        zipfile_path = zipfile_path[:-4]

    return shutil.make_archive(zipfile_path, "zip", tempdir)
