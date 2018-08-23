# $Id$

"""
Functional test for PGER.getObjects(..., oids=...)
"""

from pprint import pprint
from twisted.internet import reactor
from pangalactic.repo.pger import PGER

oids = ['sandbox:buckaroo.banzai',
        'sandbox:john.bigboote',
        'sandbox:john.smallberries',
        'sandbox:john.whorfin',
        'sandbox:H2G2',
        'sandbox:OTHER',
        'sandbox:OTHEROTHER',
        'sandbox:DOC-01.1',
        'sandbox:DOC-01.2',
        'sandbox:BTA-20.1',
        'sandbox:HM.200.1',
        'sandbox:FX-CAP.1',
        'sandbox:HOG.1',
        'sandbox:BTA-20.1-CAD.1',
        'sandbox:HM.200.1-CAD.1',
        'sandbox:FX-CAP.1-CAD.1',
        'sandbox:HOG.1-CAD.1',
        'sandbox:Representation.1',
        'sandbox:Representation.2',
        'sandbox:FileLink.1',
        'sandbox:FileLink.2',
        'sandbox:FileLink.3',
        'sandbox:FileLink.4'
        ]

def success(objectlist):
    pprint(objectlist)
    print 'expected:  %s' % str(len(oids))
    print 'got:       %s' % str(len(objectlist))
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

res = PGER.getObjectsByOids(requestor='test', oids=oids)
res.addCallbacks(success, failure)

reactor.run() # start the main loop

