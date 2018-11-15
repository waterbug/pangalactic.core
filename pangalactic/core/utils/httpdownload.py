#!/usr/bin/env python
"""
HTTP get.
"""
from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
from builtins import object
import os
import http.client
import string
import base64

from whrandom import randint
from time import time

class FileRequest(object):
    """
    HTTP file download.  Forces binary mode for a single file.
    """
    def __init__(self, tmpdir, uri, host, port, auth):
        self.uri = uri
        self.host = host
        self.port = port
        self.queryString = None
        self.auth = auth
        self.boundary= '%s%s_%s_%s' % ('-----', int(time()), os.getpid(), randint(1, 10000))
        self.tmpdir = tmpdir
        
    def request(self):
        h = http.client.HTTP()
        h.connect(self.host, self.port)
        h.putrequest('GET', self.uri)
        h.putheader('Accept', 'text/html')
        h.putheader('Accept', 'text/plain')
        h.putheader('Proxy-Connection', 'Keep-Alive')
        h.putheader('User-Agent', 'PGEF [en] (WinNT; U)')
        h.putheader('Authorization', self.auth)
        h.endheaders()
        rcode, rmsg, headers = h.getreply()
        if rcode != 200:
            msg = "error: %s, %s\n%s" % (rcode, self.uri, rmsg)
            raise http.client.HTTPException(msg)
        f = h.getfile()
        data = f.read() 
        f.close()
        localfile = open (os.path.join (self.tmpdir, os.path.basename(self.uri)), "w")
        localfile.write(data)
        localfile.close()
#        print "request rcode: " + str(rcode)
        return rcode


def httpGet(tmpdir, filename, user, host, port, subdir):

    # tbd - need to specify subdirectory on server
    #print "downloadfile"
    try:
        uri = "/pgef_files/" + subdir + "/" + filename
        #print "uri: " + uri
        # "Basic" authentication encodes userid:password in base64. Note
        # that base64.encodestring adds some extra newlines/carriage-returns
        # to the end of the result. string.strip is a simple way to remove
        # these characters.
        #print "host", type(host)
        #print "port", type(port)
        filerequest = FileRequest(tmpdir, uri, host, port, user._authorization)
        retval = filerequest.request()
        #print "retval: " + str(retval)        
        #import traceback
        #traceback.print_exc()
        return retval
    
    except Exception as e:
        #print "Get failed."
        #import traceback
        #traceback.print_exc()
        return "Get failed."

def test():
    # TODO:  need to reference a std test file here
    uri = ""
    host = 'localhost'
    port = 80
    # "Basic" authentication encodes userid:password in base64. Note
    # that base64.encodestring adds some extra newlines/carriage-returns
    # to the end of the result. string.strip is a simple way to remove
    # these characters.
    userid = "admin"
    passwd = "secret"
    auth = 'Basic ' + string.strip(base64.encodestring(userid + ':' + passwd))
    filerequest = FileRequest(uri, host, port, auth)
    response = filerequest.request()
    #print response

    
if __name__ == '__main__':
    print("else test")
    test()
