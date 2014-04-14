# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from flask import jsonify, request, abort

from raster_server import blueprints

from raster_server.data import config
from raster_server.data import responses


rasterapp = blueprints.Blueprint(name=config.BLUEPRINT_NAME,
                                 import_name=__name__)


@rasterapp.route('/')
def index():
    return '<h1>Rasterinfo</h1><a href="profile">Profile tool</a>'


@rasterapp.route('/profile', methods=['GET'])
def rasterprofile():
    """
    Return json with [distance, raster values] according to request.

    Example:
    run Flask dev server on localhost and go to
    ``http://127.0.0.1:5000/rasterinfo/profile?geom=LINESTRING(570060.51753709%206816367.7101946,568589.10474281%206815374.028827)&srs=EPSG:900913``
    """
    if not 'srs' in request.values or 'geom' not in request.values:
        abort(400)
    src_srs = request.values['srs']
    wktline = request.values['geom']
    profile = responses.get_profile(wktline, src_srs)
    return jsonify(profile=profile)
