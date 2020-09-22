# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import flooding_lib.tools.importtool.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('flooding_lib', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('approvaltool', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupImport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('table', models.FileField(upload_to=flooding_lib.tools.importtool.models.get_groupimport_table_path, null=True, verbose_name='Excel table (.xls)', blank=True)),
                ('results', models.FileField(upload_to=flooding_lib.tools.importtool.models.get_groupimport_result_path, null=True, verbose_name='Results (zipfile)', blank=True)),
                ('upload_successful', models.NullBooleanField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImportScenario',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('state', models.IntegerField(default=10, choices=[(0, 'None'), (10, 'Waiting for validation'), (20, 'Action required'), (30, 'Approved for import'), (40, 'Disapproved for import'), (50, 'Imported')])),
                ('action_taker', models.CharField(max_length=200, null=True, blank=True)),
                ('validation_remarks', models.TextField(default=b'-', null=True, blank=True)),
                ('approvalobject', models.OneToOneField(null=True, blank=True, to='approvaltool.ApprovalObject')),
                ('breach', models.ForeignKey(blank=True, to='flooding_lib.Breach', null=True)),
                ('groupimport', models.ForeignKey(blank=True, to='importtool.GroupImport', null=True)),
                ('owner', models.ForeignKey(help_text='The owner of the scenario.', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(blank=True, to='flooding_lib.Project', null=True)),
                ('region', models.ForeignKey(blank=True, to='flooding_lib.Region', null=True)),
                ('scenario', models.OneToOneField(null=True, blank=True, to='flooding_lib.Scenario')),
            ],
            options={
                'verbose_name': 'Import scenario',
                'verbose_name_plural': 'Import scenarios',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImportScenarioInputField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.IntegerField(default=20, choices=[(20, 'Waiting'), (30, 'Approved'), (40, 'Disapproved')])),
                ('validation_remarks', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Import scenario input field',
                'verbose_name_plural': 'Import scenarios input fields',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FloatValue',
            fields=[
                ('importscenario_inputfield', models.OneToOneField(primary_key=True, serialize=False, to='importtool.ImportScenarioInputField')),
                ('value', models.FloatField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileValue',
            fields=[
                ('importscenario_inputfield', models.OneToOneField(primary_key=True, serialize=False, to='importtool.ImportScenarioInputField')),
                ('value', models.FileField(null=True, upload_to=flooding_lib.tools.importtool.models.get_import_upload_files_path, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InputField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('header', models.IntegerField(default=80, choices=[(10, 'Scenario'), (20, 'Meta'), (30, 'Location'), (40, 'Breach'), (50, 'External Water'), (70, 'Model'), (80, 'Remaining'), (90, 'Files')])),
                ('position', models.IntegerField(default=0, help_text='The higher the sooner in row')),
                ('import_table_field', models.CharField(help_text='Name of col. in import csv-file', max_length=100)),
                ('destination_table', models.CharField(help_text='Name of table in flooding database', max_length=100)),
                ('destination_field', models.CharField(help_text='Name of field in flooding database table', max_length=100)),
                ('destination_filename', models.CharField(help_text='Name of imported files (match with resulttypes). Use #### for numbers', max_length=100, null=True, blank=True)),
                ('type', models.IntegerField(choices=[(10, 'Integer'), (20, 'Float'), (30, 'String'), (40, 'Text'), (60, 'Interval (D d HH:MM)'), (50, 'Date'), (70, 'File'), (80, 'Select'), (90, 'Boolean (True or False)')])),
                ('options', models.TextField(blank=True)),
                ('visibility_dependency_value', models.TextField(blank=True)),
                ('excel_hint', models.CharField(help_text='help text shown in excel file', max_length=200, blank=True)),
                ('hover_text', models.CharField(help_text='help text shown when hovering over field', max_length=200, blank=True)),
                ('hint_text', models.CharField(help_text='help text shown behind field', max_length=200, blank=True)),
                ('required', models.BooleanField(default=False)),
                ('visibility_dependency_field', models.ForeignKey(blank=True, to='importtool.InputField', null=True)),
            ],
            options={
                'ordering': ['header'],
                'verbose_name': 'Import scenario fields',
                'verbose_name_plural': 'Import scenarios fields',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IntegerValue',
            fields=[
                ('importscenario_inputfield', models.OneToOneField(primary_key=True, serialize=False, to='importtool.ImportScenarioInputField')),
                ('value', models.IntegerField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RORKering',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, null=True, verbose_name='Title', blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Uploaded At')),
                ('file_name', models.CharField(max_length=100, verbose_name='File name')),
                ('status', models.CharField(default='10', max_length=20, verbose_name='Status', choices=[('20', 'applied'), ('10', 'not applied')])),
                ('type_kering', models.CharField(max_length=20, verbose_name='Type', choices=[('10', 'primary kering'), ('20', 'regional kering'), ('30', 'waters')])),
                ('description', models.TextField(null=True, verbose_name='Description', blank=True)),
                ('owner', models.ForeignKey(verbose_name='Owner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StringValue',
            fields=[
                ('importscenario_inputfield', models.OneToOneField(primary_key=True, serialize=False, to='importtool.ImportScenarioInputField')),
                ('value', models.CharField(max_length=200, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextValue',
            fields=[
                ('importscenario_inputfield', models.OneToOneField(primary_key=True, serialize=False, to='importtool.ImportScenarioInputField')),
                ('value', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='importscenarioinputfield',
            name='importscenario',
            field=models.ForeignKey(to='importtool.ImportScenario', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='importscenarioinputfield',
            name='inputfield',
            field=models.ForeignKey(to='importtool.InputField', null=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='BooleanValue',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('importtool.integervalue',),
        ),
        migrations.CreateModel(
            name='DateValue',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('importtool.stringvalue',),
        ),
        migrations.CreateModel(
            name='IntervalValue',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('importtool.floatvalue',),
        ),
        migrations.CreateModel(
            name='SelectValue',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('importtool.integervalue',),
        ),
    ]
