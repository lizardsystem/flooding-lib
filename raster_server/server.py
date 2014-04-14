# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import logging
import sys

import flask

from raster_server import blueprints

logger = logging.getLogger(__name__)

# App
app = flask.Flask(__name__)

# Register the blueprints
for blueprint in blueprints.get_blueprints():
    url_prefix = '/' + blueprint.name
    app.register_blueprint(blueprint, url_prefix=url_prefix)


@app.route('/')
def hello():
    return flask.redirect('/wms/demo')


# argv=None is needed because Buildout sometimes adds args
def run(argv=None):
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    app.run(host='0.0.0.0', debug=True)
