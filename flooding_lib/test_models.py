import factory
#import mock

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from flooding_lib import models

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


class TestProject(TestCase):
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
