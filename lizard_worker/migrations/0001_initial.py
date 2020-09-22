# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Logging',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(null=True, blank=True)),
                ('level', models.IntegerField(blank=True, null=True, choices=[(0, 'DEBUG'), (1, 'INFO'), (2, 'WARNING'), (3, 'ERROR'), (4, 'CRITICAL')])),
                ('message', models.TextField(null=True, blank=True)),
                ('is_heartbeat', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'lizard_worker_logging',
                'get_latest_by': 'time',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ('name',),
                'db_table': 'lizard_worker_tasktype',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Worker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('worker_nr', models.IntegerField(null=True, blank=True)),
                ('status', models.CharField(blank=True, max_length=25, null=True, choices=[('ALIVE', 'ALIVE'), ('DOWN', 'DOWN'), ('BUSY', 'BUSY')])),
                ('time', models.DateTimeField(null=True, blank=True)),
                ('node', models.CharField(max_length=255, null=True, blank=True)),
                ('queue_code', models.CharField(max_length=25, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=100)),
                ('scenario', models.IntegerField(null=True, blank=True)),
                ('scenario_type', models.CharField(max_length=200, null=True, blank=True)),
                ('tcreated', models.DateTimeField(null=True, blank=True)),
                ('tstart', models.DateTimeField(null=True, blank=True)),
                ('tfinished', models.DateTimeField(null=True, blank=True)),
                ('logging_level', models.IntegerField(blank=True, null=True, choices=[(0, 'DEBUG'), (1, 'INFO'), (2, 'WARNING'), (3, 'ERROR'), (4, 'CRITICAL')])),
                ('priority', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'db_table': 'lizard_worker_workflow',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WorkflowTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('max_failures', models.IntegerField(default=0)),
                ('max_duration_minutes', models.IntegerField(default=0)),
                ('tcreated', models.DateTimeField(null=True, blank=True)),
                ('tqueued', models.DateTimeField(null=True, blank=True)),
                ('tstart', models.DateTimeField(null=True, blank=True)),
                ('tfinished', models.DateTimeField(null=True, blank=True)),
                ('successful', models.NullBooleanField()),
                ('status', models.CharField(blank=True, max_length=25, null=True, choices=[('QUEUED', 'QUEUED'), ('STARTED', 'STARTED'), ('SUCCESS', 'SUCCESS'), ('FAILED', 'FAILED')])),
                ('code', models.ForeignKey(to='lizard_worker.TaskType')),
                ('parent_code', models.ForeignKey(related_name=b'workflowtask_parent_task_code', to='lizard_worker.TaskType', help_text=b"Define a task's tree, None = end of the tree.", null=True)),
                ('workflow', models.ForeignKey(to='lizard_worker.Workflow')),
            ],
            options={
                'db_table': 'lizard_worker_workflowtask',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WorkflowTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.IntegerField(unique=True, max_length=30)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
                'db_table': 'lizard_worker_workflowtemplate',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WorkflowTemplateTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('max_failures', models.IntegerField(default=0)),
                ('max_duration_minutes', models.IntegerField(default=0)),
                ('code', models.ForeignKey(to='lizard_worker.TaskType')),
                ('parent_code', models.ForeignKey(related_name=b'parent_task_code', to='lizard_worker.TaskType', help_text=b"Define a task's tree, None = end of the tree.", null=True)),
                ('workflow_template', models.ForeignKey(to='lizard_worker.WorkflowTemplate')),
            ],
            options={
                'db_table': 'lizard_worker_workflowtemplatetask',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='workflow',
            name='template',
            field=models.ForeignKey(blank=True, to='lizard_worker.WorkflowTemplate', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='logging',
            name='task',
            field=models.ForeignKey(blank=True, to='lizard_worker.WorkflowTask', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='logging',
            name='worker',
            field=models.ForeignKey(blank=True, to='lizard_worker.Worker', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='logging',
            name='workflow',
            field=models.ForeignKey(blank=True, to='lizard_worker.Workflow', null=True),
            preserve_default=True,
        ),
    ]
