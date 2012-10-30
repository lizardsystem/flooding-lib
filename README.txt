flooding-lib
==========================================

Introduction

Usage, etc.

More details in src/lizard_flooding/USAGE.txt .


Install production / staging server
-----------------------------------

Linux task machine (i.e. task 200). The task server checks out the
master trunk of flooding. Run these commands from "flooding".

Init
    $ bin/fab staging_taskserver init
Update
    $ bin/fab staging_taskserver update_task

Task 200
========

- copy dijkringen directory (flooding share ->
  filedatabase/task_200_dijkringen) to a place and point
  Exporttool.Setting DIJKRING_SHAPES_FOLDER to it.

- set MAXIMAL_WATERDEPTH_RESULTS_FOLDER and EXPORT_FOLDER (maybe the
  settings can be merged later)

- the export folders is likely a network share, configure it in
  /etc/fstab.

- make a workflow template with code 3. At the time of writing this
  workflow template only contains task 200. The front end will try to
  find workflow template with code 3.

- set the broker and supervisor settings (see flooding:
  staging-task-200.cfg)

- for testing you can run:

    $ bin/django lw_task_worker --task_code 200 --log_level DEBUG --worker_nr 1

- Problems can arise when installing netcdf4. Try:

    $ sudo apt-get install libhdf5-serial-dev libnetcdf-dev


Task 210/220 threedi
====================

Instructions to install task machine and set up environment:

- Install subgridf90, see:
  http://publicwiki.deltares.nl/display/3Diusers/3Di-Subgrid+building+on+Linux

- Make sure the folders in the flooding_base.Settings SOURCE_DIR,
  DESTINATION_DIR are accessible.

- In the django settings, set THREEDI_DEFAULT_FILES_PATH
  (point to /../threedilib/threedi)

- In the django settings, set THREEDI_BIN_PATH
  (point to /home/buildout/3di-grid/bin/subgridf90)

- TODO: the location of subgridf90 is now static (in threedilib)

- Add workflow 4 with at least 210 -> 220 -> 185

- Add queues 210 and 220 to broker.

- To test you can run:

  $ bin/django test_task_210 1

where 1 is the id of ThreediCalculation.

  $ bin/django test_workflow_4 10973

Start workflow 4 for scenario 10973.


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

