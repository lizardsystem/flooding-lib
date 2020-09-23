# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Animation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('firstnr', models.IntegerField()),
                ('lastnr', models.IntegerField()),
                ('startnr', models.IntegerField(blank=True)),
                ('delta_timestep', models.FloatField()),
            ],
            options={
                'db_table': 'presentation_animation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Classified',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('firstnr', models.IntegerField()),
                ('lastnr', models.IntegerField()),
            ],
            options={
                'db_table': 'presentation_classified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ClassifiedNr',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nr', models.IntegerField()),
                ('boundary', models.FloatField()),
                ('classes', models.ForeignKey(to='flooding_presentation.Classified')),
            ],
            options={
                'db_table': 'presentation_classifiednr',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomIndicator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'presentation_customindicator',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Derivative',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('combine_on', models.IntegerField(choices=[(1, 'timeserie'), (2, 'locations'), (3, 'timeserie_locations'), (4, 'custom_comp_damage_embankments')])),
                ('function_derivative', models.IntegerField(choices=[(1, 'min'), (2, 'max'), (3, 'mean'), (4, 'sum'), (5, 'sum_multiplied_by_dt')])),
            ],
            options={
                'db_table': 'presentation_derivative',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Field',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('friendlyname', models.CharField(max_length=50)),
                ('source_type', models.IntegerField(choices=[(1, 'geo_source_col'), (2, 'value_source_param')])),
                ('is_main_value_field', models.BooleanField(default=False)),
                ('name_in_source', models.CharField(max_length=80)),
                ('field_type', models.IntegerField(choices=[(1, 'float'), (2, 'integer'), (3, 'interval'), (4, 'datetime'), (5, 'string'), (6, 'choice')])),
            ],
            options={
                'db_table': 'presentation_field',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('friendlyname', models.CharField(max_length=50)),
                ('fieldname_source', models.CharField(max_length=80)),
                ('field', models.ForeignKey(to='flooding_presentation.Field')),
            ],
            options={
                'db_table': 'presentation_fieldchoice',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PresentationGrid',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extent', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, verbose_name=b'Result Border', blank=True)),
                ('bbox_orignal_srid', models.IntegerField(null=True, blank=True)),
                ('rownr', models.IntegerField()),
                ('colnr', models.IntegerField()),
                ('gridsize', models.IntegerField()),
            ],
            options={
                'db_table': 'presentation_presentationgrid',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PresentationLayer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source_application', models.IntegerField(default=1, choices=[(1, 'None'), (2, 'Flooding')])),
                ('value', models.FloatField(null=True, blank=True)),
            ],
            options={
                'db_table': 'presentation_presentationlayer',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PresentationNoGeom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('presentationlayer', models.OneToOneField(to='flooding_presentation.PresentationLayer')),
            ],
            options={
                'db_table': 'presentation_presentationnogeom',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PresentationShape',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'presentation_presentationshape',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PresentationSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.IntegerField(choices=[(1, 'value_table'), (2, 'shapefile'), (3, 'hisfile'), (4, 'zipped_hisfile'), (5, 'png_file'), (6, 'serie_png_files'), (7, 'png_file_indexed_pallette'), (8, 'serie_png_file_indexed_pallette')])),
                ('file_location', models.CharField(max_length=150, null=True, blank=True)),
                ('t_source', models.DateTimeField(null=True, blank=True)),
                ('t_origin', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'presentation_presentationsource',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PresentationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('code', models.CharField(max_length=35)),
                ('name', models.CharField(max_length=35)),
                ('object', models.CharField(max_length=35)),
                ('parameter', models.CharField(max_length=35)),
                ('remarks', models.TextField(blank=True)),
                ('order_index', models.IntegerField()),
                ('absolute', models.BooleanField(default=False)),
                ('geo_type', models.IntegerField(choices=[(1, 'grid'), (2, 'polygon'), (3, 'line'), (4, 'point'), (5, 'no geom'), (6, 'pyramid')])),
                ('value_type', models.IntegerField(choices=[(1, 'only_geometry'), (2, 'value'), (3, 'time_serie'), (4, 'class_serie')])),
                ('unit', models.CharField(max_length=20)),
                ('class_unit', models.CharField(max_length=20, blank=True)),
                ('value_source_parameter_name', models.CharField(max_length=30, blank=True)),
                ('value_source_id_prefix', models.CharField(max_length=30, blank=True)),
                ('generation_geo_source', models.CharField(max_length=30, blank=True)),
                ('generation_geo_source_part', models.CharField(max_length=30, blank=True)),
                ('geo_source_filter', models.CharField(max_length=80, blank=True)),
                ('permission_level', models.IntegerField(default=1)),
                ('default_legend_id', models.IntegerField()),
                ('default_maxvalue', models.FloatField(null=True, blank=True)),
                ('custom_indicator', models.ForeignKey(blank=True, to='flooding_presentation.CustomIndicator', null=True)),
            ],
            options={
                'db_table': 'presentation_presentationtype',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PresentationValueTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('location_id', models.CharField(max_length=20, null=True, blank=True)),
                ('parameter', models.CharField(max_length=20, null=True, blank=True)),
                ('time', models.FloatField(null=True, blank=True)),
                ('value', models.FloatField()),
                ('presentationsource', models.ForeignKey(to='flooding_presentation.PresentationSource', null=True)),
            ],
            options={
                'db_table': 'presentation_presentationvaluetable',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourceLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('link_id', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=50)),
                ('presentationsource', models.ManyToManyField(to='flooding_presentation.PresentationSource')),
            ],
            options={
                'db_table': 'presentation_sourcelink',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourceLinkType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'presentation_sourcelinktype',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SupportLayers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('presentationtype', models.OneToOneField(related_name=b'supported_presentationtype', to='flooding_presentation.PresentationType')),
                ('supportive_presentationtype', models.ManyToManyField(related_name=b'supportive_presentationtypes', to='flooding_presentation.PresentationType')),
            ],
            options={
                'db_table': 'presentation_supportlayers',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='sourcelink',
            name='sourcelinktype',
            field=models.ForeignKey(to='flooding_presentation.SourceLinkType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='presentationshape',
            name='geo_source',
            field=models.ForeignKey(related_name=b'geo_source', blank=True, to='flooding_presentation.PresentationSource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='presentationshape',
            name='presentationlayer',
            field=models.OneToOneField(to='flooding_presentation.PresentationLayer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='presentationshape',
            name='value_source',
            field=models.ForeignKey(related_name=b'value_source', blank=True, to='flooding_presentation.PresentationSource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='presentationnogeom',
            name='value_source',
            field=models.ForeignKey(blank=True, to='flooding_presentation.PresentationSource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='presentationlayer',
            name='presentationtype',
            field=models.ForeignKey(to='flooding_presentation.PresentationType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='presentationgrid',
            name='location_netcdf_file',
            field=models.ForeignKey(related_name=b'location_netcdf_file', blank=True, to='flooding_presentation.PresentationSource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='presentationgrid',
            name='png_default_legend',
            field=models.ForeignKey(related_name=b'png_default_legend', blank=True, to='flooding_presentation.PresentationSource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='presentationgrid',
            name='png_indexed_palette',
            field=models.ForeignKey(related_name=b'png_indexed_palette', blank=True, to='flooding_presentation.PresentationSource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='presentationgrid',
            name='presentationlayer',
            field=models.OneToOneField(to='flooding_presentation.PresentationLayer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='field',
            name='presentationtype',
            field=models.ForeignKey(to='flooding_presentation.PresentationType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='derivative',
            name='dest_presentationtype',
            field=models.ForeignKey(to='flooding_presentation.PresentationType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='derivative',
            name='source_presentationtype',
            field=models.ForeignKey(related_name=b'source_presentationtype', to='flooding_presentation.PresentationType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='classified',
            name='presentationlayer',
            field=models.OneToOneField(to='flooding_presentation.PresentationLayer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='animation',
            name='presentationlayer',
            field=models.OneToOneField(to='flooding_presentation.PresentationLayer'),
            preserve_default=True,
        ),
    ]
