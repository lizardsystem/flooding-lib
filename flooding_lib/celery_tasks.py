"""Contains Celery tasks.

The different filename is because of the existence of the
"flooding_lib.tasks" package.

"""

# Python 3 is coming (...)
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from celery.task import task

import logging
logger = logging.getLogger(__name__)


@task
def add(x, y):
    """Add two numbers, useful in testing."""
    return x + y


@task
def handle_imported_group_files_task(groupimport_id, user_id):
    from flooding_lib.tools.importtool.views\
        import handle_imported_group_files

    return handle_imported_group_files(groupimport_id, user_id)
