import datetime
import json
import os.path

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _

from flooding_lib.util import viewutil
from flooding_lib.models import Scenario
from flooding_lib.tools.gdmapstool.forms import GDMapForm
from flooding_lib.tools.gdmapstool.models import GDMapProject, GDMap


# def get_result_path_location(result):
#     result_folder = Setting.objects.get(
#         key='MAXIMAL_WATERDEPTH_RESULTS_FOLDER').value
#     begin_index = (result.file_basename.find(result_folder) +
#                    len(result_folder))
#     path = result.file_basename[begin_index:].replace('\\', '/')
#     return path


def index(request):
    """
    Renders Lizard-flooding page with an overview of all exports

    Optionally provide
    "?action=get_attachment&path=3090850/zipfiles/totaal.zip"
    """
    # if (not (request.user.is_authenticated() and
    #          (request.user.has_perm('exporttool.can_download') or
    #           request.user.has_perm('exporttool.can_create')))):
    #     return HttpResponse(_("No permission to download export"))
    # elif request.user.has_perm('exporttool.can_create'):
    #     has_create_rights = True
    # else:
    #     has_create_rights = False
    has_create_rights = True
    show_archived = False
    if 'show_archived' in request.GET:
        show_archived = bool(request.GET['show_archived'])

    
    breadcrumbs = [
        {'name': _('GBMap tool')}]

    gd_map_projects = GDMapProject.objects.all()
    
    return render_to_response(
        'gdmapprojects_overview.html',
        {
            'gd_map_projects': gd_map_projects,
            'breadcrumbs': breadcrumbs,
            'has_create_rights': has_create_rights,
            'show_archived': show_archived,
            'request': request
        })


def gdmap_details(request, gdmap_id):
    """
    Renders the page showing the details of the export run
    """
    # if (not (request.user.is_authenticated() and
    #          (request.user.has_perm('exporttool.can_download') or
    #           request.user.has_perm('exporttool.can_create')))):
    #     return HttpResponse(_("No permission to download export"))

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
    # if not request.user.has_perm('exporttool.can_create'):
    #     return HttpResponse(_("No permission to download export"))

    gdmap = get_object_or_404(GDMap, pk=gdmap_id)

    breadcrumbs = [
        {'name': _('GBMap tool'),
         'url': reverse('flooding_gdmaapstool_index')},
        {'name': _('Edit gdmap')}]

    return render_to_response('gdmap_edit.html',
                              {'breadcrumbs': breadcrumbs,
                               'gdmap': gdmap})

def load_gdmap_form(request, gdmap_id):
    """Render the html form to load gdmap."""
    # if not (request.user.is_authenticated() and
    #         request.user.has_perm('exporttool.can_create')):
    #     return HttpResponse(_("No permission to create export"))
    gdmap = get_object_or_404(GDMap, pk=gdmap_id)
    form = GDMapForm(instance=gdmap)
    return render_to_response('gdmap_form.html',
                              {'form': form})

def save_gdmap_form(request):
    """
    Renders a html with only the form for creating a new export run

    * It uses the Django-validation bud adds a custom validation rule:
      there has to be at least one scenario selected. Otherwis an error
      is added to the error list.
    * If the form information is valid, a new export run is created and saved,
      Also the needed information for the genereation of the waterdepth map is
      saved in a CSV-file.
    """
    # if not (request.user.is_authenticated() and
    #         request.user.has_perm('exporttool.can_create')):
    #     return HttpResponse(_("No permission to create export"))

    if request.method == 'POST':
        form = GDMapForm(request.POST)
        # necessary to call 'is_valid()' before adding custom errors
        valid = form.is_valid()
        scenario_ids = json.loads(request.REQUEST.get('scenarioIds'))

        # try:
        #     setting_max_scenarios = Setting.objects.get(
        #         key='MAX_SCENARIOS_PER_EXPORT').value
        #     max_scenarios = int(setting_max_scenarios)
        # except Setting.DoesNotExist:
        #     max_scenarios = DEFAULT_MAX_SCENARIOS_PER_EXPORT

        if not scenario_ids:
            form._errors['scenarios'] = form.error_class(
                [u"U heeft geen scenario's geselecteerd."])
            valid = False
        gdmap_id = form.cleaned_data['id']
        import pdb; pdb.set_trace()
        if valid:
            new_export_run = ExportRun(
                export_type=ExportRun.EXPORT_TYPE_WATER_DEPTH_MAP,
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                owner=request.user,
                creation_date=datetime.datetime.now(),
                gridsize=form.cleaned_data['gridsize'],
                export_max_waterdepth=form.cleaned_data['export_max_waterdepth'],
                export_max_flowvelocity=form.cleaned_data['export_max_flowvelocity'],
                export_possibly_flooded=form.cleaned_data['export_possibly_flooded'],
                export_arrival_times=form.cleaned_data['export_arrival_times'],
                export_period_of_increasing_waterlevel=
                form.cleaned_data['export_period_of_increasing_waterlevel'],
                export_inundation_sources=form.cleaned_data['export_inundation_sources'],
                export_scenario_data=form.cleaned_data['export_scenario_data'],
                public=form.cleaned_data['public']
            )
            new_export_run.save()
            new_export_run.scenarios = Scenario.objects.filter(
                pk__in=scenario_ids)
            new_export_run.start()

            return HttpResponse(
                'redirect_in_js_to_' + reverse('flooding_tools_export_index'))
    else:
        form = ExportRunForm()

    return render_to_response('export/exports_new.html',
                              {'form': form})


# def export_detail_scenarios(request, export_run_id):
#     """
#     Renders the page showing the scenarios and related projects of the
#     export run
#     """
#     if not (request.user.is_authenticated() and
#             (request.user.has_perm('exporttool.can_download') or
#              request.user.has_perm('exporttool.can_create'))):
#         return HttpResponse(_("No permission to download export"))

#     export_run = get_object_or_404(ExportRun, pk=export_run_id)
#     scenario_list = export_run.scenarios.all()

#     breadcrumbs = [
#         {'name': _('Export tool'),
#          'url': reverse('flooding_tools_export_index')},
#         {'name': _('Export detail'),
#          'url': reverse('flooding_tools_export_detail',
#                         args=[export_run_id])},
#         {'name': _('Export detail scenarios and projects')}]

#     return render_to_response(
#         'export/exports_run_detail_scenarios_and_projects.html',
#         {'export_run': export_run,
#          'scenario_list': scenario_list,
#          'breadcrumbs': breadcrumbs})


# def new_export_index(request):
#     """
#     Renders Lizard-flooding page with javascript elements (lists
#     and a pane for the form)
#     """
#     if not (request.user.is_authenticated() and
#             request.user.has_perm('exporttool.can_create')):
#         return HttpResponse(_("No permission to create export"))

#     breadcrumbs = [
#         {'name': _('Export tool'),
#          'url': reverse('flooding_tools_export_index')},
#         {'name': _('New export')}]

#     return render_to_response('export/exports_new_index.html',
#                               {'breadcrumbs': breadcrumbs})


# def load_gdmap_form(request, export_run_id):
#     """Render the html form to load export run."""
#     if not (request.user.is_authenticated() and
#             request.user.has_perm('exporttool.can_create')):
#         return HttpResponse(_("No permission to create export"))
#     export_run = get_object_or_404(ExportRun, pk=export_run_id)
#     form = ExportRunForm(instance=export_run)
#     return render_to_response('export/exports_new.html',
#                               {'form': form})


# def new_export(request):
#     """
#     Renders a html with only the form for creating a new export run

#     * It uses the Django-validation bud adds a custom validation rule:
#       there has to be at least one scenario selected. Otherwis an error
#       is added to the error list.
#     * If the form information is valid, a new export run is created and saved,
#       Also the needed information for the genereation of the waterdepth map is
#       saved in a CSV-file.
#     """
#     if not (request.user.is_authenticated() and
#             request.user.has_perm('exporttool.can_create')):
#         return HttpResponse(_("No permission to create export"))

#     if request.method == 'POST':
#         form = ExportRunForm(request.POST)
#         # necessary to call 'is_valid()' before adding custom errors
#         valid = form.is_valid()
#         scenario_ids = json.loads(request.REQUEST.get('scenarioIds'))

#         try:
#             setting_max_scenarios = Setting.objects.get(
#                 key='MAX_SCENARIOS_PER_EXPORT').value
#             max_scenarios = int(setting_max_scenarios)
#         except Setting.DoesNotExist:
#             max_scenarios = DEFAULT_MAX_SCENARIOS_PER_EXPORT

#         if not scenario_ids:
#             form._errors['scenarios'] = form.error_class(
#                 [u"U heeft geen scenario's geselecteerd."])
#             valid = False
#         elif len(scenario_ids) > max_scenarios:
#             form._errors['scenarios'] = form.error_class(
#                 [u"Er zijn maximaal {} scenario's per export toegestaan."
#                  .format(max_scenarios)])
#             valid = False

#         if valid:
#             new_export_run = ExportRun(
#                 export_type=ExportRun.EXPORT_TYPE_WATER_DEPTH_MAP,
#                 name=form.cleaned_data['name'],
#                 description=form.cleaned_data['description'],
#                 owner=request.user,
#                 creation_date=datetime.datetime.now(),
#                 gridsize=form.cleaned_data['gridsize'],
#                 export_max_waterdepth=form.cleaned_data['export_max_waterdepth'],
#                 export_max_flowvelocity=form.cleaned_data['export_max_flowvelocity'],
#                 export_possibly_flooded=form.cleaned_data['export_possibly_flooded'],
#                 export_arrival_times=form.cleaned_data['export_arrival_times'],
#                 export_period_of_increasing_waterlevel=
#                 form.cleaned_data['export_period_of_increasing_waterlevel'],
#                 export_inundation_sources=form.cleaned_data['export_inundation_sources'],
#                 export_scenario_data=form.cleaned_data['export_scenario_data'],
#                 public=form.cleaned_data['public']
#             )
#             new_export_run.save()
#             new_export_run.scenarios = Scenario.objects.filter(
#                 pk__in=scenario_ids)
#             new_export_run.start()

#             return HttpResponse(
#                 'redirect_in_js_to_' + reverse('flooding_tools_export_index'))
#     else:
#         form = ExportRunForm()

#     return render_to_response('export/exports_new.html',
#                               {'form': form})


# def exportrun_resultfile(request, export_run_id):
#     if not (request.user.is_authenticated() and
#             (request.user.has_perm('exporttool.can_download') or
#              request.user.has_perm('exporttool.can_create'))):
#         return HttpResponse(_("No permission to download export"))

#     export_run = get_object_or_404(ExportRun, pk=export_run_id)
#     main_result = export_run.get_main_result()

#     if main_result is None:
#         return HttpResponse(_("Export run has no result."))

#     result_folder = Setting.objects.get(
#         key='MAXIMAL_WATERDEPTH_RESULTS_FOLDER').value

#     file_path = os.path.join(result_folder, main_result.file_basename)
#     if not os.path.isfile(file_path):
#         return HttpResponse('Het opgevraagde bestand bestaat niet.')

#     return viewutil.serve_file(
#         request, result_folder, main_result.file_basename,
#         '/download_export_run_results/')


# def get_breaches_info(scenario):
#     info = {}
#     breaches = scenario.breaches.all()
#     breaches_values = breaches.values(
#         "name", "id", "region__id", "region__name", "externalwater__name",
#         "externalwater__type")
#     info["names"] = [v.get("name") for v in breaches_values]
#     info["region_names"] = [v.get("region__name") for v in breaches_values]
#     info["externalwater_name"] = [
#         v.get("externalwater__name") for v in breaches_values]
#     info["externalwater_type"] = [
#         v.get("externalwater__type") for v in breaches_values]
#     return info


# def export_run_scenarios(request, export_run_id):
#     if not request.user.has_perm('exporttool.can_create'):
#         return HttpResponse(_("No permission to download export"))

#     export_run = get_object_or_404(ExportRun, pk=export_run_id)
#     scenarios_export_list = []
#     for s in export_run.all_active_scenarios():
#         breaches_values = get_breaches_info(s)
#         scenarios_export_list.append(
#             {
#                 'scenario_id': s.id,
#                 'scenario_name': s.name,
#                 'breach_names': breaches_values.get("names"),
#                 'region_names': breaches_values.get("region_names"),
#                 'extwname': breaches_values.get("externalwater_name"),
#                 'extwtype': breaches_values.get("externalwater_type"),
#                 'project_id': s.main_project.id,
#                 'project_name': s.main_project.name,
#                 'extwrepeattime': [
#                     sbr.extwrepeattime for sbr in s.scenariobreach_set.all()]
#             })
#     return HttpResponse(
#         json.dumps(scenarios_export_list), mimetype="application/json")


# def reuse_export(request, export_run_id):
#     if not request.user.has_perm('exporttool.can_create'):
#         return HttpResponse(_("No permission to download export"))

#     export_run = get_object_or_404(ExportRun, pk=export_run_id)
#     scenarios = export_run.all_active_scenarios()
#     projecten = {}
#     for s in scenarios:
#         project = s.main_project
#         if project in projecten.keys():
#             projecten[project] = projecten[project] + 1
#         else:
#             projecten[project] = 0

#     project = max(projecten, key=projecten.get)
#     breadcrumbs = [
#         {'name': _('Export tool'),
#          'url': reverse('flooding_tools_export_index')},
#         {'name': _('Edit export')}]

#     return render_to_response('export/export_edit.html',
#                               {'breadcrumbs': breadcrumbs,
#                                'export_run': export_run,
#                                'project': project})


# def toggle_archived_export(request, export_run_id):
#     if not request.user.has_perm('exporttool.can_create'):
#         return HttpResponse(_("No permission to download export"))

#     export_run = get_object_or_404(ExportRun, pk=export_run_id)

#     if request.user != export_run.owner:
#         return HttpResponse(_("Only the export run's owner can archive it."))

#     export_run.archived = True
#     export_run.save()

#     return HttpResponseRedirect(reverse('flooding_tools_export_index'))


# def delete_archived_export(request, export_run_id):
#     if not request.user.has_perm('exporttool.can_create'):
#         return HttpResponse(_("No permission to delete export"))

#     export_run = get_object_or_404(ExportRun, pk=export_run_id)

#     if request.user != export_run.owner:
#         return HttpResponse(_("Only the export run's owner can delete it."))

#     export_run.delete()

#     return HttpResponseRedirect(reverse('flooding_tools_export_index'))
