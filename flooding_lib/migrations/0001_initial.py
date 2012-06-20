# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Attachment'
        db.create_table('flooding_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('remarks', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('uploaded_by', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('uploaded_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('flooding_lib', ['Attachment'])

        # Adding model 'SobekVersion'
        db.create_table('flooding_sobekversion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('fileloc_startfile', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('flooding_lib', ['SobekVersion'])

        # Adding model 'SobekModel'
        db.create_table('flooding_sobekmodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sobekversion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.SobekVersion'])),
            ('sobekmodeltype', self.gf('django.db.models.fields.IntegerField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('project_fileloc', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('model_case', self.gf('django.db.models.fields.IntegerField')()),
            ('model_version', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('model_srid', self.gf('django.db.models.fields.IntegerField')()),
            ('model_varname', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('model_vardescription', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('remarks', self.gf('django.db.models.fields.TextField')(null=True)),
            ('embankment_damage_shape', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
        ))
        db.send_create_signal('flooding_lib', ['SobekModel'])

        # Adding model 'CutoffLocation'
        db.create_table('flooding_cutofflocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('bottomlevel', self.gf('django.db.models.fields.FloatField')()),
            ('width', self.gf('django.db.models.fields.FloatField')()),
            ('deftclose', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
        ))
        db.send_create_signal('flooding_lib', ['CutoffLocation'])

        # Adding model 'ExternalWater'
        db.create_table('flooding_externalwater', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('area', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('deftstorm', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('deftpeak', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('deftsim', self.gf('django.db.models.fields.FloatField')()),
            ('minlevel', self.gf('django.db.models.fields.FloatField')(default=-10)),
            ('maxlevel', self.gf('django.db.models.fields.FloatField')(default=15)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
        ))
        db.send_create_signal('flooding_lib', ['ExternalWater'])

        # Adding M2M table for field sobekmodels on 'ExternalWater'
        db.create_table('flooding_externalwater_sobekmodels', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('externalwater', models.ForeignKey(orm['flooding_lib.externalwater'], null=False)),
            ('sobekmodel', models.ForeignKey(orm['flooding_lib.sobekmodel'], null=False))
        ))
        db.create_unique('flooding_externalwater_sobekmodels', ['externalwater_id', 'sobekmodel_id'])

        # Adding M2M table for field cutofflocations on 'ExternalWater'
        db.create_table('flooding_externalwater_cutofflocations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('externalwater', models.ForeignKey(orm['flooding_lib.externalwater'], null=False)),
            ('cutofflocation', models.ForeignKey(orm['flooding_lib.cutofflocation'], null=False))
        ))
        db.create_unique('flooding_externalwater_cutofflocations', ['externalwater_id', 'cutofflocation_id'])

        # Adding model 'Dike'
        db.create_table('flooding_dike', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('flooding_lib', ['Dike'])

        # Adding model 'WaterlevelSet'
        db.create_table('flooding_waterlevelset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('remarks', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
        ))
        db.send_create_signal('flooding_lib', ['WaterlevelSet'])

        # Adding model 'Waterlevel'
        db.create_table('flooding_waterlevel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('time', self.gf('django.db.models.fields.FloatField')()),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('waterlevelset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.WaterlevelSet'])),
        ))
        db.send_create_signal('flooding_lib', ['Waterlevel'])

        # Adding unique constraint on 'Waterlevel', fields ['waterlevelset', 'time']
        db.create_unique('flooding_waterlevel', ['waterlevelset_id', 'time'])

        # Adding model 'Map'
        db.create_table('flooding_map', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('remarks', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('index', self.gf('django.db.models.fields.IntegerField')(default=100)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('layers', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('transparent', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('tiled', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('srs', self.gf('django.db.models.fields.CharField')(default='EPSG:900913', max_length=50)),
        ))
        db.send_create_signal('flooding_lib', ['Map'])

        # Adding model 'Region'
        db.create_table('flooding_region', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('longname', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('normfrequency', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')()),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
            ('dijkringnr', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('flooding_lib', ['Region'])

        # Adding M2M table for field maps on 'Region'
        db.create_table('flooding_region_maps', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('region', models.ForeignKey(orm['flooding_lib.region'], null=False)),
            ('map', models.ForeignKey(orm['flooding_lib.map'], null=False))
        ))
        db.create_unique('flooding_region_maps', ['region_id', 'map_id'])

        # Adding M2M table for field sobekmodels on 'Region'
        db.create_table('flooding_region_sobekmodels', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('region', models.ForeignKey(orm['flooding_lib.region'], null=False)),
            ('sobekmodel', models.ForeignKey(orm['flooding_lib.sobekmodel'], null=False))
        ))
        db.create_unique('flooding_region_sobekmodels', ['region_id', 'sobekmodel_id'])

        # Adding M2M table for field cutofflocations on 'Region'
        db.create_table('flooding_region_cutofflocations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('region', models.ForeignKey(orm['flooding_lib.region'], null=False)),
            ('cutofflocation', models.ForeignKey(orm['flooding_lib.cutofflocation'], null=False))
        ))
        db.create_unique('flooding_region_cutofflocations', ['region_id', 'cutofflocation_id'])

        # Adding model 'RegionSet'
        db.create_table('flooding_regionset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children_set', null=True, to=orm['flooding_lib.RegionSet'])),
        ))
        db.send_create_signal('flooding_lib', ['RegionSet'])

        # Adding M2M table for field regions on 'RegionSet'
        db.create_table('flooding_regionset_regions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('regionset', models.ForeignKey(orm['flooding_lib.regionset'], null=False)),
            ('region', models.ForeignKey(orm['flooding_lib.region'], null=False))
        ))
        db.create_unique('flooding_regionset_regions', ['regionset_id', 'region_id'])

        # Adding model 'Breach'
        db.create_table('flooding_breach', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('remarks', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('externalwater', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.ExternalWater'])),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Region'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('dike', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Dike'])),
            ('defaulttide', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.WaterlevelSet'])),
            ('levelnormfrequency', self.gf('django.db.models.fields.FloatField')()),
            ('canalbottomlevel', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('groundlevel', self.gf('django.db.models.fields.FloatField')()),
            ('defrucritical', self.gf('django.db.models.fields.FloatField')()),
            ('defbaselevel', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('decheight', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('decheightbaselevel', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('internalnode', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('externalnode', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
        ))
        db.send_create_signal('flooding_lib', ['Breach'])

        # Adding model 'BreachSobekModel'
        db.create_table('flooding_breachsobekmodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sobekmodel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.SobekModel'])),
            ('breach', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Breach'])),
            ('sobekid', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('flooding_lib', ['BreachSobekModel'])

        # Adding unique constraint on 'BreachSobekModel', fields ['sobekmodel', 'breach']
        db.create_unique('flooding_breachsobekmodel', ['sobekmodel_id', 'breach_id'])

        # Adding model 'CutoffLocationSet'
        db.create_table('flooding_cutofflocationset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('flooding_lib', ['CutoffLocationSet'])

        # Adding M2M table for field cutofflocations on 'CutoffLocationSet'
        db.create_table('flooding_cutofflocationset_cutofflocations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cutofflocationset', models.ForeignKey(orm['flooding_lib.cutofflocationset'], null=False)),
            ('cutofflocation', models.ForeignKey(orm['flooding_lib.cutofflocation'], null=False))
        ))
        db.create_unique('flooding_cutofflocationset_cutofflocations', ['cutofflocationset_id', 'cutofflocation_id'])

        # Adding model 'Project'
        db.create_table('flooding_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('friendlyname', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
        ))
        db.send_create_signal('flooding_lib', ['Project'])

        # Adding M2M table for field regionsets on 'Project'
        db.create_table('flooding_project_regionsets', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['flooding_lib.project'], null=False)),
            ('regionset', models.ForeignKey(orm['flooding_lib.regionset'], null=False))
        ))
        db.create_unique('flooding_project_regionsets', ['project_id', 'regionset_id'])

        # Adding M2M table for field regions on 'Project'
        db.create_table('flooding_project_regions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['flooding_lib.project'], null=False)),
            ('region', models.ForeignKey(orm['flooding_lib.region'], null=False))
        ))
        db.create_unique('flooding_project_regions', ['project_id', 'region_id'])

        # Adding model 'UserPermission'
        db.create_table('flooding_userpermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('permission', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_lib', ['UserPermission'])

        # Adding unique constraint on 'UserPermission', fields ['user', 'permission']
        db.create_unique('flooding_userpermission', ['user_id', 'permission'])

        # Adding model 'ProjectGroupPermission'
        db.create_table('flooding_projectgrouppermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Project'])),
            ('permission', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('flooding_lib', ['ProjectGroupPermission'])

        # Adding unique constraint on 'ProjectGroupPermission', fields ['group', 'project', 'permission']
        db.create_unique('flooding_projectgrouppermission', ['group_id', 'project_id', 'permission'])

        # Adding model 'PermissionProjectShapeDataLegend'
        db.create_table('flooding_lib_permissionprojectshapedatalegend', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Project'])),
            ('shapedatalegend', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_visualization.ShapeDataLegend'])),
        ))
        db.send_create_signal('flooding_lib', ['PermissionProjectShapeDataLegend'])

        # Adding model 'PermissionProjectGridDataLegend'
        db.create_table('flooding_lib_permissionprojectgriddatalegend', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Project'])),
            ('griddatalegend', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_visualization.ValueVisualizerMap'])),
        ))
        db.send_create_signal('flooding_lib', ['PermissionProjectGridDataLegend'])

        # Adding model 'ExtraInfoField'
        db.create_table('flooding_extrainfofield', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('use_in_scenario_overview', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('header', self.gf('django.db.models.fields.IntegerField')(default=20)),
            ('position', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('flooding_lib', ['ExtraInfoField'])

        # Adding model 'ExtraScenarioInfo'
        db.create_table('flooding_extrascenarioinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('extrainfofield', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.ExtraInfoField'])),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Scenario'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('flooding_lib', ['ExtraScenarioInfo'])

        # Adding unique constraint on 'ExtraScenarioInfo', fields ['extrainfofield', 'scenario']
        db.create_unique('flooding_extrascenarioinfo', ['extrainfofield_id', 'scenario_id'])

        # Adding model 'Scenario'
        db.create_table('flooding_scenario', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('remarks', self.gf('django.db.models.fields.TextField')(default=None, null=True, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Project'])),
            ('approvalobject', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['approvaltool.ApprovalObject'], null=True, blank=True)),
            ('strategy', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['flooding_lib.Strategy'], null=True, blank=True)),
            ('sobekmodel_inundation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.SobekModel'])),
            ('tsim', self.gf('django.db.models.fields.FloatField')()),
            ('calcpriority', self.gf('django.db.models.fields.IntegerField')(default=20)),
            ('status_cache', self.gf('django.db.models.fields.IntegerField')(default=None, null=True)),
            ('migrated', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('workflow_template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_worker.WorkflowTemplate'], db_column='workflow_template')),
        ))
        db.send_create_signal('flooding_lib', ['Scenario'])

        # Adding model 'ScenarioBreach'
        db.create_table('flooding_scenariobreach', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Scenario'])),
            ('breach', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Breach'])),
            ('waterlevelset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.WaterlevelSet'])),
            ('sobekmodel_externalwater', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.SobekModel'], null=True, blank=True)),
            ('widthbrinit', self.gf('django.db.models.fields.FloatField')()),
            ('methstartbreach', self.gf('django.db.models.fields.IntegerField')()),
            ('tstartbreach', self.gf('django.db.models.fields.FloatField')()),
            ('hstartbreach', self.gf('django.db.models.fields.FloatField')()),
            ('brdischcoef', self.gf('django.db.models.fields.FloatField')()),
            ('brf1', self.gf('django.db.models.fields.FloatField')()),
            ('brf2', self.gf('django.db.models.fields.FloatField')()),
            ('bottomlevelbreach', self.gf('django.db.models.fields.FloatField')()),
            ('ucritical', self.gf('django.db.models.fields.FloatField')()),
            ('pitdepth', self.gf('django.db.models.fields.FloatField')()),
            ('tmaxdepth', self.gf('django.db.models.fields.FloatField')()),
            ('extwmaxlevel', self.gf('django.db.models.fields.FloatField')()),
            ('extwbaselevel', self.gf('django.db.models.fields.FloatField')(default=None, null=True, blank=True)),
            ('extwrepeattime', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('tide', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='tide', null=True, blank=True, to=orm['flooding_lib.WaterlevelSet'])),
            ('tstorm', self.gf('django.db.models.fields.FloatField')(default=None, null=True, blank=True)),
            ('tpeak', self.gf('django.db.models.fields.FloatField')(default=None, null=True, blank=True)),
            ('tdeltaphase', self.gf('django.db.models.fields.FloatField')(default=None, null=True, blank=True)),
            ('manualwaterlevelinput', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
        ))
        db.send_create_signal('flooding_lib', ['ScenarioBreach'])

        # Adding unique constraint on 'ScenarioBreach', fields ['scenario', 'breach']
        db.create_unique('flooding_scenariobreach', ['scenario_id', 'breach_id'])

        # Adding model 'ScenarioCutoffLocation'
        db.create_table('flooding_scenariocutofflocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Scenario'])),
            ('cutofflocation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.CutoffLocation'])),
            ('action', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('tclose', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('flooding_lib', ['ScenarioCutoffLocation'])

        # Adding unique constraint on 'ScenarioCutoffLocation', fields ['scenario', 'cutofflocation']
        db.create_unique('flooding_scenariocutofflocation', ['scenario_id', 'cutofflocation_id'])

        # Adding model 'Program'
        db.create_table('flooding_program', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('flooding_lib', ['Program'])

        # Adding model 'ResultType'
        db.create_table('flooding_resulttype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('shortname_dutch', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('overlaytype', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('color_mapping_name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('program', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Program'])),
            ('content_names_re', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
        ))
        db.send_create_signal('flooding_lib', ['ResultType'])

        # Adding model 'Result'
        db.create_table('flooding_result', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Scenario'])),
            ('resulttype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.ResultType'])),
            ('resultloc', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('deltat', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('resultpngloc', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('startnr', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('firstnr', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('lastnr', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bbox', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(null=True, blank=True)),
        ))
        db.send_create_signal('flooding_lib', ['Result'])

        # Adding unique constraint on 'Result', fields ['scenario', 'resulttype']
        db.create_unique('flooding_result', ['scenario_id', 'resulttype_id'])

        # Adding model 'CutoffLocationSobekModelSetting'
        db.create_table('flooding_cutofflocationsobekmodelsetting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cutofflocation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.CutoffLocation'])),
            ('sobekmodel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.SobekModel'])),
            ('sobekid', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('flooding_lib', ['CutoffLocationSobekModelSetting'])

        # Adding model 'TaskType'
        db.create_table('flooding_tasktype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('flooding_lib', ['TaskType'])

        # Adding model 'Task'
        db.create_table('flooding_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Scenario'])),
            ('remarks', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('tasktype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.TaskType'])),
            ('creatorlog', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('tstart', self.gf('django.db.models.fields.DateTimeField')()),
            ('tfinished', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('errorlog', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('successful', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
        ))
        db.send_create_signal('flooding_lib', ['Task'])

        # Adding model 'TaskExecutor'
        db.create_table('flooding_taskexecutor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('ipaddress', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('port', self.gf('django.db.models.fields.IntegerField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('revision', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('seq', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('flooding_lib', ['TaskExecutor'])

        # Adding unique constraint on 'TaskExecutor', fields ['ipaddress', 'port']
        db.create_unique('flooding_taskexecutor', ['ipaddress', 'port'])

        # Adding unique constraint on 'TaskExecutor', fields ['name', 'seq']
        db.create_unique('flooding_taskexecutor', ['name', 'seq'])

        # Adding M2M table for field tasktypes on 'TaskExecutor'
        db.create_table('flooding_taskexecutor_tasktypes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('taskexecutor', models.ForeignKey(orm['flooding_lib.taskexecutor'], null=False)),
            ('tasktype', models.ForeignKey(orm['flooding_lib.tasktype'], null=False))
        ))
        db.create_unique('flooding_taskexecutor_tasktypes', ['taskexecutor_id', 'tasktype_id'])

        # Adding model 'Scenario_PresentationLayer'
        db.create_table('flooding_scenario_presentationlayer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Scenario'])),
            ('presentationlayer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.PresentationLayer'])),
        ))
        db.send_create_signal('flooding_lib', ['Scenario_PresentationLayer'])

        # Adding model 'ResultType_PresentationType'
        db.create_table('flooding_resulttype_presentationtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resulttype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.ResultType'])),
            ('presentationtype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_presentation.PresentationType'])),
            ('remarks', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('flooding_lib', ['ResultType_PresentationType'])

        # Adding model 'Strategy'
        db.create_table('flooding_strategy', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Region'], null=True, blank=True)),
            ('visible_for_loading', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('save_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('flooding_lib', ['Strategy'])

        # Adding model 'Measure'
        db.create_table('flooding_measure', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('reference_adjustment', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('adjustment', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal('flooding_lib', ['Measure'])

        # Adding M2M table for field strategy on 'Measure'
        db.create_table('flooding_measure_strategy', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('measure', models.ForeignKey(orm['flooding_lib.measure'], null=False)),
            ('strategy', models.ForeignKey(orm['flooding_lib.strategy'], null=False))
        ))
        db.create_unique('flooding_measure_strategy', ['measure_id', 'strategy_id'])

        # Adding model 'EmbankmentUnit'
        db.create_table('flooding_embankment_unit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('unit_id', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('original_height', self.gf('django.db.models.fields.FloatField')()),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flooding_lib.Region'])),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.LineStringField')()),
        ))
        db.send_create_signal('flooding_lib', ['EmbankmentUnit'])

        # Adding M2M table for field measure on 'EmbankmentUnit'
        db.create_table('flooding_embankment_unit_measure', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('embankmentunit', models.ForeignKey(orm['flooding_lib.embankmentunit'], null=False)),
            ('measure', models.ForeignKey(orm['flooding_lib.measure'], null=False))
        ))
        db.create_unique('flooding_embankment_unit_measure', ['embankmentunit_id', 'measure_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'TaskExecutor', fields ['name', 'seq']
        db.delete_unique('flooding_taskexecutor', ['name', 'seq'])

        # Removing unique constraint on 'TaskExecutor', fields ['ipaddress', 'port']
        db.delete_unique('flooding_taskexecutor', ['ipaddress', 'port'])

        # Removing unique constraint on 'Result', fields ['scenario', 'resulttype']
        db.delete_unique('flooding_result', ['scenario_id', 'resulttype_id'])

        # Removing unique constraint on 'ScenarioCutoffLocation', fields ['scenario', 'cutofflocation']
        db.delete_unique('flooding_scenariocutofflocation', ['scenario_id', 'cutofflocation_id'])

        # Removing unique constraint on 'ScenarioBreach', fields ['scenario', 'breach']
        db.delete_unique('flooding_scenariobreach', ['scenario_id', 'breach_id'])

        # Removing unique constraint on 'ExtraScenarioInfo', fields ['extrainfofield', 'scenario']
        db.delete_unique('flooding_extrascenarioinfo', ['extrainfofield_id', 'scenario_id'])

        # Removing unique constraint on 'ProjectGroupPermission', fields ['group', 'project', 'permission']
        db.delete_unique('flooding_projectgrouppermission', ['group_id', 'project_id', 'permission'])

        # Removing unique constraint on 'UserPermission', fields ['user', 'permission']
        db.delete_unique('flooding_userpermission', ['user_id', 'permission'])

        # Removing unique constraint on 'BreachSobekModel', fields ['sobekmodel', 'breach']
        db.delete_unique('flooding_breachsobekmodel', ['sobekmodel_id', 'breach_id'])

        # Removing unique constraint on 'Waterlevel', fields ['waterlevelset', 'time']
        db.delete_unique('flooding_waterlevel', ['waterlevelset_id', 'time'])

        # Deleting model 'Attachment'
        db.delete_table('flooding_attachment')

        # Deleting model 'SobekVersion'
        db.delete_table('flooding_sobekversion')

        # Deleting model 'SobekModel'
        db.delete_table('flooding_sobekmodel')

        # Deleting model 'CutoffLocation'
        db.delete_table('flooding_cutofflocation')

        # Deleting model 'ExternalWater'
        db.delete_table('flooding_externalwater')

        # Removing M2M table for field sobekmodels on 'ExternalWater'
        db.delete_table('flooding_externalwater_sobekmodels')

        # Removing M2M table for field cutofflocations on 'ExternalWater'
        db.delete_table('flooding_externalwater_cutofflocations')

        # Deleting model 'Dike'
        db.delete_table('flooding_dike')

        # Deleting model 'WaterlevelSet'
        db.delete_table('flooding_waterlevelset')

        # Deleting model 'Waterlevel'
        db.delete_table('flooding_waterlevel')

        # Deleting model 'Map'
        db.delete_table('flooding_map')

        # Deleting model 'Region'
        db.delete_table('flooding_region')

        # Removing M2M table for field maps on 'Region'
        db.delete_table('flooding_region_maps')

        # Removing M2M table for field sobekmodels on 'Region'
        db.delete_table('flooding_region_sobekmodels')

        # Removing M2M table for field cutofflocations on 'Region'
        db.delete_table('flooding_region_cutofflocations')

        # Deleting model 'RegionSet'
        db.delete_table('flooding_regionset')

        # Removing M2M table for field regions on 'RegionSet'
        db.delete_table('flooding_regionset_regions')

        # Deleting model 'Breach'
        db.delete_table('flooding_breach')

        # Deleting model 'BreachSobekModel'
        db.delete_table('flooding_breachsobekmodel')

        # Deleting model 'CutoffLocationSet'
        db.delete_table('flooding_cutofflocationset')

        # Removing M2M table for field cutofflocations on 'CutoffLocationSet'
        db.delete_table('flooding_cutofflocationset_cutofflocations')

        # Deleting model 'Project'
        db.delete_table('flooding_project')

        # Removing M2M table for field regionsets on 'Project'
        db.delete_table('flooding_project_regionsets')

        # Removing M2M table for field regions on 'Project'
        db.delete_table('flooding_project_regions')

        # Deleting model 'UserPermission'
        db.delete_table('flooding_userpermission')

        # Deleting model 'ProjectGroupPermission'
        db.delete_table('flooding_projectgrouppermission')

        # Deleting model 'PermissionProjectShapeDataLegend'
        db.delete_table('flooding_lib_permissionprojectshapedatalegend')

        # Deleting model 'PermissionProjectGridDataLegend'
        db.delete_table('flooding_lib_permissionprojectgriddatalegend')

        # Deleting model 'ExtraInfoField'
        db.delete_table('flooding_extrainfofield')

        # Deleting model 'ExtraScenarioInfo'
        db.delete_table('flooding_extrascenarioinfo')

        # Deleting model 'Scenario'
        db.delete_table('flooding_scenario')

        # Deleting model 'ScenarioBreach'
        db.delete_table('flooding_scenariobreach')

        # Deleting model 'ScenarioCutoffLocation'
        db.delete_table('flooding_scenariocutofflocation')

        # Deleting model 'Program'
        db.delete_table('flooding_program')

        # Deleting model 'ResultType'
        db.delete_table('flooding_resulttype')

        # Deleting model 'Result'
        db.delete_table('flooding_result')

        # Deleting model 'CutoffLocationSobekModelSetting'
        db.delete_table('flooding_cutofflocationsobekmodelsetting')

        # Deleting model 'TaskType'
        db.delete_table('flooding_tasktype')

        # Deleting model 'Task'
        db.delete_table('flooding_task')

        # Deleting model 'TaskExecutor'
        db.delete_table('flooding_taskexecutor')

        # Removing M2M table for field tasktypes on 'TaskExecutor'
        db.delete_table('flooding_taskexecutor_tasktypes')

        # Deleting model 'Scenario_PresentationLayer'
        db.delete_table('flooding_scenario_presentationlayer')

        # Deleting model 'ResultType_PresentationType'
        db.delete_table('flooding_resulttype_presentationtype')

        # Deleting model 'Strategy'
        db.delete_table('flooding_strategy')

        # Deleting model 'Measure'
        db.delete_table('flooding_measure')

        # Removing M2M table for field strategy on 'Measure'
        db.delete_table('flooding_measure_strategy')

        # Deleting model 'EmbankmentUnit'
        db.delete_table('flooding_embankment_unit')

        # Removing M2M table for field measure on 'EmbankmentUnit'
        db.delete_table('flooding_embankment_unit_measure')


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
        'flooding_lib.cutofflocationset': {
            'Meta': {'object_name': 'CutoffLocationSet', 'db_table': "'flooding_cutofflocationset'"},
            'cutofflocations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.CutoffLocation']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
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
        'flooding_lib.embankmentunit': {
            'Meta': {'object_name': 'EmbankmentUnit', 'db_table': "'flooding_embankment_unit'"},
            'geometry': ('django.contrib.gis.db.models.fields.LineStringField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measure': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.Measure']", 'symmetrical': 'False'}),
            'original_height': ('django.db.models.fields.FloatField', [], {}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Region']"}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'unit_id': ('django.db.models.fields.CharField', [], {'max_length': '20'})
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
            'maxlevel': ('django.db.models.fields.FloatField', [], {'default': '15'}),
            'minlevel': ('django.db.models.fields.FloatField', [], {'default': '-10'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sobekmodels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.SobekModel']", 'symmetrical': 'False', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_lib.extrainfofield': {
            'Meta': {'object_name': 'ExtraInfoField', 'db_table': "'flooding_extrainfofield'"},
            'header': ('django.db.models.fields.IntegerField', [], {'default': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'use_in_scenario_overview': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'flooding_lib.extrascenarioinfo': {
            'Meta': {'unique_together': "(('extrainfofield', 'scenario'),)", 'object_name': 'ExtraScenarioInfo', 'db_table': "'flooding_extrascenarioinfo'"},
            'extrainfofield': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.ExtraInfoField']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Scenario']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        'flooding_lib.measure': {
            'Meta': {'object_name': 'Measure', 'db_table': "'flooding_measure'"},
            'adjustment': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'reference_adjustment': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'strategy': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.Strategy']", 'symmetrical': 'False'})
        },
        'flooding_lib.permissionprojectgriddatalegend': {
            'Meta': {'object_name': 'PermissionProjectGridDataLegend'},
            'griddatalegend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Project']"})
        },
        'flooding_lib.permissionprojectshapedatalegend': {
            'Meta': {'object_name': 'PermissionProjectShapeDataLegend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Project']"}),
            'shapedatalegend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_visualization.ShapeDataLegend']"})
        },
        'flooding_lib.program': {
            'Meta': {'object_name': 'Program', 'db_table': "'flooding_program'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_lib.project': {
            'Meta': {'ordering': "('friendlyname', 'name', 'owner')", 'object_name': 'Project', 'db_table': "'flooding_project'"},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'friendlyname': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.Region']", 'symmetrical': 'False', 'blank': 'True'}),
            'regionsets': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.RegionSet']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'flooding_lib.projectgrouppermission': {
            'Meta': {'unique_together': "(('group', 'project', 'permission'),)", 'object_name': 'ProjectGroupPermission', 'db_table': "'flooding_projectgrouppermission'"},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission': ('django.db.models.fields.IntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Project']"})
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
        'flooding_lib.result': {
            'Meta': {'unique_together': "(('scenario', 'resulttype'),)", 'object_name': 'Result', 'db_table': "'flooding_result'"},
            'bbox': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True', 'blank': 'True'}),
            'deltat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'firstnr': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastnr': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'resultloc': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'resultpngloc': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'resulttype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.ResultType']"}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Scenario']"}),
            'startnr': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'flooding_lib.resulttype': {
            'Meta': {'object_name': 'ResultType', 'db_table': "'flooding_resulttype'"},
            'color_mapping_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'content_names_re': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'overlaytype': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'presentationtype': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_presentation.PresentationType']", 'through': "orm['flooding_lib.ResultType_PresentationType']", 'symmetrical': 'False'}),
            'program': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Program']"}),
            'shortname_dutch': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        },
        'flooding_lib.resulttype_presentationtype': {
            'Meta': {'object_name': 'ResultType_PresentationType', 'db_table': "'flooding_resulttype_presentationtype'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.PresentationType']"}),
            'remarks': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'resulttype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.ResultType']"})
        },
        'flooding_lib.scenario': {
            'Meta': {'ordering': "('name', 'project', 'owner')", 'object_name': 'Scenario', 'db_table': "'flooding_scenario'"},
            'approvalobject': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['approvaltool.ApprovalObject']", 'null': 'True', 'blank': 'True'}),
            'breaches': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.Breach']", 'through': "orm['flooding_lib.ScenarioBreach']", 'symmetrical': 'False'}),
            'calcpriority': ('django.db.models.fields.IntegerField', [], {'default': '20'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'cutofflocations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_lib.CutoffLocation']", 'symmetrical': 'False', 'through': "orm['flooding_lib.ScenarioCutoffLocation']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'migrated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'presentationlayer': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flooding_presentation.PresentationLayer']", 'through': "orm['flooding_lib.Scenario_PresentationLayer']", 'symmetrical': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Project']"}),
            'remarks': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'sobekmodel_inundation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.SobekModel']"}),
            'status_cache': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'strategy': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['flooding_lib.Strategy']", 'null': 'True', 'blank': 'True'}),
            'tsim': ('django.db.models.fields.FloatField', [], {}),
            'workflow_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_worker.WorkflowTemplate']", 'db_column': "'workflow_template'"})
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
        'flooding_lib.sobekmodel': {
            'Meta': {'object_name': 'SobekModel', 'db_table': "'flooding_sobekmodel'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'embankment_damage_shape': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        'flooding_lib.task': {
            'Meta': {'object_name': 'Task', 'db_table': "'flooding_task'"},
            'creatorlog': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'errorlog': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.Scenario']"}),
            'successful': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'tasktype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.TaskType']"}),
            'tfinished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'tstart': ('django.db.models.fields.DateTimeField', [], {})
        },
        'flooding_lib.taskexecutor': {
            'Meta': {'unique_together': "(('ipaddress', 'port'), ('name', 'seq'))", 'object_name': 'TaskExecutor', 'db_table': "'flooding_taskexecutor'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ipaddress': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'port': ('django.db.models.fields.IntegerField', [], {}),
            'revision': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'seq': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'tasktypes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['flooding_lib.TaskType']", 'null': 'True', 'blank': 'True'})
        },
        'flooding_lib.tasktype': {
            'Meta': {'object_name': 'TaskType', 'db_table': "'flooding_tasktype'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'flooding_lib.userpermission': {
            'Meta': {'unique_together': "(('user', 'permission'),)", 'object_name': 'UserPermission', 'db_table': "'flooding_userpermission'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'flooding_lib.waterlevel': {
            'Meta': {'unique_together': "(('waterlevelset', 'time'),)", 'object_name': 'Waterlevel', 'db_table': "'flooding_waterlevel'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.FloatField', [], {}),
            'value': ('django.db.models.fields.FloatField', [], {}),
            'waterlevelset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_lib.WaterlevelSet']"})
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
        'flooding_presentation.field': {
            'Meta': {'object_name': 'Field', 'db_table': "'presentation_field'"},
            'field_type': ('django.db.models.fields.IntegerField', [], {}),
            'friendlyname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_main_value_field': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name_in_source': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flooding_presentation.PresentationType']"}),
            'source_type': ('django.db.models.fields.IntegerField', [], {})
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
        'flooding_visualization.shapedatalegend': {
            'Meta': {'object_name': 'ShapeDataLegend', 'db_table': "'visualization_shapedatalegend'"},
            'color': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'color_set'", 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'color_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'color_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'presentationtype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'presentationtype_set'", 'to': "orm['flooding_presentation.PresentationType']"}),
            'rotation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rotation_set'", 'null': 'True', 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'rotation_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rotation_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"}),
            'shadowheight': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shadowheight_set'", 'null': 'True', 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'shadowheight_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shadowheight_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"}),
            'size': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'size_set'", 'null': 'True', 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'size_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'size_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"}),
            'symbol': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'symbol_set'", 'null': 'True', 'to': "orm['flooding_visualization.ValueVisualizerMap']"}),
            'symbol_field': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'symbol_field_set'", 'null': 'True', 'to': "orm['flooding_presentation.Field']"})
        },
        'flooding_visualization.valuevisualizermap': {
            'Meta': {'object_name': 'ValueVisualizerMap', 'db_table': "'visualization_valuevisualizermap'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interpolation': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'valuetype': ('django.db.models.fields.IntegerField', [], {}),
            'visualizertype': ('django.db.models.fields.IntegerField', [], {})
        },
        'flooding_worker.workflowtemplate': {
            'Meta': {'object_name': 'WorkflowTemplate'},
            'code': ('django.db.models.fields.IntegerField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['flooding_lib']
