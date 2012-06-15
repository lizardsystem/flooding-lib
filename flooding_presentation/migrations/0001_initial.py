# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'PresentationType'
        db.create_table('presentation_presentationtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('object', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('parameter', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('remarks', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('custom_indicator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.CustomIndicator'], null=True, blank=True)),
            ('order_index', self.gf('django.db.models.fields.IntegerField')()),
            ('absolute', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('geo_type', self.gf('django.db.models.fields.IntegerField')()),
            ('value_type', self.gf('django.db.models.fields.IntegerField')()),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('class_unit', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('value_source_parameter_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('value_source_id_prefix', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('generation_geo_source', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('generation_geo_source_part', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('geo_source_filter', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('permission_level', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('default_legend_id', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_presentation', ['PresentationType'])

        # Adding model 'CustomIndicator'
        db.create_table('presentation_customindicator', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('flooding_presentation', ['CustomIndicator'])

        # Adding model 'Derivative'
        db.create_table('presentation_derivative', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source_presentationtype', self.gf('django.db.models.fields.related.ForeignKey')(related_name='source_presentationtype', to=orm['flooding_presentation.PresentationType'])),
            ('dest_presentationtype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.PresentationType'])),
            ('combine_on', self.gf('django.db.models.fields.IntegerField')()),
            ('function_derivative', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_presentation', ['Derivative'])

        # Adding model 'SupportLayers'
        db.create_table('presentation_supportlayers', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('presentationtype', self.gf('django.db.models.fields.related.OneToOneField')(related_name='supported_presentationtype', unique=True, to=orm['flooding_presentation.PresentationType'])),
        ))
        db.send_create_signal('flooding_presentation', ['SupportLayers'])

        # Adding M2M table for field supportive_presentationtype on 'SupportLayers'
        db.create_table('presentation_supportlayers_supportive_presentationtype', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('supportlayers', models.ForeignKey(orm['flooding_presentation.supportlayers'], null=False)),
            ('presentationtype', models.ForeignKey(orm['flooding_presentation.presentationtype'], null=False))
        ))
        db.create_unique('presentation_supportlayers_supportive_presentationtype', ['supportlayers_id', 'presentationtype_id'])

        # Adding model 'Field'
        db.create_table('presentation_field', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('presentationtype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.PresentationType'])),
            ('friendlyname', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('source_type', self.gf('django.db.models.fields.IntegerField')()),
            ('is_main_value_field', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('name_in_source', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('field_type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_presentation', ['Field'])

        # Adding model 'FieldChoice'
        db.create_table('presentation_fieldchoice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('field', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.Field'])),
            ('friendlyname', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('fieldname_source', self.gf('django.db.models.fields.CharField')(max_length=80)),
        ))
        db.send_create_signal('flooding_presentation', ['FieldChoice'])

        # Adding model 'PresentationLayer'
        db.create_table('presentation_presentationlayer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('presentationtype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.PresentationType'])),
            ('source_application', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('flooding_presentation', ['PresentationLayer'])

        # Adding model 'Animation'
        db.create_table('presentation_animation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('presentationlayer', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flooding_presentation.PresentationLayer'], unique=True)),
            ('firstnr', self.gf('django.db.models.fields.IntegerField')()),
            ('lastnr', self.gf('django.db.models.fields.IntegerField')()),
            ('startnr', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('delta_timestep', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('flooding_presentation', ['Animation'])

        # Adding model 'Classified'
        db.create_table('presentation_classified', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('presentationlayer', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flooding_presentation.PresentationLayer'], unique=True)),
            ('firstnr', self.gf('django.db.models.fields.IntegerField')()),
            ('lastnr', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_presentation', ['Classified'])

        # Adding model 'ClassifiedNr'
        db.create_table('presentation_classifiednr', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('classes', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.Classified'])),
            ('nr', self.gf('django.db.models.fields.IntegerField')()),
            ('boundary', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('flooding_presentation', ['ClassifiedNr'])

        # Adding model 'PresentationSource'
        db.create_table('presentation_presentationsource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('file_location', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('t_source', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('t_origin', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('flooding_presentation', ['PresentationSource'])

        # Adding model 'SourceLink'
        db.create_table('presentation_sourcelink', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sourcelinktype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.SourceLinkType'])),
            ('link_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('flooding_presentation', ['SourceLink'])

        # Adding M2M table for field presentationsource on 'SourceLink'
        db.create_table('presentation_sourcelink_presentationsource', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sourcelink', models.ForeignKey(orm['flooding_presentation.sourcelink'], null=False)),
            ('presentationsource', models.ForeignKey(orm['flooding_presentation.presentationsource'], null=False))
        ))
        db.create_unique('presentation_sourcelink_presentationsource', ['sourcelink_id', 'presentationsource_id'])

        # Adding model 'SourceLinkType'
        db.create_table('presentation_sourcelinktype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('flooding_presentation', ['SourceLinkType'])

        # Adding model 'PresentationGrid'
        db.create_table('presentation_presentationgrid', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('presentationlayer', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flooding_presentation.PresentationLayer'], unique=True)),
            ('extent', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(null=True, blank=True)),
            ('bbox_orignal_srid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('rownr', self.gf('django.db.models.fields.IntegerField')()),
            ('colnr', self.gf('django.db.models.fields.IntegerField')()),
            ('gridsize', self.gf('django.db.models.fields.IntegerField')()),
            ('png_indexed_palette', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='png_indexed_palette', null=True, to=orm['flooding_presentation.PresentationSource'])),
            ('png_default_legend', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='png_default_legend', null=True, to=orm['flooding_presentation.PresentationSource'])),
            ('location_netcdf_file', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='location_netcdf_file', null=True, to=orm['flooding_presentation.PresentationSource'])),
        ))
        db.send_create_signal('flooding_presentation', ['PresentationGrid'])

        # Adding model 'PresentationShape'
        db.create_table('presentation_presentationshape', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('presentationlayer', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flooding_presentation.PresentationLayer'], unique=True)),
            ('geo_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='geo_source', null=True, to=orm['flooding_presentation.PresentationSource'])),
            ('value_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='value_source', null=True, to=orm['flooding_presentation.PresentationSource'])),
        ))
        db.send_create_signal('flooding_presentation', ['PresentationShape'])

        # Adding model 'PresentationNoGeom'
        db.create_table('presentation_presentationnogeom', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('presentationlayer', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flooding_presentation.PresentationLayer'], unique=True)),
            ('value_source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.PresentationSource'], null=True, blank=True)),
        ))
        db.send_create_signal('flooding_presentation', ['PresentationNoGeom'])

        # Adding model 'PresentationValueTable'
        db.create_table('presentation_presentationvaluetable', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('presentationsource', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.PresentationSource'], null=True)),
            ('location_id', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('parameter', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('time', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('flooding_presentation', ['PresentationValueTable'])


    def backwards(self, orm):
        
        # Deleting model 'PresentationType'
        db.delete_table('presentation_presentationtype')

        # Deleting model 'CustomIndicator'
        db.delete_table('presentation_customindicator')

        # Deleting model 'Derivative'
        db.delete_table('presentation_derivative')

        # Deleting model 'SupportLayers'
        db.delete_table('presentation_supportlayers')

        # Removing M2M table for field supportive_presentationtype on 'SupportLayers'
        db.delete_table('presentation_supportlayers_supportive_presentationtype')

        # Deleting model 'Field'
        db.delete_table('presentation_field')

        # Deleting model 'FieldChoice'
        db.delete_table('presentation_fieldchoice')

        # Deleting model 'PresentationLayer'
        db.delete_table('presentation_presentationlayer')

        # Deleting model 'Animation'
        db.delete_table('presentation_animation')

        # Deleting model 'Classified'
        db.delete_table('presentation_classified')

        # Deleting model 'ClassifiedNr'
        db.delete_table('presentation_classifiednr')

        # Deleting model 'PresentationSource'
        db.delete_table('presentation_presentationsource')

        # Deleting model 'SourceLink'
        db.delete_table('presentation_sourcelink')

        # Removing M2M table for field presentationsource on 'SourceLink'
        db.delete_table('presentation_sourcelink_presentationsource')

        # Deleting model 'SourceLinkType'
        db.delete_table('presentation_sourcelinktype')

        # Deleting model 'PresentationGrid'
        db.delete_table('presentation_presentationgrid')

        # Deleting model 'PresentationShape'
        db.delete_table('presentation_presentationshape')

        # Deleting model 'PresentationNoGeom'
        db.delete_table('presentation_presentationnogeom')

        # Deleting model 'PresentationValueTable'
        db.delete_table('presentation_presentationvaluetable')


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
        }
    }

    complete_apps = ['flooding_presentation']
