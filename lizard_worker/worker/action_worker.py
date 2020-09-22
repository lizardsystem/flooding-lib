#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed.

from lizard_worker.worker.action import Action

from pika import BasicProperties

from datetime import datetime
import logging


class ActionWorker(Action):

    def __init__(self, connection, worker_nr, command, task_code, queue_code):
        self.connection = connection
        self.log = logging.getLogger('worker.action.worker')
        self.worker_nr = worker_nr
        self.command = command
        self.task_code = task_code
        self.queue_code = queue_code
        self.body = {}
        self.channel = self.connection.channel()

    def callback(self, ch, method, properties, body):
        pass

    def execute(self):
        """
        Create and send message to appropriate queue.
        """
        self.set_message_properties()
        self.body = self.create_body()
        self.set_message_properties()
        msg = "Message emitted to queue '{0}'".format(self.task_code)
        self.send_trigger_message(self.body, msg, self.queue_code)

    def create_body(self):
        """
        Creates a body
        """
        option = {}
        option["worker_nr"] = self.worker_nr
        option["command"] = self.command
        option["task_code"] = self.task_code
        option["time"] = datetime.today().isoformat()
        return option

    def set_message_properties(self, priority=0, message_id=0):

        self.properties = BasicProperties(content_type="application/json",
                                          delivery_mode=2,
                                          priority=priority,
                                          message_id=str(message_id),
                                          timestamp=datetime.today().isoformat())
