# -*- coding: utf-8 -*-
import logging

from django.contrib.auth.models import Group
from django.db.models import Q

from flooding_lib.models import UserPermission, Project, Region, RegionSet
from flooding_lib.models import ProjectGroupPermission, Scenario

log = logging.getLogger('permission_manager')


class PermissionManager:
    """
    Query this objects for all accessable projects, regionsets, regions, etc, with a given
    permission.

    >>> from django.contrib.auth.models import User
    >>> from models import UserPermission
    >>> u = User.objects.get(username='jack')
    >>> pm = PermissionManager(u)
    >>> pm.check_permission(UserPermission.PERMISSION_SCENARIO_VIEW)
    True

    """

    def __init__(self, user):
        self.user = user

    def get_projects(self, permission = UserPermission.PERMISSION_SCENARIO_VIEW):
        """Find projects with given permission and return them."""
        user = self.user
        if user.is_superuser:
            return Project.objects.all() #get all projects
        elif not user.is_authenticated():
            #anonymous users: show all demo projects
            demogroup = Group.objects.get(name='demo group')
            return Project.objects.filter(
                projectgrouppermission__group=demogroup,
                projectgrouppermission__permission=permission)
        elif not self.check_permission(permission):
            return Project.objects.filter(pk = -1)
        else:
            #generate list of projects
            return Project.objects.filter(
                projectgrouppermission__group__user=user,
                projectgrouppermission__permission=permission)

    def get_regionsets(self, permission = UserPermission.PERMISSION_SCENARIO_VIEW, through_scenario=False):
        """Find regionsets with given permission for a user and return them."""
        user = self.user
        if user.is_superuser:
            return RegionSet.objects.all()
        elif not(user.is_authenticated()):
            #return all regionsets of projects that belong to the demo group
            demogroup = Group.objects.get(name = 'demo group')
            project_list = Project.objects.filter(projectgrouppermission__group = demogroup,
                projectgrouppermission__permission = permission)
        elif not self.check_permission(permission):
            return RegionSet.objects.filter(pk = -1)
        else:
            #normal authenticated user
            project_list = self.get_projects(permission)

        if through_scenario:
            return RegionSet.objects.filter(region__breach__scenario__project_in = project_list).distinct()
        else:
            return RegionSet.objects.filter(Q(project__in = project_list)|Q(regions__project__in = project_list)).distinct()

    def get_regions(self, permission = UserPermission.PERMISSION_SCENARIO_VIEW, through_scenario=False):
        """Find regions with given permission for a user and return them."""
        user = self.user
        if user.is_superuser:
            return Region.objects.all()
        elif not(user.is_authenticated()):
            #return all regionsets of projects that belong to the demo group
            demogroup = Group.objects.get(name = 'demo group')
            project_list = Project.objects.filter(Q(projectgrouppermission__group=demogroup, projectgrouppermission__permission=permission))
        elif not self.check_permission(permission):
            return Region.objects.filter(pk = -1)
        else:
            project_list = Project.objects.filter(Q(projectgrouppermission__group__user=user, projectgrouppermission__permission=permission))

        if through_scenario:
            return Region.objects.filter(Q(region__breach__scenario__project__in = project_list)|
                                         Q(breach__scenario__project__in = project_list)).distinct()
        else:
            return Region.objects.filter(Q(project__in = project_list)|
                                         Q(regionset__project__in = project_list)).distinct()



    def get_scenarios(self, breach = None, permission = UserPermission.PERMISSION_SCENARIO_VIEW, status_list = None):
        """work in progress

        scenarios met view en permission recht - alle
        scenarios met view recht - alleen met status approved


        get list of scenarios"""
        if status_list == None:
            status_list = [a for a, b in Scenario.STATUS_CHOICES]

        user = self.user
        if user.is_superuser:
            filter = Q(status_cache__in=status_list)
        elif not(user.is_authenticated()):
            #return all regionsets of projects that belong to the demo group
            demogroup = Group.objects.get(name = 'demo group')
            filter = Q(project__projectgrouppermission__group=demogroup, project__projectgrouppermission__permission=UserPermission.PERMISSION_SCENARIO_VIEW, status_cache=Scenario.STATUS_APPROVED, status_cache__in=status_list)
        elif not self.check_permission(permission):
            return Scenario.objects.filter(pk = -1)
        else:
            if permission == UserPermission.PERMISSION_SCENARIO_VIEW:
                filter = Q(project__projectgrouppermission__group__user=user,
                           project__projectgrouppermission__permission=UserPermission.PERMISSION_SCENARIO_VIEW,
                           status_cache=Scenario.STATUS_APPROVED,
                           status_cache__in=status_list)
                if self.check_permission(UserPermission.PERMISSION_SCENARIO_APPROVE):
                    filter = filter | Q(
                        project__projectgrouppermission__group__user=user,
                        project__projectgrouppermission__permission=UserPermission.PERMISSION_SCENARIO_APPROVE,
                        status_cache__in=status_list)
            else:
                filter = Q(
                    project__projectgrouppermission__group__user=user,project__projectgrouppermission__permission=permission,
                    status_cache__in=status_list)

        if breach is None:
            return Scenario.objects.filter(filter).distinct()
        else:
            return Scenario.objects.filter(breaches=breach).filter(filter).distinct()


    #------------------------- permission functions ----------------------------
    def check_permission(self, permission):
        """Checks user permission.

        mag een gebruiker uberhaupt dingen doen
        """
        if self.user.is_superuser:
            return True
        try:
            self.user.userpermission_set.get(permission = permission)
            return True
        except:
            return False

    def check_project_permission(self, project, permission):
        """Check project access permission.
        return True if user has the correct permission, False if user has no permission.

        """
        user = self.user
        if user.is_superuser:
            return True
        #user must have an entry in UserPermission for this permission
        if user.is_authenticated() and (len(user.userpermission_set.filter(permission = permission)) == 0):
            return False
        #one of users groups must have permission for this project
        if len(ProjectGroupPermission.objects.filter(group__in = user.groups.all(),
                                                     project = project,
                                                     permission = permission)) > 0:
            return True
        #last chance: user is not authenticated, then the project must
        #fall in the 'demo group'
        if not(user.is_authenticated()):
            demogroup = Group.objects.filter(name = 'demo group')[0]
            if len(ProjectGroupPermission.objects.filter(group = demogroup,
                                                         project = project,
                                                         permission = permission)) > 0:
                return True
        return False

    def check_regionset_permission(self, regionset, permission):
        """Check regionset access permission."""
        user = self.user
        if user.is_superuser:
            return True
        for p in regionset.project_set.all():
            if self.check_project_permission(p, permission):
                #if any project has the right permission, then it's ok
                return True
        return False

    def check_region_permission(self, region, permission):
        """Check region access permission."""
        user = self.user
        if user.is_superuser:
            return True
        elif not user.is_authenticated():
            demogroup = Group.objects.get(name = 'demo group')
            perms = ProjectGroupPermission.objects.filter(permission=permission, group=demogroup).filter(Q(project__regions=region)|Q(project__regionsets__regions=region)).count()
        else:
            perms = ProjectGroupPermission.objects.filter(permission=permission, group__user=user).filter(Q(project__regions=region)|Q(project__regionsets__regions=region)).count()
        if perms>0:
            return True
        else:
            return False


