# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Raster'
        db.create_table('pyramids_raster', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36, blank=True)),
        ))
        db.send_create_signal('pyramids', ['Raster'])

        # Adding model 'Animation'
        db.create_table('pyramids_animation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36, blank=True)),
            ('frames', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('pyramids', ['Animation'])


    def backwards(self, orm):

        # Deleting model 'Raster'
        db.delete_table('pyramids_raster')

        # Deleting model 'Animation'
        db.delete_table('pyramids_animation')


    models = {
        'pyramids.animation': {
            'Meta': {'object_name': 'Animation'},
            'frames': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        'pyramids.raster': {
            'Meta': {'object_name': 'Raster'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        }
    }

    complete_apps = ['pyramids']
