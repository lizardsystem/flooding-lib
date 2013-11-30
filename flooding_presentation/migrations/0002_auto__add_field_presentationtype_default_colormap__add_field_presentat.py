# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'PresentationType.default_colormap'
        db.add_column('presentation_presentationtype', 'default_colormap', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pyramids.Colormap'], null=True, blank=True), keep_default=False)

        # Adding field 'PresentationType.default_maxvalue'
        db.add_column('presentation_presentationtype', 'default_maxvalue', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'PresentationType.default_colormap'
        db.delete_column('presentation_presentationtype', 'default_colormap_id')

        # Deleting field 'PresentationType.default_maxvalue'
        db.delete_column('presentation_presentationtype', 'default_maxvalue')


    models = {
        'flooding_presentation.animation': {
            'Meta': {'object_name': 'Animation', 'db_table': "'presentation_animation'"},
            'delta_timestep': ('django.db.models.fields.FloatField', [], {}),
            'firstnr': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastnr': ('django.db.models.fields.IntegerField', [], {}),
            'presentationlayer': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flooding_presentation.PresentationLayer']", 'unique': 'True'}),
            'startnr': ('django.db.models.fields.IntegerField', [], {'blank': 'True'})
        },
        'flooding_presentation.classified': {
            'Meta': {'object_name': 'Classified', 'db_table': "'presentation_classified'"},
            'firstnr': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastnr': ('django.db.models.fields.IntegerField', [], {}),
            'presentationlayer': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flooding_presentation.PresentationLayer']", 'unique': 'True'})
        },
        'flooding_presentation.classifiednr': {
            'Meta': {'object_name': 'ClassifiedNr', 'db_table': "'presentation_classifiednr'"},
            'boundary': ('django.db.models.fields.FloatField', [], {}),
            'classes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.Classified']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nr': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_presentation.customindicator': {
            'Meta': {'object_name': 'CustomIndicator', 'db_table': "'presentation_customindicator'"},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_presentation.derivative': {
            'Meta': {'object_name': 'Derivative', 'db_table': "'presentation_derivative'"},
            'combine_on': ('django.db.models.fields.IntegerField', [], {}),
            'dest_presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.PresentationType']"}),
            'function_derivative': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source_presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'source_presentationtype'", 'to': "orm['flooding_presentation.PresentationType']"})
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
        'flooding_presentation.fieldchoice': {
            'Meta': {'object_name': 'FieldChoice', 'db_table': "'presentation_fieldchoice'"},
            'field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.Field']"}),
            'fieldname_source': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'friendlyname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'flooding_presentation.presentationgrid': {
            'Meta': {'object_name': 'PresentationGrid', 'db_table': "'presentation_presentationgrid'"},
            'bbox_orignal_srid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'colnr': ('django.db.models.fields.IntegerField', [], {}),
            'extent': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True', 'blank': 'True'}),
            'gridsize': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_netcdf_file': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'location_netcdf_file'", 'null': 'True', 'to': "orm['flooding_presentation.PresentationSource']"}),
            'png_default_legend': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'png_default_legend'", 'null': 'True', 'to': "orm['flooding_presentation.PresentationSource']"}),
            'png_indexed_palette': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'png_indexed_palette'", 'null': 'True', 'to': "orm['flooding_presentation.PresentationSource']"}),
            'presentationlayer': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flooding_presentation.PresentationLayer']", 'unique': 'True'}),
            'rownr': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_presentation.presentationlayer': {
            'Meta': {'object_name': 'PresentationLayer', 'db_table': "'presentation_presentationlayer'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.PresentationType']"}),
            'source_application': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'flooding_presentation.presentationnogeom': {
            'Meta': {'object_name': 'PresentationNoGeom', 'db_table': "'presentation_presentationnogeom'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationlayer': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flooding_presentation.PresentationLayer']", 'unique': 'True'}),
            'value_source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.PresentationSource']", 'null': 'True', 'blank': 'True'})
        },
        'flooding_presentation.presentationshape': {
            'Meta': {'object_name': 'PresentationShape', 'db_table': "'presentation_presentationshape'"},
            'geo_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'geo_source'", 'null': 'True', 'to': "orm['flooding_presentation.PresentationSource']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationlayer': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flooding_presentation.PresentationLayer']", 'unique': 'True'}),
            'value_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'value_source'", 'null': 'True', 'to': "orm['flooding_presentation.PresentationSource']"})
        },
        'flooding_presentation.presentationsource': {
            'Meta': {'object_name': 'PresentationSource', 'db_table': "'presentation_presentationsource'"},
            'file_location': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            't_origin': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            't_source': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_presentation.presentationtype': {
            'Meta': {'object_name': 'PresentationType', 'db_table': "'presentation_presentationtype'"},
            'absolute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'class_unit': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'custom_indicator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.CustomIndicator']", 'null': 'True', 'blank': 'True'}),
            'default_colormap': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pyramids.Colormap']", 'null': 'True', 'blank': 'True'}),
            'default_legend_id': ('django.db.models.fields.IntegerField', [], {}),
            'default_maxvalue': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
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
        'flooding_presentation.presentationvaluetable': {
            'Meta': {'object_name': 'PresentationValueTable', 'db_table': "'presentation_presentationvaluetable'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'presentationsource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.PresentationSource']", 'null': 'True'}),
            'time': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'flooding_presentation.sourcelink': {
            'Meta': {'object_name': 'SourceLink', 'db_table': "'presentation_sourcelink'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'presentationsource': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_presentation.PresentationSource']", 'symmetrical': 'False'}),
            'sourcelinktype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.SourceLinkType']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'flooding_presentation.sourcelinktype': {
            'Meta': {'object_name': 'SourceLinkType', 'db_table': "'presentation_sourcelinktype'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'flooding_presentation.supportlayers': {
            'Meta': {'object_name': 'SupportLayers', 'db_table': "'presentation_supportlayers'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationtype': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'supported_presentationtype'", 'unique': 'True', 'to': "orm['flooding_presentation.PresentationType']"}),
            'supportive_presentationtype': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'supportive_presentationtypes'", 'symmetrical': 'False', 'to': "orm['flooding_presentation.PresentationType']"})
        },
        'pyramids.colormap': {
            'Meta': {'ordering': "(u'description',)", 'object_name': 'Colormap'},
            'description': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'matplotlib_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        }
    }

    complete_apps = ['flooding_presentation']
