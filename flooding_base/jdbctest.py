#!/usr/bin/env python
"""
fews jdbc performance test.

requirements:
   - a working jdbc2ei instance
   - a working jdbc instance
"""

import threading

from flooding_base.eidatabaseconnector import ConnectDatabase2EiServer


class Thread (threading.Thread):

    def __init__(self, name):
        self.name = name
        threading.Thread.__init__(self)

    def run(self):
        #print(self.name)
        #vul hier je jdbc2ei adres en je jdbc adres in!
        #c = ConnectDatabase2EiServer(
        #    'http://localhost:8080/Jdbc2Ei/test',
        #    'jdbc:vjdbc:rmi://192.168.0.165:2000/VJdbc,FewsDataStore')
        # TODO: ^^^ can this be removed?  [reinout]
        c = ConnectDatabase2EiServer(
            'http://localhost:8080/Jdbc2Ei/test',
            'jdbc:vjdbc:rmi://192.168.0.165:2000/VJdbc,FewsDataStore')

        counter = 0
        while True:
            #print('%s (%d)' % (self.name, counter))
            c.execute("SELECT * from locations WHERE Id = 'ALM_241/0'")
            c.execute("SELECT * from TimeSeries WHERE filterId = 'ALM_ALL' "
                      "AND parameterId = 'h.niveau.max'  AND "
                      "locationId = 'ALM_241/0' AND time BETWEEN "
                      "'2007-01-01 13:00:00' AND '2009-01-10 13:00:00'")

            c.execute("SELECT * from TimeSeriesGraphs WHERE "
                      "filterId = 'ALM_GW_NonA' AND "
                      "parameterId = 'h.grond.meting'  AND "
                      "locationId = 'ALM_GWAB_14' AND "
                      "time BETWEEN '2006-01-01 13:00:00' AND "
                      "'2009-01-10 13:00:00' and width=1000 and height=1000")

            counter += 1


if __name__ == '__main__':
    for i in range(500):
        Thread('%d' % i).start()
    # TODO: niet meer te stoppen!
