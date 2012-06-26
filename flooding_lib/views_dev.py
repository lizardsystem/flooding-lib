# -*- coding: utf-8 -*-
import datetime

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson

from flooding_lib import calc
from flooding_lib.models import Breach, WaterlevelSet, Measure, Region
from flooding_lib.models import ExternalWater, UserPermission, Project
from flooding_lib.models import Scenario, SobekModel, Strategy
from flooding_lib.models import ScenarioCutoffLocation, CutoffLocation
from flooding_lib.models import TaskType, Task, Waterlevel, ScenarioBreach
from flooding_lib.permission_manager import receives_permission_manager
from nens.sobek import SobekHIS
from django.views.decorators.cache import never_cache

#--------------------- services for sobek his results ---------------


def service_result(request, object_id, location_nr, parameter_nr):
    """Shows sobek his results in json, given result_id, location_nr
    and parameter_nr"""
    his = SobekHIS('/home/jack/struc.his')
    return render_to_response(
        'flooding/result_timeseries.json',
        {'data': his.get_timeseries_by_index(int(location_nr),
                                             int(parameter_nr))}
        )


def get_externalwater_graph_infowindow(
    request, width, height, scenario_breach_id):
    """  """
    scenario_breach = get_object_or_404(ScenarioBreach, pk=scenario_breach_id)
    if not scenario_breach.tstartbreach:
        scenario_breach.tstartbreach = 0
    if not scenario_breach.tide:
        scenario_breach_tide_id = None
    else:
        scenario_breach_tide_id = scenario_breach.tide.id

    if scenario_breach.manualwaterlevelinput:
        waterlevels = (
            scenario_breach.waterlevelset.waterlevel_set.all().order_by(
            'time'))
        time_values = []
        for wl in waterlevels:
            time_values += [','.join([str(wl.time), str(wl.value)])]
        manual_timeserie = '|'.join(time_values)
    else:
        manual_timeserie = ""

    return get_externalwater_graph(
        request, width, height, scenario_breach.breach.id,
        scenario_breach.extwmaxlevel, scenario_breach.tpeak,
        scenario_breach.tstorm, scenario_breach.scenario.tsim,
        scenario_breach.tstartbreach, scenario_breach.tdeltaphase,
        scenario_breach_tide_id, scenario_breach.extwbaselevel,
        scenario_breach.manualwaterlevelinput, manual_timeserie,
        False)


def get_externalwater_graph(
    request, width, height, breach_id, extwmaxlevel, tpeak, tstorm, tsim,
    tstartbreach=0, tdeltaphase=None, tide_id=None, extwbaselevel=None,
    useManualInput=False, manualTimeserie="", save_in_session=True):
    """  """
    breach = get_object_or_404(Breach, pk=breach_id)
    if not useManualInput:
        waterlevel = calc.BoundaryConditions(
            breach, extwmaxlevel, tpeak, tstorm, tsim, tstartbreach,
            tdeltaphase, tide_id, extwbaselevel)
    else:
        waterlevel = calc.BoundaryConditions(
            breach, extwmaxlevel, tpeak, tstorm, tsim, tstartbreach,
            tdeltaphase, tide_id, extwbaselevel)
        waterlevel.set_waterlevels(manualTimeserie)

    response = HttpResponse(content_type='image/png')  # image/png
    if save_in_session:
        request.session['external_water_graph'] = waterlevel.get_graph(
            response, width, height)
        return HttpResponse('Grafiek opgeslagen in sessie')
    else:
        return waterlevel.get_graph(response, width, height)


def get_externalwater_graph_session(request):
    return request.session['external_water_graph']


def get_externalwater_csv(
    request, width, height, breach_id, extwmaxlevel, tpeak, tstorm, tsim,
    tstartbreach=0, tdeltaphase=None, tide_id=None, extwbaselevel=None,
    useManualInput=False, manualTimeserie=""):
    """  """
    breach = get_object_or_404(Breach, pk=breach_id)
    if not useManualInput:
        waterlevel = calc.BoundaryConditions(
            breach, extwmaxlevel, tpeak, tstorm, tsim, tstartbreach,
            tdeltaphase, tide_id, extwbaselevel)
    else:
        waterlevel = calc.BoundaryConditions(
            breach, extwmaxlevel, tpeak, tstorm, tsim, tstartbreach,
            tdeltaphase, tide_id, extwbaselevel)
        waterlevel.set_waterlevels(manualTimeserie)

    answer = '\n'.join([
            "%s,%.3f" %
            (a['time'], a['waterlevel'])
            for a in waterlevel.get_waterlevels()])
    return HttpResponse(answer, mimetype="application/csv", content_type='csv')


def service_save_new_scenario(request):
    """  """

    def to_intervalfloat(value):
        if value == None:
            return None
        else:
            return float(value) / (24 * 60 * 60 * 1000)

    query = request.POST

    tsim = to_intervalfloat(query.get('tsim_ms'))
    breach = Breach.objects.get(pk=query.get('breach_id'))
    #Scenario

    scenario = Scenario.objects.create(
        name=query.get('name'),
        owner=request.user,
        remarks=query.get('remarks'),
        sobekmodel_inundation=SobekModel.objects.get(
            pk=query.get('inundationmodel')),
        tsim=to_intervalfloat(query.get('tsim_ms')),
        calcpriority=query.get('calcpriority'))
    scenario.set_project(Project.objects.get(pk=query.get('project_fk')))

    scenario.code = '2s_c_%i' % scenario.id
    scenario.save()

    task = Task.objects.create(
        scenario=scenario,
        tasktype=TaskType.objects.get(pk=50),
        creatorlog=request.user.get_full_name(),
        tstart=datetime.datetime.now())

    useManualInput = query.get("useManualInput", False)
    if useManualInput == 'false' or useManualInput == False:
        useManualInput = False
    else:
        useManualInput = True

    waterlevel_list = []
    if useManualInput:

        js_waterlevel_set = query.get("waterlevelInput").split('|')
        for js_wl in js_waterlevel_set:
            js_waterlevel_props = js_wl.split(',')
            wl = {}
            wl['time'] = float(js_waterlevel_props[0])
            wl['waterlevel'] = float(js_waterlevel_props[1])
            waterlevel_list += [wl]
    else:
        waterlevel = calc.BoundaryConditions(
            breach,
            float(query.get('extwmaxlevel')),
            to_intervalfloat(query.get('tpeak_ms')),
            to_intervalfloat(query.get('tstorm_ms')),
            to_intervalfloat(query.get('tsim_ms')),
            to_intervalfloat(query.get('tstartbreach_ms')),
            to_intervalfloat(query.get('tdeltaphase_ms')),
            int(query.get('loctide', -999)),
            query.get('extwbaselevel'))
        waterlevel_list = waterlevel.get_waterlevels(0, tsim)

    waterlevelset = WaterlevelSet.objects.create(
        name=scenario.name,
        type=WaterlevelSet.WATERLEVELSETTYPE_BREACH,
        code=scenario.code)

    for wl in waterlevel_list:
        Waterlevel.objects.create(
            time=wl['time'],  # interval
            value=wl['waterlevel'],
            waterlevelset=waterlevelset)

    #ScenarioBreaches
    try:
        sobekmodel_extwater = SobekModel.objects.get(
            pk=query.get('externalwatermodel'))
    except SobekModel.DoesNotExist:
        sobekmodel_extwater = None

    try:
        tide = WaterlevelSet.objects.get(pk=query.get('loctide'))
    except WaterlevelSet.DoesNotExist:
        tide = None

    ScenarioBreach.objects.create(
        breach=breach,
        scenario=scenario,
        sobekmodel_externalwater=sobekmodel_extwater,
        #bres widthbrinit
        widthbrinit=query.get('widthbrinit'),
        methstartbreach=ScenarioBreach.METHOD_START_BREACH_TOP,
        tstartbreach=to_intervalfloat(query.get('tstartbreach_ms')),
        hstartbreach=query.get('extwmaxlevel'),
        brdischcoef=query.get('brdischcoef'),
        brf1=query.get('brf1'),
        brf2=query.get('brf2'),
        bottomlevelbreach=query.get('bottomlevelbreach'),
        ucritical=query.get('ucritical'),
        pitdepth=query.get('pitdepth'),
        tmaxdepth=to_intervalfloat(query.get('tmaxdepth_ms')),

        waterlevelset=waterlevelset,

        #waterlevels
        extwmaxlevel=query.get('extwmaxlevel'),
        extwbaselevel=query.get('extwbaselevel', None),
        extwrepeattime=query.get('extwrepeattime', None),
        tide=tide,
        tstorm=to_intervalfloat(query.get('tstorm_ms', None)),
        tpeak=to_intervalfloat(query.get('tpeak_ms', None)),
        tdeltaphase=to_intervalfloat(query.get('tdeltaphase_ms', None)),
        code=scenario.code,
        manualwaterlevelinput=useManualInput)

    loccutoffs = query.get("loccutoffs").split(',')
    if len(loccutoffs[0]) > 0:
        for cutoffloc in loccutoffs:
            cutoffloc_id = cutoffloc.split('|')[0]
            cutoffloc_action = int(cutoffloc.split('|')[1])
            cutoffloc_tclose = cutoffloc.split('|')[2]
            ScenarioCutoffLocation.objects.create(
                cutofflocation=CutoffLocation.objects.get(pk=cutoffloc_id),
                scenario=scenario,
                action=cutoffloc_action,
                tclose=to_intervalfloat(cutoffloc_tclose))

    measures = query.get("measures").split(';')

    if len(query.get("measures")) > 0:
        strategy = Strategy.objects.create(
            name="scen: %s" % scenario.name[:30])

        if query.get('saveStrategy') == 'true':
            strategy.name = query.get('strategyName', "-")
            strategy.region = breach.region
            strategy.visible_for_loading = True
            strategy.user = request.user
            strategy.save_date = datetime.datetime.now()

        strategy.save()

        scenario.strategy_id = strategy.id
        scenario.save()

        for measure_input in measures:
            measure_part = measure_input.split('|')
            measure = Measure.objects.get(pk=measure_part[0])
            measure_new = Measure.objects.create(
                name=measure_part[1],
                reference_adjustment=measure_part[2],
                adjustment=measure_part[3])
            measure.save()

            measure_new.strategy.add(strategy)

            for embankment in measure.embankmentunit_set.all():
                measure_new.embankmentunit_set.add(embankment)

    else:
        pass
        #Strategy.objects.get(pk=strategy_id).delete()

    task.tfinished = datetime.datetime.now()
    task.successful = True
    task.save()

    scenario.update_status()
    answer = {
        'successful': True,
        'save_log': 'opgeslagen. scenario id is: %i' % scenario.id}

    return HttpResponse(simplejson.dumps(answer), mimetype="application/json")


@never_cache
def service_select_strategy(request, region_id):
    """  """
    region = Region.objects.get(pk=region_id)
    #data[0].tdeltaphase = intervalFormatter(intervalReader("0 00:00"));
    strategies = Strategy.objects.filter(
        visible_for_loading=True, region=region).order_by('name')

    return render_to_response(
        'flooding/select_strategy.html',
        {
         'region': region,
         'strategies': strategies,
         'current_strategy': 12,
         })


@receives_permission_manager
def service_compose_scenario(request, permission_manager, breach_id):
    """  """
    breach = Breach.objects.get(pk=breach_id)
    #data[0].tdeltaphase = intervalFormatter(intervalReader("0 00:00"));
    bottomlevelbreach = {}
    pitdepth = {}
    if not breach.groundlevel == None:
        if not breach.canalbottomlevel == None:
            bottomlevelbreach['defaultvalue'] = max(
                breach.groundlevel, breach.canalbottomlevel) + 0.01
            pitdepth['defaultvalue'] = breach.groundlevel - 0.01
            bottomlevelbreach['min'] = breach.canalbottomlevel
        else:
            bottomlevelbreach['defaultvalue'] = breach.groundlevel
            pitdepth['defaultvalue'] = breach.groundlevel - 0.01
            bottomlevelbreach['min'] = -10

        pitdepth['max'] = breach.groundlevel

    projects_queryset = permission_manager.get_projects(
        UserPermission.PERMISSION_SCENARIO_ADD)
    projects = projects_queryset.filter(
        regions__breach=breach).distinct().values_list('id', flat=True)
    projects2 = projects_queryset.filter(
        regionsets__regions__breach=breach
        ).distinct().values_list('id', flat=True)

    projects = Project.objects.filter(
        Q(id__in=projects) |
        Q(id__in=projects2)).distinct().order_by('name')

    sealake = (breach.externalwater.type == ExternalWater.TYPE_SEA or
               breach.externalwater.type == ExternalWater.TYPE_LAKE)
    lake = breach.externalwater.type == ExternalWater.TYPE_LAKE
    sea = breach.externalwater.type == ExternalWater.TYPE_SEA
    loctide = WaterlevelSet.objects.filter(
        type=WaterlevelSet.WATERLEVELSETTYPE_TIDE).order_by('name')

    print 'ready to respond'
    return render_to_response(
        'flooding/compose_scenario.html',
        {
         'projects': projects,
         'sealake': sealake,
         'lake': lake,
         'sea': sea,
         'loctide': loctide,
         'pitdepth': pitdepth,
         'bottomlevelbreach': bottomlevelbreach,
         'breach': breach
         })


'''
vul loccutoffs_ids
loccutoffs_tclose

nog naar kijken: start_calculation
!mis maxdeflevel
! geeft niet altijd wat terug - breach.get_all_projects()

    breach.region.name
    breach.name
    breach.canalbottomlevel
    #breach.decheight
    breach.decheightbaselevel
    #breach.defaulttide_id
    #breach.defbaselevel
    #breach.defrucritical,
    breach.get_all_projects
    breach.groundlevel
    #breach.levelnormfrequency

    breach.region.normfrequency

    'deftpeak', 'deftsim', 'deftstorm', 'maxlevel', 'minlevel', 'name',
    'type'
'''
