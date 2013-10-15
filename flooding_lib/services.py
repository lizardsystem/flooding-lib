# -*- coding: utf-8 -*-
import Image
import StringIO
import mapnik
import os
import datetime

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson
from django.views.decorators.cache import never_cache

from flooding_lib import scenario_sharing
from flooding_base.models import Setting
from flooding_lib.models import Breach
from flooding_lib.models import CutoffLocationSet
from flooding_lib.models import EmbankmentUnit
from flooding_lib.models import ExternalWater
from flooding_lib.models import Measure
from flooding_lib.models import Project
from flooding_lib.models import Region
from flooding_lib.models import RegionSet
from flooding_lib.models import Result
from flooding_lib.models import Scenario
from flooding_lib.models import SobekModel
from flooding_lib.models import Strategy
from flooding_lib.models import UserPermission
from flooding_lib.permission_manager import receives_permission_manager
from flooding_lib.views import get_externalwater_csv
from flooding_lib.views import get_externalwater_graph
from flooding_lib.views import get_externalwater_graph_infowindow
from flooding_lib.views import get_externalwater_graph_session
from flooding_lib.views import service_compose_scenario
from flooding_lib.views import service_compose_3di_scenario
from flooding_lib.views import service_save_new_scenario
from flooding_lib.views import service_save_new_3di_scenario
from flooding_lib.views import service_select_strategy
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.tools.importtool.models import RORKering

SPHERICAL_MERCATOR = (
    '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 ' +
    '+lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null ' +
    '+no_defs +over')
RDS = (
    "+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 " +
    "+k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel " +
    "+towgs84=565.237,50.0087,465.658,-0.406857,0.350733," +
    "-1.87035,4.0812 +units=m +no_defs")

#-------------------- Services ----------------


def external_file_location(filename):
    """Return full filename of file that's on smb (currently)

    Old: look in database for config value and request smb file from windows.

    New: look if django setting exists and then assume a mounted directory.

    """
    if hasattr(settings, 'EXTERNAL_RESULT_MOUNTED_DIR'):
        # smb mounted on linux.
        base_dir = settings.EXTERNAL_RESULT_MOUNTED_DIR
        filename = filename.replace('\\', '/')
        full_name = os.path.join(base_dir, filename)
    else:
        # Windows direct smb link.
        base_dir = Setting.objects.get(key='destination_dir').value
        full_name = os.path.join(base_dir, filename.lstrip('\\').lstrip('/'))
    return str(full_name)


@never_cache
@receives_permission_manager
def service_get_region_tree(
    request, permission_manager,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW,
    filter_has_model=False):
    """Get a tree of regionsets and regions

    optional: Filter on permissions

    optional: Filter which selects regions through through project -
                    scenario - breaches - regions, otherwise
                    project-regionsets-regions

    optional: filter_onlyscenariobreaches=filter only the breaches in
    scenario's

    optional: filter_scenario: filter on scenario status. choices are
    None or Scenario.STATUS_*
    """
    if request.method == "GET":
        #see if there's a parameter called "permission"
        permission_from_get = request.GET.get('permission')
        if permission_from_get is not None:
            permission = int(permission_from_get)

    regionset_list = permission_manager.get_regionsets(permission)
    region_list_total = permission_manager.get_regions(permission)

    object_list = []
    for regionset in regionset_list:

        if filter_has_model:
            region_list = region_list_total.filter(
                regionset=regionset, sobekmodels__active=True
                ).order_by('name').distinct()
        else:
            region_list = region_list_total.filter(
                regionset=regionset).order_by('name')

        if region_list.count() > 0:
            rswest, rssouth, rseast, rsnorth = (1e8, 1e8, None, None)
            for region in region_list:
                west, south, east, north = region.geom.extent

                object_list.append({'rid': region.id,
                                    'name': region.__unicode__(),
                                    'parentid': regionset.id,
                                    'isregion': True,
                                    'west': west,
                                    'south': south,
                                    'east': east,
                                    'north': north,
                                    })
                #used function below because of performance. Instead
                #of #west, south, east, north =
                #regionset.regions.unionagg().extent
                if east:
                    rswest = min(rswest, west)
                    rssouth = min(rssouth, south)
                    rseast = max(rseast, east)
                    rsnorth = max(rsnorth, north)

            if regionset.parent:
                parentid = regionset.parent.id
            else:
                parentid = None
            #add regionset

            object_list.append({'rsid': regionset.id,
                                'name': regionset.__unicode__(),
                                'parentid': parentid,
                                'isregion': False,
                                'west': rswest,
                                'south': rssouth,
                                'east': rseast,
                                'north': rsnorth,
                                })

    return HttpResponse(
        simplejson.dumps(object_list), mimetype="application/json")
#render_to_response('flooding/regiontree.json', {'object_list': object_list})


def service_get_region_maps(request,
                            region_id):
    """Get maps linked to scenario's

    """

    region = get_object_or_404(Region, pk=region_id)
    print str(region)
    object_list = []
    for map in region.maps.filter(active=True).order_by('index'):
        print map
        object_list.append({'id': map.id,
                            'name': map.name,
                            'url': map.url,
                            'layers': map.layers,
                            'transparent': map.transparent,
                            'tiled': map.tiled,
                            'srs': map.srs
                            })

    response = HttpResponse(
        simplejson.dumps(object_list), mimetype="application/json")
    response['Cache-Control'] = 'max-age=0'
    return response


def breach_info_url(breach, permission_manager):
    """If user has approval rights in one of the special projects
    (ROR, etc), and this breach has scenarios in that project, a link
    to the breach info page will be shown next to it. Otherwise,
    return None."""

    for project_id in scenario_sharing.PROJECT_IDS:
        project = Project.objects.get(pk=project_id)
        if not permission_manager.check_project_permission(
            project=project,
            permission=UserPermission.PERMISSION_SCENARIO_APPROVE):
            continue

        if permission_manager.get_scenarios(breach=breach).filter(
            scenarioproject__project=project).exists():
            return reverse(
                'flooding_breachinfo_page',
                kwargs=dict(project_id=project_id, breach_id=breach.id))

    return None


@never_cache
@receives_permission_manager
def service_get_breach_tree(
    request, permission_manager,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW,
    region_id=None, filter_onlyscenariobreaches=False,
    filter_scenario=None, filter_active=None):
    """Get breaches and external waters in a tree.

    optional: filter on region. find out all breaches of a region,
    build tree with external waters and breaches

    optional: Filter on permissions

    optional: filter_onlyscenariobreaches=filter only the breaches in
    scenario's

    optional: filter_scenario: filter on scenario status. choices are
    None or Scenario.STATUS_*

    """
    import pdb; pdb.set_trace()
    scenarios = permission_manager.get_scenarios(
        None, permission, filter_scenario)

    if region_id:
        region = get_object_or_404(Region, pk=region_id)
        if not(permission_manager.check_region_permission(
                region, permission)):
            raise Http404
        if filter_onlyscenariobreaches:
            breach_list = region.breach_set.filter(
                scenario__in=scenarios).distinct()
        else:
            breach_list = region.breach_set.filter(active=True)
    else:
        if not(permission_manager.check_permission(permission)):
            raise Http404
        if filter_onlyscenariobreaches:
            breach_list = Breach.objects.filter(
                scenario__in=scenarios).distinct()
        else:
            breach_list = Breach.objects.filter(active=True)

    #if filter_active == 1:
    #     breach_list = breach_list.filter(active=True)

    externalwater_list = ExternalWater.objects.filter(
        breach__in=breach_list).distinct()

    object_list = [
        {'id': -ew.id,
         'name': unicode(ew),
         'type': ew.type,
         'parentid': None,
         'isbreach': False,
         'info_url': None,
         }
        for ew in externalwater_list]

    object_list += [
        {'id': breach.id,
         'name': unicode(breach),
         'parentid': -breach.externalwater.id,
         'isbreach': True,
         'x': breach.geom.x,
         'y': breach.geom.y,
         'info_url': breach_info_url(breach, permission_manager),
         }
        for breach in breach_list]

    return HttpResponse(
        simplejson.dumps(object_list), mimetype="application/json")


@never_cache
@receives_permission_manager
def service_get_scenario_tree(
    request, permission_manager, breach_id,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW,
    filter_scenarioproject=None,
    filter_onlyprojectswithscenario=False,
    filter_scenariostatus=None):
    """Get tree with projects and scenario's as leafs given a single breach.

    Input: breach_id from GET
    (optional) filter_scenariostatus None/0(=None)/status code

    """
    if filter_scenariostatus == 0:
        filter_scenariostatus = []

    #select all projects that you can see
    scenario_list = permission_manager.get_scenarios(
        breach_id, permission, filter_scenariostatus)

    permitted_projects = permission_manager.get_projects(permission)
    #only projects with scenario
    if filter_onlyprojectswithscenario:
        project_list = Project.in_scenario_list(scenario_list).distinct()
    else:
        project_list = permitted_projects

    object_list = []
    projects_shown = set()

    for scenario in scenario_list:
        # If a scenario is in multiple projects, we add it to the object
        # list once for each project.
        for project in scenario.projects.all():
            if (project in permitted_projects and
                scenario.visible_in_project(
                    permission_manager, project, permission)):

                projects_shown.add(project.id)
                object_list.append({'sid': scenario.id,
                                    'name': scenario.__unicode__(),
                                    'parentid': project.id,
                                    'isscenario': True,
                                    'status': scenario.get_status(),
                                    'strategy_id': scenario.strategy_id,
                                    })
    for project in project_list:
        # Only show the projects under which there are actually
        # scenarios visible to this user.
        if project.id in projects_shown:
            object_list.append({'pid': project.id,
                                'name': project.__unicode__(),
                                'parentid': None,
                                'isscenario': False,
                                'status': 0,
                                })

    return HttpResponse(
        simplejson.dumps(object_list), mimetype="application/json")


@never_cache
@receives_permission_manager
def service_get_cutofflocations_from_scenario(
    request, permission_manager, scenario_id,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get cutofflocations of given scenario.

    Conditions:
    - from given scenario (check permission for given scenario)
    - given permission level
    """
    scenario = get_object_or_404(Scenario, pk=scenario_id)

    if not(permission_manager.check_project_permission(
            scenario.main_project, permission)):
        raise Http404
    scenariocutofflocation_list = scenario.scenariocutofflocation_set.all()

    return render_to_response('flooding/scenariocutofflocation.json',
                              {'object_list': scenariocutofflocation_list})

# Request used by 'new scenarios', 'table', 'import', 'export'


@never_cache
@receives_permission_manager
def service_get_project_regions(
    request, permission_manager, project_id,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get all regions for a given project_id and given permission."""
    project = Project.objects.filter(id=project_id)
    regions = []
    if project.exists():        
        regionsets = project[0].regionsets.all()
    
        for regionset in regionsets:
            if (permission_manager.check_regionset_permission(
                    regionset, permission)):
                regions.extend([r for r in regionset.get_all_regions()])
                 
        result_list = [{'id': r.id, 'name': str(r.name)} for r in regions]
    else:
        result_list = []
    return HttpResponse(
        simplejson.dumps(
            {'identifier': 'id',
             'label': 'name',
             'items': result_list}), mimetype="application/json")


@never_cache
@receives_permission_manager
def service_get_regions(
    request, permission_manager, regionset_id,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get all regions for a given regionset_id and given permission."""
    regionset = get_object_or_404(RegionSet, pk=regionset_id)

    if not(permission_manager.check_regionset_permission(
            regionset, permission)):
        raise Http404
    if request.user.is_staff:
        filter_active = None
    else:
        filter_active = True
    regions = regionset.get_all_regions(filter_active)
    result_list = [{'id': r.id, 'name': str(r.name)} for r in regions]
    return HttpResponse(
        simplejson.dumps(result_list), mimetype="application/json")


@never_cache
@receives_permission_manager
def service_get_regionsets(
    request, permission_manager,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get all regionsets where you have the given permission."""
    if request.method == "GET":
        #see if there's a parameter called "permission"
        permission_from_get = request.GET.get('permission')
        if permission_from_get is not None:
            permission = int(permission_from_get)

    regionsets = permission_manager.get_regionsets(permission).order_by('name')
    result_list = [{'id': r.id, 'name': str(r.name)} for r in regionsets]
    return HttpResponse(
        simplejson.dumps(result_list), mimetype="application/json")


@never_cache
@receives_permission_manager
def service_get_breaches(
    request, permission_manager, region_id, scenariofilter=-1):
    """Get breaches from a given region_id.

    * breaches from given region_id (permissions: scenario_view), if
      not existent, return []

    * optional scenariofilter (all,approved,disapproved, to be approved).

    """
    try:
        region = Region.objects.get(pk=region_id)
    except Region.DoesNotExist:
        return HttpResponse(simplejson.dumps([]), mimetype="application/json")

    if not(permission_manager.check_region_permission(
            region,
            UserPermission.PERMISSION_SCENARIO_VIEW)):
        raise Http404

    if scenariofilter == -1:
        breaches = region.breach_set.all().order_by('name')
    else:
        breaches = region.breach_set.filter(
            scenario__status_cache=scenariofilter
            ).order_by('name').distinct()

    result_list = [{'id': b.id, 'name': str(b)} for b in breaches]

    return HttpResponse(
        simplejson.dumps(result_list), mimetype="application/json")


@never_cache
@receives_permission_manager
def service_get_projects(
    request, permission_manager,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get the list of projects with given permission and return in
    JSON format."""

    project_list = permission_manager.get_projects(permission)
    return render_to_response(
        'flooding/project.json',
        {'project_list': project_list})


def get_breaches_info(scenario):
    info = {}
    breaches = scenario.breaches.all()
    breaches_values= breaches.values(
        "name", "id", "region__id", "region__name", "externalwater__name",
        "externalwater__type")
    info["names"] = [v.get("name") for v in breaches_values]
    info["ids"] = [v.get("id") for v in breaches_values]
    info["region_names"] = [v.get("region__name") for v in breaches_values]
    info["region_ids"] = [v.get("region__id") for v in breaches_values]
    info["externalwater_name"] = [v.get("externalwater__name") for v in breaches_values]
    info["externalwater_type"] = [v.get("externalwater__type") for v in breaches_values]
    return info
        

@never_cache
@receives_permission_manager
def service_get_scenarios_export_list(
    request, permission_manager, project_id,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """
    Gets the scenario list with all scenarios, with all the info neede
    for displaying in the drag and drop window for the export tool.
    """
    project = get_object_or_404(Project, pk=project_id)
    inputfield_calcmethod = InputField.objects.get(pk=45)
    inputfield_statesecurity = InputField.objects.get(pk=34)
    inputfield_shelflife = InputField.objects.get(pk=27)
    if not(permission_manager.check_project_permission(project, permission)):
        raise Http404
    scenarios_export_list = []
    for s in project.all_scenarios():
        breaches_values = get_breaches_info(s)
        scenarios_export_list.append(
            {
                'scenario_id': s.id,
                'scenario_name': s.name,
                'breach_ids': breaches_values.get("ids"),
                'breach_names': breaches_values.get("names"),
                'region_ids': breaches_values.get("region_ids"),
                'region_names': breaches_values.get("region_names"),
                'extwname': breaches_values.get("externalwater_name"),
                'extwtype': breaches_values.get("externalwater_type"),
                'project_id': project.id,
                'project_name': project.name,
                'project_id': project.id,
                'project_name': project.name,
                'owner_id': s.owner.id,
                'owner_name': s.owner.username,
                'extwrepeattime': [sbr.extwrepeattime for sbr in s.scenariobreach_set.all()],
                '_visible': True
            })
    ## Bij ROR project neem te veel tijd, request wordt gekilld
    ## Niet verwijderen totdat er een definitief oplossing komt.

    # scenarios_export_list = [
    #     {
    #         'scenario_id': s.id,
    #         'scenario_name': s.name,
    #         'breach_ids': [br.id for br in s.breaches.all()],
    #         'breach_names': [br.name for br in s.breaches.all()],
    #         'region_ids': [br.region.id for br in s.breaches.all()],
    #         'region_names': [br.region.name for br in s.breaches.all()],
    #         'extwname': [br.externalwater.name for br in s.breaches.all()],
    #         'extwtype': [br.externalwater.get_type_display() for br in s.breaches.all()],
    #         'project_id': project.id,
    #         'project_name': project.name,
    #         'owner_id': s.owner.id,
    #         'owner_name': s.owner.username,
    #         'calcmethod': s.string_value_for_inputfield(inputfield_calcmethod),
    #         'statesecurity': s.string_value_for_inputfield(inputfield_statesecurity),
    #         'shelflife': s.string_value_for_inputfield(inputfield_shelflife),
    #         'extwrepeattime': [sbr.extwrepeattime for sbr in s.scenariobreach_set.all()]}
    #     for s in project.all_scenarios()]
    return HttpResponse(
        simplejson.dumps(scenarios_export_list), mimetype="application/json")


@never_cache
@receives_permission_manager
def service_get_all_regions(
    request, permission_manager,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get the list of regions with given permission and return in
    JSON format."""

    regions = permission_manager.get_regions(permission).order_by('name')
    result_list = [{'id': r.id, 'name': str(r.name)} for r in regions]
    return HttpResponse(
        simplejson.dumps(result_list), mimetype="application/json")


@never_cache
def service_get_inundationmodels(
    request, region_id=None, only_active=True):
    """Get inundationmodels, with filter region_id and SobekModel.active
    * in gebruik bij flooding new, stap 2
    """
    region = get_object_or_404(Region, pk=region_id)
    if only_active:
        models = region.sobekmodels.filter(active=True)
    else:
        models = region.externalwater.sobekmodels.all()

    resp = [{
            'id':obj.id,
            'name': str(obj.model_version) + ', ' + str(obj.model_varname),
            'is_3di': obj.is_3di()
            } for obj in models]
    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')


@never_cache
def service_get_externalwatermodels(
    request, breach_id, only_active=True):
    """Get externalwater models , with filter breach_id and SobekModel.active
    * in gebruik bij flooding new, stap 2
    """
    breach = get_object_or_404(Breach, pk=breach_id)

    if only_active:
        models = breach.externalwater.sobekmodels.filter(active=True)
    else:
        models = breach.externalwater.sobekmodels.all()

    resp = [{
            'id':obj.id,
            'name':str(obj.model_version) + ', ' + str(obj.model_varname)
            } for obj in models]

    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')


@never_cache
def service_get_cutofflocations(
    request, inundationmodel_id=None, extwatermodel_id=None):
    """Get cutofflocations, with filter region_id and/or externalwater_id
    """
    if inundationmodel_id:
        inundationmodel = get_object_or_404(SobekModel, pk=inundationmodel_id)
    else:
        inundationmodel = None
    if extwatermodel_id:
        extwatermodel = get_object_or_404(SobekModel, pk=extwatermodel_id)
    else:
        extwatermodel = None
    cl_list = []
    if inundationmodel:
        cl_list.extend(inundationmodel.cutofflocation_set.all())
    if extwatermodel:
        cl_list.extend(extwatermodel.cutofflocation_set.all())

    resp = []
    for obj in cl_list:
        loc = obj.geom
        resp.append({
                'id': obj.id,
                'name': obj.name,
                'type': obj.type,
                'action': 1,
                'tdef': obj.deftclose,
                'x': loc.x,
                'y': loc.y})
    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')


@never_cache
def service_get_cutofflocationsets(
    request, inundationmodel_id=None, extwatermodel_id=None):
    """Get cutofflocations, with filter region_id and/or externalwater_id
    """
    cutofflocationset = []
    if inundationmodel_id:
        inundationmodel = get_object_or_404(SobekModel, pk=inundationmodel_id)
        cutofflocationset.extend(
            CutoffLocationSet.objects.filter(
                cutofflocations__sobekmodels=inundationmodel).distinct())
    if extwatermodel_id:
        extwatermodel = get_object_or_404(SobekModel, pk=extwatermodel_id)
        cutofflocationset.extend(
            CutoffLocationSet.objects.filter(
                cutofflocations__sobekmodels=extwatermodel).distinct())
    resp = []
    for set in cutofflocationset:
        cutofflocation_ids = [obj.id for obj in set.cutofflocations.all()]
        resp.append({
                'id': set.id,
                'name': set.name,
                'number': len(cutofflocation_ids),
                'cuttofflocation': cutofflocation_ids})
    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')


@never_cache
@receives_permission_manager
def service_get_cutofflocations_from_cutofflocationset(
    request, permission_manager, cutofflocationset_id, permission):
    """Get cutofflocations, given cutofflocationset_id
    """
    cls = get_object_or_404(CutoffLocationSet, pk=cutofflocationset_id)
    if request.user.is_authenticated() and request.user.is_staff:
        object_list = cls.cutofflocations.all()
    else:
        projects = permission_manager.get_projects(permission)
        object_list = cls.cutofflocations.filter(
            region__regionset__project__in=projects).distinct()
    return render_to_response('flooding/cutofflocation.json',
                              {'object_list': object_list})


@never_cache
def service_get_result_settings(
    request, result_id):
    """get_result_settings, with filter result_id
        voor resultaten met figuren, haalt afmetingen en extents op
    """
    result = get_object_or_404(Result, pk=result_id)

    settings_in_db = Setting.objects.get(key='destination_dir')
    png_name = settings_in_db.value + "\\" + result.resultpngloc
    if result.resulttype.overlaytype == 'ANIMATEDMAPOVERLAY':
        numberstring = '%4i' % result.firstnr
        numberstring = numberstring.replace(" ", "0")
        png_name = png_name.replace('####', numberstring)
    pgw_name = png_name.replace(".png", ".pgw")
    pgwfile = open(pgw_name, 'r')
    pgwfields = pgwfile.readlines()
    pgwfile.close()

    gridsize, a, b, c, west, north = [float(s) for s in pgwfields]

    picture = Image.open(png_name)
    width, height = picture.size

    east = west + width * gridsize
    south = north - height * gridsize

    pictureinfo = {
        'gridsize': gridsize,
        'width': width,
        'height': height,
        'north': north,
        'west': west,
        'east': east,
        'south': south,
        'projection': 'rds',
    }

    return render_to_response(
        'flooding/result_settings.json',
        {'result': result, 'pictureinfo': pictureinfo})


@never_cache
def service_get_presentations_of_scenario(
    request, scenario_id, type_filter=None,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get presentationlayers of given scenario with a filter on custom type
    input:
        scenario_id:
        type_filter: name of 'custom' presentationtype filter (is in
        te stellen door gebruiker)

    Conditions:
    - from given scenario (check permission for given scenario)
    - return only presentationtypes allowed by userpermission

    return:
        id: presentationlayer_id

        name: presentationtype_name (short name)

        overlaytype: presentationtype_overlaytype - integer - (wms,
        map, general, (point, line))

        type: presentationtype_valuetype - integer - (timeserie,
        classification, singlevalue, static)
    """
    scenario = get_object_or_404(Scenario, pk=scenario_id)

    players = scenario.presentationlayer.filter(
        presentationtype__custom_indicator__name='flooding_result'
        ).select_related('presentationtype').order_by(
        'presentationtype__order_index')
    resp = []
    for pl in players:
        name = pl.presentationtype.name
        if pl.value:
            if pl.value > 1000000:
                name = ("%s (%.1f miljoen %s)" %
                        (name, pl.value / 1000000, pl.presentationtype.unit))
            elif pl.value < 10:
                name = ("%s (%.1f %s)" %
                        (name, pl.value, pl.presentationtype.unit))
            else:
                name = ("%s (%.0f %s)" %
                        (name, pl.value, pl.presentationtype.unit))

        resp.append({
                'id': pl.id,
                'name': name,
                'prestypeid': pl.presentationtype.id,
                'geoType': pl.presentationtype.geo_type,
                'valueType': pl.presentationtype.value_type})

    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')


@never_cache
def service_get_raw_result(
    request, presentationlayer):
    '''

    '''
    result = Result.objects.filter(
        resulttype__presentationtype__presentationlayer=presentationlayer,
        scenario__presentationlayer=presentationlayer)
    if (result.count() == 1):
        file_name = external_file_location(result[0].resultloc)

        response = HttpResponse(open(file_name, 'rb').read())
        response['Content-type'] = 'application/zip'
        response['Content-Disposition'] = (
            'attachment; filename=' + os.path.split(file_name)[1])

        return response

    resp = {'opmerking': 'Ruwe resultaten niet beschikbaar'}
    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')


@never_cache
@receives_permission_manager
def service_get_attachment(request, permission_manager, scenario_id, path):
    """ Returns a non-public attachment if one has the permission

    """

    scenario = get_object_or_404(Scenario, pk=scenario_id)

    if not permission_manager.check_project_permission(
        scenario.main_project, UserPermission.PERMISSION_SCENARIO_VIEW):
        raise Http404

    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.isfile(file_path):
        return HttpResponse('Het opgevraagde bestand bestaat niet.')

    file_name = os.path.split(path)[1]
    file_object = open(file_path, 'rb')
    response = HttpResponse(file_object.read())
    response['Content-Disposition'] = (
        'attachment; filename="' + file_name + '"')
    file_object.close()
    return  response


@never_cache
@receives_permission_manager
def service_get_import_scenario_uploaded_file(
    request, permission_manager, path):
    """ Returns a non-public uploaded file if one has the permission

    """
    if not(permission_manager.check_permission(
            UserPermission.PERMISSION_SCENARIO_ADD)):
        raise Http404

    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.isfile(file_path):
        return HttpResponse('Het opgevraagde bestand bestaat niet.')

    file_name = os.path.split(path)[1]
    file_object = open(file_path, 'rb')
    response = HttpResponse(file_object.read())
    response['Content-Disposition'] = (
        'attachment; filename="' + file_name + '"')
    file_object.close()
    return  response


@never_cache
def service_get_existing_embankments_shape(
    request, width, height, bbox, region_id, strategy_id,
    only_selected=False):
    """
    Returns a png with:

    - the existing embankments (that are splitted in several units
      that are selectable)

    - the new drawn embankments

    - the selecte embankments (by polygon selection)

    width = int
    height = int
    bbox = tuple
    """

    #################### set up map ###################################
    m = mapnik.Map(width, height)

    m.srs = SPHERICAL_MERCATOR
    m.background = mapnik.Color('transparent')

    #### Line style for new embankments
    s2 = mapnik.Style()
    rule_2 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(128, 0, 128)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_2.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s2.rules.append(rule_2)
    m.append_style('Line Style New Embankment', s2)

    #### Line style for polygon selections
    s3 = mapnik.Style()
    rule_3 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(0, 255, 0)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_3.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s3.rules.append(rule_3)
    m.append_style('Line Style Polygon Selection', s3)

    #### Line style for the embankment units that can be selected
    s4 = mapnik.Style()
    rule_4 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(200, 200, 200)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 2
    rule_4.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s4.rules.append(rule_4)
    m.append_style('Line Style Specific Region', s4)

    #### Line style for region boundary
    s5 = mapnik.Style()
    rule_5 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(0, 0, 0)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 2.0
    rule_5.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s5.rules.append(rule_5)
    m.append_style('Line Style Region Boundary', s5)

    #### Get layer for a  region (boundary)
    lyr_region = mapnik.Layer('Geometry from PostGIS')
    lyr_region.srs = '+proj=latlong +datum=WGS84'
    BUFFERED_TABLE = (
        '(SELECT geom FROM flooding_region WHERE id = %i) region' %
        region_id)

    database = settings.DATABASES['default']

    lyr_region.datasource = mapnik.PostGIS(host=database['HOST'],
                                           user=database['USER'],
                                           password=database['PASSWORD'],
                                           dbname=database['NAME'],
                                           table=str(BUFFERED_TABLE))

    lyr_region.styles.append('Line Style Region Boundary')
    m.layers.append(lyr_region)

    #### Get layer for a specific region (embankment units)
    lyr_specific_region = mapnik.Layer('Geometry from PostGIS')
    lyr_specific_region.srs = '+proj=latlong +datum=WGS84'
    BUFFERED_TABLE = (
        '''(SELECT geometry
            FROM flooding_embankment_unit
            WHERE type=0
            AND region_id=%i)
            specific_region''' %
        region_id)
    lyr_specific_region.datasource = mapnik.PostGIS(
        host=database['HOST'],
        user=database['USER'],
        password=database['PASSWORD'],
        dbname=database['NAME'],
        table=str(BUFFERED_TABLE))
    lyr_specific_region.styles.append('Line Style Specific Region')
    m.layers.append(lyr_specific_region)

    #### Get layer for new embankments
    lyr_new_embankments = mapnik.Layer('Geometry from PostGIS')
    lyr_new_embankments.srs = '+proj=latlong +datum=WGS84'
    BUFFERED_TABLE = '''
        (SELECT fe.geometry
         AS geometry
         FROM flooding_embankment_unit fe,
              flooding_strategy fs,
              flooding_embankment_unit_measure fem,
              flooding_measure_strategy fms,
              flooding_measure fm
         WHERE fs.id = fms.strategy_id
         AND fms.measure_id = fm.id
         AND fm.id = fem.measure_id
         AND fem.embankmentunit_id = fe.id
         AND fe.type=1
         AND fs.id=%i)
         polygon_new_embankements''' % strategy_id
    lyr_new_embankments.datasource = mapnik.PostGIS(
        host=database['HOST'],
        user=database['USER'],
        password=database['PASSWORD'],
        dbname=database['NAME'],
        table=str(BUFFERED_TABLE))
    lyr_new_embankments.styles.append('Line Style New Embankment')
    m.layers.append(lyr_new_embankments)

    #### Get layer for polygon selected embankments
    lyr_polygon_selected_embankments = mapnik.Layer('Geometry from PostGIS')
    lyr_polygon_selected_embankments.srs = '+proj=latlong +datum=WGS84'
    BUFFERED_TABLE = '''
        (SELECT fe.geometry
         AS geometry
         FROM flooding_embankment_unit fe,
              flooding_strategy fs,
              flooding_embankment_unit_measure fem,
              flooding_measure_strategy fms,
              flooding_measure fm
         WHERE fs.id = fms.strategy_id
         AND fms.measure_id = fm.id
         AND fm.id = fem.measure_id
         AND fem.embankmentunit_id = fe.id
         AND fe.type=0
         AND fs.id=%i)
         polygon_selected_embankements''' % strategy_id

    lyr_polygon_selected_embankments.datasource = mapnik.PostGIS(
        host=database['HOST'],
        user=database['USER'],
        password=database['PASSWORD'],
        dbname=database['NAME'],
        table=str(BUFFERED_TABLE))
    lyr_polygon_selected_embankments.styles.append(
        'Line Style Polygon Selection')
    m.layers.append(lyr_polygon_selected_embankments)

    ##################### render map #############################
    m.zoom_to_box(mapnik.Envelope(*bbox))
    #m.zoom_to_box(lyrl.envelope())

    img = mapnik.Image(width, height)
    mapnik.render(m, img)

    # you can use this if you want te modify image with PIL
    imgPIL = Image.fromstring(
        'RGBA', (width, height), img.tostring())
    #imgPIL = imgPIL.convert('RGB')
    buffer = StringIO.StringIO()
    imgPIL.save(buffer, 'png')
    buffer.seek(0)

    response = HttpResponse(buffer.read())
    response['Content-type'] = 'image/png'
    return response


def service_get_extra_shapes(request, width, height, bbox, region_id):
    """
    Return the Keringen-shapes that already exist.

    width = int
    height = int
    bbox = tuple
    """

    #################### set up map ###################################
    m = mapnik.Map(width, height)

    m.srs = SPHERICAL_MERCATOR
    m.background = mapnik.Color('transparent')

    #### Line style for Primaire keringen
    sl = mapnik.Style()
    rule_l = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(0, 0, 200)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_l.symbols.append(mapnik.LineSymbolizer(rule_stk))
    sl.rules.append(rule_l)
    m.append_style('Line Style Primaire Keringen', sl)

    #### Line style for Regionale keringen met Functie
    s2 = mapnik.Style()
    rule_2 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(200, 0, 0)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_2.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s2.rules.append(rule_2)
    m.append_style('Line Style Regionale Keringen Met Functie', s2)

    #### Line style for Keringen buiten de provincie
    s4 = mapnik.Style()
    rule_4 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(235, 235, 50)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_4.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s4.rules.append(rule_4)
    m.append_style('Line Style Keringen Buiten De Provincie', s4)

    #### Get layer for shape file
    lyrl = mapnik.Layer('lines', RDS)
    lyrl.datasource = mapnik.Shapefile(
        file=os.path.join(settings.GIS_DIR, 'primairekering.shp'))
    lyrl.styles.append('Line Style Primaire Keringen')
    m.layers.append(lyrl)

    lyr2 = mapnik.Layer('lines', RDS)
    lyr2.datasource = mapnik.Shapefile(
        file=os.path.join(settings.GIS_DIR, 'kering_buitenprov.shp'))
    lyr2.styles.append('Line Style Keringen Buiten De Provincie')
    m.layers.append(lyr2)

    lyr3 = mapnik.Layer('lines', RDS)
    lyr3.datasource = mapnik.Shapefile(
        file=os.path.join(settings.GIS_DIR, 'ontwerp_Regionale_keringen.shp'))
    lyr3.styles.append('Line Style Regionale Keringen Met Functie')
    m.layers.append(lyr3)

    ##################### render map #############################
    m.zoom_to_box(mapnik.Envelope(*bbox))
    #m.zoom_to_box(lyrl.envelope())

    img = mapnik.Image(width, height)
    mapnik.render(m, img)

    # you can use this if you want te modify image with PIL
    imgPIL = Image.fromstring('RGBA', (width, height), img.tostring())
    #imgPIL = imgPIL.convert('RGB')
    buffer = StringIO.StringIO()
    imgPIL.save(buffer, 'png')
    buffer.seek(0)

    response = HttpResponse(buffer.read())
    response['Content-type'] = 'image/png'
    return response


def service_get_extra_grid_shapes(request, width, height, bbox, region_id):
    """
    width = int
    height = int
    bbox = tuple

    Returns the Elevation model
    """

    #################### set up map ###################################
    m = mapnik.Map(width, height)

    m.srs = SPHERICAL_MERCATOR
    m.background = mapnik.Color('transparent')

    s = mapnik.Style()
    r = mapnik.Rule()
    rs = mapnik.RasterSymbolizer()
    r.symbols.append(rs)
    s.rules.append(r)
    #styles['geotiff'] = s
    m.append_style('geotiff', s)

    #### Get layer for shape file
    raster = mapnik.Gdal(
        file=os.path.join(settings.GIS_DIR, 'ahn5_medtot_gm_trans.tif'))
    lyrl = mapnik.Layer('Tiff Layer', SPHERICAL_MERCATOR)
    lyrl.datasource = raster
    #lyrl.styles.append('Geotiff Style')
    lyrl.styles.append('geotiff')
    m.layers.append(lyrl)

    ##################### render map #############################
    m.zoom_to_box(mapnik.Envelope(*bbox))
    #m.zoom_to_box(lyrl.envelope())

    img = mapnik.Image(width, height)
    mapnik.render(m, img)

    # you can use this if you want te modify image with PIL
    imgPIL = Image.fromstring('RGBA', (width, height), img.tostring())
    #imgPIL = imgPIL.convert('RGB')
    buffer = StringIO.StringIO()
    imgPIL.save(buffer, 'png')
    buffer.seek(0)

    response = HttpResponse(buffer.read())
    response['Content-type'] = 'image/png'
    return response


def service_save_drawn_embankment(geometries, strategy_id, region_id):

    selected_strategy = Strategy.objects.get(pk=strategy_id)
    selected_measure = selected_strategy.measure_set.create(name='Ingetekend')

    region = Region.objects.get(pk=region_id)

    if len(geometries) > 0:
        for geometry in geometries.split(';'):
            line = GEOSGeometry(geometry, srid=900913)
            embankment_unit = EmbankmentUnit(
                unit_id=-999,
                type=EmbankmentUnit.TYPE_NEW,
                original_height=-999,
                region=region,
                geometry=line)
            embankment_unit.save()
            selected_measure.embankmentunit_set.add(embankment_unit)

        answer = {
            'successful': True,
            'id': selected_measure.id,
            'name': selected_measure.name,
            'number_embankment_units':
            selected_measure.embankmentunit_set.all().count()}
        return HttpResponse(
            simplejson.dumps(answer), mimetype="application/json")
    else:
        answer = {'successful': False}
        return HttpResponse(
            simplejson.dumps(answer), mimetype="application/json")


def select_existing_embankments_by_polygon(geometries, strategy_id, region_id):
    if len(geometries) > 0:
        geometries = geometries.split(';')

        joining_polygon = []
        for i in range(0, len(geometries)):
            joining_polygon.append(GEOSGeometry(geometries[i], srid=900913))

        multi_polygon = MultiPolygon(joining_polygon)
        multi_polygon.srid = 900913

        selected_strategy = Strategy.objects.get(pk=strategy_id)
        selected_measure = selected_strategy.measure_set.create(name='test')
        selected_measure.name = "Bestaand (%i)" % selected_measure.id
        selected_measure.save()

        selected_embankment_units = EmbankmentUnit.objects.filter(
            region=region_id, type=EmbankmentUnit.TYPE_EXISTING
            ).exclude(measure=selected_measure).filter(
            geometry__intersects=multi_polygon)
        selected_measure.embankmentunit_set.add(*selected_embankment_units)

        answer = {
            'successful': True,
            'id': selected_measure.id,
            'name': selected_measure.name,
            'number_embankment_units':
            selected_measure.embankmentunit_set.all().count()}
        return HttpResponse(
            simplejson.dumps(answer), mimetype="application/json")
    else:
        answer = {'successful': False}
        return HttpResponse(
            simplejson.dumps(answer), mimetype="application/json")


def service_delete_measure(measure_ids):

    measure_ids = [int(id) for id in measure_ids.split(';')]
    Measure.objects.filter(id__in=measure_ids).delete()
    answer = {'successful': True}
    return HttpResponse(simplejson.dumps(answer), mimetype="application/json")


def upload_ror_keringen(request):
    """Save zipfile."""
    #import pdb; pdb.set_trace()
    template = 'import/upload_message.html'
    upload_path = settings.ROR_KERINGEN_NOTAPPLIED_PATH
    c_date = datetime.datetime.today()
    f_prefix = "{0:04}{1:02}{2:02}_{3:02}{4:02}".format(
                c_date.year, c_date.month, c_date.day,
                c_date.hour, c_date.minute)
    if not os.path.isdir(upload_path):
        os.makedirs(upload_path)

    f_upload = request.FILES.get('zip', None)
    
    if f_upload is not None:
        try:
            unique_name = "{0}_{1}".format(f_prefix, f_upload.name)          
            with open(os.path.join(upload_path, unique_name), 'wb') as f_destination:
                for chunk in f_upload.chunks():
                    f_destination.write(chunk)
        except:
            return render_to_response(template, {'message': _('Error on upload.')}) 
    else:
       return render_to_response(template, {'message': _('Error on upload.')})
                
    try:
        
        RORKering(
            title=request.POST.get('title'),
            owner=User.objects.get(username=request.user),
            file_name="{0}_{1}".format(f_prefix, f_upload.name),
            type_kering=request.POST.get('code'),
            description=request.POST.get('opmerking')).save() 
    except:
        return render_to_response(template, {'message': _('Error on save.')})

    return render_to_response(template, {'message': _('Uploaded.')})


def service_load_strategies(current_strategy, strategies):
    selected_strategies_ids = strategies.split(';')
    new_measures = []
    for strategy_id in selected_strategies_ids:
        strat = Strategy.objects.get(pk=strategy_id)
        for measure in strat.measure_set.all():
            measure_new = Measure.objects.create(
                name=measure.name,
                reference_adjustment=measure.reference_adjustment,
                adjustment=measure.adjustment)
            for embankment in measure.embankmentunit_set.all():
                measure_new.embankmentunit_set.add(embankment)
            measure_new.strategy.add(current_strategy)
            measure_new.save()
            new_measures += [measure_new]

    answer = {'successful': True, 'measures': []}

    for measure in new_measures:
        answer['measures'].append(
            {'id': measure.id,
             'name': measure.name,
             'number_embankment_units':
             measure.embankmentunit_set.all().count(),
             'adjustment': measure.adjustment,
             'reference': measure.reference_adjustment})

    return HttpResponse(simplejson.dumps(answer), mimetype="application/json")


def service_get_strategy_id():

    strategy = Strategy.objects.create(name='-')
    answer = {'successful': True, 'strategyId': strategy.id}
    return HttpResponse(simplejson.dumps(answer), mimetype="application/json")


def service_import_embankment_shape():
    import osgeo.ogr

    datasource = osgeo.ogr.Open(
        'C:/repo/gisdata/Verhoogde_lijnelementen_c3_split200.shp')
    lyr = datasource.GetLayer()

    feature = lyr.next()
    ident_index = feature.GetFieldIndex('IDENT')
    height_index = feature.GetFieldIndex('HOOGTENIVE')
    lyr.ResetReading()

    for feature in lyr:
        geometry = GEOSGeometry(feature.geometry().ExportToWkt(), srid=28992)
        unit_id = (
            feature.GetField(ident_index)
            if feature.GetField(ident_index) is not None else 'no_id')
        original_height = (
            feature.GetField(height_index)
            if feature.GetField(height_index) is not None else -999)
        regions = Region.objects.filter(geom__intersects=geometry)

        for region in regions:
            embankment_unit = EmbankmentUnit(unit_id=unit_id,
                                     type=EmbankmentUnit.TYPE_EXISTING,
                                     original_height=original_height,
                                     region=region,
                                     geometry=geometry)
            embankment_unit.save()

    return HttpResponse("Gelukt")


def get_raw_result_scenario(request, scenarioid):
    scenario = get_object_or_404(Scenario, id=scenarioid)

    results = []
    for result in scenario.result_set.all():
        resultloc = result.resultloc.replace('\\', '/')
        file_path = os.path.join(
            settings.EXTERNAL_RESULT_MOUNTED_DIR, resultloc)
        if not os.path.exists(file_path):
            # Skip
            continue

        view_url = reverse('result_download', kwargs={
                'result_id': result.id,
                })

        # Add filename at the end of the URL so that the browser knows
        # what to call the file it is served. This part of the URL is
        # ignored by urls.py.
        url = view_url + os.path.basename(file_path)

        results.append({
                "url": url,
                "result": result,
                })

    return render_to_response("flooding/results_scenario.html", {
            "results": results
            })

def get_ror_keringen_types():
    types = [{'code': unicode(i[0]), 'type': unicode(i[1])} for i in RORKering.TYPE_KERING]
    return HttpResponse(simplejson.dumps(types),
                        mimetype='application/json')

def get_ror_keringen():
    keringen = [k.kering_as_dict for k in RORKering.objects.all()]
    return HttpResponse(simplejson.dumps(keringen),
                        mimetype='application/json')

def service(request):
    """Calls other service functions

    parameters depend on action.
    """
    if request.method == 'GET':
        query = request.GET

        if 'action' not in query and 'ACTION' not in query:
            raise Http404

        action_name = query.get('action', query.get('ACTION')).lower()

        # I have no idea why we let the user decide which permission level
        # to use, but OK...
        permission = int(
            query.get('permission',
                      UserPermission.PERMISSION_SCENARIO_VIEW))

        if action_name == 'get_projects':
            return service_get_projects(request, permission)

        elif action_name == 'get_scenarios_from_project':
            project_id = query.get('project_id')
            return service_get_scenarios_from_project(
                request, project_id, permission=permission)

        elif action_name == 'get_scenarios':
            return service_get_scenarios(request, permission=permission)

        elif action_name == 'get_scenarios_export_list':
            project_id = query.get('project_id')
            return service_get_scenarios_export_list(
                request, project_id, permission)

        elif action_name == 'get_scenario_tree':
            breach_id = query.get('breach_id', None)
            true_or_false = {'0': False, '1': True, 'None': None}
            filter_onlyprojectswithscenario = true_or_false[
                query.get('onlyprojectswithscenario', '0')]

            filter = query.get('filter', 'all')
            filter_dict = {
                'all': None,
                'all_with_results': [
                    Scenario.STATUS_DISAPPROVED,
                    Scenario.STATUS_APPROVED,
                    Scenario.STATUS_CALCULATED],
                'rejected': [Scenario.STATUS_DISAPPROVED],
                'accepted': [Scenario.STATUS_APPROVED],
                'verify': [Scenario.STATUS_CALCULATED],
                }
            filter_scenariostatus = filter_dict[filter.lower()]

            return service_get_scenario_tree(
               request, breach_id, permission=permission,
               filter_onlyprojectswithscenario=filter_onlyprojectswithscenario,
               filter_scenariostatus=filter_scenariostatus)

        elif action_name == 'get_results_from_scenario':
            scenario_id = query.get('scenario_id')
            return service_get_results_from_scenario(
                request, scenario_id, permission=permission)

        elif action_name == 'get_tasks_from_scenario':
            scenario_id = query.get('scenario_id')
            return service_get_tasks_from_scenario(
                request, scenario_id, permission=permission)

        elif action_name == 'get_cutofflocations_from_scenario':
            scenario_id = query.get('scenario_id')
            return service_get_cutofflocations_from_scenario(
                request, scenario_id, permission=permission)

        elif action_name == 'get_regionsets':
            return service_get_regionsets(request, permission=permission)

        elif action_name == 'get_all_regions':
            return service_get_all_regions(request, permission=permission)

        elif action_name == 'get_region_tree':
            filter_has_model = int(query.get('has_model', 0))

            return service_get_region_tree(
                request, permission=permission,
                filter_has_model=filter_has_model)

        elif action_name == 'get_breaches':
            region_id = query.get('region_id')
            scenariofilter = int(query.get('scenariofilter', -1))
            return service_get_breaches(
                request, region_id, scenariofilter=scenariofilter)

        elif action_name == 'get_breach_tree':

            region_id = query.get('region_id')
            filter_bool_dict = {'1': True, '0': False}

            active = query.get('active', '0')
            onlyscenariobreaches = query.get('onlyscenariobreaches', '0')
            filter_active = filter_bool_dict[active]
            filter_onlyscenariobreaches = filter_bool_dict[
                onlyscenariobreaches]

            filter = query.get('filter', 'all')
            filter_dict = {
                'all': None,
                'all_with_results': [
                    Scenario.STATUS_DISAPPROVED,
                    Scenario.STATUS_APPROVED,
                    Scenario.STATUS_CALCULATED],
                'rejected': [Scenario.STATUS_DISAPPROVED],
                'accepted': [Scenario.STATUS_APPROVED],
                'verify': [Scenario.STATUS_CALCULATED],
                }
            filter_scenario = filter_dict[filter.lower()]

            return service_get_breach_tree(
                request, permission=permission, region_id=region_id,
                filter_onlyscenariobreaches=filter_onlyscenariobreaches,
                filter_scenario=filter_scenario,
                filter_active=filter_active)

        elif action_name == 'get_regions':
            regionset_id = query.get('regionset_id')
            return service_get_regions(
                request, regionset_id, permission=permission)
        elif action_name == 'get_project_regions':
            project_id = query.get('project_id')
            return service_get_project_regions(
                request, project_id, permission=permission)
        elif action_name == 'get_region_maps':
            region_id = query.get('region_id', None)
            return service_get_region_maps(request, region_id)
        elif action_name == 'get_cutofflocations':
            inundationmodel_id = query.get('inundationmodel_id', None)
            extwatermodel_id = query.get('extwatermodel_id', None)
            return service_get_cutofflocations(
                request,
                inundationmodel_id=inundationmodel_id,
                extwatermodel_id=extwatermodel_id)
        elif action_name == 'get_cutofflocationsets':
            inundationmodel_id = query.get('inundationmodel_id', None)
            extwatermodel_id = query.get('extwatermodel_id', None)
            return service_get_cutofflocationsets(
                request,
                inundationmodel_id=inundationmodel_id,
                extwatermodel_id=extwatermodel_id)

        elif action_name == 'get_cutofflocations_from_cutofflocationset':
            cutofflocationset_id = query.get('cutofflocationset_id', None)
            return service_get_cutofflocations_from_cutofflocationset(
                request,
                cutofflocationset_id=cutofflocationset_id,
                permission=permission)
        elif action_name == 'get_result_settings':
            result_id = query.get('result_id', None)
            return service_get_result_settings(request,
                                               result_id=result_id)

        elif action_name == 'get_presentation_of_scenario':
            scenario_id = query.get('scenario_id', None)
            return service_get_presentations_of_scenario(request,
                                               scenario_id=scenario_id)

        elif action_name == 'get_inundationmodels':
            region_id = query.get('region_id', None)
            return service_get_inundationmodels(request,
                                               region_id=region_id)

        elif action_name == 'get_externalwatermodels':
            breach_id = query.get('breach_id', None)
            return service_get_externalwatermodels(request,
                                               breach_id=breach_id)
        elif action_name == 'compose_scenario':
            breach_id = query.get('breach_id', None)
            return service_compose_scenario(request,
                                            breach_id=breach_id)
        elif action_name == 'compose_3di_scenario':
            breach_id = query.get('breach_id', None)
            return service_compose_3di_scenario(request,
                                                breach_id=breach_id)
        elif action_name == 'select_strategy':
            region_id = query.get('region_id', None)
            return service_select_strategy(request,
                                           region_id=region_id)

        elif action_name == 'get_externalwater_graph':
            mid = 24 * 60 * 60 * 1000

            width = int(query.get('width', None))
            height = int(query.get('height', None))
            breach_id = int(query.get('breach_id', None))
            extwmaxlevel = float(query.get('extwmaxlevel', -999))
            tpeak = float(query.get('tpeak', 0)) / mid
            tstorm = float(query.get('tstorm', 0)) / mid
            tsim = float(query.get('tsim', 0)) / mid
            tstartbreach = float(query.get('tstartbreach', 0)) / mid
            tdeltaphase = float(query.get('tdeltaphase', 0)) / mid
            tide_id = int(query.get('tide_id', 0))
            extwbaselevel = float(query.get('extwbaselevel', -999))
            use_manual_input = bool(query.get('useManualInput', False))
            timeserie = str(query.get('timeserie', 0))

            return get_externalwater_graph(
                request,
                width,
                height,
                breach_id,
                extwmaxlevel,
                tpeak,
                tstorm,
                tsim,
                tstartbreach,
                tdeltaphase,
                tide_id,
                extwbaselevel,
                use_manual_input,
                timeserie,
                True)

        elif action_name == 'get_externalwater_csv':
            mid = 24 * 60 * 60 * 1000

            width = int(query.get('width', None))
            height = int(query.get('height', None))
            breach_id = int(query.get('breach_id', None))
            extwmaxlevel = float(query.get('extwmaxlevel', -999))
            tpeak = float(query.get('tpeak', 0)) / mid
            tstorm = float(query.get('tstorm', 0)) / mid
            tsim = float(query.get('tsim', 0)) / mid
            tstartbreach = float(query.get('tstartbreach', 0)) / mid
            tdeltaphase = float(query.get('tdeltaphase', 0)) / mid
            tide_id = int(query.get('tide_id', 0))
            extwbaselevel = float(query.get('extwbaselevel', -999))
            use_manual_input = bool(query.get('useManualInput', False))
            timeserie = str(query.get('timeserie', 0))

            return get_externalwater_csv(
                request,
                width,
                height,
                breach_id,
                extwmaxlevel,
                tpeak,
                tstorm,
                tsim,
                tstartbreach,
                tdeltaphase,
                tide_id,
                extwbaselevel,
                use_manual_input,
                timeserie)

        elif action_name == 'get_raw_result':
            presentationlayer = int(query.get('presentationlayer', None))
            return service_get_raw_result(request,
                                          presentationlayer)
        elif action_name == 'get_raw_result_scenario':
            scenarioid = int(query.get('scenarioid', None))
            return get_raw_result_scenario(request, scenarioid)

        elif action_name == 'get_import_scenario_uploaded_file':
            path = query.get('path', '')
            return service_get_import_scenario_uploaded_file(request, path)

        elif action_name == 'get_attachment':
            scenario_id = query.get('scenario_id', None)
            path = query.get('path', '')
            return service_get_attachment(request, scenario_id, path)
        elif action_name == 'get_existing_embankments_shape':
            bbox = query.get('BBOX', None)
            width = query.get('WIDTH', None)
            height = query.get('HEIGHT', None)
            strategy_id = query.get('STRATEGY_ID', -1)
            region_id = query.get('REGION_ID', -1)
            if query.get('ONLY_SELECTED', False) == 'TRUE':
                only_selected = True
            else:
                only_selected = False
            return service_get_existing_embankments_shape(
                request, int(width), int(height),
                tuple([float(value) for value in bbox.split(',')]),
                int(region_id), int(strategy_id), only_selected)
        elif action_name == 'import_embankment_shape':
            return service_import_embankment_shape()
        elif action_name == 'get_externalwater_graph_session':
            return get_externalwater_graph_session(request)
        elif action_name == 'get_strategy_id':
            return service_get_strategy_id()

        elif  action_name == 'get_extra_shapes':
            bbox = query.get('BBOX', None)
            width = query.get('WIDTH', None)
            height = query.get('HEIGHT', None)
            region_id = query.get('REGION_ID', -1)

            return service_get_extra_shapes(
                request, int(width), int(height),
                tuple([float(value) for value in bbox.split(',')]),
                int(region_id))
        elif action_name == 'get_extra_grid_shapes':
            bbox = query.get('BBOX', None)
            width = query.get('WIDTH', None)
            height = query.get('HEIGHT', None)
            region_id = query.get('REGION_ID', -1)

            return service_get_extra_grid_shapes(
                request, int(width), int(height),
                tuple([float(value) for value in bbox.split(',')]),
                int(region_id))

        elif action_name == 'get_externalwater_graph_infowindow':
            width = int(query.get('width', None))
            height = int(query.get('height', None))
            scenariobreach_id = int(query.get('scenariobreach_id', None))
            return get_externalwater_graph_infowindow(
                request, width, height, scenariobreach_id)
        elif action_name == 'get_ror_keringen':
            return get_ror_keringen()
        elif action_name == 'get_ror_keringen_types':
            return get_ror_keringen_types()
        else:
            #pass
            raise Http404

    elif request.method == 'POST':
        query = request.POST
        action_name = query.get('action', query.get('ACTION')).lower()
        
        if action_name == 'post_newscenario':
            return service_save_new_scenario(request)
        elif action_name == 'post_new3discenario':
            return service_save_new_3di_scenario(request)
        elif action_name == 'save_drawn_embankment':
            geometry = query.get('geometry')
            strategy_id = query.get('strategy_id', -1)
            region_id = query.get('region_id', -1)
            return service_save_drawn_embankment(
                geometry, strategy_id, region_id)
        elif action_name == 'select_existing_embankments_by_polygon':
            geometry = query.get('geometry')
            strategy_id = query.get('strategy_id', -1)
            region_id = query.get('region_id', -1)
            return select_existing_embankments_by_polygon(
                geometry, strategy_id, region_id)
        elif action_name == 'delete_measure':
            measure_ids = query.get('measure_ids', -1)
            return service_delete_measure(measure_ids)
        elif action_name == 'post_load_strategies':
            current_strategy = query.get('current_strategy')
            strategies = query.get('strategies')
            return service_load_strategies(current_strategy, strategies)
        elif action_name == 'get_externalwater_graph':
            mid = 24 * 60 * 60 * 1000

            width = int(query.get('width', None))
            height = int(query.get('height', None))
            breach_id = int(query.get('breach_id', None))
            extwmaxlevel = float(query.get('extwmaxlevel', -999))
            tpeak = float(query.get('tpeak', 0)) / mid
            tstorm = float(query.get('tstorm', 0)) / mid
            tsim = float(query.get('tsim', 0)) / mid
            tstartbreach = float(query.get('tstartbreach', 0)) / mid
            tdeltaphase = float(query.get('tdeltaphase', 0)) / mid
            try:
                tide_id = int(query.get('tide_id', 0))
            except:
                tide_id = None
            try:
                extwbaselevel = float(query.get('extwbaselevel', -999))
            except:
                extwbaselevel = None

            if query.get('use_manual_input', False) == 'true':
                use_manual_input = True
            else:
                use_manual_input = False

            timeserie = str(query.get('timeserie', 0))

            return get_externalwater_graph(request,
                                        width,
                                        height,
                                        breach_id,
                                        extwmaxlevel,
                                        tpeak,
                                        tstorm,
                                        tsim,
                                        tstartbreach,
                                        tdeltaphase,
                                        tide_id,
                                        extwbaselevel,
                                        use_manual_input,
                                        timeserie,
                                        True)
        elif action_name == 'upload_ror_keringen':
            return upload_ror_keringen(request)
        else:
            raise Http404


@receives_permission_manager
def service_get_scenarios_from_breach(
    request, permission_manager, breach_id, scenariofilter=-1):
    """Get scenario's.

    Conditions:
    - given BREACH

    - given scenariofilter SCENARIOSTATUS (all, approved, disapproved,
      to be approved)

    - permission level scenario_view

    """
    scenario_dict = {}
    breach = get_object_or_404(Breach, pk=breach_id)

    for s in breach.scenario_set.all():
        if permission_manager.check_project_permission(
            s.project,
            UserPermission.PERMISSION_SCENARIO_VIEW):
            if scenariofilter == -1 or s.status == scenariofilter:
                scenario_dict[s.id] = s
    return render_to_response('flooding/scenario.json',
                              {'scenario_list': scenario_dict.values()})


@receives_permission_manager
def service_get_tasks_from_scenario(
    request, permission_manager, scenario_id,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get tasks from a given scenario.

    Conditions:
    - from given scenario (check permission for given scenario)
    - given permission level
    - todo: filter tasks(?)
    """
    scenario = get_object_or_404(Scenario, pk=scenario_id)

    if not(permission_manager.check_project_permission(
            scenario.main_project, permission)):
        raise Http404
    #todo: filter
    object_list = scenario.task_set.all()
    return render_to_response('flooding/task.json',
                              {'object_list': object_list})


@receives_permission_manager
def service_get_scenarios_from_project(
    request, permission_manager, project_id,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get the list of scenarios from a project with given permission.

    return in JSON format

    """
    project = get_object_or_404(Project, pk=project_id)

    if not(permission_manager.check_project_permission(project, permission)):
        raise Http404

    return render_to_response(
        'flooding/scenario.json',
        {'scenario_list': project.all_scenarios()})


@receives_permission_manager
def service_get_scenarios(
    request, permission_manager,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get the list of scenarios with given permission and return in
    JSON format."""
    scenario_list = []

    project_list = permission_manager.get_projects(permission)
    for p in project_list:
        scenario_list += p.scenario_set.all()
    return render_to_response('flooding/scenario.json',
                              {'scenario_list': scenario_list})


@receives_permission_manager
def service_get_results_from_scenario(
    request, permission_manager, scenario_id,
    permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get results from a given scenario.

    Conditions:
    - from given scenario (check permission for given scenario)
    - given permission level
    - todo: predefined types only
    """
    scenario = get_object_or_404(Scenario, pk=scenario_id)

    if not permission_manager.check_project_permission(
        scenario.main_project, permission):
        raise Http404

    result = scenario.result_set.all().select_related(
        'resulttype').order_by('resulttype__id')  # shortname_dutch

    return render_to_response('flooding/result.json',
                              {'result_list': result})
