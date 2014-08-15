import datetime
import random


class DummyDatabaseConnector:
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def isAlive(self):
        return -1

    #returns a list of dictionaries. keys in the dict are the
    #columnNames, or ['0','1',...]
    #dateColumns: these columns need to be converted to python dates.
    def execute(self, query, column_names=None, date_fields=None,
                binary_fields=None,
                requesttagname=None, debug=False):
        if debug:
            #print 'about to execute: ' + query
            # ^^^ No printing in mod_wsgi
            pass
        #print query
        if query == 'get_filters':
            result = [{'id': 1, 'name': 'Gebied1', 'parentid': None},
                      {'id': 2, 'name': 'Gebied2', 'parentid': None},
                      {'id': 3, 'name': 'Gebied3', 'parentid': None},
                      {'id': 4, 'name': 'Gebied4', 'parentid': 1},
                      {'id': 5, 'name': 'Gebied5', 'parentid': 1},
                      {'id': 6, 'name': 'Gebied6', 'parentid': 2},
                      {'id': 7, 'name': 'Gebied7', 'parentid': 2},
                      {'id': 8, 'name': 'Gebied8', 'parentid': 2},
                      ]
        elif query.find('get_locations') >= 0:
            locations = (((5.18258096854, 52.4041857439),),
                         ((5.11600, 52.09297),
                          (5.10253, 52.09180),),
                         ((4.20433, 52.05736),),
                         ((6.58836, 53.22166),),
                         )
            result = []
            for i, loctuple in enumerate(locations):
                result.append({'id': '%d' % (i),
                               'name': 'locatie group %d' % (i),
                               'parentid': None,
                               'description': 'beschrijving',
                               'shortname': 'loc%d' % i,
                               'tooltiptext': 'demo location %d' % (i),
                               'longitude': loctuple[0][0] + 0.01,
                               'latitude': loctuple[0][1] + 0.01,
                               'in_filter': 1})
                for j, loc in enumerate(loctuple):
                    result.append({'id': 'l %d/%d' % (i, j),
                                   'name': 'locatatie %d/%d' % (i, j),
                                   'parentid': i,
                                   'description': 'beschrijving',
                                   'shortname': 'loc%d' % i,
                                   'tooltiptext':
                                   'demo location %d/%d' % (i, j),
                                   'longitude': loc[0],
                                   'latitude': loc[1],
                                   'in_filter': 1})
        elif query.find('parameter from filters') >= 0:
            result = []
            for i in range(10):
                result.append({'parameterid': i,
                               'parameter': 'parameter %d' % i})
        elif query.find('timeseriesgraph') >= 0:
            f = open('base/dummygraph.png', 'r')
            graph = f.read()
            f.close()
            result = [{'graph': graph}]
        elif query.find('timeseries') >= 0:
            time = datetime.datetime.now() - datetime.timedelta(days=1)
            delta = datetime.timedelta(minutes=15)
            result = []
            for t in range(96):
                result.append({'time': time,
                               'value': t + random.randint(0, 100) / 10,
                               'flag': 0,
                               'detection': None,
                               'comment': None})
                time += delta

        else:
            result = [{'A': 1, 'B': 2},
                      {'A': 3, 'B': 4},
                      ]
        return result
