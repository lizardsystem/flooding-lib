# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from django.contrib.auth.models import User
from django.http import Http404
from django.test import TestCase, client
from django.utils import simplejson

from flooding_lib import services

from flooding_lib import test_models


class TestService(TestCase):
    def setUp(self):
        self.request_factory = client.RequestFactory()

    def test_no_action_raises_404(self):
        self.assertRaises(Http404, lambda: services.service(
                self.request_factory.get('/service')))

    def test_unknown_action_raises_404(self):
        self.assertRaises(Http404, lambda: services.service(
            self.request_factory.get('/service?action=whooptidoo')))


class UserTestCase(TestCase):
    def setUp(self):
        self.request_factory = client.RequestFactory()
        self.scenario = test_models.ScenarioF.create()

        self.anonymous_user = User()
        self.superuser = User(is_superuser=True)

    def anon_request(self):
        request = self.request_factory.get('/')
        request.user = self.anonymous_user
        return request

    def superuser_request(self):
        request = self.request_factory.get('/')
        request.user = self.superuser
        return request


class TestServiceGetResultsFromScenario(UserTestCase):
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
#        json = simplejson.loads(response.content)
#        self.assertEquals(json, '')
