#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed.

from lizard_worker.models import Workflow
from lizard_worker.models import WorkflowTask
from lizard_worker.models import WorkflowTemplate
from lizard_worker.models import WorkflowTemplateTask
from lizard_worker.worker.action import Action
from lizard_worker.worker.messaging_body import Body

from pika import BasicProperties

import time
import datetime
import logging


class ActionTaskPublisher(Action):
    """
    ActionStartTask publishes a singel task to
    the queue.
    """

    def __init__(self, connection, task):
        self.connection = connection
        self.log = logging.getLogger('worker.action.workflow')
        self.channel = self.connection.channel()
        self.task = task

    def perform(self):
        """
        Creates message body as instruction
        Sends message the broker
        """
        self.set_message_properties()
        self.set_message_body()
        try:
            self.publish_task()
            return True
        except:
            return False

    def set_message_body(self):
        """
        Creates a body of a message.
        """
        self.body = Body().body
        self.body[Body.INSTRUCTION] = {self.task.code.name: self.task.code.name}
        self.body[Body.WORKFLOW_TASKS] = {self.task.code.name: self.task.id}
        self.body[Body.MAX_FAILURES] = {self.task.code.name: self.task.max_failures}
        self.body[Body.MAX_FAILURES_TMP] = {self.task.code.name: self.task.max_failures}
        self.body[Body.WORKFLOW_ID] = self.task.workflow.id
        self.body[Body.PRIORITY] = self.task.workflow.priority
        self.body[Body.SCENARIO_ID] = self.task.workflow.scenario
        self.body[Body.SCENARIO_TYPE] = self.task.workflow.scenario_type
        self.body[Body.TIME] = time.time()
        self.body[Body.CURR_TASK_CODE] = self.task.code.name

    def publish_task(self):
        """Sends message to the broker."""
        queue = self.task.code.name
        self.send_trigger_message(
            self.body,
            "Message emitted to queue %s" % queue,
            queue)
        self.set_task_status(self.QUEUED)
        self.set_current_task(queue)
        self.log.info("Task is {}.".format(self.QUEUED))

    def set_message_properties(self, priority=0, message_id=0):
        priority = self.task.workflow.priority
        self.properties = BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            priority=priority)

    def callback(self, ch, method, properties, body):
        pass


class ActionHeartbeat(Action):
    """
    Publish the HEARTBEAT message.
    """
    def __init__(self, connection, queue_codes):
        self.connection = connection
        self.log = logging.getLogger(__name__)
        self.channel = self.connection.channel()
        self.queue_codes = queue_codes

    def perform(self):
        """
        Creates message body as instruction
        Sends message the broker
        """
        self.set_message_properties()
        self.set_message_body()
        try:
            self.publish_tasks()
            return True
        except:
            return False

    def set_message_body(self):
        """
        Creates a body of a message.
        """
        self.body = Body().body
        self.body[Body.TIME] = time.time()
        self.body[Body.IS_HEARTBEAT] = True

    def publish_tasks(self):
        """Sends message to the broker."""
        for queue_code in self.queue_codes:
            self.send_trigger_message(
                self.body,
                "HEARBEAT emitted to queue {}".format(queue_code),
                queue_code)
            print "HEARTBEAT emitted to queue {}".format(queue_code)
            time.sleep(2)

    def set_message_properties(self, priority=0, message_id=0):
        self.properties = BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            priority=priority)

    def callback(self, ch, method, properties, body):
        pass


class ActionWorkflow(Action):

    def __init__(self, connection, scenario_id, workflowtemplate_id,
                 workflowpriority=0, worker_nr="999", scenario_type="flooding_scenario"):
        """
        scenario_id is not necessarily a lizard-flooding scenario
        object id. It could be anything. The field scenario_type
        describes the object type. In general this should be metadata,
        but it can also be used in a task. Normally you would know
        what kind of id you get in a task.
        """
        self.connection = connection
        self.log = logging.getLogger('worker.action.workflow')
        self.scenario_id = scenario_id
        self.scenario_type = scenario_type
        self.workflowtemplate_id = workflowtemplate_id
        self.workflowpriority = workflowpriority
        self.workflow = None
        self.bulk_tasks = []
        self.channel = self.connection.channel()
        self.worker_nr = worker_nr

    def callback(self, ch, method, properties, body):
        pass

    def perform_workflow(self):
        """
        Creates workflow and tasks.
        Creates message body as instruction
        Sends message to next queue(s)
        """
        if not self.create_workflow():
            # TODO define default body or log it only to logfile
            # self.log.error("Workflow is interrupted.")
            return

        #self.body = self.retrieve_workflow_options()
        self.set_message_body()
        self.set_message_properties()
        try:
            self.start_workflow()
            success = True
        except:
            success = False
        return success

    def create_workflow(self):
        """
        Creates and sets workflow, tasks.
        """
        try:
            template = WorkflowTemplate.objects.get(
                pk=self.workflowtemplate_id)
            if template is None:
                self.log.warning("Workflow template '%s' does not exist.")
                return False
            template_tasks = WorkflowTemplateTask.objects.filter(
                workflow_template=template.id)
            if template_tasks.exists() == False:
                self.log.warning(
                    "Workflow template '%s' has not any task." % template.code)
                return False
            # Adde field tcreated to workflow
            self.workflow = Workflow(scenario=self.scenario_id,
                                     code=template.code,
                                     template=template,
                                     tcreated=datetime.datetime.today(),
                                     priority=self.workflowpriority)
            self.workflow.save()
            # TODO define default body
            # self.log.debug("Created workflow '%s' for scenario '%s'." % (
            #         template.code, self.scenario_id))
            self.bulk_tasks = []
            for template_task in template_tasks:
                task = WorkflowTask(workflow=self.workflow,
                                    code=template_task.code,
                                    tcreated=datetime.datetime.today(),
                                    parent_code=template_task.parent_code,
                                    max_failures=template_task.max_failures,
                                    max_duration_minutes=template_task.max_duration_minutes)
                task.save()
                self.bulk_tasks.append(task)
            return True
        except Exception as ex:
            self.log.error("{0}".format(ex))
            return False

    def set_message_body(self):
        """
        Creates a body as instruction mechanizm
        for messaging.
        """
        self.body = Body().body
        instruction = {}
        workflow_tasks = {}
        task_failures = {}

        for task in self.bulk_tasks:
            instruction[task.code.name] = task.parent_code.name
            workflow_tasks[task.code.name] = unicode(task.id)
            task_failures[task.code.name] = task.max_failures

        self.body[Body.INSTRUCTION] = instruction
        self.body[Body.WORKFLOW_TASKS] = workflow_tasks
        self.body[Body.MAX_FAILURES] = task_failures
        self.body[Body.MAX_FAILURES_TMP] = task_failures
        self.body[Body.WORKFLOW_ID] = self.workflow.id
        self.body[Body.PRIORITY] = self.workflow.priority
        self.body[Body.SCENARIO_ID] = self.scenario_id
        self.body[Body.SCENARIO_TYPE] = self.scenario_type
        self.body[Body.TIME] = time.time()

    def start_workflow(self):
        """
        Send trigger and logging messages to broker.
        """

        queues = self.root_queues()
        for queue in queues:
            self.set_task_status(self.QUEUED)
            self.set_current_task(queue)
            self.log.info("Task is {}.".format(self.QUEUED))
            self.send_trigger_message(self.body,
                                      "Message emitted to queue %s" % queue,
                                      queue)

    def set_message_properties(self, priority=0, message_id=0):
        if self.workflow is not None:
            priority = self.workflow.priority
            message_id = self.workflow.id

        self.properties = BasicProperties(content_type="application/json",
                                          delivery_mode=2,
                                          priority=priority,
                                          message_id=str(message_id))
