"""Utils for use in views."""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import os
import mimetypes
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

    # Guess content type, set filename
    contenttype, encoding = mimetypes.guess_type(filename)

    response['Content-Type'] = contenttype
    # If the file doesn't exist, we still want to return correct
    # headers so that Nginx can generate a 404. Also for testing...
    filepath = os.path.join(dirname, filename)
    if os.path.exists(filepath):
        # But we can only set content length if it exists.
        response['Content-Length'] = str(
            os.stat(os.path.join(dirname, filename)).st_size)
    response['Content-Disposition'] = (
        'attachment; filename="{}"'.format(filename))
    if encoding is not None:
        response['Content-Encoding'] = encoding

    # Apache
    response['X-Sendfile'] = filepath

    # Nginx
    nginx_path = os.path.join(nginx_dirname, filename)
    response['X-Accel-Redirect'] = nginx_path

    return response
