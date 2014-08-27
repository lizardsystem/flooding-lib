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

- filename's format of export-zip is [name export]_ddmmyyyy_hhMM.zip

- export-zip contains meta.json file within:
  - name export
  - owner
  - filelocation (as mounted on task server)
  - list of scenarios
  - selected maps
  - creration datetime
  - selected maps

- export-zip contains .asc files per selected map per 'dijkring'


Task 201
========

Create a zip file that contains all metadata of a list of scenarios in
CSV files, plus all result files.


Task 210
========

Do a 3Di calculation on a scenario and place the result netcdf back in a zip
subgrid_map.zip.


Task 220/221/222
================

Convert the netcdf in zip to a bunch of geo referenced png images.

- 220: Mask of region, automatic resolution setting. This is the preferred
  task.

- 221: Mask of region, take gridsize 0.5 (finest detail). Use only for small
  areas.

- 222: No mask of region, automatic resolution setting.


Upgrade to 3Di support
======================

- Make a SobekModel object, with version "3di".

- Make a 3Di specific region and add a breach. Add the newly created
  SobekModel to the region.

- Make the region part of a region set.

- Make workflow with code 8. This workflow consists of tasks: 210 ->
  220/221/222 -> 155.


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

- Problems can arise when installing netcdf4. Try:

    $ sudo apt-get install libhdf5-serial-dev libnetcdf-dev

- Add ResultType 'threediwaterlevel_t' and PresentationType '1f)
  anim. waterdiepte (3Di)' to the database.


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
