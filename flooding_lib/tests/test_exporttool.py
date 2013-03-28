# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from django.test import TestCase
from flooding_lib.tests import test_models

from flooding_lib.tasks.calculate_export_maps import generate_dst_filename


class TestCalculateExportMapsTask(TestCase):

    def test_generate_dst_filename(self):
        export_run = test_models.ExportRunF.build()
        export_name = export_run.name[:20].replace(' ', '_')
        extention = 'zip'
        dst_filename = generate_dst_filename(export_run)
        self.assertTrue(dst_filename.endswith(extention))
        self.assertTrue(dst_filename.startswith(export_name))
