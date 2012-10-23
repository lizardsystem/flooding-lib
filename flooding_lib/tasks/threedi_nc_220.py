# Task 220: read netcdf (.nc) 3Di result file, output in .png files.

from threedilib.threedi import post_process_3di


def process_threedi_nc(some_id):
    """
    Read netcdf (.nc) 3Di result file, output in .png files.
    """
    full_path = "/home/jack/git/sites/flooding/driedi/Vecht/subgrid_map.nc"
    post_process_3di(full_path)
