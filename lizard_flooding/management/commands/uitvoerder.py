#!/usr/bin/env python
# -*- coding: utf-8 -*-
#***********************************************************************
#*   
#***********************************************************************
#*                      All rights reserved                           **
#*   
#*   
#*                                                                    **
#*   
#*   
#*   
#***********************************************************************
#* Library    : <if this is a module, what is its name>
#* Purpose    : (choose, mark busy, perform, mark done) a task
#* Function   : main
#* Usage      : uitvoerder.py --help
#*               
#* Project    : J0005
#*  
#* $Id$
#*
#* initial programmer :  Mario Frasca
#* initial date       :  20080821
#**********************************************************************

__revision__ = "$Rev$"[6:-2]

import sys
if sys.version_info < (2, 4):
    print "I think I need version python2.4 and I was called from %d.%d" % sys.version_info[:2]

import logging, threading, time, datetime, random, math
from tasks import threaded_program 
from SimpleXMLRPCServer import SimpleXMLRPCServer
import socket

from django.core.management.base import BaseCommand
from django.db import connection as django_connection
import  django.db.transaction

import lizard_flooding.models
from perform_task import perform_task

log = logging.getLogger('nens.lizard.flooding.uitvoerder') 

TASK_ADMIN_CREATES_SCENARIO_050   =  50
TASK_COMPUTE_SOBEK_MODEL_120      = 120
TASK_PERFORM_SOBEK_SIMULATION_130 = 130
TASK_COMPUTE_RISE_SPEED_132       = 132
TASK_COMPUTE_MORTALITY_GRID_134   = 134
TASK_SOBEK_PNG_GENERATION_150     = 150
TASK_HISSSM_SIMULATION_160        = 160
TASK_SOBEK_EMBANKMENT_DAMAGE_162  = 162
TASK_HISSSM_PNG_GENERATION_180    = 180
TASK_SOBEK_PRESENTATION_GENERATION_155  = 155
TASK_HISSSM_PRESENTATION_GENERATION_185 = 185


def geometric(p):
   """ Geometric distribution per Devroye, Luc. _Non-Uniform Random Variate
   Generation_, 1986, p 500. http://cg.scs.carleton.ca/~luc/rnbookindex.html
   """

   # p should be in (0.0, 1.0].
   if p <= 0.0 or p > 1.0:
       raise ValueError("p must be in the interval (0.0, 1.0]")
   elif p == 1.0:
     # If p is exactly 1.0, then the only possible generated value is 1.
     # Recognizing this case early means that we can avoid a log(0.0) later.
     # The exact floating point comparison should be fine. log(eps) works just
     # dandy.
     return 1

   # random() returns a number in [0, 1). The log() function does not
   # like 0.  1-random() is in (0, 1].
   U = 1.0 - random.random()

   # Find the corresponding geometric variate by inverting the uniform variate.
   G = int(math.floor(math.log(U, 1.0 - p)))
   return G

class uitvoerder(threaded_program.threaded_program):

    def __init__(self, connection, capabilities, ip, port=8000, hostname=None, seq=None,
                 scenario_range=[0, -1],
                 hisssm_location='c:/Program Files/HIS-SSMv2.4/', hisssm_year=2008,
                 tmp_location='c:/temp/', max_hours=72
                 ):

        threaded_program.threaded_program.__init__(self)
        self.ip = ip
        self.port = port
        self.connection = django_connection
        self.capabilities = capabilities
        self.scenario_range = scenario_range
        self.hostname = hostname
        self.sequential = seq
        self.living = True
        self.hisssm_year = hisssm_year
        self.hisssm_location = hisssm_location
        self.max_hours = max_hours
        self.tmp_location = tmp_location

    def thread_loop(self):
        "main loop...  never ending"
        self.task = self.last_id = self.scenario = 0
        while True:
            self.sleep("main executing loop starts by waiting five second", 5, 0)
            choice = self.choose_and_lock()


            log.debug("got this choice: %s" % (choice,))
            remarks = 'uitvoerder-' + __revision__
            if choice is None:
                self.sleep("main executing loop", 60, 5)
            else: 
                self.last_id, self.task, self.scenario = choice

                log.info("task %s-%s(%s): starting" % (self.scenario, self.task, self.last_id))
                
                success_code, remarks, error_messages = perform_task(self.scenario,
                                                                     self.task,
                                                                     self.sequential,
                                                                     self.max_hours,
                                                                     self.hisssm_year,
                                                                     self.hisssm_location,
                                                                     self.tmp_directory)

                time.sleep(10)
                log.info("task %s-%s(%s): successful=%s" % (self.scenario, self.task, self.last_id, success_code))
                self.close_task(successful=success_code, remarks=remarks+error_messages)
                django.db.transaction.commit_unless_managed()
                scen = lizard.flooding.models.Scenario.objects.get(pk = self.scenario)
                scen.update_status()

                self.task = 0

    def close_task(self, successful, remarks=None):
        #get cursor at begin of function (otherwise there is nothing committed to the database)
        curs = django_connection.cursor()

        params = {}
        params['finished_at'] = datetime.datetime.now()
        params['successful'] = successful
        params['remarks'] = remarks
        params['id'] = self.last_id

        curs.execute("""\
        UPDATE flooding_task SET tfinished=%(finished_at)s, successful=%(successful)s, remarks=%(remarks)s
        WHERE id=%(id)s""",
                     params)
        django.db.transaction.commit_unless_managed()
        log.debug("transaction committed")

    def choose_and_lock(self):
        """give me a connection to the database and a list of tasks you are
        available to perform, I will return you the ID of the task of
        that kind with highest priority and which is waiting the
        longest.  

        make sure you execute this inside of a transaction and not in
        automatic commit mode, otherwise there's no 100% warranty that
        the chosen task will stay reserved for you during the
        milliseconds between one SQL query and the following.

        self.hostname will be stored in the database as taskby

        the return value is the primary key of the task that you will be
        taking care of...  or None if nothing is waiting.
        """
        #get cursor at begin of function (otherwise there is nothing committed to the database)
        curs = django_connection.cursor()

        def minimax_lt(a, b):
            """compares lists with at least three elements.  
            defines a 'miniminimax' ordering...

            a0 > b0:                       a < b
            a0 < b0:                       a > b
            a0 == b0, a1 > b1:             a < b
            a0 == b0, a1 < b1:             a > b
            a0 == b0, a1 == b1, a2 < b2:   a < b
            a0 == b0, a1 == b1, a2 > b2:   a > b

            used for lists with structure priority:task:date|Tail
            """

            #max priority
            a1, b1 = a[0], b[0]
            if a1 > b1: return -1
            if a1 < b1: return 1
            #max task
            a2, b2 = a[1], b[1]
            if a2 > b2: return -1
            if a2 < b2: return 1
            #lowest date (wait longest)
            a3, b3 = a[2], b[2]
            if a3 < b3: return -1
            if a3 > b3: return 1
            return 0

        # a task can be performed if the one it depends on was
        # successfully excecuted, and the task is not still executing.
        task_dependencies = [{'candidate': TASK_COMPUTE_SOBEK_MODEL_120, 'depends_on': TASK_ADMIN_CREATES_SCENARIO_050},
                             {'candidate': TASK_PERFORM_SOBEK_SIMULATION_130, 'depends_on': TASK_COMPUTE_SOBEK_MODEL_120},
                             {'candidate': TASK_COMPUTE_RISE_SPEED_132, 'depends_on': TASK_PERFORM_SOBEK_SIMULATION_130},
                             {'candidate': TASK_COMPUTE_MORTALITY_GRID_134, 'depends_on': TASK_COMPUTE_RISE_SPEED_132},
                             {'candidate': TASK_HISSSM_SIMULATION_160, 'depends_on': TASK_COMPUTE_MORTALITY_GRID_134},
                             {'candidate': TASK_SOBEK_EMBANKMENT_DAMAGE_162, 'depends_on': TASK_HISSSM_SIMULATION_160},
                             {'candidate': TASK_SOBEK_PNG_GENERATION_150, 'depends_on': TASK_PERFORM_SOBEK_SIMULATION_130},
                             {'candidate': TASK_HISSSM_PNG_GENERATION_180, 'depends_on': TASK_SOBEK_EMBANKMENT_DAMAGE_162},
                             {'candidate': TASK_HISSSM_PRESENTATION_GENERATION_185, 'depends_on': TASK_HISSSM_PNG_GENERATION_180},
                             {'candidate': TASK_SOBEK_PRESENTATION_GENERATION_155, 'depends_on': TASK_SOBEK_PNG_GENERATION_150},
                             ]
        
        # human approval (task 190) comes after both 185 and 155.

        log.debug("perform series of queries to select all waiting tasks")

        curs.execute("LOCK TABLE flooding_task IN SHARE MODE NOWAIT")

        low, high = self.scenario_range
        waiting_tasks = []
        for dependency in task_dependencies:
            if dependency['candidate'] not in self.capabilities: continue
            curs.execute("""\
    SELECT s.calcpriority, %(candidate)s, t.tfinished, t.scenario_id  AS type_fk 
    FROM flooding_task t, flooding_scenario s
    WHERE t.scenario_id = s.id
    AND (t.tasktype_id=%(depends_on)s AND NOT (t.tfinished IS NULL) AND t.successful=TRUE 
    AND NOT t.scenario_id IN 
      (SELECT scenario_id FROM flooding_task WHERE tasktype_id=%(candidate)s AND (successful=TRUE OR successful IS NULL)))
    """, dependency)
            waiting = curs.fetchall()
            if low != 0:
                waiting = [(p, c, f, s) for (p, c, f, s) in waiting if s >= low]
            if high != -1:
                waiting = [(p, c, f, s) for (p, c, f, s) in waiting if s <= high]
            log.debug("candidate-> %s: %s" % (dependency['candidate'], waiting))
            waiting_tasks.extend(waiting)

        if not waiting_tasks: 
            log.debug("no waiting tasks for me")
            django.db.transaction.commit_unless_managed()
            return None

        params = {}
        # the 'minimax_lt' function defines the choosing cryterium
        waiting_tasks.sort(minimax_lt)
        while True:
            index_of_chosen_task = geometric(0.25)
            if index_of_chosen_task < len(waiting_tasks):
                break
        _, params['task_type'], _, params['scenario_id'] = chosen = waiting_tasks[index_of_chosen_task]

        params['started_at'] = datetime.datetime.now()
        params['taskby'] = self.hostname

        curs.execute("SELECT NEXTVAL('flooding_task_id_seq')")
        params['task_id'] = curs.fetchone()[0]
        params['remarks'] = "reserved and locked by uitvoerder-" + __revision__

        log.debug("going to reserve this task: %s" % params)

        curs.execute("""\
    INSERT INTO flooding_task 
    (id, scenario_id, tasktype_id, creatorlog, tstart, remarks) 
    VALUES 
    (%(task_id)s, %(scenario_id)s, %(task_type)s, %(taskby)s, %(started_at)s, %(remarks)s)""", 
                     params)

        log.debug("about to COMMIT the INSERT")
        django.db.transaction.commit_unless_managed()
        log.debug("COMMIT succeded")

        return params['task_id'], params['task_type'], params['scenario_id']

    def thread_serve(self):
        "start the xmlrpc server - returns when server is stopped"

        server = SimpleXMLRPCServer((self.ip, self.port))
        server.allow_reuse_address = True
        server.allow_none = True

        server.register_introspection_functions()

        def status_function():
            """returns a pair describing the status of this 'uitvoerder'

            first element:  the id of the last task executed
            second element: the type of the task being executed / or None"""
            return (self.last_id, self.task)

        def id_function():
            "identify this 'uitvoerder'"
            if self.sequential:
                return "%(hostname)s-%(sequential)s" % self.__dict__
            else:
                return self.hostname

        server.register_function(status_function, 'status')
        server.register_function(id_function, 'id')

        server.serve_forever()

def main(args, options):

    
    [handler.setLevel(options['loglevel']) for handler in logging.getLogger().handlers]

    #get cursor at begin of function (otherwise there is nothing committed to the database)
    curs = django_connection.cursor()
    
    log.debug("looking in DB for uitvoerder %(hostname)s" % options)
    try:
        if options['sequential']:
            curs.execute("SELECT id, seq FROM flooding_taskexecutor WHERE name=%(hostname)s AND seq=%(sequential)s", 
                         options)
        else:
            curs.execute("SELECT id, seq FROM flooding_taskexecutor WHERE name=%(hostname)s", 
                         options)
        options['uit_id'], options['sequential'] = curs.fetchone()
    except TypeError, e:
        raise ValueError("database contains no taskexecutor where name[/seq]=(name=%(hostname)s AND seq=%(sequential)s)" % options)
    if curs.fetchone():
        raise ValueError("database contains multiple uitvoerders matching name/seq=%(hostname)s/seq=%(sequential)s" % options)

    if options['capabilities']:
        log.debug("capabilities were specified: update the database")
        curs.execute("DELETE FROM flooding_taskexecutor_tasktypes WHERE taskexecutor_id=%(uit_id)s", 
                     options)
        curs.executemany("""\
INSERT INTO flooding_taskexecutor_tasktypes
(taskexecutor_id, tasktype_id) VALUES (%(uit_id)s, %(tt)s)""", 
                         [{'uit_id': options['uit_id'], 'tt': tt} 
                          for tt in options['capabilities']])
        django.db.transaction.commit_unless_managed()
    else:
        log.debug("capabilities were not specified: retrieve from database")
        curs.execute("""\
SELECT tasktype_id 
FROM flooding_taskexecutor_tasktypes
WHERE taskexecutor_id=%(uit_id)s""", 
                     options)
        options['capabilities'] = [i[0] for i in curs.fetchall()]
        pass

    if options['x_port']:
        log.debug("x-port was specified: update the database")
        curs.execute("UPDATE flooding_taskexecutor SET port=%(x_port)s WHERE id=%(uit_id)s", 
                      options)
        django.db.transaction.commit_unless_managed()
        pass
    else:
        log.debug("x-port was not specified: retrieve from database")
        curs.execute("SELECT port FROM flooding_taskexecutor WHERE id=%(uit_id)s", 
                      options)
        options['x_port'] = curs.fetchone()[0]
        pass

    options['x_ip'] = socket.gethostbyname(socket.gethostname())
    options['revision'] = __revision__
    log.debug("""UPDATE flooding_taskexecutor
                 SET ipaddress=%(x_ip)s, 
                     active=TRUE, 
                     revision=%(revision)s 
                 WHERE id=%(uit_id)s""" % options)
    curs.execute("""UPDATE flooding_taskexecutor
                    SET ipaddress=%(x_ip)s, 
                        active=TRUE, 
                        revision=%(revision)s 
                    WHERE id=%(uit_id)s""", 
                 options)
    django.db.transaction.commit_unless_managed()

    if options['capabilities'] == []:
        raise ValueError("uitvoerder is not able of doing anything - not starting")

    log.info("starting uitvoerder %(uit_id)s:%(hostname)s[%(sequential)s] on tasktypes %(capabilities)s - available at http://%(x_ip)s:%(x_port)s" % options)

    log.debug("options = %s" % options)
    u = uitvoerder(connection=django_connection,
                   capabilities=options['capabilities'], 
                   ip=options['x_ip'], 
                   port=options['x_port'], 
                   hostname=options['hostname'],
                   seq=options['sequential'],
                   scenario_range = options['scenario_range'],
                   hisssm_location = options['hisssm_location'],
                   hisssm_year = options['hisssm_year'],
                   tmp_location = options['tmp_location'],
                   max_hours = options['max_hours']
                   )
    u.start()

from optparse import make_option


class Command(BaseCommand):
    help = ("""\
uitvoerder.py [options]

for example:
./uitvoerder.py --capabilities 120 --capabilities 130 --scenario-range 50 58 --sequential 1
""")

    option_list = BaseCommand.option_list + (
    make_option('--info', help='be sanely informative - the default', action='store_const', dest='loglevel', const=logging.INFO, default=logging.INFO),
    make_option('--debug', help='be verbose', action='store_const', dest='loglevel', const=logging.DEBUG),
    make_option('--quiet', help='log warnings and errors', action='store_const', dest='loglevel', const=logging.WARNING),
    make_option('--extreme-debugging', help='be extremely verbose', action='store_const', dest='loglevel', const=0),
    make_option('--silent', help='log only errors', action='store_const', dest='loglevel', const=logging.ERROR),

    make_option('--hisssm-location', default='C:/Program Files/HIS-SSMv2.4/', help='the root of the his-ssm installation'),
    make_option('--hisssm-year', default=2008, help='the year of hisssm simulation data', type='int'),
    make_option('--x-port', help='the xmlrpc server port (if not given, taken from db)', default=None, type='int'),
    make_option('--capabilities', help='tasks that uitvoerder can perform', default=[], action='append', type='int'),

    make_option('--scenario-range', help='DEBUG: limit action on these scenarios', nargs=2, type='int', default=[0, -1]),
    make_option('--sequential', help='use this if you need more than one uitvoerder on this workstation', type='int', default=None),

    make_option('--tmp_location', default='C:/temp/', help='the root of the temporary files for task execution'),
    make_option('--max_hours', help='maximum hours for a single task ', default=72, type='int'))


    def handle(self, *args, **options):
        print options
        options['hostname'] = socket.gethostname().lower()
        if len(options['capabilities']) == 0:
            self.stdout.write(self.help)
        else:
            main(args, options)            


