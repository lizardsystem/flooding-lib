# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from django.http import Http404
from django.test import TestCase, client

from flooding_lib import services


class TestService(TestCase):
    def setUp(self):
        self.request_factory = client.RequestFactory()

    def test_no_action_raises_404(self):
        self.assertRaises(Http404, lambda: services.service(
                self.request_factory.get('/service')))

    def test_unknown_action_raises_404(self):
        self.assertRaises(Http404, lambda: services.service(
            self.request_factory.get('/service?action=whooptidoo')))
