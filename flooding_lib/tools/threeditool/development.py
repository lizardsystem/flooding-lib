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
    for item in converter.extract(name='s1', interval=600):
        # continue  # TODO remove
        datetime = item['datetime']
        with Dataset(item['array'], **converter.kwargs) as variable_dataset:
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
    max_waterlevel = converter.maximum(name='s1')
    with Dataset(item['array'], **converter.kwargs) as variable_dataset:
        subtractor = Subtractor(
            bathymetry_dataset=bathymetry_dataset,
            variable_dataset=variable_dataset,
            resolution=5,
        )
        depth_maximum_path = join(output_dir, 'depth-maximum.tif')
        subtractor.process(path=depth_maximum_path)

    # Convert maximum flow velocity and clip by bathymetry
    max_waterlevel = converter.maximum(name='s1')
    with Dataset(item['array'], **converter.kwargs) as variable_dataset:
        subtractor = Subtractor(
            bathymetry_dataset=bathymetry_dataset,
            variable_dataset=variable_dataset,
            resolution=5,
        )
        depth_maximum_path = join(output_dir, 'depth-maximum.tif')
        subtractor.process(path=depth_maximum_path)


"""
- Use new quads with extractor to yield frames
- (Temporarily, or even in-memory?) Resample the bathymetry to some resolution
- Create differ
- Create iterator that optionally uses diffs
- Create flowvelocity




An object that generates tifs
An object that iterates
"""
