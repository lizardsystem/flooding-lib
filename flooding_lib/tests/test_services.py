# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import json

from django.http import Http404
from django.test import TestCase, client

from flooding_lib import services
from flooding_lib import models
from flooding_lib.tests import test_models
from flooding_lib.tests import utils


class TestService(TestCase):
    def setUp(self):
        self.request_factory = client.RequestFactory()

    def test_no_action_raises_404(self):
        self.assertRaises(Http404, lambda: services.service(
                self.request_factory.get('/service')))

    def test_unknown_action_raises_404(self):
        self.assertRaises(Http404, lambda: services.service(
            self.request_factory.get('/service?action=whooptidoo')))


class TestServiceGetResultsFromScenario(utils.UserTestCase):
    def test_anon_no_access(self):
        self.assertRaises(
            Http404,
            lambda: services.service_get_results_from_scenario(
                self.anon_request(), self.scenario.id))

    def test_superuser_access(self):
        response = services.service_get_results_from_scenario(
            self.superuser_request(), self.scenario.id)

        self.assertEquals(response.status_code, 200)
        # Check if correct JSON - but it isn't...
#        j = json.loads(response.content)
#        self.assertEquals(j, '')


class TestServiceGetScenarioTree(utils.UserTestCase):
    def test_scenario_that_is_in_two_projects_shows_up_in_both(self):
        breach = test_models.BreachF.create()
        project1 = test_models.ProjectF.create(
            name="hoofdproject", friendlyname="hoofdproject")
        project2 = test_models.ProjectF.create(
            name="ror", friendlyname="ror")

        scenario = test_models.ScenarioF.create()
        scenario.set_project(project1)
        project2.add_scenario(scenario)

        scenario.status_cache = models.Scenario.STATUS_APPROVED
        scenario.save()

        test_models.ScenarioBreachF.create(
            scenario=scenario,
            breach=breach)

        response = services.service_get_scenario_tree(
            self.superuser_request(),
            breach.id,
            filter_onlyprojectswithscenario=True,
            filter_scenariostatus=[
                models.Scenario.STATUS_DISAPPROVED,
                models.Scenario.STATUS_APPROVED,
                models.Scenario.STATUS_CALCULATED])
        self.assertEquals(response.status_code, 200)

        j = json.loads(response.content)

        # Check that each root element (parentid None) has children,
        # and each child has a parent.
        projectids = set()
        parentprojects = set()
        names = set()
        for node in j:
            if 'pid' in node:
                projectids.add(node['pid'])
                names.add(node['name'])
            elif 'sid' in node:
                parentprojects.add(node['parentid'])

        self.assertTrue(project1.id in projectids)
        self.assertTrue(project2.id in projectids)
        self.assertTrue(project1.id in parentprojects)
        self.assertTrue(project2.id in parentprojects)
        self.assertTrue("hoofdproject" in names)
        self.assertTrue("ror" in names)
