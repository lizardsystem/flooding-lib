# Some scenarios had already been approved or disapproved in the old system
# We copied their approval status into the new system
# However, we didn't copy their creatorlog and remarks
# That data is still in the old Task table

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from django.core.management.base import BaseCommand
#from django.core.management.base import CommandError

APPROVAL_TASKTYPE_ID = 190

from flooding_lib import models
from flooding_lib.tools.approvaltool import models as approvalmodels


class Command(BaseCommand):
    def handle(self, *args, **options):
        states = approvalmodels.ApprovalObjectState.objects.exclude(
            successful=None).filter(
            creatorlog='').filter(
                approvalobject__name="Generic approval object")

        for state in states:
            print("{0} ({1}): ({2})".
                  format(state.id, state.creatorlog, state.remarks))

            for scenarioproject in (
                state.approvalobject.scenarioproject_set.all()):
                print("Scenario id: {0}".format(scenarioproject.scenario.id))

                # Now find a task 190 for this in the Task table
                tasks = list(models.Task.objects.filter(
                    scenario=scenarioproject.scenario,
                    tasktype__id=APPROVAL_TASKTYPE_ID))
                if tasks:
                    task = tasks[0]
                    print('creatorlog: {0} remarks: {1}'.
                          format(task.creatorlog, task.remarks))

                    # And save
                    state.creatorlog = task.creatorlog
                    state.remarks = task.remarks
                    state.save()

