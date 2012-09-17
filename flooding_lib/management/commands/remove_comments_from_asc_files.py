# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import os

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from flooding_lib.util.files import remove_comments_from_asc_files


class Command(BaseCommand):
    args = '<path>'
    help = """Walks the directory tree starting at <path>, also going into
ZIP files, looking for .asc and .inc files. If they are found, check if
the first line starts with '/*', and if so, remove it."""

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No path given.")
        path = args[0]
        if not os.path.exists(path) or not os.path.isdir(path):
            raise CommandError("'{0}' is not an existing directory.".
                               format(path))

        remove_comments_from_asc_files(path, verbose=True)
