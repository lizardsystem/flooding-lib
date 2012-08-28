# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Province'
        db.create_table('sharedproject_province', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('sharedproject', ['Province'])

        # Adding model 'Owner'
        db.create_table('sharedproject_owner', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('province', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sharedproject.Province'])),
        ))
        db.send_create_signal('sharedproject', ['Owner'])


    def backwards(self, orm):
        
        # Deleting model 'Province'
        db.delete_table('sharedproject_province')

        # Deleting model 'Owner'
        db.delete_table('sharedproject_owner')


    models = {
        'sharedproject.owner': {
            'Meta': {'object_name': 'Owner'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'province': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sharedproject.Province']"})
        },
        'sharedproject.province': {
            'Meta': {'object_name': 'Province'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['sharedproject']
