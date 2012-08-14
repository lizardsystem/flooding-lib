"""Tests for flooding_lib/models.py."""

from __future__ import unicode_literals

import factory
import mock

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from flooding_lib import models
from flooding_lib.tools.approvaltool.models import ApprovalObjectType
from flooding_lib.tools.approvaltool.models import ApprovalRule
from flooding_lib.tools.approvaltool.models import ApprovalObjectState
from flooding_lib.tools.importtool import models as importmodels

from flooding_lib.tools.importtool.test_models import InputFieldF

MULTIPOLYGON = 'MULTIPOLYGON(((0 0,4 0,4 4,0 4,0 0),(1 1,2 1,2 2,1 2,1 1)))'
POINT = 'POINT(0 0)'


class FakeObject(object):
    """Object with some attributes"""
    def __init__(self, **kwargs):
        for attribute, value in kwargs.iteritems():
            setattr(self, attribute, value)

## Model factories


class ContentTypeF(factory.Factory):
    FACTORY_FOR = ContentType


class AttachmentF(factory.Factory):
    FACTORY_FOR = models.Attachment

    content_type = ContentTypeF.create()
    object_id = 1


class SobekVersionF(factory.Factory):
    FACTORY_FOR = models.SobekVersion


class SobekModelF(factory.Factory):
    FACTORY_FOR = models.SobekModel

    sobekversion = SobekVersionF.create()
    sobekmodeltype = 1
    model_case = 0
    model_srid = 28992


class CutoffLocationF(factory.Factory):
    FACTORY_FOR = models.CutoffLocation

    bottomlevel = 0.0
    width = 1.0
    type = 1  # sluis (_('lock'))
    geom = POINT


class DikeF(factory.Factory):
    FACTORY_FOR = models.Dike


class ExtraInfoFieldF(factory.Factory):
    FACTORY_FOR = models.ExtraInfoField

    name = 'dummy'
    use_in_scenario_overview = True
    header = models.ExtraInfoField.HEADER_SCENARIO
    position = 0


class ExtraScenarioInfoF(factory.Factory):
    FACTORY_FOR = models.ExtraScenarioInfo

    extrainfofield = ExtraInfoFieldF(name='forextrascenarioinfo')
    scenario = FakeObject()
    value = None


class ScenarioF(factory.Factory):
    FACTORY_FOR = models.Scenario

    owner = User.objects.get_or_create(username='remco')[0]
    tsim = 0.0


class ProjectF(factory.Factory):
    FACTORY_FOR = models.Project

    owner = User.objects.get_or_create(username='remco')[0]


class ExternalWaterF(factory.Factory):
    FACTORY_FOR = models.ExternalWater

    name = 'dewoeligebaren'
    type = models.ExternalWater.TYPE_SEA

    deftsim = 0.0


class RegionF(factory.Factory):
    FACTORY_FOR = models.Region

    name = 'Utrecht'
    longname = 'Uuuuuuutrecht'
    geom = MULTIPOLYGON


class RegionSetF(factory.Factory):
    FACTORY_FOR = models.RegionSet

    name = "testregionset"


class DikeF(factory.Factory):
    FACTORY_FOR = models.Dike

    name = "Een dijk"


class BreachF(factory.Factory):
    FACTORY_FOR = models.Breach

    name = 'testname'

    externalwater = factory.LazyAttribute(lambda obj: ExternalWaterF.create())
    region = factory.LazyAttribute(lambda obj: RegionF.create())
    dike = factory.LazyAttribute(lambda obj: DikeF.create())
    defaulttide = factory.LazyAttribute(lambda obj: WaterlevelSetF.create())

    levelnormfrequency = 1
    groundlevel = 1
    defrucritical = 0
    internalnode = 'POINT(0 0)'
    externalnode = 'POINT(0 0)'

    geom = 'POINT(0 0)'


class WaterlevelSetF(factory.Factory):
    FACTORY_FOR = models.WaterlevelSet

    type = models.WaterlevelSet.WATERLEVELSETTYPE_UNDEFINED


class ScenarioBreachF(factory.Factory):
    FACTORY_FOR = models.ScenarioBreach

    scenario = factory.LazyAttribute(lambda obj: ScenarioF.create())
    breach = factory.LazyAttribute(lambda obj: BreachF.create())
    waterlevelset = factory.LazyAttribute(lambda obj: WaterlevelSetF.create())

    widthbrinit = 1
    methstartbreach = 1
    tstartbreach = 1
    hstartbreach = 1
    brdischcoef = 1
    brf1 = 1
    brf2 = 1
    bottomlevelbreach = 1
    ucritical = 1
    pitdepth = 1
    tmaxdepth = 1
    extwmaxlevel = 1


class WaterlevelF(factory.Factory):
    FACTORY_FOR = models.Waterlevel

    time = 0
    value = 0


class MapF(factory.Factory):
    FACTORY_FOR = models.Map

    name = "testmap"


class TaskExecutorF(factory.Factory):
    FACTORY_FOR = models.TaskExecutor

    name = "testtaskexecutor"


class ResultTypePresentationTypeF(factory.Factory):
    FACTORY_FOR = models.ResultType_PresentationType

    remarks = "testremarks"


class StrategyF(factory.Factory):
    FACTORY_FOR = models.Strategy

    name = "teststrategy"


class MeasureF(factory.Factory):
    FACTORY_FOR = models.Measure

    name = "testmeasure"


class EmbankmentUnitF(factory.Factory):
    FACTORY_FOR = models.EmbankmentUnit

    unit_id = "test"

## Test cases


class TestHelperFunctions(TestCase):
    def testColorToHex_CorrectInput(self):
        self.assertEquals(
            "#00FF00",
            models.convert_color_to_hex((0, 255, 0)))

    def testAttachmentPath_CorrectInput(self):
        instance = FakeObject(
            content_type=u'test_content_type',
            object_id=1234)

        self.assertEquals(
            'attachments/test_content_type/1234/filename.zip',
            models.get_attachment_path(instance, 'filename.zip'))


class TestAttachment(TestCase):
    def testFilename(self):
        path = 'some/path/with/several.periods.txt'
        filename = 'several.periods.txt'

        attachment = AttachmentF()
        attachment.file = FakeObject(name=path)

        self.assertEquals(
            attachment.filename, filename)

    def test_has_unicode(self):
        """Check that with __unicode__ returns is in fact unicode."""
        attachment = AttachmentF(name=u"some name")
        self.assertEquals(type(attachment.__unicode__()), unicode)


class TestSobekVersion(TestCase):
    def test_has_unicode(self):
        """Check that with __unicode__ returns is in fact unicode."""
        sobekversion = SobekVersionF(name=u"some name")
        self.assertEquals(type(sobekversion.__unicode__()), unicode)


class TestSobekModel(TestCase):
    def test_has_unicode(self):
        sobekmodel = SobekModelF()
        self.assertEquals(type(sobekmodel.__unicode__()), unicode)

    def test_get_summary_str(self):
        """Check that it returns something and is Unicode"""
        sobekmodel = SobekModelF()
        summary = sobekmodel.get_summary_str()
        self.assertEquals(type(summary), unicode)
        self.assertTrue(summary)


class TestCutoffLocation(TestCase):
    def test_has_unicode(self):
        cutofflocation = CutoffLocationF()
        self.assertEquals(type(cutofflocation.__unicode__()), unicode)

    def test_isinternal(self):
        """Returns if CutoffLocation is an internal cutoff location

        True if it is exclusively connected to region's,
        False if it is exclusively connected to external waters
        None else
        """
        cutofflocation = CutoffLocationF()
        # Should be None because we didn't connect it at all
        self.assertEquals(cutofflocation.isinternal(), None)

    def test_isinternal_connected_to_region(self):
        cutofflocation = CutoffLocationF.create()
        cutofflocation.region_set.add(RegionF.create())

        self.assertEquals(cutofflocation.isinternal(), True)

    def test_isinternal_connected_to_externalwater(self):
        cutofflocation = CutoffLocationF.create()
        cutofflocation.externalwater_set.add(ExternalWaterF.create())

        self.assertEquals(cutofflocation.isinternal(), False)

    def test_isinternal_connected_to_both(self):
        cutofflocation = CutoffLocationF.create()
        cutofflocation.region_set.add(RegionF.create())
        cutofflocation.externalwater_set.add(ExternalWaterF.create())

        self.assertEquals(cutofflocation.isinternal(), None)

    def test_getdeftclose_seconds(self):
        cutofflocation = CutoffLocationF.build(deftclose=1)
        self.assertEquals(cutofflocation.get_deftclose_seconds(), 86400)


class TestExternalWater(TestCase):
    def test_has_unicode(self):
        externalwater = ExternalWaterF.build()
        self.assertEquals(type(externalwater.__unicode__()), unicode)


class TestDike(TestCase):
    def test_has_unicode(self):
        dike = DikeF.build()
        self.assertEquals(type(dike.__unicode__()), unicode)


class TestWaterlevelSet(TestCase):
    def test_has_unicode(self):
        waterlevelset = WaterlevelSetF.build()
        self.assertEquals(type(waterlevelset.__unicode__()), unicode)


class TestWaterlevel(TestCase):
    def test_has_unicode(self):
        waterlevel = WaterlevelF.build(
            waterlevelset=WaterlevelSetF.create())

        self.assertEquals(type(waterlevel.__unicode__()), unicode)


class TestRegion(TestCase):
    def test_unicode_with_long_name(self):
        region = RegionF.build(longname="whee")

        uni = region.__unicode__()

        self.assertEquals(uni, "whee")
        self.assertTrue(isinstance(uni, unicode))

    def test_unicode_without_long_name(self):
        region = RegionF.build(
            longname=None, name="whe")

        uni = region.__unicode__()

        self.assertEquals(uni, "whe")
        self.assertTrue(isinstance(uni, unicode))


class TestRegionSet(TestCase):
    def test_has_unicode(self):
        regionset = RegionSetF.build()
        uni = regionset.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))

    def test_get_all_regions_empty(self):
        regionset = RegionSetF.create()

        self.assertEquals(len(regionset.get_all_regions()), 0)

    def test_get_all_regions_returns_own_regions(self):
        region = RegionF.create()
        regionset = RegionSetF.create()
        regionset.regions.add(region)

        all_regions = regionset.get_all_regions(filter_active=None)
        self.assertEquals(len(all_regions), 1)
        self.assertTrue(region in all_regions)

    def test_get_all_regions_returns_descendants_regions(self):
        region = RegionF.create()
        regionsetparent = RegionSetF.create()
        regionsetchild = RegionSetF.create(parent=regionsetparent)
        regionsetchild.regions.add(region)

        all_regions = regionsetparent.get_all_regions(filter_active=None)
        self.assertEquals(len(all_regions), 1)
        self.assertTrue(region in all_regions)

    def test_get_all_regions_returns_descendants_regions2(self):
        region = RegionF.create()
        regionsetparent = RegionSetF.create()
        regionsetchild = RegionSetF.create(parent=regionsetparent)
        regionsetgrandchild = RegionSetF.create(parent=regionsetchild)
        regionsetgrandchild.regions.add(region)

        all_regions = regionsetparent.get_all_regions(filter_active=None)
        self.assertEquals(len(all_regions), 1)
        self.assertTrue(region in all_regions)

    def test_get_all_regions_returns_region_only_once(self):
        region = RegionF.create()

        regionsetparent = RegionSetF.create()
        regionsetparent.regions.add(region)
        regionsetchild1 = RegionSetF.create(parent=regionsetparent)
        regionsetchild1.regions.add(region)
        regionsetchild2 = RegionSetF.create(parent=regionsetparent)
        regionsetchild2.regions.add(region)

        all_regions = regionsetparent.get_all_regions(filter_active=None)
        self.assertTrue(len(all_regions), 1)

    def test_get_all_regions_filter_active_works(self):
        regionset = RegionSetF.create()
        regionset.regions.add(RegionF.create(active=True))
        regionset.regions.add(RegionF.create(active=False))

        regions = regionset.get_all_regions(filter_active=False)
        self.assertEquals(len(regions), 1)
        self.assertFalse(regions[0].active)

    def test_get_all_regions_sorting_works(self):
        regionset = RegionSetF.create()
        regionset.regions.add(RegionF.create(name='B'))
        regionset.regions.add(RegionF.create(name='A'))
        regionset.regions.add(RegionF.create(name='C'))

        regions = regionset.get_all_regions(filter_active=None)
        self.assertEquals(len(regions), 3)
        self.assertEquals(regions[0].name, 'A')
        self.assertEquals(regions[1].name, 'B')
        self.assertEquals(regions[2].name, 'C')


class TestBreach(TestCase):
    """Tests for Breach model."""
    def test_has_unicode(self):
        """Does the __unicode__ method return unicode."""
        breach = BreachF.build()
        uni = breach.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestMap(TestCase):
    def test_has_unicode(self):
        map = MapF.build()
        uni = map.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestScenario(TestCase):
    def setUp(self):
        self.aot = ApprovalObjectType.objects.create(
            type=ApprovalObjectType.TYPE_PROJECT)
        self.rule = ApprovalRule.objects.create(
            name="test_rule",
            description="test",
            position=0)
        self.aot.approvalrule.add(self.rule)

    def testMainProject(self):
        """Use set_project to set a scenario's main project, then use the
        main_project property to see that it is returned correctly."""

        scenario = ScenarioF.create()
        project = ProjectF.create()

        scenario.set_project(project)
        self.assertEquals(project.pk, scenario.main_project.pk)

    def testGetMainProject(self):
        """A scenario may have more than one project associated with
        it. If it has, scenario.main_project should be the first of
        them."""

        scenario = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()

        scenario.set_project(project1)
        project2.add_scenario(scenario)
        scenario.save()

        main_project = scenario.main_project
        self.assertEquals(main_project.pk, project1.pk)

    def testSettingProjectTwiceRaisesValueError(self):
        scenario = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()

        scenario.set_project(project1)
        self.assertRaises(
            ValueError, lambda: scenario.set_project(project2))

    def testAllProjects(self):
        scenario = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()
        scenario.set_project(project1)
        project2.add_scenario(scenario)

        projects = scenario.all_projects()
        self.assertEqual(len(projects), 2)

        ids = set(project.id for project in projects)
        self.assertEqual(len(ids), 2)
        self.assertTrue(project1.id in ids)
        self.assertTrue(project2.id in ids)

    def test_in_project_list(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        scenarios = models.Scenario.in_project_list(
            models.Project.objects.all())
        self.assertEquals(scenarios.count(), 1)
        self.assertEquals(scenario.id, scenarios[0].id)

    def test_update_status_new_scenario(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        scenario.update_status()
        self.assertEquals(scenario.status_cache, models.Scenario.STATUS_NONE)

    def test_main_approval_object_always_same(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        # There was a bug because they weren't saved
        ao1 = scenario.main_approval_object()
        ao2 = scenario.main_approval_object()

        self.assertEquals(ao1, ao2)

    def test_update_status_scenario_one_task(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        tasktype = models.TaskType.objects.create(
            name='calculate sobek',
            id=models.TaskType.TYPE_SCENARIO_CREATE)

        models.Task.create_fake(
            scenario=scenario,
            task_type=tasktype.id,
            remarks="test",
            creatorlog="test")

        scenario.update_status()
        self.assertEquals(
            scenario.status_cache, models.Scenario.STATUS_WAITING)

    def test_update_scenario_disapprove(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        tasktype = models.TaskType.objects.create(
            name='calculate sobek',
            id=models.TaskType.TYPE_SCENARIO_CREATE)

        models.Task.create_fake(
            scenario=scenario,
            task_type=tasktype.id,
            remarks="test",
            creatorlog="test")

        approvalobject = scenario.main_approval_object()
        aos = ApprovalObjectState.objects.get(
            approvalobject=approvalobject,
            approvalrule=self.rule)
        aos.successful = False
        aos.save()

        scenario.update_status()

        self.assertEquals(
            scenario.status_cache, models.Scenario.STATUS_DISAPPROVED)

    def test_update_scenario_approve(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        tasktype = models.TaskType.objects.create(
            name='calculate sobek',
            id=models.TaskType.TYPE_SCENARIO_CREATE)

        models.Task.create_fake(
            scenario=scenario,
            task_type=tasktype.id,
            remarks="test",
            creatorlog="test")

        approvalobject = scenario.main_approval_object()
        aos = ApprovalObjectState.objects.get(
            approvalobject=approvalobject,
            approvalrule=self.rule)
        aos.successful = True
        aos.save()

        scenario.update_status()

        self.assertEquals(
            scenario.status_cache, models.Scenario.STATUS_APPROVED)

    def test_update_scenario_deleted(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        tasktype = models.TaskType.objects.create(
            name='calculate sobek',
            id=models.TaskType.TYPE_SCENARIO_DELETE)

        models.Task.create_fake(
            scenario=scenario,
            task_type=tasktype.id,
            remarks="test",
            creatorlog="test")

        # Approve or disapprove shouldn't matter, we test approved
        approvalobject = scenario.main_approval_object()
        aos = ApprovalObjectState.objects.get(
            approvalobject=approvalobject,
            approvalrule=self.rule)
        aos.successful = True
        aos.save()

        scenario.update_status()

        self.assertEquals(
            scenario.status_cache, models.Scenario.STATUS_DELETED)

    def test_set_value_raises_not_implemented(self):
        """The function supports only a few destination tables, should
        raise NotImplementedError if another table is asked for."""
        scenario = ScenarioF.build()
        inputfield = InputFieldF.build(
            destination_table="Project")

        self.assertRaises(
            NotImplementedError,
            lambda: scenario.set_value_for_inputfield(inputfield, None))

    def test_set_value_for_inputfield_on_scenario_sets_value(self):
        """See if a value is really set."""
        scenario = ScenarioF.create()

        inputfield = InputFieldF.build(
            destination_table='Scenario',
            destination_field='name',
            type=importmodels.InputField.TYPE_STRING)

        value_object = inputfield.build_value_object()
        value_object.set("new name")

        scenario.set_value_for_inputfield(inputfield, value_object)

        # Was it saved?
        scenario = models.Scenario.objects.get(pk=scenario.id)

        self.assertEquals(scenario.name, "new name")

    def test_set_value_for_inputfield_sets_scenariobreach_value(self):
        """See if an inputfield using ScenarioBreach is set."""
        scenario = ScenarioF.create()
        ScenarioBreachF.create(scenario=scenario)

        inputfield = InputFieldF.build(
            destination_table='ScenarioBreach',
            destination_field='widthbrinit',
            type=importmodels.InputField.TYPE_FLOAT)

        value_object = inputfield.build_value_object()
        value_object.set(0.5)

        scenario.set_value_for_inputfield(inputfield, value_object)

        # Was it saved?
        if hasattr(scenario, '_data_objects'):
            del scenario._data_objects

        scenariobreach = scenario.gather_data_objects()['scenariobreach']
        self.assertEquals(scenariobreach.widthbrinit, 0.5)

    def test_set_value_for_inputfield_sets_extrascenarioinfo(self):
        """See if an inputfield using ExtraScenarioInfo is set."""
        scenario = ScenarioF.create()
        ExtraInfoFieldF.create(name="test")
        inputfield = InputFieldF.build(
            destination_table='ExtraScenarioInfo',
            destination_field='test',
            type=importmodels.InputField.TYPE_FLOAT)

        value_object = inputfield.build_value_object()
        value_object.set(0.5)

        scenario.set_value_for_inputfield(inputfield, value_object)

        # Was it saved?
        esi = models.ExtraScenarioInfo.get(scenario, 'test')
        self.assertEquals(esi.value, u'0.5')


class TestProject(TestCase):
    def setUp(self):
        ApprovalObjectType.objects.create(
            type=ApprovalObjectType.TYPE_PROJECT)

    def testAddScenarioValueErrorIfScenarioHasNoMainProject(self):
        """You can't add a scenario to another project if it doesn't have a
        main project yet."""
        scenario = ScenarioF.create()
        project = ProjectF.create()

        self.assertRaises(ValueError, lambda: project.add_scenario(scenario))

    def testAddScenarioValueErrorIfAddedToMainProject(self):
        """You can't add a scenario to a project if that project is already
        the scenario's main project."""

        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        self.assertRaises(ValueError, lambda: project.add_scenario(scenario))

    def testSetProject(self):
        """Set a scenario, see that count_scenarios returns 1."""
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        self.assertEquals(project.count_scenarios(), 1)

    def testAddScenario(self):
        """Add a scenario, see that count_scenarios returns 1."""
        scenario = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()
        scenario.set_project(project1)
        project2.add_scenario(scenario)

        self.assertEquals(project2.count_scenarios(), 1)

    def test_in_scenario_list(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        projects = models.Project.in_scenario_list(
            models.Scenario.objects.all())

        self.assertEquals(projects.count(), 1)
        self.assertEquals(project.id, projects[0].id)

    def test_all_scenarios(self):
        scenario1 = ScenarioF.create()
        scenario2 = ScenarioF.create()
        project = ProjectF.create()
        scenario1.set_project(project)
        scenario2.set_project(project)

        scenarios = project.all_scenarios()
        self.assertEquals(scenarios.count(), 2)

        # We don't test anything about order, that's not specified
        scenarioset = set(scenario.id for scenario in scenarios)
        self.assertTrue(scenario1.id in scenarioset)
        self.assertTrue(scenario2.id in scenarioset)

    def test_original_scenarios(self):
        # Three scenarios; two are originally in project1,
        # the other is originally in project2 and was added to project1.
        # Function should return the first two.
        scenario1 = ScenarioF.create()
        scenario2 = ScenarioF.create()
        scenario3 = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()

        scenario1.set_project(project1)
        scenario2.set_project(project1)
        scenario3.set_project(project2)
        project1.add_scenario(scenario3)

        scenarios = project1.original_scenarios()

        self.assertEquals(scenarios.count(), 2)
        scenarioset = set(scenario.id for scenario in scenarios)
        self.assertTrue(scenario1.id in scenarioset)
        self.assertTrue(scenario2.id in scenarioset)

    def test_original_scenarios_deleted(self):
        """original_scenarios() shouldn't return deleted scenarios."""
        scenario = ScenarioF.create(
            status_cache=models.Scenario.STATUS_DELETED)
        project = ProjectF.create()
        scenario.set_project(project)

        scenarios = project.original_scenarios()

        self.assertEquals(scenarios.count(), 0)


class TestFindImportedValue(TestCase):
    def test_get_integer_from_scenario(self):
        scenario = FakeObject(field=3)

        inputfield = InputFieldF.build(
            destination_table='Scenario',
            destination_field='field')

        retvalue = models.find_imported_value(
            inputfield, {'scenario': scenario})
        self.assertEquals(retvalue, 3)

    def test_simple_scenario_info(self):
        scenario = ScenarioF.create()
        fieldname = 'test'
        value = 3

        extrainfofield = ExtraInfoFieldF.create(name=fieldname)
        ExtraScenarioInfoF.create(
            scenario=scenario,
            extrainfofield=extrainfofield,
            value=value)

        inputfield = InputFieldF.build(
            destination_table='ExtraScenarioInfo',
            destination_field=fieldname)

        retvalue = models.find_imported_value(
            inputfield, {'scenario': scenario})
        self.assertEquals(retvalue, 3)

    def test_999(self):
        scenario = ScenarioF.create()
        fieldname = 'test'
        value = '-999'

        extrainfofield = ExtraInfoFieldF.create(name=fieldname)
        ExtraScenarioInfoF.create(
            scenario=scenario,
            extrainfofield=extrainfofield,
            value=value)

        inputfield = InputFieldF.build(
            destination_table='ExtraScenarioInfo',
            destination_field=fieldname,
            type=importmodels.InputField.TYPE_STRING)

        retvalue = models.find_imported_value(
            inputfield, {'scenario': scenario})
        self.assertEquals(retvalue, None)

    def test_xy(self):
        WGS_X = 10
        WGS_Y = 20
        RD_X = 110
        RD_Y = 120

        breach = FakeObject(
            geom=FakeObject(
                x=WGS_X, y=WGS_Y))

        inputfieldx = InputFieldF.build(
            name='X coordinaat',
            destination_table='Breach',
            destination_field='geom')
        inputfieldy = InputFieldF.build(
            name='Y coordinaat',
            destination_table='Breach',
            destination_field='geom')

        with mock.patch(
            'flooding_lib.coordinates.wgs84_to_rd',
            return_value=(RD_X, RD_Y)):
            retvaluex = models.find_imported_value(
                inputfieldx, {'breach': breach})
            retvaluey = models.find_imported_value(
                inputfieldy, {'breach': breach})
            self.assertEquals(retvaluex, RD_X)
            self.assertEquals(retvaluey, RD_Y)


class TestTaskExecutor(TestCase):
    def test_has_unicode(self):
        task_executor = TaskExecutorF.build()

        uni = task_executor.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestResultTypePresentationType(TestCase):
    def test_has_unicode(self):
        rtpt = ResultTypePresentationTypeF.build()
        uni = rtpt.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestStrategy(TestCase):
    def test_has_unicode(self):
        strategy = StrategyF.build()

        uni = strategy.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestMeasure(TestCase):
    def test_has_unicode(self):
        measure = MeasureF.build()

        uni = measure.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestEmbankmentUnit(TestCase):
    def test_has_unicode(self):
        embankment_unit = EmbankmentUnitF.build()

        uni = embankment_unit.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))
