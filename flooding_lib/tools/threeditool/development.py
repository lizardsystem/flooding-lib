# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from os.path import join

from osgeo import gdal

from flooding_lib.tools.threeditool.converters import Converter
from flooding_lib.tools.threeditool.processors import Cutter, Subtractor
from flooding_lib.tools.threeditool.datasets import Dataset


def run_example():

    # paths
    development_dir = 'development/5158'
    development_dir = 'development/0000'
    results_3di_path = join(development_dir, 'results_3di.nc')
    bathymetry_path = join(development_dir, 'dem_test_5m.tif')
    output_dir = join(development_dir, 'output')

    # converter test
    bathymetry_dataset = gdal.Open(bathymetry_path)
    with Converter(results_3di_path) as converter:
        # Convert waterlevels and turn them into depths
        for datetime, array in converter.extract(name='s1', interval=3600):
            with Dataset(array, **converter.kwargs) as variable_dataset:
                subtractor = Subtractor(
                    bathymetry_dataset=bathymetry_dataset,
                    variable_dataset=variable_dataset,
                    resolution=5,
                )
                depth_path = join(
                    output_dir, datetime.strftime('depth-%Y%m%mT%H%M%S.tif'),
                )
                subtractor.process(path=depth_path)

        # Convert maximum waterlevel and turn into depth
        array = converter.maxlevel()
        with Dataset(array, **converter.kwargs) as variable_dataset:
            subtractor = Subtractor(
                bathymetry_dataset=bathymetry_dataset,
                variable_dataset=variable_dataset,
                resolution=5,
            )
            depth_maximum_path = join(output_dir, 'depth-maximum.tif')
            subtractor.process(path=depth_maximum_path)

        # Convert maximum flow velocity and clip by bathymetry
        array = converter.maxflow()
        with Dataset(array, **converter.kwargs) as variable_dataset:
            cutter = Cutter(
                bathymetry_dataset=bathymetry_dataset,
                variable_dataset=variable_dataset,
                resolution=5,
            )
            depth_maximum_path = join(output_dir, 'flow-maximum.tif')
            cutter.process(path=depth_maximum_path)

    # iterate on the tifs to get arrival and risetime
