# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import io
import json

from matplotlib import cm
from matplotlib import colors
from PIL import Image
import flask
import numpy as np

from gislib import projections
from gislib import statistics
from gislib.utils import get_transformed_extent

from flooding_lib.util.colormap import get_mpl_cmap

from raster_server import settings
from raster_server import utils
from raster_server.wms import effects

LANDUSE = {
    1: '1 - BAG - Overig / Onbekend',
    2: '2 - BAG - Woonfunctie',
    3: '3 - BAG - Celfunctie',
    4: '4 - BAG - Industriefunctie',
    5: '5 - BAG - Kantoorfunctie',
    6: '6 - BAG - Winkelfunctie',
    7: '7 - BAG - Kassen',
    8: '8 - BAG - Logiesfunctie',
    9: '9 - BAG - Bijeenkomstfunctie',
    10: '10 - BAG - Sportfunctie',
    11: '11 - BAG - Onderwijsfunctie',
    12: '12 - BAG - Gezondheidszorgfunctie',
    13: '13 - BAG - Overig kleiner dan 50 m2<br />(schuurtjes)',
    14: '14 - BAG - Overig groter dan 50 m2<br />(bedrijfspanden)',
    15: '15 - BAG - None',
    16: '16 - BAG - None',
    17: '17 - BAG - None',
    18: '18 - BAG - None',
    19: '19 - BAG - None',
    20: '20 - BAG - None',
    21: '21 - Top10 - Water',
    22: '22 - Top10 - Primaire wegen',
    23: '23 - Top10 - Secundaire wegen',
    24: '24 - Top10 - Tertiaire wegen',
    25: '25 - Top10 - Bos/Natuur',
    26: '26 - Top10 - Bebouwd gebied',
    27: '27 - Top10 - Boomgaard',
    28: '28 - Top10 - Fruitkwekerij',
    29: '29 - Top10 - Begraafplaats',
    30: '30 - Top10 - Agrarisch gras',
    31: '31 - Top10 - Overig gras',
    32: '32 - Top10 - Spoorbaanlichaam',
    33: '33 - Top10 - None',
    34: '34 - Top10 - None',
    35: '35 - Top10 - None',
    36: '36 - Top10 - None',
    37: '37 - Top10 - None',
    38: '38 - Top10 - None',
    39: '39 - Top10 - None',
    40: '40 - Top10 - None',
    41: '41 - LGN - Agrarisch Gras',
    42: '42 - LGN - Mais',
    43: '43 - LGN - Aardappelen',
    44: '44 - LGN - Bieten',
    45: '45 - LGN - Granen',
    46: '46 - LGN - Overige akkerbouw',
    47: '47 - LGN - None',
    48: '48 - LGN - Glastuinbouw',
    49: '49 - LGN - Boomgaard',
    50: '50 - LGN - Bloembollen',
    51: '51 - LGN - None',
    52: '52 - LGN - Gras overig',
    53: '53 - LGN - Bos/Natuur',
    54: '54 - LGN - None',
    55: '55 - LGN - None',
    56: '56 - LGN - Water (LGN)',
    57: '57 - LGN - None',
    58: '58 - LGN - Bebouwd gebied',
    59: '59 - LGN - None',
    61: '61 - CBS - Spoorwegen terrein',
    62: '62 - CBS - Primaire wegen',
    63: '63 - CBS - Woongebied',
    64: '64 - CBS - Winkelgebied',
    65: '65 - CBS - Bedrijventerrein',
    66: '66 - CBS - Sportterrein',
    67: '67 - CBS - Volkstuinen',
    68: '68 - CBS - Recreatief terrein',
    69: '69 - CBS - Glastuinbouwterrein',
    70: '70 - CBS - Bos/Natuur',
    71: '71 - CBS - Begraafplaats',
    72: '72 - CBS - Zee',
    73: '73 - CBS - Zoet water',
    74: '74 - CBS - None',
    75: '75 - CBS - None',
    76: '76 - CBS - None',
    77: '77 - CBS - None',
    78: '78 - CBS - None',
    79: '79 - CBS - None',
    97: '97 - Overig - buitenland',
    98: '98 - Top10 - erf',
    99: '99 - Overig - Overig/Geen landgebruik'
}


SWAP = 'epsg:4326',

CAPABILITIES = ('epsg:3857',
                'epsg:4326',
                'epsg:28992')


def jsonify(content):
    """ Return flask response tuple for json with some headers. """
    return json.dumps(content), 200, {
        'content-type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET'
    }


def float_or_none(string):
    """ Return float or None. """
    try:
        return float(string)
    except ValueError:
        return None


def merge(images):
    """
    Return a pil image.

    Merge a list of pil images with equal sizes top down based on
    the alpha channel.
    """
    def paste(image1, image2):
        image = image2.copy()
        mask = Image.fromarray(np.array(image1)[:, :, 3])
        rgb = Image.fromarray(np.array(image1)[:, :, 0:3])
        image.paste(rgb, None, mask)
        return image

    return reduce(paste, images)


def get_geometry(bbox, width, height,
                 srs=None, crs=None, version='1.1.1', **kwargs):
    """
    Return dictionary.

    Input wms parameters are handled according to wms version. Dictionary
    can be used as kwargs for the get_data function.
    """
    size = int(width), int(height)
    extent = map(float, bbox.split(','))

    if version == '1.1.1':
        crs = srs
    else:
        if crs.lower() in SWAP:
            extent = extent[1], extent[0], extent[3], extent[2]

    wkt = ('POLYGON (({x1} {y1},{x2} {y1},'
           '{x2} {y2},{x1} {y2},{x1} {y1}))').format(x1=extent[0],
                                                     y1=extent[1],
                                                     x2=extent[2],
                                                     y2=extent[3])
    return dict(wkt=wkt, crs=crs, size=size)


def get_data(layer, geometry):
    """ Return numpy array. """
    pyramid = utils.get_pyramid(layer)
    return pyramid.get_data(**geometry)[0]


def get_image(data, style):
    """ Return PIL image. """
    parts = style.split(':')
    colormap = get_mpl_cmap(
        parts[0] if parts[0] else 'jet',
        settings_module=settings)

    if isinstance(colormap, colors.ListedColormap):
        normalize = lambda x: x
    if (isinstance(colormap, colors.LinearSegmentedColormap) and
        hasattr(colormap, 'csv_max_value')):
        normalize = lambda x: x / colormap.csv_max_value
    else:
        normalize = colors.Normalize(*map(float_or_none, parts[1:]), clip=True)
    rgba = colormap(normalize(data), bytes=True)
    return Image.fromarray(rgba)


def get_response_for_getmap(get_parameters):
    """ Return png image. """
    # Retrieve data
    geometry = get_geometry(**get_parameters)
    layers = get_parameters['layers'].split(',')
    data = tuple(get_data(l, geometry) for l in layers)

    # Prepare images
    images = []

    # Effect images
    effect_kwargs = dict(data=data, geometry=geometry)
    effect_list = map(lambda e: e.split(':'),
                      get_parameters.get('effects', '').split(','))
    effect_args = [e[1:] for e in effect_list]
    effect_names = [e[0] for e in effect_list]
    images.extend(getattr(effects, n)(a, **effect_kwargs)
                  for n, a in zip(effect_names, effect_args) if n)

    # Standard images
    styles = get_parameters['styles'].split(',')
    images.extend([get_image(d, s) for d, s in zip(data, styles)])

    # Composite
    buf = io.BytesIO()
    merge(images).save(buf, 'png')

    return buf.getvalue(), 200, {
        'content-type': 'image/png',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET'
    }


def get_response_for_getlimits(get_parameters):
    """ Return json with limits per layer. """
    geometry = get_geometry(**get_parameters)
    layers = get_parameters['layers'].split(',')
    data = tuple(get_data(l, geometry) for l in layers)
    limits = [np.ma.array([d.min(),
                           d.max()]).tolist() for d in data]
    return jsonify(limits)


def get_response_for_getcurves(get_parameters):
    """ Return json with curve coordinates. """
    geometry = get_geometry(**get_parameters)
    layers = get_parameters['layers'].split(',')
    data = tuple(get_data(l, geometry) for l in layers)
    curves = tuple(map(
        lambda d: np.array(statistics.get_curve(d)).transpose().tolist(),
        data,
    ))
    return jsonify(curves)


def get_response_for_getcounts(get_parameters):
    """ Return json with curve coordinates. """
    geometry = get_geometry(**get_parameters)
    layers = get_parameters['layers'].split(',')
    data = tuple(get_data(l, geometry) for l in layers)
    bins = np.arange(0, 256)
    histograms = [np.histogram(d.compressed(), bins)[0] for d in data]
    nonzeros = [h.nonzero() for h in histograms]
    nbins = [bins[:-1][n] for n in nonzeros]
    nhistograms = [h[n] for n, h in zip(nonzeros, histograms)]
    # Determine the ordering
    argsorts = [h.argsort() for h in nhistograms]
    arg10 = [a[:-10:-1] for a in argsorts]
    argrest = [a[-10::-1] for a in argsorts]
    # Use it to group
    rests = [h[argrest].sum() for h, a in zip(nhistograms, argsorts)]
    pairs = [np.array([b[arg10], h[arg10]]).transpose()
             for b, h, a in zip(nbins, nhistograms, argsorts)]
    # Prepare result data
    styles = get_parameters['styles'].split(',')
    colormaps = [
        get_mpl_cmap(s.split(':')[0], settings_module=settings)
        for s in styles]

    result = [[dict(label=LANDUSE.get(b, b),
                    data=d,
                    color=colors.rgb2hex((c(b))))
               for b, d in p.tolist()] for p, c in zip(pairs, colormaps)]

    for r, s in zip(result, rests):
        if s:
            r.append(dict(label='Overig', data=float(s), color='#ffffff'))
    return jsonify(result)


def get_response_for_getfeatureinfo(get_parameters):
    """ Return some featureinfo in json format. """
    geometry = get_geometry(**get_parameters)
    leafno = utils.get_leafno(geometry)
    return jsonify([leafno])


def get_response_for_getcapabilities(get_parameters):
    """ Return xml. """
    site = settings.SITE_NAME
    layers = []
    styles = sorted(cm.cmap_d.keys())

    for layername in get_parameters['layers'].split(','):
        pyramid = utils.get_pyramid(layername)
        projection = pyramid.info['projection']
        extent = pyramid.extent
        bboxes = {projections.get_authority(crs):
                  get_transformed_extent(extent, projection, crs)
                  for crs in CAPABILITIES}
        layers.append(dict(bboxes=bboxes, name=layername))

    return flask.render_template(
        'wms/capabilities.xml',
        layers=layers,
        styles=styles,
        site=site,
    ), 200, {
        'content-type': 'application/xml',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET'
    }
