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

import logging
import os
import shutil

from matplotlib import colors
import Image
from osgeo import gdal
import numpy as np

from django.conf import settings
from django.db import models
from django_extensions.db.fields import UUIDField
from django_extensions.db.fields.json import JSONField

from gislib import pyramids

from flooding_lib.util.colormap import get_mpl_cmap


logger = logging.getLogger(__name__)

SUBDIR_DEPTH = 6  # Number of characters of a UUID to use as directories

LIMIT = 0.01  # Values below this are considered to be zero / nodata


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

        # Ensure bytestring
        return (
            os.path.join(pyramid_base_dir, *self.uuid_parts()).encode('utf8'))

    @property
    def pyramid(self):
        return pyramids.Pyramid(path=self.pyramid_path)

    @property
    def layer(self):
        return ':'.join(self.uuid_parts())

    def add(self, dataset, **kwargs):
        defaults = {
            'raster_size': (1024, 1024),
            'block_size': (256, 256)
            }
        defaults.update(kwargs)

        self.pyramid.add(dataset, **defaults)

    def delete(self):
        super(Raster, self).delete()

        # Delete pyramid
        try:
            if os.path.exists(self.pyramid_path):
                shutil.rmtree(self.pyramid_path)
        except Exception as e:
            logger.debug("EXCEPTION IN DELETE: {}".format(e))


class Animation(models.Model):
    """We don't store animations in pyramids anymore, but as
    individual geotiffs.  Filenames are of the form 'dataset0001.tiff'
    and they are stored in the results directory (same place as the
    old .pngs).

    This model keeps metadata of the animation. We _assume_ all frames
    are RD projection (28992).

    XXX: This model COULD track the start frame as well, and it should
    be based on the scenario's "Startmoment bresgroei". But right now
    it doesn't, so it has to be looked up in the scenario."""

    frames = models.IntegerField(default=0)
    cols = models.IntegerField(default=0)
    rows = models.IntegerField(default=0)
    maxvalue = models.FloatField(null=True, blank=True)
    geotransform = JSONField()
    basedir = models.TextField()

    def get_dataset_path(self, i):
        if not (0 <= i < self.frames):
            raise ValueError(
                "i must be a valid frame number, is {}, num frames is {}."
                .format(i, self.frames))

        return os.path.join(
            self.basedir.encode('utf8'), b'dataset{:04d}.tiff'.format(i))

    @property
    def bounds(self):

        x0, dxx, dxy, y0, dyx, dyy = self.geotransform['geotransform']

        # Note that JSONField returns Decimals, not floats...
        answer = {
            'west': float(x0),
            'east': float(x0 + self.cols * dxx),
            'north': float(y0),
            'south': float(y0 + self.rows * dyy),
            'projection': 28992,
        }
        if 'projection' in self.geotransform:
            answer['projection'] = self.geotransform['projection']
        return answer

    @property
    def gridsize(self):
        # Assume square pixels, that is, dxx == dyy == gridsize
        return float(self.geotransform['geotransform'][1])  # dxx

    def __unicode__(self):
        return "{} frames in {}".format(self.frames, self.basedir)

    def save_image_to_response(
            self, response, framenr=0,
            colormap=None, maxvalue=None):
        if colormap is None:
            colormap = 'PuBu'
        if maxvalue is None:
            maxvalue = self.maxvalue

        dataset = gdal.Open(self.get_dataset_path(framenr))
        colormap = get_mpl_cmap(colormap)

        # Colormaps from CSVs have a fixed maxvalue, which is in the
        # attribute 'csv_max_value'.
        maxvalue = getattr(colormap, 'csv_max_value', maxvalue)

        # Get data as masked array
        data = np.ma.masked_less(
            dataset.GetRasterBand(1).ReadAsArray(), LIMIT, copy=False)

        # Normalize
        normalize = colors.Normalize(vmin=0, vmax=maxvalue, clip=True)

        # Apply colormap
        rgba = colormap(normalize(data), bytes=True)

        # Turn into PIL image
        image = Image.fromarray(rgba)

        # Save into response
        response['Content-type'] = 'image/png'
        image.save(response, 'png')

    def get_geotransform(self):
        return [float(g) for g in self.geotransform['geotransform']]


class Colormap(models.Model):
    """Available colormaps from matplotlib."""

    matplotlib_name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ('description',)

    def __unicode__(self):
        return "{} ({})".format(self.description, self.matplotlib_name)

    @classmethod
    def colormaps(cls):
        return [
            (colormap.matplotlib_name, colormap.description)
            for colormap in cls.objects.all()]
