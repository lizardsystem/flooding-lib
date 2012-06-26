from flooding_lib import permission_manager

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.test.client import RequestFactory

from mock import MagicMock


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
