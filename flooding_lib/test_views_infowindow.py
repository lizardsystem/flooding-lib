"""Tests for views_inforwindow.py."""

import factory
import mock

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

import flooding_lib.coordinates

from flooding_lib.tools.importtool import models as importmodels
from flooding_lib.test_models import ScenarioF
from flooding_lib import models

from flooding_lib.views_infowindow import find_imported_value
from flooding_lib.views_infowindow import display_string


class FakeObject(object):
    """Object with some attributes"""
    def __init__(self, **kwargs):
        for attribute, value in kwargs.iteritems():
            setattr(self, attribute, value)


class ExtraInfoFieldF(factory.Factory):
    FACTORY_FOR = models.ExtraInfoField

    name = 'dummy'
    use_in_scenario_overview = True
    header = models.ExtraInfoField.HEADER_SCENARIO
    position = 0


class ExtraScenarioInfoF(factory.Factory):
    FACTORY_FOR = models.ExtraScenarioInfo

    extrainfofield = ExtraInfoFieldF(name='forextrascenarioinfo')
    scenario = FakeObject()
    value = None


class InputFieldF(factory.Factory):
    FACTORY_FOR = importmodels.InputField

    name = 'dummy'
    header = importmodels.InputField.HEADER_SCENARIO
    import_table_field = ''
    destination_table = ''
    destination_field = ''
    type = importmodels.InputField.TYPE_INTEGER
    options = ''
    visibility_dependency_value = ''
    excel_hint = ''
    hover_text = ''
    hint_text = ''
    required = False


class TestFindImportedValue(TestCase):
    def test_get_integer_from_scenario(self):
        scenario = FakeObject(field=3)

        inputfield = InputFieldF.build(
            destination_table='Scenario',
            destination_field='field')

        retvalue = find_imported_value(inputfield, {'scenario': scenario})
        self.assertEquals(retvalue, 3)

    def test_simple_scenario_info(self):
        scenario = ScenarioF.create()
        fieldname = 'test'
        value = 3

        extrainfofield = ExtraInfoFieldF.create(name=fieldname)
        extrascenarioinfo = ExtraScenarioInfoF.create(
            scenario=scenario,
            extrainfofield=extrainfofield,
            value=value)

        inputfield = InputFieldF.build(
            destination_table='ExtraScenarioInfo',
            destination_field=fieldname)

        retvalue = find_imported_value(inputfield, {'scenario': scenario})
        self.assertEquals(retvalue, 3)

    def test_999(self):
        scenario = ScenarioF.create()
        fieldname = 'test'
        value = '-999'

        extrainfofield = ExtraInfoFieldF.create(name=fieldname)
        extrascenarioinfo = ExtraScenarioInfoF.create(
            scenario=scenario,
            extrainfofield=extrainfofield,
            value=value)

        inputfield = InputFieldF.build(
            destination_table='ExtraScenarioInfo',
            destination_field=fieldname,
            type=importmodels.InputField.TYPE_STRING)

        retvalue = find_imported_value(inputfield, {'scenario': scenario})
        self.assertEquals(retvalue, None)

    def test_xy(self):
        WGS_X = 10
        WGS_Y = 20
        RD_X = 110
        RD_Y = 120

        breach = FakeObject(
            geom=FakeObject(
                x=WGS_X, y=WGS_Y))

        inputfieldx = InputFieldF.build(
            name='X coordinaat',
            destination_table='Breach',
            destination_field='geom')
        inputfieldy = InputFieldF.build(
            name='Y coordinaat',
            destination_table='Breach',
            destination_field='geom')

        with mock.patch(
            'flooding_lib.coordinates.wgs84_to_rd',
            return_value=(RD_X,RD_Y)):
            retvaluex = find_imported_value(inputfieldx, {'breach': breach})
            retvaluey = find_imported_value(inputfieldy, {'breach': breach})
            self.assertEquals(retvaluex, RD_X)
            self.assertEquals(retvaluey, RD_Y)


class TestDisplayValueStr(TestCase):
    def test_none(self):
        self.assertEquals(display_string(None, None), '')

    def test_interval(self):
        inputfield = InputFieldF.build(
            type=importmodels.InputField.TYPE_INTERVAL)
        value_str = display_string(inputfield, 2.5)
        self.assertEquals(value_str, '2 d 12:00')


