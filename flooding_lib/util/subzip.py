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
import signal
import tempfile


class TimeoutError(Exception):
    pass


class ZipError(Exception):
    pass


def handler(signum, frame):
    raise TimeoutError('Timeout')


def rezip(source_path, source_item, target_path, target_item, timeout=1):
    """
    Transfer using external zip and unzip processes.

    :param source_path: path to source zipfile
    :param source_item: relative path of item in source zipfile
    :param target_path: path to target zipfile
    :param target_item: relative path of item in target zipfile
    :param timeout: seconds patience for the start of the zip process

    Involves two processes and a fifo.

    Note that if the unzip process fails, it happens quietly and the resulting
    zip ends up with an empty item.

    If the zip process fails to start, the function gets stuck on trying to
    open the fifo for writing, which will raise an exception after timeout
    seconds.

    If the zip process fails after starting, an exception will be raised, too.
    """
    workdir = tempfile.mkdtemp()
    startdir = getcwd()

    # note explicit zip64 setting because size can't be inferred from fifo
    zip_template = 'zip --force-zip64 --quiet --fifo %s %s'

    # paths need to be absolute because the workdir will be changed
    cmd_zip = zip_template % (abspath(target_path), target_item)
    cmd_unzip = 'unzip -p %s %s' % (abspath(source_path), source_item)

    # change to the working dir to achieve correct zipped folder structure
    chdir(workdir)
    target_item_dirname = dirname(target_item)
    try:
        # make a fifo in a folder structure resembling item
        if target_item_dirname:
            makedirs(target_item_dirname)
        mkfifo(target_item)

        # start reading from the fifo
        proc_zip = Popen(shlex.split(cmd_zip), stdout=PIPE, stderr=PIPE)

        # set timeout for opening of the fifo
        signal.alarm(timeout)
        try:
            # open the fifo for writing, which may block
            with open(target_item, 'w') as f:
                # disable the timeout
                signal.alarm(0)
                # start writing to the fifo from the unzip process
                Popen(shlex.split(cmd_unzip), stdout=f)
        except TimeoutError:
            pass

        # make sure the zip process is finished
        stdout, stderr = proc_zip.communicate()
        if proc_zip.poll():
            raise ZipError(stdout)

    finally:
        chdir(startdir)
        shutil.rmtree(workdir)


signal.signal(signal.SIGALRM, handler)
