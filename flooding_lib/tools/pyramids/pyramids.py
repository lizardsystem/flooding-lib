# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

""" """

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import uuid

from gislib import pyramids

from . import models


def save_dataset_as_pyramid(dataset):
    """Return a Raster instance that represents a saved dataset."""

    unique_id = uuid.uuid4()
    raster = models.Raster(uuid=unique_id)

    pyramid = pyramids.Pyramid(path=raster.pyramid_path)
    pyramid.add(dataset, blocksize=(512, 512))

    raster.save()
    return raster
