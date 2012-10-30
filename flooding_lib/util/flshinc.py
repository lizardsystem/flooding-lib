"""Tool to loop over fls_h.inc files. Based on nens/asc.py and NumPy
masked arrays. Stripped out all unnecessary flexibility.

Usage:

# Opens zipfile if path ends with zip; inside it opens the only file,
# or raises ValueError if there are several. Currently we need to no
# data value passed in because we don't get it from the file; you may
# need to use some asc file present to get one.
flsh = flshinc.Flsh(path, no_data_value=-999.0)
geo_transform = flsh.geo_transform()  # Format same as GDAL's, in
                                      # Rijksdriehoek probably
cellsize_in_m2 = geo_transform[1]*geo_transform[1]
for timestamp, grid in flsh:
    print("Total inundated area at timestamp {0}: {1} m2".format(
        timestamp, numpy.greater(grid, 0).sum() * cellsize_in_m2))

Extra boolean options to Flsh:
one_per_hour: only yield the first grid of each hour (assumes
              timestamp is in hours)
mutate: constantly yield the same grid object. Means that previously
        yielded grids change. Faster because no copies are made, but
        only use when you understand the risk.

If anything unexpected is encountered in a file, a possibly cryptic
ValueError is raised.
"""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import logging
import numpy
import numpy.ma
import scipy
import zipfile

logger = logging.getLogger(__name__)


def splitline(f):
    return f.readline().decode('utf8').strip().split()


def ints(f):
    return [int(i) for i in splitline(f)]


def floats(f):
    return [float(fl) for fl in splitline(f)]


def check(line, expected):
    if line != expected:
        raise ValueError("line {0} was expected to be {1}".
                         format(line, expected))


class Flsh(object):
    def __init__(
        self, path, no_data_value=-999.0, one_per_hour=False, mutate=False):
        self.path = path
        self.no_data_value = no_data_value
        self.one_per_hour = one_per_hour
        self.mutate = mutate

    def geo_transform(self):
        header = self._parse_header()

        return [
            header['x0'], header['dx'], 0.0,
            header['y0'], 0.0, header['dx']
            ]

    def get_classes(self):
        header = self._parse_header()
        return header['classes']

    def _open_path(self):
        if self.path.endswith('.zip'):
            zipf = zipfile.ZipFile(self.path)
            namelist = zipf.namelist()
            if len(namelist) != 1:
                raise ValueError(
                    "Can only open .zip files with 1 file inside.")
            return zipf.open(namelist[0], mode='rU')
        else:
            return file(self.path, 'rU')

    def _parse_header(self):
        if hasattr(self, '_header'):
            return self._header

        self.f = self._open_path()

        # 1: dimensions
        check(splitline(self.f), ['MAIN', 'DIMENSIONS', 'MMAX', 'NMAX'])
        ncols, nrows = ints(self.f)
#        logger.debug("ncols={0} nrows={1}".format(ncols, nrows))

        # 2: grid
        check(splitline(self.f), ['GRID', 'DX', 'X0', 'Y0'])
        dx, x0, y0 = floats(self.f)
#        logger.debug("dx={0} x0={1} y0={2}".format(dx, x0, y0))

        # 3: classes
        check(
            splitline(self.f),
            ['CLASSES', 'OF', 'INCREMENTAL', 'FILE', 'H', 'C', 'Z', 'U', 'V'])
        classes = []
        line = splitline(self.f)
        while line != ['ENDCLASSES']:
            classes += [[float(fl) for fl in line]]
            line = splitline(self.f)

#        logger.debug("classes: {0}".format(classes))

        self._header = {
            'ncols': ncols,
            'nrows': nrows,
            'dx': dx,
            'x0': x0,
            'y0': y0,
            'classes': classes,
            }
        return self._header

    def __iter__(self):
        header = self._parse_header()

        the_array = numpy.zeros((header['nrows'], header['ncols']))
        current_timestamp = False
        yield_this_grid = False
        last_yielded_hour = None

        for line in self.f:
            line = line.strip().decode('utf8').split()

            if not line or '.' in line[0]:
                if yield_this_grid:
                    if self.mutate:
                        yield current_timestamp, the_array
                    else:
                        yield current_timestamp, numpy.array(the_array)
                    last_yielded_hour = int(current_timestamp)

                    if not line:
                        # End of file
                        return

                # Start of a new timestamp
                timestamp, _, class_column = line
                current_timestamp = float(timestamp)
                class_column = int(class_column) - 1
                yield_this_grid = (
                    not self.one_per_hour
                    or int(current_timestamp) != last_yielded_hour)
            else:
                row, col, classvalue = [int(l) for l in line]

                if classvalue == 0:
                    value = 0.0
                else:
#                    logger.debug(
#                        "classvalue={0} class_column={1}"
#                        .format(classvalue, class_column))
                    value = header['classes'][classvalue - 1][class_column]
#                logger.debug(
#                    "row={0} col={1} value={2}".format(row, col, value))
                the_array[-col][row - 1] = value


def save_grid_to_image(grid, path, classes, colormap, geo_transform=None):
    """Assumes that all values in the grid are values that come from
    one of the classes. Translates the values in the classes to colors
    from the colormap, then finds all the places in the grid that are
    equal to that class and sets all those to the right color.

    The value 0.0 is translated to 'transparent'.

    The type of image is decided by the path, but I only test with
    PNG.

    If path ends with .png, and geo_transform is not None, save a .pgw along
    with the .png based on the geo_transform."""
#    print(classes)

    colormap = colormap[::-1]
#    print(colormap)

    classvalues = set()
    for classline in classes:
        for value in classline:
            classvalues.add(value)

#    print(classvalues)

    class_to_color = dict()
    for classvalue in classvalues:
        for value, color in colormap:
            if classvalue > value:
                class_to_color[classvalue] = color
                break
        else:
            class_to_color[classvalue] = (0, 0, 0, 0)

    n, m = grid.shape
    colorgrid = numpy.zeros((4, n, m), dtype=numpy.uint8)

    redgrid = numpy.zeros((n, m))
    greengrid = numpy.zeros((n, m))
    bluegrid = numpy.zeros((n, m))

    for classvalue, color in class_to_color.items():
        mask = (grid == classvalue)
        redgrid += mask * color[0]
        greengrid += mask * color[1]
        bluegrid += mask * color[2]

    colorgrid[0] = redgrid
    colorgrid[1] = greengrid
    colorgrid[2] = bluegrid

    scipy.misc.imsave(path, colorgrid)

    if path.endswith('.png') and geo_transform is not None:
        pgw = path[:-4]+'.pgw'
        f = file(pgw, 'w')
        for gt in geo_transform:
            f.write("{0}\n".format(gt))
        f.close()

    print("{0} saved.".format(path))


