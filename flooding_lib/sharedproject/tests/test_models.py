# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

""" """

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import mock

from django.test import TestCase

from flooding_lib.sharedproject import models
from flooding_lib.sharedproject.tests import factories
from flooding_lib import models as libmodels
from flooding_lib.tests import test_models


class TestProvince(TestCase):
    def test_province_for_returns_scenarios_province_if_set(self):
        scenario = test_models.ScenarioF.build()
        province = factories.ProvinceFactory.build()
        scenario.ror_province = province

        self.assertTrue(models.Province.province_for(scenario) is province)

    def test_raises_does_not_exist_without_metadata(self):
        scenario = test_models.ScenarioF.build()
        self.assertRaises(
            models.Province.DoesNotExist,
            lambda: models.Province.province_for(scenario))

    def test_returns_owner_if_id_is_in_metadata(self):
        scenario = test_models.ScenarioF.create()
        extrainfofield = test_models.ExtraInfoFieldF.create()
        province = factories.ProvinceFactory.create()

        owner = factories.OwnerFactory.create(
            name="Waterschap Groot Salland",
            province=province)

        with mock.patch(
            'flooding_lib.sharedproject.models.OWNER_EXTRAINFOFIELD_ID',
            extrainfofield.id):
            test_models.ExtraScenarioInfoF.create(
                extrainfofield=extrainfofield,
                scenario=scenario,
                value=str(owner.id))

            self.assertEquals(
                models.Province.province_for(scenario),
                province)

    def test_returns_owner_if_name_is_in_metadata(self):
        scenario = test_models.ScenarioF.create()
        extrainfofield = test_models.ExtraInfoFieldF.create()
        province = factories.ProvinceFactory.create()

        factories.OwnerFactory.create(
            name="Waterschap Groot Salland",
            province=province)

        with mock.patch(
            'flooding_lib.sharedproject.models.OWNER_EXTRAINFOFIELD_ID',
            extrainfofield.id):
            test_models.ExtraScenarioInfoF.create(
                extrainfofield=extrainfofield,
                scenario=scenario,
                value="Waterschap Groot Salland")

            self.assertEquals(
                models.Province.province_for(scenario),
                province)

