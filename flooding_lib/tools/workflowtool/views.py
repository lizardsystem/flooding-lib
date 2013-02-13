import datetime
import os.path

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.utils import simplejson as json

from lizard_worker import executor
from lizard_worker import models as workermodels

from flooding_lib import models as libmodels


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

class CountPagesView(View):
    """
    """

    def get(self, request):
        amount_per_step = 200
        if not request.user.is_superuser:
            return render_to_response('403.html')
        count_scenarios = libmodels.Scenario.objects.all().count()
        if count_scenarios <= amount_per_step:
            last_pagenumber = 1
        else:
            rest_scenarios = count_scenarios % amount_per_step
            last_pagenumber = (count_scenarios - rest_scenarios) / amount_per_step

        context = {'last_pagenumber': last_pagenumber}

        return HttpResponse(content=json.dumps(context))


class ScenarioWorkflowView(View):
    """
    Scenario processing view:
    shows latest execution status.
    Contains functionality to execute a Scenario
    """

    def get(self, request):
        if request.user.is_superuser is False:
            return render_to_response('403.html')

        rowstoload = int(request.GET.get("rowstoload", "25"))
        scenario_id = request.GET.get("scenario_id")
        scenario_ids = []
        if scenario_id != 'null':
            scenario_ids = self.scenarios_string_to_list(scenario_id)
        
        if len(scenario_ids) > 0:
            scenarios = libmodels.Scenario.objects.filter(
                id__in=scenario_ids).order_by("-id")
        else:
            scenarios = libmodels.Scenario.objects.all().order_by("-id")
            scenarios = scenarios[:rowstoload]
            
        processing = []

        for scenario in scenarios:
            workflows = workermodels.Workflow.objects.filter(
                scenario=scenario.id)
            
            template_code = ""
            template_id = ""
            execute_url = ""
            if scenario.workflow_template is not None:
                template_code = scenario.workflow_template.code
                template_id = scenario.workflow_template.id
                execute_url = self.create_execution_url(scenario.id, template_id, request.get_host())
            
            scenario_workflow = {
                "execute_url": execute_url,
                'scenario_id': scenario.id,
                'scenario_name': scenario.name,
                'template_id': template_id,
                'template_code': template_code,
                'breach': [br.name for br in scenario.breaches.all()],
                'region': [br.region.name for br in scenario.breaches.all()],
                'project_id': scenario.main_project.id,
                'project_name': scenario.main_project.name}
            if workflows.exists():
                workflow = workflows.latest('tcreated')
                created = ""
                finished = ""
                if isinstance(workflow.tcreated, datetime.datetime):
                    created = workflow.tcreated.isoformat()
                if isinstance(workflow.get_tfinished(), datetime.datetime):
                    finished =workflow.get_tfinished().isoformat()  
                scenario_workflow.update({'workflows_count': workflows.count(),
                                          'workflow_status': workflow.get_status(),
                                          'workflow_created': created,
                                          'workflow_tfinished': finished})
            processing.append(scenario_workflow)

        return HttpResponse(content=json.dumps(processing))

    def scenarios_string_to_list(self, scenarios_string):
        """
        Creates a list of numbers from string.
        Expected string like '100,20-70,1-2,200'.
        """
        raw_list = scenarios_string.split(',')
        numbers_list = [self.cnumber(n) for n in raw_list if n.find('-') == -1]
        ranges_list = [self.clist2number(n.split('-')) for n in raw_list if n.find('-') > -1]
        numbers_2dem_list = [range(l[0],l[1]+1) for l in ranges_list if len(l) > 1]
        for l in numbers_2dem_list:
            numbers_list.extend(l)
        return numbers_list

    def cnumber(self, n_string):
        """ Convert text to number."""
        try:
            return int(n_string)
        except:
            return -1

    def clist2number(self, n_list):
        """Convert all texts in list to numbers."""
        try:
            return map(int, n_list)
        except:
            return -1

    def create_execution_url(self, scenario_id, template_id, host):
        """Create url to execute a scenario."""
        execution_url = reverse("workflow_start_scenario")
        url_params = "scenario_id={0}&template_id={1}".format(
            scenario_id, template_id)
        return "http://{0}{1}?{2}".format(host, execution_url, url_params)


def execute_scenario(request):
    if request.user.is_superuser is False:
        return render_to_response('403.html')
    scenario_id = request.GET.get('scenario_id')
    template_id = request.GET.get('template_id', u'')
    success = False
    success = executor.start_workflow(scenario_id, template_id)
    message = "Scenario {0} is {1} in de wachtrij geplaatst."
    if success is False:
        message = message.format(scenario_id, "NIET")
    else:
        message = message.format(scenario_id, "")
    context = {'success': success, 'message': message}
    return HttpResponse(content=json.dumps(context))


def execute_scenarios(request):
    if request.user.is_superuser is False:
        return render_to_response('403.html')
    data = json.loads(request.POST.get('scenarios', '[]'))
    result = []
    for scenario in data:
        success = False;
        if scenario["template_id"] not in ['null', '']:
            success = executor.start_workflow(
                scenario["scenario_id"], scenario["template_id"])
        result.extend([{"scenario_id": scenario["scenario_id"],
                       "success": success}])
    return HttpResponse(content=json.dumps(result))


def rowstoload_options(request):
    if request.user.is_superuser is False:
        return render_to_response('403.html')
    context = [{"name":"--no limit--", "val":1000000},
               {"name":"25", "val":25},
               {"name":"50", "val":50},
               {"name":"100", "val":100},
               {"name":"500", "val":500},
               {"name":"1000", "val":1000}]
    return HttpResponse(content=json.dumps(context))
