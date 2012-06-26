import datetime
import os.path

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson
from django.utils.translation import ugettext as _

from flooding_lib.models import Scenario
from flooding_lib.tools.exporttool.forms import ExportRunForm
from flooding_lib.tools.exporttool.models import ExportRun, Setting


def get_result_path_location(result):
    result_folder = Setting.objects.get(
        key='MAXIMAL_WATERDEPTH_RESULTS_FOLDER').value
    begin_index = (result.file_location.find(result_folder) +
                   len(result_folder))
    path = result.file_location[begin_index:].replace('\\', '/')
    return path


def index(request):
    """
    Renders Lizard-flooding page with an overview of all exports
    """
    if request.method == 'GET':
        action = request.GET.get('action', '')
        path = request.GET.get('path', '')
        if action and path:
            return service_get_max_water_depth_result(request, path)

    if (not (request.user.is_authenticated() and
             (request.user.has_perm('exporttool.can_download') or
              request.user.has_perm('exporttool.can_create')))):
        return HttpResponse(_("No permission to download export"))
    elif request.user.has_perm('exporttool.can_create'):
        has_create_rights = True
    else:
        has_create_rights = False

    export_run_list = list()
    for export_run in ExportRun.objects.all():
        main_result = export_run.get_main_result()
        path = get_result_path_location(main_result) if main_result else None
        detail_url = reverse(
            'flooding_tools_export_detail', args=[export_run.id])

        export_run_list.append((export_run.name,
                    export_run.creation_date,
                    export_run.description,
                    path,
                    detail_url,
                    export_run.get_state_display())
                    )

    breadcrumbs = [
        {'name': _('Export tool')}]

    return render_to_response('export/exports_overview.html',
                              {'export_run_list': export_run_list,
                               'breadcrumbs': breadcrumbs,
                               'has_create_rights': has_create_rights})


def export_detail(request, export_run_id):
    """
    Renders the page showing the details of the export run
    """
    if (not (request.user.is_authenticated() and
             (request.user.has_perm('exporttool.can_download') or
              request.user.has_perm('exporttool.can_create')))):
        return HttpResponse(_("No permission to download export"))

    export_run = get_object_or_404(ExportRun, pk=export_run_id)

    main_result = export_run.get_main_result()
    main_result_file_url = (
        get_result_path_location(main_result) if main_result else None)
    main_result_name = main_result.name if main_result else None

    results_list = []
    for result in export_run.result_set.order_by('area'):
        path = get_result_path_location(result)
        results_list += [[result.get_area_display(), result.name, path]]

    num_scenarios = len(export_run.scenarios.all())
    num_projects = len(
        set([s.main_project for s in export_run.scenarios.all()]))

    breadcrumbs = [
        {'name': _('Export tool'),
         'url': reverse('flooding_tools_export_index')},
        {'name': _('Export detail')}]

    return render_to_response(
        'export/exports_run_detail.html',
        {'export_run': export_run,
         'export_run_main_result_file_url': main_result_file_url,
         'export_run_main_result_name': main_result_name,
         'results_list': results_list,
         'num_scenarios': num_scenarios,
         'num_projects': num_projects,
         'breadcrumbs': breadcrumbs})


def export_detail_scenarios(request, export_run_id):
    """
    Renders the page showing the scenarios and related projects of the
    export run
    """
    if not (request.user.is_authenticated() and
            (request.user.has_perm('exporttool.can_download') or
             request.user.has_perm('exporttool.can_create'))):
        return HttpResponse(_("No permission to download export"))

    export_run = get_object_or_404(ExportRun, pk=export_run_id)
    scenario_list = export_run.scenarios.all()

    breadcrumbs = [
        {'name': _('Export tool'),
         'url': reverse('flooding_tools_export_index')},
        {'name': _('Export detail'),
         'url': reverse('flooding_tools_export_detail',
                        args=[export_run_id])},
        {'name': _('Export detail scenarios and projects')}]

    return render_to_response(
        'export/exports_run_detail_scenarios_and_projects.html',
        {'export_run': export_run,
         'scenario_list': scenario_list,
         'breadcrumbs': breadcrumbs})


def new_export_index(request):
    """
    Renders Lizard-flooding page with javascript elements (lists
    and a pane for the form)
    """
    if not (request.user.is_authenticated() and
            request.user.has_perm('exporttool.can_create')):
        return HttpResponse(_("No permission to create export"))

    breadcrumbs = [
        {'name': _('Export tool'),
         'url': reverse('flooding_tools_export_index')},
        {'name': _('New export')}]

    return render_to_response('export/exports_new_index.html',
                              {'breadcrumbs': breadcrumbs})


def new_export(request):
    """
    Renders a html with only the form for creating a new export run

    * It uses the Django-validation bud adds a custom validation rule:
      there has to be at least one scenario selected. Otherwis an error
      is added to the error list.
    * If the form information is valid, a new export run is created and saved,
      Also the needed information for the genereation of the waterdepth map is
      saved in a CSV-file.
    """
    if not (request.user.is_authenticated() and
            request.user.has_perm('exporttool.can_create')):
        return HttpResponse(_("No permission to create export"))

    if request.method == 'POST':
        form = ExportRunForm(request.POST)

        # necessary to call 'is_valid()' before adding custom errors
        valid = form.is_valid()
        scenario_ids = simplejson.loads(request.REQUEST.get('scenarioIds'))
        if not scenario_ids:
            form._errors['scenarios'] = form.error_class(
                [u"U heeft geen scenario's geselecteerd."])
            valid = False

        if valid:
            new_export_run = ExportRun(
                export_type=ExportRun.EXPORT_TYPE_WATER_DEPTH_MAP,
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                owner=request.user,
                creation_date=datetime.datetime.now()
                )
            new_export_run.save()
            new_export_run.scenarios = Scenario.objects.filter(
                pk__in=scenario_ids)

            if (new_export_run.export_type ==
                ExportRun.EXPORT_TYPE_WATER_DEPTH_MAP):
                export_result_type = 1
                # Get the EXPORT_FOLDER settings (from the settings of
                # the export-tool)
                export_folder = Setting.objects.get(key='EXPORT_FOLDER').value
                csv_file_location = os.path.join(
                    export_folder, str(new_export_run.id) + '.csv')
                text_file_location = os.path.join(
                    export_folder, str(new_export_run.id) + '.txt')
                new_export_run.create_csv_file_for_gis_operation(
                    export_result_type, csv_file_location)
                new_export_run.create_general_file_for_gis_operation(
                    text_file_location)

            return HttpResponse(
                'redirect_in_js_to_' + reverse('flooding_tools_export_index'))
    else:
        form = ExportRunForm()

    return render_to_response('export/exports_new.html',
                              {'form': form})


def service_get_max_water_depth_result(request, path):
    if not (request.user.is_authenticated() and
            (request.user.has_perm('exporttool.can_download') or
             request.user.has_perm('exporttool.can_create'))):
        return HttpResponse(_("No permission to download export"))

    result_folder = Setting.objects.get(
        key='MAXIMAL_WATERDEPTH_RESULTS_FOLDER').value
    file_path = os.path.join(result_folder, path)
    if not os.path.isfile(file_path):
        return HttpResponse('Het opgevraagde bestand bestaat niet.')

    file_name = os.path.split(path)[1]
    file_object = open(file_path, 'rb')
    response = HttpResponse(file_object.read())
    response['Content-Disposition'] = (
        'attachment; filename="' + file_name + '"')
    file_object.close()
    return  response
