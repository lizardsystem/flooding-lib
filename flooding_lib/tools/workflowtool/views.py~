import datetime
import os.path

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson
from django.utils.translation import ugettext as _


def index(request):
    """
    Renders Lizard-flooding page with an overview of all exports

    Optionally provide "?action=get_attachment&path=3090850/zipfiles/totaal.zip"
    """
    if request.method == 'GET':
        action = request.GET.get('action', '')
        if action:
            # TODO execute scenario
            return None

    # if not request.user.is_authenticated():
    #     return HttpResponse(_("No permission to ...")
    has_execute_rights = True

    breadcrumbs = [
        {'name': _('Workflow tool')}]

    return render_to_response('workflow/scenarios_overview.html',
                              {'breadcrumbs': breadcrumbs,
                              'has_execute_rights': has_execute_rights})
