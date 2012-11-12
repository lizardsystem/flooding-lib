# Task 220: read netcdf (.nc) 3Di result file, output in .png files.

from threedilib.threedi import post_process_3di
from threedilib.threedi import post_process_detailed_3di
from flooding_lib.models import ThreediCalculation
from flooding_lib.models import Result
from flooding_lib.models import ResultType
from flooding_lib.models import Scenario
from flooding_lib.util import files

import tempfile
import os


def process_threedi_nc(some_id, some_type, detailed=True):
    """
    Read netcdf (.nc) 3Di result file, output in .png files.

    Input:

    if some_type is 'threedi_calculation_id', take corresponding
    ThreediCalculation object. There must be a "subgrid_map.nc" (and a
    scenario.zip) at threedi_calculation.full_result_path.

    if some_type is something else, a flooding scenario is
    assumed. Then Scenario.threedicalculation_set.all() returns the
    (one and only) calcuation object.

    Output:

    folder with png files and a Result object corresponding to this
    folder.
    """

    if some_type == 'threedi_calculation_id':
        threedi_calculation_id = some_id
        threedi_calculation = ThreediCalculation.objects.get(pk=threedi_calculation_id)
    else:
        scenario_id = some_id
        scenario = Scenario.objects.get(pk=scenario_id)
        if scenario.threedicalculation_set.count() == 0:
            print 'No ThreediCalculation for scenario %s, skipping' % scenario_id
            return
        threedi_calculation = scenario.threedicalculation_set.all()[0]  # Only 1 possible, right?

    #full_path = "/home/jack/git/sites/flooding/driedi/Vecht/subgrid_map.nc"
    full_path_zip = os.path.join(threedi_calculation.full_result_path, 'subgrid_map.zip')

    result_folder = os.path.join(threedi_calculation.full_base_path, 'threedi_waterlevel_png')
    #print result_folder

    try:
        print 'creating result folder...'
        os.makedirs(result_folder)
    except OSError:
        print 'warning: error creating folder %s, does it already exist?' % result_folder

    dst_basefilename = os.path.join(result_folder, 'waterlevel_%04d')

    print 'input: %s' % full_path_zip
    print 'output: %s' % dst_basefilename
    with files.unzipped(full_path_zip) as files_in_zip:
        for filename in files_in_zip:
            if filename.endswith('subgrid_map.nc'):
                print 'yup, subgrid_map.nc found, proceeding'
                if detailed:
                    num_steps = post_process_detailed_3di(filename, dst_basefilename)
                else:
                    num_steps = post_process_3di(filename, dst_basefilename)
            else:
                print 'ignored file %s' % filename

    #print 'results are available at:'
    #print filenames

    print 'creating corresponding Result object...'
    src_rel_path = os.path.join(
        threedi_calculation.scenario.get_rel_destdir(),
        'threedi',
        'subgrid_map.zip')
    dst_rel_path = os.path.join(
        threedi_calculation.scenario.get_rel_destdir(),
        'threedi_waterlevel_png',
        'waterlevel_####.png')

    result_type = ResultType.objects.get(name='threediwaterlevel_t')
    result, created = Result.objects.get_or_create(
        resulttype=result_type,
        scenario=threedi_calculation.scenario,
        defaults={
            'resultloc': src_rel_path,
            'resultpngloc': dst_rel_path,
            'startnr': 0,
            'firstnr': 0,
            'lastnr': num_steps-1}
        )
    if not created:
        print 'updating existing result.'
        print 'old results: %s %s' % (result.resultloc, result.resultpngloc)
        if result.resultpngloc != dst_rel_path or result.resultloc != src_rel_path:
            print '!delete old result files manually!'
        result.resultloc = src_rel_path
        result.resultpngloc = dst_rel_path
        result.startnr = 0
        result.firstnr = 0
        result.lastnr = num_steps - 1
        print 'new results: %s %s' % (result.resultloc, result.resultpngloc)
        result.save()
    print 'result updated/created with id %d' % result.id
