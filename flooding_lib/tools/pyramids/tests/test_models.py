from django.test import TestCase

from flooding_lib.tools.pyramids import models


class TestRaster(TestCase):
    def test_parts(self):
        raster = models.Raster(
            uuid='4a802ad90241447495dcf93e01915b86')
        self.assertEquals(
            raster.uuid_parts(),
            ['4', 'a', '8', '0', '2', 'a', 'd90241447495dcf93e01915b86']
            )
