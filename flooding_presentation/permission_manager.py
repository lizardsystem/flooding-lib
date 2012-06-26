# -*- coding: utf-8 -*-
from flooding_presentation.models import PresentationLayer
from flooding_visualization.models import ShapeDataLegend
from flooding_lib.permission_manager import PermissionManager as \
    PermissionManagerFlooding
from flooding_lib.models import UserPermission as UserPermissionFlooding


class PermissionManager:
    """
    Permission manager for presentation. See the TWiki docs.

    Sample usage:
    >>> from permission_manager import PermissionManager
    >>> user = get_object_or_404(User, username='jack')
    >>> pl = get_object_or_404(PresentationLayer, pk=1)
    >>> pm = PermissionManager(user)
    >>> pm.check_permission(
    ...     pl, PermissionManager.PERMISSION_PRESENTATIONLAYER_VIEW)
    True

    """
    PERMISSION_PRESENTATIONLAYER_VIEW = 1
    PERMISSION_PRESENTATIONLAYER_EDIT = 2

    PERMISSION_DICT = {
        1: 'PRESENTATIONLAYER_VIEW',
        2: 'PRESENTATIONLAYER_EDIT',
        }

    def __init__(self, user):
        self.user = user
        #we gaan er even van uit dat Flooding aanwezig is
        if True:
            self.pm_flooding = PermissionManagerFlooding(self.user)
        #except ImportError:
        #    self.pm_flooding = None

    def check_permission_flooding(
        self, permission_level, permission, presentationlayer=None):
        """Mapping from presentationtype to flooding
        permissions. Returns True if permitted

        An example mapping function is implemented now
        """
        result = False

        def always_true(*args, **kwargs):
            return True

        def flooding_project(presentationlayer, flooding_permission):
            """Checks for flooding project permission

            presentationlayer.scenario_set.all() should have length 1.
            if one of the 'scenario's' has the correct permission,
            then return True, else False
            """
            for scenario in presentationlayer.scenario_set.all():
                if self.pm_flooding.check_project_permission(
                    scenario.main_project, flooding_permission):
                    return True
            return False

        if presentationlayer is None:
            project_permission = always_true
        else:
            #prepare stuff for flooding project permission check
            project_permission = flooding_project

        if permission == self.PERMISSION_PRESENTATIONLAYER_VIEW:
            if permission_level == 1:
                # flooding permission
                fp = UserPermissionFlooding.PERMISSION_SCENARIO_VIEW
                result = (self.pm_flooding.check_permission(permission=fp) and
                          project_permission(presentationlayer, fp))
            elif permission_level == 2:
                # flooding permission
                fp = UserPermissionFlooding.PERMISSION_SCENARIO_VIEW
                result = (self.pm_flooding.check_permission(permission=fp) and
                          project_permission(presentationlayer, fp))

        elif permission == self.PERMISSION_PRESENTATIONLAYER_EDIT:
            # flooding permission
            if permission_level == 1:
                fp = UserPermissionFlooding.PERMISSION_SCENARIO_EDIT
                result = (self.pm_flooding.check_permission(permission=fp) and
                          project_permission(presentationlayer, fp))
            elif permission_level == 2:
                # flooding permission
                fp = UserPermissionFlooding.PERMISSION_PROJECT_ADD
                result = (self.pm_flooding.check_permission(permission=fp) and
                          project_permission(presentationlayer, fp))

        return result

    def check_permission_app(self, app_code, permission_level, permission,
                             presentationlayer=None):
        """check permission for given app, permission_level and
        requested permission for current user

        optioneel: presentationlayer. Indien deze niet is opgegeven,
        dan krijg je "mag de user uberhaupt dingen doen". Indien wel:
        "mag de user dit doen met deze layer".

        """
        if self.user.is_staff:
            return True
        if app_code == PresentationLayer.SOURCE_APPLICATION_NONE:
            return True
        elif app_code == PresentationLayer.SOURCE_APPLICATION_FLOODING:
            return self.check_permission_flooding(
                permission_level, permission,
                presentationlayer=presentationlayer)
        return False

    def check_permission(self, presentationlayer, permission):
        """
        Strenge permissiecheck - mag de user uberhaupt dingen doen,
        plus igv flooding: heeft hij de juiste permissies voor het
        project waar de layer bij hoort?

        permission in PERMISSION_PRESENTATIONLAYER_VIEW/EDIT
        """

        sa = presentationlayer.source_application
        pl = presentationlayer.presentationtype.permission_level
        return self.check_permission_app(sa, pl, permission,
                                         presentationlayer=presentationlayer)

    def get_legends(self, presentationlayer):
        """Get all legends for given presentationlayer for this user"""
        sa = presentationlayer.source_application
        #pt = presentationlayer.presentationtype
        #pl = pt.permission_level
        if (self.user.is_staff or
            sa == PresentationLayer.SOURCE_APPLICATION_NONE):

            result = ShapeDataLegend.objects.filter(
                presentationtype=presentationlayer.presentationtype)
        elif sa == PresentationLayer.SOURCE_APPLICATION_FLOODING:
            if self.check_permission(
                presentationlayer, self.PERMISSION_PRESENTATIONLAYER_VIEW):
                result = ShapeDataLegend.objects.filter(
                    presentationtype=presentationlayer.presentationtype)
            else:
                result = []

        return result
