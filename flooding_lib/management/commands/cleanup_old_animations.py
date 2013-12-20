"""New animations are .tiff files, in the directories pointed at by
the .basedir property of pyramids.Animation records. In the same
directories, there may be .png and .pgw files of old animations."""

import os

from django.core.management.base import BaseCommand

from flooding_lib.models import Result


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for result in Result.objects.filter(animation__isnull=False):
            # Filter through results to find their animations, this
            # way we don't delete old animations if the new animation
            # isn't connected to the result correctly.
            basedir = result.animation.basedir
            if os.path.exists(basedir):
                for filename in os.listdir(basedir):
                    if (filename.endswith(".png") or
                        filename.endswith(".pgw")):
                        fullpath = os.path.join(basedir, filename)
                        print("Removing {}.".format(fullpath))
                        os.remove(fullpath)
