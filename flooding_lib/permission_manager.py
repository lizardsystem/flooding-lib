# -*- coding: utf-8 -*-
import functools
import logging

from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q

from flooding_lib.models import (
    UserPermission,
    Project,
    Region,
    RegionSet,
    ExternalWater
)
from flooding_lib.models import ProjectGroupPermission, Scenario

log = logging.getLogger('permission_manager')


def receives_permission_manager(view):
    """Decorator that wraps a function that receives a request as its first
    argument, creates a permission manager using request.user, and passes it
    as second argument to the function.

    Hack: if the first argument is an instance of a Django class-based
    view, we assume that the _second_ argument is request and function
    as a method decorator."""
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        args = list(args)
        request = args.pop(0)

        if isinstance(request, generic.View):
            self = request
            request = args.pop(0)
            permission_manager = get_permission_manager(request.user)
            return view(
                self, request, permission_manager, *args, **kwargs)

        permission_manager = get_permission_manager(request.user)
        return view(request, permission_manager, *args, **kwargs)

    return wrapper


def receives_loggedin_permission_manager(view):
    """Decorator that combines login_required and
    receives_permission_manager."""
    return login_required(receives_permission_manager(view))


def get_permission_manager(user=None):
    """Factory function for the three types of permission managers."""
    if user is None or not user.is_authenticated():
        return AnonymousPermissionManager()
    elif user.is_superuser:
        return SuperuserPermissionManager()
    else:
        return UserPermissionManager(user)


class SuperuserPermissionManager(object):
    """Superusers can do everything they want, permissions are all True."""

    def get_projects(self, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Superuser can see all projects."""
        return Project.objects.all()

    def get_regionsets(self,
                       permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Superuser can see all RegionSets."""
        return RegionSet.objects.all()

    def get_regions(self, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Superuser can see all Regions."""
        return Region.objects.all()

    def get_external_waters(self, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Superuser can see all ExternalWaters."""
        return ExternalWater.objects.all()

    def get_scenarios(
        self, breach=None, permission=UserPermission.PERMISSION_SCENARIO_VIEW,
        status_list=None):
        """Return all scenarios, for this breach if given otherwise
        for all breaches, for these statuses if given, otherwise for all
        STATUS_CHOICES."""

        if status_list is None:
            status_list = [a for a, b in Scenario.STATUS_CHOICES]

        criteria = dict()
        criteria["status_cache__in"] = status_list
        if breach:
            criteria["breaches"] = breach

        return Scenario.objects.filter(**criteria).distinct()

    #------------------------- permission functions --------------
    def check_permission(self, permission):
        """Superuser has all permissions."""
        return True

    def check_project_permission(self, project, permission):
        """Superuser has all permissions."""
        return True

    def check_regionset_permission(self, regionset, permission):
        """Superuser has all permissions."""
        return True

    def check_region_permission(self, region, permission):
        """Superuser has all permissions."""
        return True

    def check_scenario_permission(self, scenario, permission):
        """Superuser has all permissions."""
        return True


class AnonymousPermissionManager(object):
    def get_projects(self, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Find projects with given permission and return them."""

        #anonymous users: show all demo projects
        return Project.objects.filter(
            projectgrouppermission__group__name='demo group',
            projectgrouppermission__permission=permission)

    def get_regionsets(self,
                       permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Find regionsets with given permission for a user and return them."""

        project_list = Project.objects.filter(
            projectgrouppermission__group__name='demo group',
            projectgrouppermission__permission=permission)

        return RegionSet.objects.filter(
            Q(project__in=project_list) |
            Q(regions__project__in=project_list)).distinct()

    def get_regions(self, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Find regions with given permission for a user and return them."""

        #return all regionsets of projects that belong to the demo group
        demogroup = Group.objects.get(name='demo group')
        project_list = Project.objects.filter(
            Q(projectgrouppermission__group=demogroup,
              projectgrouppermission__permission=permission))

        return Region.objects.filter(
                Q(project__in=project_list) |
                Q(regionset__project__in=project_list)).distinct()

    def get_scenarios(
        self, breach=None, permission=UserPermission.PERMISSION_SCENARIO_VIEW,
        status_list=None):
        """work in progress

        scenarios met view en permission recht - alle
        scenarios met view recht - alleen met status approved


        get list of scenarios"""
        if status_list == None:
            status_list = [a for a, b in Scenario.STATUS_CHOICES]

        # return all regionsets of projects that belong to the demo group
        demogroup = Group.objects.get(name='demo group')
        PSV = UserPermission.PERMISSION_SCENARIO_VIEW
        filter = Q(
            scenarioproject__project__projectgrouppermission__group=demogroup,
            scenarioproject__project__projectgrouppermission__permission=PSV,
            status_cache=Scenario.STATUS_APPROVED,
            status_cache__in=status_list)

        if breach is None:
            return Scenario.objects.filter(filter).distinct()
        else:
            return Scenario.objects.filter(
                breaches=breach).filter(filter).distinct()

    #------------------------- permission functions --------------
    def check_permission(self, permission):
        """Checks user permission.

        mag een gebruiker uberhaupt dingen doen
        """

        return False

    def check_project_permission(self, project, permission):
        """Check project access permission.

        return True if user has the correct permission, False if user
        has no permission.

        """

        #last chance: user is not authenticated, then the project must
        #fall in the 'demo group'
        return ProjectGroupPermission.objects.filter(
            group__name='demo group',
            project=project,
            permission=permission).exists()

    def check_regionset_permission(self, regionset, permission):
        """Check regionset access permission."""

        for p in regionset.project_set.all():
            if self.check_project_permission(p, permission):
                #if any project has the right permission, then it's ok
                return True
        return False

    def check_region_permission(self, region, permission):
        """Check region access permission."""

        return ProjectGroupPermission.objects.filter(
            permission=permission,
            group__name='demo group').filter(
            Q(project__regions=region) |
            Q(project__regionsets__regions=region)).exists()

    def check_scenario_permission(self, scenario, permission):
        """Check whether user has the given permission in any of the
        scenario's projects."""
        return any(self.check_project_permission(project, permission)
                   for project in scenario.project_set.all())


class UserPermissionManager(object):
    """
    Query this objects for all accessable projects, regionsets,
    regions, etc, with a given permission.

    >>> from django.contrib.auth.models import User
    >>> from models import UserPermission
    >>> u, created = User.objects.get_or_create(username='jack')
    >>> if created:
    ...     UserPermission(
    ...         user=u,
    ...         permission=UserPermission.PERMISSION_SCENARIO_VIEW).save()
    >>> pm = get_permission_manager(u)
    >>> pm.check_permission(UserPermission.PERMISSION_SCENARIO_VIEW)
    True

    """

    def __init__(self, user):
        self.user = user

    def get_projects(self, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Find projects with given permission and return them."""

        if not self.check_permission(permission):
            return Project.objects.filter(pk=-1)

        #generate list of projects
        return Project.objects.filter(
            projectgrouppermission__group__user=self.user,
            projectgrouppermission__permission=permission)

    def get_regionsets(self,
                       permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Find regionsets with given permission for a user and return them."""
        if not self.check_permission(permission):
            return RegionSet.objects.filter(pk=-1)

        project_list = self.get_projects(permission)

        return RegionSet.objects.filter(
            Q(project__in=project_list) |
            Q(regions__project__in=project_list)).distinct()

    def get_regions(self, permission=UserPermission.PERMISSION_SCENARIO_VIEW):
        """Find regions with given permission for a user and return them."""

        if not self.check_permission(permission):
            return Region.objects.filter(pk=-1)

        project_list = Project.objects.filter(
            Q(projectgrouppermission__group__user=self.user,
              projectgrouppermission__permission=permission))

        return Region.objects.filter(
            Q(project__in=project_list) |
            Q(regionset__project__in=project_list)).distinct()

    def get_scenarios(
        self, breach=None, permission=UserPermission.PERMISSION_SCENARIO_VIEW,
        status_list=None):
        """
        If permission is SCENARIO_VIEW, and the user does not have
        SCENARIO_APPROVE rights, then only show scenarios that are
        approved within the project that gives the user the view
        rights.

        Otherwise, return a queryset of distinct scenarios to which
        user has the given permission.

        If a breach is given, return only scenarios involving that
        breach.

        If a status_list is given, return only scenarios with a status
        in that list.

        Bug: In theory it is possible that a scenario has view rights
        to a scenario in some project, that the scenario is approved
        within that project, but not approved in its main project. And
        that status_list asks for approved projects only. In that
        case, the scenario won't be visible because its status will
        not be STATUS_APPROVED.
        """

        PSA = UserPermission.PERMISSION_SCENARIO_APPROVE
        PSV = UserPermission.PERMISSION_SCENARIO_VIEW

        if not self.check_permission(permission):
            return Scenario.objects.filter(pk=-1)

        if status_list == None:
            status_list = [a for a, b in Scenario.STATUS_CHOICES]

        if permission == PSV:
            filter = Q(
  scenarioproject__project__projectgrouppermission__group__user=self.user,
  scenarioproject__project__projectgrouppermission__permission=PSV,
  scenarioproject__approved=True,
                status_cache__in=status_list)
            if self.check_permission(PSA):
                filter = filter | Q(
  scenarioproject__project__projectgrouppermission__group__user=self.user,
  scenarioproject__project__projectgrouppermission__permission=PSA,
                    status_cache__in=status_list)
        else:
            filter = Q(
  scenarioproject__project__projectgrouppermission__group__user=self.user,
  scenarioproject__project__projectgrouppermission__permission=permission,
                status_cache__in=status_list)

        if breach is None:
            return Scenario.objects.filter(filter).distinct()
        else:
            return Scenario.objects.filter(
                breaches=breach).filter(filter).distinct()

    #------------------------- permission functions --------------
    def check_permission(self, permission):
        """Checks user permission.

        mag een gebruiker uberhaupt dingen doen
        """

        try:
            self.user.userpermission_set.get(permission=permission)
            return True
        except:
            return False

    def check_project_permission(self, project, permission):
        """Check project access permission.

        return True if user has the correct permission, False if user
        has no permission.

        """
        #one of users groups must have permission for this project
        return ProjectGroupPermission.objects.filter(
            group__user=self.user,
            project=project,
            permission=permission).exists()

    def check_regionset_permission(self, regionset, permission):
        """Check regionset access permission."""

        # User has this permission on a regionset if he has this
        # permission on any of the projects related to this regionset
        return any(self.check_project_permission(p, permission)
                   for p in regionset.project_set.all())

    def check_region_permission(self, region, permission):
        """Check region access permission."""

        return ProjectGroupPermission.objects.filter(
            permission=permission, group__user=self.user).filter(
            Q(project__regions=region) |
            Q(project__regionsets__regions=region)).exists()

    def check_scenario_permission(self, scenario, permission):
        """Check whether user has the given permission in any of the
        scenario's projects."""
        return any(
            self.check_project_permission(project, permission)
            for project in scenario.projects.all())
