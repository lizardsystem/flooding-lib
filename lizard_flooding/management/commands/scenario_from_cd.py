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
#* Purpose    : prepare asc files for png generation
#* Function   : main
#* Usage      : ./scenario_from_cd.py --help
#* 
#* Project    : J0005
#* 
#* $Id$
#* 
#* initial programmer :  Mario Frasca
#* initial date       :  20080912
#**********************************************************************

__revision__ = "$Rev$"[6:-2]

"""./scenario_from_cd.py is a tool to open a zipped archive describing
scenarios and store them into the database.

the structure of the zipped archive is very rigid:
there must be an .xls file describing each of the scenarios.
and a separate directory in which the SOBEK data is stored.

it accepts the usual options needed to identify and access the database,
the usual options to determine the logging level,
some custom options to help resume operations.
"""

import logging, math, os, datetime
from nens import sobek, asc
from zipfile import ZipFile, ZIP_DEFLATED

log = logging.getLogger('nens.lizardkadebreuk.scenario_from_cd')

class Task:
    def __init__(self, conn, scenario_id):
        import socket
        log.debug("reserve this task in database.  use user@host as 'taskby'")
        self.conn = conn
        self.task = {}
        self.task['remarks'] = "reserved and locked by scenario_from_cd-" + __revision__
        self.task['type_fk'] = 130
        self.task['scenario_fk'] = scenario_id
        self.task['taskby'] = socket.gethostname().lower()
        self.task['tstart'] = datetime.datetime.now()
        self.task = create_database_object(conn, "tasks", self.task)
    def close(self):
        log.debug("mark task as completed")
        self.task['tfinished'] = datetime.datetime.now()
        self.task['successful'] = True
        self.task['remarks'] = "performed using scenario_from_cd-" + __revision__
        setthing = ", ".join(["%s=%%(%s)s"%(i,i) for i in self.task.keys() if i!= 'id'])
        insq = "UPDATE tasks SET " + setthing + " WHERE id = %(id)s"
        execute(self.conn.cursor(), insq, self.task)
        self.conn.commit()

def get_scenarios_from_sheet(sheet):
    "extract scenarios from DATA sheet as list of dictionaries"

    def integer_or_None(obj, name_list):
        "if obj defines a name in name_list, its value is converted to int or None"
        for key in name_list:
            if obj.get(key):
                obj[key] = int(obj[key])
        return obj

    log.debug("get_scenarios_from_sheet entering")
    base=0
    while not sheet.cell_value(rowx=base,colx=0): 
        log.debug("skipping row %d" % base)
        base+=1

    log.debug("sheet starts with %s information rows, before the header row"
              % base)
 
    ncols = 0
    try:
        while sheet.cell_value(rowx=base, colx=ncols+1): 
            log.debug("there are at least %d columns" % ncols)
            ncols+=1
    except IndexError:
        ncols += 1 # there is some confusion about 1 or 0 based...
        log.debug("hit the right margin of the spreadsheet after column %d" % ncols)
        pass
 
    log.debug("for all we need, there are %s entries in the header"
              % ncols)

    fields = [sheet.cell_value(base, col).lower() for col in range(ncols)]
    result = [integer_or_None(dict(zip(fields, 
                                       [(sheet.cell_value(row, col) or None) for col in range(ncols)])),
                              ['regiongroup_id', 'region_id', 'breach_id', 'project_id', 'scenario_id'])
              for row in range(base+1, sheet.nrows)]
    log.debug("get_scenarios_from_sheet returning")
    return result

def dict_from_cursor(curs, null_fields = None):
    """returns dictionary representing the first record in result set

    if null_fields is given, it is expected to be an empty list and it
    will be extended with the names of the fields that hold NULL
    values.
    """

    fields = [i[0].lower() for i in curs.description]
    from_database = zip(fields, curs.fetchone())

    if null_fields is not None:
        null_fields.extend([key for key, value in from_database if value is None])

    return dict([(key, value) for key, value in from_database if value is not None])

def dictlist_from_cursor(curs):
    """returns the whole result set as list of dictionaries"""

    fields = [i[0].lower() for i in curs.description]
    return [dict(zip(fields, row)) for row in curs.fetchall()]

def get_project_from_sheet(sheet):
    """scan the first rows of sheet in search of project definition

    well, that would be nice but no...  we just assume the project is
    defined in row=1, col=2,3,4
    """

    #fields = [sheet.cell_value(0,col).lower() for col in [2, 3, 4]]
    fields = ['id', 'name', 'comments']
    values = [(sheet.cell_value(1,col) or None) for col in [2, 3, 4]]
    return dict(zip(fields, values))

def execute(curs, query, params=None):
    if params:
        log.debug(query % params)
        curs.execute(query, params)
    else:
        log.debug("%s" % (query))
        curs.execute(query)

def create_database_object(conn, table, obj):
    """create the object in table, fill it with the values in 'obj',
    return the updated 'obj'.
    """

    curs = conn.cursor()
    log.debug("insert a new %s object into database" % table)
    execute(curs, "SELECT NEXTVAL('"+table+"_id_seq') AS id")
    obj.update(dict_from_cursor(curs))
    fields = obj.keys()
    names = ", ".join(fields)
    pynames = ", ".join(["%%(%s)s"%i for i in fields])
    insq = "INSERT INTO "+table+" ("+names+") VALUES ("+pynames+")"
    execute(curs, insq, obj)
    conn.commit()

    return obj

def validate_database_object(conn, table, obj):
    """syncronize obj with database

    fills in the blanks in either obj variable and/or objs
    database table.  

    the object in the database is identified by the 'id' or
    differelty, depending on whether it's a region, a breach or a
    scenario.

    if 'id' is given, the object exists or a ValueError exception is
    raised.

    if 'id' is not given, a corresponding database object might still
    exist and it is looked for differently depending on the table.

    this operation can also fail with a ValueError exception.

    if the object is found, all fields that in the database are not
    NULL are retrieved.  conversely, all fields that in the database
    are NULL are looked for in the given obj and updated in the
    database.

    the function returns the complete current obj record.

    obj is a dictionary, field names match the database.
    conn is the database connection.
    """

    log.debug("validate %s database object %s - entering" % (table, obj))
    null_fields = []
    if obj.get('id') is not None:
        log.debug("get %s object data from database" % table)
        curs = conn.cursor()
        execute(curs, "SELECT * FROM "+table+" WHERE id=%(id)s", obj)
        obj.update(dict_from_cursor(curs, null_fields))
        
    elif table == 'regions':
        raise ValueError(table+" object '%s' does not have an 'id'" % obj)
    elif obj.get('name') is None:
        raise ValueError(table+" object '%s' does not have an 'id' nor a 'name'" % obj)
    else:
        where_clause = 'name=%(name)s'
        where_explain = 'name'
        if table == 'scenarios':
            where_clause += ' AND breach_fk=%(breach_fk)s'
            where_explain += ' and breach_fk'
        elif table == 'breaches':
            where_clause += ' AND region_fk=%(region_fk)s'
            where_explain += ' and region_fk'
        
        log.debug("find %s object by %s in database" % (table, where_explain))
        curs = conn.cursor()
        execute(curs, "SELECT id FROM "+table+" WHERE "+where_clause, obj)

        try:
            obj.update(dict_from_cursor(curs, null_fields))
        except TypeError:
            obj = create_database_object(conn, table, obj)

    # right, now we have the object and we know which fields hold NULL values in the database.
    fields_to_be_defined = [key for key in null_fields if obj.get(key) is not None]
    if fields_to_be_defined:
        set_clauses = " ".join(["SET %s=%%(%s)s" % (key, key) for key in fields_to_be_defined])
        updq = "UPDATE "+table+" "+set_clauses+" WHERE id=%(id)s"
        execute(curs, updq, obj)
    
    log.debug("validate %s database object %s - returning" % (table, obj))
    return obj

def xls_row_decoder(conn, item):
    """decode dictionary item into scenario/breach/region
    """

    log.debug("xls_row_decoder entering")
    log.debug("this is the item: '%s'" % item)

    region = {'regiongroup_fk': item['regiongroup_id'],
              'name': item['dijkring naam'],
              'id': item['region_id'],
              }
    if not region['regiongroup_fk']: del region['regiongroup_fk']

    region.update(dict((k.split('.')[-1], v) for k, v in item.items() if k.startswith('db.regions.')))
    region = validate_database_object(conn, "regions", region)
    item['region_id'] = region['id']

    breach = {'id': item['breach_id'],
              'active': False,
              'name': item['breslocatie'],
              'region_fk': region['id'],
              }

    breach.update(dict((k.split('.')[-1], v) for k, v in item.items() if k.startswith('db.breaches.')))
    breach = validate_database_object(conn, "breaches", breach)
    
    if breach['id'] != item['breach_id']:
        log.debug('validating the breach updated its id: we are dealing with a new breach and we must update its geom')

        item['breach_id'] = breach['id']
        breach['x'] = item['x']
        breach['y'] = item['y']
        curs = conn.cursor()

        execute(curs, """UPDATE breaches 
                     SET geom=Transform(GeomFromEWKT('SRID=28992;POINT(%(x)s %(y)s)'),4326) 
                     WHERE id=%(id)s""",
                breach)

    scenario = {'breach_fk': breach['id'],
                'project_fk': item['project_id'],
                'name': item['scenario'],
                }
    scenario.update(dict((k.split('.')[-1], v) for k, v in item.items() if k.startswith('db.scenarios.')))
    scenario = validate_database_object(conn, "scenarios", scenario)
    item['scenario_id'] = scenario['id']
    pass

def translate_inc_files(conn, item):
    """read the inc file associated to item and store it in a zip file as
    collection of .asc files

    returns the name of the newly created zip file, relative to the
    global destination_dir"""

    curs = conn.cursor()
    execute(curs, "SELECT name, value FROM settings")
    params = dict(curs.fetchall())

    output_dir_base = "%(destination_dir)s\\" % params
    output_dir_rel = "%(region_id)s\\%(breach_id)s\\%(scenario_id)s\\" % item
    output_dir_abs = output_dir_base + output_dir_rel

    item['results'] = []

    for resulttype_id, field_name, output_name in [(1, 'maxh', '/dm1maxd0.asc'),
                                                   (5, 'maxc', '/dm1maxc0.asc'),
                                                   (18, 'filenaam', 'fls_h.inc'),
                                                   ]:
        if not (item[field_name] == '' or  item[field_name] == None):
        
            item['resulttype_id'] = resulttype_id
            log.info("for scenario %(scenario_id)s: doing result of type %(resulttype_id)s" % item)
            curs = conn.cursor()
            execute(curs, "SELECT name FROM resulttypes WHERE id=%s" % resulttype_id)
            (name,) = curs.fetchone()
            pattern = ("%(abs_base)s/data/%(dijkringnr)s/%(breslocatie)s/%(scenario)s/%("+field_name+")s")

            row = {}
            row['resulttype_id'] = resulttype_id
            row['zipfile'] = output_dir_rel + name + '.zip'
            try:
                log.debug("creating directory '%s' to hold results" % (output_dir_base + output_dir_rel))
                os.makedirs(output_dir_base + output_dir_rel)
            except:
                log.debug("already there")

            log.debug("opening destination zip file '%s'" % (output_dir_base + row['zipfile']))
            dest = ZipFile(output_dir_base + row['zipfile'], mode="w", compression=ZIP_DEFLATED) 

            if resulttype_id == 18:
                filename = pattern % item
                log.debug("store inc file '%s'" % filename)

                log.debug("writing item " + output_name + " to zipfile") 
                content = file(filename).read()
                dest.writestr(output_name, content)

                log.debug("count how many grids are defined by this file")
                i = asc.AscGrid.listFromStream(file(filename), oneperhour=True, just_count=True)

                log.debug("decoded to %s files" % i)
                row['file_base'] = 0
                row['file_count'] = i
                row['deltat'] = datetime.timedelta(0, 1*60*60)
            else:
                src = asc.AscGrid(pattern % item)
                src.writeToStream(dest, output_name)
                row['deltat'] = row['file_base'] = row['file_count'] = None
                
            dest.close()
            item['results'].append(row)

    log.debug("after translation of inc files: item=%s" % item)
    return

def scenario_seems_already_there(conn, item):
    "returns number of scenarios for which name matches item['scenario']"

    curs = conn.cursor()
    execute(curs, "SELECT count(*) FROM scenarios WHERE name=%(scenario)s", item)
    (count,) = curs.fetchone()
    return count

def store_results_in_database(conn, item):
    """updates the database, inserting the data describing the results and
    the fact that the results have been computed.
    """

    curs = conn.cursor()
    for row in item['results']:
        qparams = {'resulttype_id': row['resulttype_id'],
                   'scenario_id': item['scenario_id'],
                   'resultloc': row['zipfile'],
                   'min_nr': row['file_base'],
                   'max_nr': row['file_count'],
                   'deltat': row['deltat'],
                   }
        execute(curs, """DELETE from results  
                        WHERE scenario_fk = %(scenario_id)s
                          AND resulttype_fk = %(resulttype_id)s 
                        """, qparams)
        execute(curs, """INSERT INTO results 
                        (scenario_fk, resulttype_fk, resultloc, firstnr, lastnr, deltat) 
                        VALUES 
                        (%(scenario_id)s, %(resulttype_id)s, %(resultloc)s, %(min_nr)s, %(max_nr)s, %(deltat)s) 
                        """, qparams)

    conn.commit()

def main(options, args):
    [handler.setLevel(options.loglevel) for handler in logging.getLogger().handlers]

    log.debug("open database connection")
    import psycopg2
    connect_string='dbname=%(dbname)s user=%(user)s password=%(password)s host=%(host)s port=%(dbport)i' % options.__dict__
    # # useful for testing...
    # connect_string='dbname=lizardkbsp user=lizardkadebreuk password=lizardkadebreuk host=192.168.0.168 port=5432'
    conn = psycopg2.connect(connect_string)
    
    import zipfile
    if options.already_unpacked:
        log.info("assume the zipfile has already been unzipped into directory '%s'" % options.basedir)
    else:
        log.debug("does the input zip file exist... otherwise bail out")
        fh = file(args[0], 'rb')

        try:
            zsrc = zipfile.ZipFile(fh)

            log.info("uncompress zipfile into temporary directory '%s'" % options.basedir)
            for name in zsrc.namelist():
                if name.endswith('/'):
                    log.debug("item '%s' is a directory: making it" % name)
                    try:
                        os.makedirs(options.basedir + name)
                    except OSError:
                        pass
                else:
                    log.debug("item '%s' is a file: unpacking it" % name)
                    outfile = file(options.basedir + name, 'wb')
                    outfile.write(zsrc.read(name))
                    outfile.close()
            fh.close()
        except zipfile.BadZipfile:
            log.error("sorry, can't unzip '%s' myself..." % args[0])
            raise
        except IOError, e:
            log.warning("can't uncompress this.  uncompress manually to '%s' and try again" % options.basedir)
            print e

    if options.unpack_and_stop:
        log.info("finished unpacking and requested not to do more")
        return
    
    log.debug("find the xls workbook in the DATA directory")
    found = None
    for root, _, names in os.walk(options.basedir + "HIS Scenarioviewer/"):
        for name in names:
            if name.endswith('.xls'): 
                found=(root, name)
            if found: break
        if found: break

    filename = os.sep.join(found)
    log.info("read %s into list of dictionaries" % filename)

    log.debug("read workbook and get DATA sheet out of it")
    import xlrd
    wb = xlrd.open_workbook(filename)
    sheet = wb.sheet_by_name('DATA')
    log.debug("found DATA sheet at index %s.  size:(cols:%s, rows:%s)" 
              % (sheet.number, sheet.ncols, sheet.nrows))

    project = get_project_from_sheet(sheet)
    project = validate_database_object(conn, "projects", project)

    table = get_scenarios_from_sheet(sheet)

    log.debug("decode each dictionary into scenario/breach/region")
    for item in table:
        item['project_id'] = project['id']
        item['abs_base'] = options.basedir + 'HIS Scenarioviewer'
        if options.resume and scenario_seems_already_there(conn, item):
            log.debug("skipping scenario %s" % item)
            continue
        if options.resume:
            log.debug("found non matching scenario: stop skipping!")
            options.resume = False
        xls_row_decoder(conn, item)
        task = Task(conn, item['scenario_id'])
        translate_inc_files(conn, item)
        store_results_in_database(conn, item)
        task.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s',) 

    try:
        import psyco
        psyco.full()
        log.debug("psyco-active")
    except ImportError:
        log.debug("failed starting psyco")
        pass

    from optparse import OptionParser

    parser = OptionParser('''\
scenario_from_cd.py [options]

for example:
./scenario_from_cd.py --host 192.168.0.168 --dbname lizardkbsp --user lizardkadebreuk --pass lizardkadebreuk "d:/HIS Scenarioviewer.zip"
''')
    parser.add_option('--info', help='be sanely informative - the default', action='store_const', dest='loglevel', const=logging.INFO, default=logging.INFO)
    parser.add_option('--debug', help='be verbose', action='store_const', dest='loglevel', const=logging.DEBUG)
    parser.add_option('--quiet', help='log warnings and errors', action='store_const', dest='loglevel', const=logging.WARNING)
    parser.add_option('--extreme-debugging', help='be extremely verbose', action='store_const', dest='loglevel', const=0)
    parser.add_option('--silent', help='log only errors', action='store_const', dest='loglevel', const=logging.ERROR)

    parser.add_option('--host', help='the name or ip address of the PostgreSQL server')
    parser.add_option('--dbport', help='the PostgreSQL port', default=5432, type='int')
    parser.add_option('--dbname', help='the name of the database')
    parser.add_option('--user', help='the account to access the database')
    parser.add_option('--password', help='the password for this account')

    parser.add_option('--already-unpacked', action='store_true', default=False, help='zipfile is already unpacked at location')
    parser.add_option('--unpack-and-stop', action='store_true', default=False, help='only unpack the zipfile')
    parser.add_option('--resume', action='store_true', default=False, help='skip the first scenarios while name matches')
    parser.add_option('--basedir', default='m:/j0005/', help='the root directory to which files are extracted and expected')

    (options, args) = parser.parse_args()
    import psycopg2
    try:
        main(options, args)
    except psycopg2.IntegrityError, e:
        log.error("IntegrityError: %s" % e)
        log.info("correct the situation in the database and try again.")
