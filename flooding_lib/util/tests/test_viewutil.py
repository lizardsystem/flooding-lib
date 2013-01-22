# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from django.http import Http404
from django.test import TestCase, client
from flooding_lib.util import viewutil


class TestServeFile(TestCase):
    def setUp(self):
        self.request_factory = client.RequestFactory()

    def test_works(self):
        request = self.request_factory.get('/')

        # /dirname/file.txt doesn't exist, so static.serve raises
        # Http404
        self.assertRaises(Http404, lambda: viewutil.serve_file(
                request, '/dirname', 'file.txt', '/nginx/', debug=True))

        # With debug=False, the response object should be interesting
        response = viewutil.serve_file(
            request, '/dirname', 'file.txt', '/nginx/', debug=False)

        # Empty content type
        self.assertEquals('', response['Content-Type'])
        # Apache URL
        self.assertEquals('/dirname/file.txt', response['X-Sendfile'])
        # Nginx URL
        self.assertEquals('/nginx/file.txt', response['X-Accel-Redirect'])
        # 200 = OK
        self.assertEquals(200, response.status_code)

    def test_with_debug_none_for_coverage(self):
        request = self.request_factory.get('/')
        try:
            # May or may not raise an exception depending on settings.DEBUG...
            viewutil.serve_file(
                request, '/dirname', 'file.txt', '/nginx/', debug=None)
        except Http404:
            pass
