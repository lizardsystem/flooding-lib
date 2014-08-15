#!/usr/bin/env python
import logging
import xmlrpclib

import iso8601

log = logging.getLogger('nens.eidatabaseconnector')


class EiPingError(Exception):
    """
    - The error that can be thrown if the Ei-server can not be pinged
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ConnectDatabase2EiServer:
    """
    - Is the connection between the EiServer and the database

    - Construct object with 'ConnectDatabase2EiServer(urlEiServer,
      urlJdbcServer)'

    - Use command 'execute' to execute a query.

    - Example

    - connector= 'ConnectDatabase2EiServer(
            'http://192.168.0.23:8090/Jdbc2Ei/test',
            'jdbc:vjdbc:rmi://192.168.0.23:2005/VJdbc, FewsDataStore')
      connector.execute(
         "SELECT TIME, VALUE from TimeSeries WHERE filterId = 'HHNK_METEO' AND
          parameterId = 'P.radar.cal'  AND locationId = 'RG_ALK_55' AND time
          BETWEEN '2009-06-04 13:00:00' AND '2009-06-08 13:00:00'")
    """
    urlEiServer = ''
    urlJdbcServer = ''
    tagname = 'url'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, _urlEiServer, _urlJdbcServer, tagname=None):
        self.urlEiServer = _urlEiServer
        self.urlJdbcServer = _urlJdbcServer
        if tagname != None:
            self.tagname = tagname

    def isAlive(self):
        server = xmlrpclib.Server(self.urlEiServer)
        return server.Ping.isAlive('', '')

    def getUrl(self):
        server = xmlrpclib.Server(self.urlEiServer)
        return server.Config.get('', '', self.tagname)

    def getTagname(self):
        return self.tagname

    #returns a list of dictionaries. keys in the dict are the
    #columnNames, or ['0','1',...]
    #dateColumns: these columns need to be converted to python dates.
    def execute(self, query, column_names=None,
                date_fields=None, binary_fields=None,
                requesttagname=None, debug=False):
        """
        - execute (query, column_names = None, date_fields = None,
                   binary_fields = None,
                   requesttagname = None, debug = False)
        - Executes the query given as input
        - If Debug is True, the query and the column_names are printed
        """
        TRIES = 10
        log.debug('about to execute: %s', query)
        log.debug('column_names: %s', str(column_names))

        server = xmlrpclib.Server(self.urlEiServer)

        counter = 0
        finished = False

        while not finished:
            try:
                if server.Ping.isAlive('', '') > 0:
                    raise EiPingError('Ei server did not Ping.isAlive <= 0')
                finished = True
            except:
                counter += 1
                if counter > TRIES:
                    raise EiPingError('Could not ping to Ei server')
                else:
                    pass

        if not(server.Config.containsKey('', '', self.tagname)):
            server.Config.put('', '', self.tagname, self.urlJdbcServer)
        if server.Config.get('', '', self.tagname) != self.urlJdbcServer:
            server.Config.put('', '', self.tagname, self.urlJdbcServer)
        try:
            resultList = server.Query.execute('', '', query, [self.tagname])
        except ValueError:
            # Sometimes the you get an error like 'ValueError: invalid literal
            # for float(): NaN' For example, this error can occur if it wants
            # to get the mean, min, max or sum and there is is no data for
            # these results and it returns a strange square-symbol, which can
            # not be sent with xmlrpc as a float. Therefore, we catch the
            # error.
            return -2  # Error code.
        #now convert this list to a dictionary, using column_names (if present)
        try:
            rowLen = len(resultList[0])
        except:
            #todo: goede foutmelding oid
            return []
        #there are no columnNames: just take numbers
        if column_names == None:
            #make ['0', '1', ...] as columnNames
            column_names = map(lambda x: str(x), range(rowLen))
        result = []
        for row in resultList:
            newRow = {}
            for i in range(rowLen):
                if (row[i]) != (row[i]):
                    rowValue = None
                elif (date_fields is not None and
                      date_fields.count(column_names[i]) > 0):
                    # parse iso8601 date, maar niet helemaal omdat er
                    # minnetjes tussen moeten...   TODO: English
                    rowStr = str(row[i])
                    if len(rowStr) != 17:
                        # I saw dates like: 292278994-08-17 08:12:55.192
                        rowValue = None
                        log.error('Weird date found: %s', rowStr)
                    else:
                        rowEdited = (rowStr[:4] + '-' + rowStr[4:6] +
                                     '-' + rowStr[6:])
                        rowValue = iso8601.parse_date(rowEdited)
                elif (binary_fields is not None and
                      binary_fields.count(column_names[i]) > 0):
                    rowValue = row[i].data
                elif row[i] == -999:
                    rowValue = None
                else:
                    rowValue = row[i]
                newRow[column_names[i]] = rowValue
            result.append(newRow)
        return result

    def executeTest(self):
        return self.execute('select * from filters where issubfilter=0')

if __name__ == '__main__':
    #object testing
    print 'creating connect object Almere...'
    connect = ConnectDatabase2EiServer(
        'http://nens-web_extern:8080/Jdbc2Ei/test',
        'jdbc:vjdbc:rmi://192.168.0.23:2000/VJdbc,FewsDataStore')
    print 'result of query: ' + str(connect.execute(
            'select name,x,y from locations where x>161000',
            ['name', 'x', 'y']))

    print 'creating connect object Purmerend...'
    connect2 = ConnectDatabase2EiServer(
        'http://nens-web_extern:8080/Jdbc2Ei/test',
        'jdbc:vjdbc:rmi://192.168.0.23:2001/VJdbc,FewsDataStore')
    print 'result of query2: ' + str(connect2.execute(
            ("select LOCATIONID, PARAMETERID, MEAN, MIN, DATEOFMIN, MAX, "
             "DATEOFMAX, SUM, STANDARDDEVIATION, COUNT, ORIGINAL, COMPLETED, "
             "CORRECTED, RELIABLE, DOUBTFULL, UNRELIABLE, MISSING "
             "from timeseriesstats where filterid = 'PUR_FONE_RGM' "
             "and parameterid = 'V.berekend' and "
             "locationid = 'PUR_FONE_RGM_030058_Pomp 2' and "
             "time between '2009-01-01 00:00:00' and "
             "'2009-02-01 00:00:00'"),
            columnNames=['LOCATIONID', 'PARAMETERID', 'MEAN', 'MIN',
                         'DATEOFMIN',
                         'MAX', 'DATEOFMAX', 'SUM', 'STANDARDDEVIATION',
                         'COUNT',
                         'ORIGINAL', 'COMPLETED', 'CORRECTED', 'RELIABLE',
                         'DOUBTFULL', 'UNRELIABLE', 'MISSING']))
