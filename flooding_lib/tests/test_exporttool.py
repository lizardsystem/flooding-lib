# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import os

from django.test import TestCase
from flooding_lib.tests import test_models


class TestCalculateExportMapsTask(TestCase):
    def test_generate_dst_filename(self):
        test_models.ExporttoolSettingF.create(
            key='EXPORT_FOLDER', value='/tmp')

        export_run = test_models.ExportRunF.build()
        export_name = export_run.name[:20].replace(' ', '_')
        extention = 'zip'
        dst_filename = export_run.generate_dst_path()
        self.assertTrue(dst_filename.endswith(extention))
        self.assertTrue(dst_filename.startswith('/tmp'))
        self.assertTrue(os.path.basename(dst_filename)
                        .startswith(export_name))
