"""Reads colormap.csv files.

Can apply colors to numpy grids to save as images.
"""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import logging
import os

import numpy
from matplotlib import colors
from matplotlib import cm

settings = None

try:
    from django.conf import settings
except ImportError:
    # Raster server calls this module as well, and it runs in Flask,
    # not Django!
    pass


logger = logging.getLogger(__name__)


def get_mpl_cmap(colormap, settings_module=settings):
    """We supprort 2 kinds of colormap: default matplotlib colormaps,
    and .csv file colormaps. We first check if the colormap exists as
    a.CSV file, in the COLORMAP_DIR, and create a matplotlib colormap
    using the ColorMap object below. If not, we return the matplotlib
    colormap.

    In both cases, return a matplotlib colormap."""
    if colormap.lower().endswith('.csv'):
        colormap_path = os.path.join(
            settings_module.FLOODING_LIB_COLORMAP_DIR, colormap)

        return ColorMap(colormap_path).to_matplotlib()

    return cm.get_cmap(colormap)


def to_color_tuple(s):
    if len(s) != 6:
        raise ValueError(
            "Colors should have 6 characters, found {0}".format(s))

    rs = s[0:2]
    gs = s[2:4]
    bs = s[4:6]

    t = (int(rs, 16), int(gs, 16), int(bs, 16))

    return t


class ColorMap(object):
    def __init__(self, filename):
        self.filename = filename

        self.leftbounds = []
        self.colors = []

        # We skip all erroneous lines.
        for line in open(self.filename):
            if "," not in line:
                continue

            leftbound, color = line.strip().split(',')

            try:
                leftbound = float(leftbound)
            except ValueError:
                # Probably the header line
                continue

            try:
                color_tuple = to_color_tuple(color)
            except ValueError:
                continue

            self.leftbounds += [leftbound]
            self.colors += [color_tuple]

    def value_to_color(self, value):
        """Return a (r, g, b) tuple for the color this value maps to.

        Return None if no color was found."""

        for leftbound, color in reversed(zip(self.leftbounds, self.colors)):
            if leftbound < value:
                return color

    def legend_values(self):
        """Generate, for each step in the legend, a value that
        falls within that step."""
        leftbounds = list(self.leftbounds)
        leftbounds += [leftbounds[-1] + 1]

        for i in range(len(leftbounds) - 1):
            left, right = leftbounds[i], leftbounds[i + 1]
            yield float(left + right) / 2

    def apply_to_grid(self, grid, opacity_value=255):
        """Returns a 4 x n x m uint8 grid, with four planes that can
        be used to save as an image: red, green, blue and transparent
        values.

        The values that have data will get an opacity equal to
        opacity_value, the others are fully transparent (opacity
        0)."""
        n, m = grid.shape

        colorgrid = numpy.zeros((4, n, m), dtype=numpy.uint8)

        for i, leftbound in enumerate(self.leftbounds):
            if i + i >= len(self.leftbounds):
                # Last leftbound
                mask = (grid >= leftbound)
            else:
                mask = (leftbound <= grid) & (self.leftbounds[i + 1] > grid)

            red, green, blue = self.colors[i]

            colorgrid[0] |= mask * red
            colorgrid[1] |= mask * green
            colorgrid[2] |= mask * blue

        # The opacity should be equal to 'opacity_value' wherever
        # there is a color, and 0 elsewhere. There is a color defined
        # for all values greater than the lowest leftbound.
        if self.leftbounds:
            colorgrid[3] = (min(self.leftbounds) < grid) * opacity_value

        return colorgrid

    def to_matplotlib(self):
        """Return a matplotlib colormap instance."""
        scale_factor = max(self.leftbounds)
        segmentdata = self._matplotlib_segments_from_list(
            zip(self.leftbounds, self.colors),
            scale_factor=scale_factor)

        mpl_cmap = colors.LinearSegmentedColormap(
            name=os.path.basename(self.filename),
            segmentdata=segmentdata)
        mpl_cmap.csv_max_value = scale_factor  # Hack
        return mpl_cmap

    def _matplotlib_segments_from_list(self, values, scale_factor):
        """Value is a list of (leftbound, (r, g, b)) tuples."""
        segmentdata = {
            'red': [],
            'green': [],
            'blue': []
            }

        old_red = old_green = old_blue = 0.0

        for leftbound, (red, green, blue) in values:
            red /= 255.0
            green /= 255.0
            blue /= 255.0
            leftbound /= scale_factor
            segmentdata['red'].append((leftbound, old_red, red))
            segmentdata['green'].append((leftbound, old_green, green))
            segmentdata['blue'].append((leftbound, old_blue, blue))
            old_red = red
            old_green = green
            old_blue = blue

        segmentdata['red'].append((1.0, old_red, 1.0))
        segmentdata['green'].append((1.0, old_green, 1.0))
        segmentdata['blue'].append((1.0, old_blue, 1.0))

        return segmentdata
