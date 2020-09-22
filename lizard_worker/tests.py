# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

import mock

from django.test import TestCase
from lizard_worker import models as w_models
from lizard_worker.worker.action import Action
from lizard_worker.worker.action_task import ActionTask
from lizard_worker.worker.messaging_body import Body


class ExampleTest(TestCase):

    def test_something(self):
        self.assertEquals(1, 1)


class WorkflowTest(TestCase):

    def setUp(self):
        self.tasks = (u'120', u'130', u'132')
        self.create_workflow_template()
        self.template = w_models.WorkflowTemplate.objects.get(
            code=w_models.WorkflowTemplate.DEFAULT_TEMPLATE_CODE)
        self.create_task_types()
        self.add_tasks_to_workflow_template()
        self.workflow = self.create_workflow()
        self.create_tasks()

    def test_is_status_failed(self):
        """
        Test is successful if one or more tasks has/have
        the status FAILED.
        """
        self.update_tasks_status(
            Action.FAILED, self.tasks[0])
        self.assertEquals(self.workflow.is_failed(), True)

    def test_is_status_success(self):
        """
        Test is successful if all tasks have
        the status SUCCESS.
        """
        self.update_tasks_status(Action.SUCCESS)
        self.assertEquals(self.workflow.is_successful(), True)

    def test_is_status_queued(self):
        """
        Test is successful if one or more tasks has the status QUEUED
        and the rest doesn't have any status.
        """
        self.update_tasks_status(None)
        self.update_tasks_status(
            Action.QUEUED, self.tasks[0])
        self.assertEquals(self.workflow.is_queued(), True)

    def create_task_types(self):
        for task in self.tasks:
            w_models.TaskType(name=task).save()

    def create_workflow_template(self):
        w_models.WorkflowTemplate(
            code=w_models.WorkflowTemplate.DEFAULT_TEMPLATE_CODE).save()

    def add_tasks_to_workflow_template(self):
        for task in self.tasks:
            w_models.WorkflowTemplateTask(
                code=w_models.TaskType.objects.get(name=task),
                workflow_template=self.template).save()

    def create_workflow(self):
        scenario_code = 3828
        workflow = w_models.Workflow(code='TEST {0}'.format(scenario_code),
                                     template=self.template,
                                     scenario=scenario_code)
        workflow.save()
        return workflow

    def create_tasks(self):
        template_tasks = self.template.workflowtemplatetask_set.all()
        for template_task in template_tasks:
            w_models.WorkflowTask(
                workflow=self.workflow,
                code=w_models.TaskType.objects.get(name=template_task)).save()

    def update_tasks_status(self, status, task_code=None):
        if task_code is None:
            self.workflow.workflowtask_set.update(status=status)
        else:
            tasks = self.workflow.workflowtask_set.filter(
                code=w_models.TaskType.objects.get(name=task_code))
            tasks.update(status=status)


class MockChannel(object):

    def basic_publish(self, exchange, routing_key, body, properties):
        pass


class MockMethod(object):

    def __init__(self, exchange, routing_key):
        self.exchange = exchange
        self.routing_key = routing_key


class ActionTaskTest(TestCase):

    def setUp(self):
        self.mock_channel = MockChannel()
        self.mock_method = MockMethod("", "")
        self.task_code = 120
        self.worker_nr = 1

    def test_requeue_failed_message(self):
        """
        Test requeueing of failed tasks.
        """
        action_task = ActionTask(self.task_code, self.worker_nr)
        action_task.properties = None
        action_task.body = self.create_body(0, 0)
        action_task.requeue_failed_message(self.mock_channel, self.mock_method)

        action_task.body = self.create_body(1, 2)
        action_task.requeue_failed_message(self.mock_channel, self.mock_method)

        action_task.body = {}
        action_task.requeue_failed_message(self.mock_channel, self.mock_method)

    def test_status_task(self):
        """
        """
        action_task = ActionTask(self.task_code, self.worker_nr)
        self.assertEqual(True, action_task.status_task(True))
        self.assertEqual(True, action_task.status_task((True,)))
        self.assertEqual(False, action_task.status_task(None))

    def create_body(self, failures, failures_tmp):
        body = Body().body
        body[Body.MAX_FAILURES_TMP] = {self.task_code: failures_tmp}
        body[Body.MAX_FAILURES] = {self.task_code: failures}
        return body
