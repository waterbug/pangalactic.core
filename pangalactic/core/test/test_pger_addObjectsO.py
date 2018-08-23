# $Id$

"""
Functional test for PGER.addObjects()
"""

from twisted.internet import reactor
from pangalactic.repo.pger import PGER
from pangalactic.test.utils4test import gen_linked_test_objects

# create test objects
test_objects = gen_linked_test_objects('TPaOO', addable=True, versionable=False,
                                    registry=PGER.db.registry)

def success(results):
    print "\nAdded %s objects:\n" % len(results)
    print results
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

dts = PGER.addObjects(requestor='test:fester.bestertester',
                      objects=test_objects,
                      input='objects',
                      ret='objects')
dts.addCallbacks(success, failure)

reactor.run()

print '\n- test is complete -\n'

