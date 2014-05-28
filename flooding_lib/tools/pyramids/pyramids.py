# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

""" """

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import logging

import numpy as np
from matplotlib import colors

from flooding_lib.util.colormap import get_mpl_cmap
from flooding_lib.util.colormap import ColorMap
from flooding_lib.tools.importtool.models import InputField

from . import models

INPUTFIELD_STARTMOMENT_BREACHGROWTH_ID = 9

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


def settings_for_animation(animation, scenario=None):
    startnr = 0

    if scenario is not None:
        # See if the scenario has a "startmoment bresgroei", use
        # that as the start frame.
        inputfield = InputField.objects.get(
            pk=INPUTFIELD_STARTMOMENT_BREACHGROWTH_ID)
        startmoment_days = scenario.value_for_inputfield(inputfield)
        startmoment_hours = int(startmoment_days * 24 + 0.5)

        if startmoment_hours > 0:
            startnr = startmoment_hours

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
            'options': {'startnr': startnr},
            },
        "default_legend": {
            "id": 21,
            "name": "Dummy"
            },
        "legends": [{"id": 21, "name": "Dummy"}]
        }


def values_in_range(maxvalue, n):
    """Divide interval (0, maxvalue) into n equal size subintervals and
    return values in the middle of each subinterval"""
    subintervalsize = maxvalue / n
    return [
        (i + 0.5) * subintervalsize
        for i in range(n)]


def rgba_to_html(rgba):
    return "#%02x%02x%02x" % rgba[:3]


def result_legend(result, presentationlayer, colormap=None, maxvalue=None):
    presentationtype = presentationlayer.presentationtype

    default_colormap, default_maxvalue = presentationtype.colormap_info(
        project=result.scenario.main_project)

    try:
        maxvalue = float(maxvalue)
    except (ValueError, TypeError):
        maxvalue = default_maxvalue

    if colormap is None:
        colormap = default_colormap

    if not colormap.endswith('.csv'):
        show_maxvalue = True
        # Matplotlib colormap -- use given maxvalue, and always do 10 steps
        cmap = get_mpl_cmap(colormap)
        arr = np.array(values_in_range(maxvalue, 10))
        # Color the way that the grids are colored
        normalize = colors.Normalize(vmin=0, vmax=maxvalue)
        rgba = cmap(normalize(arr), bytes=True)

        legend = [
            (arr[i], rgba_to_html(tuple(rgba[i])))
            for i in range(10)
            ]
    else:
        # Our own .csv colormaps.
        show_maxvalue = False
        cmap = ColorMap(colormap)
        legend = [
            (value, rgba_to_html(cmap.value_to_color(value)))
            for value in cmap.legend_values()
            ]

    return {
        'title': unicode(presentationtype),
        'content': legend,
        'colormaps': models.Colormap.colormaps(),
        'active_colormap': colormap,
        'current_maxvalue': maxvalue,
        'show_maxvalue': show_maxvalue,
        }
