"""Module that can start 3Di-specific tasks."""

from __future__ import division

from osgeo import gdal
import math
import os
import shutil
import tempfile

from flooding_lib.tools.importtool.models import InputField
from flooding_lib.models import Result, ResultType, Scenario
from flooding_lib.util.files import temporarily_unzipped, add_to_zip

from flooding_lib.tools.threeditool.converters import Converter
from flooding_lib.tools.threeditool.processors import Cutter, Subtractor
from flooding_lib.tools.threeditool.datasets import Dataset

RESOLUTION_MAX_DEPTH = 5  # We don't want the highest 3Di resolution for
                          # space reasons

# the animation resolution must be restricted to make each frame about this
# amount of pixels
APPROXIMATE_ANIMATION_PIXELS = 4 * 1024 * 1024  # just low enough to work


def get_animation_resolution(dataset):
    """ Return not too high resulution for animations based on dataset. """
    dataset_size = dataset.RasterXSize * dataset.RasterYSize
    dataset_resolution = dataset.GetGeoTransform()[1]

    size_correction = dataset_size / APPROXIMATE_ANIMATION_PIXELS
    resolution_correction = math.sqrt(size_correction)

    return max(dataset_resolution, dataset_resolution * resolution_correction)


def process_scenario(scenario_id):
    """Convert a 3Di scenario that was imported."""

    # The normal (Sobek) task starts Workflow Template 2.
    # This starts
    # 132 -> 134 -> 160 -> 162 -> 180 -> 185
    # and
    # 150 -> 155
    #
    # meaning
    #
    # 132 = compute rise speed
    # 134 = compute mortality grid
    # 160 = simulation
    # 162 = embankment damage
    # 180 = pyramid generation
    # 185 = presentation generation
    # 150 = pyramid generation 150
    # 155 = presentation generation 155
    #
    # pyramid_generation has 'sobek' and 'his_ssm' functions
    # Same for presentation generation
    #
    # For 3Di we need to do
    # - Compute "sobek-equivalent" results
    # - See if the sobek pyramid generation works on it
    # - See if the sobek presentation generation works on it

    scenario = Scenario.objects.get(pk=scenario_id)

    bathymetry = scenario.result_set.get(resulttype__name='bathymetry')
    netcdf = scenario.result_set.get(resulttype__name='results_3di')

    success1, success2 = False, False
    result1, result2 = None, None

    with temporarily_unzipped(bathymetry.absolute_resultloc) as bathpath:
        with temporarily_unzipped(netcdf.absolute_resultloc) as ncdfpath:
            bathymetry_dataset = gdal.Open(bathpath[0])

            with Converter(ncdfpath[0]) as converter:
                workdir = tempfile.mkdtemp()

                try:
                    result1, success1 = compute_waterdepth_animation(
                        scenario,
                        bathymetry_dataset,
                        converter,
                        workdir)

                    result2, success2 = compute_max_waterdepth_tif_result(
                        scenario,
                        bathymetry_dataset,
                        converter,
                        workdir)
                finally:
                    shutil.rmtree(workdir)

    success = all([success1, success2])
    result = result1, result2
    return (success, result, '-')


def compute_waterdepth_animation(
        scenario, bathymetry_dataset, converter, workdir):
    paths = []  # Will be input parameter for add_to_zip(), so should
                # contain dicts with filename, arcname, remove_after
    waterdepthanim = ResultType.objects.get(name='gridwaterdepth_t')

    for datetime, array in converter.extract(name='s1', interval=3600):
        with Dataset(array, **converter.kwargs) as variable_dataset:
            subtractor = Subtractor(
                bathymetry_dataset=bathymetry_dataset,
                variable_dataset=variable_dataset,
                resolution=get_animation_resolution(bathymetry_dataset),
            )
            depth_path = os.path.join(
                workdir, datetime.strftime('depth-%Y%m%dT%H%M%S.tif'),
            )
            subtractor.process(path=depth_path)
            paths.append({
                'filename': depth_path,
                'arcname': os.path.basename(depth_path),
                'remove_after': False
            })

    zip_path = os.path.join(workdir, 'waterdepth_rasters.zip')
    add_to_zip(zip_path, paths)

    result = Result.objects.create_from_file(
        scenario,
        waterdepthanim,
        zip_path)

    return result, True

def compute_max_waterdepth_tif_result(
        scenario, bathymetry_dataset, converter, workdir):
    # Compute and store a max water depth TIF
    maxlevel = converter.maxlevel()
    maxwdepth = ResultType.objects.get(name='gridmaxwaterdepth')

    with Dataset(maxlevel, **converter.kwargs) as variable_dataset:
        subtractor = Subtractor(
            bathymetry_dataset=bathymetry_dataset,
            variable_dataset=variable_dataset,
            resolution=RESOLUTION_MAX_DEPTH,
        )
        depth_maximum_path = os.path.join(
            workdir, 'depth-maximum.tif')
        subtractor.process(path=depth_maximum_path)

    # Import max water depth grid as a Result into the
    # normal Flooding database
    result = Result.objects.create_from_file(
        scenario, maxwdepth, depth_maximum_path)

    return result, True
