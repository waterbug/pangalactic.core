# $Id$

"""
Functional test for PGER.getObjects() with extracts returned
"""

from pprint import pprint
from twisted.internet import reactor
from pangalactic.repo.pger import PGER

def success(objectlist):
    pprint(objectlist)
    # TODO:  determine # expected from direct DB query
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

res = PGER.getObjects(requestor='test',
                      schema_name='Representation',
                      id_ns='sandbox')
res.addCallbacks(success, failure)

reactor.run() # start the main loop

