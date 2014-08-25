# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Task for exporting all data of a set of scenarios."""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
import shutil
import tempfile

from flooding_lib.tools.exporttool.models import ExportRun


def calculate_export_data(export_run_id):
    # Get export scenarios
    export_run = ExportRun.objects.get(export_run_id)
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


def create_main_csv_file(scenarios, directory):
    pass


def create_scenario_dir(scenario, directory):
    scenario_path = os.path.join(directory, str(scenario.id))
    os.mkdir(scenario_path)


def dirs_into_zipfile(tempdir):
    pass
