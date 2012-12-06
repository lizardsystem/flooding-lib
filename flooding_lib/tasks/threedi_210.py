# Start 3Di calculation using 3Di exe
# Run this under windows.
# This will produce a .nc file.
from threedilib.threedi import setup_and_run_3di
#from flooding_lib.models import ThreediCalculation
from flooding_lib.models import Scenario
from flooding_base.models import Setting
from django.conf import settings

from flooding_lib.util import files
import os
import shutil


def full_model_path(rel_path):
    #/p-flod-fs-00-d1.external-nens.local/flod-share/Flooding/filedatabase/
    if rel_path == '/':
        # Apparently the path is absolute
        return rel_path  # = full path
    else:
        path = Setting.objects.get(key='SOURCE_DIR').value
        path = path.replace('\\', '/')  # Unix path
        model_path = os.path.join(path, rel_path)
        return model_path


def run_threedi_task(some_id, some_type):
    """
    3Di task

    some_id and some_type:

    if some_type = 'threedi_calculation_id', then some_id is the
    threedi_calculation_id, otherwise it is the scenario_id.

    SobekModel can also be a 3di model:
    - project_fileloc contains the .zip filename
    - model_varname contains the .mdu filename
    """

    if hasattr(settings, 'THREEDI_DEFAULT_FILES_PATH'):
        default_source_files_path = settings.THREEDI_DEFAULT_FILES_PATH
    else:
        default_source_files_path = "/home/jack/3di-subgrid/bin"
        print 'No THREEDI_DEFAULT_FILES_PATH in django settings. Taking default %s' % default_source_files_path

    if hasattr(settings, 'THREEDI_BIN_PATH'):
        subgrid_exe_path = settings.THREEDI_BIN_PATH
    else:
        subgrid_exe_path = "/home/jack/3di-subgrid/bin/subgridf90"
        print 'No THREEDI_BIN_PATH in django settings. Taking default %s' % subgrid_exe_path

    scenario_id = some_id
    scenario = Scenario.objects.get(pk=scenario_id)

    print 'Working on 3Di calculation: %s (id %d)' % (scenario, scenario.id)
    if str(scenario.sobekmodel_inundation.sobekversion) != '3di':
        print 'Warning: "sobekversion" is not "3di", but "%s". Is "%s" a 3di model?' % (
            scenario.sobekmodel_inundation.sobekversion, scenario.sobekmodel_inundation)

    full_path = full_model_path(
            scenario.sobekmodel_inundation.project_fileloc)
    print 'Unzipping %s...' % full_path
    with files.unzipped(full_path) as files_in_zip:
        tmp_path = os.path.dirname(files_in_zip[0])  # Assume no subdirs or whatsoever
        mdu_full_path = os.path.join(tmp_path, scenario.sobekmodel_inundation.model_varname)
        #print files_in_zip
        #nc_filename = setup_and_run_3di(mdu_full_path, skip_if_results_available=False)

        print "running..."
        nc_filename = setup_and_run_3di(
            mdu_full_path,
            skip_if_results_available=True,
            source_files_dir=default_source_files_path,
            subgrid_exe=subgrid_exe_path)

        result_folder = os.path.join(scenario.get_abs_destdir().replace('\\', '/'), 'threedi')
        #threedi_calculation.full_result_path
        #print result_folder

        try:
            print 'creating result folder %s...' % result_folder
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
