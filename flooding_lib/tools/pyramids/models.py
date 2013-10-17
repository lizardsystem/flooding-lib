# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Models for the flooding_lib.tools.pyramids app. We store grids and
animations using gislib's pyramids, so that they can be served as WMS
by raster-server. These models keep track of what went where."""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from django.db import models
from django_extensions.db.fields import UUIDField

SUBDIR_DEPTH = 6  # Number of characters of a UUID to use as directories


class Raster(models.Model):
    uuid = UUIDField(unique=True)

    def uuid_parts(self):
        return (
            list(self.uuid[:SUBDIR_DEPTH]) + [self.uuid[SUBDIR_DEPTH:]])

