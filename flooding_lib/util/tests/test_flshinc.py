# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

""" """

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase

from flooding_lib.util import flshinc


class TestY0IsSouth(TestCase):
    def test_from_scenario_980(self):
        """Which is an old flshinc scenario"""
        flsh_header = {
            'x0': 115025.0, 'y0': 413025.0, 'dx': 50.0, 'nrows': 540}

        maxwaterdepth_geotransform = (
            115000.0, 50.0, 0.0, 428000.0, 0.0, -50.0)

        self.assertTrue(flshinc.y0_is_south(
                flsh_header, maxwaterdepth_geotransform))

    def test_from_scenario_13782(self):
        """Which is a new flshinc scenario"""
        flsh_header = {
            'dx': 100.0, 'y0': 614950.0, 'x0': 145050.0, 'nrows': 1450}

        maxwaterdepth_geotransform = (
            145000.0, 100.0, 0.0, 615000.0, 0.0, -100.0)

        self.assertFalse(flshinc.y0_is_south(
                flsh_header, maxwaterdepth_geotransform))

    def test_from_scenario_13049(self):
        """Which is a new flshinc scenario"""
        flsh_header = {
            'dx': 50.0, 'y0': 501225.0, 'x0': 185325.0, 'nrows': 841}

        maxwaterdepth_geotransform = (
            185300.0, 50.0, 0.0, 5393500, 0.0, -50.0)

        self.assertTrue(flshinc.y0_is_south(
                flsh_header, maxwaterdepth_geotransform))
