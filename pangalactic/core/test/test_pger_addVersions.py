"""
Functional test for pger.add_versions()
"""

from pprint import pprint
from twisted.internet import reactor
from pangalactic.meta.utils import extract
from pangalactic.repo.pger import PGER
from pangalactic.test.utils4test import gen_linked_test_objects

#  Need to add something like this database command at the end of success to
#  verify that the new version was added and its attributes and flags were set
#  right:

#  select _oid, _base_id, _id, _name, _iteration, _version from _part
#  where _name = 'Flux Capacitor';

test_objects = gen_linked_test_objects('TPaV', PGER.db.registry, addable=True,
                                    versionable=True)
extracts = [extract(o) for o in test_objects]
print '------------------------------------------------------'
print 'Extracts of test objects:'
for e in extracts:
    pprint(e)
print '------------------------------------------------------'

def success(result):
    pprint(result)
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

res = PGER.addVersions('test', extracts)
res.addCallbacks(success, failure)

reactor.run()

