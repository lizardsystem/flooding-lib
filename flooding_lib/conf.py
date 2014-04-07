# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Use AppConf to store sensible defaults for settings. This also documents the
settings that lizard_damage defines. Each setting name automatically has
"LIZARD_DAMGE_" prepended to it.

By puttng the AppConf in this module and importing the Django settings
here, it is possible to import Django's settings with `from
lizard_damage.conf import settings` and be certain that the AppConf
stuff has also been loaded."""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os

from django.conf import settings
settings  # Pyflakes...

from appconf import AppConf


class MyAppConf(AppConf):
    COLORMAP_DIR = os.path.join(
        settings.FLOODING_SHARE, 'colormaps')
