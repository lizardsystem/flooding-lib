lizard-flooding
==========================================

Introduction

Usage, etc.

More details in src/lizard_flooding/USAGE.txt .


Development installation
------------------------

The first time, you'll have to run the "bootstrap" script to set up setuptools
and buildout::

    $> python bootstrap.py

And then run buildout to set everything up::

    $> bin/buildout

(On windows it is called ``bin\buildout.exe``).

You'll have to re-run buildout when you or someone else made a change in
``setup.py`` or ``buildout.cfg``.

The current package is installed as a "development package", so
changes in .py files are automatically available (just like with ``python
setup.py develop``).

If you want to use trunk checkouts of other packages (instead of released
versions), add them as an "svn external" in the ``local_checkouts/`` directory
and add them to the ``develop =`` list in buildout.cfg.

Tests can always be run with ``bin/test`` or ``bin\test.exe``.



Deployment installation for Windows
-----------------------------------
Install GDAL: gdalwin32-1.6
Add to the system environment variables:
- GDAL_DATA (to the right folder)
- PATH (Gdal\bin)

install matplotlib



Comment or uncomment the EXTERNAL_MOUNTED_DIR in settings.py:
Uncommented-> this folder is used for the external files
Commented-> the settings in the admin interface (like 'presentation_dir') are used.   

Settings:
# Use the different settings in localsettings.py if you need them.

