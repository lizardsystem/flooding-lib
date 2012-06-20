import factory
import mock

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from flooding_lib import models


class FakeObject(object):
    """Object with some attributes"""
    def __init__(self, **kwargs):
        for attribute, value in kwargs.iteritems():
            setattr(self, attribute, value)


class ContentTypeF(factory.Factory):
    FACTORY_FOR = ContentType


class AttachmentF(factory.Factory):
    FACTORY_FOR = models.Attachment

    content_type = ContentTypeF.create()
    object_id = 1


class TestHelperFunctions(TestCase):
    def testColorToHex_CorrectInput(self):
        self.assertEquals(
            "#00FF00",
            models.convert_color_to_hex((0, 255, 0)))

    def testAttachmentPath_CorrectInput(self):
        instance = FakeObject(
            content_type = u'test_content_type',
            object_id = 1234)

        self.assertEquals(
            'attachments/test_content_type/1234/filename.zip',
            models.get_attachment_path(instance, 'filename.zip'))


class TestAttachment(TestCase):
    def testFilename(self):
        path = 'some/path/with/several.periods.txt'
        filename = 'several.periods.txt'

        attachment = AttachmentF()
        attachment.file = FakeObject(name=path)

        self.assertEquals(
            attachment.filename, filename)
