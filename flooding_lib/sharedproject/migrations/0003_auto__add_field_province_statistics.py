# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Province.statistics'
        db.add_column('sharedproject_province', 'statistics', self.gf('django.db.models.fields.TextField')(null=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Province.statistics'
        db.delete_column('sharedproject_province', 'statistics')


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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'statistics': ('django.db.models.fields.TextField', [], {'null': 'True'})
        }
    }

    complete_apps = ['sharedproject']
