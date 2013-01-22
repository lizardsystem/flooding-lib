"""Tests for views_inforwindow.py."""

from django.test import TestCase
from django.utils.safestring import SafeString
from django.utils.translation import ugettext as _

from flooding_lib.tests.test_models import BreachF
from flooding_lib.tests.test_models import ExternalWaterF
from flooding_lib.tests.test_models import ScenarioF
from flooding_lib.tests.test_models import ScenarioBreachF
from flooding_lib.tests.test_models import WaterlevelF
from flooding_lib.tests.test_models import WaterlevelSetF
from flooding_lib import models

from flooding_lib.views.infowindow import extra_infowindow_information_fields


class FakeObject(object):
    """Object with some attributes"""
    def __init__(self, **kwargs):
        for attribute, value in kwargs.iteritems():
            setattr(self, attribute, value)


class TestExtraInfowindowInformationFields(TestCase):
    def test_unknown_header(self):
        self.assertEquals(
            len(extra_infowindow_information_fields('unknown_header', None)),
            0)

    def test_scenario(self):
        # Should add scenario ID
        scenario = ScenarioF.create()

        fields = extra_infowindow_information_fields(
            'Scenario', scenario)

        self.assertEquals(len(fields), 1)
        self.assertEquals(fields[0].value_str, str(scenario.id))

    def test_external_water(self):
        # If external water is sea, and the scenariobreach has
        # waterlevels, it should add a link to a externalwater graph
        # image. The string is HTML, so it should be a SafeString. The
        # link depends on the scenariobreach id.

        scenario = ScenarioF.create()

        externalwater = ExternalWaterF.create(
            type=models.ExternalWater.TYPE_SEA)

        breach = BreachF.create(externalwater=externalwater)

        waterlevelset = WaterlevelSetF.create()
        WaterlevelF.create(waterlevelset=waterlevelset)

        scenariobreach = ScenarioBreachF.create(
            scenario=scenario, breach=breach, waterlevelset=waterlevelset)

        fields = extra_infowindow_information_fields(
            _('External Water'), scenario)

        self.assertEquals(len(fields), 1)

        value = fields[0].value_str

        self.assertTrue(isinstance(value, SafeString))
        self.assertTrue('get_externalwater_graph_infowindow' in value)
        self.assertTrue(str(scenariobreach.id) in value)
