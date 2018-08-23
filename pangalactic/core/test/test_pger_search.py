# $Id$

"""
Functional test for PGER.search()
"""

from pprint import pprint
from twisted.internet import reactor
from pangalactic.repo.pger import PGER

def success(resultsets):
    pprint(resultsets)
    print
    print '(%s objects found.)' % len(resultsets)
    print
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

out = PGER.search('test', 'Model', refs=0, subtypes=0,
                  args=[('name', 'like', 'twang')]
                  )

out.addCallbacks(success, failure)

reactor.run() # start the main loop

