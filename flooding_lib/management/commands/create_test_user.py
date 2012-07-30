from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # For testing right now it's easiest if we just change the
        # name and password of YP
        user = User.objects.get(username='YP')

        user.username = 'remco'
        user.first_name = 'Remco'
        user.last_name = 'Gerlich'
        user.set_password('password')
        user.email = 'remco.gerlich@nelen-schuurmans.nl'
        user.save()
