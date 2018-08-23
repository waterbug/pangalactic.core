# $Id$

"""
Functional for PGER getting a result set for a list of docs
obtained from a full text search
  - executes interface call:
    - [PyLucene].search(string)
  - does a PgerDb search on the results
  - outputs results of callback(s)
"""

from pprint import pprint
from twisted.internet import reactor
# from pangalactic.repo.pger import PGER

def success(result):
    print '\n Expected 4 result sets; got %s:\n' % len(result)
    pprint(result)
    print
    print "\n- end of test -"
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

# result = [pylucene].search('vacuum')
# result.addCallback(lambda x: PGER.search('Alert', 
#                                          'test', 0, 0, 0,
#                                          ('oid', tuple(x))))
# result.addCallbacks(success, failure)
# reactor.run()

