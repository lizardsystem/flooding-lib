# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.contrib.auth.models import User
from django.test import TestCase, client

from flooding_lib.tests import test_models


class UserTestCase(TestCase):
    def setUp(self):
        self.request_factory = client.RequestFactory()
        self.scenario = test_models.ScenarioF.create()

        self.anonymous_user = User()
        self.superuser = User(is_superuser=True)

    def anon_request(self, url='/'):
        request = self.request_factory.get(url)
        request.user = self.anonymous_user
        return request

    def superuser_request(self, url='/'):
        request = self.request_factory.get(url)
        request.user = self.superuser
        return request
