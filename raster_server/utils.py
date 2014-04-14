# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import os
import ogr
import osr

import flask
from gislib import pyramids
from gislib import projections
from raster_server import settings

cache = {}


def get_parameters():
    """ Return the request parameters with lowercase keys. """
    return {k.lower(): v for k, v in flask.request.args.items()}


def get_layers():
    """ Return the layers in the datadir. """
    path = settings.DATA_DIR

    def get(path):
        """Return path generator of pyramids in path.

        Yields all the directories below path that contain
        '.pyramid.tif', without recursing deeper into the directory
        structure once that has been found."""
        # Use a queue to track paths we still need to check, so we
        # don't have to use recursion.
        paths_queue = [path]

        while paths_queue:
            path = paths_queue.pop(0)
            names = os.listdir(path)
            if '.pyramid.tif' in names:
                yield path
            else:
                # Add subdirs to queue
                for name in names:
                    subpath = os.path.join(path, name)
                    if os.path.isdir(subpath):
                        # Prepend the path so this becomes a
                        # depth-first search; otherwise the queue will
                        # become as large as the number of layers,
                        # which can be very large for Flooding.
                        paths_queue.insert(0, subpath)

    for layer in get(path):
        yield os.path.relpath(layer, path).replace(os.path.sep, ':')


def get_pyramid(layer):
    """ Return the pyramid for a layer. """
    try:
        return cache[layer]
    except KeyError:
        pyramid = pyramids.Pyramid(os.path.join(settings.DATA_DIR,
                                                *layer.split(':')))
        cache[layer] = pyramid
        return pyramid


def get_leafno(geometry):
    """ Return leafno based on geometry. """
    index = ogr.Open(os.path.join(settings.DATA_DIR, 'index'))
    layer = index[0]
    wkb = ogr.CreateGeometryFromWkt(geometry['wkt'])
    ct = osr.CoordinateTransformation(
        projections.get_spatial_reference(geometry['crs']),
        layer.GetSpatialRef(),
    )
    wkb.Transform(ct)
    layer.SetSpatialFilter(wkb)
    return layer.next().GetField(b'BLADNR')
