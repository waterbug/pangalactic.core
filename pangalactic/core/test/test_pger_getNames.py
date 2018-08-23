# $Id$
"""
Functional test for PGER.getNames()
"""

from pprint import pprint
from twisted.internet import reactor
from pangalactic.repo.pger import PGER

def success(resultsets):
    pprint(resultsets)
    print
    print '(%s test Names found.)' % len(resultsets)
    print
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

out = PGER.getNames('test', 'sandbox')

out.addCallbacks(success, failure)

reactor.run() # start the main loop

