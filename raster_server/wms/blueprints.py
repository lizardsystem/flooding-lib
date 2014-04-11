# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import flask
from matplotlib import cm

from raster_server import blueprints
from raster_server import colors
from raster_server import utils

from raster_server.wms import responses

colors.add_cmap_shade(name='hill', ctr=0.7)
colors.add_cmap_shade(name='shade', ctr=0.5)
colors.add_cmap_transparent(name='transparent')
colors.add_cmap_drought(name='drought')
colors.add_cmap_damage(name='damage')
colors.add_cmap_landuse(name='landuse')
colors.add_cmap_landuse_beira(name='landuse_beira')

blueprint = blueprints.Blueprint(name=__name__.split('.')[-2],
                                 import_name=__name__,
                                 static_folder='static',
                                 template_folder='templates')


@blueprint.route('')
def wms():
    """ Return response according to request. """
    get_parameters = utils.get_parameters()
    if 'crs' in get_parameters:
        get_parameters.update(srs=get_parameters['crs'])
    request = get_parameters['request'].lower()

    request_handlers = dict(
        getmap=responses.get_response_for_getmap,
        getcurves=responses.get_response_for_getcurves,
        getcounts=responses.get_response_for_getcounts,
        getlimits=responses.get_response_for_getlimits,
        getfeatureinfo=responses.get_response_for_getfeatureinfo,
        getcapabilities=responses.get_response_for_getcapabilities,
    )
    return request_handlers[request](get_parameters=get_parameters)


@blueprint.route('/demo')
def demo():
    layers = sorted(utils.get_layers())
    styles = sorted(cm.cmap_d.keys())
    return flask.render_template(
        'wms/demo.html',
        layers=layers,
        styles=styles,
    )
