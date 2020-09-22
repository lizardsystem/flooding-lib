# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(null=True, blank=True)),
                ('type', models.IntegerField(choices=[(1, b'fews'), (2, b'flooding'), (3, b'flow'), (4, b'presentation'), (5, b'gisviewer'), (6, b'mis'), (7, b'nhi')])),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'base_application',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('datasourcetype', models.IntegerField(choices=[(1, 'DataSourceEI'), (2, 'DataSourceDummy')])),
                ('coords_w', models.FloatField(default=3.289)),
                ('coords_e', models.FloatField(default=7.314)),
                ('coords_s', models.FloatField(default=50.765)),
                ('coords_n', models.FloatField(default=53.471)),
            ],
            options={
                'db_table': 'base_configuration',
                'verbose_name': 'Configuration',
                'verbose_name_plural': 'Configurations',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DataSourceDummy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('configuration', models.OneToOneField(to='flooding_base.Configuration')),
            ],
            options={
                'db_table': 'base_datasourcedummy',
                'verbose_name': 'DataSourceDummy',
                'verbose_name_plural': 'Data sources dummy',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DataSourceEI',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('connectorurl', models.CharField(default=b'http://127.0.0.1:8080/Jdbc2Ei/test', max_length=200)),
                ('databaseurl', models.CharField(default=b'jdbc:vjdbc:rmi://127.0.0.1:2000/VJdbc,FewsDataStore', max_length=200)),
                ('databaseurltagname', models.CharField(max_length=200)),
                ('usecustomfilterresponse', models.BooleanField(default=False)),
                ('customfilterresponse', models.TextField(help_text=b"Use a pythonic list of dictionaries. The rootnode has 'parentid': None. i.e. [{'id':'id','name':'name','parentid':None}, {'id':'id2','name':'name2','parentid':'id'}]", null=True, blank=True)),
                ('configuration', models.OneToOneField(to='flooding_base.Configuration')),
            ],
            options={
                'db_table': 'base_datasourceei',
                'verbose_name': 'DataSourceEI',
                'verbose_name_plural': 'Data sources EI',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupConfigurationPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('permission', models.IntegerField(default=1, choices=[(1, 'VIEW')])),
                ('configuration', models.ForeignKey(to='flooding_base.Configuration')),
                ('group', models.ForeignKey(to='auth.Group')),
            ],
            options={
                'db_table': 'base_groupconfigurationpermission',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Map',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('remarks', models.TextField(null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('url', models.CharField(max_length=200)),
                ('layers', models.TextField()),
                ('transparent', models.NullBooleanField(default=None)),
                ('is_base_layer', models.NullBooleanField(default=False)),
                ('tiled', models.NullBooleanField(default=None)),
                ('srs', models.CharField(default=b'EPSG:900913', max_length=50)),
            ],
            options={
                'db_table': 'base_map',
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
                'db_table': 'base_setting',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('favicon_image', models.ImageField(null=True, upload_to=b'user/favicon', blank=True)),
                ('logo_image', models.ImageField(help_text='The size is 280x45 pixels', null=True, upload_to=b'user/logo', blank=True)),
                ('topbar_image', models.ImageField(help_text='The size is 600x70 pixels (width can vary)', null=True, upload_to=b'user/topbar', blank=True)),
                ('coords_w', models.FloatField(default=3.289)),
                ('coords_e', models.FloatField(default=7.314)),
                ('coords_s', models.FloatField(default=50.765)),
                ('coords_n', models.FloatField(default=53.471)),
                ('configurations', models.ManyToManyField(to='flooding_base.Configuration', null=True, blank=True)),
                ('maps', models.ManyToManyField(to='flooding_base.Map', null=True, blank=True)),
            ],
            options={
                'db_table': 'base_site',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubApplication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.IntegerField(default=1)),
                ('type', models.IntegerField(choices=[(11, b'fewsMap'), (12, b'fewsGraph'), (13, b'fewsReport'), (14, b'fewsConfig'), (21, b'floodingResults'), (22, b'floodingNew'), (23, b'floodingTable'), (24, b'floodingImport'), (25, b'floodingExport'), (31, b'flowResults'), (41, b'gisviewerMap'), (51, b'mis_map'), (52, b'mis_table'), (53, b'mis_report'), (54, b'mis_admin'), (55, b'mis_import'), (61, b'nhi_map')])),
                ('application', models.ForeignKey(to='flooding_base.Application')),
            ],
            options={
                'ordering': ('application', 'index'),
                'db_table': 'base_subapplication',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.CharField(max_length=200)),
                ('language', models.CharField(default=b'nl', max_length=5, choices=[(b'nl', b'Nederlands')])),
                ('content', models.TextField(blank=True)),
                ('is_html', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='site',
            name='starter_application',
            field=models.ForeignKey(related_name=b'starter_application', to='flooding_base.SubApplication'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='site',
            name='subapplications',
            field=models.ManyToManyField(to='flooding_base.SubApplication'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='configuration',
            name='groups',
            field=models.ManyToManyField(to='auth.Group', through='flooding_base.GroupConfigurationPermission'),
            preserve_default=True,
        ),
    ]
