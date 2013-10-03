# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'RORKering.type_kering'
        db.add_column('importtool_rorkering', 'type_kering', self.gf('django.db.models.fields.CharField')(default=datetime.date(2013, 9, 25), max_length=20), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'RORKering.type_kering'
        db.delete_column('importtool_rorkering', 'type_kering')


    models = {
        'approvaltool.approvalobject': {
            'Meta': {'object_name': 'ApprovalObject'},
            'approvalobjecttype': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['approvaltool.ApprovalObjectType']", 'symmetrical': 'False'}),
            'approvalrule': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['approvaltool.ApprovalRule']", 'through': "orm['approvaltool.ApprovalObjectState']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        },
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
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'flooding_lib.attachment': {
            'Meta': {'object_name': 'Attachment', 'db_table': "'flooding_attachment'"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'uploaded_by': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'uploaded_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'flooding_lib.breach': {
            'Meta': {'ordering': "['name']", 'object_name': 'Breach', 'db_table': "'flooding_breach'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'canalbottomlevel': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'decheight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'decheightbaselevel': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'defaulttide': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.WaterlevelSet']"}),
            'defbaselevel': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'defrucritical': ('django.db.models.fields.FloatField', [], {}),
            'dike': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Dike']"}),
            'externalnode': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'externalwater': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.ExternalWater']"}),
            'geom': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'groundlevel': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internalnode': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'levelnormfrequency': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Region']"}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sobekmodels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.SobekModel']", 'through': "orm['flooding_lib.BreachSobekModel']", 'symmetrical': 'False'})
        },
        'flooding_lib.breachsobekmodel': {
            'Meta': {'unique_together': "(('sobekmodel', 'breach'),)", 'object_name': 'BreachSobekModel', 'db_table': "'flooding_breachsobekmodel'"},
            'breach': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Breach']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sobekid': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.SobekModel']"})
        },
        'flooding_lib.cutofflocation': {
            'Meta': {'object_name': 'CutoffLocation', 'db_table': "'flooding_cutofflocation'"},
            'bottomlevel': ('django.db.models.fields.FloatField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'deftclose': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.SobekModel']", 'through': "orm['flooding_lib.CutoffLocationSobekModelSetting']", 'symmetrical': 'False'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'width': ('django.db.models.fields.FloatField', [], {})
        },
        'flooding_lib.cutofflocationsobekmodelsetting': {
            'Meta': {'object_name': 'CutoffLocationSobekModelSetting', 'db_table': "'flooding_cutofflocationsobekmodelsetting'"},
            'cutofflocation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.CutoffLocation']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sobekid': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.SobekModel']"})
        },
        'flooding_lib.dike': {
            'Meta': {'object_name': 'Dike', 'db_table': "'flooding_dike'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_lib.externalwater': {
            'Meta': {'object_name': 'ExternalWater', 'db_table': "'flooding_externalwater'"},
            'area': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'cutofflocations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.CutoffLocation']", 'symmetrical': 'False', 'blank': 'True'}),
            'deftpeak': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'deftsim': ('django.db.models.fields.FloatField', [], {}),
            'deftstorm': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'liztype': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'maxlevel': ('django.db.models.fields.FloatField', [], {'default': '15'}),
            'minlevel': ('django.db.models.fields.FloatField', [], {'default': '-10'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.SobekModel']", 'symmetrical': 'False', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_lib.map': {
            'Meta': {'object_name': 'Map', 'db_table': "'flooding_map'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'layers': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'srs': ('django.db.models.fields.CharField', [], {'default': "'EPSG:900913'", 'max_length': '50'}),
            'tiled': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'transparent': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_lib.project': {
            'Meta': {'ordering': "('friendlyname', 'name', 'owner')", 'object_name': 'Project', 'db_table': "'flooding_project'"},
            'approval_object_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['approvaltool.ApprovalObjectType']", 'null': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'color_mapping_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'friendlyname': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.Region']", 'symmetrical': 'False', 'blank': 'True'}),
            'regionsets': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.RegionSet']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'flooding_lib.region': {
            'Meta': {'object_name': 'Region', 'db_table': "'flooding_region'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'cutofflocations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.CutoffLocation']", 'symmetrical': 'False', 'blank': 'True'}),
            'dijkringnr': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'longname': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'maps': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.Map']", 'symmetrical': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'normfrequency': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.SobekModel']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'flooding_lib.regionset': {
            'Meta': {'object_name': 'RegionSet', 'db_table': "'flooding_regionset'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children_set'", 'null': 'True', 'to': "orm['flooding_lib.RegionSet']"}),
            'regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.Region']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'flooding_lib.scenario': {
            'Meta': {'ordering': "('name', 'owner')", 'object_name': 'Scenario', 'db_table': "'flooding_scenario'"},
            'breaches': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.Breach']", 'through': "orm['flooding_lib.ScenarioBreach']", 'symmetrical': 'False'}),
            'calcpriority': ('django.db.models.fields.IntegerField', [], {'default': '20'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'config_3di': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'cutofflocations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.CutoffLocation']", 'symmetrical': 'False', 'through': "orm['flooding_lib.ScenarioCutoffLocation']", 'blank': 'True'}),
            'has_sobek_presentation': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'migrated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'presentationlayer': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_presentation.PresentationLayer']", 'through': "orm['flooding_lib.Scenario_PresentationLayer']", 'symmetrical': 'False'}),
            'project_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'scenarios'", 'symmetrical': 'False', 'through': "orm['flooding_lib.ScenarioProject']", 'to': "orm['flooding_lib.Project']"}),
            'remarks': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'result_base_path': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'ror_province': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sharedproject.Province']", 'null': 'True', 'blank': 'True'}),
            'sobekmodel_inundation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.SobekModel']", 'null': 'True'}),
            'status_cache': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'strategy': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['flooding_lib.Strategy']", 'null': 'True', 'blank': 'True'}),
            'tsim': ('django.db.models.fields.FloatField', [], {}),
            'workflow_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_worker.WorkflowTemplate']", 'null': 'True', 'db_column': "'workflow_template'"})
        },
        'flooding_lib.scenario_presentationlayer': {
            'Meta': {'object_name': 'Scenario_PresentationLayer', 'db_table': "'flooding_scenario_presentationlayer'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationlayer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.PresentationLayer']"}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Scenario']"})
        },
        'flooding_lib.scenariobreach': {
            'Meta': {'unique_together': "(('scenario', 'breach'),)", 'object_name': 'ScenarioBreach', 'db_table': "'flooding_scenariobreach'"},
            'bottomlevelbreach': ('django.db.models.fields.FloatField', [], {}),
            'brdischcoef': ('django.db.models.fields.FloatField', [], {}),
            'breach': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Breach']"}),
            'brf1': ('django.db.models.fields.FloatField', [], {}),
            'brf2': ('django.db.models.fields.FloatField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'extwbaselevel': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'extwmaxlevel': ('django.db.models.fields.FloatField', [], {}),
            'extwrepeattime': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'hstartbreach': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initialcrest': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'manualwaterlevelinput': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'methstartbreach': ('django.db.models.fields.IntegerField', [], {}),
            'pitdepth': ('django.db.models.fields.FloatField', [], {}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Scenario']"}),
            'sobekmodel_externalwater': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.SobekModel']", 'null': 'True', 'blank': 'True'}),
            'tdeltaphase': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'tide': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'tide'", 'null': 'True', 'blank': 'True', 'to': "orm['flooding_lib.WaterlevelSet']"}),
            'tmaxdepth': ('django.db.models.fields.FloatField', [], {}),
            'tpeak': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'tstartbreach': ('django.db.models.fields.FloatField', [], {}),
            'tstorm': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'ucritical': ('django.db.models.fields.FloatField', [], {}),
            'waterlevelset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.WaterlevelSet']"}),
            'widthbrinit': ('django.db.models.fields.FloatField', [], {})
        },
        'flooding_lib.scenariocutofflocation': {
            'Meta': {'unique_together': "(('scenario', 'cutofflocation'),)", 'object_name': 'ScenarioCutoffLocation', 'db_table': "'flooding_scenariocutofflocation'"},
            'action': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'cutofflocation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.CutoffLocation']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Scenario']"}),
            'tclose': ('django.db.models.fields.FloatField', [], {})
        },
        'flooding_lib.scenarioproject': {
            'Meta': {'object_name': 'ScenarioProject'},
            'approvalobject': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['approvaltool.ApprovalObject']", 'null': 'True', 'blank': 'True'}),
            'approved': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_main_project': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Project']"}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Scenario']"})
        },
        'flooding_lib.sobekmodel': {
            'Meta': {'object_name': 'SobekModel', 'db_table': "'flooding_sobekmodel'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'embankment_damage_shape': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keep_initial_level': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'model_case': ('django.db.models.fields.IntegerField', [], {}),
            'model_srid': ('django.db.models.fields.IntegerField', [], {}),
            'model_vardescription': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'model_varname': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'model_version': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'project_fileloc': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'sobekmodeltype': ('django.db.models.fields.IntegerField', [], {}),
            'sobekversion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.SobekVersion']"})
        },
        'flooding_lib.sobekversion': {
            'Meta': {'object_name': 'SobekVersion', 'db_table': "'flooding_sobekversion'"},
            'fileloc_startfile': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_lib.strategy': {
            'Meta': {'object_name': 'Strategy', 'db_table': "'flooding_strategy'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Region']", 'null': 'True', 'blank': 'True'}),
            'save_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'visible_for_loading': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'flooding_lib.waterlevelset': {
            'Meta': {'object_name': 'WaterlevelSet', 'db_table': "'flooding_waterlevelset'"},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_presentation.customindicator': {
            'Meta': {'object_name': 'CustomIndicator', 'db_table': "'presentation_customindicator'"},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_presentation.presentationlayer': {
            'Meta': {'object_name': 'PresentationLayer', 'db_table': "'presentation_presentationlayer'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.PresentationType']"}),
            'source_application': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
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
        'importtool.filevalue': {
            'Meta': {'object_name': 'FileValue'},
            'importscenario_inputfield': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['importtool.ImportScenarioInputField']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'importtool.floatvalue': {
            'Meta': {'object_name': 'FloatValue'},
            'importscenario_inputfield': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['importtool.ImportScenarioInputField']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'importtool.groupimport': {
            'Meta': {'object_name': 'GroupImport'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'results': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'table': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'upload_successful': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'importtool.importscenario': {
            'Meta': {'object_name': 'ImportScenario'},
            'action_taker': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'approvalobject': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['approvaltool.ApprovalObject']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'breach': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Breach']", 'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'groupimport': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['importtool.GroupImport']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Project']", 'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Region']", 'null': 'True', 'blank': 'True'}),
            'scenario': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flooding_lib.Scenario']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'validation_remarks': ('django.db.models.fields.TextField', [], {'default': "'-'", 'null': 'True', 'blank': 'True'})
        },
        'importtool.importscenarioinputfield': {
            'Meta': {'object_name': 'ImportScenarioInputField'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'importscenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['importtool.ImportScenario']", 'null': 'True'}),
            'inputfield': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['importtool.InputField']", 'null': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '20'}),
            'validation_remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'importtool.inputfield': {
            'Meta': {'ordering': "['header']", 'object_name': 'InputField'},
            'destination_field': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'destination_filename': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'destination_table': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'excel_hint': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'header': ('django.db.models.fields.IntegerField', [], {'default': '80'}),
            'hint_text': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'hover_text': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_table_field': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'options': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'visibility_dependency_field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['importtool.InputField']", 'null': 'True', 'blank': 'True'}),
            'visibility_dependency_value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'importtool.integervalue': {
            'Meta': {'object_name': 'IntegerValue'},
            'importscenario_inputfield': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['importtool.ImportScenarioInputField']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'importtool.rorkering': {
            'Meta': {'ordering': "['uploaded_at']", 'object_name': 'RORKering'},
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'type_kering': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'importtool.stringvalue': {
            'Meta': {'object_name': 'StringValue'},
            'importscenario_inputfield': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['importtool.ImportScenarioInputField']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'importtool.textvalue': {
            'Meta': {'object_name': 'TextValue'},
            'importscenario_inputfield': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['importtool.ImportScenarioInputField']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'lizard_worker.workflowtemplate': {
            'Meta': {'object_name': 'WorkflowTemplate'},
            'code': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'max_length': '30'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'sharedproject.province': {
            'Meta': {'object_name': 'Province'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'statistics': ('django.db.models.fields.TextField', [], {'null': 'True'})
        }
    }

    complete_apps = ['importtool']
