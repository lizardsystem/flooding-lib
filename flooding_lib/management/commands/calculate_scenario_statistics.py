"""Run the calculate_scenario_statistics task as a management
command. First and only argument is the scenario_id."""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from flooding_lib.tasks import calculate_scenario_statistics


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not args:
            raise CommandError("No scenarioid given.")

        scenario_id = int(args[0])

        calculate_scenario_statistics.calculate_statistics(scenario_id)
