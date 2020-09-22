#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed.

import json
from datetime import datetime

from lizard_worker.worker.action import Action
from lizard_worker.models import WorkflowTask
from lizard_worker.models import Logging, Workflow
from lizard_worker.models import Worker
from lizard_worker.worker.messaging_body import Body

import logging
log = logging.getLogger('flooding.action_logging')


class ActionLogging(Action):

    def callback(self, ch, method, properties, body):
        """
        Inserts logging data into database.
        Used by logging_worker.
        Cuts message to max. 200 chars.

        body is json
        message is in body['message']
        """
        body_dict = json.loads(body)
        # TODO move keys of body to Action class as class variables
        task_code = body_dict.get(Body.CURR_TASK_CODE, None)
        # TODO Implement logging of root/supervisor worker
        tasks = body_dict.get(Body.WORKFLOW_TASKS, None)
        event_time = body_dict.get(Body.TIME)
        task_id = tasks.get(task_code, None)
        try:
            task = WorkflowTask.objects.get(pk=task_id)
        except:
            task = None
        workflow_id = body_dict.get(Body.WORKFLOW_ID, None)
        try:
            workflow = Workflow.objects.get(pk=workflow_id)
        except:
            workflow = None

        task_status = body_dict.get(Body.STATUS, None)
        is_heartbeat = body_dict.get(Body.IS_HEARTBEAT)

        if task_status is not None and task_status != "" and not is_heartbeat:
            self.store_task_status(task, task_status, event_time)

        # TODO [:200]

        message = body_dict[Body.MESSAGE][:200]
        worker = self.update_or_create_worker(body_dict)

        try:
            new_logging = Logging(
                workflow=workflow,
                task=task,
                time=datetime.fromtimestamp(event_time),
                level=body_dict.get(Body.CURR_LOG_LEVEL, None),
                message=message,
                is_heartbeat=is_heartbeat,
                worker=worker)
            new_logging.save()
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as ex:
            log.error(",".join(map(str, ex.args)))

    def retrieve_body(self):
        """ Return to insrt into db
        """

    def store_task_status(self, task, status, event_time):
        """
        Save status and event time to database

        Arguments:
        event_time - "", float or None
        """
        task.status = status
        if isinstance(event_time, datetime) or event_time == "":
            task.set_action_time()
        else:
            task.set_action_time(datetime.fromtimestamp(event_time))
        task.save()

    def update_or_create_worker(self, body_dict):
        """
        Save data to Worker model.
        """
        worker_nr = body_dict.get(Body.WORKER_NR, None)
        node = body_dict.get(Body.NODE)
        if worker_nr is None or node is None:
            return
        event_time = body_dict.get(Body.TIME)
        status = body_dict.get(Body.WORKER_STATUS, None)
        options = {'worker_nr': worker_nr,
                  'node': node,
                  'time': datetime.fromtimestamp(event_time),
                  'status': status}
        workers = Worker.objects.filter(worker_nr=worker_nr, node=node)
        if workers.exists():
            workers.update(**options)
            worker = workers[0]
        else:
            worker = Worker(**options)
            worker.save()

        return worker
