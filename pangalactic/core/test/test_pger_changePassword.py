# $Id$

"""
Functional test for PGER.changePassword()
"""

from twisted.internet import reactor
from pangalactic.repo.pger import PGER

def success(res):
    print res
    reactor.stop()

def failure(f):
    print f
    reactor.stop()

d = PGER.changePassword('admin', 'zaphod', 'sekret')
d.addCallbacks(success, failure)

reactor.run()

