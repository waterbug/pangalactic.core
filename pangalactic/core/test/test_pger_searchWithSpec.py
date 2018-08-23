# $Id$

"""
Functional test for PGER.search(..., spec=(...))
"""

from pprint import pprint
from twisted.internet import reactor
from pangalactic.repo.pger import PGER

def success(resultsets):
    pprint(resultsets)
    print
    print '(%s things found.)' % len(resultsets)
    print
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

out = PGER.search('test', 'Model', refs=0, subtypes=0,
                  args=[('name', 'like', 'twang')],
                  spec=('id', 'name')
                  )

# out = PGER.search('test', 'Namespace', refs=0, subtypes=0,
#                   args=[('_schema_name', '=', 'Namespace')],
#                   spec=('oid', 'id')
#                   )

out.addCallbacks(success, failure)

reactor.run() # start the main loop

