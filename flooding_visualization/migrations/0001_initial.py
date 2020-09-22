# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flooding_presentation', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShapeDataLegend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'visualization_shapedatalegend',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValueVisualizerMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('valuetype', models.IntegerField(choices=[(1, 'Absolute value'), (2, 'Percentage'), (3, 'Percentile')])),
                ('interpolation', models.IntegerField(choices=[(1, 'No interpolation'), (2, 'Linear interpolation'), (3, 'Linear interpolation degrees')])),
                ('visualizertype', models.IntegerField(choices=[(1, 'float -> color'), (2, 'float -> size'), (3, 'float -> float'), (6, 'float -> integer'), (4, 'float -> string'), (5, 'string -> string')])),
            ],
            options={
                'db_table': 'visualization_valuevisualizermap',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValueVisualizerMapFloatColor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_in', models.FloatField(null=True, blank=True)),
                ('r', models.FloatField()),
                ('g', models.FloatField()),
                ('b', models.FloatField()),
                ('a', models.FloatField()),
                ('valuevisualizermap', models.ForeignKey(to='flooding_visualization.ValueVisualizerMap')),
            ],
            options={
                'ordering': ('value_in',),
                'db_table': 'visualization_valuevisualizermapfloatcolor',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValueVisualizerMapFloatFloat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_in', models.FloatField(null=True, blank=True)),
                ('value_out', models.FloatField()),
                ('valuevisualizermap', models.ForeignKey(to='flooding_visualization.ValueVisualizerMap')),
            ],
            options={
                'db_table': 'visualization_valuevisualizermapfloatfloat',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValueVisualizerMapFloatInteger',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_in', models.FloatField(null=True, blank=True)),
                ('value_out', models.IntegerField()),
                ('valuevisualizermap', models.ForeignKey(to='flooding_visualization.ValueVisualizerMap')),
            ],
            options={
                'db_table': 'visualization_valuevisualizermapfloatinteger',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValueVisualizerMapFloatSize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_in', models.FloatField(null=True, blank=True)),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('valuevisualizermap', models.ForeignKey(to='flooding_visualization.ValueVisualizerMap')),
            ],
            options={
                'ordering': ('value_in',),
                'db_table': 'visualization_valuevisualizermapfloatsize',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValueVisualizerMapFloatString',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_in', models.FloatField(null=True, blank=True)),
                ('value_out', models.CharField(max_length=200)),
                ('valuevisualizermap', models.ForeignKey(to='flooding_visualization.ValueVisualizerMap')),
            ],
            options={
                'db_table': 'visualization_valuevisualizermapfloatstring',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValueVisualizerMapStringString',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_in', models.CharField(max_length=200, null=True, blank=True)),
                ('value_out', models.CharField(max_length=200)),
                ('valuevisualizermap', models.ForeignKey(to='flooding_visualization.ValueVisualizerMap')),
            ],
            options={
                'db_table': 'visualization_valuevisualizermapstringstring',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='color',
            field=models.ForeignKey(related_name=b'color_set', to='flooding_visualization.ValueVisualizerMap'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='color_field',
            field=models.ForeignKey(related_name=b'color_field_set', blank=True, to='flooding_presentation.Field', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='presentationtype',
            field=models.ForeignKey(related_name=b'presentationtype_set', to='flooding_presentation.PresentationType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='rotation',
            field=models.ForeignKey(related_name=b'rotation_set', blank=True, to='flooding_visualization.ValueVisualizerMap', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='rotation_field',
            field=models.ForeignKey(related_name=b'rotation_field_set', blank=True, to='flooding_presentation.Field', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='shadowheight',
            field=models.ForeignKey(related_name=b'shadowheight_set', blank=True, to='flooding_visualization.ValueVisualizerMap', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='shadowheight_field',
            field=models.ForeignKey(related_name=b'shadowheight_field_set', blank=True, to='flooding_presentation.Field', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='size',
            field=models.ForeignKey(related_name=b'size_set', blank=True, to='flooding_visualization.ValueVisualizerMap', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='size_field',
            field=models.ForeignKey(related_name=b'size_field_set', blank=True, to='flooding_presentation.Field', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='symbol',
            field=models.ForeignKey(related_name=b'symbol_set', blank=True, to='flooding_visualization.ValueVisualizerMap', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shapedatalegend',
            name='symbol_field',
            field=models.ForeignKey(related_name=b'symbol_field_set', blank=True, to='flooding_presentation.Field', null=True),
            preserve_default=True,
        ),
    ]
