#!c:/python25/python.exe
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
#* Purpose    : this is a supervisor for the various slaves...
#* Function   : main
#* Usage      : regisseur.py --help
#*               
#* Project    : J0005
#*  
#* $Id$
#*
#* initial programmer :  Mario Frasca
#* initial date       :  20080901
#**********************************************************************

__revision__ = "$Rev$"[6:-2]

import sys
if sys.version_info < (2, 4):
    print "I think I need version python2.4 and I was called from %d.%d" % sys.version_info[:2]

import logging, threading, time, datetime, random
from datetime import datetime, timedelta

sys.path.append('..')

from django.core.management import setup_environ
import lizard.settings
setup_environ(lizard.settings)

from lizard.flooding.models import TaskExecutor, Task

from django.db import connection as django_connection
import  django.db.transaction
from django.db.models import Q

log = logging.getLogger('nens.lizard.kadebreuk.regisseur') 

import threaded_program

class regisseur(threaded_program.threaded_program):

    def __init__(self, owner):
        threaded_program.threaded_program.__init__(self)
        self.owner = owner

    def send_warning(self, subject, body):
        """
        sends a warning email to the door keeper.

        body: the body of the email that will be sent.
        """

        import smtplib
        import email
        import socket
        me = 'regisseur@' + socket.gethostname().lower() + ".nelen-schuurmans.nl"
        msg = email.message_from_string(body)
        msg['Subject'] = subject
        msg['From'] = me
        msg['To'] = self.owner
        msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
        log.info("sending warning to owner " + self.owner)

        try:        
            s = smtplib.SMTP('mail.nelen-schuurmans.nl')
            s.sendmail(me, [self.owner], msg.as_string())
            s.close()
        except Exception, e:
            log.info("error sending warning to owner. " )

    def thread_copy(self):
        "makes a dump of the database to the mirror"

        conn = django_connection
        while True:
            curs = conn.cursor()
            curs.execute("LOCK TABLE flooding_task IN ROW EXCLUSIVE MODE")
            django.db.transaction.commit_unless_managed()
            self.sleep('copy', 86400, 300)
            pass
        pass

    def thread_watch_slaves(self):
        "all slaves are still alive - or warns door keeper"
        import xmlrpclib
        
        conn = django_connection
        status = {}
        while True:
            curs = conn.cursor()
            #is dit echt nodig? curs.execute("LOCK TABLE flooding_task IN ROW EXCLUSIVE MODE")
            task_executors = TaskExecutor.objects.filter(active=True)
            failing = []
            for task_executor in task_executors:
                log.debug("is uitvoerder %i still alive?" % task_executor.id)
                
                proxy = xmlrpclib.ServerProxy("http://%s:%d" %(task_executor.ipaddress, task_executor.port))
                try:
                    log.debug("remote %i returned: %s" % (task_executor.id, proxy.status()))
                    log.info("uitvoerder %i is still alive" % task_executor.id)
                    status[task_executor.id] = 0
                except Exception, e:
                    task_executor.message = str(e)
                    log.warning("uitvoerder %s died with message %s" % (task_executor.ipaddress, task_executor.message))
                    failing.append(task_executor)
                    status.setdefault(task_executor.id, 0)
                    status[task_executor.id] += 1
                    task_executor.save()

            if failing:
                mark_dead = []
                lines = ['found uitvoerders which were marked as active and which do not serve xmlrpc calls...  they may be dead in fact.  please have a look!',
                         '',
                         "'|'-separated representation of the data.",
                         "| *id* | *name* | *URL* | *error message* |"
                         ]
                for task_executor in failing:
                    if status[task_executor.id] == 2:
                        lines.append("| %(id)s | %(name)s | http://%(ipaddress)s:%(port)d | %(message)s |" %task_executor.__dict__)
                        mark_dead.append(task_executor)
                        status[task_executor.id] = -1

                if mark_dead:
                    for task_executor in mark_dead:
                        task_executor.active = False
                        task_executor.save()
                    self.send_warning('regisseur found dead uitvoerders', '\n'.join(lines))
                pass

            #django.db.transaction.commit_unless_managed()
            self.sleep('watch_slaves', 600, 10)
            pass
        pass

    def thread_watch_lost(self):
        """finds lost tasks and frees them for other slaves

        tasks with tfinished NULL and successful NULL are currently
        being performed.  this thread watches that they don't stay in
        this situation for too long (longer than one day is too
        long)...  if any is found in this situation, it is marked as
        completed now, failed (successful=FALSE), and remarked that
        the regisseur took action about it.  an email is sent to the
        owner of this regisseur.
        """

        self.sleep('pre-start watch_lost', 10, 10)
        conn = django_connection
        while True:
            curs = conn.cursor()
            curs.execute("LOCK TABLE flooding_task IN ROW EXCLUSIVE MODE")
            once_upon_a_time = datetime.now() - timedelta(3,0)
            hanging = Task.objects.filter(Q(tfinished = None), Q(successful = None), 
                                          tasktype__in = (120, 130, 132, 134, 150, 155, 160, 162, 180, 185),
                                          tstart__lt = once_upon_a_time)
            
            log.debug("lost: hanging=%s" % str(hanging))
            if hanging:
                for task in hanging:
                    task.tfinished = datetime.now()
                    task.remark = 'regisseur (Rev: %s) marked this task as finished.' % __revision__
                    task.successful = False
                    task.save()

                log.info("marked lost tasks %s as free" % str(hanging.values_list('id',flat=True)))
                lines = ['found lost tasks in database and marked them back as available.',
                         '',
                         "'|'-separated representation of the data.",
                         "| *id* | *scenario_fk* | *type_fk* | *taskby* | *tstart* |"
                         ]
                for task in hanging:
                    lines.append("| %(task_id)s | %(scenario_id)s | %(tasktype_id)s | %(creatorlog)s | %(tstart)s |" % task.__dict__)
                self.send_warning('regisseur found lost tasks', '\n'.join(lines))
                pass
            django.db.transaction.commit_unless_managed()
            self.sleep('watch_lost', 60, 10)
            pass
        pass

    def thread_watch_failing(self):
        """finds tasks deterministically failing and parks them

        non-parked pairs (scenario, task) that have failed three or
        more times and have never succeeded will be parked now.  this
        is done by adding a mock task with the same (scenario, task)
        pair, taskby the 'regisseur', finished now but with
        successful=NULL.  this will prevent the pair to be performed
        again.
        """

        #self.sleep('pre-start watch_failing', 10, 10)
        conn = django_connection
        while True:

            curs = conn.cursor()
            curs.execute("LOCK TABLE flooding_task IN ROW EXCLUSIVE MODE")
            curs.execute("""SELECT scenario_id AS scenario_id, 
                                            tasktype_id AS tasktype_id, 
                                            COUNT(*) AS failures 
                                     FROM flooding_task 
                                     WHERE successful=FALSE 
                                     AND NOT ROW(scenario_id, tasktype_id) 
                                         IN (SELECT scenario_id, tasktype_id 
                                             FROM flooding_task 
                                             WHERE (successful IS NULL AND tfinished IS NOT NULL) 
                                                OR successful=TRUE)
                                     GROUP BY scenario_id, tasktype_id
                                     HAVING COUNT(*)>1""")
            failing = [{'scenario_id':row[0], 'tasktype_id':row[1], 'failures' : row[2]} for row in curs.fetchall()]
            log.info("lost: failing=%s" % str(failing))
            if failing:
                for d in failing:
                    d['now'] = datetime.now()
                    d['remarks'] = "regisseur (Rev: %s) parked task after %d failures" % (__revision__, d['failures'])
                    curs.execute("""INSERT INTO flooding_task
                                    (scenario_id, tasktype_id, creatorlog, tstart, tfinished, successful, remarks)
                                    VALUES
                                    (%(scenario_id)s, %(tasktype_id)s, 'regisseur', %(now)s, %(now)s, NULL, %(remarks)s)""",
                                 d)
                log.info("marked failing tasks %s as parked" % str(["%(scenario_id)s-%(tasktype_id)s" % i for i in failing]))

                lines = ['found failing tasks in database',
                         '',
                         "partial '|'-separated representation of the rows just added.",
                         "| *scenario_fk* | *type_fk* | *tstart* | *remarks* |",
                         ]
                for d in failing:
                    lines.append("| %(scenario_id)s | %(tasktype_id)s | %(now)s | %(remarks)s |" % d)
                django.db.transaction.commit_unless_managed()
                #self.send_warning('regisseur found failing tasks', '\n'.join(lines))

            else:
                log.debug('no failing tasks found')
            django.db.transaction.commit_unless_managed()
            self.sleep('watch_failing', 600, 10)

def main(options, args):

    [handler.setLevel(options.loglevel) for handler in logging.getLogger().handlers]

    log.debug("options = %s" % options)
    u = regisseur(options.owner)
    u.start()
    pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s',) 
    from optparse import OptionParser
    parser = OptionParser("""\
uitvoerder.py [options]

for example:
./regisseur.py --owner lizard_admin@nelen-schuurmans.nl
""")

    parser.add_option('--info', help='be sanely informative - the default', action='store_const', dest='loglevel', const=logging.INFO, default=logging.INFO)
    parser.add_option('--debug', help='be verbose', action='store_const', dest='loglevel', const=logging.DEBUG)
    parser.add_option('--quiet', help='log warnings and errors', action='store_const', dest='loglevel', const=logging.WARNING)
    parser.add_option('--extreme-debugging', help='be extremely verbose', action='store_const', dest='loglevel', const=0)
    parser.add_option('--silent', help='log only errors', action='store_const', dest='loglevel', const=logging.ERROR)

    parser.add_option('--owner', help='the email address of the door keeper')

    (options, args) = parser.parse_args()
    log.debug("regisseur called with options: %s" % str(options.__dict__))

    if not (options.owner):
        parser.print_help()
    else:
        main(options, args)
