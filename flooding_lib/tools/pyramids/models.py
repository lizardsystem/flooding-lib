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

import os

from django.conf import settings
from django.db import models
from django_extensions.db.fields import UUIDField

from gislib import pyramids

SUBDIR_DEPTH = 6  # Number of characters of a UUID to use as directories


class Raster(models.Model):
    uuid = UUIDField(unique=True)

    def uuid_parts(self):
        chars = unicode(self.uuid)
        return (
            list(chars[:SUBDIR_DEPTH]) + [chars[SUBDIR_DEPTH:]])

    @property
    def pyramid_path(self):
        pyramid_base_dir = getattr(
            settings, 'PYRAMIDS_BASE_DIR',
            os.path.join(settings.BUILDOUT_DIR, 'var', 'pyramids'))

        return os.path.join(pyramid_base_dir, *self.uuid_parts())

    @property
    def pyramid(self):
        return pyramids.Pyramid(path=self.pyramid_path)

    @property
    def layer(self):
        return ':'.join(self.uuid_parts())

    def add(self, dataset, **kwargs):
        defaults = {
            'tilesize': (1024, 1024),
            'blocksize': (256, 256)
            }
        defaults.update(kwargs)

        self.pyramid.add(dataset, **defaults)


class Animation(models.Model):
    """Animations are stored in UUID-based directories, just like
    Rasters, but with one subdirectory per animation frame."""
    uuid = UUIDField(unique=True)
    frames = models.IntegerField(default=0)

    def uuid_parts(self):
        chars = unicode(self.uuid)
        return (
            list(chars[:SUBDIR_DEPTH]) + [chars[SUBDIR_DEPTH:]])

    def pyramid_path(self, frame_nr):
        """Frame_nr starts at 1."""
        if not (1 <= frame_nr <= self.frames):
            raise ValueError(
                "frame_nr ({}) outside of range [1, {}]."
                .format(frame_nr, self.frames))

        pyramid_base_dir = getattr(
            settings, 'PYRAMIDS_BASE_DIR',
            os.path.join(settings.BUILDOUT_DIR, 'var', 'pyramids'))

        return os.path.join(
            pyramid_base_dir,
            os.path.join(*self.uuid_parts()),
            str(frame_nr))

    def pyramid(self, frame_nr):
        """Frame_nr starts at 1."""
        return pyramids.Pyramid(path=self.pyramid_path(frame_nr))

    def layer(self, frame_nr):
        return ':'.join(self.uuid_parts() + [str(frame_nr)])

    def add(self, dataset, **kwargs):
        """Adds a new frame, increases frame number."""
        self.frames += 1

        defaults = {
            'tilesize': (1024, 1024),
            'blocksize': (256, 256)
            }
        defaults.update(kwargs)

        self.pyramid(self.frames).add(dataset, **defaults)
        self.save()  # Save increased frames counter
