# $Source$

"""
Functional test for PGER.addExtracts()
"""

from pprint import pprint
from twisted.internet import reactor
from pangalactic.meta.utils import extract
from pangalactic.repo.pger import PGER
from pangalactic.test.utils4test import gen_linked_test_objects

# create test objects
test_objects = gen_linked_test_objects('TPaOE', addable=True, versionable=False,
                                    registry=PGER.db.registry)
extracts = [extract(o) for o in test_objects]

def success(result):
    pprint(result)
    print '\nAdded %s objects (as extracts).\n' % len(result)
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

res = PGER.addObjects('test:fester.bestertester', extracts)
res.addCallbacks(success, failure)

reactor.run()

