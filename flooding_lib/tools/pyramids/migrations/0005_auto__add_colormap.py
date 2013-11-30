# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Colormap'
        db.create_table('pyramids_colormap', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('matplotlib_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('description', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('pyramids', ['Colormap'])


    def backwards(self, orm):
        
        # Deleting model 'Colormap'
        db.delete_table('pyramids_colormap')


    models = {
        'pyramids.animation': {
            'Meta': {'object_name': 'Animation'},
            'basedir': ('django.db.models.fields.TextField', [], {}),
            'cols': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'frames': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'geotransform': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maxvalue': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'rows': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'pyramids.colormap': {
            'Meta': {'ordering': "(u'description',)", 'object_name': 'Colormap'},
            'description': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'matplotlib_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'pyramids.raster': {
            'Meta': {'object_name': 'Raster'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        }
    }

    complete_apps = ['pyramids']
