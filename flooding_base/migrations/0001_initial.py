# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Configuration'
        db.create_table('base_configuration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('datasourcetype', self.gf('django.db.models.fields.IntegerField')()),
            ('coords_w', self.gf('django.db.models.fields.FloatField')(default=3.289)),
            ('coords_e', self.gf('django.db.models.fields.FloatField')(default=7.314)),
            ('coords_s', self.gf('django.db.models.fields.FloatField')(default=50.765)),
            ('coords_n', self.gf('django.db.models.fields.FloatField')(default=53.471)),
        ))
        db.send_create_signal('flooding_base', ['Configuration'])

        # Adding model 'DataSourceEI'
        db.create_table('base_datasourceei', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('configuration', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flooding_base.Configuration'], unique=True)),
            ('connectorurl', self.gf('django.db.models.fields.CharField')(default='http://127.0.0.1:8080/Jdbc2Ei/test', max_length=200)),
            ('databaseurl', self.gf('django.db.models.fields.CharField')(default='jdbc:vjdbc:rmi://127.0.0.1:2000/VJdbc,FewsDataStore', max_length=200)),
            ('databaseurltagname', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('usecustomfilterresponse', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('customfilterresponse', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('flooding_base', ['DataSourceEI'])

        # Adding model 'DataSourceDummy'
        db.create_table('base_datasourcedummy', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('configuration', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flooding_base.Configuration'], unique=True)),
        ))
        db.send_create_signal('flooding_base', ['DataSourceDummy'])

        # Adding model 'Application'
        db.create_table('base_application', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('flooding_base', ['Application'])

        # Adding model 'SubApplication'
        db.create_table('base_subapplication', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('application', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_base.Application'])),
            ('index', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_base', ['SubApplication'])

        # Adding model 'GroupConfigurationPermission'
        db.create_table('base_groupconfigurationpermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('configuration', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_base.Configuration'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
            ('permission', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('flooding_base', ['GroupConfigurationPermission'])

        # Adding model 'Setting'
        db.create_table('base_setting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('remarks', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('flooding_base', ['Setting'])

        # Adding model 'Map'
        db.create_table('base_map', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('remarks', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('layers', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('transparent', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('is_base_layer', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('tiled', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('srs', self.gf('django.db.models.fields.CharField')(default='EPSG:900913', max_length=50)),
        ))
        db.send_create_signal('flooding_base', ['Map'])

        # Adding model 'Site'
        db.create_table('base_site', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('starter_application', self.gf('django.db.models.fields.related.ForeignKey')(related_name='starter_application', to=orm['flooding_base.SubApplication'])),
            ('favicon_image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('logo_image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('topbar_image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('coords_w', self.gf('django.db.models.fields.FloatField')(default=3.289)),
            ('coords_e', self.gf('django.db.models.fields.FloatField')(default=7.314)),
            ('coords_s', self.gf('django.db.models.fields.FloatField')(default=50.765)),
            ('coords_n', self.gf('django.db.models.fields.FloatField')(default=53.471)),
        ))
        db.send_create_signal('flooding_base', ['Site'])

        # Adding M2M table for field configurations on 'Site'
        db.create_table('base_site_configurations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('site', models.ForeignKey(orm['flooding_base.site'], null=False)),
            ('configuration', models.ForeignKey(orm['flooding_base.configuration'], null=False))
        ))
        db.create_unique('base_site_configurations', ['site_id', 'configuration_id'])

        # Adding M2M table for field maps on 'Site'
        db.create_table('base_site_maps', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('site', models.ForeignKey(orm['flooding_base.site'], null=False)),
            ('map', models.ForeignKey(orm['flooding_base.map'], null=False))
        ))
        db.create_unique('base_site_maps', ['site_id', 'map_id'])

        # Adding M2M table for field subapplications on 'Site'
        db.create_table('base_site_subapplications', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('site', models.ForeignKey(orm['flooding_base.site'], null=False)),
            ('subapplication', models.ForeignKey(orm['flooding_base.subapplication'], null=False))
        ))
        db.create_unique('base_site_subapplications', ['site_id', 'subapplication_id'])


    def backwards(self, orm):
        # Deleting model 'Configuration'
        db.delete_table('base_configuration')

        # Deleting model 'DataSourceEI'
        db.delete_table('base_datasourceei')

        # Deleting model 'DataSourceDummy'
        db.delete_table('base_datasourcedummy')

        # Deleting model 'Application'
        db.delete_table('base_application')

        # Deleting model 'SubApplication'
        db.delete_table('base_subapplication')

        # Deleting model 'GroupConfigurationPermission'
        db.delete_table('base_groupconfigurationpermission')

        # Deleting model 'Setting'
        db.delete_table('base_setting')

        # Deleting model 'Map'
        db.delete_table('base_map')

        # Deleting model 'Site'
        db.delete_table('base_site')

        # Removing M2M table for field configurations on 'Site'
        db.delete_table('base_site_configurations')

        # Removing M2M table for field maps on 'Site'
        db.delete_table('base_site_maps')

        # Removing M2M table for field subapplications on 'Site'
        db.delete_table('base_site_subapplications')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'flooding_base.application': {
            'Meta': {'object_name': 'Application', 'db_table': "'base_application'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_base.configuration': {
            'Meta': {'object_name': 'Configuration', 'db_table': "'base_configuration'"},
            'coords_e': ('django.db.models.fields.FloatField', [], {'default': '7.314'}),
            'coords_n': ('django.db.models.fields.FloatField', [], {'default': '53.471'}),
            'coords_s': ('django.db.models.fields.FloatField', [], {'default': '50.765'}),
            'coords_w': ('django.db.models.fields.FloatField', [], {'default': '3.289'}),
            'datasourcetype': ('django.db.models.fields.IntegerField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'through': "orm['flooding_base.GroupConfigurationPermission']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_base.datasourcedummy': {
            'Meta': {'object_name': 'DataSourceDummy', 'db_table': "'base_datasourcedummy'"},
            'configuration': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flooding_base.Configuration']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'flooding_base.datasourceei': {
            'Meta': {'object_name': 'DataSourceEI', 'db_table': "'base_datasourceei'"},
            'configuration': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flooding_base.Configuration']", 'unique': 'True'}),
            'connectorurl': ('django.db.models.fields.CharField', [], {'default': "'http://127.0.0.1:8080/Jdbc2Ei/test'", 'max_length': '200'}),
            'customfilterresponse': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'databaseurl': ('django.db.models.fields.CharField', [], {'default': "'jdbc:vjdbc:rmi://127.0.0.1:2000/VJdbc,FewsDataStore'", 'max_length': '200'}),
            'databaseurltagname': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'usecustomfilterresponse': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'flooding_base.groupconfigurationpermission': {
            'Meta': {'object_name': 'GroupConfigurationPermission', 'db_table': "'base_groupconfigurationpermission'"},
            'configuration': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_base.Configuration']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'flooding_base.map': {
            'Meta': {'object_name': 'Map', 'db_table': "'base_map'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_base_layer': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'layers': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'srs': ('django.db.models.fields.CharField', [], {'default': "'EPSG:900913'", 'max_length': '50'}),
            'tiled': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'transparent': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_base.setting': {
            'Meta': {'object_name': 'Setting', 'db_table': "'base_setting'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_base.site': {
            'Meta': {'object_name': 'Site', 'db_table': "'base_site'"},
            'configurations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['flooding_base.Configuration']", 'null': 'True', 'blank': 'True'}),
            'coords_e': ('django.db.models.fields.FloatField', [], {'default': '7.314'}),
            'coords_n': ('django.db.models.fields.FloatField', [], {'default': '53.471'}),
            'coords_s': ('django.db.models.fields.FloatField', [], {'default': '50.765'}),
            'coords_w': ('django.db.models.fields.FloatField', [], {'default': '3.289'}),
            'favicon_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'maps': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['flooding_base.Map']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'starter_application': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'starter_application'", 'to': "orm['flooding_base.SubApplication']"}),
            'subapplications': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_base.SubApplication']", 'symmetrical': 'False'}),
            'topbar_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'flooding_base.subapplication': {
            'Meta': {'ordering': "('application', 'index')", 'object_name': 'SubApplication', 'db_table': "'base_subapplication'"},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_base.Application']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['flooding_base']