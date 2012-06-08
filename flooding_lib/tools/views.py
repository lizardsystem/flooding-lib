from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _

from django.conf import settings


def index(request):
    """Renders Lizard-flooding tools index page."""
    return render_to_response('tools/index.html',
                               {'breadcrumbs': [{'name':_('Flooding')}],
                               'user': request.user,
                               'LANGUAGES': settings.LANGUAGES,}
                            )
