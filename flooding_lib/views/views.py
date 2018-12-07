# Create your views here.
from math import cos, sin
import flooding_lib.util.csvutil
import datetime
import logging
import os
import time

from PIL import Image
from PIL import ImageDraw

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models import Count
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.static import serve

from flooding_lib.views.classbased import BaseView
from flooding_lib.util import viewutil
from flooding_base.models import Text
from flooding_lib.models import (Project, UserPermission, Scenario,
    Region, RegionSet, Breach, ScenarioCutoffLocation, ScenarioBreach, Result,
    ResultType, Task, TaskType, SobekModel, ScenarioProject)
from flooding_lib.forms import ScenarioBreachForm, ProjectForm
from flooding_lib.forms import ScenarioForm, ScenarioCutoffLocationForm
from flooding_lib.forms import ScenarioNameRemarksForm
from flooding_lib.permission_manager import receives_permission_manager
from flooding_lib.permission_manager import \
    receives_loggedin_permission_manager
from flooding_lib import forms
from flooding_lib import excel_import_export


logger = logging.getLogger(__name__)

#-----------------------'constants' - make a copy when using them----
"""
The search defaults that are used in the search application
for the scenarios
"""
scenario_list_search_defaults = {
    'sort': '',
    'q': '',
    'page_nr': 1,
    'items_per_page': 25,
    'status': [10, 20, 30, 40, 50, 60, 70, 80],
    'regionset': 0,
    'region': 0,
    'breach': 0,
    'waterlevel_lte': None,
    'waterlevel_gte': None,
    'repeattime_lte': None,
    'repeattime_gte': None,
    }

"""
The table columns that are used in the search application
for the scenarios
"""
scenario_list_search_table_columns = (
    {'name': _('id'),
     'sort': 'id',
     'sort_rev': 'id_rev',
     'width': '3%'},
    {'name': _('name'),
     'sort': 'name',
     'sort_rev': 'name_rev',
     'width': '12%'},
    {'name': _('status'),
     'sort': 'status',
     'sort_rev': 'status_rev',
     'width': '3%'},
    {'name': _('mainproject'),
     'sort': 'projects',
     'sort_rev': 'mainproject_rev',
     'width': '8%'},
    {'name': _('projects'),
     'sort': 'projects',
     'sort_rev': 'projects_rev',
     'width': '8%'},
    {'name': _('region'),
     'width': '8%'},
    {'name': _('sobekmodel inundation'),
     'sort': 'sobekmodelinundation',
     'sort_rev': 'sobekmodelinundation_rev',
     'width': '12%'},
    {'name': _('breach properties'),
     'width': '13%'},
    {'name': _('cutofflocations'),
     'width': '10%'},
    {'name': _('delete'),
     'width': '3%'},
    )

#-----------------------------editing views-----------------------------------


@receives_loggedin_permission_manager
def project_delete(request, permission_manager, object_id):
    project = get_object_or_404(Project, pk=object_id)

    if ((project.owner == request.user or request.user.is_staff) and
        permission_manager.check_project_permission(
            project, UserPermission.PERMISSION_PROJECT_DELETE)):
        project.delete()

    next = reverse('flooding_projects_url')
    return HttpResponseRedirect(next)


@receives_loggedin_permission_manager
def scenario_addedit(request, permission_manager, object_id=None):
    """Adds a scenario if object_id is None, else edit scenario"""

    user = request.user
    if object_id is not None:
        scenario = get_object_or_404(Scenario, pk=object_id)
        scenario_name = scenario.name
        #check scenario_edit permission FOR PROJECT

        if not (permission_manager.check_project_permission(
                scenario.main_project,
                UserPermission.PERMISSION_SCENARIO_EDIT)):
            raise Http404
    else:
        #check scenario_add permission FOR USER
        scenario = []
        scenario_name = _('New scenario')
        if not(permission_manager.check_permission(
                UserPermission.PERMISSION_SCENARIO_ADD)):
            raise Http404

    if request.method == 'POST':
        # check if we're editing an existing scenario
        if object_id is None:
            form = ScenarioForm(request.POST)
        else:
            form = ScenarioForm(request.POST, instance=scenario)
        if form.is_valid():
            scenario = form.save(commit=False)
            scenario.owner = user
            scenario.save()
            next = reverse('flooding_scenarios_url')
            return HttpResponseRedirect(next)

    else:
        if object_id is None:
            form = ScenarioForm()
        else:
            form = ScenarioForm(instance=scenario)

    breadcrumbs = [
        {'name': _('Flooding'), 'url': reverse('flooding')},
        {'name': _('Scenario'), 'url': reverse('flooding_scenarios_url')},
        {'name': scenario_name}]

    return render_to_response('flooding/scenario_form.html', {
            'form': form,
            'user': user,
            'scenario': scenario,
            'breadcrumbs': breadcrumbs})


@receives_loggedin_permission_manager
def scenario_editnameremarks(request, permission_manager, object_id):
    """Edits scenario name and remarks"""
    scenario = get_object_or_404(Scenario, pk=object_id)
    if not(permission_manager.check_permission(
            UserPermission.PERMISSION_SCENARIO_EDIT)):
        raise Http404
    if request.method == 'POST':
        form = ScenarioNameRemarksForm(request.POST, instance=scenario)
        if form.is_valid():
            form.save()
            next = reverse('flooding_scenarios_url')
            return HttpResponseRedirect(next)
    else:
        form = ScenarioNameRemarksForm(instance=scenario)
    return render_to_response('flooding/scenario_name_remarks_form.html',
                              {'form': form})


@receives_loggedin_permission_manager
def scenario_delete(request, permission_manager, object_id):
    """Create delete scenario task"""
    scenario = get_object_or_404(Scenario, pk=object_id)

    project = scenario.main_project
    if ((scenario.owner == request.user or request.user.is_staff) and
        permission_manager.check_project_permission(
            project, UserPermission.PERMISSION_SCENARIO_DELETE)):
        #scenario.delete()
        tasktype = TaskType.objects.get(pk=TaskType.TYPE_SCENARIO_DELETE)
        task = Task(
            scenario=scenario, remarks=('deleted by %s from gui' %
                                        (request.user)),
            tasktype=tasktype, creatorlog='', tstart=datetime.datetime.now(),
            successful=True)
        task.save()

    next = reverse('flooding_scenarios_url')
    return HttpResponseRedirect(next)


@receives_loggedin_permission_manager
def scenario_cutofflocation_add(request, permission_manager, scenario_id):
    """Add /edit page for ScenarioCutoffLocation"""
    user = request.user

    if not(permission_manager.check_permission(
            UserPermission.PERMISSION_SCENARIO_EDIT)):
        raise Http404

    scenario = get_object_or_404(Scenario, pk=scenario_id)

    if not(permission_manager.check_project_permission(
            scenario.main_project,
            UserPermission.PERMISSION_SCENARIO_EDIT)):
        raise Http404

    if request.method == 'POST':
        form = ScenarioCutoffLocationForm(request.POST)
        if form.is_valid():
            scenario_cutofflocation = form.save(commit=False)
            scenario_cutofflocation.scenario = scenario
            scenario_cutofflocation.save()
            next = reverse(
                'flooding_scenario_edit',
                kwargs={'object_id': scenario.id})
            return HttpResponseRedirect(next)
    else:
        form = ScenarioCutoffLocationForm()

    return render_to_response('flooding/scenario_cutofflocation_form.html', {
            'form': form, 'user': user, 'scenario': scenario})


@receives_loggedin_permission_manager
def scenario_breach_add(request, permission_manager, scenario_id):
    """Add /edit page for ScenarioBreach"""

    if not(permission_manager.check_permission(
            UserPermission.PERMISSION_SCENARIO_EDIT)):
        raise Http404

    scenario = get_object_or_404(Scenario, pk=scenario_id)

    if not(permission_manager.check_project_permission(
            scenario.main_project,
            UserPermission.PERMISSION_SCENARIO_EDIT)):
        raise Http404

    if request.method == 'POST':
        form = ScenarioBreachForm(request.POST)
        if form.is_valid():
            scenario_breach = form.save(commit=False)
            scenario_breach.scenario = scenario
            scenario_breach.save()
            next = reverse(
                'flooding_scenario_edit', kwargs={'object_id': scenario.id})
            return HttpResponseRedirect(next)
    else:
        form = ScenarioBreachForm()

    return render_to_response(
        'flooding/scenario_breach_form.html', {
            'form': form,
            'user': request.user,
            'scenario': scenario})


@receives_loggedin_permission_manager
def scenario_cutofflocation_delete(request, permission_manager, object_id):
    scenario_cutofflocation = get_object_or_404(
        ScenarioCutoffLocation, pk=object_id)
    scenario = scenario_cutofflocation.scenario
    project = scenario.main_project

    if ((scenario.owner == request.user or request.user.is_staff) and
        permission_manager.check_project_permission(
            project, UserPermission.PERMISSION_SCENARIO_EDIT)):
        scenario_cutofflocation.delete()

    next = reverse('flooding_scenario_edit', kwargs={'object_id': scenario.id})
    return HttpResponseRedirect(next)


@receives_loggedin_permission_manager
def scenario_breach_delete(request, permission_manager, object_id):
    scenario_breach = get_object_or_404(ScenarioBreach, pk=object_id)
    scenario = scenario_breach.scenario

    project = scenario.main_project

    if ((scenario.owner == request.user or request.user.is_staff) and
        permission_manager.check_project_permission(
            project, UserPermission.PERMISSION_SCENARIO_EDIT)):
        scenario_breach.delete()

    next = reverse('flooding_scenario_edit', kwargs={'object_id': scenario.id})
    return HttpResponseRedirect(next)


@receives_permission_manager
def project_addedit(request, permission_manager, object_id=None):
    """Add/edit project"""

    user = request.user

    if object_id is not None:
        project = get_object_or_404(Project, pk=object_id)
        project_name = project.name
        #check project_edit permission FOR PROJECT
        if not permission_manager.check_project_permission(
                project, UserPermission.PERMISSION_PROJECT_EDIT):
            raise Http404
    else:
        #check project_add permission FOR USER
        project = []
        project_name = _('New project')
        if not(permission_manager.check_permission(
                UserPermission.PERMISSION_PROJECT_ADD)):
            raise Http404

    if request.method == 'POST':
        #check if we're editing an existing project
        if object_id is None:
            form = ProjectForm(request.POST)
        else:
            form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = user
            project.save()
            next = reverse('flooding_projects_url')
            return HttpResponseRedirect(next)
    else:
        if object_id is None:
            form = ProjectForm()
        else:
            form = ProjectForm(instance=project)

    breadcrumbs = [
        {'name': _('Flooding'), 'url': reverse('flooding')},
        {'name': _('My projects'), 'url': reverse('flooding_projects_url')},
        {'name': project_name}]

    return render_to_response(
        'flooding/project_form.html', {
            'form': form, 'user': user, 'project': project,
            'breadcrumbs': breadcrumbs})


#--------------------------- look only views ----------------------------------

def index(request):
    """Renders Lizard-flooding main page."""
    return render_to_response(
        'flooding/index.html',
        {
            'breadcrumbs': [{'name':_('Flooding')}],
            'user': request.user,
            'LANGUAGES': settings.LANGUAGES}
        )


@receives_permission_manager
def project_list(request, permission_manager):
    """Renders index of projects: viewable projects."""

    #stuff from request
    query = request.GET.get('q', '')
    items_per_page = int(request.GET.get('items_per_page', '25'))
    page_nr = int(request.GET.get('page_nr', '1'))
    sort = request.GET.get('sort', '')
    filter_owner = int(request.GET.get('filter_owner', '-1'))

    #from database: all possible projects
    projects = permission_manager.get_projects(
        UserPermission.PERMISSION_SCENARIO_VIEW)

    #make list of owners
    owners = {}
    for p in projects:
        owners[p.owner.id] = p.owner
    owner_choices = tuple(
        [(-1, _('(choose owner)'))] + [(k, v) for k, v in owners.items()]
        )

    #order and filter projects
    order_dict = {
        'id': 'id', 'id_rev': '-id',
        'name': 'name', 'name_rev': '-name',
        'friendlyname': 'friendlyname',
        'friendlyname_rev': '-friendlyname',
        'owner': 'owner', 'owner_rev': '-owner',
        }
    if filter_owner is not None and filter_owner != -1:
        projects = projects.filter(owner__id=filter_owner)
    if query is not None and query != '':
        projects = projects.filter(
            Q(name__icontains=query) | Q(name__icontains=query))
    if sort:
        projects = projects.order_by(order_dict[sort])

    #paginate projects
    paginator = Paginator(projects, items_per_page)
    try:
        page = paginator.page(page_nr)
    except:
        page_nr = 1
        page = paginator.page(page_nr)

    fields = {
        'q': query,
        'sort': sort,
        'filter_owner': filter_owner,
        'page_nr': page_nr,
        'items_per_page': items_per_page,
        }
    table_columns = [{'name': _('id'),
                      'sort': 'id',
                      'sort_rev': 'id_rev',
                      'width': '3%'},
                     {'name': _('name'),
                      'sort': 'name',
                      'sort_rev': 'name_rev',
                      'width': '15%'},
                     {'name': _('friendlyname'),
                      'sort': 'friendlyname',
                      'sort_rev': 'friendlyname_rev',
                      'width': '15%'},
                     {'name': _('owner'),
                      'sort': 'owner',
                      'sort_rev': 'owner_rev',
                      'width': '5%'},
                     {'name': _('regionsets'),
                      'width': '5%'},
                     {'name': _('scenarios'),
                      'width': '35%'},
                     {'name': _('edit'),
                      'width': '3%'},
                     {'name': _('delete'),
                      'width': '3%'},
                     ]
    table_data = []
    for o in page.object_list:
        regionsets = ', '.join(
            [str(rs) for rs in o.regionsets.all().order_by('name')])
        scenarios = ', '.join(
            [str(s) for s in o.scenario_set.all().order_by('name')])

        if permission_manager.check_project_permission(
            o, UserPermission.PERMISSION_PROJECT_EDIT):
            edit_field = {'icon': 'edit',
                          'icontitle': _('edit this item'),
                          'url': reverse("flooding_project_edit",
                                         kwargs={"object_id": o.pk})
                          }
        else:
            edit_field = {
                'icon': 'edit_disabled',
                'icontitle': _('you need permission to edit this item')}
        if permission_manager.check_project_permission(
            o, UserPermission.PERMISSION_PROJECT_DELETE):
            delete_field = {'icon': 'delete',
                            'icontitle': _('delete this item'),
                            'urlpost': reverse("flooding_project_delete",
                                               kwargs={"object_id": o.pk}),
                            'postclickmessage': _('are you sure?'),
                            }
        else:
            delete_field = {
                'icon': 'delete_disabled',
                'icontitle': _('you need permission to delete this item')}

        row = [{'url': o.get_absolute_url(),
                'value': o.id},
               {'url': o.get_absolute_url(),
                'value': o.name},
               {'url': o.get_absolute_url(),
                'value': o.friendlyname},
               {'value': o.owner},
               {'value': regionsets},
               {'value': scenarios},
               edit_field,
               delete_field,
               ]
        table_data.append(row)

    return render_to_response('flooding/project_list.html', {
            'user': request.user,
            'projects': projects,
            'breadcrumbs': [
                {'name': _('Flooding'), 'url': reverse('flooding')},
                {'name': _('Projects')},
                ],
            'LANGUAGES': settings.LANGUAGES,
            'owner_choices': owner_choices,

            'name': _('Projects'),
            'fields': fields,
            'paginator': paginator,
            'page': page,
            'table_columns': table_columns,
            'table_data': table_data,
            })


@receives_permission_manager
def task_list(request, permission_manager):
    """Task list.
    """

    page_nr = int(request.GET.get('page_nr', '1'))
    items_per_page = int(request.GET.get('items_per_page', 20))
    sort = request.GET.get('sort', '')
    query = request.GET.get('q', '')
    filter_scenario = int(request.GET.get('filter_scenario', -1))
    filter_tasktype = int(request.GET.get('filter_tasktype', -1))
    filter_successful = int(request.GET.get('filter_successful', -1))

    projects = permission_manager.get_projects()
    scenarios = Scenario.in_project_list(projects)
    tasks = Task.objects.filter(scenario__in=scenarios)
    if filter_scenario != -1:
        tasks = tasks.filter(scenario__id=filter_scenario)
    if filter_tasktype != -1:
        tasks = tasks.filter(tasktype__id=filter_tasktype)
    if filter_successful != -1:
        successful_filter = {1: True,
                             2: False,
                             3: None}
        tasks = tasks.filter(successful=successful_filter[filter_successful])

    if query:
        tasks = tasks.filter(Q(scenario__name__icontains=query) |
                             Q(tasktype__name__icontains=query) |
                             Q(creatorlog__icontains=query) |
                             Q(errorlog__icontains=query))

    sort_dict = {
        'id': 'id', 'id_rev': '-id',
        'scenario': 'scenario__name', 'scenario_rev': '-scenario__name',
        'tasktype': 'tasktype', 'tasktype_rev': '-tasktype',
        'tstart': 'tstart', 'tstart_rev': '-tstart',
        'tfinished': 'tfinished', 'tfinished_rev': '-tfinished',
        'successful': 'successful', 'successful_rev': '-successful',
        'creatorlog': 'creatorlog', 'creatorlog_rev': '-creatorlog',
        'errorlog': 'errorlog', 'errorlog_rev': '-errorlog',
        }

    if sort:
        tasks = tasks.order_by(sort_dict[sort])

    paginator = Paginator(tasks, items_per_page)
    try:
        page = paginator.page(page_nr)
    except:
        page_nr = 1
        page = paginator.page(page_nr)

    fields = {
        'q': query,
        'sort': sort,
        'filter_scenario': filter_scenario,
        'filter_tasktype': filter_tasktype,
        'filter_successful': filter_successful,
        }

    scenario_choices = tuple(
        [(-1, _('(choose scenario)'))] + [(s.id, str(s)) for s in scenarios]
        )
    tasktype_choices = tuple(
        [(-1, _('(choose tasktype)'))] +
        [(tt.id, str(tt)) for tt in TaskType.objects.all()]
        )
    successful_choices = (
        (-1, _('(choose successful)')),
        (1, _('true')), (2, _('false')), (3, _('none')),
        )
    filter_entries = [
        {'choices': scenario_choices,
         'output_name': 'filter_scenario',
         'current_value': filter_scenario},
        {'choices': tasktype_choices,
         'output_name': 'filter_tasktype',
         'current_value': filter_tasktype},
        {'choices': successful_choices,
         'output_name': 'filter_successful',
         'current_value': filter_successful},
        ]

    table_columns = [{'name': _('id'),
                      'sort': 'id',
                      'sort_rev': 'id_rev',
                      'width': '2%'},
                     {'name': _('scenario'),
                      'sort': 'scenario',
                      'sort_rev': 'scenario_rev',
                      'width': '17%'},
                     {'name': _('tasktype'),
                      'sort': 'tasktype',
                      'sort_rev': 'tasktype_rev',
                      'width': '8%'},
                     {'name': _('tstart'),
                      'sort': 'tstart',
                      'sort_rev': 'tstart_rev',
                      'width': '8%'},
                     {'name': _('tfinished'),
                      'sort': 'tfinished',
                      'sort_rev': 'tfinished_rev',
                      'width': '8%'},
                     {'name': _('successful'),
                      'sort': 'successful',
                      'sort_rev': 'successful_rev',
                      'width': '1%'},
                     {'name': _('creator log'),
                      'sort': 'creatorlog',
                      'sort_rev': 'creatorlog_rev',
                      'width': '10%'},
                     {'name': _('error log'),
                      'sort': 'errorlog',
                      'sort_rev': 'errorlog_rev',
                      'width': '10%'},
                     {'name': _('edit'),
                      'width': '2%'},
                     {'name': _('delete'),
                      'width': '2%'},
                     ]
    table_data = []
    for o in page.object_list:
        if permission_manager.check_project_permission(
            o, UserPermission.PERMISSION_TASK_EDIT):
            edit_field = {'icon': 'edit',
                          'icontitle': _('not implemented yet')}
        else:
            edit_field = {
                'icon': 'edit_disabled',
                'icontitle': _('you need permission to edit this item')}
        if permission_manager.check_project_permission(
            o, UserPermission.PERMISSION_TASK_DELETE):
            delete_field = {'icon': 'delete',
                            'icontitle': _('not implemented yet')}
        else:
            delete_field = {
                'icon': 'delete_disabled',
                'icontitle': _('you need permission to delete this item')}
        row = [{'url': o.get_absolute_url(),
                'value': o.id},
               {'url': o.scenario.get_absolute_url(),
                'value': o.scenario},
               {'value': o.tasktype},
               {'value': o.tstart},
               {'value': o.tfinished},
               {'value': o.successful},
               {'value': o.creatorlog},
               {'value': o.errorlog},
               edit_field,
               delete_field,
               ]
        table_data.append(row)

    breadcrumbs = [{'name': _('Flooding'), 'url': reverse('flooding')},
                   {'name': _('Tasks')},
                   ]

    return render_to_response('flooding/task_list.html', {
            'user': request.user,

            'fields': fields,
            'paginator': paginator,
            'page': page,

            'table_columns': table_columns,
            'table_data': table_data,
            'name': _('Tasks'),

            'filter_entries': filter_entries,

            'breadcrumbs': breadcrumbs,
            })


def scenario_list_get_search_parameters(request, search_defaults):
    """
    Returns the search parameter as a combination of the search session,
    the search defaults and the request paramaters.
    """
    #get the request.GET options, overwrite existing value
    search_session = request.session.get('scenario_list', {})
    qd = request.GET  # querydict

    #get search options from request
    search_session['q'] = qd.get(
        'q', search_session.get('q', search_defaults['q']))

    search_session['items_per_page'] = int(
        qd.get('items_per_page',
               search_session.get('items_per_page',
                                  search_defaults['items_per_page'])))

    search_session['page_nr'] = int(
        qd.get('page_nr',
               search_session.get('page_nr', search_defaults['page_nr'])))

    search_session['sort'] = qd.get(
        'sort', search_session.get('sort', search_defaults['sort']))

    if 'status' in qd:
        # je hebt syntax filter_status=10&filter_status=20 OF
        # filter_status=[10, 20]
        try:
            search_session['status'] = [int(s) for s in qd.getlist('status')]
        except:
            status_str = request.GET.get('status').strip('[]').split(',')
            search_session['status'] = [int(s) for s in status_str]
    else:
        search_session['status'] = search_session.get(
            'status', search_defaults['status'])

    search_session['regionset'] = int(
        qd.get('regionset',
               search_session.get('regionset', search_defaults['regionset'])))
    search_session['region'] = int(
        qd.get('region',
               search_session.get('region', search_defaults['region'])))
    search_session['breach'] = int(
        qd.get('breach',
               search_session.get('breach', search_defaults['breach'])))

    try:
        search_session['waterlevel_lte'] = float(qd['waterlevel_lte'])
    except:
        search_session['waterlevel_lte'] = None
    try:
        search_session['waterlevel_gte'] = float(qd['waterlevel_gte'])
    except:
        search_session['waterlevel_gte'] = None

    try:
        search_session['repeattime_lte'] = float(qd['repeattime_lte'])
    except:
        search_session['repeattime_lte'] = None
    try:
        search_session['repeattime_gte'] = float(qd['repeattime_gte'])
    except:
        search_session['repeattime_gte'] = None

    return search_session


@receives_loggedin_permission_manager
def scenario_list(request, permission_manager):
    """Renders index of scenario's: divided in own and viewable scenario's.

    options:
    items_per_page (optional, default=20)
    page_nr (optional, default=1)
    sort (optional, default="")
    filter_status (optional, default=...)
    filter_regionset (optional, default="0")
    filter_region (optional, default="0")
    filter_breach (optional, default="0")
    q (optional, default="")
    format (optional, default="html")

    search options are stored in the session 'scenario_list' as a dictionary

    """

    is_embedded = request.GET.get('is_embedded', 0)
    search_defaults = scenario_list_search_defaults.copy()

    clear_search = 'clear_search' in request.GET
    if clear_search:
        search_session = search_defaults.copy()
    else:
        search_parameters = scenario_list_get_search_parameters(
            request, search_defaults)
        search_session = search_parameters
        #save search parameters to session
        request.session['scenario_list'] = search_parameters

    #get the objects (scenario's) that you can see and filter
    projects = permission_manager.get_projects(
        permission=UserPermission.PERMISSION_SCENARIO_VIEW)

    scenarios = Scenario.in_project_list(projects)
    if search_session['q']:
        q = search_session['q']
        scenarios = scenarios.filter(
            Q(name__icontains=q) |
            Q(remarks__icontains=q) |
            Q(scenarioproject__project__name__icontains=q) |
            Q(scenarioproject__project__friendlyname__icontains=q))
    if search_session['status']:
        scenarios = scenarios.filter(status_cache__in=search_session['status'])
    if search_session['regionset'] > 0:
        filter_regionset_object = get_object_or_404(
            RegionSet, pk=search_session['regionset'])
        scenarios = scenarios.filter(
            breaches__region__regionset__in=[filter_regionset_object])
    if search_session['region'] > 0:
        #in het menu staan altijd opties die je mag doen, anders heb
        #je gehacked, dus 404 is wel okee
        filter_region_object = get_object_or_404(
            Region, pk=search_session['region'])
        if not(permission_manager.check_region_permission(
                filter_region_object,
                UserPermission.PERMISSION_SCENARIO_VIEW)):
            raise Http404
        scenarios = scenarios.filter(
            breaches__region__in=[filter_region_object])
    else:
        filter_region_object = None
    if search_session['breach'] > 0:
        search_breach = get_object_or_404(Breach, pk=search_session['breach'])
        scenarios = scenarios.filter(breaches__in=[search_breach])
    if search_session['waterlevel_lte'] is not None:
        scenarios = scenarios.exclude(
            scenariobreach__extwmaxlevel__gt=search_session['waterlevel_lte'])
    if search_session['waterlevel_gte'] is not None:
        scenarios = scenarios.exclude(
            scenariobreach__extwmaxlevel__lt=search_session['waterlevel_gte'])
    if search_session['repeattime_lte'] is not None:
        scenarios = scenarios.exclude(
           scenariobreach__extwrepeattime__gt=search_session['repeattime_lte'])
    if search_session['repeattime_gte'] is not None:
        scenarios = scenarios.exclude(
           scenariobreach__extwrepeattime__lt=search_session['repeattime_gte'])
    
    scenarios = scenarios.order_by('id').distinct('id')

    #order the object list
    order_dict = {
        'id': 'id', 'id_rev': '-id',
        'name': 'name', 'name_rev': '-name',
        'projects': 'projects', 'projects_rev': '-projects',
        'mainproject': 'projects', 'mainproject_rev': '-projects',
        'sobekmodelinundation': 'sobekmodel_inundation',
        'sobekmodelinundation_rev': '-sobekmodel_inundation',
        'tsim': 'tsim', 'tsim_rev': '-tsim',
        'calcpriority': 'calcpriority',
        'calcpriority_rev': '-calcpriority',
        'remarks': 'remarks', 'remarks_rev': '-remarks',
        'owner': 'owner', 'owner_rev': '-owner',
        'status': 'status_cache', 'status_rev': '-status_cache',
        }
    if search_session['sort']:
        scenarios = scenarios.order_by(order_dict[search_session['sort']])

    format = request.GET.get('format', 'html')
    if format == 'csv':
        def join(sequence):
            """Join a bunch of things into a |-separated unicode string"""
            return u'|'.join(unicode(item) for item in sequence)

        # create a CSV response
        # write Unicode CSV to it directly
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=query.csv'

        writer = flooding_lib.util.csvutil.UnicodeWriter(response)

        writer.writerow((
                'Id',
                'Name',
                'Status',
                'Regions',
                'Project name',
                'Inundation model name',
                'Inundation model version',
                'Names of breaches',
                'X-coordinates of breaches',
                'Y-coordinates of breaches',
                'Name of external water of breaches',
                'Type of external water of breaches',
                'Initial width of breaches',
                'Bottom level of breaches',
                'Pit depth of breaches',
                'Max level of external water of breaches',
                'Base level of external water of breaches',
                'Time till max depth of breaches',
                'Duration of storm of breaches',
                'Duration of the peak of the storm of breaches',
                'Number of cutofflocations of the external water',
                'Ids of cutofflocations of the external water',
                'Number of cutofflocations of the internal water',
                'Ids of cutofflocations of the internal water',
                'Number of casualties',
                'Damage to the flooding area',
                'Damage to the embankments'
                ))

        for s in scenarios:
            # retrieve data to use for filling the row
            regions = Region.objects.filter(
                breach__scenario__in=[s]).distinct()
            scenario_inundation_model = s.sobekmodel_inundation
            scenario_breaches = s.scenariobreach_set.all()
            cutofflocations_externalwater = s.cutofflocations.filter(
                sobekmodels__sobekmodeltype=SobekModel.SOBEKMODELTYPE_CANAL)
            cutofflocations_internal = s.cutofflocations.filter(
              sobekmodels__sobekmodeltype=SobekModel.SOBEKMODELTYPE_INUNDATION)
            try:
                casualties = s.presentationlayer.filter(
                    presentationtype__code="casualties")[0].value
            except (ValueError, IndexError):
                casualties = None
            try:
                damage_embankments = s.presentationlayer.filter(
                    presentationtype__code="damage_embankments")[0].value
            except (ValueError, IndexError):
                damage_embankments = None
            try:
                damage_floodingarea = s.presentationlayer.filter(
                    presentationtype__code="damage_floodingarea")[0].value
            except (ValueError, IndexError):
                damage_floodingarea = None

            # fill the row
            writer.writerow((
                    s.id,
                    s.name,
                    s.status_cache,
                    s.main_project.name,
                    join(r.name for r in regions),
                    scenario_inundation_model.model_varname,
                    scenario_inundation_model.sobekversion.name,
                    join(sb.breach.name for sb in scenario_breaches),
                    join(sb.breach.geom.x for sb in scenario_breaches),
                    join(sb.breach.geom.y for sb in scenario_breaches),
                    join(sb.breach.externalwater.name
                         for sb in scenario_breaches),
                    join(sb.breach.externalwater.get_type_display()
                         for sb in scenario_breaches),
                    join(sb.widthbrinit for sb in scenario_breaches),
                    join(sb.bottomlevelbreach for sb in scenario_breaches),
                    join(sb.pitdepth for sb in scenario_breaches),
                    join(sb.extwmaxlevel for sb in scenario_breaches),
                    join(sb.extwbaselevel for sb in scenario_breaches),
                    join(sb.tmaxdepth for sb in scenario_breaches),
                    join(sb.tstorm for sb in scenario_breaches),
                    join(sb.tpeak for sb in scenario_breaches),
                    cutofflocations_externalwater.count(),
                    join(c.id for c in cutofflocations_externalwater),
                    cutofflocations_internal.count(),
                    join(c.id for c in cutofflocations_internal),
                    casualties,
                    damage_floodingarea,
                    damage_embankments))

        return response

    if format == 'html':
        #paginate
        paginator = Paginator(scenarios, search_session['items_per_page'])
        try:
            page = paginator.page(search_session['page_nr'])
        except:
            page_nr = 1
            page = paginator.page(page_nr)

        #scenario columns
        table_columns = list(scenario_list_search_table_columns)

        #build table data for template
        table_data = []
        for o in page.object_list:
            if permission_manager.check_project_permission(
                o, UserPermission.PERMISSION_SCENARIO_DELETE):
                delete_field = {
                    'icon': '/static_media/images/icons/delete',
                    'icontitle': _('delete this item'),
                    'urlpost': reverse(
                        "flooding_scenario_delete",
                        kwargs={"object_id": o.pk}),
                    'postclickmessage': _('are you sure?'),
                }
            else:
                delete_field = {
                    'icon': '/static_media/images/icons/delete_disabled',
                    'icontitle': _('you need permission to delete this item')
                    }

            #calculate breaches_list
            breaches_summary = '\n\n'.join(
                [sb.get_summary_str()
                 for sb in o.scenariobreach_set.all()])

            #calculate string value for cutofflocations
            #todo: minimale en maximale tclose van
            #ScenarioCutoffLocation.object.filter(scenario=o)
            cutofflocations_summary = u'* %s: %d\n* %s: %d' % (
                _('count external'),
                o.cutofflocations.filter(
                    sobekmodels__sobekmodeltype=SobekModel.SOBEKMODELTYPE_CANAL
                    ).count(),
                _('count internal'),
                o.cutofflocations.filter(
              sobekmodels__sobekmodeltype=SobekModel.SOBEKMODELTYPE_INUNDATION
                    ).count(),
                )

            regions_str = '\n\n'.join(
                [r.name for r in Region.objects.filter(
                        breach__scenario__in=[o]).distinct()])

            row = [{'value': o.id},
                   {'url': o.get_scenarioresults_url(o.main_project.id),
                    'target': '_top',
                    'value': o},
                   {'value': o.get_status_cache_display()},
                   {'url': o.main_project.get_absolute_url(),
                    'value': o.main_project},
                   {'value': ''.join([b"* %s \n" % p.name for p in o.projects.all()])},
                   {'value': regions_str},
                   {'value': o.sobekmodel_inundation.get_summary_str()},
                   {'value': breaches_summary},
                   {'value': cutofflocations_summary},
                   delete_field,
                   ]
            table_data.append(row)

        #build search fields
        regionsets = permission_manager.get_regionsets(
            UserPermission.PERMISSION_SCENARIO_VIEW
            ).order_by('name')
        regions = permission_manager.get_regions().order_by('name')
        search_fields = [
            {'name': _('Search (scenario name or project name)'),
             'type': 'text',
             'output_field': 'q',
             'fields': (search_session['q'], ),
             },
            {'name': 'Status',
             'type':'checkbox',
             'output_field': 'status',
             'fields': (
                    (_('approved'), 20,
                     search_session['status'].count(20) != 0),
                    (_('disapproved'), 30,
                     search_session['status'].count(30) != 0),
                    (_('calculated'), 40,
                     search_session['status'].count(40) != 0),
                    (_('deleted'), 10,
                     search_session['status'].count(10) != 0),
                    (_('error'), 50,
                     search_session['status'].count(50) != 0),
                    (_('waiting'), 60,
                     search_session['status'].count(60) != 0),
                    (_('archive'), 80,
                     search_session['status'].count(80) != 0),
                    (_('none'), 70,
                     search_session['status'].count(70) != 0),
                    ),
             },
            {'name': _('RegionSet'),
             'type': 'option',
             'output_field': 'regionset',
             'fields': (tuple(
                        [(0, _('All regionsets'),
                          search_session['regionset'] == 0)] +
                        [(r.id, r.name,
                          r.id == search_session['regionset'])
                         for r in regionsets])),
             },
            {'id': 'search_region',
             'name': _('Region'),
             'type': 'option',
             'output_field': 'region',
             'options': {'onChange': 'javascript:updateBreaches()'},
             'fields': (tuple(
                        [(0, _('All regions'),
                          search_session['region'] == 0)] +
                        [(r.id, r.name,
                          r.id == search_session['region'])
                         for r in regions])),
             },
            {'id': 'search_breach',
             'name': _('Breach'),
             'type': 'option',
             'options': {'disabled': search_session['region'] == 0},
             'output_field': 'breach',
             'fields': (tuple(
                        [(0, _('All breaches'),
                          search_session['breach'] == 0)] +
                        [(b.id, b.name, b.id == search_session['breach'])
                         for b in Breach.objects.filter(
                                region=filter_region_object,
                                region__regionset__in=regionsets
                                ).order_by('name')])),
             },
            {'name': _('Waterlevel'),
             'type': 'multitext',
             'output_field': 'waterlevel',
             'fields': ({'label': _('less than'),
                         'field_postfix': '_lte',
                         'value': search_session['waterlevel_lte']},
                        {'label': _('greater than'),
                         'field_postfix': '_gte',
                         'value': search_session['waterlevel_gte']},
                        ),
             },
            {'name': _('Repeattime'),
             'type': 'multitext',
             'output_field': 'repeattime',
             'fields': ({'label': _('less than'),
                         'field_postfix': '_lte',
                         'value': search_session['repeattime_lte']},
                        {'label': _('greater than'),
                         'field_postfix': '_gte',
                         'value': search_session['repeattime_gte']},
                        ),
             },
            ]

        # Do we have any projects in which we can approve scenarios?
        # Pass that info to the template, which shows a link to the
        # share/accept page in that case.
        can_approve = permission_manager.get_projects(
            permission=UserPermission.PERMISSION_SCENARIO_APPROVE).exists()

        return render_to_response('flooding/scenario_list.html', {
                'is_embedded': is_embedded,
                'user': request.user,
                'name': _('Scenarios'),
                'breadcrumbs': [
                    {'name': _('Flooding'), 'url': reverse('flooding')},
                    {'name': _('Scenarios')},
                    ],
                'LANGUAGES': settings.LANGUAGES,
                'fields': search_session,
                'table_columns': table_columns,
                'table_data': table_data,
                'paginator': paginator,
                'page': page,
                'search_fields': search_fields,
                'can_approve': can_approve
                })


@receives_permission_manager
def scenario(request, permission_manager, object_id):
    """Renders page for a single scenario."""
    scenario = get_object_or_404(Scenario, pk=object_id)

    if not(permission_manager.check_project_permission(
            scenario.main_project,
            UserPermission.PERMISSION_SCENARIO_VIEW)):
        raise Http404  # user cannot see difference between no access
                       # and not existing

    return render_to_response('flooding/scenario_detail.html', {
            'user': request.user,
            'object': scenario,
            'breadcrumbs': [
                {'name': _('Flooding-home'), 'url': reverse('flooding')},
                {'name': _('Scenarios'),
                 'url': reverse('flooding_scenarios_url')},
                {'name': scenario.name},
                ]
            })


@receives_permission_manager
def project(request, permission_manager, object_id):
    """Renders page for single project."""
    project = get_object_or_404(Project, pk=object_id)

    if not(permission_manager.check_project_permission(
            project, UserPermission.PERMISSION_SCENARIO_VIEW)):
        raise Http404  # user cannot see difference between no access
                       # and not existing

    return render_to_response('flooding/project_detail.html', {
            'user': request.user,
            'object': project,
            'breadcrumbs': [
                {'name': _('Flooding'), 'url': reverse('flooding')},
                {'name': _('Projects'),
                 'url': reverse('flooding_projects_url')},
                {'name': project.name},
                ]
            })


@receives_permission_manager
def task(request, permission_manager, object_id):
    """Renders task detail.

    """
    task = get_object_or_404(Task, pk=object_id)

    if not(permission_manager.check_project_permission(
            task.scenario.main_project,
            UserPermission.PERMISSION_SCENARIO_VIEW)):
        raise Http404
    return render_to_response('flooding/task_detail.html', {
            'user': request.user,
            'object': task,
            })


#@login_required
@receives_permission_manager
def result_list(request, permission_manager):
    """Renders result list.

    #todo: filter result list, so you can see only a sublist
    """

    #stuff from request
    query = request.GET.get('q', '')
    items_per_page = int(request.GET.get('items_per_page', '25'))
    page_nr = int(request.GET.get('page_nr', '1'))
    sort = request.GET.get('sort', 'scenario')
    filter_resulttype = int(request.GET.get('filter_resulttype', -1))

    extra_fields = {'sort': sort,
                    'filter_resulttype': filter_resulttype,
                    'q': query,
                    'page_nr': page_nr,
                    'items_per_page': items_per_page,
                    }

    #for filter_resulttype
    resulttype_choices = tuple(
        [(-1, _('all resulttypes'))] +
        [(rt.id, str(rt))
         for rt in ResultType.objects.all()]
        )

    #from database
    projects = permission_manager.get_projects()
    if filter_resulttype == -1:
        lookup_query = {
            'scenario__scenarioproject__project__in': projects}
    else:
        lookup_query = {
            'scenario__scenarioproject__project__in': projects,
            'resulttype': get_object_or_404(
                ResultType, pk=filter_resulttype)}
    if query:
        objects = Result.objects.filter(
            Q(scenario__name__icontains=query) |
            Q(scenario__scenarioproject__project__name__icontains=query),
            **lookup_query)
    else:
        objects = Result.objects.filter(**lookup_query)

    #sort
    order_dict = {
        'id': 'id', 'id_rev': '-id',
        'scenario': 'scenario', 'scenario_rev': '-scenario',
        'project': 'scenario__scenarioproject__project',
        'project_rev': '-scenario__scenarioproject__project',
        'resulttype': 'resulttype', 'resulttype_rev': '-resulttype',
        }
    objects = objects.order_by(order_dict[sort])

    paginator = Paginator(objects, items_per_page)
    try:
        page = paginator.page(page_nr)
    except:
        page_nr = 1
        page = paginator.page(page_nr)

    #table preparation
    table_columns = [{'name': 'id',
                      'sort': 'id',
                      'sort_rev': 'id_rev'},
                     {'name': 'scenario',
                      'sort': 'scenario',
                      'sort_rev': 'scenario_rev'},
                     {'name': 'project',
                      'sort': 'project',
                      'sort_rev': 'project_rev'},
                     {'name': 'cutofflocations'},
                     {'name': 'scenario breaches'},
                     {'name': 'resulttype',
                      'sort': 'resulttype',
                      'sort_rev': 'resulttype_rev'},
                     ]
    table_data = []
    for o in page.object_list:
        row = []
        if o.scenario.cutofflocations.all():
            cutofflocations = ', '.join(
                [str(cl) for cl in o.scenario.cutofflocations.all()])
        else:
            cutofflocations = '-'
        if o.scenario.scenariobreach_set.all():
            scenariobreaches = ', '.join(
                [str(sb) for sb in o.scenario.scenariobreach_set.all()])
        else:
            scenariobreaches = '-'

        row = [{'value': o.id},
               {'url': reverse('flooding_scenario_detail',
                               kwargs={'object_id': o.scenario_id}),
                'value': o.scenario},

               {'url': reverse(
                    'flooding_project_detail',
                    kwargs={'object_id': o.scenario.main_project.id}),
                'value': o.scenario.main_project},
               {'value': cutofflocations},
               {'value': scenariobreaches},
               {'value': o.resulttype}]
        table_data.append(row)

    return render_to_response('flooding/result_list.html', {
            'user': request.user,
            'breadcrumbs': [
                {'name': _('Flooding'), 'url': reverse('flooding')},
                {'name': _('Results')},
                ],
            'LANGUAGES': settings.LANGUAGES,

            'fields': extra_fields,
            'paginator': paginator,
            'page': page,
            'resulttype_choices': resulttype_choices,
            'table_columns': table_columns,
            'table_data': table_data,
            })


def fractal(request):
    def rotate_scale(coords, angle, scale):
        return (scale * (cos(angle) * coords[0] - sin(angle) * coords[1]),
                scale * (sin(angle) * coords[0] + cos(angle) * coords[1]))

    def linelength(line):
        #approximately... but fast
        return max(abs(line[0] - line[2]), abs(line[1] - line[3]))
    image = Image.new("RGB", (1600, 850), "white")
    draw = ImageDraw.Draw(image)

    lines = [(600, 850, 600, 600)]
    scales = [0.8, 0.5]
    rotates = [0.5, -1]
    #scales = [0.8, 0.5, 0.3, 0.2]
    #rotates = [0.5, -1, -2, 2.5]

    #breadth first
    while lines:
        single_line = lines.pop(0)
        draw.line(single_line, fill="black")
        #now the fun part.. add lines

        new_lines = []
        for i in range(len(scales)):
            r_coords = rotate_scale(
                (single_line[2] - single_line[0],
                 single_line[3] - single_line[1]), rotates[i], scales[i])
            new_lines.append((single_line[2],
                              single_line[3],
                              single_line[2] + r_coords[0],
                              single_line[3] + r_coords[1]))
        for new_line in new_lines:
            if linelength(new_line) > 1:
                lines.append(new_line)

    response = HttpResponse(content_type="image/png")
    image.save(response, "PNG")
    return response


def result_download(request, result_id):
    result = get_object_or_404(Result, id=result_id)

    resultloc = result.resultloc.replace('\\', '/')

    # See etc/nginx.conf.in of flooding
    nginx_path = os.path.join('/download_results/', resultloc)
    file_path = os.path.join(settings.EXTERNAL_RESULT_MOUNTED_DIR, resultloc)

    logger.debug("NGINX PATH: " + nginx_path)
    logger.debug("FILE PATH: " + file_path)

    if settings.DEBUG:
        # When debugging, let Django serve the file
        return serve(request, file_path, '/')

    # Otherwise do it by letting Apache or Nginx serve it for us
    response = HttpResponse()
    response['X-Sendfile'] = file_path  # Apache
    response['X-Accel-Redirect'] = nginx_path  # Nginx

    # Unset the Content-Type as to allow for the webserver
    # to determine it.
    response['Content-Type'] = ''

    return response


class ExcelImportExportView(BaseView):
    template_name = "flooding/excel_import_export.html"

    @receives_permission_manager
    def get(self, request, permission_manager):
        self.permission_manager = permission_manager

        return super(ExcelImportExportView, self).get(request)

    def title(self):
        return Text.get(slug="excel_import_export_title")

    def summary(self):
        return Text.get(slug="excel_import_export_summary")

    def projects(self):
        """Return only those projects in which the current user has
        approval rights, and in which there is at least one
        scenario."""
        return self.permission_manager.get_projects(
            permission=UserPermission.PERMISSION_SCENARIO_APPROVE).annotate(
            num_scenarios=Count('scenarioproject')).filter(
                    num_scenarios__gt=0)


class ExcelImportExportViewProject(BaseView):
    template_name = "flooding/excel_import_export_project.html"

    def get(self, request):
        self.form = forms.ExcelImportForm()

        return super(ExcelImportExportViewProject, self).get(request)

    def post(self, request):
        self.form = forms.ExcelImportForm(request.POST, request.FILES)
        self.excel_errors = []

        if not self.permission_manager.check_project_permission(
            self.project(), UserPermission.PERMISSION_SCENARIO_EDIT):
            raise PermissionDenied()

        if self.form.is_valid():
            # Move file
            filename = request.FILES['excel_file'].name
            expected = self.project().excel_filename()
            if filename != expected:
                self.excel_error(
                    'Wrong filename, expected "{0}".'.format(expected))
            else:
                dest_path = os.path.join('/tmp/', expected)
                with open(dest_path, 'wb') as dest:
                    for chunk in request.FILES['excel_file'].chunks():
                        dest.write(chunk)

                # Only scenario_ids from this project are allowed
                allowed_scenario_ids = set(
                    scenarioproject.scenario_id
                    for scenarioproject in
                    ScenarioProject.objects.filter(
                        project__id=self.project_id).all())
                # Check it
                errors = excel_import_export.import_uploaded_excel_file(
                    dest_path, allowed_scenario_ids)

                if self.permission_manager.check_project_permission(
                   self.project(), UserPermission.PERMISSION_SCENARIO_APPROVE):
                    errors += (excel_import_export.
                               import_upload_excel_file_for_approval(
                            self.project(), request.user.get_full_name(),
                            dest_path, allowed_scenario_ids))

                # If successful, redirect
                if not errors:
                    return HttpResponseRedirect(
                        reverse(
                            'flooding_excel_import_export_project',
                            kwargs={'project_id': self.project_id}))

                self.excel_errors += errors

        return super(ExcelImportExportViewProject, self).get(request)

    def excel_error(self, message):
        self.excel_errors.append(message)

    def project(self):
        if not hasattr(self, '_project'):
            self._project = get_object_or_404(Project, pk=self.project_id)
        return self._project

    def last_changed(self):
        filename = os.path.join(
            settings.EXCEL_DIRECTORY, self.project().excel_filename())

        if not os.path.exists(filename):
            return u"het bestand bestaat nog niet"

        mtime = time.localtime(os.path.getmtime(filename))
        return unicode(datetime.datetime(
                mtime.tm_year, mtime.tm_mon, mtime.tm_mday,
                mtime.tm_hour, mtime.tm_min, mtime.tm_sec))


@receives_loggedin_permission_manager
def excel_download(request, permission_manager, project_id):
    project = get_object_or_404(Project, pk=project_id)

    # Check permissions
    if not permission_manager.check_project_permission(
        project, UserPermission.PERMISSION_SCENARIO_VIEW):
        raise PermissionDenied()

    filename = project.excel_filename()
    directory = settings.EXCEL_DIRECTORY
    full_path = os.path.join(directory, filename)

    # Make sure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    if (not os.path.exists(full_path) or
        not project.excel_generation_too_slow()):
        # Generate it if it's not there or generating isn't too slow
        from flooding_lib import excel_import_export
        excel_import_export.create_excel_file(
            project, project.original_scenarios(), full_path)

    return viewutil.serve_file(
        request=request,
        dirname=directory,
        filename=filename,
        nginx_dirname='/download_excel')


def ror_keringen_download(request, filename):
    
    # Check permissions
    user = User.objects.get(username=request.user)
    if user is None or not user.is_authenticated():
        raise PermissionDenied()

    directory = settings.ROR_KERINGEN_APPLIED_PATH
    full_path = os.path.join(directory, filename)
    response = viewutil.serve_file(
        request=request,
        dirname=directory,
        filename=filename,
        nginx_dirname='/download_ror_keringen_applied')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response


@receives_permission_manager
def preload_scenario_redirect(
    request, permission_manager, project_id, scenario_id):
    """View for going to the front page with a particular scenario
    opened. This finds the necessary ids and puts them in the session,
    then redirects to the front page."""
    project_id = int(project_id)
    scenario_id = int(scenario_id)

    scenario = Scenario.objects.get(pk=scenario_id)
    project = Project.objects.get(pk=project_id)

    if (not permission_manager.check_project_permission(
            project, UserPermission.PERMISSION_SCENARIO_VIEW) or
        not permission_manager.check_scenario_permission(
            scenario, UserPermission.PERMISSION_SCENARIO_VIEW)):
        raise PermissionDenied()

    breach = scenario.breaches.all()[0]

    preload_scenario = {
        "scenario_id": scenario_id,
        "project_id": project_id,
        "breach_id": breach.id,
        "region_id": breach.region.id
        }

    request.session['preload_scenario'] = preload_scenario

    return HttpResponseRedirect('/')
