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
