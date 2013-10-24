# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

""" """

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
import shutil
import tempfile

import gdal

from django.test import TestCase

from flooding_lib.tools import pyramids

# There is an ASCII in this directory that we use for testing
ASCII_FILENAME = os.path.join(os.path.dirname(__file__), 'dm1maxd0.asc')


class TestSaveDatasetAsPyramid(TestCase):
    def setUp(self):
        self.data_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.data_dir)

    def test_creates_pyramid_from_ascii(self):
        dataset = gdal.Open(ASCII_FILENAME)

        with self.settings(PYRAMIDS_BASE_DIR=self.data_dir):
            pyramids.save_dataset_as_pyramid(dataset)

        self.assertEquals(len(os.listdir(self.data_dir)), 1)
