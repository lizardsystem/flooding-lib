# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ApprovalObjectType'
        db.create_table('approvaltool_approvalobjecttype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('approvaltool', ['ApprovalObjectType'])

        # Adding M2M table for field approvalrule on 'ApprovalObjectType'
        db.create_table('approvaltool_approvalobjecttype_approvalrule', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('approvalobjecttype', models.ForeignKey(orm['approvaltool.approvalobjecttype'], null=False)),
            ('approvalrule', models.ForeignKey(orm['approvaltool.approvalrule'], null=False))
        ))
        db.create_unique('approvaltool_approvalobjecttype_approvalrule', ['approvalobjecttype_id', 'approvalrule_id'])

        # Adding model 'ApprovalObject'
        db.create_table('approvaltool_approvalobject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('approvaltool', ['ApprovalObject'])

        # Adding M2M table for field approvalobjecttype on 'ApprovalObject'
        db.create_table('approvaltool_approvalobject_approvalobjecttype', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('approvalobject', models.ForeignKey(orm['approvaltool.approvalobject'], null=False)),
            ('approvalobjecttype', models.ForeignKey(orm['approvaltool.approvalobjecttype'], null=False))
        ))
        db.create_unique('approvaltool_approvalobject_approvalobjecttype', ['approvalobject_id', 'approvalobjecttype_id'])

        # Adding model 'ApprovalObjectState'
        db.create_table('approvaltool_approvalobjectstate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('approvalobject', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['approvaltool.ApprovalObject'])),
            ('approvalrule', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['approvaltool.ApprovalRule'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('creatorlog', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('successful', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('remarks', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('approvaltool', ['ApprovalObjectState'])

        # Adding model 'ApprovalRule'
        db.create_table('approvaltool_approvalrule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('position', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('permissionlevel', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('approvaltool', ['ApprovalRule'])


    def backwards(self, orm):
        
        # Deleting model 'ApprovalObjectType'
        db.delete_table('approvaltool_approvalobjecttype')

        # Removing M2M table for field approvalrule on 'ApprovalObjectType'
        db.delete_table('approvaltool_approvalobjecttype_approvalrule')

        # Deleting model 'ApprovalObject'
        db.delete_table('approvaltool_approvalobject')

        # Removing M2M table for field approvalobjecttype on 'ApprovalObject'
        db.delete_table('approvaltool_approvalobject_approvalobjecttype')

        # Deleting model 'ApprovalObjectState'
        db.delete_table('approvaltool_approvalobjectstate')

        # Deleting model 'ApprovalRule'
        db.delete_table('approvaltool_approvalrule')


    models = {
        'approvaltool.approvalobject': {
            'Meta': {'object_name': 'ApprovalObject'},
            'approvalobjecttype': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['approvaltool.ApprovalObjectType']", 'symmetrical': 'False'}),
            'approvalrule': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['approvaltool.ApprovalRule']", 'through': "orm['approvaltool.ApprovalObjectState']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'approvaltool.approvalobjectstate': {
            'Meta': {'object_name': 'ApprovalObjectState'},
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
            'type': ('django.db.models.fields.IntegerField', [], {})
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
