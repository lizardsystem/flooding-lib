"""Module that can start 3Di-specific tasks."""
from osgeo import gdal

from flooding_lib.tools.importtool.models import InputField
from flooding_lib.models import Scenario
from flooding_lib.util.files import temporarily_unzipped

from flooding_lib.tools.threeditool.converters import Converter
from flooding_lib.tools.threeditool.processors import Cutter, Subtractor
from flooding_lib.tools.threeditool.datasets import Dataset

GOAL_RESOLUTION = 5  # We don't want the highest 3Di resolution for
                     # space reasons


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

    with temporarily_unzipped(bathymetry.absolute_resultloc) as bathpath:
        with temporarily_unzipped(netcdf.absolute_resultloc) as ncdfpath:
            bath = gdal.Open(bathpath[0])

            with Converter(ncdfpath[0]) as converter:
                maxlevel = converter.maxlevel()
                subtractor = Subtractor(
                    bathymetry_dataset=bathymetry_dataset,
                    variable_dataset=variable_dataset,
                    resolution=GOAL_RESOLUTION,
                )
                depth_maximum_path = join(output_dir, 'depth-maximum.tif')
                subtractor.process(path=depth_maximum_path)


    return (True, bathymetry.absolute_resultloc, 'fouten')
