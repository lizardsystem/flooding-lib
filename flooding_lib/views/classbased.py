"""Base classes to use for class-based views."""

from django.core.exceptions import PermissionDenied
import django.views.generic
import lizard_ui.views

from flooding_lib import permission_manager


class SetKwargsOnSelfMixin(object):
    def dispatch(self, request, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        return super(
            SetKwargsOnSelfMixin, self).dispatch(request, *args)


class PermissionManagerMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.permission_manager = permission_manager.get_permission_manager(
            user=request.user)

        if hasattr(self, 'required_permission'):
            if not self.permission_manager.check_project_permission(
                self.project,
                self.required_permission):
                raise PermissionDenied()

        return super(PermissionManagerMixin, self).dispatch(
            request, *args, **kwargs)


class BaseView(
    SetKwargsOnSelfMixin,
    PermissionManagerMixin,
    lizard_ui.views.ViewContextMixin,
    django.views.generic.TemplateView):
    """We always want at least these."""
    pass
