#!/usr/bin/python
# (c) Nelen & Schuurmans.  GPL licensed.
import platform

class Body():
    """
    Represens a body of amqp message.
    """

    INSTRUCTION = "instruction"
    WORKFLOW_TASKS = "workflow_tasks"
    MAX_FAILURES = "max_failures"
    MAX_FAILURES_TMP = "max_failures_tmp"
    WORKFLOW_ID = "workflow_id"
    PRIORITY = "priority"
    SCENARIO_ID = "scenario_id"
    SCENARIO_TYPE = "scenario_type"
    CURR_LOG_LEVEL = "curr_log_level"
    MESSAGE = "message"
    TIME = "time"
    STATUS = "status"
    CURR_TASK_CODE = "curr_task_code"
    WORKER_NR = "worker_nr"
    WORKER_STATUS = "worker_status"
    NODE = "node"
    IS_HEARTBEAT = "is_heartbeat"

    def __init__(self):
        self.body = {
            Body.INSTRUCTION: {},
            Body.WORKFLOW_TASKS: {},
            Body.MAX_FAILURES: {},
            Body.MAX_FAILURES_TMP: {},
            Body.WORKFLOW_ID: "",
            Body.PRIORITY: 0,
            Body.SCENARIO_ID: "",
            Body.SCENARIO_TYPE: "",
            Body.CURR_LOG_LEVEL: 0,
            Body.MESSAGE: "",
            Body.TIME: 0,
            Body.STATUS: "",
            Body.CURR_TASK_CODE: "",
            Body.IS_HEARTBEAT: False,
            Body.WORKER_NR: None,
            Body.WORKER_STATUS: "",
            Body.NODE: platform.node()}

    def __getitem__(self, key):
        return self.body[key]

    def __setitem__(self, key, item):
        self.body[key] = item
