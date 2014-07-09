"""Base classes to use for class-based views."""

from django.core.exceptions import PermissionDenied
import django.views.generic

from flooding_lib import permission_manager


# Mixin copied from lizard_ui, better than depending on it
class ViewContextMixin(object):
    """View mixin that adds the view object to the context.

    Make sure this is near the front of the inheritance list: it should come
    before other mixins that (re-)define ``get_context_data()``.

    When you use this mixin in your view, you can do ``{{ view.some_method
    }}`` or ``{{ view.some_attribute }}`` in your class and it will call those
    methods or attributes on your view object: no more need to pass in
    anything in a context dictionary, just stick it on ``self``!

    """
    def get_context_data(self, **kwargs):
        """Return context with view object available as 'view'."""
        try:
            context = super(ViewContextMixin, self).get_context_data(**kwargs)
        except AttributeError:
            context = {}
        context.update({'view': self})
        return context


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
    ViewContextMixin,
    django.views.generic.TemplateView):
    """We always want at least these."""
    pass
