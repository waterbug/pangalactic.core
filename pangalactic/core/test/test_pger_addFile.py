# $Id$

"""
Functional test for PGER.addFile()
"""

import base64
import time
from pprint import pprint
from twisted.internet import reactor
from pangalactic.repo.pger import PGER

fileoid = '.'.join(['test:TPaF.txt', str(time.time())])
headers = {}
headers['oid'] = fileoid
headers['user-agent'] = 'PanGalaxian'
headers['filenames'] = 'TPaF.txt'
headers['filemimetype'] = 'text/plain'
text = 'This is a test; this is only a test.\n'
text += 'If this were your real life, you would have \n'
text += 'received much more detailed instructions.\n'
text = base64.encodestring(text)

def success(result):
    pprint(result)
    reactor.stop()

def failure(error):
    print error
    reactor.stop()

added = PGER.addFile('test:fester.bestertester', headers, text)
added.addCallbacks(success, failure)

reactor.run()

