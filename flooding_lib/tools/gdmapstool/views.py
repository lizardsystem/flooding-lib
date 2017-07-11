import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _

from flooding_lib.models import Scenario
from flooding_lib.tools.gdmapstool.forms import GDMapForm
from flooding_lib.tools.gdmapstool.models import GDMapProject, GDMap


def index(request):
    """
    Renders Lizard-flooding page with an overview of all gdmap-projects
    """
    has_edit_rights = False
    has_read_rights = False

    if request.user.has_perm(
            'gdmapstool.change_gdmap'):
        has_edit_rights = True
    elif request.user.is_authenticated():
        has_read_rights = True
    else:
        return HttpResponse(_("No permission."))

    breadcrumbs = [
        {'name': _('GBMap tool')}]

    gd_map_projects = GDMapProject.objects.all()

    return render_to_response(
        'gdmapprojects_overview.html',
        {
            'gd_map_projects': gd_map_projects,
            'breadcrumbs': breadcrumbs,
            'has_edit_rights': has_edit_rights,
            'has_read_rights': has_read_rights
        })


def gdmap_details(request, gdmap_id):
    """
    Renders the page showing the details of the gdmap run
    """

    gdmap = get_object_or_404(GDMap, pk=gdmap_id)
    breadcrumbs = [
        {'name': _('GBMap tool'),
         'url': reverse('flooding_gdmaapstool_index')},
        {'name': _('GBMap detail')}]
    return render_to_response(
        'gdmap_overview.html',
        {'gdmap': gdmap,
         'breadcrumbs': breadcrumbs})


def reuse_gdmap(request, gdmap_id):
    if not (request.user.is_authenticated() and request.user.has_perm(
            'gdmapstool.change_gdmap')):
        return HttpResponse(_("No permission."))

    gdmap = get_object_or_404(GDMap, pk=gdmap_id)
    scenarios = []
    for s in gdmap.scenarios.all():
        scenarios.append(
            {
                'scenario_id': s.id,
                'scenario_name': s.name,
                'project_id': s.main_project.id,
                'project_name': s.main_project.name
            })

    breadcrumbs = [
        {'name': _('GBMap tool'),
         'url': reverse('flooding_gdmaapstool_index')},
        {'name': _('Edit gdmap')}]

    return render_to_response('gdmap_edit.html',
                              {'breadcrumbs': breadcrumbs,
                               'scenarios': json.dumps(scenarios),
                               'gdmap': gdmap})


def load_gdmap_form(request, gdmap_id):
    """Render the html form to load gdmap."""
    if not (request.user.is_authenticated() and request.user.has_perm(
            'gdmapstool.change_gdmap')):
        return HttpResponse(_("No permission."))
    gdmap = get_object_or_404(GDMap, pk=gdmap_id)
    form = GDMapForm(instance=gdmap)
    return render_to_response('gdmap_form.html',
                              {'form': form})

def save_gdmap_form(request):
    """
    Renders a html with only the form for editing a gdmap
    """
    if not (request.user.is_authenticated() and request.user.has_perm(
            'gdmapstool.change_gdmap')):
        return HttpResponse(_("No permission."))

    if request.method == 'POST':
        form = GDMapForm(request.POST)
        # necessary to call 'is_valid()' before adding custom errors
        valid = form.is_valid()
        scenario_ids = json.loads(request.REQUEST.get('scenarioIds'))

        if not scenario_ids:
            form._errors['scenarios'] = form.error_class(
                [u"U heeft geen scenario's geselecteerd."])
            valid = False
        gdmap_id = form.cleaned_data['id']
        gdmap_name = form.cleaned_data['name']
        if valid:
            gdmap = GDMap.objects.get(pk=gdmap_id)
            gdmap.name = gdmap_name
            gdmap.scenarios = Scenario.objects.filter(
                pk__in=scenario_ids)
            gdmap.save()

            return HttpResponse(
                'redirect_in_js_to_' + reverse('flooding_gdmaapstool_index'))
    else:
        form = GDMapForm()

    return render_to_response('gdmap_form.html', {'form': form})
