import factory
from mock import MagicMock

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.test.client import RequestFactory

from flooding_lib import permission_manager
from flooding_lib.models import UserPermission
from flooding_lib.models import ProjectGroupPermission
from flooding_lib.models import Scenario
from flooding_lib.models import ScenarioProject
from flooding_lib.tests.test_models import ScenarioF
from flooding_lib.tests.test_models import ProjectF

from flooding_lib.tools.approvaltool.models import ApprovalObjectType


class UserF(factory.Factory):
    FACTORY_FOR = User

    username = 'remco'


class TestDecorators(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def testReceivesPermissionManager(self):
        request = self.request_factory.get('/')
        user = User()
        user.is_superuser = True
        request.user = user

        function = MagicMock()
        function.__name__ = ''  # For functools.wraps

        # decorate
        decorated = permission_manager.receives_permission_manager(function)

        # call with request
        decorated(request)

        # Check if mock received request and superuser permission manager
        self.assertTrue(function.called)
        args = function.call_args  # Two elements, first the ordered
                                   # arguments, second the kw
                                   # arguments
        self.assertTrue(args[0][0] is request)
        self.assertTrue(isinstance(
                args[0][1],
                permission_manager.SuperuserPermissionManager))

    def testReceivesLoggedInPermissionManagerAnonymous(self):
        request = self.request_factory.get('/')
        user = AnonymousUser()
        request.user = user

        function = MagicMock()
        function.__name__ = ''  # For functools.wraps

        # decorate
        decorated = (permission_manager.
                     receives_loggedin_permission_manager(function))

        # call with request
        decorated(request)

        # Anonymous, function not called
        self.assertFalse(function.called)


class TestAnonymousPermissionManager(TestCase):
    def test_scenarios(self):
        """If we have a Group named 'demo group', and a scenario in a
        project where that groep has view permission, we should be
        able to see it."""

        group = Group(name='demo group')
        group.save()

        project = ProjectF.create()

        group.projectgrouppermission_set.add(
            ProjectGroupPermission(
                group=group,
                project=project,
                permission=UserPermission.PERMISSION_SCENARIO_VIEW))

        scenario = ScenarioF.create(status_cache=Scenario.STATUS_APPROVED)
        scenario.set_project(project)

        pm = permission_manager.AnonymousPermissionManager()
        self.assertTrue(scenario.id in (s.id for s in pm.get_scenarios()))


class TestUserPermissionManager(TestCase):
    def setUp(self):
        ApprovalObjectType.objects.create(
            type=ApprovalObjectType.TYPE_PROJECT)

    def testGetScenariosUserDoesntHavePermission(self):
        # If the user doesn't have the required permission, an empty
        # queryset is returned.
        scenario = ScenarioF.create(status_cache=Scenario.STATUS_APPROVED)
        project = ProjectF.create()
        scenario.set_project(project)
        scenarioproject = ScenarioProject.objects.get(
            scenario=scenario, project=project)
        scenarioproject.approved = True
        scenarioproject.save()

        user, _ = User.objects.get_or_create(username='remco')
        group = Group()
        group.save()
        user.groups.add(group)

        group.projectgrouppermission_set.add(
            ProjectGroupPermission(
                group=group,
                project=project,
                permission=UserPermission.PERMISSION_SCENARIO_VIEW))

        pm = permission_manager.UserPermissionManager(user)

        self.assertFalse(pm.check_permission(
                UserPermission.PERMISSION_SCENARIO_VIEW))
        self.assertEquals(0, len(pm.get_scenarios()))

        user.userpermission_set.add(
            UserPermission(
                permission=UserPermission.PERMISSION_SCENARIO_VIEW,
                user=user))

        self.assertTrue(pm.check_permission(
                UserPermission.PERMISSION_SCENARIO_VIEW))
        self.assertEquals(1, len(pm.get_scenarios()))

    def testGetScenariosPermissionScenarioView(self):
        user, _ = User.objects.get_or_create(username='remco')
        group = Group()
        group.save()
        user.groups.add(group)

        user.userpermission_set.add(
            UserPermission(
                permission=UserPermission.PERMISSION_SCENARIO_VIEW,
                user=user))

        project = ProjectF.create()
        # User can only see approved scenarios
        scenario = ScenarioF.create(status_cache=Scenario.STATUS_APPROVED)
        scenario.set_project(project)
        scenarioproject = ScenarioProject.objects.get(
            scenario=scenario, project=project)
        scenarioproject.approved = True
        scenarioproject.save()
        # So can't see this one
        scenario2 = ScenarioF.create(status_cache=Scenario.STATUS_WAITING)
        scenario2.set_project(project)

        group.projectgrouppermission_set.add(
            ProjectGroupPermission(
                group=group,
                project=project,
                permission=UserPermission.PERMISSION_SCENARIO_VIEW))

        pm = permission_manager.UserPermissionManager(user)
        self.assertTrue(pm.check_permission(
                UserPermission.PERMISSION_SCENARIO_VIEW))
        scenarios = pm.get_scenarios()
        self.assertEquals(len(scenarios), 1)
        self.assertEquals(scenarios[0].id, scenario.id)

    def testScenarioInMultipleProjects(self):
        # Check whether user can see a scenario, given that user has
        # rights in an 'extra' project the scenario is in

        # User is in some group and has view rights
        user, _ = User.objects.get_or_create(username='remco')
        group = Group()
        group.save()
        user.groups.add(group)

        user.userpermission_set.add(
            UserPermission(
                permission=UserPermission.PERMISSION_SCENARIO_VIEW,
                user=user))

        # There are two projects
        project1 = ProjectF.create()
        project2 = ProjectF.create()

        # An approved scenario is originally in project1 and approved there
        scenario = ScenarioF.create(status_cache=Scenario.STATUS_APPROVED)
        scenario.set_project(project1)
        scenarioproject = ScenarioProject.objects.get(
            scenario=scenario, project=project1)
        scenarioproject.approved = True
        scenarioproject.save()

        # Our user's group has view rights in project2
        group.projectgrouppermission_set.add(
            ProjectGroupPermission(
                group=group,
                project=project2,
                permission=UserPermission.PERMISSION_SCENARIO_VIEW))

        pm = permission_manager.UserPermissionManager(user)

        # We can't see the scenario
        self.assertEquals(len(pm.get_scenarios()), 0)

        # If we add the scenario to the second project
        project2.add_scenario(scenario)

        # Then we still can't, because it's not approved there
        self.assertEquals(len(pm.get_scenarios()), 0)

        # But once it's approved in project2...
        scenarioproject2 = ScenarioProject.objects.get(
            scenario=scenario, project=project2)
        scenarioproject2.approved = True
        scenarioproject2.save()

        # Then we can!
        self.assertEquals(len(pm.get_scenarios()), 1)
