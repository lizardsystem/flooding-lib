from __future__ import unicode_literals, division
from __future__ import print_function, absolute_import

from stat import S_IRUSR, S_IWUSR, S_IRGRP, S_IROTH
import logging
import os
import scipy.misc
import shutil
import tempfile
import zipfile

from django.conf import settings

"""Utilities for working with files in general."""
logger = logging.getLogger(__name__)


class ZipfileTooLarge(Exception):
    pass


class temporarily_unzipped(object):
    """Context manager that unzips a zip file, allowing code to change
    the files in it, and eventually zips the files back again."""

    def __init__(
        self, path, rezip=True,
        rezip_on_exceptions=False, max_size=None,
        tmp_dir=getattr(settings, 'TMP_DIR')):
        """Temporarily unzip a zipfile and return the files in it,
        rezip afterwards.

        path is a path leading to a zipfile.

        If rezip is False, the files aren't put back into the zipfile
        afterwards.

        tmp_dir is the location of the temp directory. By default,
        this uses the TMP_DIR setting in the main Django settings.py.

        By default, if an exception is raised inside the context
        manager, the changed files will NOT be added back into the
        zipfile, because there's probably something wrong with
        them. To change that behaviour, set rezip_on_exceptions=True."""

        self.tmp_dir_path = tmp_dir
        self.path = path
        self.rezip = rezip
        self.rezip_on_exceptions = rezip_on_exceptions
        self.max_size = max_size

    def __enter__(self):
        # Create a temp directory
        self.tmpdir = tempfile.mkdtemp(
            prefix="flooding_lib_temporarily_unzipped",
            dir=self.tmp_dir_path)

        # Unzip everything to it
        # Pass a file descriptor, much faster because otherwise the file
        # is opened many times if there are many files in it
        zipf = zipfile.ZipFile(open(self.path, 'rb'))

        # If a max size is given, check the total file sizes of files within
        if self.max_size is not None:
            uncompressed_size = sum(
                fileinfo.file_size
                for fileinfo in zipf.infolist())
            if uncompressed_size > self.max_size:
                raise ZipfileTooLarge(
                    "Contents of {0} are too large ({1} bytes)".
                    format(self.path, uncompressed_size))

        self.namelist = zipf.namelist()
        zipf.extractall(path=self.tmpdir)
        zipf.close()

        # Return full paths to unzipped files
        return [os.path.join(self.tmpdir, name)
                for name in self.namelist]

    def __exit__(self, exc_type, exc_value, traceback):
        if (self.rezip and
            (exc_type is None or self.rezip_on_exceptions)):
            # Rewrite zipfile
            zipf = zipfile.ZipFile(
                self.path, 'w', compression=zipfile.ZIP_DEFLATED)
            for name in self.namelist:
                file_to_zip = os.path.join(self.tmpdir, name)
                # It may have been deleted, only add if it's still there
                if os.path.exists(file_to_zip):
                    zipf.write(filename=file_to_zip, arcname=name)
            zipf.close()

        # Remove temp directory
        shutil.rmtree(self.tmpdir)


class unzipped(temporarily_unzipped):
    """Context manager that unzips a zip file."""
    def __exit__(self, exc_type, exc_value, traceback):
        pass


def filename_matches(filename, extensions):
    return any(filename.lower().endswith(extension.lower())
               for extension in extensions)


def all_files_in(path, extensions=None, enter_zipfiles=False, verbose=False,
                 max_uncompressed_zip_size=None):
    """Walk all directories under path and yield full paths to all the
    files in it.

    If extensions is not None, it should be a tuple of allowed
    extensions. Only those files will be yielded.

    If extensions is not None and enter_zipfiles is True, zipfiles
    will be extracted into /tmp, the full paths to files inside these
    temp directories will be returned and the (possible changed) files
    will be re-zipped into their original filenames when this
    generator finishes.

    Using enter_zipfiles without extensions has no effect; .zip files
    will be returned as normal.
    """

    # Os.walk only works with directories. We want to be able to call
    # this function on a single file.
    if os.path.isdir(path):
        walk = os.walk(path)
    elif os.path.isfile(path):
        # Fake a walk representing a single file
        walk = [(os.path.dirname(path), (), (os.path.basename(path),))]

    for directory, dirnames, filenames in walk:
        for filename in filenames:
            full_path = os.path.join(directory, filename)

            if extensions is None:
                # Yield them all
                yield full_path

            elif filename_matches(filename, extensions):
                # File matches, yield it
                yield full_path

            elif enter_zipfiles and filename.lower().endswith('.zip'):
                # If we enter zipfiles and this is one, loop over the
                # files inside it.
                try:
                    with temporarily_unzipped(
                        full_path,
                        max_size=max_uncompressed_zip_size) as files_in_zip:
                        for unzipped_file in files_in_zip:
                            if filename_matches(unzipped_file, extensions):
                                # File matches, yield it
                                yield unzipped_file
                except (zipfile.BadZipfile, ZipfileTooLarge) as e:
                    if verbose:
                        print("Exception for {0}: {1}".
                              format(full_path, e))


def first_line(path):
    """Return the first line of file 'path'."""
    f = open(path)
    line = f.readline()
    f.close()
    return line


def remove_from_start(path, data):
    """Remove the string data from the beginning of file with path path, by
    reading it all in and writing it anew, minus data."""

    all_data = open(path).read()
    if not all_data.startswith(data):
        raise ValueError(
            "remove_from_start should only be called if the file"
            " really starts with the given data string.")

    all_data = all_data[len(data):]
    open(path, 'w').write(all_data)


def remove_comments_from_asc_files(
    path,
    verbose=False,
    max_uncompressed_zip_size=1000000000):  # 1G
    """In all .asc files under path, including those inside zip files,
    if the first line starts with '/*', remove that line.

    Skips files over 1G uncompressed size by default. The limit can be
    changed, or set to 'None' to go without size limit."""

    for filename in all_files_in(
        path,
        extensions=('.asc', '.inc'),
        enter_zipfiles=True,
        verbose=verbose,
        max_uncompressed_zip_size=max_uncompressed_zip_size):
        line = first_line(filename)
        if line.startswith('/*'):
            if verbose:
                print("Removing first line of {0}.".format(filename))
            remove_from_start(filename, line)


def add_to_zip(output_zipfile, zip_result):
    """
    Zip all files listed in zip_result

    zip_result is a list of dictionaries with keys:
    - filename: filename on disc
    - arcname: target filename in archive
    - delete_after: set this to remove file from file system after zipping
    """
    #print 'zipping result into %s' % output_zipfile
    with zipfile.ZipFile(output_zipfile, 'a', zipfile.ZIP_DEFLATED) as myzip:
        for file_in_zip in zip_result:
            #print 'zipping %s...' % file_in_zip['arcname']
            myzip.write(file_in_zip['filename'], file_in_zip['arcname'])
            if file_in_zip.get('delete_after', False):
                #print 'removing %r (%s in arc)' % (file_in_zip['filename'], file_in_zip['arcname'])
                os.remove(file_in_zip['filename'])


def mktemp(prefix='task_'):
    """Make a temp file

    You are responsible for deleting it.
    """
    f = tempfile.NamedTemporaryFile(delete=False, prefix=prefix)
    pathname = f.name
    f.close()
    return pathname


def save_geopng(path, colorgrid, geo_transform=None):
    """Save colored grid data to an image.

    Colorgrid is a (4 x n x m) grid that should be saved as an
    image. The 4 planes are red, green, blue and opacity.

    If the path ends in '.png' and a geo_transform is given, a '.pgw'
    file containing this data is also created, so that the image
    functions as a "geopng".
    """

    scipy.misc.imsave(path, colorgrid)

    if path.lower().endswith('.png') and geo_transform is not None:
        x0, dxx, dxy, y0, dyx, dyy = geo_transform
        pgw = path[:-4] + '.pgw'
        f = file(pgw, 'w')
        for gt in dxx, dxy, dyx, dyy, x0, y0:
            f.write("{0}\n".format(gt))
        f.close()


def make_file_readable_for_all(filepath):
    """This must be done to make the file readable to Nginx.

    The same goal could be achieved by changing the group of
    the file to 'www-data' and giving only the group read
    permissions, but user buildout is not part of www-data and
    therefore isn't allowed to do that. The below seems to be
    the lesser evil."""

    try:
        os.chmod(filepath, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)
    except OSError as e:
        # Only log
        logger.error(
            'OSError as we tried to change export result permissions:',
            str(e))
