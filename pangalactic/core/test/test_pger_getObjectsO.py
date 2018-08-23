# $Id$

"""
Functional test for PGER.getObjects()
  - initializes Pger
  - executes Pger interface call(s):
    - getObjects()
  - outputs results of callback(s)
"""

import os
from twisted.internet import reactor
from pangalactic.repo.pger import PGER
from pangalactic.node.uberorb import UberORB

U = UberORB(debug=True)
U.initCache(home='pangalaxian_test')

def success(extracts):
    print "\ntest objects returned:"
    for e in extracts:
        obj = U.remember(e)
        print obj
    print
    print "(%s test objects)" % len(extracts)
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

out = PGER.getObjects(requestor='test',
                      schema_name='Part',
                      id_ns='sandbox')
out.addCallbacks(success, failure)

reactor.run()

print '\n- end of test -'

