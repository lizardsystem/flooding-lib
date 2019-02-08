# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import itertools

from osgeo import gdal
from osgeo import gdal_array
import numpy as np

from flooding_lib.tools.threeditool.utils import GeoTransform
from flooding_lib.tools.threeditool.datasets import Dataset

# resulting dtypes for the processor results
DTYPE = 'f4'
NO_DATA_VALUE = -9999.

DRIVER = gdal.GetDriverByName(str('Gtiff'))
DATA_TYPE = gdal_array.NumericTypeCodeToGDALTypeCode(np.dtype(DTYPE).type)


def partition(shape, chunks=(1024, 1024)):
    """
    Return generator of (offset, shape) tuples.

    :param shape: Shape of the array that is processed.
    :type shape: 2-tuple of ints

    :param chunks: Maximum size of the chunks.
    :type chunks: 2-tuple of ints

    The returned offset and shape can be used to process an array in
    chunks. The shape of chunks at lower right edges may be smaller than the
    chunks parameter.
    """

    # offsets of the chunks into the raster
    i1, j1 = np.mgrid[0:shape[0]:chunks[0], 0:shape[1]:chunks[1]]

    # stops per chunk, either offset plus chunkshape, or shape if at edge
    i2, j2 = (np.minimum(i1 + chunks[0], shape[0]),
              np.minimum(j1 + chunks[1], shape[1]))

    # process the slices in morton order
    for p, q in itertools.product(*map(range, i1.shape)):
        offset = i1[p, q], j1[p, q]
        shape = i2[p, q] - offset[0], j2[p, q] - offset[1]
        yield offset, shape


class Processor(object):
    """
    Do things with bathymetry and 3Di variable in a new resolution.
    """
    options = ['COMPRESS=DEFLATE', 'TILED=YES']

    def __init__(self, bathymetry_dataset, variable_dataset, resolution):
        """
        :param bathymetry_dataset: High resolution bathymetry gdal dataset
        :param variable_dataset: Low resolution 3Di variable gdal dataset
        :param resolution: result raster resolution in meter.
        """
        self.projection = bathymetry_dataset.GetProjection()
        self.bathymetry_dataset = bathymetry_dataset
        self.variable_dataset = variable_dataset

        # derive the
        self.shape, self.geo_transform = self._get_shape_and_geo_transform(
            bathymetry_dataset=bathymetry_dataset, resolution=resolution,
        )

    def _get_shape_and_geo_transform(self, bathymetry_dataset, resolution):
        """
        Return shape, geo_tranfsorm.
        Determine shape and geotransform for a given resolution in meters.
        """
        p, a, b, q, c, d = bathymetry_dataset.GetGeoTransform()

        # determine the projected geometry of the bathymetry
        width = a * bathymetry_dataset.RasterXSize
        height = -d * bathymetry_dataset.RasterYSize

        # 'ceil division' to determine the shape in the desired resolution
        shape = -int(-height // resolution), -int(-width // resolution)

        return shape, GeoTransform([p, resolution, 0, q, 0, -resolution])

    def _reproject(self, source, offset, shape):
        kwargs = {
            'geo_transform': self.geo_transform.shift(offset),
            'no_data_value': NO_DATA_VALUE,
            'projection': self.projection,
        }
        values = np.full(shape, NO_DATA_VALUE, dtype=DTYPE)
        with Dataset(values[np.newaxis], **kwargs) as target:
            gdal.ReprojectImage(
                source,
                target,
                source.GetProjection(),
                target.GetProjection(),
                gdal.GRA_NearestNeighbour,
                0.0,    # Dummy WarpMemoryLimit, same as default.
                0.125,  # Max error in pixels. Without passing this,
                        # it's 0.0, which is very slow. 0.125 is the
                        # default of gdalwarp on the command line.
            )
        return {'values': values, 'no_data_value': NO_DATA_VALUE}

    def process(self, path, resolution=5):
        """
        Store processed raster at path.

        :param path: path to the resulting geotiff.
        """
        # create result dataset
        result_dataset = DRIVER.Create(
            path,
            self.shape[1],
            self.shape[0],
            1,
            DATA_TYPE,
            options=self.options,
        )
        result_dataset.SetProjection(self.projection)
        result_dataset.SetGeoTransform(self.geo_transform)
        result_band = result_dataset.GetRasterBand(1)
        result_band.SetNoDataValue(NO_DATA_VALUE)

        # loop the chunks
        for offset, shape in partition(self.shape):
            bathymetry_data = self._reproject(
                source=self.bathymetry_dataset, offset=offset, shape=shape,
            )
            variable_data = self._reproject(
                source=self.variable_dataset, offset=offset, shape=shape,
            )
            result_data = self._function(
                variable_data=variable_data,
                bathymetry_data=bathymetry_data,
            )
            result_band.WriteArray(
                result_data['values'], offset[1], offset[0],
            )


class Subtractor(Processor):
    """
    Subtract high resolution bathymetry from low resolution waterlevel and
    save as tif.
    """
    def _function(self, variable_data, bathymetry_data):
        # do some unpacking
        v_values = variable_data['values']
        v_no_data_value = variable_data['no_data_value']
        b_values = bathymetry_data['values']
        b_no_data_value = bathymetry_data['no_data_value']

        # determine where both sources have data
        select = np.logical_and(
            v_values != v_no_data_value,
            b_values != b_no_data_value,
        )

        # prepare result
        r_values = np.full_like(v_values, v_no_data_value)

        # populate result
        r_values[select] = v_values[select] - b_values[select]

        # mask below zero
        dry = np.logical_and(select, r_values < 0)
        r_values[dry] = v_no_data_value

        return {'values': r_values, 'no_data_value': v_no_data_value}


class Cutter(Processor):
    """
    Use high resolution bathymetry to clip low resolution flow velocity and
    save as tif.
    """
    def _function(self, variable_data, bathymetry_data):
        # do some unpacking
        v_values = variable_data['values']
        v_no_data_value = variable_data['no_data_value']
        b_values = bathymetry_data['values']
        b_no_data_value = bathymetry_data['no_data_value']

        # determine where both sources have data
        select = np.logical_and(
            v_values != v_no_data_value,
            b_values != b_no_data_value,
        )

        # prepare result
        r_values = np.full_like(v_values, v_no_data_value)

        # populate result
        r_values[select] = v_values[select]

        return {'values': r_values, 'no_data_value': v_no_data_value}
