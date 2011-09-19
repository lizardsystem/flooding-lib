#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the lizard_waterbalance Django app.
#
# The lizard_waterbalance app is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# the lizard_waterbalance app.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Bastiaan Roos
#
#******************************************************************************



from optparse import make_option
import csv

from django.core.management.base import BaseCommand

from lizard_flooding.models import Breach, Scenario



class Command(BaseCommand):
    help = ("""\
uitvoerder.py [options]

for example:
./uitvoerder.py --capabilities 120 --capabilities 130 --scenario-range 50 58 --sequential 1
""")
    option_list = BaseCommand.option_list 

    option_list += make_option('--csv-location', help='file location of csv-file with scenario information')

    def handle(self, *args, **options):
        print(dir(args))
        csv_file = file('c:\\_source\\import_scenario.csv', 'r')
        scenarios = csv.DictReader(csv_file)
        for scenario in scenarios:
            print scenario
            breach = Breach.objects.get(pk=int(scenario['breach_id']))
            print breach
            post = {}
            post['action'] = 'post_newscenario'

            post['name'] = scenario['name']
            post['remarks'] = scenario['remarks']
            post['project_fk'] = scenario['project_fk']
            post['rbreach_id'] = scenario['breach_id']
            post['inundationmodel'] = scenario['inundationmodel']

            
            


name	test automatisch uploaden
remarks	test automatisch uploaden

project_fk	9
breach_id	10481
inundationmodel	239

#optional calculated
extwmaxlevel	automatisch
extwrepeattime	4000

extwbaselevel	automatisch
pitdepth	automatisch

#from database
decheight	automatisch
extw_type	2
extwrepeattime_ini	4000

#optional, otherwise default
calcpriority	20

strategyId	322

brdischcoef	1
brf1	1,3
brf2	0,04
ucritical	0,2

tsim	1 d 0:00
tsim_ms	86400000
start_calculation	0

tstorm	1970-01-02T10:59:59
tstorm_ms	125999999
tpeak	1970-01-01T04:00:00
tpeak_ms	14400000

tdeltaphase_ms	0


bottomlevelbreach	koppeling breach?

extwmaxlevel_ini	automatisch
widthbrinit	10
tmaxdepth	1:00
tmaxdepth_ms	3600000
tstartbreach	0:00
tstartbreach_ms	0




#not supported yet
loccutoffs	
measures







       
        
         
