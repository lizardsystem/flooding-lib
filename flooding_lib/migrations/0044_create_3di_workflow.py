# -*- coding: utf-8 -*-
from south.v2 import DataMigration


class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."

        # Create a WorkflowTemplate for 3di.
        from lizard_worker.models import WorkflowTemplate
        from lizard_worker.models import WorkflowTemplateTask
        from lizard_worker.models import TaskType
        template, _ = WorkflowTemplate.objects.get_or_create(
            code=301, defaults=dict(
                description='3Di import workflow template'
            ))
        import_task = TaskType.objects.get(name='220')
        pyramid_task = TaskType.objects.get(name='150')
        presentation_task = TaskType.objects.get(name='155')

        WorkflowTemplateTask.objects.get_or_create(
            code=import_task, parent_code=import_task,
            workflow_template=template
        )
        WorkflowTemplateTask.objects.get_or_create(
            code=pyramid_task, parent_code=import_task,
            workflow_template=template
        )
        WorkflowTemplateTask.objects.get_or_create(
            code=presentation_task, parent_code=pyramid_task,
            workflow_template=template
        )

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'approvaltool.approvalobject': {
            'Meta': {'object_name': 'ApprovalObject'},
            'approvalobjecttype': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['approvaltool.ApprovalObjectType']", 'symmetrical': 'False'}),
            'approvalrule': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['approvaltool.ApprovalRule']", 'through': u"orm['approvaltool.ApprovalObjectState']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'approvaltool.approvalobjectstate': {
            'Meta': {'unique_together': "(('approvalobject', 'approvalrule'),)", 'object_name': 'ApprovalObjectState'},
            'approvalobject': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['approvaltool.ApprovalObject']"}),
            'approvalrule': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['approvaltool.ApprovalRule']"}),
            'creatorlog': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'successful': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        u'approvaltool.approvalobjecttype': {
            'Meta': {'object_name': 'ApprovalObjectType'},
            'approvalrule': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['approvaltool.ApprovalRule']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'type': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        u'approvaltool.approvalrule': {
            'Meta': {'object_name': 'ApprovalRule'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'permissionlevel': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'flooding_lib.attachment': {
            'Meta': {'object_name': 'Attachment', 'db_table': "'flooding_attachment'"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'uploaded_by': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'uploaded_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'flooding_lib.breach': {
            'Meta': {'ordering': "['name']", 'object_name': 'Breach', 'db_table': "'flooding_breach'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'administrator': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'canalbottomlevel': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'decheight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'decheightbaselevel': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'defaulttide': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.WaterlevelSet']"}),
            'defbaselevel': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'defrucritical': ('django.db.models.fields.FloatField', [], {}),
            'dike': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Dike']"}),
            'externalnode': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'externalwater': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.ExternalWater']"}),
            'fl_rk_adm_jud': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fl_rk_dpv_ref_part': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fl_rk_dpv_ref_sect': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fl_rk_nrm': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'groundlevel': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internalnode': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'levelnormfrequency': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Region']"}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sobekmodels': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.SobekModel']", 'through': u"orm['flooding_lib.BreachSobekModel']", 'symmetrical': 'False'})
        },
        u'flooding_lib.breachsobekmodel': {
            'Meta': {'unique_together': "(('sobekmodel', 'breach'),)", 'object_name': 'BreachSobekModel', 'db_table': "'flooding_breachsobekmodel'"},
            'breach': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Breach']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sobekid': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodel': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.SobekModel']"})
        },
        u'flooding_lib.cutofflocation': {
            'Meta': {'object_name': 'CutoffLocation', 'db_table': "'flooding_cutofflocation'"},
            'bottomlevel': ('django.db.models.fields.FloatField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'deftclose': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodels': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.SobekModel']", 'through': u"orm['flooding_lib.CutoffLocationSobekModelSetting']", 'symmetrical': 'False'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'width': ('django.db.models.fields.FloatField', [], {})
        },
        u'flooding_lib.cutofflocationset': {
            'Meta': {'object_name': 'CutoffLocationSet', 'db_table': "'flooding_cutofflocationset'"},
            'cutofflocations': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.CutoffLocation']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'flooding_lib.cutofflocationsobekmodelsetting': {
            'Meta': {'object_name': 'CutoffLocationSobekModelSetting', 'db_table': "'flooding_cutofflocationsobekmodelsetting'"},
            'cutofflocation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.CutoffLocation']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sobekid': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodel': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.SobekModel']"})
        },
        u'flooding_lib.dike': {
            'Meta': {'object_name': 'Dike', 'db_table': "'flooding_dike'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'flooding_lib.embankmentunit': {
            'Meta': {'object_name': 'EmbankmentUnit', 'db_table': "'flooding_embankment_unit'"},
            'geometry': ('django.contrib.gis.db.models.fields.LineStringField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measure': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.Measure']", 'symmetrical': 'False'}),
            'original_height': ('django.db.models.fields.FloatField', [], {}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Region']"}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'unit_id': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'flooding_lib.externalwater': {
            'Meta': {'object_name': 'ExternalWater', 'db_table': "'flooding_externalwater'"},
            'area': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'cutofflocations': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.CutoffLocation']", 'symmetrical': 'False', 'blank': 'True'}),
            'deftpeak': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'deftsim': ('django.db.models.fields.FloatField', [], {}),
            'deftstorm': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'liztype': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'maxlevel': ('django.db.models.fields.FloatField', [], {'default': '15'}),
            'minlevel': ('django.db.models.fields.FloatField', [], {'default': '-10'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodels': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.SobekModel']", 'symmetrical': 'False', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        u'flooding_lib.extrainfofield': {
            'Meta': {'object_name': 'ExtraInfoField', 'db_table': "'flooding_extrainfofield'"},
            'header': ('django.db.models.fields.IntegerField', [], {'default': '20'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'use_in_scenario_overview': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'flooding_lib.extrascenarioinfo': {
            'Meta': {'unique_together': "(('extrainfofield', 'scenario'),)", 'object_name': 'ExtraScenarioInfo', 'db_table': "'flooding_extrascenarioinfo'"},
            'extrainfofield': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.ExtraInfoField']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Scenario']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'flooding_lib.map': {
            'Meta': {'object_name': 'Map', 'db_table': "'flooding_map'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'layers': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'srs': ('django.db.models.fields.CharField', [], {'default': "'EPSG:900913'", 'max_length': '50'}),
            'tiled': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'transparent': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'visible': ('django.db.models.fields.BooleanField', [], {})
        },
        u'flooding_lib.measure': {
            'Meta': {'object_name': 'Measure', 'db_table': "'flooding_measure'"},
            'adjustment': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'reference_adjustment': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'strategy': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.Strategy']", 'symmetrical': 'False'})
        },
        u'flooding_lib.program': {
            'Meta': {'object_name': 'Program', 'db_table': "'flooding_program'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'flooding_lib.project': {
            'Meta': {'ordering': "('friendlyname', 'name', 'owner')", 'object_name': 'Project', 'db_table': "'flooding_project'"},
            'approval_object_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['approvaltool.ApprovalObjectType']", 'null': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'color_mapping_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'friendlyname': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.Region']", 'symmetrical': 'False', 'blank': 'True'}),
            'regionsets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.RegionSet']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'flooding_lib.projectcolormap': {
            'Meta': {'object_name': 'ProjectColormap'},
            'colormap': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pyramids.Colormap']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_presentation.PresentationType']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Project']"})
        },
        u'flooding_lib.projectgrouppermission': {
            'Meta': {'unique_together': "(('group', 'project', 'permission'),)", 'object_name': 'ProjectGroupPermission', 'db_table': "'flooding_projectgrouppermission'"},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission': ('django.db.models.fields.IntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Project']"})
        },
        u'flooding_lib.region': {
            'Meta': {'object_name': 'Region', 'db_table': "'flooding_region'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'cutofflocations': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.CutoffLocation']", 'symmetrical': 'False', 'blank': 'True'}),
            'dijkringnr': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'longname': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'maps': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.Map']", 'symmetrical': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'normfrequency': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodels': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.SobekModel']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'flooding_lib.regionset': {
            'Meta': {'object_name': 'RegionSet', 'db_table': "'flooding_regionset'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children_set'", 'null': 'True', 'to': u"orm['flooding_lib.RegionSet']"}),
            'regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.Region']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'flooding_lib.result': {
            'Meta': {'unique_together': "(('scenario', 'resulttype'),)", 'object_name': 'Result', 'db_table': "'flooding_result'"},
            'animation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pyramids.Animation']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'bbox': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True', 'blank': 'True'}),
            'deltat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'firstnr': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastnr': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'raster': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pyramids.Raster']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'resultloc': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'resultpngloc': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'resulttype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.ResultType']"}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Scenario']"}),
            'startnr': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'flooding_lib.resulttype': {
            'Meta': {'object_name': 'ResultType', 'db_table': "'flooding_resulttype'"},
            'color_mapping_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'content_names_re': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'overlaytype': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'presentationtype': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_presentation.PresentationType']", 'through': u"orm['flooding_lib.ResultType_PresentationType']", 'symmetrical': 'False'}),
            'program': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Program']"}),
            'shortname_dutch': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'use_to_compute_arrival_times': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'flooding_lib.resulttype_presentationtype': {
            'Meta': {'object_name': 'ResultType_PresentationType', 'db_table': "'flooding_resulttype_presentationtype'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_presentation.PresentationType']"}),
            'remarks': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'resulttype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.ResultType']"})
        },
        u'flooding_lib.scenario': {
            'Meta': {'ordering': "('name', 'owner')", 'object_name': 'Scenario', 'db_table': "'flooding_scenario'"},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'archived_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'archived_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'archived_by_user'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'breaches': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.Breach']", 'through': u"orm['flooding_lib.ScenarioBreach']", 'symmetrical': 'False'}),
            'calcpriority': ('django.db.models.fields.IntegerField', [], {'default': '20'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'config_3di': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'cutofflocations': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_lib.CutoffLocation']", 'symmetrical': 'False', 'through': u"orm['flooding_lib.ScenarioCutoffLocation']", 'blank': 'True'}),
            'has_sobek_presentation': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'migrated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'presentationlayer': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['flooding_presentation.PresentationLayer']", 'through': u"orm['flooding_lib.Scenario_PresentationLayer']", 'symmetrical': 'False'}),
            'project_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'scenarios'", 'symmetrical': 'False', 'through': u"orm['flooding_lib.ScenarioProject']", 'to': u"orm['flooding_lib.Project']"}),
            'remarks': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'result_base_path': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'ror_province': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sharedproject.Province']", 'null': 'True', 'blank': 'True'}),
            'sobekmodel_inundation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.SobekModel']", 'null': 'True'}),
            'status_cache': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'strategy': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['flooding_lib.Strategy']", 'null': 'True', 'blank': 'True'}),
            'tsim': ('django.db.models.fields.FloatField', [], {}),
            'workflow_template': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['lizard_worker.WorkflowTemplate']", 'null': 'True', 'db_column': "'workflow_template'"})
        },
        u'flooding_lib.scenario_presentationlayer': {
            'Meta': {'object_name': 'Scenario_PresentationLayer', 'db_table': "'flooding_scenario_presentationlayer'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationlayer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_presentation.PresentationLayer']"}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Scenario']"})
        },
        u'flooding_lib.scenariobreach': {
            'Meta': {'unique_together': "(('scenario', 'breach'),)", 'object_name': 'ScenarioBreach', 'db_table': "'flooding_scenariobreach'"},
            'bottomlevelbreach': ('django.db.models.fields.FloatField', [], {}),
            'brdischcoef': ('django.db.models.fields.FloatField', [], {}),
            'breach': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Breach']"}),
            'brf1': ('django.db.models.fields.FloatField', [], {}),
            'brf2': ('django.db.models.fields.FloatField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'extwbaselevel': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'extwmaxlevel': ('django.db.models.fields.FloatField', [], {}),
            'extwrepeattime': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'hstartbreach': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initialcrest': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'manualwaterlevelinput': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'methstartbreach': ('django.db.models.fields.IntegerField', [], {}),
            'pitdepth': ('django.db.models.fields.FloatField', [], {}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Scenario']"}),
            'sobekmodel_externalwater': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.SobekModel']", 'null': 'True', 'blank': 'True'}),
            'tdeltaphase': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'tide': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'tide'", 'null': 'True', 'blank': 'True', 'to': u"orm['flooding_lib.WaterlevelSet']"}),
            'tmaxdepth': ('django.db.models.fields.FloatField', [], {}),
            'tpeak': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'tstartbreach': ('django.db.models.fields.FloatField', [], {}),
            'tstorm': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'ucritical': ('django.db.models.fields.FloatField', [], {}),
            'waterlevelset': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.WaterlevelSet']"}),
            'widthbrinit': ('django.db.models.fields.FloatField', [], {})
        },
        u'flooding_lib.scenariocutofflocation': {
            'Meta': {'unique_together': "(('scenario', 'cutofflocation'),)", 'object_name': 'ScenarioCutoffLocation', 'db_table': "'flooding_scenariocutofflocation'"},
            'action': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'cutofflocation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.CutoffLocation']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Scenario']"}),
            'tclose': ('django.db.models.fields.FloatField', [], {})
        },
        u'flooding_lib.scenarioproject': {
            'Meta': {'object_name': 'ScenarioProject'},
            'approvalobject': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['approvaltool.ApprovalObject']", 'null': 'True', 'blank': 'True'}),
            'approved': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_main_project': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Project']"}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Scenario']"})
        },
        u'flooding_lib.scenarioshareoffer': {
            'Meta': {'unique_together': "(('scenario', 'new_project'),)", 'object_name': 'ScenarioShareOffer'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Project']"}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Scenario']"}),
            'shared_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'})
        },
        u'flooding_lib.sobekmodel': {
            'Meta': {'object_name': 'SobekModel', 'db_table': "'flooding_sobekmodel'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'embankment_damage_shape': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keep_initial_level': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'model_case': ('django.db.models.fields.IntegerField', [], {}),
            'model_srid': ('django.db.models.fields.IntegerField', [], {}),
            'model_vardescription': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'model_varname': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'model_version': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'project_fileloc': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'sobekmodeltype': ('django.db.models.fields.IntegerField', [], {}),
            'sobekversion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.SobekVersion']"})
        },
        u'flooding_lib.sobekversion': {
            'Meta': {'object_name': 'SobekVersion', 'db_table': "'flooding_sobekversion'"},
            'fileloc_startfile': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'flooding_lib.strategy': {
            'Meta': {'object_name': 'Strategy', 'db_table': "'flooding_strategy'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Region']", 'null': 'True', 'blank': 'True'}),
            'save_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'visible_for_loading': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'flooding_lib.task': {
            'Meta': {'object_name': 'Task', 'db_table': "'flooding_task'"},
            'creatorlog': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'errorlog': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Scenario']"}),
            'successful': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'tasktype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.TaskType']"}),
            'tfinished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'tstart': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'flooding_lib.taskexecutor': {
            'Meta': {'unique_together': "(('ipaddress', 'port'), ('name', 'seq'))", 'object_name': 'TaskExecutor', 'db_table': "'flooding_taskexecutor'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ipaddress': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'port': ('django.db.models.fields.IntegerField', [], {}),
            'revision': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'seq': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'tasktypes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['flooding_lib.TaskType']", 'null': 'True', 'blank': 'True'})
        },
        u'flooding_lib.tasktype': {
            'Meta': {'object_name': 'TaskType', 'db_table': "'flooding_tasktype'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'flooding_lib.threedicalculation': {
            'Meta': {'object_name': 'ThreediCalculation'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.Scenario']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'threedi_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.ThreediModel']"})
        },
        u'flooding_lib.threedimodel': {
            'Meta': {'object_name': 'ThreediModel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mdu_filename': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'scenario_zip_filename': ('django.db.models.fields.TextField', [], {})
        },
        u'flooding_lib.userpermission': {
            'Meta': {'unique_together': "(('user', 'permission'),)", 'object_name': 'UserPermission', 'db_table': "'flooding_userpermission'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'flooding_lib.waterlevel': {
            'Meta': {'unique_together': "(('waterlevelset', 'time'),)", 'object_name': 'Waterlevel', 'db_table': "'flooding_waterlevel'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.FloatField', [], {}),
            'value': ('django.db.models.fields.FloatField', [], {}),
            'waterlevelset': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_lib.WaterlevelSet']"})
        },
        u'flooding_lib.waterlevelset': {
            'Meta': {'object_name': 'WaterlevelSet', 'db_table': "'flooding_waterlevelset'"},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        u'flooding_presentation.customindicator': {
            'Meta': {'object_name': 'CustomIndicator', 'db_table': "'presentation_customindicator'"},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'flooding_presentation.presentationlayer': {
            'Meta': {'object_name': 'PresentationLayer', 'db_table': "'presentation_presentationlayer'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_presentation.PresentationType']"}),
            'source_application': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'flooding_presentation.presentationtype': {
            'Meta': {'object_name': 'PresentationType', 'db_table': "'presentation_presentationtype'"},
            'absolute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'class_unit': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'custom_indicator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['flooding_presentation.CustomIndicator']", 'null': 'True', 'blank': 'True'}),
            'default_colormap': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pyramids.Colormap']", 'null': 'True', 'blank': 'True'}),
            'default_legend_id': ('django.db.models.fields.IntegerField', [], {}),
            'default_maxvalue': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'generation_geo_source': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'generation_geo_source_part': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'geo_source_filter': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'geo_type': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        u'lizard_worker.workflowtemplate': {
            'Meta': {'object_name': 'WorkflowTemplate'},
            'code': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'max_length': '30'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'pyramids.animation': {
            'Meta': {'object_name': 'Animation'},
            'basedir': ('django.db.models.fields.TextField', [], {}),
            'cols': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'frames': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'geotransform': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maxvalue': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'rows': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'pyramids.colormap': {
            'Meta': {'ordering': "(u'description',)", 'object_name': 'Colormap'},
            'description': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'matplotlib_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        u'pyramids.raster': {
            'Meta': {'object_name': 'Raster'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'sharedproject.province': {
            'Meta': {'object_name': 'Province'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'statistics': ('django.db.models.fields.TextField', [], {'null': 'True'})
        }
    }

    complete_apps = ['flooding_lib']
    symmetrical = True
