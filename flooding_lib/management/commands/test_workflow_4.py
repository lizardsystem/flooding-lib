from django.core.management.base import BaseCommand
from lizard_worker.executor import start_workflow
from lizard_worker.models import WorkflowTemplate


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print "Starting workflow 4 (3Di)..."
        workflow_template = WorkflowTemplate.objects.get(code='4')
        result = start_workflow(
            args[0],  # scenario id
            workflow_template.id, log_level='DEBUG')
