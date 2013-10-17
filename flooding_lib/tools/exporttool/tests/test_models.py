# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

""" """

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division


from django.test import TestCase

from . import factories


class TestExportRun(TestCase):
    def test_selected_maps_default_all(self):
        export_run = factories.ExportRunF()

        self.assertEquals(
            export_run.selected_maps,
            [
                'The maximal waterdepth',
                'The maximal flowvelocity',
                'The flooded area',
                'The arrival times',
                'The period of increasing waterlevel',
                'The sources of inundation'
                ])
