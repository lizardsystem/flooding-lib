#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed.

import json

from lizard_worker.worker.action import Action


class ActionQueue(Action):
    """
    Handles sort requist.
    """

    def __init__(self, connection, task_code):
        """
        task_code = queue name
        target_queue - queue has to be sotred
        body - containse target_queue
        bulk_masseqes - dict for messages
        """
        self.task_code = task_code
        self.target_queue = None
        self.connection = connection
        self.body = None
        self.log = None
        self.bulk_messages = {}

    def callback(self, ch, method, properties, body):
        """
        Called from worker.
        Retrieves target_queue from body.
        Runs sort_target_queue fuction.
        Catches exceptions.
        """
        self.channel = ch
        self.body = json.loads(body)
        self.target_queue = self.body["target_queue"]

        self.log.info("Start prioritizing task on queue %s." %
                      self.target_queue)

        if not self.target_queue or self.target_queue == "":
            self.log.error("UNKNOWN target queue - '%s'.")
            return

        try:
            self.sort_target_queue()
        except Exception as ex:
            self.log.error("{0}".format(ex))

        self.log.info("End prioritizing task on queue %s." % self.target_queue)

    def sort_target_queue(self):
        """
        Consumes, groups, sorts and publishes
        messages from/to the target queue.
        """
        ch = self.connection.channel()
        consume = True
        while consume:
            method, properties, body = ch.basic_get(queue=self.target_queue)
            if method.NAME == 'Basic.GetEmpty':
                consume = False
                self.publish_sorted(ch)
                ch.close()
            else:
                self.consume_target_queue(ch, method, properties, body)
                ch.basic_ack(delivery_tag=method.delivery_tag)

    def publish_sorted(self, ch, reverse=True):
        """
        Sorts messages by priority and timestamp,
        publishes them back to the target queue.
        """
        for key_x in sorted(self.bulk_messages, reverse=reverse):
            for key_y in sorted(self.bulk_messages[key_x], reverse=reverse):
                exchange = self.bulk_messages[key_x][key_y]["method"].exchange
                r_key = self.bulk_messages[key_x][key_y]["method"].routing_key
                body = self.bulk_messages[key_x][key_y]["body"]
                properties = self.bulk_messages[key_x][key_y]["properties"]
                ch.basic_publish(exchange=exchange,
                                 routing_key=r_key,
                                 body=body,
                                 properties=properties)

    def group_messages(self, ch, method, properties, body):
        """
        Puts messages grouped in to dict like
        {"priority": {"timestamp": {"ch": ch, "method": ....}}}
        """
        message = {}
        message[properties.timestamp] = {"ch": ch,
                                         "method": method,
                                         "properties": properties,
                                         "body": body}

        if properties.priority in self.bulk_messages.keys():
            value = self.bulk_messages[properties.priority]
            value.update(message)
        else:
            value = message

        self.bulk_messages[properties.priority] = value
