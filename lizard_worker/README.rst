lizard-worker
==========================================

Itroduction
------------------------

This the messaging application to manage the
tasks. It uses the RabbitMQ as message broker, pika to send
en recieve messages from the broker.


Development installation
------------------------

The first time, you'll have to run the "bootstrap" script to set up setuptools
and buildout::

    $> python bootstrap.py

And then run buildout to set everything up::

    $> bin/buildout

Create models

    $> bin/django syncdb

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

Create QUEUES in RabbitMQ using rabbitmq_managent webinterface.

Add BROKER_SETTINGS and QUEUES to the project settings (see example in
workersettings.py)

Add mudule that contains a perform_task function to the project settings(see 
example in workersettings.py)
 

Load fixture

   $> bin/django loaddata flooding_worker_initial

Start logging_workers, it wil save the logs into database

   $> bin/django logging_worker
or
   $> bin/django supervisord

Start one or more workers per queue/task_code (queue=task_code).
The queues are defined in brokerconfig.py.
The workers reads message from queue,
performs task and send the logging to logging queue and/or to next queue.

   $> bin/django run_common_worker queue/task_code

Start scenario with workflow_id as argument. The tasks wil be executed
according the value of sequence field in WorkfloTask table.

   $> bin/django start_scenario workflow_id

Open website on http://localhost:8000/logs/ to monitor the logging
Open website on http://10.100.155.150:55672 to monitor the broker

For more information about RabbitMQ take a look at
http://www.rabbitmq.com/.


Configuration
-------------


