# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('flooding_lib', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExportRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('export_type', models.IntegerField(default=10, choices=[(10, 'Water depth map')])),
                ('export_max_waterdepth', models.BooleanField(default=True, verbose_name='The maximal waterdepth')),
                ('export_max_flowvelocity', models.BooleanField(default=True, verbose_name='The maximal flowvelocity')),
                ('export_possibly_flooded', models.BooleanField(default=True, verbose_name='The flooded area')),
                ('export_arrival_times', models.BooleanField(default=True, verbose_name='The arrival times')),
                ('export_period_of_increasing_waterlevel', models.BooleanField(default=True, verbose_name='The period of increasing waterlevel')),
                ('export_inundation_sources', models.BooleanField(default=True, verbose_name='The sources of inundation')),
                ('export_scenario_data', models.BooleanField(default=False, verbose_name='All scenario data')),
                ('creation_date', models.DateTimeField(null=True, verbose_name='Creation date', blank=True)),
                ('run_date', models.DateTimeField(null=True, verbose_name='Run date', blank=True)),
                ('approved_date', models.DateTimeField(null=True, verbose_name='Approved date', blank=True)),
                ('gridsize', models.PositiveIntegerField(default=50, verbose_name='Gridsize')),
                ('state', models.IntegerField(default=10, choices=[(10, 'Waiting'), (50, 'Ready')])),
                ('public', models.BooleanField(default=True, verbose_name='Publicly visible')),
                ('archived', models.BooleanField(default=False, verbose_name='Moved to the archive')),
                ('owner', models.ForeignKey(verbose_name='Owner', to=settings.AUTH_USER_MODEL)),
                ('scenarios', models.ManyToManyField(to='flooding_lib.Scenario')),
            ],
            options={
                'ordering': ['creation_date'],
                'verbose_name': 'Export run',
                'verbose_name_plural': 'Export runs',
                'permissions': (('can_create', 'Can create export'), ('can_download', 'Can download exportresult')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('file_basename', models.CharField(max_length=100)),
                ('area', models.IntegerField(choices=[(10, 'Diked area'), (20, 'Province'), (30, 'Country')])),
                ('export_run', models.ForeignKey(to='exporttool.ExportRun')),
            ],
            options={
                'verbose_name': 'Result',
                'verbose_name_plural': 'Results',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(unique=True, max_length=200)),
                ('value', models.CharField(max_length=200)),
                ('remarks', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
