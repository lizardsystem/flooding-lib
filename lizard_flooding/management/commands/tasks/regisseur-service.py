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
#* Purpose    : script meant to be registered as windows service
#* Usage      : sc.exe regisseur-service.py lfregisseur
#*               
#* Project    : J0005
#*  
#* $Id: regisseur-service.py 5854 2009-03-25 11:34:06Z Mario $
#*
#* initial programmer :  Mario Frasca
#* initial date       :  20090325
#**********************************************************************

__revision__ = "$Rev: 5854 $"[6:-2]

import sys
import ConfigParser
import os


import win32serviceutil
import win32service
import win32event
import servicemanager
import socket

class Values:
    """simulates the optparse.Values class
    """
    pass

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "Regisseur"
    _svc_display_name_ = "Lizard Flooding - Regisseur"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        self.notStopped = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.notStopped = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        import logging

        log = logging.getLogger('nens.lizard.kadebreuk.regisseur.start') 
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s',) 

        [handler.setLevel(logging.DEBUG) for handler in logging.getLogger().handlers]
        log.debug("reading regisseur configuration " + os.environ['SYSTEMROOT'] + "/lizardflooding.ini")
        f = file(os.environ['SYSTEMROOT'] + "/lizardflooding.ini")
        config = ConfigParser.ConfigParser()
        config.readfp(f)

        section = 'regisseur'

        import logging.handlers
        logfile = config.get(section, 'logfile') 
        rotatingHandler = logging.handlers.RotatingFileHandler(logfile, maxBytes=1024*1024, backupCount=5)

        # create formatter
        formatter = logging.Formatter("%(asctime)s; %(name)s; %(levelname)s; %(message)s")
        # add formatter to ch
        rotatingHandler.setFormatter(formatter)
        logging.getLogger('').addHandler(rotatingHandler)

        log.info('*****Start service. Logging initialised*****')
        

        try:
            options = Values()

            options.loglevel = logging.INFO
            loglevel = config.get(section, 'loglevel')
            if loglevel == "DEBUG":
                options.loglevel = logging.DEBUG
            elif loglevel == "WARNING":
                options.loglevel = logging.WARNING
            elif loglevel == "ERROR":
                options.loglevel = logging.ERROR
            rotatingHandler.setLevel(options.loglevel)
            
            options.host = config.get(section, 'host') 
            options.dbport = int (config.get(section, 'port') ) 
            options.dbname = config.get(section, 'dbname') 
            options.user = config.get(section, 'user') 
            options.password = config.get(section, 'password')
            options.owner = config.get(section, 'owner-email')

            #import socket
            options.id = socket.gethostname().lower()

            import regisseur
            log.info("about to start regisseur %s" % options.__dict__)
            regisseur.main(options, args=[])
            log.info("regisseur started")

            log.debug('loop until service is killed')
            import time
            while self.notStopped:
                 time.sleep(15)
                 log.debug('still looping until service is stopped')
            log.info('leaving loop. stop service')

            
        except Exception, e:
            log.error("service regisseur stopt with exception %s", e)
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_WARNING_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, " stopt with error " + e)
                )

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)
