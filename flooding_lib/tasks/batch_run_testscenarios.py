"""
  script for adding test calculations for Waterbaord Hunze en Aa's

"""

from flooding_lib.models import RegionSet, Project
from django.contrib.auth.models import User
import logging
from lizard_worker import models as workermodels
from lizard_worker import executor as workerexecutor

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',)
log = logging.getLogger('nens')
#log.setLevel(logging.INFO)
log.setLevel(20)
log = logging.getLogger('pika')
#log.setLevel(logging.INFO)
log.setLevel(20)
#import flooding_lib.views.dev.service_save_new_scenario

def start_scenarios_again(start_id, end_id):

    for scenario_id in range(start_id, end_id+1):

        workflow_template = workermodels.WorkflowTemplate.objects.get(
                code=workermodels.WorkflowTemplate.DEFAULT_TEMPLATE_CODE)
        workerexecutor.start_workflow(scenario_id, workflow_template.id)

# If this has 'test' in the name, while the file has 'test' in the name too,
# nose will try to run it as a unit test...
def add_te_st_calcs():
    user = User.objects.get(username='BR')
    project = Project.objects.get(pk=140)


    region_set = RegionSet.objects.get(pk=23)

    #for region in region_set.regionset_regions.region.all():
    for region in region_set.regions.filter(id__in=[455,456,463,464,467]):

        for breach in region.breach_set.filter(active=True):

            print "breach: %i0"%breach.id

            request = {
                'tsim_ms': 7200000,
                'breach_id': breach.id,
                'name': 'test som config',
                'user': user,
                'remarks': '2 uur som voor testen van configuratie',
                'inundationmodel': breach.region.sobekmodels.all()[0].id,
                'externalwatermodel': breach.externalwater.sobekmodels.all()[0].id,
                'calcpriority': 20,
                'project_fk': project.id,

                'extwmaxlevel': -9999,
                'tpeak_ms': 0,
                'tstorm_ms': 0,
                'tstartbreach_ms': 0,
                'tdeltaphase_ms': 0,
                'extwbaselevel': -9999,

                'widthbrinit': 10,
                'brdischcoef': 1,
                'brf1': 1.3,
                'brf2': 0.04,
                'bottomlevelbreach': breach.groundlevel,
                'ucritical': 0.5,
                'pitdepth': (breach.groundlevel-0.01),
                'tmaxdepth_ms': 7200000,

                'loccutoffs': "",
                'measures': "",
            }
            service_save_new_scenario(request)

import datetime

from django.db.models import Q
from flooding_lib import calc
from flooding_lib.models import Breach, WaterlevelSet, Measure, Region
from flooding_lib.models import ExternalWater, UserPermission, Project
from flooding_lib.models import Scenario, SobekModel, Strategy
from flooding_lib.models import ScenarioCutoffLocation, CutoffLocation
from flooding_lib.models import Waterlevel, ScenarioBreach


def service_save_new_scenario(request):
    """  """

    def to_intervalfloat(value):
        if value == None:
            return None
        else:
            return float(value) / (24 * 60 * 60 * 1000)

    query = request

    tsim = to_intervalfloat(query.get('tsim_ms'))
    breach = Breach.objects.get(pk=query.get('breach_id'))
    #Scenario

    scenario = Scenario.objects.create(
        name=query.get('name'),
        owner=request['user'],
        remarks=query.get('remarks'),
        sobekmodel_inundation=SobekModel.objects.get(
            pk=query.get('inundationmodel')),
        tsim=to_intervalfloat(query.get('tsim_ms')),
        calcpriority=query.get('calcpriority'))
    scenario.set_project(Project.objects.get(pk=query.get('project_fk')))

    scenario.code = '2s_c_%i' % scenario.id
    scenario.save()

    task = scenario.setup_initial_task(request['user'])

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

    print answer['save_log']

    return True



