#!c:/python25/python.exe
# -*- coding: utf-8 -*-
#***********************************************************************
#
# This file is part of Lizard Flooding 2.0.
#
# Lizard Flooding 2.0 is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Lizard Flooding 2.0 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lizard Flooding 2.0.  If not, see
# <http://www.gnu.org/licenses/>.
#
# Copyright 2008, 2009 Mario Frasca
#
#***********************************************************************
# this script implements task 120: alter a sobek model according to
# the data contained in a specific scenario
#
# $Id$
#
# initial programmer :  Mario Frasca
# initial date       :  <yyyymmdd>
#***********************************************************************

__revision__ = "$Rev$"[6:-2]

"""this script gets a sobek model and a breach description, it
computes an altered sobek model where the breach has been added.  the
model can be run to compute the short term effects of the breach.

please refer to LizardKadebreukRekencentrumSobekKoppelen for more
details.
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import logging, math, os, datetime
from nens import sobek, asc

import lizard_flooding as flooding
import lizard_base as base
from osgeo import osr, ogr, gdal

#TO DO:
sobek.log.setLevel(logging.INFO)
asc.log.setLevel(logging.INFO)

log = logging.getLogger('nens')

DB_SEA = 1
DB_LAKE = 2
DB_CANAL = 3
DB_INNER_LAKE = 4
DB_INNER_CANAL = 5


def add_prefix_to_values_of_attributes(obj, prefix, skip_attribs=[]):
    "adds prefix to values of attributes, except those listed in skip_attribute"

    prefix_attribs = ['bn', 'ci', 'cj', 'dd', 'di', 'en', 'id', 'ml', 'si', ]
    skip_attribs = {'D2FR': ['ci', 'id'],
                    'GLFR': ['dd'],
                    'GLIN': ['id'],
                    'NODE': ['ml'],
                    'D2IN' : ['id' ,'ci']
                    }.get(obj.tag, [])

    for a_name in prefix_attribs:
        if a_name in skip_attribs:
            continue
        if a_name in obj:
            log.debug( "about to add prefix %s to attribute value of a %s: at %s the old value is %s" % (prefix, obj.tag, a_name, [(type(v), v) for v in obj[a_name]]))
            
            obj[a_name] = [prefix+value for value in obj[a_name]]

def add_prefix_to_objects(pool, prefix):
    "adds prefix to all id's in polder sobek model - with minor exceptions..."

    for name, item in pool.items():
        if isinstance(item, sobek.Verbatim):
            continue

        if name.lower() == 'network.d12':
            log.info("network.d12: add prefix to objects inside of 'DOMN', but leave 'DOMN' itself alone")
            for domain in item['DOMN']:
                for obj in domain:
                    add_prefix_to_values_of_attributes(obj, prefix)

        else:
            for obj in item:
                add_prefix_to_values_of_attributes(obj, prefix)

        if name.lower() == 'network.gr':
            log.debug("alter all GRID objects in 'network.gr': in the first TBLE, entries 3, 4 and 5 get the prefix unless entry is ''")
            for obj in item['GRID']:
                table = obj['TBLE'][0]
                for row_no in range(table.rows()):
                    for col_no in [2, 3,4]:
                        if table[row_no, col_no] != '':
                            log.debug( "about to add prefix %s to id in table: at (%d, %d) the old value is %s(%s)" % (prefix, row_no, col_no, str(type(table[row_no, col_no])), table[row_no, col_no]))
                            table[row_no, col_no] = prefix + table[row_no, col_no]

class Scenario:
    """an object of this class is created from a scenario id.

    once created, you can ask it to compute the corresponding sobek model.
    """

    def __init__(self, id, tmp_dir):
        """collects all data describing the scenario from the database
        """

        self.scenario = flooding.models.Scenario.objects.get(id=id)

        # get the only breach.
        breaches = self.scenario.breaches.all()
        if len(breaches) != 1:
            raise ValueError("there are %d breaches at scenario %d (expected 1)" % (len(breaches), id))
        self.breach = breaches[0]

        # get the properties of the link to the breach.
        breachlinkproperties = self.scenario.scenariobreach_set.all()
        if len(breachlinkproperties) != 1:
            raise ValueError("there are %d breaches at scenario %d (expected 1)" % (len(breachlinkproperties), id))
        self.breachlinkproperty = breachlinkproperties[0]

        # get the system settings.
        self.settings = dict([(i.key, i.value) for i in base.models.Setting.objects.all()])

        # make sure we're using the configured coordinates.
        if self.scenario.sobekmodel_inundation.model_srid == 28992:
            #there is an error in the proj.4 library. So in case of  28992 is the next spatial reference WKT string
           srs = "+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs"
        else:
           srs = self.scenario.sobekmodel_inundation.model_srid

        self.breach_length = self.breach.internalnode.distance(self.breach.externalnode)
        self.breach.internalnode.transform(srs)
        self.breach.externalnode.transform(srs)

        self.extern = self.breach.externalnode.x, self.breach.externalnode.y

        self.tmp_dir = tmp_dir

        log.info("create new empty temporary directory %s"%tmp_dir)
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir)
        else:
            files = os.listdir(tmp_dir)
            print files
            for fil in files:
                print fil
                if os.path.isfile(os.path.join(tmp_dir,fil)):
                    print 'remove'
                    os.remove(os.path.join(tmp_dir,fil))
        



    def collect_initial_data(self):
        """collects initial data from the SOBEK description of area to be inundated and external water.
        """

        ##################################################################
        log.info("read the sobek representation of the internal network...")

        self.base = base.models.Setting.objects.get(key='source_dir').value + '/'
        path = self.base + "%(project_fileloc)s/%(model_case)i/" % self.scenario.sobekmodel_inundation.__dict__
        path = path.replace('\\', os.sep)
        sobek.File.setSourceDir(path)
        log.debug("sobek.File.setSourceDir('%s')" % sobek.File.sourcedir)

        log.debug("read the nens.sobek.File objects")
        pool = {}
        files_to_edit = ['boundary.dat', 'control.def', 'friction.dat', 
                         'network.cn', 'network.cp', 'network.cr', 'network.d12', 
                         'network.gr', 'network.st', 'network.tp', 
                         'nodes.dat', 'initial.dat', 'lateral.dat', 'network.me', 
                         'profile.dat', 'profile.def', 'struct.dat', 'struct.def', ]

        for item in os.listdir(sobek.File.getSourceDir()):
            if item == '.svn': continue
            if item.lower() in files_to_edit:
                log.debug("reading sobek.File %s" % item)
                construct = sobek.File 
            else:
                log.debug("reading sobek.Verbatim %s" % item)
                construct = sobek.Verbatim
            pool[item.lower()] = construct(item)

        ##################################################################
        log.debug("choose a few unique identifiers for the objects to be added...")

        # we scan all identifiers that match lkb_[0-9]+ and choose the
        # maximum among them, then start counting from its successor.  in
        # practice?  if there's a lkb_57, we start our identifiers from
        # lkb_0058.  if there's none, we start from lkb_0001

        class NextId:
            def __init__(self, base):
                self.value = base
            def __call__(self):
                self.value += 1
                return "lkb_%04i" % self.value

        import re
        lkbid = re.compile(r'lkb_([0-9]+)')
        rootObjects = []
        for name in files_to_edit:
            log.debug("getting root objects from %s" % name)
            for key in pool[name].keys():
                log.debug("get objects of type '%s'" % key)
                rootObjects.extend(pool[name][key])

        identifiers = [0];
        for item in rootObjects:
            try:
                m = lkbid.match(item.id)
                identifiers.append(int(m.group(1)))
            except (AttributeError, ValueError, TypeError), e:
                log.debug("%s while examining %s" % (str(e), item))
                pass
        log.debug("lkb identifiers: %s" % identifiers)

        nextid = NextId(max(identifiers))
        idpool = {}
        idpool['breach'] = nextid()
        idpool['grid'] = nextid()
        idpool['boundary'] = nextid()
        idpool['intern'] = nextid() # overridden if we reuse an internal node 
        idpool['extern'] = nextid()

        log.debug("lkb idpool: %s" % idpool)
        self.idpool = idpool
        self.nextid = nextid
        self.pool = pool
        self.files_to_edit = files_to_edit
        self.start_of_simulation = datetime.datetime(2000, 1, 1, 0, 0, 0)

        levels = [i.value for i in self.breachlinkproperty.waterlevelset.waterlevel_set.all()]
        try:
            self.min_water_level = min(levels)
        except:
            self.min_water_level = None
        try:
            self.max_water_level = max(levels)
        except:
            self.max_water_level = None

        self.lowest_crest_level = self.breachlinkproperty.bottomlevelbreach
        self.initial_breach_width = self.breachlinkproperty.widthbrinit
        self.profile_depth = self.breachlinkproperty.bottomlevelbreach
        self.extwaters_area = self.breach.externalwater.area
        self.time_of_breach_start = datetime.timedelta(self.breachlinkproperty.tstartbreach, 0)
        self.time_of_breach_max_depth = datetime.timedelta(self.breachlinkproperty.tmaxdepth, 0)
        self.duration_of_simulation = datetime.timedelta(self.scenario.tsim, 0)

    def save_sobek_model(self):
        ########################################################################
        log.info("write altered model to central destination directory")

        log.debug("create output zipfile")
        from zipfile import ZipFile, ZIP_DEFLATED
        self.base = base.models.Setting.objects.get(key='destination_dir').value + '/'
        
        output_dir_name = os.path.join(self.base, self.scenario.get_rel_destdir())
        output_file_name = os.path.join(output_dir_name, "model.zip")
        if not os.path.isdir( output_dir_name ):
            os.makedirs( output_dir_name )
        output_file = ZipFile(output_file_name, 
                              mode="w", compression=ZIP_DEFLATED)

        log.debug("write elevation and friction grids")
        self.elev_grid.writeToStream(output_file, self.new_elev_name)
        elevation_resultfile = file(os.path.join(self.tmp_dir,"elevation_grid.asc"),'w')
        self.elev_grid.writeToStream(elevation_resultfile, self.new_elev_name)
        elevation_resultfile.close()
        if self.frict_grid:
            self.frict_grid.writeToStream(output_file, self.new_frict_name)

        log.debug("write all nens.sobek.File and nens.sobek.Verbatim objects")
        for to_close in self.pool.values():
            to_close.writeToStream(output_file)
        output_file.close()
        
        result, new = self.scenario.result_set.get_or_create(resulttype=flooding.models.ResultType.objects.get(pk=26))
        result.resultloc = os.path.join(self.scenario.get_rel_destdir(),"model.zip")
        result.save()
        

    def compute_sobek_model(self):  

        ##################################################################
        """

        """
        log.info("expand the network with the external water...")
        pool2 = None

        if self.breach.externalwater.type == DB_SEA:
            ##################################################################
            log.info("external water is: sea")

            # boundary.dat
            flbo = sobek.Object("FLBO id '%(extern)s' ty 0 h_ wt 1 0 0 PDIN 0 0 pdin flbo" % self.idpool)
            for i in self.breachlinkproperty.waterlevelset.waterlevel_set.all().order_by('time'):
                flbo.addRow( [datetime.datetime(2000,1,1) + datetime.timedelta(i.time,0), i.value] )
            self.pool['boundary.dat'].append(flbo)

            # network.tp
            node_ext = sobek.Object("NODE id '%(extern)s' nm 'the sea' node" % self.idpool)
            node_ext['px'], node_ext['py'] = self.breach.externalnode.x, self.breach.externalnode.y
            self.pool['network.tp'].append(node_ext)

            # network.cn
            flbo = sobek.Object("FLBO id '%(extern)s' ci '%(extern)s' flbo" % self.idpool)
            self.pool['network.cn'].append(flbo)

        elif self.breach.externalwater.type == DB_CANAL or self.breach.externalwater.type == DB_INNER_CANAL:
            ##################################################################
            log.info("external water is: canal or inner_cannel")

            log.info("read the sobek representation of the external network...")

            sobek.File.setSourceDir(self.base + "%(project_fileloc)s/%(model_case)i/" % self.breachlinkproperty.sobekmodel_externalwater.__dict__)
            pool2 = {}
            for filename in self.files_to_edit:
                pool2[filename] = sobek.File(filename)

            # in initial.dat staan er twee type objecten: FLIN en GLIN. de
            # FLIN beschrijven de ... en hun 'lv ll' parameter is de
            # maximale hoogte van het water...

            log.debug("initial situation for water height in the external water is equal to max_water_level")
            for obj in pool2['initial.dat']['FLIN']:
                obj['lv ll'][1] = self.breachlinkproperty.extwmaxlevel
                obj['ty'][0] = 1

            # GLIN dat is een global object...  het mag niet twee keer
            # voorkomen, eentje moet verwijderd worden (een GLIN object,
            # niet het hele bestand initial.dat...)

            log.debug("removing the GLIN from pool2 before merging the pools")
            try:
                del pool2['initial.dat']['GLIN', 0]
            except KeyError:
                log.debug("pool2 GLIN had already been purged")

            
            #TO DO: verkeerd uitgelijnd. In oude code opzoeken waarvoor dit diende
            '''
            else:
                if node_id == None:
                    raise ValueError("no candidate cutoff location")
                log.debug("done examining cutoff locations")
            '''
        ##########################
            # still in DB_CANAL || DB_INNER_CANAL

            log.debug("get the coordinates of the external node in the 'canal' network")
            node_id = self.breachlinkproperty.breach.breachsobekmodel_set.get(sobekmodel__scenariobreach = self.breachlinkproperty).sobekid
            found = False
            for grid in pool2['network.gr']['GRID']:
                table = grid['TBLE'][0]
                for row_no in range(table.rows()):
                    if table[row_no, 3] == node_id:
                        self.extern = table[row_no, 5], table[row_no, 6]
                        found = True
                        break
                if found: 
                    break
            
            if not found:
                raise ValueError("the external node %s does not exist" % node_id)

            log.debug("add 'c_' prefix to all id's in canal sobek model")
            add_prefix_to_objects(pool2, 'c_')

            self.idpool['extern'] = 'c_' + node_id

            log.debug("copy canal objects into polder pool of objects")
            for name in self.files_to_edit:
                if name == 'network.d12':
                    try:
                        source_container = pool2[name]['DOMN'][0]
                    except IndexError:
                        log.debug("there is no source DOMN: %s" % repr(pool2[name].content))
                        continue
                    destination_container = self.pool[name]['DOMN'][0]
                else:
                    source_container = pool2[name]
                    destination_container = self.pool[name]

                for obj in source_container:
                    destination_container.addObject(obj)

            try:
                log.debug('check whether the external node is a node or a point')
                self.pool['network.tp']['NODE', self.idpool['extern']]
            except KeyError:
                log.debug("it's a calculation point, adding NDLK object to network.tp in external water")
                ndlk = sobek.Object(tag='NDLK', id=self.idpool['extern'])
                ndlk['nm'] = 'promoted external point'
                ndlk['px'], ndlk['py'] = self.extern
                ndlk['ci'] = grid['ci'][0]
                ndlk['lc'] = table[row_no, 0]
                self.pool['network.tp'].addObject(ndlk)

            log.debug("set global water level to max water level")
            self.pool['initial.dat']['GLIN'][0]['FLIN'][0]['lv ll'][1] = self.max_water_level
            if self.pool['initial.dat']['GLIN'][0]['FLIN'][0]['ty'][0] != 1:
                log.warning("correcting data: we work with water height, not water depth.")
                self.pool['initial.dat']['GLIN'][0]['FLIN'][0]['ty'][0] = 1 


        elif self.breach.externalwater.type == DB_LAKE or self.breach.externalwater.type == DB_INNER_LAKE :
            ##################################################################
            log.info("external water is: LAKE")

            # bij het modelleren van 'lake' worden twee punten
            # gedefinieerd, een 'peak' en een 'mean'.  twee
            # watergangen verbinden deze twee punten.  de 'peak'
            # plaatsen we waar de 'extern' ligt, de 'mean' 10 meters
            # naar zuiden, 10 meter naar westen.
            
            extern_mean = [self.extern[0] - 10, self.extern[1] - 10]
            self.idpool['extern_mean'] = self.nextid()
            self.idpool['branch_mean'] = self.nextid()
            self.idpool['branch_peak'] = self.nextid()
            self.idpool['prof_high_peak'] = self.nextid()
            self.idpool['prof_high_mean'] = self.nextid()
            self.idpool['prof_low_peak'] = self.nextid()
            self.idpool['prof_low_mean'] = self.nextid()
            self.idpool['lake_prof'] = self.nextid()

            # this is not the mean level, it's the level for the
            # 'mean' point, calculated as minimal level minus half
            # distance among max and min levels
            level_mean = self.min_water_level - 0.5 * abs(self.max_water_level - self.min_water_level)

            # network.tp
            node_ext = sobek.Object("NODE id '%(extern)s' nm 'the innerlake 1' node" % self.idpool)
            node_ext['px'], node_ext['py'] = self.extern
            self.pool['network.tp'].append(node_ext)

            node_ext = sobek.Object("NODE id '%(extern_mean)s' nm 'the innerlake 2' node" % self.idpool)
            node_ext['px'], node_ext['py'] = extern_mean
            self.pool['network.tp'].append(node_ext)

            branch_ext = sobek.Object("BRCH id '%(branch_peak)s' nm '' bn '%(extern_mean)s' en '%(extern)s' al 10 brch" % self.idpool)
            self.pool['network.tp'].append(branch_ext)

            branch_ext = sobek.Object("BRCH id '%(branch_mean)s' nm '' bn '%(extern_mean)s' en '%(extern)s' al 10 brch" % self.idpool)
            self.pool['network.tp'].append(branch_ext)

            #network.gr (grid)
            branch_ext = sobek.Object("GRID id '%(branch_peak)s' ci '%(branch_peak)s' re 0 dc 0 gr gr 'GridPoint Table' PDIN 0 0 '' pdin CLTT 'Location' '1/R' cltt CLID '' '' clid grid" % self.idpool)
            branch_ext.addRow(row=[0, 0, "", "%(extern_mean)s" % self.idpool, '%(branch_peak)s' % self.idpool, self.extern[0], self.extern[1], "", "", ""])
            branch_ext.addRow(row=[10, 0, "%(branch_peak)s" % self.idpool, "%(extern)s" % self.idpool, '', extern_mean[0], extern_mean[1], "", "", ""])
            self.pool['network.gr'].append(branch_ext)

            branch_ext = sobek.Object("GRID id '%(branch_mean)s' ci '%(branch_mean)s' re 0 dc 0 gr gr 'GridPoint Table' PDIN 0 0 '' pdin CLTT 'Location' '1/R' cltt CLID '' '' clid grid" % self.idpool)
            branch_ext.addRow(row=[0, 0, "", "%(extern_mean)s" % self.idpool, '%(branch_mean)s' % self.idpool, self.extern[0], self.extern[1], "", "", ""])
            branch_ext.addRow(row=[10, 0, "%(branch_mean)s" % self.idpool, "%(extern)s" % self.idpool, '', extern_mean[0], extern_mean[1], "", "", ""])
            self.pool['network.gr'].append(branch_ext)

            # nodes.dat
            node_dat = sobek.Object("NODE id '%(extern)s' ty 1 ws 0 ss 0 wl 0 ml 999999 node" % self.idpool)
            node_dat['ws'] = self.extwaters_area*0.33*10000
            node_dat['wl'] = self.max_water_level - 10
            self.pool['nodes.dat'].append(node_dat)

            node_dat = sobek.Object("NODE id '%(extern_mean)s' ty 1 ws 0 ss 0 wl 0 ml 999999 node" % self.idpool)
            node_dat['ws'] = self.extwaters_area*0.67*10000
            node_dat['wl'] = level_mean - 10
            self.pool['nodes.dat'].append(node_dat)

            # initial.dat
            initial_dat = sobek.Object("FLIN nm 'initial' ss 0 id '%(branch_peak)s' ci '%(branch_peak)s' lc 9.9999e+009 q_ lq 0  0 ty 0 lv ll 0 10 9.9999e+009 flin" % self.idpool)
            self.pool['initial.dat'].append(initial_dat)

            initial_dat = sobek.Object("FLIN nm 'initial' ss 0 id '%(branch_mean)s' ci '%(branch_mean)s' lc 9.9999e+009 q_ lq 0  0 ty 0 lv ll 0 10 9.9999e+009 flin" % self.idpool)
            self.pool['initial.dat'].append(initial_dat)


            # network.cp
            brch = sobek.Object("BRCH id '%(branch_peak)s' cp 1 ct bc\nTBLE\n 5 360 <\ntble brch" % self.idpool)
            self.pool['network.cp'].append(brch)

            brch = sobek.Object("BRCH id '%(branch_mean)s' cp 1 ct bc\nTBLE\n 5 360 <\ntble brch" % self.idpool)
            self.pool['network.cp'].append(brch)

            # network.cr
            profile = sobek.Object("CRSN id '%(prof_high_peak)s' nm '' ci '%(branch_peak)s' lc 9 crsn" % self.idpool)
            self.pool['network.cr'].append(profile)

            profile = sobek.Object("CRSN id '%(prof_high_mean)s' nm '' ci '%(branch_mean)s' lc 9 crsn" % self.idpool)
            self.pool['network.cr'].append(profile)

            profile = sobek.Object("CRSN id '%(prof_low_peak)s' nm '' ci '%(branch_peak)s' lc 1 crsn" % self.idpool)
            self.pool['network.cr'].append(profile)

            profile = sobek.Object("CRSN id '%(prof_low_mean)s' nm '' ci '%(branch_mean)s' lc 1 crsn" % self.idpool)
            self.pool['network.cr'].append(profile)

            storage = sobek.Object("STON id '%(extern)s' ci '%(branch_peak)s' lc 10 st 'Normal' ston" % self.idpool)
            self.pool['network.cr'].append(storage)                                   

            storage = sobek.Object("STON id '%(extern_mean)s' ci '%(branch_peak)s' lc 0 st 'Normal' ston" % self.idpool)
            self.pool['network.cr'].append(storage)

            # profile.dat
            profile = sobek.Object("CRSN id '%(prof_high_peak)s' di '%(lake_prof)s' rl 0 rs 2 crsn" % self.idpool)
            profile['rl'] = self.max_water_level - 10
            self.pool['profile.dat'].append(profile)

            profile = sobek.Object("CRSN id '%(prof_high_mean)s' di '%(lake_prof)s' rl 0 rs 2 crsn" % self.idpool)
            profile['rl'] = self.max_water_level - 10
            self.pool['profile.dat'].append(profile)

            profile = sobek.Object("CRSN id '%(prof_low_peak)s' di '%(lake_prof)s' rl 0 rs 2 crsn" % self.idpool)
            profile['rl'] = level_mean - 10
            self.pool['profile.dat'].append(profile)

            profile = sobek.Object("CRSN id '%(prof_low_mean)s' di '%(lake_prof)s' rl 0 rs 2 crsn" % self.idpool)
            profile['rl'] = level_mean - 10
            self.pool['profile.dat'].append(profile)


            # profile.def
            profile = sobek.Object("CRDS id '%(lake_prof)s' nm 'Lizard lake_prof' ty 0 wm 100 w1 0 w2 0 sw 0 gl 0 gu 0 lt lw\nTBLE\n0  100  100 <\n0.0001  101  101 <\ntble crds" % self.idpool)
            self.pool['profile.def'].append(profile)


            # network.st
            stru = sobek.Object("STRU id '%(branch_peak)s' nm '' ci '%(branch_peak)s' lc 5 stru" % self.idpool)
            self.pool['network.st'].append(stru)

            stru = sobek.Object("STRU id '%(branch_mean)s' nm '' ci '%(branch_mean)s' lc 5 stru" % self.idpool)
            self.pool['network.st'].append(stru)                                   

            # struct.dat
            stru = sobek.Object("STRU id '%(branch_peak)s' nm '' ca 1 dd '%(branch_peak)s' cj '%(branch_peak)s' stru" % self.idpool)
            self.pool['struct.dat'].append(stru)

            stru = sobek.Object("STRU id '%(branch_mean)s' nm '' ca 0 dd '%(branch_mean)s' cj '' stru" % self.idpool)
            self.pool['struct.dat'].append(stru)

            # struct.def
            stru = sobek.Object("STDS id '%(branch_peak)s' nm '' ty 6 cl -5 cw 100 ce 1 sc 1 rt 0 stds" % self.idpool)                                  
            stru['cl'] = self.max_water_level - 9
            stru['cw'] = self.extwaters_area*100
            self.pool['struct.def'].append(stru)

            stru = sobek.Object("STDS id '%(branch_mean)s' nm '' ty 6 cl -5 cw 100 ce 1 sc 1 rt 1 stds" % self.idpool)                                  
            stru['cl'] = self.max_water_level - 9
            stru['cw'] = self.extwaters_area*100
            self.pool['struct.def'].append(stru)

            #control.def    
            cntl_def = sobek.Object(tag="CNTL", id = self.idpool['branch_peak'])
            cntl_def['nm'] = 'Time' 
            cntl_def['ct'] = 0 
            cntl_def['ac'] = 1 
            cntl_def['ca'] = 0 
            cntl_def['cf'] = 1 
            cntl_def['mc'] = 0 
            cntl_def['bl'] = 1 
            cntl_def['ti'] = []
            cntl_def['tv'] = []

            log.info("in the control definition, add a new table")

            for i in self.breachlinkproperty.waterlevelset.waterlevel_set.all().order_by('time'):
                value = i.value
                if (abs(value - self.min_water_level) < 0.1 ):
                    value = value - 1
                cntl_def.addRow( [datetime.datetime(2000,1,1) + datetime.timedelta(i.time,0), value] )


            self.pool['control.def'].addObject(cntl_def)


         ##################################################################       

        else:
            log.error("unrecognized external water")



         ##################################################################
        if self.scenario.cutofflocations.all():
            log.info("alter the model for cutoff locations")

        node_id = None
        for loc_cutoff in self.scenario.scenariocutofflocation_set.all():

            delay_of_cutoff = datetime.timedelta(loc_cutoff.tclose)
            action_of_cutoff = loc_cutoff.action
            crest_level = loc_cutoff.cutofflocation.bottomlevel
            width = loc_cutoff.cutofflocation.width
            # validate that the location cutoff is a calculation point
            # select the pool[]['GRID'] if obj[TBLE][0][_, 3] ==
            # location_cutoff_id (it is unique)

            
            if loc_cutoff.cutofflocation.externalwater_set.count() > 0:
                log.debug('external cuttofflocation')
                pool_ref = pool2
                node_id = loc_cutoff.cutofflocation.cutofflocationsobekmodelsetting_set.get(sobekmodel=self.breachlinkproperty.sobekmodel_externalwater_id).sobekid
            else:
                log.debug('internal cuttofflocation')
                pool_ref = self.pool
                node_id = loc_cutoff.cutofflocation.cutofflocationsobekmodelsetting_set.get(sobekmodel=self.scenario.sobekmodel_inundation).sobekid


            found = False
            for candidate_grid in pool_ref['network.gr']['GRID']:
                table = candidate_grid['TBLE'][0]
                for row_no in range(table.rows()):
                    if (table[row_no, 2] == node_id or table[row_no, 4] == node_id):
                        log.debug("branch "+node_id + " gevonden")
                        branch_id = candidate_grid['ci'][0]
                        if table[row_no, 2] == node_id:
                            prev_c = table[row_no-1, 0]
                            here_c = (table[row_no-1, 0]+table[row_no, 0])/2
                            next_c = table[row_no, 0]
                        else:
                            prev_c = table[row_no, 0]
                            here_c = (table[row_no, 0]+table[row_no+1, 0])/2
                            next_c = table[row_no+1, 0]
                        found = True
                        break
                if found: 
                    break
            if not found:
                for candidate_grid in pool_ref['network.gr']['GRID']:
                    table = candidate_grid['TBLE'][0]
                    for row_no in range(table.rows()):
                        if (table[row_no, 3] == node_id):
                            log.debug("node "+node_id + " gevonden")
                            branch_id = candidate_grid['ci'][0]
                            prev_c = table[row_no-1, 0]
                            here_c = table[row_no, 0]
                            next_c = table[row_no+1, 0]
                            found = True
                            break
                    if found:
                        break
                if found:
                    log.warning('cuttofflocation is on a node instead of a branch!')


            if not found:
                log.error("did not find the location cutoff ID in network.gr['GRID']. Id node: "+ node_id)
            else:
                # note the distance from the origin of the cutoff point,
                # compared with the preceding and the following points on the
                # branch.  this is the first column in the table.

                st = pool_ref["network.st"]
                # select here all structures on the same branch falling
                # between previous and next node (close to location cutoff).
                usable_structs = [(abs(here_c - obj['lc'][0]), obj) 
                                  for obj in pool_ref['network.st']['STRU'] 
                                  if prev_c < obj['lc'][0] < next_c and obj['ci'][0] == branch_id]

                idnext=self.nextid()

                if usable_structs != []:
                    stru_st = min(usable_structs)[1]
                    stru_dat = pool_ref['struct.dat']['STRU', stru_st.id]

                    stru_dat['dd'] = idnext
                    stru_dat['ca'] = 1
                    stru_dat['cj'] = idnext
                    del stru_dat['cj']
                    stru_dat['cj'] = idnext

                    del pool_ref['struct.dat']['STRU', stru_st.id]
                    pool_ref['struct.dat'].addObject(stru_dat)
                else:

                    log.debug("create a new weir close to the cutoff location")

                    # have a look at case '12' in lizardkb.lit...  that is the
                    # joined models plus breach plus the added new weir close
                    # to the cutoff location.  compare it to case '10' to have
                    # the description of what to do here.

                    stru_st = sobek.Object(tag="STRU", id=idnext)
                    # some c for the new weir... ... take 33% of the distance
                    # towards the furthest adjacent point
                    c = max([(next_c - here_c, (here_c*2 + next_c)/3), 
                             (here_c - prev_c, (here_c*2 + prev_c)/3)]
                            )[1]
                    stru_st['lc'] = c
                    stru_st['ci'] = branch_id
                    pool_ref['network.st'].addObject(stru_st)

                    stru_dat = sobek.Object(tag="STRU", id=idnext)
                    stru_dat['cj'] = idnext
                    stru_dat['dd'] = idnext
                    stru_dat['ca'] = 1
                    stru_dat['nm'] = ''
                    pool_ref['struct.dat'].addObject(stru_dat)

                # stru_st is in the the network.st file...

                stru_def = sobek.Object(tag="STDS", id=idnext)
                stru_def['ty'] = 6
                stru_def['cw'] = 11
                stru_def['ce'] = 1
                stru_def['sc'] = 1
                stru_def['rt'] = 0
                stru_def['cl'] = crest_level
                pool_ref['struct.def'].addObject(stru_def)

                log.debug("network.st: %s" % self.pool['network.st'].content)
                log.debug("struct.dat: %s" % self.pool['struct.dat'].content)
                log.debug("struct.def: %s" % self.pool['struct.def'].content)
                log.debug("control.def: %s" % self.pool['control.def'].content)

                stru_dat = pool_ref['struct.dat']['STRU', stru_st.id]
                stru_def = pool_ref['struct.def']['STDS', stru_dat['dd'][0]]

                # do not alter the crest_level if it is already specified
                # in the struct, otherwise get loc_cutoff['crest_level']
                if 'cl' not in stru_def:
                    stru_def['cl'] = crest_level

                cntl_def = sobek.Object(tag="CNTL", id = stru_dat['cj'][0])
                cntl_def['nm'] = 'Time' 
                cntl_def['ct'] = 0 
                cntl_def['ac'] = 1 
                cntl_def['ca'] = 0 
                cntl_def['cf'] = 1 
                cntl_def['mc'] = 0 
                cntl_def['bl'] = 1 
                cntl_def['ti'] = []
                cntl_def['tv'] = []
                pool_ref['control.def'].addObject(cntl_def)

                log.debug("in the control definition, add a new table")
                
                if action_of_cutoff == 2:
                    cntl_def.addRow([datetime.datetime(2000, 1, 1) + delay_of_cutoff - datetime.timedelta(0, 60), 1000])
                    cntl_def.addRow([datetime.datetime(2000, 1, 1) + delay_of_cutoff, stru_def['cl'][0]])                    
                else:
                    cntl_def.addRow([datetime.datetime(2000, 1, 1) + delay_of_cutoff - datetime.timedelta(0, 60), stru_def['cl'][0]])
                    cntl_def.addRow([datetime.datetime(2000, 1, 1) + delay_of_cutoff, 1000])

        ##################################################################
        log.info("alter the elevation grid / copy the friction grid")

        log.debug("get the grid location out of the polder")

        domain_id = self.pool['network.d12']['DOMN'][0].id
        # network location of model
        lead_str = (self.base + self.scenario.sobekmodel_inundation.project_fileloc)
        self.frict_grid = None
        
        if int(self.pool['friction.dat']['D2FR', domain_id]['mt cp'][0]) in [1,2]:
            frict_grid_name = self.pool['friction.dat']['D2FR', domain_id]['mt cp'][1]
            log.info("%s" % str(self.pool['friction.dat']['D2FR'][0]['mt cp']))
            log.info("in source model, the friction grid is stored as %s" % repr(frict_grid_name))
            # from this path, replace all what comes before 'FIXED' with
            trail_pos = frict_grid_name.lower().find('\\fixed\\')
            if trail_pos == -1:
                log.error("could not locate '\\fixed\\' in reference friction grid name")
                raise RuntimeError("could not locate '\\fixed\\' in reference friction grid name")
            frict_grid_name = lead_str + frict_grid_name[trail_pos:]
            log.info("in model to be used, the friction grid is stored as '%s'" % frict_grid_name)

            try:
                frict_grid = self.frict_grid = asc.AscGrid(frict_grid_name)
            except:
                frict_grid = self.frict_grid = None
                log.info("in model to be used, there is no friction grid " )
                pass

            if frict_grid:
                print frict_grid_name
                
                self.new_frict_name = new_frict_name = '../WORK/grid/' + frict_grid.srcname
                print new_frict_name
                self.pool['friction.dat']['D2FR', domain_id]['mt cp'][1] = new_frict_name
                self.pool['network.ntw'].replace(frict_grid_name, new_frict_name)

        elev_grid_name = self.pool['network.d12']['DOMN'][0]['GFLS'][0]['fnm'][0]
        log.debug("in source model, the elevation grid is stored as '%s'" % elev_grid_name)
        trail_pos = elev_grid_name.lower().find('\\fixed\\')
        elev_grid_name = lead_str + elev_grid_name[trail_pos:]
        log.debug("in model to be used, the elevation grid is stored as '%s'" % elev_grid_name)
        elev_grid = self.elev_grid = asc.AscGrid(elev_grid_name)
        self.new_elev_name = new_elev_name = '../WORK/grid/' + elev_grid.srcname
        self.pool['network.d12']['DOMN'][0]['GFLS'][0]['fnm'][0] = new_elev_name
        self.pool['network.ntw'].replace(elev_grid_name, new_elev_name)

        log.debug("now we have the grid")

        if elev_grid[self.breach.internalnode.coords] is False:
            raise ValueError("the 'intern' point is really outside of the grid")
        
        if elev_grid[self.breach.internalnode.coords] is None:
            print 'ooo'
            #raise ValueError("the 'intern' point is on an invalid pixel of the grid")

        log.info(str(elev_grid[self.breach.externalnode.coords]))
        print type(str(elev_grid[self.breach.externalnode.coords]))

        if elev_grid[self.breach.externalnode.coords] not in (False, None):

            if self.breach.externalwater.type == DB_CANAL or self.breach.externalwater.type == DB_INNER_CANAL:
                log.debug("external point at valid grid pixel.  this is acceptable for DB_CANAL and DB_INNER_CANAL")
            else:
                raise ValueError("the 'extern' point is inside of the grid")

        log.debug("now we know that intern is intern and extern is extern.")

        # what is the direction of the breach: W-E or S-N?

        # vector computation is not available in django.contrib.gis.geos.geometries
        c_breach = [self.breach.internalnode.x - self.breach.externalnode.x,
                    self.breach.internalnode.y - self.breach.externalnode.y]

        mid_col, mid_row = mid_pixel = elev_grid.get_col_row(self.breach.internalnode)
        target = [mid_pixel]
        log.debug("elevation of mid pixel: %s" % elev_grid[mid_pixel])

        if abs(c_breach[1]) < abs(c_breach[0]):
            log.debug("breach is W-E so we examine three pixels 'vertically'")

            left_pixel = (mid_col, mid_row + 1)
            log.debug("elevation of left pixel %s: %s" % (left_pixel, elev_grid[left_pixel]))
            #if isinstance(elev_grid[left_pixel], float):
            left_point = elev_grid.point(left_pixel, (0.5, 0.5))
            target.append(left_pixel)
            #else:
            #    log.debug("left pixel %s is not a valid grid pixel" % (left_pixel,))
            #    left_pixel = mid_pixel
            #    left_point = elev_grid.point(mid_pixel, (0.5, 0.90))

            right_pixel = (mid_col, mid_row - 1)
            log.debug("elevation of right pixel %s: %s" % (right_pixel, elev_grid[right_pixel]))
            #if isinstance(elev_grid[right_pixel], float):
            right_point = elev_grid.point(right_pixel, (0.5, 0.5))
            target.append(right_pixel)
            #else:
            #    log.debug("right pixel %s is not a valid grid pixel" % (right_pixel,))
            #    right_pixel = mid_pixel
            #    right_point = elev_grid.point(mid_pixel, (0.5, 0.10))

        else:
            log.debug("breach is N-S so we examine three pixels 'horizontally'")

            left_pixel = (mid_col - 1, mid_row)
            log.debug("elevation of left pixel %s: %s" % (left_pixel, elev_grid[left_pixel]))
            #if isinstance(elev_grid[left_pixel], float):
            left_point = elev_grid.point(left_pixel, (0.5, 0.5))
            target.append(left_pixel)
            #else:
            #    log.debug("left pixel %s is not a valid grid pixel" % (left_pixel,))
            #    left_pixel = mid_pixel
            #    left_point = elev_grid.point(mid_pixel, (0.1, 0.50))

            right_pixel = (mid_col + 1, mid_row)
            log.debug("elevation of right pixel %s: %s" % (right_pixel, elev_grid[right_pixel]))
            #if isinstance(elev_grid[right_pixel], float):
            right_point = elev_grid.point(right_pixel, (0.5, 0.5))
            target.append(right_pixel)
            #else:
            #    log.debug("right pixel %s is not a valid grid pixel" % (right_pixel,))
            #    right_pixel = mid_pixel
            #    right_point = elev_grid.point(mid_pixel, (0.9, 0.50))

        #########################################################################

        def empty_grid(elevation_grid):
            result = elevation_grid.copy()
            for col in range(len(elevation_grid)):
                for row in range(len(elevation_grid[0])):
                    result[col][row] = 0
            return result        

        def add_adjusted_embankments(elevation_grid, adjustment_grid):
            
            result = elevation_grid.copy()
        
            for col in range(len(elevation_grid)):
                for row in range(len(elevation_grid[0])):
                    result[col][row] = elevation_grid[col][row] + adjustment_grid[col][row]

            return result


        try:
            for reference in [flooding.models.Measure.TYPE_SEA_LEVEL, flooding.models.Measure.TYPE_EXISTING_LEVEL]:
                #first sea level
                if self.scenario.strategy and self.scenario.strategy.measure_set.filter(reference_adjustment = reference).count() > 0:
                    try:
                        conn = osgeo.ogr.Open("PG: host='nens-webontw-01' dbname='flooding_20110128_test' user='postgres' password='postgres' port=5432")

                        sql = "SELECT AsBinary(TRANSFORM(eu.geometry, 28992)) as wkb_geometry, m.adjustment as adjustment \
                                        FROM flooding_strategy s, flooding_measure m, flooding_embankment_unit eu, flooding_measure_strategy ms, flooding_embankment_unit_measure eum \
                                        WHERE s.id = %(strategy_id)i and s.id = ms.strategy_id and ms.measure_id = m.id and m.id = eum.measure_id and eum.embankmentunit_id = eu.id \
                                        and m.reference_adjustment = %(reference)i"% {'strategy_id':self.scenario.strategy.id, 'reference':reference}

                        layer = conn.ExecuteSQL(sql)
                    except:
                        log.warning('use alternative way to get layer of adjusted embankments')

                        log.info('generate shapefile for adjustment embankments')
                        t_srs = osr.SpatialReference()
                        t_srs.ImportFromProj4("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs" )
                        drv = ogr.GetDriverByName('ESRI Shapefile')
                        tmp_shp_filename = os.path.join(self.tmp_dir, 'tmp_asc%i.shp'%reference)
                        ds = drv.CreateDataSource( str(tmp_shp_filename))
                        layer = ds.CreateLayer(ds.GetName(), geom_type = ogr.wkbLineString, srs = t_srs)
                        layer.CreateField(ogr.FieldDefn('adjustment', ogr.OFTReal))

                        fid = 0                 
                        
                        for measure in self.scenario.strategy.measure_set.filter(reference_adjustment = reference):
                            for embankement_unit in measure.embankmentunit_set.all():
                                feat = ogr.Feature(feature_def=layer.GetLayerDefn())
                                geom_trans = embankement_unit.geometry.transform(28992, True)
                                geom = ogr.CreateGeometryFromWkt(geom_trans.ewkt.split(';')[1])
                                feat.SetGeometry(geom)
                                
                                feat.SetFID(fid)
                                feat.SetField('adjustment', measure.adjustment)
                                layer.CreateFeature(feat)
                                fid = fid + 1            

                        log.info('nr of nodes '+ str(fid))
                        layer.SyncToDisk()

                    if reference == flooding.models.Measure.TYPE_EXISTING_LEVEL:
                        #leeg grid
                        empty_grid_name = os.path.join(self.tmp_dir, 'empty_asc%i.asc'%reference)
                        empty_grid = self.elev_grid.copy()
                        #asc.AscGrid.apply(lambda x: 0, self.elev_grid)
                        for col in range(1, empty_grid.ncols+1):
                            for row in range(1, empty_grid.nrows+1):
                            
                                empty_grid[col,row] = 0
 

                        empty_file = file(empty_grid_name,'w')
                        empty_grid.writeToStream(empty_file, empty_grid)
                        empty_file.close()
                        target_ds = gdal.Open(str(empty_grid_name))
                        err = gdal.RasterizeLayer(target_ds, [1], layer, options=["ATTRIBUTE=adjustment"])
                        tmp_asc_filename = os.path.join(self.tmp_dir, 'tmp_asc%i.asc'%reference)
                        dst_ds = gdal.GetDriverByName('AAIGrid').CreateCopy(str(tmp_asc_filename), target_ds,0)
                        dst_ds = None

                        adjustment_grid = asc.AscGrid(tmp_asc_filename)
                        self.elev_grid = elev_grid = asc.AscGrid.apply(lambda x,y: x+y, self.elev_grid, adjustment_grid)
                        adjustment_grid = None

                         
                    else:
                        target_ds = gdal.Open(str(elev_grid_name))
                        err = gdal.RasterizeLayer(target_ds, [1], layer, options=["ATTRIBUTE=adjustment"])
                        tmp_asc_filename = os.path.join(self.tmp_dir, 'tmp_asc%i.asc'%reference)
                        dst_ds = gdal.GetDriverByName('AAIGrid').CreateCopy(str(tmp_asc_filename), target_ds,0)
                        dst_ds = None

                        self.elev_grid = elev_grid = asc.AscGrid(tmp_asc_filename)
  
                    ds.Destroy()
                    ds = None

        finally:
            #print "Unexpected error:", sys.exc_info()[0]
            ds = None
            dst_ds = None
            adjustment_grid = None
            empty_file = None
            target_ds = None

        log.debug("right_pixel: %s, right_point: %s" % (right_pixel, right_point))
        log.debug("left_pixel: %s, left_point: %s" % (left_pixel, left_point))

        # does any of the target pixels contain anything like a connection
        # node or a calculation point?
        log.debug("breach target: %s" % target)

        # select all points that fall in target pixels
        hit_points = [p for p in self.pool['network.d12']['DOMN'][0]['PT12'] if (p['mc'][0], p['mr'][0]) in target]
        log.debug("sobek PT12 objects in the target pixels" % hit_points)

        if hit_points:
            # which of the node/points is closer to the breach external end?
            log.debug("just choose one")
            intern_sobek = hit_points[0]
            intern = intern_sobek['px'][0], intern_sobek['py'][0]
            self.idpool['intern'] = intern_sobek.id

            log.debug("chose this one: %s" % intern_sobek)

            target = []

        else:
            intern_sobek = None
            log.debug("lowering level of pixels containing new boundary line")
            for pix in target:
                elev_grid[pix] = self.breachlinkproperty.pitdepth

        # the answers to the preceding questions are:
        # hit_points
        # target


        ##################################################################
        log.info("add objects modeling the breach itself...")

        # control.def
        cntl = sobek.Object("CNTL id '%(breach)s' nm 'breach' ct 0 ac 1 ca 4 cf 1 mc 0 bl 1 ti tv cntl" % self.idpool)
        cntl.addRow([self.start_of_simulation + self.time_of_breach_start, 0])
        cntl.addRow([self.start_of_simulation + self.time_of_breach_max_depth, ((self.max_water_level -   self.lowest_crest_level) *  self.initial_breach_width)])
        self.pool['control.def'].append(cntl)

        # network.cp
        brch = sobek.Object("BRCH id '%(breach)s' cp 1 ct bc brch" % self.idpool)
        breach_orientation = 90 - math.atan2(c_breach[1], c_breach[0]) * 180 / math.pi
        breach_length = self.breach_length
        if breach_length > 200:
            log.info("breach_length = %.f . set to 200"%breach_length)
            breach_length = 200

        brch.addRow([breach_length / 2, breach_orientation])
        self.pool['network.cp'].append(brch)

        # network.cr
        crsn = sobek.Object("CRSN id '%(breach)s' nm 'the breach' ci '%(breach)s' crsn" % self.idpool)
        crsn['lc'] = breach_length / 2
        self.pool['network.cr'].append(crsn)

        crsn = sobek.Object("CRSN id '%(breach)s_2' nm 'the breach' ci '%(breach)s' crsn" % self.idpool)
        crsn['lc'] = breach_length / 100
        self.pool['network.cr'].append(crsn)

        # initial.dat
        initial_dat = sobek.Object("FLIN nm 'initial' ss 0 id '%(breach)s' ci '%(breach)s' lc 9.9999e+009 q_ lq 0 0 ty 0 lv ll 0 0.02 9.9999e+009 flin" % self.idpool)
        self.pool['initial.dat'].append(initial_dat)

        # network.gr
        ngrid = sobek.Object("GRID id '%(grid)s' ci '%(breach)s' re 0 dc 0 gr gr 'GridPoint Table' PDIN 0 0 '' pdin CLTT 'Location' '1/R' cltt CLID '' '' clid grid" % self.idpool)
        ngrid.addRow(row=[0, 0, "", "%(extern)s" % self.idpool, '%(breach)s' % self.idpool, self.extern[0], self.extern[1], "", "", ""])
        ngrid.addRow(row=[breach_length, 0, "%(breach)s" % self.idpool, "%(intern)s" % self.idpool, '', self.breach.internalnode.x, self.breach.internalnode.y, "", "", ""])
        self.pool['network.gr'].append(ngrid)

        # network.st
        stru = sobek.Object("STRU id '%(breach)s' nm 'the breach' ci '%(breach)s' stru" % self.idpool)
        stru['lc'] =  breach_length / 2
        self.pool['network.st'].append(stru)

        # network.tp
        brch = sobek.Object("BRCH id '%(breach)s' nm 'the breach' bn '%(extern)s' en '%(intern)s' brch" % self.idpool)
        brch['al'] = breach_length
        self.pool['network.tp'].append(brch)

        # nodes.dat
        node = sobek.Object("NODE id '%(intern)s' ty 1 ws 20000 ss 0 wl 0 ml 0 node" % self.idpool)
        node['wl'] = self.breachlinkproperty.pitdepth
        self.pool['nodes.dat'].append(node)

        # network.cr
        storage = sobek.Object("STON id '%(intern)s' ci '%(breach)s' lc 0 st 'Normal' ston" % self.idpool)
        storage['lc'] = breach_length
        self.pool['network.cr'].append(storage)



        # profile.dat
        crsn = sobek.Object("CRSN id '%(breach)s' di '%(breach)s' crsn" % self.idpool)
        crsn['rl'] = self.profile_depth
        self.pool['profile.dat'].append(crsn)

        crsn = sobek.Object("CRSN id '%(breach)s_2' di '%(breach)s' crsn" % self.idpool)
        if self.breach.externalwater.type == DB_LAKE:
            crsn['rl'] = self.max_water_level - 0.02
        else:
            crsn['rl'] = self.profile_depth    


        self.pool['profile.dat'].append(crsn)

        # profile.def
        crds = sobek.Object("CRDS id '%(breach)s' nm 'dambreak' ty 0 wm 200 w1 0 w2 0 sw 0 gl 0 gu 0 lt lw crds" % self.idpool)
        crds.addRow([0, 200, 200])
        crds.addRow([0.0001, 200, 200])
        self.pool['profile.def'].append(crds)

        # struct.dat
        stru = sobek.Object("STRU id '%(breach)s' nm 'the breach' dd '%(breach)s' ca 1 cj '%(breach)s' stru" % self.idpool)
        self.pool['struct.dat'].append(stru)

        # struct.def
        stds = sobek.Object("STDS id '%(breach)s' nm 'the breach' ty 13 td 2 cl 1.9 cw 10.0 ml 0.45 f1 1.3 f2 0.04 uc 0.2 ce 1 rt 0 eq -1 ts '2000/01/01;00:30:00' dt '0:01:00:00' stds" % self.idpool)
        stds['cl'] = self.max_water_level
        stds['cw'] = self.breachlinkproperty.widthbrinit
        stds['ml'] = self.breachlinkproperty.bottomlevelbreach
        stds['f1'] = self.breachlinkproperty.brf1
        stds['f2'] = self.breachlinkproperty.brf2
        stds['uc'] = self.breachlinkproperty.ucritical
        stds['ce'] = self.breachlinkproperty.brdischcoef
        stds['ts'] = self.start_of_simulation + self.time_of_breach_start
        stds['dt'] = self.time_of_breach_max_depth
        self.pool['struct.def'].append(stds)

        ##################################################################
        log.info("add objects modeling the internal side of the breach...")

        ##################################################################
        log.debug("did we hit anything and what was it?")
        if hit_points:
            if intern_sobek['lc'][0] == 0: 
                log.debug("we hit a connection node, intern we are already done")
            else:
                log.debug("we hit a calculation point - marking it as linkage node")
                ndlk = sobek.Object(tag="NDLK", id=self.idpool['intern'])
                ndlk['nm'] = 'promoted internal point'
                ndlk['px'], ndlk['py'] = intern
                ndlk['ci'] = intern_sobek['ci'][0]
                ndlk['lc'] = intern_sobek['lc'][0]
                self.pool['network.tp'].append(ndlk)

        else:
            log.debug("we did not hit anything so we add the internal boundary")

            node_int = sobek.Object("NODE id '%(intern)s' nm 'internal end of breach' node" % self.idpool)
            node_int['px'], node_int['py'] = self.breach.internalnode.x, self.breach.internalnode.y
            self.pool['network.tp'].append(node_int)

            # boundary.dat
            d2li = sobek.Object("D2LI id '%(boundary)s' ty 4 cp '%(intern)s' d2li" % self.idpool)
            self.pool['boundary.dat'].append(d2li)

            # network.cn
            d2li = sobek.Object("D2LI id '%(boundary)s' nm 'internal line boundary' ci '%(boundary)s' d2li" % self.idpool)
            d2li['bx'], d2li['by'] = left_point
            d2li['ex'], d2li['ey'] = right_point
            self.pool['network.cn'].append(d2li)

            fl2b = sobek.Object("FL2B id '%(intern)s' nm 'internal end of breach' ci '%(breach)s' fl2b" % self.idpool)
            fl2b['px'], fl2b['py'] = self.breach.internalnode.x, self.breach.internalnode.y
            self.pool['network.cn'].append(fl2b)

            # network.d12
            domn = self.pool['network.d12']['DOMN'][0]
            li12 = domn.addObject(sobek.Object("LI12 id '%(boundary)s' nm 'internal line boundary' ci '' lc 0 li12" % self.idpool))
            li12['bx'], li12['by'] = left_point
            li12['ex'], li12['ey'] = right_point
            li12['bc'], li12['br'] = elev_grid.get_col_row(left_point)
            li12['ec'], li12['er'] = elev_grid.get_col_row(right_point)
            li12.addRow(row=[1, '1D2D Boundary Flow'], to_table='boundaries')
            for col, row in target:
                li12.addRow(row=[str(col), str(row)], to_table='cells')

        ########################################################################
        # in case of an canal or internal canal, there are no extra
        # connections between canal and inundationmodel except the
        # breach remove other potential linkages by removing the grids
        # where both crosses

        # get alle x and y nodes from the bosommodel calculation and
        # connectionnodes

        if self.breach.externalwater.type == DB_CANAL or self.breach.externalwater.type == DB_INNER_CANAL:
            objects = pool2['network.gr']['GRID']
            for obj in objects:
                #log.info(obj)
                table = obj['TBLE'][0]

                for row_no in range(table.rows()):
                    if elev_grid[[table[row_no,5],table[row_no,6]]] not in (False, None):
                        log.info('snijpunt met boezem verwijderd ' )
                        elev_grid[[table[row_no,5],table[row_no,6]]] = None

        log.debug("we are not going to use the second pool any more")
        del pool2

        ########################################################################
        log.debug("update SETTINGS.DAT in the pool")
        from ConfigParser import ConfigParser
        config = ConfigParser()
        log.debug("current settings: %s", str(self.pool['settings.dat'].content))
        self.pool['settings.dat'].reset()
        config.readfp(self.pool['settings.dat'])
        for section, items in {'ResultsBranches':[('Discharge', -1),
                                                 ('Velocity', -1),
                                                 ('SedimentFrijlink', 0),
                                                 ('SedimentVanRijn', 0),
                                                 ('Wind', 0),
                                                 ('WaterLevelSlope', 0),
                                                 ('Chezy', 0),
                                                 ('SubSections', 0),
                                                 ],
                               'ResultsNodes':[('WaterLevel', -1),
                                              ('WaterDepth', -1),
                                              ('WaterOnStreet', 0),
                                              ('TimeWaterOnStreet', 0),
                                              ('LevelFromStreetLevel', 0),
                                              ('RunOff', 0),
                                              ('VolumeOnStreet', 0),
                                              ('NodeVolume', 0), 
                                              ],
                               'ResultsStructures':[('Discharge', -1),
                                                    ('WaterLevel', 0),
                                                    ('CrestlevelOpeningsHeight', -1),
                                                    ('StructHead', 0),
                                                    ('StructVelocity', -1),
                                                    ('OpeningsWidth', -1),
                                                    ('OpeningsArea', 0),
                                                    ('CrestLevel', -1),
                                                    ('GateOpeningsLevel', 0),
                                                    ('PressureDifference', 0),
                                                    ('WaterlevelOnCrest', 0),
                                                    ],
                               'Overland Flow':[('MAPParam H', -1),
                                                ('MAPParam C', -1),
                                                ('MAPParam Z', -1),
                                                ('MAPParam U', 0),
                                                ('MAPParam V', 0),
                                                ('AsciiOutput', -1),
                                                ],
                               'Simulation':[('periodfromevent', 0),
                                                ],
                               }.items():
            for key, value in items:
                config.remove_option(section, key)
                config.set(section, key, str(value))

        for prefix, date in [("begin", self.start_of_simulation), 
                             ("end", self.start_of_simulation + self.duration_of_simulation)]:
            for field in ["year", "month", "day", "hour", "minute", "second", ]:
                config.remove_option('Simulation', prefix + field)
                config.set('Simulation', prefix + field, 
                           str(date.__getattribute__(field)))

        log.debug("updated settings: %s", str(self.pool['settings.dat'].content))

        self.pool['settings.dat'].truncate(0)
        config.write(self.pool['settings.dat'])
        

def compute_sobek_model(scenario, tmp_dir = 'c:/tmp/1/'):
    """task 120: compute_sobek_model

    read the original polder model and add the breach...

    the model is written to a zipfile in the destination directory.
    """


    s = Scenario(scenario, tmp_dir)
    s.collect_initial_data()
    s.compute_sobek_model()
    s.save_sobek_model()
    
    return True



def main(options, args):
    """decode options and arguments into the corresponding variables, then
    call the real main function open_breach.
    """

    [handler.setLevel(options.loglevel) for handler in logging.getLogger().handlers]

    log.debug("options: %s" % options)

    return compute_sobek_model(options.scenario)

if __name__ == '__main__':

   compute_sobek_model(9202)

def select_testcases():
    testcases = {}
    for scenario in flooding.models.Scenario.objects.all():
        s = Scenario(scenario.id)
        testcases.setdefault((s.breach.externalwater.name), scenario.id)
    return testcases


