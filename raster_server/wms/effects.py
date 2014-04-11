# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
Container for special operations on data, such as shades, levelmaps.

These functions by default have access to the geometry and data
layers in the request.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import re

from matplotlib import cm
from matplotlib import colors
from PIL import Image
from scipy import ndimage
import numpy as np


WKT = re.compile('POLYGON \(\((?P<x1>[^\ ]+) [^,]+,(?P<x2>[^ ]+)')
SHADE = np.array([[0,  1,  1,  1,  0],
                  [1,  1,  1,  0, -1],
                  [1,  1,  0, -1, -1],
                  [1,  0, -1, -1, -1],
                  [0, -1, -1, -1,  0]]) / 18


def shade(args, data, geometry, **kwargs):
    """ Return PIL image. """
    # Determine index, strength from effect
    index = int(args[0])
    strength = float(args[1])
    # Determine zoom dependent magnitude
    x1, x2 = map(float, WKT.match(geometry['wkt']).groups())
    w, h = geometry['size']
    magnitude = w / (x2 - x1)
    # Perform the shade
    colormap = cm.get_cmap('shade')
    normalize = colors.Normalize(vmin=-1, vmax=1)
    shade = np.ma.array(
        magnitude * strength * ndimage.convolve(data[index].data, SHADE),
        mask=data[index].mask,
    )
    rgba = colormap(normalize(shade), bytes=True)
    return Image.fromarray(rgba)


def drought(args, data, **kwargs):
    """ Color according to a waterlevel. """
    # Determine index, strength from effect
    index = int(args[0])
    level = float(args[1])
    # Subtract data from level
    depth = data[index] - level
    # Colorize
    colormap = cm.get_cmap('drought')
    normalize = colors.Normalize(vmin=0.1, vmax=1.5)
    rgba = colormap(normalize(depth), bytes=True)
    return Image.fromarray(rgba)
