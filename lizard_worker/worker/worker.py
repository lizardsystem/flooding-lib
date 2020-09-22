#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed.

from pika.exceptions import AMQPChannelError

import logging
log = logging.getLogger('worker.worker')

import threading
import subprocess
from multiprocessing import Process
from lizard_worker.worker.broker_connection import BrokerConnection


class Worker():

    def __init__(self, connection, task_code, action, worker_nr=1):
        self.connection = connection
        self.action = action
        self.task_code = task_code
        self.worker_nr = worker_nr
        self.channel = None

    def run_worker(self):
        """
        Runs common worker to perform tasks.
        Task code equals to queue's name.
        """
        try:
            self.channel = self.connection.channel()
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(self.action.callback,
                                  queue=self.task_code,
                                  no_ack=False)
            self.channel.start_consuming()
        except AMQPChannelError as ex:
            log.error("Worker_nr: {0} error: {1}".format(
                    self.worker_nr, ",".join(map(str, ex.args))))

    def start_consuming(self):
        self.channel.start_consuming()

    def stop_consuming(self):
        self.channel.stop_consuming()


class WorkerThread(threading.Thread):
    def __init__(self, cmd):
        self.stdout = None
        self.stderr = None
        self.cmd = cmd
        self.p = None
        threading.Thread.__init__(self)

    def run(self):
        self.p = subprocess.Popen(self.cmd,
                             shell=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        self.stdout, self.stderr = self.p.communicate()

    def kill_subprocess(self):
        self.p.kill()


class WorkerProcess(Process):

    def __init__(self, action, worker_nr, task_code, *args, **kwargs):
        self.worker_nr = worker_nr
        self.task_code = task_code
        self.connection = None
        self.channel = None
        self.action = action
        self.set_connection()
        self.set_channel()
        Process.__init__(self, *args, **kwargs)

    def set_connection(self):
        self.connection = BrokerConnection().connect_to_broker()

    def set_channel(self):
        try:
            self.channel = self.connection.channel()
        except AMQPChannelError as ex:
            log.error("Worker_nr: {0} error: {1}".format(
                    self.worker_nr, ",".join(map(str, ex.args))))

    def set_action(self, action):
        self.action = action

    def run(self):
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(self.action.callback,
                                  queue=self.task_code,
                                  no_ack=False)
            self.channel.start_consuming()
        except AMQPChannelError as ex:
            log.error("Worker_nr: {0} error: {1}".format(
                    self.worker_nr, ",".join(map(str, ex.args))))
