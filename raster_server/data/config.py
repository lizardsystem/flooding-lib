
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from raster_server import settings
import os

BLUEPRINT_NAME = 'profile'

DATA_DIR = os.path.join(settings.DATA_DIR, BLUEPRINT_NAME)
PYRAMID_PATH = os.path.join(DATA_DIR, 'pyramid')
