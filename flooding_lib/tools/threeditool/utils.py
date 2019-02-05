# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import numpy as np


def force_to_str(text):
    """
    Return str.

    HDF5 strings written in python2 come back as bytes in python3. Use
    this utility to convert them.
    """
    if isinstance(text, bytes):
        return str(text.decode('ascii'))  # bytes must be decoded first
    return str(text)


def get_inverse(a, b, c, d):
    """ Return inverse for a 2 x 2 matrix with elements (a, b), (c, d). """
    D = 1 / (a * d - b * c)
    return d * D, -b * D, -c * D, a * D


class GeoTransform(tuple):
    """
    Convenience wrapper adding all sorts of handy methods to the
    GeoTransform tuple as used by the GDAL library.

    In the raster-store as well as in the GDAL libarary the geo_transform
    defines the transformation from array pixel indices to projected
    coordinates. A pair of projected coordinates (x, y) is calculated
    from a pair of array indices (i, j) as follows:

    p, a, b, q, c, d = self  # the geo_transform tuple

    x = p + a * j + b * i
    y = q + c * j + d * i

    or in a kind of vector notation:

    [x, y] = [p, q] + [[a, b], [c, d]] * [j, i]
    """
    def scale(self, x, y):
        """
        return scaled geo transform.

        :param x: Multiplication factor for the pixel width.
        :param y: Multiplication factor for the pixel height.

        Adjust the second, third, fifth and sixth elements of the geo
        transform so that the extent of the respective image is multiplied
        by scale.
        """
        p, a, b, q, c, d = self
        return self.__class__([p, a * x, b * x, q, c * y, d * y])

    def shift(self, origin):
        """
        Return shifted geo transform.

        :param origin: Integer pixel coordinates.

        Adjust the first and fourth element of the geo transform to match
        a subarray that starts at origin.
        """
        p, a, b, q, c, d = self
        i, j = origin
        return self.__class__([p + a * j + b * i, a, b,
                               q + c * j + d * i, c, d])

    def get_indices(self, points):
        """
        Return pixel indices as a tuple of linear numpy arrays
        """
        # inverse transformation
        p, a, b, q, c, d = self
        e, f, g, h = get_inverse(a, b, c, d)

        # calculate
        x, y = points.transpose()
        return (np.int64(g * (x - p) + h * (y - q)),
                np.int64(e * (x - p) + f * (y - q)))

