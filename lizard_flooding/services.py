# -*- coding: utf-8 -*-


from django.http import HttpResponse, Http404
from django.utils import simplejson
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

from lizard_flooding.views_dev import service_compose_scenario, get_externalwater_graph, get_externalwater_graph_session, service_save_new_scenario, get_externalwater_csv
from lizard_base.models import Setting
from lizard_flooding.models import Breach, CutoffLocationSet, \
    ExternalWater, EmbankmentUnit, Measure, RegionSet,  \
    Project, Result, Region, Scenario, UserPermission, Strategy, SobekModel
from lizard_flooding.permission_manager import PermissionManager

import Image
import mapnik
import os
import PIL
import StringIO
#-------------------- Services ----------------


@never_cache
def service_get_region_tree(request, permission=UserPermission.PERMISSION_SCENARIO_VIEW, filter_through_scenario=False, filter_has_model=False ):
    """Get a tree of regionsets and regions

    optional: Filter on permissions
    optional: Filter which selects regions through through project - scenario - breaches - regions,
                    otherwise project-regionsets-regions
    optio
    optional: filter_onlyscenariobreaches=filter only the breaches in scenario's
    optional: filter_scenario: filter on scenario status. choices are None or Scenario.STATUS_*
    """
    if request.method == "GET":
        #see if there's a parameter called "permission"
        permission_from_get = request.GET.get('permission')
        if permission_from_get is not None:
            permission = int(permission_from_get)
    pm = PermissionManager(request.user)
    if filter_through_scenario:
        regionset_list = pm.get_regionsets(permission, True)
    else:
        regionset_list = pm.get_regionsets(permission)

    region_list_total = pm.get_regions(permission)


    object_list = []
    for regionset in regionset_list:

        if filter_has_model:
            region_list = region_list_total.filter(regionset=regionset, sobekmodels__active = True).order_by('name').distinct()
        else:
            region_list = region_list_total.filter(regionset=regionset).order_by('name')

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
                #used function below because of performance. Instead of #west, south, east, north = regionset.regions.unionagg().extent
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

    return HttpResponse(simplejson.dumps(object_list), mimetype="application/json")
#render_to_response('flooding/regiontree.json', {'object_list': object_list})

@never_cache
def service_get_breach_tree(request, permission=UserPermission.PERMISSION_SCENARIO_VIEW,
                            region_id=None, filter_onlyscenariobreaches=False, filter_scenario=None, filter_active=None):
    """Get breaches and external waters in a tree.

    optional: filter on region. find out all breaches of a region,
    build tree with external waters and breaches
    optional: Filter on permissions
    optional: filter_onlyscenariobreaches=filter only the breaches in scenario's
    optional: filter_scenario: filter on scenario status. choices are None or Scenario.STATUS_*

    """
  
    pm = PermissionManager(request.user)

    scenarios = pm.get_scenarios(None, permission, filter_scenario)


    if region_id:
        region = get_object_or_404(Region, pk=region_id)
        if not(pm.check_region_permission(region, permission)):
            raise Http404
        if filter_onlyscenariobreaches:
            breach_list = region.breach_set.filter(scenario__in=scenarios).distinct()
        else:
            breach_list = region.breach_set.filter(active=True)
    else:
        if not(pm.check_permission(permission)):
            raise Http404
        if filter_onlyscenariobreaches:
            breach_list = Breach.objects.filter(scenario__in=scenarios).distinct()
        else:
            breach_list = Breach.objects.filter(active=True)

    #if filter_active == 1:
    #     breach_list = breach_list.filter(active=True)

    externalwater_list = ExternalWater.objects.filter(breach__in=breach_list).distinct()

    object_list = []
    #add externalwaters
    for ew in externalwater_list:
        object_list.append({'id': -1*ew.id,
                            'name': ew.__unicode__(),
                            'type': ew.type,
                            'parentid': None,
                            'isbreach': False,
                            })
    #add breaches
    for breach in breach_list:
        loc = breach.geom #.transform(900913,True)
        object_list.append({'id': breach.id,
                            'name': breach.__unicode__(),
                            'parentid': -1*breach.externalwater.id,
                            'isbreach': True,
                            'x': loc.x,
                            'y': loc.y,
                            }
                           )

    return HttpResponse(simplejson.dumps(object_list), mimetype="application/json")


@never_cache
def service_get_scenario_tree(request, breach_id,
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
    pm = PermissionManager(request.user)

    scenario_list = pm.get_scenarios(breach_id, permission, filter_scenariostatus)

    #only projects with scenario
    if filter_onlyprojectswithscenario:
        project_list = Project.objects.filter(scenario__in=scenario_list).distinct()
    else:
        project_list = pm.get_projects(permission)


    object_list = []
    for project in project_list:
        object_list.append({'pid': project.id,
                            'name': project.__unicode__(),
                            'parentid': None,
                            'isscenario': False,
                            'status': 0,
                            })
    for scenario in scenario_list:
            object_list.append({'sid': scenario.id,
                                'name': scenario.__unicode__(),
                                'parentid': scenario.project.id,
                                'isscenario': True,
                                'status': scenario.get_status(),
                                'strategy_id': scenario.strategy_id,
                                })

    return HttpResponse(simplejson.dumps(object_list), mimetype="application/json")


@never_cache
def service_get_cutofflocations_from_scenario(
    request, scenario_id, permission = UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get cutofflocations of given scenario.

    Conditions:
    - from given scenario (check permission for given scenario)
    - given permission level
    """
    scenario = get_object_or_404(Scenario, pk=scenario_id)
    pm = PermissionManager(request.user)
    if not(pm.check_project_permission(scenario.project, permission)):
        raise Http404
    scenariocutofflocation_list = scenario.scenariocutofflocation_set.all()

    return render_to_response('flooding/scenariocutofflocation.json',
                              {'object_list': scenariocutofflocation_list})

# Request used by 'new scenarios', 'table', 'import', 'export'
#
#
@never_cache
def service_get_regions(request, regionset_id, permission = UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get all regions for a given regionset_id and given permission."""
    regionset = get_object_or_404(RegionSet, pk=regionset_id)
    pm = PermissionManager(request.user)
    if not(pm.check_regionset_permission(regionset, permission)):
        raise Http404
    if request.user.is_staff:
        filter_active = None
    else:
        filter_active = True
    regions = regionset.get_all_regions(filter_active).order_by('name')
    result_list = [{'id': r.id, 'name': str(r.name)} for r in regions]
    return HttpResponse(simplejson.dumps(result_list), mimetype="application/json")

@never_cache
def service_get_regionsets(request, permission = UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get all regionsets where you have the given permission."""
    if request.method == "GET":
        #see if there's a parameter called "permission"
        permission_from_get = request.GET.get('permission')
        if permission_from_get is not None:
            permission = int(permission_from_get)
    pm = PermissionManager(request.user)
    regionsets = pm.get_regionsets(permission).order_by('name')
    result_list = [{'id': r.id, 'name': str(r.name)} for r in regionsets]
    return HttpResponse(simplejson.dumps(result_list), mimetype="application/json")

@never_cache
def service_get_breaches(request, region_id, scenariofilter=-1):
    """Get breaches from a given region_id.

    * breaches from given region_id (permissions: scenario_view), if not existent, return []
    * optional scenariofilter (all,approved,disapproved, to be approved).

    """
    try:
        region = Region.objects.get(pk=region_id)
    except Region.DoesNotExist:
        return HttpResponse(simplejson.dumps([]), mimetype="application/json")

    pm = PermissionManager(request.user)
    if not(pm.check_region_permission(
            region,
            UserPermission.PERMISSION_SCENARIO_VIEW)):
        raise Http404


    if scenariofilter == -1:
        breaches = region.breach_set.all().order_by('name')
    else:
        breaches = region.breach_set.filter(scenario__status_cache=scenariofilter).order_by('name').distinct()

    result_list = [{'id': b.id, 'name': str(b)} for b in breaches]

    return HttpResponse(simplejson.dumps(result_list), mimetype="application/json")

@never_cache
def service_get_projects(request, permission = UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get the list of projects with given permission and return in JSON format."""
    pm = PermissionManager(request.user)
    project_list = pm.get_projects(permission)
    return render_to_response('flooding/project.json',
                              {'project_list': project_list})

@never_cache
def service_get_scenarios_export_list(request, project_id, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """
    Gets the scenario list with all scenarios, with all the info neede for displaying
    in the drag and drop window for the export tool.
    """
    project = get_object_or_404(Project, pk = project_id)
    pm = PermissionManager(request.user)
    if not(pm.check_project_permission(project, permission)):
        raise Http404
    scenarios_export_list = [{'scenario_id': s.id, 'scenario_name': s.name,
                              'breach_ids': [br.id for br in s.breaches.all()], 'breach_names': [br.name for br in s.breaches.all()],
                              'region_ids': [br.region.id for br in s.breaches.all()], 'region_names': [br.region.name for br in s.breaches.all()],
                              'project_id': project.id, 'project_name': project.name,
                              'owner_id': s.owner.id, 'owner_name': s.owner.username}
                            for s in project.scenario_set.all()]
    return HttpResponse(simplejson.dumps(scenarios_export_list), mimetype="application/json")

@never_cache
def service_get_all_regions(request, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get the list of regions with given permission and return in JSON format."""
    pm = PermissionManager(request.user)
    regions = pm.get_regions(permission).order_by('name')
    result_list = [{'id': r.id, 'name': str(r.name)} for r in regions]
    return HttpResponse(simplejson.dumps(result_list), mimetype="application/json")


@never_cache
def service_get_inundationmodels(
    request, region_id=None, only_active = True):
    """Get inundationmodels, with filter region_id and SobekModel.active
    * in gebruik bij flooding new, stap 2
    """
    region = get_object_or_404(Region, pk=region_id)

    if only_active:
        models = region.sobekmodels.filter(active = True)
    else:
        models = region.externalwater.sobekmodels.all()

    resp = [{'id':obj.id, 'name': str(obj.model_version) + ', ' + str(obj.model_varname)} for obj in models]

    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')

@never_cache
def service_get_externalwatermodels(
    request, breach_id, only_active = True):
    """Get externalwater models , with filter breach_id and SobekModel.active
    * in gebruik bij flooding new, stap 2
    """
    breach = get_object_or_404(Breach, pk=breach_id)

    if only_active:
        models = breach.externalwater.sobekmodels.filter(active = True)
    else:
        models = breach.externalwater.sobekmodels.all()

    resp = [{'id':obj.id, 'name':str(obj.model_version) + ', ' + str(obj.model_varname)} for obj in models]

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
        loc = obj.geom #.transform(900913,True)
        resp.append({'id':obj.id, 'name': obj.name,'type':obj.type, 'tdef': obj.deftclose, 'x': loc.x, 'y': loc.y })
    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')

@never_cache
def service_get_cutofflocationsets(
    request, inundationmodel_id=None, extwatermodel_id=None):
    """Get cutofflocations, with filter region_id and/or externalwater_id
    """
    cutofflocationset = []
    if inundationmodel_id:
        inundationmodel = get_object_or_404(SobekModel, pk=inundationmodel_id)
        cutofflocationset.extend(CutoffLocationSet.objects.filter(cutofflocations__sobekmodels = inundationmodel).distinct())
    if extwatermodel_id:
        extwatermodel = get_object_or_404(SobekModel, pk=extwatermodel_id)
        cutofflocationset.extend(CutoffLocationSet.objects.filter(cutofflocations__sobekmodels = extwatermodel).distinct())
    resp = []
    for set in cutofflocationset:
        cutofflocation_ids = [obj.id for obj in set.cutofflocations.all()]
        resp.append({'id':set.id, 'name': set.name, 'number': len(cutofflocation_ids) ,'cuttofflocation':  cutofflocation_ids} )
    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')

@never_cache
def service_get_cutofflocations_from_cutofflocationset(
    request, cutofflocationset_id, permission):
    """Get cutofflocations, given cutofflocationset_id
    """
    cls = get_object_or_404(CutoffLocationSet, pk=cutofflocationset_id)
    if request.user.is_staff:
        object_list = cls.cutofflocations.all()
    else:
        pm = PermissionManager(request.user)
        projects = pm.get_projects(permission)
        object_list = cls.cutofflocations.filter(region__regionset__project__in=projects).distinct()
    return render_to_response('flooding/cutofflocation.json',
                              {'object_list': object_list})
@never_cache
def service_get_result_settings(
    request, result_id):
    """get_result_settings, with filter result_id
        voor resultaten met figuren, haalt afmetingen en extents op
    """
    result = get_object_or_404(Result, pk=result_id)

    settings_in_db = Setting.objects.get(  key = 'destination_dir'  )
    png_name = settings_in_db.value + "\\" + result.resultpngloc
    if result.resulttype.overlaytype == 'ANIMATEDMAPOVERLAY':
        numberstring = '%4i' % result.firstnr
        numberstring = numberstring.replace(" ","0")
        png_name = png_name.replace('####',numberstring)
    pgw_name = png_name.replace(".png", ".pgw")
    pgwfile = open(pgw_name, 'r')
    pgwfields = pgwfile.readlines()
    pgwfile.close()

    gridsize, a, b, c, west, north = [float(s) for s in pgwfields]


    picture = Image.open( png_name )
    width, height = picture.size

    east = west +  width * gridsize
    south = north - height * gridsize

    pictureinfo = {
        'gridsize': gridsize,
        'width':width,
        'height':height,
        'north':north,
        'west':west,
        'east':east,
        'south':south,
        'projection':'rds',
    }

    return render_to_response('flooding/result_settings.json',
                              {'result': result, 'pictureinfo':pictureinfo})

@never_cache
def service_get_presentations_of_scenario(
    request, scenario_id, type_filter = None,  permission = UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get presentationlayers of given scenario with a filter on custom type
    input:
        scenario_id:
        type_filter: name of 'custom' presentationtype filter (is in te stellen door gebruiker)

    Conditions:
    - from given scenario (check permission for given scenario)
    - return only presentationtypes allowed by userpermission

    return:
        id: presentationlayer_id
        name: presentationtype_name (short name)
        overlaytype: presentationtype_overlaytype - integer - (wms, map, general, (point, line))
        type: presentationtype_valuetype - integer - (timeserie, classification, singlevalue, static)
    """
    scenario = get_object_or_404(Scenario, pk=scenario_id)

    players = scenario.presentationlayer.filter(presentationtype__custom_indicator__name = 'flooding_result').select_related('presentationtype').order_by('presentationtype__order_index')
    resp = []
    for pl in players:
        name = pl.presentationtype.name
        if pl.value:
            if pl.value > 1000000:
                name = "%s (%.1f miljoen %s)"%(name, pl.value/1000000, pl.presentationtype.unit)
            elif pl.value < 10:
                name = "%s (%.1f %s)"%(name, pl.value, pl.presentationtype.unit)
            else:
                name = "%s (%.0f %s)"%(name, pl.value, pl.presentationtype.unit)

        resp.append({'id':pl.id, 'name': name, 'prestypeid': pl.presentationtype.id ,'geoType': pl.presentationtype.geo_type, 'valueType': pl.presentationtype.value_type})

    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')

@never_cache
def service_get_raw_result(
    request, presentationlayer):
    '''

    '''

    result = Result.objects.filter(resulttype__presentationtype__presentationlayer = presentationlayer, scenario__presentationlayer = presentationlayer)
    if (result.count() == 1):
        file_name = os.path.join(Setting.objects.get( key = 'destination_dir' ).value,  result[0].resultloc.lstrip('\\').lstrip('/'))

        response = HttpResponse(open(file_name,'rb').read())
        response['Content-type'] = 'application/zip'
        response['Content-Disposition'] = 'attachment; filename='+os.path.split(file_name)[1]

        return response

    resp = {'opmerking': 'Ruwe resultaten niet beschikbaar'}
    return HttpResponse(simplejson.dumps(resp), mimetype='application/json')

@never_cache
def service_get_attachment(request, scenario_id, path):
    """ Returns a non-public attachment if one has the permission

    """

    scenario = get_object_or_404(Scenario, pk=scenario_id)
    user = request.user
    pm = PermissionManager(user)
    if not pm.check_project_permission(scenario.project, UserPermission.PERMISSION_SCENARIO_VIEW):
        raise Http404

    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.isfile(file_path):
        return HttpResponse('Het opgevraagde bestand bestaat niet.')

    file_name = os.path.split(path)[1]
    file_object = open(file_path, 'rb')
    response = HttpResponse(file_object.read())
    response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
    file_object.close()
    return  response

@never_cache
def service_get_import_scenario_uploaded_file(request, path):
    """ Returns a non-public uploaded file if one has the permission

    """

    user = request.user
    pm = PermissionManager(user)
    if not(pm.check_permission(UserPermission.PERMISSION_SCENARIO_ADD)):
        raise Http404

    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.isfile(file_path):
        return HttpResponse('Het opgevraagde bestand bestaat niet.')

    file_name = os.path.split(path)[1]
    file_object = open(file_path, 'rb')
    response = HttpResponse(file_object.read())
    response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
    file_object.close()
    return  response

@never_cache
def service_get_existing_embankments_shape(request, width, height, bbox, region_id, strategy_id, only_selected = False):
    """
    width = int
    height = int
    bbox = tuple
    """
    
    #################### set up map ###################################
    m = mapnik.Map(width, height)
    spherical_mercator = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over'
    rds = "+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs"
    m.srs = spherical_mercator
    m.background = mapnik.Color('transparent')
    #p = mapnik.Projection(spherical_mercator)

    #### Line style for existing embankments
    sl = mapnik.Style()
    rule_l = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(0,0,200)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 2.0
    rule_l.symbols.append(mapnik.LineSymbolizer(rule_stk))
    sl.rules.append(rule_l)
    m.append_style('Line Style', sl)
    
    #### Line style for new embankments
    s2 = mapnik.Style()
    rule_2 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.add_dash(10.0, 10.0)
    rule_stk.color = mapnik.Color(200,0,0)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_2.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s2.rules.append(rule_2)
    m.append_style('Line Style New Embankment', s2)
    
    #### Line style for polygon selections
    s3 = mapnik.Style()
    rule_3 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.add_dash(5.0, 5.0)
    rule_stk.color = mapnik.Color(255,128,0)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_3.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s3.rules.append(rule_3)
    m.append_style('Line Style Polygon Selection', s3)
        
    #### Line style for polygon selections
    s4 = mapnik.Style()
    rule_4 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(200,200,200)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 6.0
    rule_4.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s4.rules.append(rule_4)
    m.append_style('Line Style Specific Region', s4)
        
    #### Line style for region boundary
    s5 = mapnik.Style()
    rule_5 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(0,0,0)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 2.0
    rule_5.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s5.rules.append(rule_5)
    m.append_style('Line Style Region Boundary', s5)


    #### Get layer for a  region (boundary)    
    lyr_region = mapnik.Layer('Geometry from PostGIS')
    lyr_region.srs = '+proj=latlong +datum=WGS84'
    BUFFERED_TABLE = '(SELECT geom FROM flooding_region WHERE id = %i) region'%region_id
    lyr_region.datasource = mapnik.PostGIS(host=settings.DATABASE_HOST, user=settings.DATABASE_USER, password=settings.DATABASE_PASSWORD, dbname=settings.DATABASE_NAME, table=str(BUFFERED_TABLE))
    lyr_region.styles.append('Line Style Region Boundary')
    m.layers.append(lyr_region)
    
    #### Get layer for new embankments
    lyr_new_embankments = mapnik.Layer('Geometry from PostGIS')
    lyr_new_embankments.srs = '+proj=latlong +datum=WGS84'
    BUFFERED_TABLE = '(SELECT fe.geometry AS geometry FROM flooding_embankment_unit fe, \
                       flooding_strategy fs, flooding_embankment_unit_measure fem, \
                       flooding_measure_strategy fms, flooding_measure fm \
                       WHERE fs.id = fms.strategy_id AND fms.measure_id = fm.id AND \
                       fm.id = fem.measure_id AND fem.embankmentunit_id = fe.id AND \
                       fe.type=1 AND fs.id=%i) polygon_new_embankements' % strategy_id
    lyr_new_embankments.datasource = mapnik.PostGIS(host=settings.DATABASE_HOST, user=settings.DATABASE_USER, password=settings.DATABASE_PASSWORD, dbname=settings.DATABASE_NAME, table=str(BUFFERED_TABLE))
    lyr_new_embankments.styles.append('Line Style New Embankment')
    m.layers.append(lyr_new_embankments)
        
    #### Get layer for polygon selected embankments
    lyr_polygon_selected_embankments = mapnik.Layer('Geometry from PostGIS')
    lyr_polygon_selected_embankments.srs = '+proj=latlong +datum=WGS84'
    BUFFERED_TABLE = '(SELECT fe.geometry AS geometry FROM flooding_embankment_unit fe, \
                       flooding_strategy fs, flooding_embankment_unit_measure fem, \
                       flooding_measure_strategy fms, flooding_measure fm \
                       WHERE fs.id = fms.strategy_id AND fms.measure_id = fm.id AND \
                       fm.id = fem.measure_id AND fem.embankmentunit_id = fe.id AND \
                       fe.type=0 AND fs.id=%i) polygon_selected_embankements' % strategy_id

    
    lyr_polygon_selected_embankments.datasource = mapnik.PostGIS(host=settings.DATABASE_HOST, user=settings.DATABASE_USER, password=settings.DATABASE_PASSWORD, \
                                                                 dbname=settings.DATABASE_NAME, table=str(BUFFERED_TABLE), geometry_field='geometry', srid=4326)
    lyr_polygon_selected_embankments.styles.append('Line Style Polygon Selection')
    m.layers.append(lyr_polygon_selected_embankments)
      
    ##################### render map #############################
    m.zoom_to_box(mapnik.Envelope(*bbox))
    #m.zoom_to_box(lyrl.envelope())
    
    img = mapnik.Image(width,height)
    mapnik.render(m,img)

    # you can use this if you want te modify image with PIL
    imgPIL = PIL.Image.fromstring('RGBA', (width,height), img.tostring())
    #imgPIL = imgPIL.convert('RGB')
    buffer = StringIO.StringIO()
    imgPIL.save(buffer, 'png')#,transparency = 10
    buffer.seek(0)

    response = HttpResponse(buffer.read())
    response['Content-type'] = 'image/png'
    return response


def service_get_extra_shapes(request, width, height, bbox, region_id):
    """
    width = int
    height = int
    bbox = tuple
    """
    
    #################### set up map ###################################
    m = mapnik.Map(width, height)
    spherical_mercator = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over'
    rds = "+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs"
    m.srs = spherical_mercator
    m.background = mapnik.Color('transparent')
    #p = mapnik.Projection(spherical_mercator)

    #### Line style for existing embankments
    sl = mapnik.Style()
    rule_l = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(0,0,200)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_l.symbols.append(mapnik.LineSymbolizer(rule_stk))
    sl.rules.append(rule_l)
    m.append_style('Line Style Primaire Keringen', sl)
    
    #### Line style for new embankments
    s2 = mapnik.Style()
    rule_2 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(200,0,0)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_2.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s2.rules.append(rule_2)
    m.append_style('Line Style Regionale Keringen Met Functie', s2)
    
    #### Line style for polygon selections
    s3 = mapnik.Style()
    rule_3 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(0,200,0)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_3.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s3.rules.append(rule_3)
    m.append_style('Line Style Regionale Keringen Zonder Functie', s3)
        
    #### Line style for polygon selections
    s4 = mapnik.Style()
    rule_4 = mapnik.Rule()

    rule_stk = mapnik.Stroke()
    rule_stk.color = mapnik.Color(235,235,50)
    rule_stk.line_cap = mapnik.line_cap.ROUND_CAP
    rule_stk.width = 3.0
    rule_4.symbols.append(mapnik.LineSymbolizer(rule_stk))
    s4.rules.append(rule_4)
    m.append_style('Line Style Keringen Buiten De Provincie', s4)
        
    #### Get layer for shape file    
    lyrl = mapnik.Layer('lines', rds)
    lyrl.datasource = mapnik.Shapefile(file = os.path.join(settings.GIS_DIR,'primairekering.shp'))
    lyrl.styles.append('Line Style Primaire Keringen')
    m.layers.append(lyrl)
    
    lyr2 = mapnik.Layer('lines', rds)
    lyr2.datasource = mapnik.Shapefile(file= os.path.join(settings.GIS_DIR,'kering_buitenprov.shp'))
    lyr2.styles.append('Line Style Keringen Buiten De Provincie')
    m.layers.append(lyr2)
            
    lyr4 = mapnik.Layer('lines', rds)
    lyr4.datasource = mapnik.Shapefile(file= os.path.join(settings.GIS_DIR,'regio_zonder_functie.shp'))
    lyr4.styles.append('Line Style Regionale Keringen Zonder Functie')
    m.layers.append(lyr4)
    
    lyr3 = mapnik.Layer('lines', rds)
    lyr3.datasource = mapnik.Shapefile(file= os.path.join(settings.GIS_DIR,'ontwerp_Regionale_keringen.shp'))
    lyr3.styles.append('Line Style Regionale Keringen Met Functie')
    m.layers.append(lyr3)    
      
    ##################### render map #############################
    m.zoom_to_box(mapnik.Envelope(*bbox))
    #m.zoom_to_box(lyrl.envelope())
    
    img = mapnik.Image(width,height)
    mapnik.render(m,img)

    # you can use this if you want te modify image with PIL
    imgPIL = PIL.Image.fromstring('RGBA', (width,height), img.tostring())
    #imgPIL = imgPIL.convert('RGB')
    buffer = StringIO.StringIO()
    imgPIL.save(buffer, 'png')#,transparency = 10
    buffer.seek(0)

    response = HttpResponse(buffer.read())
    response['Content-type'] = 'image/png'
    return response

def service_get_extra_grid_shapes(request, width, height, bbox, region_id):
    """
    width = int
    height = int
    bbox = tuple
    """
    
    #################### set up map ###################################
    m = mapnik.Map(width, height)
    spherical_mercator = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over'
    rds = "+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs"
    m.srs = spherical_mercator
    m.background = mapnik.Color('transparent')
    #p = mapnik.Projection(spherical_mercator)
    
    s = mapnik.Style()
    r = mapnik.Rule()
    rs = mapnik.RasterSymbolizer()
    r.symbols.append(rs)
    s.rules.append(r)
    #styles['geotiff'] = s
    m.append_style('geotiff', s)
 
    #### Get layer for shape file    
    raster = mapnik.Gdal(file= os.path.join(settings.GIS_DIR, 'ahn5_medtot_gm_trans.tif'))
    lyrl = mapnik.Layer('Tiff Layer', spherical_mercator)
    lyrl.datasource = raster
    #lyrl.styles.append('Geotiff Style')
    lyrl.styles.append('geotiff')
    m.layers.append(lyrl)
          
    ##################### render map #############################
    m.zoom_to_box(mapnik.Envelope(*bbox))
    #m.zoom_to_box(lyrl.envelope())
    
    img = mapnik.Image(width,height)
    mapnik.render(m,img)

    # you can use this if you want te modify image with PIL
    imgPIL = PIL.Image.fromstring('RGBA', (width,height), img.tostring())
    #imgPIL = imgPIL.convert('RGB')
    buffer = StringIO.StringIO()
    imgPIL.save(buffer, 'png')#,transparency = 10
    buffer.seek(0)

    response = HttpResponse(buffer.read())
    response['Content-type'] = 'image/png'
    return response

def service_save_drawn_embankment(geometries, strategy_id, region_id):
    
    selected_strategy = Strategy.objects.get(pk=strategy_id)
    selected_measure = selected_strategy.measure_set.create(name='Ingetekend')
    
    region=Region.objects.get(pk=region_id)
    
    if len(geometries) > 0:
        for geometry in geometries.split(';'):
            line = GEOSGeometry(geometry, srid=900913)     
            embankment_unit = EmbankmentUnit(unit_id=-999,
                                             type = EmbankmentUnit.TYPE_NEW,
                                             original_height=-999,
                                             region=region,
                                             geometry=line)
            embankment_unit.save()
            selected_measure.embankmentunit_set.add(embankment_unit)
        
        answer = {'successful':True, 'id':selected_measure.id, 'name': selected_measure.name, 'number_embankment_units': selected_measure.embankmentunit_set.all().count()  }
        return HttpResponse(simplejson.dumps(answer), mimetype="application/json")
    else:
        answer = {'successful':False }
        return HttpResponse(simplejson.dumps(answer), mimetype="application/json") 

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
        selected_measure.name = "Bestaand (%i)" %  selected_measure.id
        selected_measure.save()   
           
        selected_embankment_units = EmbankmentUnit.objects.filter(region=region_id, type=EmbankmentUnit.TYPE_EXISTING)\
                                    .exclude(measure=selected_measure).filter(geometry__intersects=multi_polygon)
        selected_measure.embankmentunit_set.add(*selected_embankment_units)
        
        answer = {'successful':True, 'id':selected_measure.id, 'name': selected_measure.name, 'number_embankment_units': selected_measure.embankmentunit_set.all().count()  }
        return HttpResponse(simplejson.dumps(answer), mimetype="application/json")
    else:
        answer = {'successful':False}
        return HttpResponse(simplejson.dumps(answer), mimetype="application/json")

def service_delete_measure(measure_ids):
        
    measure_ids = [int(id) for id in measure_ids.split(';')]
    Measure.objects.filter(id__in = measure_ids).delete()
    answer = {'successful':True }
    return HttpResponse(simplejson.dumps(answer), mimetype="application/json")        

def service_get_strategy_id():
    
    strategy = Strategy.objects.create(name='-')
    answer = {'successful':True, 'strategyId':strategy.id }
    return HttpResponse(simplejson.dumps(answer), mimetype="application/json")    


def service_import_embankment_shape():
    import osgeo.ogr
    
    datasource = osgeo.ogr.Open('C:/repo/gisdata/Verhoogde_lijnelementen_c3_split200.shp')
    lyr = datasource.GetLayer()
        
    feature = lyr.next()
    ident_index = feature.GetFieldIndex('IDENT')
    height_index = feature.GetFieldIndex('HOOGTENIVE')    
    lyr.ResetReading()
    
    for feature in lyr:
        geometry = GEOSGeometry(feature.geometry().ExportToWkt(), srid=28992)
        unit_id = feature.GetField(ident_index) if feature.GetField(ident_index) is not None else 'no_id'         
        original_height = feature.GetField(height_index) if feature.GetField(height_index) is not None else -999
        regions = Region.objects.filter(geom__intersects=geometry)
                        
        for region in regions:        
            embankment_unit = EmbankmentUnit(unit_id=unit_id,
                                     type=EmbankmentUnit.TYPE_EXISTING,
                                     original_height=original_height,
                                     region=region,                   
                                     geometry=geometry)
            embankment_unit.save()
        
    
    return HttpResponse("Gelukt")

def service(request):
    """Calls other service functions

    parameters depend on action.

    """

    if request.method == 'GET':
        query = request.GET
        action_name = query.get('action', query.get('ACTION')).lower()        

        if action_name == 'get_projects':
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_projects(request, permission)

        elif action_name == 'get_scenarios_from_project':
            project_id = query.get('project_id')
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_scenarios_from_project(
                request, project_id, permission=permission)

        elif action_name == 'get_scenarios':
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_scenarios(request, permission=permission)

        elif action_name == 'get_scenarios_export_list':
            project_id = query.get('project_id')
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_scenarios_export_list(request, project_id, permission)

        elif action_name == 'get_scenario_tree':
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            breach_id = query.get('breach_id', None)
            true_or_false = {'0': False, '1': True, 'None': None}
            filter_onlyprojectswithscenario = true_or_false[query.get('onlyprojectswithscenario', '0')]

            filter = query.get('filter', 'all')
            filter_dict = {'all': None,
                           'all_with_results': [Scenario.STATUS_DISAPPROVED, Scenario.STATUS_APPROVED, Scenario.STATUS_CALCULATED],
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
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_results_from_scenario(
                request, scenario_id, permission=permission)

        elif action_name == 'get_tasks_from_scenario':
            scenario_id = query.get('scenario_id')
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_tasks_from_scenario(
                request, scenario_id, permission=permission)

        elif action_name == 'get_cutofflocations_from_scenario':
            scenario_id = query.get('scenario_id')
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_cutofflocations_from_scenario(
                request, scenario_id, permission=permission)

        elif action_name == 'get_regionsets':
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_regionsets(request, permission=permission)

        elif action_name == 'get_all_regions':
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_all_regions(request, permission=permission)

        elif action_name == 'get_region_tree':
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            filter_has_model = int(query.get('has_model',0))

            return service_get_region_tree(request, permission=permission, filter_has_model=filter_has_model)

        elif action_name == 'get_breaches':
            region_id = query.get('region_id')
            scenariofilter = int(query.get('scenariofilter', -1))
            return service_get_breaches(request, region_id, scenariofilter=scenariofilter)

        elif action_name == 'get_breach_tree':
                      
            region_id = query.get('region_id')
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            filter_bool_dict = {'1': True, '0': False}

            active = query.get('active', '0')
            onlyscenariobreaches = query.get('onlyscenariobreaches', '0')
            filter_active = filter_bool_dict[active]
            filter_onlyscenariobreaches = filter_bool_dict[onlyscenariobreaches]

            filter = query.get('filter', 'all')
            filter_dict = {'all': None,
                           'all_with_results': [Scenario.STATUS_DISAPPROVED, Scenario.STATUS_APPROVED, Scenario.STATUS_CALCULATED],
                           'rejected': [Scenario.STATUS_DISAPPROVED],
                           'accepted': [Scenario.STATUS_APPROVED],
                           'verify': [Scenario.STATUS_CALCULATED],
                           }
            filter_scenario = filter_dict[filter.lower()]

            return service_get_breach_tree(request, permission=permission, region_id=region_id, filter_onlyscenariobreaches=filter_onlyscenariobreaches, filter_scenario=filter_scenario, filter_active = filter_active)

        elif action_name == 'get_regions':
            regionset_id = query.get('regionset_id')
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
            return service_get_regions(request, regionset_id, permission=permission)
        elif action_name == 'get_cutofflocations':
            inundationmodel_id = query.get('inundationmodel_id', None)
            extwatermodel_id = query.get('extwatermodel_id', None)
            return service_get_cutofflocations(request,
                                               inundationmodel_id = inundationmodel_id,
                                               extwatermodel_id = extwatermodel_id)
        elif action_name == 'get_cutofflocationsets':
            inundationmodel_id = query.get('inundationmodel_id', None)
            extwatermodel_id = query.get('extwatermodel_id', None)
            return service_get_cutofflocationsets(request,
                                               inundationmodel_id = inundationmodel_id,
                                               extwatermodel_id = extwatermodel_id)

        elif action_name == 'get_cutofflocations_from_cutofflocationset':
            cutofflocationset_id = query.get('cutofflocationset_id', None)
            permission = int(query.get('permission',
                                       UserPermission.PERMISSION_SCENARIO_VIEW))
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
            breach_id= query.get('breach_id', None)
            return service_get_externalwatermodels(request,
                                               breach_id=breach_id)
        elif action_name == 'compose_scenario':
            breach_id= query.get('breach_id', None)
            return service_compose_scenario(request,
                                               breach_id=breach_id)



        elif action_name == 'get_externalwater_graph':
            mid = 24*60*60*1000

            width = int(query.get('width',None))
            height = int(query.get('height',None))
            breach_id= int(query.get('breach_id',None))
            extwmaxlevel= float(query.get('extwmaxlevel',-999))
            tpeak=  float(query.get('tpeak',0))/mid
            tstorm=  float(query.get('tstorm',0))/mid
            tsim=  float(query.get('tsim',0))/mid
            tstartbreach=  float(query.get('tstartbreach',0))/mid
            tdeltaphase=  float(query.get('tdeltaphase',0))/mid
            tide_id= int(query.get('tide_id',0))
            extwbaselevel= float(query.get('extwbaselevel',-999))
            use_manual_input= bool(query.get('useManualInput',False))
            timeserie= str(query.get('timeserie',0))

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
                                        timeserie)
        
        elif action_name == 'get_externalwater_csv':
            mid = 24*60*60*1000

            width = int(query.get('width',None))
            height = int(query.get('height',None))
            breach_id= int(query.get('breach_id',None))
            extwmaxlevel= float(query.get('extwmaxlevel',-999))
            tpeak=  float(query.get('tpeak',0))/mid
            tstorm=  float(query.get('tstorm',0))/mid
            tsim=  float(query.get('tsim',0))/mid
            tstartbreach=  float(query.get('tstartbreach',0))/mid
            tdeltaphase=  float(query.get('tdeltaphase',0))/mid
            tide_id= int(query.get('tide_id',0))
            extwbaselevel= float(query.get('extwbaselevel',-999))
            use_manual_input= bool(query.get('useManualInput',False))
            timeserie= str(query.get('timeserie',0))
            
            return get_externalwater_csv(request,
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

        elif  action_name == 'get_raw_result':
            presentationlayer = int(query.get('presentationlayer',None))
            return service_get_raw_result(request,
                                   presentationlayer)
        elif  action_name == 'get_import_scenario_uploaded_file':
            path = query.get('path', '')
            return service_get_import_scenario_uploaded_file(request, path)

        elif  action_name == 'get_attachment':
            scenario_id = query.get('scenario_id', None)
            path = query.get('path', '')
            return service_get_attachment(request, scenario_id, path)
        elif  action_name == 'get_existing_embankments_shape':
            bbox =  query.get('BBOX', None)
            width =  query.get('WIDTH', None)
            height =  query.get('HEIGHT', None)
            strategy_id = query.get('STRATEGY_ID', -1)
            region_id = query.get('REGION_ID', -1)
            if query.get('ONLY_SELECTED', False) == 'TRUE':
                only_selected = True
            else:
                only_selected = False
            return service_get_existing_embankments_shape(request, int(width), int(height), \
                                                          tuple([float(value) for value in bbox.split(',')]), int(region_id), int(strategy_id), only_selected)
        elif action_name == 'import_embankment_shape':
            return service_import_embankment_shape()
        elif action_name == 'get_externalwater_graph_session':
            return get_externalwater_graph_session(request)        
       
       
        elif  action_name == 'get_extra_shapes':
            bbox =  query.get('BBOX', None)
            width =  query.get('WIDTH', None)
            height =  query.get('HEIGHT', None)
            region_id = query.get('REGION_ID', -1)

            return service_get_extra_shapes(request, int(width), int(height), \
                                                          tuple([float(value) for value in bbox.split(',')]), int(region_id))
        elif  action_name == 'get_extra_grid_shapes':
            bbox =  query.get('BBOX', None)
            width =  query.get('WIDTH', None)
            height =  query.get('HEIGHT', None)
            region_id = query.get('REGION_ID', -1)

            return service_get_extra_grid_shapes(request, int(width), int(height), \
                                                          tuple([float(value) for value in bbox.split(',')]), int(region_id))
 
        
        else:
            #pass
            raise Http404

    elif request.method == 'POST':
        query = request.POST
        action_name = query.get('action', query.get('ACTION')).lower()    
        
        if action_name == 'post_newscenario':
            return service_save_new_scenario(request)
        elif action_name == 'save_drawn_embankment':            
            geometry = query.get('geometry')
            strategy_id = query.get('strategy_id', -1)
            region_id = query.get('region_id', -1)
            return service_save_drawn_embankment(geometry, strategy_id, region_id)
        elif action_name == 'select_existing_embankments_by_polygon':            
            geometry = query.get('geometry')
            strategy_id = query.get('strategy_id', -1)
            region_id = query.get('region_id', -1)
            return select_existing_embankments_by_polygon(geometry, strategy_id, region_id)
        elif action_name == 'get_strategy_id':
            return service_get_strategy_id()
        elif action_name == 'delete_measure':
            measure_ids = query.get('measure_ids', -1)    
            return service_delete_measure (measure_ids)
        elif action_name == 'get_externalwater_graph':
            mid = 24*60*60*1000

            width = int(query.get('width',None))
            height = int(query.get('height',None))
            breach_id= int(query.get('breach_id',None))
            extwmaxlevel= float(query.get('extwmaxlevel',-999))
            tpeak=  float(query.get('tpeak',0))/mid
            tstorm=  float(query.get('tstorm',0))/mid
            tsim=  float(query.get('tsim',0))/mid
            tstartbreach=  float(query.get('tstartbreach',0))/mid
            tdeltaphase=  float(query.get('tdeltaphase',0))/mid
            tide_id= int(query.get('tide_id',0))
            try:
                extwbaselevel= float(query.get('extwbaselevel',-999))
            except:
                extwbaselevel = None
            
            if query.get('use_manual_input',False) == 'true':
                use_manual_input = True
            else:
                use_manual_input = False

            timeserie= str(query.get('timeserie',0))

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
                                        timeserie)
        else:
            raise Http404

# not in use:
def service_get_scenarios_from_breach(request, breach_id, scenariofilter = -1):
    """Get scenario's.

    Conditions:
    - given BREACH
    - given scenariofilter SCENARIOSTATUS (all, approved, disapproved, to be approved)
    - permission level scenario_view

    """
    scenario_dict = {}
    breach = get_object_or_404(Breach, pk=breach_id)
    pm = PermissionManager(request.user)
    for s in breach.scenario_set.all():
        if pm.check_project_permission(s.project,
                                       UserPermission.PERMISSION_SCENARIO_VIEW):
            if scenariofilter == -1 or s.status == scenariofilter:
                scenario_dict[s.id] = s
    return render_to_response('flooding/scenario.json',
                              {'scenario_list': scenario_dict.values()})


def service_get_tasks_from_scenario(
    request, scenario_id, permission = UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get tasks from a given scenario.

    Conditions:
    - from given scenario (check permission for given scenario)
    - given permission level
    - todo: filter tasks(?)
    """
    scenario = get_object_or_404(Scenario, pk=scenario_id)
    pm = PermissionManager(request.user)
    if not(pm.check_project_permission(scenario.project, permission)):
        raise Http404
    #todo: filter
    object_list = scenario.task_set.all()
    return render_to_response('flooding/task.json',
                              {'object_list': object_list})
def service_get_scenarios_from_project(request, project_id, permission = UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get the list of scenarios from a project with given permission.

    return in JSON format

    """
    project = get_object_or_404(Project, pk = project_id)
    pm = PermissionManager(request.user)
    if not(pm.check_project_permission(project, permission)):
        raise Http404
    return render_to_response('flooding/scenario.json',
                              {'scenario_list': project.scenario_set.all()})

def service_get_scenarios(request, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get the list of scenarios with given permission and return in JSON format."""
    scenario_list = []
    pm = PermissionManager(request.user)
    project_list = pm.get_projects(permission)
    for p in project_list:
        scenario_list += p.scenario_set.all()
    return render_to_response('flooding/scenario.json',
                              {'scenario_list': scenario_list})

def service_get_results_from_scenario(
    request, scenario_id, permission = UserPermission.PERMISSION_SCENARIO_VIEW):
    """Get results from a given scenario.

    Conditions:
    - from given scenario (check permission for given scenario)
    - given permission level
    - todo: predefined types only
    """
    scenario = get_object_or_404(Scenario, pk=scenario_id)
    pm = PermissionManager(request.user)
    if not(pm.check_project_permission(scenario.project, permission)):
        raise Http404

    result = scenario.result_set.all().select_related('resulttype').order_by('resulttype__id')#shortname_dutch

    return render_to_response('flooding/result.json',
                              {'result_list': result})

