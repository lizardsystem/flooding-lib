# Task 220: read netcdf (.nc) 3Di result file, output in .png files.

#from threedilib.threedi import post_process_3di
#from threedilib.threedi import post_process_detailed_3di
#from flooding_lib.models import ThreediCalculation
from flooding_lib.models import Result
from flooding_lib.models import ResultType
from flooding_lib.models import Scenario
from flooding_lib.models import Region
from flooding_lib.util import files

import tempfile
import os


def process_threedi_nc(
    some_id, some_type,
    detailed=True, with_region=True,
    gridsize=None,
    gridsize_divider=2):
    """
    Read netcdf (.nc) 3Di result file, output in .png files.

    Input:

    There must be a "subgrid_map.zip" (and a
    scenario.zip) at (scenario.get_abs_destdir())/threedi.

    Output:

    folder with png files and a Result object corresponding to this
    folder.
    """

    region = None

    scenario_id = some_id
    scenario = Scenario.objects.get(pk=scenario_id)
    try:
        if with_region:
            region = scenario.breaches.all()[0].region
    except:
        print 'Something went wrong with getting region extent for scenario %s' % scenario

    #full_path = "/home/jack/git/sites/flooding/driedi/Vecht/subgrid_map.nc"

    full_base_path = scenario.get_abs_destdir().replace('\\', '/')
    full_path_zip = os.path.join(
        full_base_path, 'threedi', 'subgrid_map.zip')

    result_folder = os.path.join(full_base_path, 'threedi_waterlevel_png')
    #print result_folder

    try:
        print 'creating result folder...'
        os.makedirs(result_folder)
    except OSError:
        print 'warning: error creating folder %s, does it already exist?' % result_folder

    dst_basefilename = os.path.join(result_folder, 'waterlevel_%04d_j')
    dst_basefilename_detailed = os.path.join(result_folder, 'waterlevel_%04d')

    print 'input: %s' % full_path_zip
    if detailed:
        print 'output (detailed): %s' % dst_basefilename_detailed
    else:
        print 'output: %s' % dst_basefilename
    with files.unzipped(full_path_zip) as files_in_zip:
        for filename in files_in_zip:
            if filename.endswith('subgrid_map.nc'):
                print 'yup, subgrid_map.nc found, proceeding'
                if detailed:
                    num_steps = post_process_detailed_3di(
                        filename, dst_basefilename_detailed,
                        region=region, gridsize_divider=gridsize_divider,
                        gridsize=gridsize)
                else:
                    num_steps = post_process_3di(filename, dst_basefilename)
            else:
                print 'ignored file %s' % filename

    #print 'results are available at:'
    #print filenames

    print 'creating corresponding Result object...'
    src_rel_path = os.path.join(
        scenario.get_rel_destdir(),
        'threedi',
        'subgrid_map.zip')
    dst_rel_path = os.path.join(
        scenario.get_rel_destdir(),
        'threedi_waterlevel_png',
        'waterlevel_####.png')

    result_type = ResultType.objects.get(name='threediwaterlevel_t')
    result, created = Result.objects.get_or_create(
        resulttype=result_type,
        scenario=scenario,
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
