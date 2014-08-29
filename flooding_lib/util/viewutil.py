"""Utils for use in views."""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import os
import platform

from django.conf import settings
from django import http
from django.views import static


def serve_file(request, dirname, filename, nginx_dirname, debug=None):
    """Serve a static file. If running under Linux and not in debug
    mode, let Apache or Nginx serve it, otherwise use Django's static
    serve view."""

    # It's also possible to pass it in for easy testing
    if debug is None:
        debug = settings.DEBUG

    # Sending by webserver only works for Apache and Nginx, under
    # Linux right now. Otherwise and in development, use Django's
    # static serve.
    if debug or not platform.system() == 'Linux':
        return static.serve(
            request, filename, dirname)

    response = http.HttpResponse()

    # Unset the Content-Type as to allow for the webserver
    # to determine it.
    response['Content-Type'] = ''

    # Set filename
    response['Content-Disposition'] = (
        'attachment; filename="{}"'.format(filename))

    # Apache
    response['X-Sendfile'] = os.path.join(dirname, filename)

    # Nginx
    nginx_path = os.path.join(nginx_dirname, filename)
    response['X-Accel-Redirect'] = nginx_path

    return response
