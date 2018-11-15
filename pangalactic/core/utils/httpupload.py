#!/usr/bin/env python
"""
Upload from the local path either the specified file, or all
files in the specified directory, as MIME multipart/form-data

Usage: httpupload.py localpath userid:passwd@url [oid]

    ... where url has the form:
    
       http[s]://host:port[resourcepath]

Options:
    -h / --help
        Print this message and exit.
"""
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
import base64
import getopt
from http.client import HTTPConnection, HTTPException
from http.client import HTTPSConnection
# For guessing MIME type based on file name extension
import mimetypes
import os
import string
import sys
from urllib.parse import urlparse

from email import Encoders
from email.MIMEAudio import MIMEAudio
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEImage import MIMEImage
from email.MIMEText import MIMEText


def usage(code, msg=''):
    print(__doc__, file=sys.stderr)
    if msg:
        print(msg, file=sys.stderr)
    sys.exit(code)

def enclose(lpath):
    """
    Create a part for a MIME multipart message

    @type lpath:  string
    @param lpath: path of file to be enclosed

    @rtype:      a subtype of email.Message
    @return:     an encoded part ready to attach to a
                 MIMEMultipart message
    """
    # Guess the content type based on the file's extension.  Encoding
    # will be ignored, although we should check for simple things like
    # gzip'd or compressed files.
    ctype, encoding = mimetypes.guess_type(lpath)
    if ctype is None or encoding is not None:
        # No guess could be made, or the file is encoded (compressed), so
        # use a generic bag-of-bits type.
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    if maintype == 'text':
        fp = open(lpath)
        # Note: we should handle calculating the charset
        msg = MIMEText(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == 'image':
        fp = open(lpath, 'rb')
        msg = MIMEImage(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == 'audio':
        fp = open(lpath, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=subtype)
        fp.close()
    else:
        fp = open(lpath, 'rb')
        msg = MIMEBase(maintype, subtype)
        msg.set_payload(fp.read())
        fp.close()
    # Encode the payload using Base64
    Encoders.encode_base64(msg)
    # Set the filename parameter
    filename = os.path.basename(lpath)
    msg.add_header('Content-Disposition', 'form-data',
                   name='file', filename=filename)
    return msg, filename, ctype

def upload(localpath='', host='', port='', srvpath='/', userid='',
           passwd='', secure=0, useragent='PanGalaxian [en]',
           oid='', mimetype=''):
    """
    Upload a file or files to an HTTP server.

    @type localpath:    string or list
    @param localpath:   local file, directory, or list of file(s)
                        to be uploaded.  If a directory, only
                        files in that directory will be included
                        (non-recursive).  If a list, only files
                        will be included (not directories).
                        Paths may be relative or absolute.

    @type host:         string
    @param host:        hostname of the HTTP server

    @type port:         string
    @param port:        port of the HTTP server

    @type srvpath:      string
    @param srvpath:     path to the upload resource on the HTTP
                        server

    @type userid:       string
    @param userid:      userid for Basic Auth

    @type passwd:       string
    @param passwd:      passwd for Basic Auth

    @type secure:       int
    @param secure:      if 0, use http; if 1, use https

    @type useragent:    string
    @param useragent:   value for User-Agent header; default is
                        'PanGalaxian [en]'

    @type oid:          string
    @param oid:         oid of the repository FileLink with
                        which the uploaded file is to be
                        associated

    @rtype:             string
    @return:            the space-delimited concatenation of two
                        strings:
                        (1) the file size in bytes
                        (2) the oid of the corresponding
                        FileLink object in the database.
    """
    files = []
    if isinstance(localpath, str):
        p = os.path.abspath(localpath)
        if os.path.isfile(p):
            files = [p]
        elif (os.path.isdir(p)):
            for fn in os.listdir(p):
                if (os.path.isfile(fn)):
                    files.append(os.path.join(p, fn))
    elif isinstance(localpath, list):
        for p in localpath:
            p = os.path.abspath(p)
            if os.path.isfile(p):
                files.append(p)
    # Create the container
    outer = MIMEMultipart(_subtype='form-data')
    # Add the file(s)
    fns = []
    for f in files:
        msg, filename, filemime = enclose(f)
        outer.attach(msg)
        fns.append(filename)
    fnheader = ', '.join(fns)
    # Send to the server
    if secure:
        h = HTTPSConnection(host, int(port))
    else:
        h = HTTPConnection(host, port)
    h.putrequest('POST', srvpath)
    h.putheader('Host', host+':'+port)
    h.putheader('Accept', '*/*')
    h.putheader('Proxy-Connection', 'Keep-Alive')
    h.putheader('User-Agent', useragent)
    h.putheader('Referer', host+':'+port+srvpath)
    h.putheader('Filenames', fnheader)
    h.putheader('Oid', oid)
    # if a mime type is passed in, use it ...
    if mimetype:
        h.putheader('FileMimeType', mimetype)
    # otherwise, use the one that enclose() guessed ...
    else:
        h.putheader('FileMimeType', filemime)
    h.putheader('Content-Length', len(outer.as_string()))
    h.putheader('Content-Type', outer['Content-Type'])
    h.putheader('MIME-Version', outer['MIME-Version'])
    if userid and passwd:
        auth = 'Basic ' + string.strip(base64.encodestring(userid + ':' + passwd))
        h.putheader('Authorization', auth)
    h.endheaders()
    h.send(outer.as_string()+'\n')
    response = h.getresponse()
    if response.status != 200:
        msg = "error: %s, %s\n%s\n%s" % (response.status,
                                         host+':'+port+srvpath,
                                         response.reason,
                                         response.msg) #.as_string())
        raise HTTPException(msg)
    return response.read()

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h:', ['help'])
    except getopt.error as msg:
        usage(1, msg)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)

    if len(args) < 2:
        usage(1)

    localpath = args[0]
    uri = args[1]
    try:
        oid = args[2]
    except:
        print('An oid (or target file name) must be supplied.')
        sys.exit()
    userpass, url = uri.split('@')
    userid, passwd = userpass.split(':')
    scheme, hostport, srvpath, p, q, f = urlparse(url)
    secure = 0
    if scheme == 'https':
        secure = 1
    host, port = hostport.split(':')
    upload(localpath=localpath,
           host=host,
           port=port,
           srvpath=srvpath,
           userid=userid,
           passwd=passwd,
           secure=secure,
           oid=oid)

