from optparse import make_option

from django.core.management.base import BaseCommand

from lizard_worker.executor import start_workflow
from lizard_worker.models import WorkflowTemplate
from flooding_lib import models


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--scenarios',
                    default=None,
                    help='Scenario ids separated with "," as string.'),
        make_option('--templatecode',
                    default=None,
                    help='Template code'),
        )

    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    def handle(self, *args, **options):
        scenarios = options.get('scenarios')
        templatecode = options.get('templatecode')
        workflow_template = None

        if templatecode is None:
            print "Pass a templatecode."
            return
        else:
            try:
                workflow_template = WorkflowTemplate.objects.get(code=templatecode)
            except:
                print "Templete {} does not exsist.".templatecode
                return
        
        if scenarios is None:
            sc = models.Scenario.objects.all()
        else:
            scenarios = scenarios.replace(' ', '').split(',')
            sc = models.Scenario.objects.filter(id__in=scenarios)

        for s in sc:
            result = start_workflow(s.id, workflow_template.id, log_level='DEBUG')
        
        print "The end."
