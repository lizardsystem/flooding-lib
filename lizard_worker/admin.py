from lizard_worker.models import Workflow
from lizard_worker.models import Worker
from lizard_worker.models import Logging
from lizard_worker.models import WorkflowTask
from lizard_worker.models import WorkflowTemplate
from lizard_worker.models import WorkflowTemplateTask
from lizard_worker.models import TaskType

from django.contrib import admin


class WorkflowInline(admin.TabularInline):
    model = Workflow
    extra = 0
    inlines = [WorkflowTask]


class TaskInline(admin.TabularInline):
    model = WorkflowTask
    extra = 0


class LoggingInline(admin.TabularInline):
    model = Logging
    extra = 0


class WorkerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'worker_nr',
        'status',
        'time',
        'node',
        'queue_code',)

    list_filter = ('queue_code', 'node',)


class LoggingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'workflow',
        'task',
        'time',
        'message',
        'worker',
        'is_heartbeat',)

    list_filter = ('worker', 'workflow', 'task', 'is_heartbeat',)


class WorkflowTemplateTaskInline(admin.TabularInline):
    model = WorkflowTemplateTask
    extra = 0


class WorkflowAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'template',
        'scenario',
        'tstart',
        'tfinished',)

    list_filter = ('scenario',)


class WorkflowTemplateAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,          {'fields': ['code']})
    ]
    inlines = [WorkflowTemplateTaskInline]


admin.site.register(Workflow, WorkflowAdmin)
admin.site.register(WorkflowTask)
admin.site.register(WorkflowTemplateTask)
admin.site.register(TaskType)
admin.site.register(WorkflowTemplate, WorkflowTemplateAdmin)
admin.site.register(Logging, LoggingAdmin)
admin.site.register(Worker, WorkerAdmin)
