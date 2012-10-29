# Start 3Di calculation using 3Di exe
# Run this under windows.
# This will produce a .nc file.
from threedilib.threedi import setup_and_run_3di
from flooding_lib.models import ThreediCalculation
from flooding_lib.models import Scenario

from flooding_lib.util import files
import os
import shutil


def run_threedi_task(some_id, some_type):
    """
    3Di task

    some_id and some_type:

    if some_type = 'threedi_calculation_id', then some_id is the
    threedi_calculation_id, otherwise it is the scenario_id.
    """

    if some_type == 'threedi_calculation_id':
        threedi_calculation_id = some_id
        threedi_calculation = ThreediCalculation.objects.get(pk=threedi_calculation_id)
    else:
        scenario_id = some_id
        scenario = Scenario.objects.get(pk=scenario_id)
        if scenario.threedicalculation_set.count() == 0:
            print 'No ThreediCalculation for scenario %d, skipping' % scenario_id
            return
        threedi_calculation = scenario.threedicalculation_set.all()[0]  # Only 1 possible, right?

    print 'Working on 3Di calculation: %s (belonging to scenario %d)' % (
        threedi_calculation, threedi_calculation.scenario.id)

    print 'Unzipping...'
    with files.unzipped(threedi_calculation.full_model_path) as files_in_zip:
        tmp_path = os.path.dirname(files_in_zip[0])  # Assume no subdirs or whatsoever
        mdu_full_path = os.path.join(tmp_path, threedi_calculation.threedi_model.mdu_filename)
        #print files_in_zip
        #nc_filename = setup_and_run_3di(mdu_full_path, skip_if_results_available=False)
        nc_filename = setup_and_run_3di(mdu_full_path)

        result_folder = threedi_calculation.full_result_path
        #print result_folder

        try:
            print 'creating result folder...'
            os.makedirs(result_folder)
        except OSError:
            print 'warning: error creating folder %s, does it already exist?' % result_folder

        # make subgrid_map.zip from subgrid_map.nc
        tmp_nc_zip = files.mktemp()
        files.add_to_zip(
            tmp_nc_zip,
            [{'filename': nc_filename, 'arcname': 'subgrid_map.nc'}])
        try:
            print 'copying nc zip file...'
            shutil.copy(tmp_nc_zip, os.path.join(result_folder, 'subgrid_map.zip'))
            os.remove(tmp_nc_zip)
        except:
            print 'problem copying nc zip file %s to %s' % (tmp_nc_zip, result_folder)

        # # move .nc to result folder
        # try:
        #     print 'moving nc file...'
        #     shutil.move(nc_filename, result_folder)
        # except:
        #     print 'problem moving nc file %s to %s' % (nc_filename, result_folder)

        # zip the other files to result folder
        tmp_zipfile = files.mktemp()
        for root, dirs, filenames in os.walk(tmp_path):
            for filename in filenames:
                files.add_to_zip(tmp_zipfile, [{
                            'filename': os.path.join(root, filename),
                            'arcname': filename,
                            'delete_after': True
                            }])
        #print tmp_zipfile
        shutil.copy(tmp_zipfile, os.path.join(result_folder, 'scenario.zip'))
        os.remove(tmp_zipfile)


    print 'Finished.'
