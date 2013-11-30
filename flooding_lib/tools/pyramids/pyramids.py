# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

""" """

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import logging

from . import models

import numpy as np
from matplotlib import cm
from matplotlib import colors

logger = logging.getLogger(__name__)


def save_dataset_as_pyramid(dataset):
    """Return a Raster instance that represents a saved dataset."""

    raster = models.Raster.objects.create()
    raster.add(dataset, block_size=(512, 512))

    return raster


def get_result_by_presentationlayer(presentation_layer):
    """Return a presentation layer's result, IF it has either a raster
    or an animation."""
    results = presentation_layer.results()
    if not results:
        return None

    result = results[0]

    if not result.raster and not result.animation:
        return None

    return result


def settings_for_animation(animation):
    """{
        "rec": {
            "width": 841,
            "gridsize": 50,
            "bounds": {
                "west": 185300.0,
                "east": 227350.0,
                "north": 539350.0,
                "projection": 28992,
                "south": 501200.0},
            "height": 763
        },
        "anim": {},
        "default_legend": {
            "id": 11, "name": "max. waterdiepte overstr. gebied"},
        "legends": [{"id": 11, "name": "max. waterdiepte overstr. gebied"}]}
    """

    return {
        'rec': {
            'bounds': animation.bounds,
            'width': animation.cols,
            'gridsize': animation.gridsize,
            'height': animation.rows,
            },
        'anim': {
            'firstnr': 0,
            'lastnr': animation.frames - 1,
            'options': {'startnr': 0},
            },
        "default_legend": {
            "id": 21,
            "name": "anim. waterdiepte (fls_h)"
            },
        "legends": [{"id": 21, "name": "anim. waterdiepte (fls_h)"}]
        }


def values_in_range(maxvalue, n):
    """Divide interval (0, maxvalue) into n equal size subintervals and
    return values in the middle of each subinterval"""
    subintervalsize = maxvalue / n
    return [
        (i + 0.5) * subintervalsize
        for i in range(n)]


def rgba_to_html(rgba):
    r, g, b, _ = rgba

    return "#%02x%02x%02x" % rgba[:3]


def result_legend(result, presentationlayer, colormap=None, maxvalue=None):
    presentationtype = presentationlayer.presentationtype

    default_colormap, default_maxvalue = presentationtype.colormap_info

    try:
        maxvalue = float(maxvalue)
    except (ValueError, TypeError):
        maxvalue = default_maxvalue

    if colormap is None:
        colormap = default_colormap

    cmap = cm.get_cmap(colormap)
    arr = np.array(values_in_range(maxvalue, 10))
    # Color the way that the grids are colored
    normalize = colors.Normalize(vmin=0, vmax=maxvalue)
    rgba = cmap(normalize(arr), bytes=True)

    legend = [
        (arr[i], rgba_to_html(tuple(rgba[i])))
        for i in range(10)
        ]

    return {
        'title': unicode(presentationtype),
        'content': legend,
        'colormaps': models.Colormap.colormaps(),
        'active_colormap': colormap,
        'current_maxvalue': maxvalue,
        }
