# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import importlib

import flask

from raster_server import settings

blueprints = []


def get_blueprints():
    """
    Return blueprint classes.

    This is done by importing the blueprint modules. If the modules
    instantiate the Blueprint class defined here, they are automatically
    added to the blueprints attribute of this module.
    """
    for module in settings.BLUEPRINTS:
        importlib.import_module(module)
    return blueprints


class Blueprint(flask.Blueprint):
    """ This version of the flask Blueprint tracks all blueprint instances. """
    def __init__(self, *args, **kwargs):
        """ Automatically registers blueprints. """
        super(Blueprint, self).__init__(*args, **kwargs)
        blueprints.append(self)
