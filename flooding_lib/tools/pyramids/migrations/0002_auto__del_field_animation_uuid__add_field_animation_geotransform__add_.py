# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Animation.uuid'
        db.delete_column('pyramids_animation', 'uuid')

        # Adding field 'Animation.geotransform'
        db.add_column('pyramids_animation', 'geotransform', self.gf('django.db.models.fields.TextField')(default='{}'), keep_default=False)

        # Adding field 'Animation.basedir'
        db.add_column('pyramids_animation', 'basedir', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'Animation.uuid'
        db.add_column('pyramids_animation', 'uuid', self.gf('django.db.models.fields.CharField')(default='', max_length=36, unique=True, blank=True), keep_default=False)

        # Deleting field 'Animation.geotransform'
        db.delete_column('pyramids_animation', 'geotransform')

        # Deleting field 'Animation.basedir'
        db.delete_column('pyramids_animation', 'basedir')


    models = {
        'pyramids.animation': {
            'Meta': {'object_name': 'Animation'},
            'basedir': ('django.db.models.fields.TextField', [], {}),
            'frames': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'geotransform': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'pyramids.raster': {
            'Meta': {'object_name': 'Raster'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        }
    }

    complete_apps = ['pyramids']
