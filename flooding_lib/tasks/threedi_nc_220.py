# Task 220: read netcdf (.nc) 3Di result file, output in .png files.

from threedilib.threedi import post_process_3di
import tempfile
import os


def process_threedi_nc(some_id):
    """
    Read netcdf (.nc) 3Di result file, output in .png files.
    """
    full_path = "/home/jack/git/sites/flooding/driedi/Vecht/subgrid_map.nc"
    dst_tmp_dir = tempfile.mkdtemp()
    dst_basefilename = os.path.join(dst_tmp_dir, '_step%d.png')

    print 'input: %s' % full_path
    print 'output: %s' % dst_basefilename
    filenames = post_process_3di(full_path, dst_basefilename)

    print 'results are available at:'
    print filenames
