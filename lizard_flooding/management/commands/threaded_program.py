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
#* Library    : base class for threaded programs
#* Purpose    : derive from this to implement a multithreaded program 
#*              where threads are not supposed to return.
#*               
#* Project    : J0005
#*  
#* $Id$
#*
#* initial programmer :  Mario Frasca
#* initial date       :  20080909
#**********************************************************************

__revision__ = "$Rev$"[6:-2]

import sys
if sys.version_info < (2, 4):
    print "I think I need version python2.4 and I was called from %d.%d" % sys.version_info[:2]

import logging, threading

log = logging.getLogger('nens.lizard.kadebreuk') 

class threaded_program:

    def __init__(self, tasks=None):
        if tasks == None:
            tasks = [i for i in dir(self) 
                     if i.startswith('thread_') and callable(getattr(self, i))]
        self.threads = {}
        for key in tasks:
            self.threads[key] = threading.Thread(name=key, target=getattr(self, key))

    def start(self):
        for t in self.threads.values():
            t.start()

        threading.Thread(target=self.watchdog).start()
    
    def sleep(self, name, length, more_or_less):
        "sleeps length seconds (more or less)"

        import random
        really = length - more_or_less + random.random()*more_or_less*2
        log.info(name + ' sleeping')
        import time
        time.sleep(really)
        log.info(name + ' woke up')

    def watchdog(self):
        "ensures all threads in self.threads are running"
        
        log.debug('starting watchdog thread')
        while True:
            try:
                self.sleep('watchdog', 120, 0)
                for key in [key for key, t in self.threads.items() if not t.isAlive()]:
                    log.warning("thread %s crashed and watchdog is restarting it" % key)
                    sys.stderr.flush()
                    self.threads[key] = threading.Thread(name=key, target=getattr(self, key))
                    self.threads[key].start()
            except Exception, e:
                log.warning("ignoring exception in watchdog thread: " + str(e))
