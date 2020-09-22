#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed.

import json

from lizard_worker.worker.action import Action
from lizard_worker.worker.action_task import ActionTask
from lizard_worker.worker.worker import WorkerProcess
from lizard_worker.worker.message_logging_handler import AMQPMessageHandler
from multiprocessing import Queue, Process

import logging, time

WORKER_COMMAND = ('start', 'kill')


class ActionSupervisor(Action):

    def __init__(self, connection, task_code, worker_nr, numeric_loglevel=20):
        self.task_code = task_code
        self.worker_nr = worker_nr
        self.connection = connection
        self.numeric_loglevel = numeric_loglevel
        self.log = logging.getLogger('worker.action_supervisor')
        self.processes = {}

    def callback(self, ch, method, properties, body):
        """
        """
        self.body = json.loads(body)
        self.channel = ch
        self.properties = properties
        self.execute_command()

        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    def test_action(self, child, task_code, worker_nr):
        #action = ActionTask('120', '10')
        from lizard_worker.worker.worker import Worker
        from lizard_worker.worker.broker_connection import BrokerConnection
        connection = BrokerConnection().connect_to_broker()
        action = ActionTask(task_code, worker_nr)
        worker = Worker(connection, task_code, action, worker_nr)
        worker.run_worker()
        # for i in range(0, 10):
        #     print i
        #     time.sleep(1)
        # for line in p.stdout.readlines():
        #         print line,

    def execute_command(self):
        command = self.body.get("command", None)
        success = True
        if command == 'start':
            worker_nr = self.next_worker_nr()
            task_code = self.body.get("task_code", None)
            self.log.info("Start worker nr. {0} to performe task {1}".format(
                    worker_nr, task_code))
            # set handler to forward logging to message broker
            #action = ActionTask(task_code, worker_nr)
            #self.set_logger(action)

            # create and start worker as subprocess
            #p = WorkerProcess(action, worker_nr, task_code)
            #q = Queue()
            #p = Process(target=self.test_action, args=(q,))
            #p.start()
            import subprocess, threading, os
            from django.conf import settings
            from lizard_worker.worker.worker import WorkerThread
            cmd = [os.path.join(settings.BUILDOUT_DIR, "bin", "django"),
                   "task_worker_new", "--task_code", str(task_code),
                   "--worker_nr", str(worker_nr), "--log_level", str(self.numeric_loglevel)]
            self.log.info("COMMAND PATH {0}".format(cmd))
            worker = WorkerThread(cmd)
            worker.start()
            self.processes.update({str(worker_nr): worker})
        elif command == 'kill':
            worker_nr = str(self.body.get("worker_nr", None))
            worker = self.get_process(worker_nr)
            if worker is not None and worker.is_alive():
                #p.connection.disconnect()
                worker.kill_subprocess()
                #p.join()
                self.processes.pop(worker_nr)
                self.log.info("Worker nr.{0} is closed.".format(worker_nr))
        else:
            self.log.warning("The command '{0}' is NOT defined.")
            success = False
        return success

    def next_worker_nr(self):
        numbers = self.processes.keys()
        numbers.sort()
        if len(numbers) > 0:
            number = int(numbers[-1]) + 1
            return number
        return 1

    def get_process(self, worker_nr):
        p = self.processes.get(worker_nr, None)
        if p is None:
            self.log.error("Worker nr.{0} is not present".format(worker_nr))
        return p

    def set_logger(self, action):
        action.log = logging.getLogger(
            'worker.action.{0}'.format(action.worker_nr))
        logging.handlers.AMQPMessageHandler = AMQPMessageHandler
        broker_logging_handler = logging.handlers.AMQPMessageHandler(
            action, self.numeric_loglevel)
        action.set_broker_logging_handler(broker_logging_handler)
