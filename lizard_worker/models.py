# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import logging
import datetime
from django.db import models
from django.core.urlresolvers import reverse
from lizard_worker.worker.action import Action


LOGGING_LEVELS = (
    (0, u'DEBUG'),
    (1, u'INFO'),
    (2, u'WARNING'),
    (3, u'ERROR'),
    (4, u'CRITICAL'),
)


STATUSES = (
    (Action.QUEUED, Action.QUEUED),
    (Action.STARTED, Action.STARTED),
    (Action.SUCCESS, Action.SUCCESS),
    (Action.FAILED, Action.FAILED),
)


logger = logging.getLogger(__name__)


class WorkflowTemplate(models.Model):
    DEFAULT_TEMPLATE_CODE = 1
    IMPORTED_TEMPLATE_CODE = 2
    THREEDI_TEMPLATE_CODE = 3
    MAP_EXPORT_TEMPLATE_CODE = 4

    code = models.IntegerField(unique=True, max_length=30)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return str(self.code)

    class Meta:
        db_table = 'lizard_worker_workflowtemplate'


class Workflow(models.Model):

    code = models.CharField(max_length=100)
    template = models.ForeignKey(WorkflowTemplate, blank=True, null=True)
    scenario = models.IntegerField(blank=True, null=True)
    scenario_type = models.CharField(max_length=200, blank=True, null=True)
    tcreated = models.DateTimeField(
        blank=True,
        null=True)
    tstart = models.DateTimeField(
        blank=True,
        null=True)
    tfinished = models.DateTimeField(
        blank=True,
        null=True)
    logging_level = models.IntegerField(
        choices=LOGGING_LEVELS,
        blank=True,
        null=True)
    priority = models.IntegerField(
        blank=True,
        null=True)

    def get_tfinished(self):
        tasks = self.workflowtask_set.all()
        status = self.get_status()
        if status in (Action.SUCCESS, Action.FAILED):
            return tasks.latest('tfinished').tfinished
        else:
            return None

    def get_status(self):
        if not self.is_published():
            return None
        elif self.is_queued():
            return Action.QUEUED
        elif self.is_successful():
            return Action.SUCCESS
        elif self.is_failed():
            return Action.FAILED
        else:
            return Action.STARTED

    def is_published(self):
        tasks = self.workflowtask_set.all()
        none_status_tasks = tasks.filter(status__isnull=True)
        return (len(tasks) > len(none_status_tasks))

    def is_successful(self):
        tasks = self.workflowtask_set.all()
        success_tasks = self.workflowtask_set.filter(status=Action.SUCCESS)
        return (len(tasks) == len(success_tasks))

    def is_queued(self):
        tasks = self.workflowtask_set.all()
        none_status_tasks = self.workflowtask_set.filter(status=None)
        queued_status_tasks = self.workflowtask_set.filter(
            status=Action.QUEUED)
        return (
            len(none_status_tasks) + len(queued_status_tasks) == len(tasks))

    def is_failed(self):
        statuses = self.workflowtask_set.values_list(
            'status', flat=True)
        return (Action.FAILED in statuses)

    def latest_log(self):
        return self.logging_set.filter(
            is_heartbeat=False).latest('time').message

    def tasks_count(self):
        return self.workflowtask_set.all().count()

    def __unicode__(self):
        return self.code

    def get_absolute_url_scenario(self):
        return reverse('lizard_worker_scenario', kwargs={
                'scenario_id': self.scenario})

    def get_absolute_url_tasks(self):
        return reverse('lizard_worker_workflow_task', kwargs={
                'workflow_id': self.id})

    def get_absolute_url_logging(self):
        return reverse('lizard_worker_workflow_logging', kwargs={
                'workflow_id': self.id,
                'scenario_id': self.scenario})

    def get_absolute_url(self):
        return self.get_absolute_url_scenario()

    class Meta:
        db_table = 'lizard_worker_workflow'


class TaskType(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'lizard_worker_tasktype'
        ordering = ('name',)


class WorkflowTemplateTask(models.Model):
    code = models.ForeignKey(TaskType)
    parent_code = models.ForeignKey(
        TaskType, null=True, related_name='parent_task_code',
        help_text="Define a task's tree, None = end of the tree.")
    max_failures = models.IntegerField(default=0)
    max_duration_minutes = models.IntegerField(default=0)
    workflow_template = models.ForeignKey(WorkflowTemplate)

    def __unicode__(self):
        return self.code.name

    class Meta:
        db_table = 'lizard_worker_workflowtemplatetask'


class WorkflowTask(models.Model):
    workflow = models.ForeignKey(Workflow)
    code = models.ForeignKey(TaskType)
    parent_code = models.ForeignKey(
        TaskType, null=True, related_name='workflowtask_parent_task_code',
        help_text="Define a task's tree, None = end of the tree.")
    max_failures = models.IntegerField(default=0)
    max_duration_minutes = models.IntegerField(default=0)
    tcreated = models.DateTimeField(blank=True, null=True)
    tqueued = models.DateTimeField(blank=True, null=True)
    tstart = models.DateTimeField(blank=True, null=True)
    tfinished = models.DateTimeField(blank=True, null=True)
    successful = models.NullBooleanField(blank=True, null=True)
    status = models.CharField(choices=STATUSES,
                              blank=True, null=True,
                              max_length=25)

    def set_action_time(self, t=None):
        """
        """
        if t is None:
            t = datetime.datetime.today()
        if self.status == Action.QUEUED:
            self.tqueued = t
        elif self.status == Action.STARTED:
            self.tstart = t
        elif self.status in (Action.FAILED, Action.SUCCESS):
            self.tfinished = t
        else:
            logger.warning("Unknown action status {0} at {1}.".format(
                    self.status, t.isoformat()))

    def latest_log(self):
        loggings = self.logging_set.filter(is_heartbeat=False)
        if len(loggings) > 0:
            return loggings.latest('time').message

    def get_absolute_url_logging(self):
        return reverse('lizard_worker_workflow_task_logging', kwargs={
                'task_id': self.id,
                'workflow_id': self.workflow.id,
                'scenario_id': self.workflow.scenario})

    def __unicode__(self):
        return self.code.name

    class Meta:
        db_table = 'lizard_worker_workflowtask'


class Worker(models.Model):

    W_STATUSES = (
        (Action.ALIVE, Action.ALIVE),
        (Action.DOWN, Action.DOWN),
        (Action.BUSY, Action.BUSY),)

    worker_nr = models.IntegerField(blank=True, null=True)
    status = models.CharField(choices=W_STATUSES,
                              blank=True, null=True,
                              max_length=25)
    time = models.DateTimeField(blank=True, null=True)
    node = models.CharField(blank=True, null=True,
                            max_length=255)
    queue_code = models.CharField(blank=True, null=True,
                            max_length=25)


class Logging(models.Model):
    workflow = models.ForeignKey(Workflow, blank=True, null=True)
    task = models.ForeignKey(WorkflowTask, blank=True, null=True)
    time = models.DateTimeField(
        blank=True,
        null=True)
    level = models.IntegerField(
        choices=LOGGING_LEVELS,
        blank=True,
        null=True)
    message = models.TextField(blank=True, null=True)
    worker = models.ForeignKey(Worker, blank=True,
                               null=True)
    is_heartbeat = models.BooleanField(default=False)

    class Meta:
        get_latest_by = "time"
        db_table = 'lizard_worker_logging'
