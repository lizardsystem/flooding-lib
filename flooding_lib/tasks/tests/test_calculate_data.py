# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Tests for calculate_export_data."""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division


import csv
import os
import shutil
import tempfile

from django.test import TestCase

from flooding_lib.tasks import calculate_export_data


class TestWriterow(TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_writing_unicode(self):
        """Just check that no exception is raised."""
        csvfile = os.path.join(self.directory, 'test.csv')
        writer = csv.writer(open(csvfile, 'wb'), delimiter=b"|")

        calculate_export_data.writerow(
            writer, ["o", b"o", b"ö", "ö", 3])
