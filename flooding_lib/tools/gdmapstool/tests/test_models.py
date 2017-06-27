# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

""" """

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from datetime import datetime

from django.test import TestCase

from . import factories
from flooding_lib.tests.test_models import ScenarioF


class TestGDMap(TestCase):

    def test_gd_map(self):
        scenario1 = ScenarioF()
        scenario2 = ScenarioF()
        scenario3 = ScenarioF()
        gdmap = factories.GDMapF.create(scenarios=(
            scenario1, scenario2, scenario3))
        self.assertEquals(gdmap.scenarios.count(), 3)
