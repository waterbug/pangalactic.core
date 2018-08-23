# $Id$

"""
Functional test for pangalactic.repo.pger module
  - executes PGER interface call(s):
    - getResultSets()
  - outputs results of callback(s)
"""

from twisted.internet import reactor
from pangalactic.repo.pger import PGER

def success(result):
    print
    print '* %s objects matched *' % result
    print '* 2 objects expected *'
    print
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

out = PGER.getCount('test', 'Model', refs=0, subtypes=0,
                    args=[('name', 'like', 'twang')]
                    )

out.addCallbacks(success, failure)

reactor.run() # start the main loop

