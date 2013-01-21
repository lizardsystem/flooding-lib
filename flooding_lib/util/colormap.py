"""Reads colormap.csv files.

Can apply colors to numpy grids to save as images.
"""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import numpy


def to_color_tuple(s):
    if len(s) != 6:
        raise ValueError(
            "Colors should have 6 characters, found {0}".format(s))

    rs = s[0:2]
    gs = s[2:4]
    bs = s[4:6]

    t = (int(rs, 16), int(gs, 16), int(bs, 16))
    print("Translated color '{0}' to tuple '{1}'"
          .format(s, t))
    return t


class ColorMap(object):
    def __init__(self, filename):
        self.filename = filename

        self.leftbounds = []
        self.colors = []

        for line in open(self.filename):
            leftbound, color = line.strip().split(',')

            try:
                leftbound = float(leftbound)
            except ValueError:
                # Probably the header line
                continue

            self.leftbounds += [leftbound]
            self.colors += [to_color_tuple(color)]

    def value_to_color(self, value):
        """Return a (r, g, b) tuple for the color this value maps to.

        Return None if no color was found."""

        for leftbound, color in reversed(zip(self.leftbounds, self.colors)):
            if leftbound < value:
                return color

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
                mask = (grid > leftbound)
            else:
                mask = (leftbound < grid) & (self.leftbounds[i + 1] >= grid)

            red, green, blue = self.colors[i]

            colorgrid[0] |= mask * red
            colorgrid[1] |= mask * green
            colorgrid[2] |= mask * blue
            colorgrid[3] |= mask

        # Colorgrid is now a mask grid, that is 1 wherever there are
        # values, and 0 where there are None. Multiply it by the
        # opacity value to get the right opacity grid.
        colorgrid[3] *= opacity_value

        return colorgrid
