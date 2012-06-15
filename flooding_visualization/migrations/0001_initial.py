# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ValueVisualizerMap'
        db.create_table('visualization_valuevisualizermap', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('valuetype', self.gf('django.db.models.fields.IntegerField')()),
            ('interpolation', self.gf('django.db.models.fields.IntegerField')()),
            ('visualizertype', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_visualization', ['ValueVisualizerMap'])

        # Adding model 'ValueVisualizerMapFloatColor'
        db.create_table('visualization_valuevisualizermapfloatcolor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('valuevisualizermap', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('value_in', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('r', self.gf('django.db.models.fields.FloatField')()),
            ('g', self.gf('django.db.models.fields.FloatField')()),
            ('b', self.gf('django.db.models.fields.FloatField')()),
            ('a', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('flooding_visualization', ['ValueVisualizerMapFloatColor'])

        # Adding model 'ValueVisualizerMapFloatSize'
        db.create_table('visualization_valuevisualizermapfloatsize', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('valuevisualizermap', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('value_in', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('x', self.gf('django.db.models.fields.IntegerField')()),
            ('y', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_visualization', ['ValueVisualizerMapFloatSize'])

        # Adding model 'ValueVisualizerMapFloatFloat'
        db.create_table('visualization_valuevisualizermapfloatfloat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('valuevisualizermap', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('value_in', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('value_out', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('flooding_visualization', ['ValueVisualizerMapFloatFloat'])

        # Adding model 'ValueVisualizerMapFloatInteger'
        db.create_table('visualization_valuevisualizermapfloatinteger', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('valuevisualizermap', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('value_in', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('value_out', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_visualization', ['ValueVisualizerMapFloatInteger'])

        # Adding model 'ValueVisualizerMapFloatString'
        db.create_table('visualization_valuevisualizermapfloatstring', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('valuevisualizermap', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('value_in', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('value_out', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('flooding_visualization', ['ValueVisualizerMapFloatString'])

        # Adding model 'ValueVisualizerMapStringString'
        db.create_table('visualization_valuevisualizermapstringstring', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('valuevisualizermap', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('value_in', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('value_out', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('flooding_visualization', ['ValueVisualizerMapStringString'])

        # Adding model 'ShapeDataLegend'
        db.create_table('visualization_shapedatalegend', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('presentationtype', self.gf('django.db.models.fields.related.ForeignKey')(related_name='presentationtype_set', to=orm['flooding_presentation.PresentationType'])),
            ('color', self.gf('django.db.models.fields.related.ForeignKey')(related_name='color_set', to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('color_field', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='color_field_set', null=True, to=orm['flooding_presentation.Field'])),
            ('size', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='size_set', null=True, to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('size_field', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='size_field_set', null=True, to=orm['flooding_presentation.Field'])),
            ('symbol', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='symbol_set', null=True, to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('symbol_field', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='symbol_field_set', null=True, to=orm['flooding_presentation.Field'])),
            ('rotation', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='rotation_set', null=True, to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('rotation_field', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='rotation_field_set', null=True, to=orm['flooding_presentation.Field'])),
            ('shadowheight', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='shadowheight_set', null=True, to=orm['flooding_visualization.ValueVisualizerMap'])),
            ('shadowheight_field', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='shadowheight_field_set', null=True, to=orm['flooding_presentation.Field'])),
        ))
        db.send_create_signal('flooding_visualization', ['ShapeDataLegend'])


    def backwards(self, orm):
        
        # Deleting model 'ValueVisualizerMap'
        db.delete_table('visualization_valuevisualizermap')

        # Deleting model 'ValueVisualizerMapFloatColor'
        db.delete_table('visualization_valuevisualizermapfloatcolor')

        # Deleting model 'ValueVisualizerMapFloatSize'
        db.delete_table('visualization_valuevisualizermapfloatsize')

        # Deleting model 'ValueVisualizerMapFloatFloat'
        db.delete_table('visualization_valuevisualizermapfloatfloat')

        # Deleting model 'ValueVisualizerMapFloatInteger'
        db.delete_table('visualization_valuevisualizermapfloatinteger')

        # Deleting model 'ValueVisualizerMapFloatString'
        db.delete_table('visualization_valuevisualizermapfloatstring')

        # Deleting model 'ValueVisualizerMapStringString'
        db.delete_table('visualization_valuevisualizermapstringstring')

        # Deleting model 'ShapeDataLegend'
        db.delete_table('visualization_shapedatalegend')


    models = {
        'flooding_presentation.customindicator': {
            'Meta': {'object_name': 'CustomIndicator', 'db_table': "'presentation_customindicator'"},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_presentation.field': {
            'Meta': {'object_name': 'Field', 'db_table': "'presentation_field'"},
            'field_type': ('django.db.models.fields.IntegerField', [], {}),
            'friendlyname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_main_value_field': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name_in_source': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.PresentationType']"}),
            'source_type': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_presentation.presentationtype': {
            'Meta': {'object_name': 'PresentationType', 'db_table': "'presentation_presentationtype'"},
            'absolute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'class_unit': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'custom_indicator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.CustomIndicator']", 'null': 'True', 'blank': 'True'}),
            'default_legend_id': ('django.db.models.fields.IntegerField', [], {}),
            'generation_geo_source': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'generation_geo_source_part': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'geo_source_filter': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'geo_type': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'object': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'order_index': ('django.db.models.fields.IntegerField', [], {}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'permission_level': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'value_source_id_prefix': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'value_source_parameter_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'value_type': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_visualization.shapedatalegend': {
            'Meta': {'object_name': 'ShapeDataLegend', 'db_table': "'visualization_shapedatalegend'"},
            'color': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'color_set'", 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'color_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'color_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'presentationtype_set'", 'to': "orm['flooding_presentation.PresentationType']"}),
            'rotation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rotation_set'", 'null': 'True', 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'rotation_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rotation_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"}),
            'shadowheight': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shadowheight_set'", 'null': 'True', 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'shadowheight_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shadowheight_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"}),
            'size': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'size_set'", 'null': 'True', 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'size_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'size_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"}),
            'symbol': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'symbol_set'", 'null': 'True', 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'symbol_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'symbol_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"})
        },
        'flooding_visualization.valuevisualizermap': {
            'Meta': {'object_name': 'ValueVisualizerMap', 'db_table': "'visualization_valuevisualizermap'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interpolation': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'valuetype': ('django.db.models.fields.IntegerField', [], {}),
            'visualizertype': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_visualization.valuevisualizermapfloatcolor': {
            'Meta': {'ordering': "('value_in',)", 'object_name': 'ValueVisualizerMapFloatColor', 'db_table': "'visualization_valuevisualizermapfloatcolor'"},
            'a': ('django.db.models.fields.FloatField', [], {}),
            'b': ('django.db.models.fields.FloatField', [], {}),
            'g': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'r': ('django.db.models.fields.FloatField', [], {}),
            'value_in': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'valuevisualizermap': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_visualization.ValueVisualizerMap']"})
        },
        'flooding_visualization.valuevisualizermapfloatfloat': {
            'Meta': {'object_name': 'ValueVisualizerMapFloatFloat', 'db_table': "'visualization_valuevisualizermapfloatfloat'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_in': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_out': ('django.db.models.fields.FloatField', [], {}),
            'valuevisualizermap': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_visualization.ValueVisualizerMap']"})
        },
        'flooding_visualization.valuevisualizermapfloatinteger': {
            'Meta': {'object_name': 'ValueVisualizerMapFloatInteger', 'db_table': "'visualization_valuevisualizermapfloatinteger'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_in': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_out': ('django.db.models.fields.IntegerField', [], {}),
            'valuevisualizermap': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_visualization.ValueVisualizerMap']"})
        },
        'flooding_visualization.valuevisualizermapfloatsize': {
            'Meta': {'ordering': "('value_in',)", 'object_name': 'ValueVisualizerMapFloatSize', 'db_table': "'visualization_valuevisualizermapfloatsize'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_in': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'valuevisualizermap': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'x': ('django.db.models.fields.IntegerField', [], {}),
            'y': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_visualization.valuevisualizermapfloatstring': {
            'Meta': {'object_name': 'ValueVisualizerMapFloatString', 'db_table': "'visualization_valuevisualizermapfloatstring'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_in': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_out': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'valuevisualizermap': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_visualization.ValueVisualizerMap']"})
        },
        'flooding_visualization.valuevisualizermapstringstring': {
            'Meta': {'object_name': 'ValueVisualizerMapStringString', 'db_table': "'visualization_valuevisualizermapstringstring'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_in': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'value_out': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'valuevisualizermap': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_visualization.ValueVisualizerMap']"})
        }
    }

    complete_apps = ['flooding_visualization']
