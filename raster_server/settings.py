# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import json
import os

if os.environ.get('RASTER_SERVER_SETTINGS'):
    # This may raise an exception if something is wrong. Since there's
    # nothing we can do to fix that, and running with defaults while the
    # environment variable is set is likely to be useless, let's just
    # crash.
    SETTINGS_FROM_FILE = json.loads(
        open(os.environ.get('RASTER_SERVER_SETTINGS')).read())
else:
    SETTINGS_FROM_FILE = dict()


# Register your backends here
BLUEPRINTS = SETTINGS_FROM_FILE.get('blueprints', [
    'raster_server.wms',
    #'raster_server.tms',
    #'raster_server.data',  # GetLimits, GetProfile, GetExtent, etc.
])

# Directories
BUILDOUT_DIR = SETTINGS_FROM_FILE.get(
    'buildout_dir',
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))


DATA_DIR = SETTINGS_FROM_FILE.get(
    'data_dir',
    os.path.join(BUILDOUT_DIR, 'var', 'data'))

SITE_NAME = SETTINGS_FROM_FILE.get('site_name', "localhost:5000")

FLOODING_SHARE = SETTINGS_FROM_FILE.get(
    'flooding_share')
FLOODING_LIB_COLORMAP_DIR = os.path.join(
    FLOODING_SHARE, 'colormaps')

# Import local settings
try:
    from raster_server.localsettings import *
except ImportError:
    pass
