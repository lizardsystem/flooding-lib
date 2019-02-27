# -*- coding: utf-8 -*-
"""
This module provides a way to rezip items using external unzip and zip
programs, bypassing some limitations encountered when using the python zipfile
module to extract from archives created on windows.
"""

from subprocess import Popen, PIPE
from os import chdir, getcwd, makedirs, mkfifo
from os.path import abspath, dirname

import shlex
import shutil
import tempfile


def rezip(source_path, source_item, target_path, target_item):
    """
    Transfer using external zip and unzip processes.

    :param source_path: path to source zipfile
    :param source_item: relative path of item in source zipfile
    :param target_path: path to target zipfile
    :param target_item: relative path of item in target zipfile

    Involves two processes and a fifo.
    """
    workdir = tempfile.mkdtemp()
    startdir = getcwd()

    # note explicit zip64 setting because size can't be inferred from fifo
    zip_template = 'zip --force-zip64 --quiet --fifo %s %s'

    # paths need to be absolute because the workdir will be changed
    zip_command = zip_template % (abspath(target_path), target_item)
    unzip_command = 'unzip -p %s %s' % (abspath(source_path), source_item)

    # change to the working dir to achieve correct zipped folder structure
    chdir(workdir)
    target_item_dirname = dirname(target_item)
    try:
        # make a fifo in a folder structure resembling item
        if target_item_dirname:
            makedirs(target_item_dirname)
        mkfifo(target_item)

        # start reading from the fifo
        proc_zip = Popen(shlex.split(zip_command), stdout=PIPE, stderr=PIPE)

        # start writing to the fifo
        with open(target_item, 'w') as f:
            Popen(shlex.split(unzip_command), stdout=f)

        # make sure the zip process is finished
        stdout, stderr = proc_zip.communicate()
        if proc_zip.poll():
            raise Exception(stdout)

    finally:
        chdir(startdir)
        shutil.rmtree(workdir)
