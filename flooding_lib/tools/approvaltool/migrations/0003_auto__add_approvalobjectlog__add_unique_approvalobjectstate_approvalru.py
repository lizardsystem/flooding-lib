# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ApprovalObjectLog'
        db.create_table('approvaltool_approvalobjectlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('approvalobject', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['approvaltool.ApprovalObject'])),
            ('approvalrule', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['approvaltool.ApprovalRule'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('creatorlog', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('successful', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('remarks', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('approvaltool', ['ApprovalObjectLog'])

        # Adding unique constraint on 'ApprovalObjectState', fields ['approvalrule', 'approvalobject']
        db.create_unique('approvaltool_approvalobjectstate', ['approvalrule_id', 'approvalobject_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'ApprovalObjectState', fields ['approvalrule', 'approvalobject']
        db.delete_unique('approvaltool_approvalobjectstate', ['approvalrule_id', 'approvalobject_id'])

        # Deleting model 'ApprovalObjectLog'
        db.delete_table('approvaltool_approvalobjectlog')


    models = {
        'approvaltool.approvalobject': {
            'Meta': {'object_name': 'ApprovalObject'},
            'approvalobjecttype': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['approvaltool.ApprovalObjectType']", 'symmetrical': 'False'}),
            'approvalrule': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['approvaltool.ApprovalRule']", 'through': "orm['approvaltool.ApprovalObjectState']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'approvaltool.approvalobjectlog': {
            'Meta': {'object_name': 'ApprovalObjectLog'},
            'approvalobject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['approvaltool.ApprovalObject']"}),
            'approvalrule': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['approvaltool.ApprovalRule']"}),
            'creatorlog': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'successful': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'approvaltool.approvalobjectstate': {
            'Meta': {'unique_together': "(('approvalobject', 'approvalrule'),)", 'object_name': 'ApprovalObjectState'},
            'approvalobject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['approvaltool.ApprovalObject']"}),
            'approvalrule': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['approvaltool.ApprovalRule']"}),
            'creatorlog': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'successful': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'approvaltool.approvalobjecttype': {
            'Meta': {'object_name': 'ApprovalObjectType'},
            'approvalrule': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['approvaltool.ApprovalRule']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'type': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        'approvaltool.approvalrule': {
            'Meta': {'object_name': 'ApprovalRule'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'permissionlevel': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['approvaltool']
