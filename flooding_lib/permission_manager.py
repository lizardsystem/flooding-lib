# -*- coding: utf-8 -*-
import logging

from django.contrib.auth.models import Group
from django.db.models import Q

from flooding_lib.models import UserPermission, Project, Region, RegionSet
from flooding_lib.models import ProjectGroupPermission, Scenario

log = logging.getLogger('permission_manager')


def get_permission_manager(user):
    """Factory function for the three types of permission managers."""
    if not user.is_authenticated():
        return AnonymousPermissionManager()
    elif user.is_superuser:
        return SuperuserPermissionManager()
    else:
        return UserPermissionManager(user)


def PermissionManager(user):
    """Placeholder, because there used to be a class of this name."""
    return get_permission_manager(user)


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

        return Scenario.objects.filter(criteria).distinct()

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
            project__projectgrouppermission__group=demogroup,
            project__projectgrouppermission__permission=PSV,
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
    >>> pm = PermissionManager(u)
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
        """work in progress

        scenarios met view en permission recht - alle
        scenarios met view recht - alleen met status approved


        get list of scenarios"""
        if not self.check_permission(permission):
            return Scenario.objects.filter(pk=-1)

        if status_list == None:
            status_list = [a for a, b in Scenario.STATUS_CHOICES]

        if permission == UserPermission.PERMISSION_SCENARIO_VIEW:
            PSV = UserPermission.PERMISSION_SCENARIO_VIEW
            filter = Q(
                project__projectgrouppermission__group__user=self.user,
                project__projectgrouppermission__permission=PSV,
                status_cache=Scenario.STATUS_APPROVED,
                status_cache__in=status_list)
            if self.check_permission(
                UserPermission.PERMISSION_SCENARIO_APPROVE):
                PSA = UserPermission.PERMISSION_SCENARIO_APPROVE
                filter = filter | Q(
                    project__projectgrouppermission__group__user=self.user,
                    project__projectgrouppermission__permission=PSA,
                    status_cache__in=status_list)
        else:
            filter = Q(
                project__projectgrouppermission__group__user=self.user,
                project__projectgrouppermission__permission=permission,
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
