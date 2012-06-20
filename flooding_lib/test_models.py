from django.test import TestCase

from flooding_lib import models

class TestHelperFunctions(TestCase):
    def testColorToHex_CorrectInput(self):
        self.assertEquals(
            "#00FF00",
            models.convert_color_to_hex((0, 255, 0)))

    def testAttachmentPath_CorrectInput(self):
        class MockInstance(object):
            content_type = u'test_content_type'
            object_id = 1234

        self.assertEquals(
            'attachments/test_content_type/1234/filename.zip',
            models.get_attachment_path(
                MockInstance(), 'filename.zip'))
