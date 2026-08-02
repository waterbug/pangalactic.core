# -*- coding: utf-8 -*-
"""
The Pan Galactic Engineering Framework (PGEF) core package.
"""
import os
import sys

# RDFLib
from rdflib import URIRef

# SqlAlchemy
from sqlalchemy import (Boolean, Date, DateTime, Float, Integer, LargeBinary,
                        String, Time)

# ruamel yaml
import ruamel_yaml as yaml

# pangalactic version
__version__ = '4.4.dev3'

# `diagramz` is a module-level dict that contains the data structure of the
# diagram cache (see pangalactic.node.gui.diagrams.view for more detail)
diagramz = {}

datatypes = {
    # (is_datatype, range, functional) : Column datatype
    (True, 'bool', True)      : Boolean,
    (True, 'bool', False)     : set,
    (True, 'int', True)       : Integer,  # BigInteger ?
    (True, 'int', False)      : set,
    (True, 'float', True)     : Float,    # ***
                                # *** cf. sa notes about Numeric/Decimal
    (True, 'float', False)    : set,
    # kb.py maps xsd:base64Binary to Python 'bytes', which is here mapped to sa
    # 'LargeBinary'.  The 'bytes' datatype is intended for data values which
    # may be used as Python identifiers
    (True, 'bytes', True)     : LargeBinary,
    (True, 'str', True)       : String,
                                # narrative -> "Text" (multi-line)
    (True, 'str', False)      : set,
    (True, 'date', True)      : Date,
    (True, 'date', False)     : set,
    (True, 'time', True)      : Time,
    (True, 'time', False)     : set,
    (True, 'datetime', True)  : DateTime,
    (True, 'datetime', False) : set,
    # TODO:  figure out what this should be for sqlalchemy automap classes ...
    #        meanwhile, not used
    (False, None, True)       : String,   # MAYBE!
    (False, None, False)      : set
    }

# xsd_datatypes was adapted from XSDtoPythonTypeNames in sparta.py, which is
# the mapping used by RDFLib, too.

# NOTE:  'token' was added to support specific PGEF semantics.

# The following copyright and permission notice are included from sparta.py:

# Copyright (c) 2001.3.10 Mark Nottingham <mnot@pobox.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

xsd_datatypes = {  #  (schema->python, python->schema)  Does not validate.
    URIRef('http://www.w3.org/2001/XMLSchema#string') : ('str', str),
    URIRef('http://www.w3.org/2001/XMLSchema#normalizedString') : ('str',
                                                                   str),
    # 'token' added -- maps to single-word text values
    URIRef('http://www.w3.org/2001/XMLSchema#token') : ('str', str),
    URIRef('http://www.w3.org/2001/XMLSchema#language') : ('str', str),
    URIRef('http://www.w3.org/2001/XMLSchema#boolean') : ('bool', 
                                                lambda i:str(i).lower()),
    URIRef('http://www.w3.org/2001/XMLSchema#decimal') : ('float', str),
    URIRef('http://www.w3.org/2001/XMLSchema#integer') : ('long', str),
    URIRef('http://www.w3.org/2001/XMLSchema#nonPositiveInteger') : ('int',
                                                                     str),
    URIRef('http://www.w3.org/2001/XMLSchema#long') : ('long', str),
    URIRef('http://www.w3.org/2001/XMLSchema#nonNegativeInteger') : ('int',
                                                                     str),
    URIRef('http://www.w3.org/2001/XMLSchema#negativeInteger') : ('int',
                                                                  str),
    URIRef('http://www.w3.org/2001/XMLSchema#int') : ('int', str),
    URIRef('http://www.w3.org/2001/XMLSchema#unsignedLong') : ('long',
                                                               str),
    URIRef('http://www.w3.org/2001/XMLSchema#positiveInteger') : ('int',
                                                                  str),
    URIRef('http://www.w3.org/2001/XMLSchema#short') : ('int', str),
    URIRef('http://www.w3.org/2001/XMLSchema#unsignedInt') : ('long', str),
    URIRef('http://www.w3.org/2001/XMLSchema#byte') : ('bytes', str),
    URIRef('http://www.w3.org/2001/XMLSchema#unsignedShort') : ('int',
                                                                str),
    URIRef('http://www.w3.org/2001/XMLSchema#unsignedByte') : ('int', str),
    URIRef('http://www.w3.org/2001/XMLSchema#float') : ('float', str),
    # doesn't do the whole range:
    URIRef('http://www.w3.org/2001/XMLSchema#double') : ('float', str),
    URIRef('http://www.w3.org/2001/XMLSchema#dateTime') : ('datetime', str),
    # base64Binary modified for use in PGEF
    URIRef('http://www.w3.org/2001/XMLSchema#base64Binary') : (
                                        'bytes', str),
                                        # base64.decodestring,
                                        # lambda i:base64.encodestring(i)[:-1]),
    URIRef('http://www.w3.org/2001/XMLSchema#anyURI') : ('str', str),
}

# `config`, `deleted`, `prefs`, `state`, and `trash` are module-level vars for
# application configuration, oids of deleted objects, user preferences, state,
# and deleted objects, respectively.
# (See NOTES_FOR_DEVELOPERS.md for more detail.)
config = {}
deleted = {}
prefs = {}
state = {}
trash = {}

# `deletion_queue` holds deletions made on a client while it was offline, so
# they can be replayed to the repository at the next sync:
#
#     {oid: {'cname': str, 'datetime': str}}
#
# Without it a deletion made offline is simply undone -- both sync paths treat
# "the client did not report this oid" as "the client needs it", so the server
# sends the object back and the client deserializes it again.  See
# pangalactic.node/NOTES_ON_OFFLINE_AND_SYNC.md section 3.2.
#
# NOTE: this is a *client-side* cache, and is deliberately a separate file
# rather than an item in `state`.  state is only written at shutdown, so a
# crash would lose the queued deletion and the object would quietly come back
# -- which is the failure this exists to prevent.  write_deletion_queue() is
# therefore called as soon as a deletion is queued, not at exit.
#
# The class name is kept alongside the oid because the object is already gone
# from the local db by the time the queue is read, so it is the only thing
# left to report the deletion with.
deletion_queue = {}

def my_unicode_repr(self, data):
    """
    Encode dumped unicode as utf-8.
    """
    return self.represent_str(data.encode('utf-8'))

yaml.representer.Representer.add_representer(str, my_unicode_repr)

def get_user_home():
    """
    Get the path of the user's home directory.

    NOTE: this exists so that the platform branch lives in exactly one place.
    It was previously copy-pasted into uberorb.start(), pangalaxian.run(), and
    gargleblaster's __main__ (plus a fourth copy in the experimental
    fastorb.py), each carrying the same latent bug: the win32 branch did
    "os.path.join(os.environ.get('USERPROFILE'))" -- a single-argument join,
    which raises TypeError when the variable is unset instead of yielding a
    falsy value the surrounding guard could catch.  In gargleblaster that made
    the "if all else fails" fallback unreachable, because the TypeError was
    raised before it.

    Returns:
        str:  path to the user's home directory, or '' if it cannot be
            determined -- callers are expected to fall back (typically to the
            current working directory)
    """
    if sys.platform == 'win32':
        return os.environ.get('USERPROFILE', '') or ''
    # Linux, macOS, and anything else posix-ish
    return os.environ.get('HOME', '') or ''

def read_config(configpath):
    """
    Read node config from the config file.
    """
    # TODO:  add checksum check for security
    if os.path.exists(configpath):
        with open(configpath) as f:
            data = f.read()
        if data:
            config.update(yaml.safe_load(data))

def write_config(configpath):
    """
    Write node config to the config file.
    """
    # TODO:  create checksum for security
    # NOTE: serialize *before* opening the file -- opening in 'w' mode
    # truncates it, so a yaml exception here would destroy the previous
    # contents.
    data = yaml.safe_dump(config, allow_unicode=True,
                          default_flow_style=False)
    with open(configpath, 'w') as f:
        f.write(data)

def read_deleted(deletedpath):
    """
    Read data from the deleted file.  NOTE: the 'deleted' cache is only used on
    the server side (vger), where it is used to ensure permanence of deletions.
    """
    # TODO:  add checksum check for security
    if os.path.exists(deletedpath):
        with open(deletedpath) as f:
            data = f.read()
        if data:
            deleted.update(yaml.safe_load(data))

def write_deleted(deletedpath):
    """
    Write data to the deleted file.  NOTE: the 'deleted' cache is only used on
    the server side (vger), where it is used to ensure permanence of deletions.
    """
    # TODO:  create checksum for security
    # NOTE: serialize *before* opening the file (see write_config).
    data = yaml.safe_dump(deleted, allow_unicode=True,
                          default_flow_style=False)
    with open(deletedpath, 'w') as f:
        f.write(data)

def read_deletion_queue(queuepath):
    """
    Read the offline deletion queue from its file.

    NOTE: client-side only -- see the `deletion_queue` comment above.
    """
    # TODO:  add checksum check for security
    if os.path.exists(queuepath):
        with open(queuepath) as f:
            data = f.read()
        if data:
            deletion_queue.update(yaml.safe_load(data))

def write_deletion_queue(queuepath):
    """
    Write the offline deletion queue to its file.

    Called as soon as a deletion is queued or cleared, rather than only at
    shutdown:  a deletion that is lost in a crash reappears at the next sync,
    silently, which is precisely what the queue exists to prevent.

    NOTE: serialize *before* opening the file (see write_config).
    """
    # TODO:  create checksum for security
    data = yaml.safe_dump(deletion_queue, allow_unicode=True,
                          default_flow_style=False)
    with open(queuepath, 'w') as f:
        f.write(data)

def read_prefs(prefspath):
    """
    Read user preferences from the prefs file.
    """
    # TODO:  add checksum check for security
    if os.path.exists(prefspath):
        with open(prefspath) as f:
            data = f.read()
        if data:
            prefs.update(yaml.safe_load(data))

def write_prefs(prefspath):
    """
    Write user preferences to the prefs file.
    """
    # NOTE: serialize *before* opening the file (see write_config).
    data = yaml.safe_dump(prefs, allow_unicode=True,
                          default_flow_style=False)
    with open(prefspath, 'w') as f:
        f.write(data)

def read_state(statepath):
    """
    Read node state from the state file.
    """
    # TODO:  add checksum check for security
    if os.path.exists(statepath):
        with open(statepath) as f:
            data = f.read()
        if data:
            saved_state = yaml.safe_load(data)
            # do not use saved 'app_' items -- may be modified in a new release
            app_items = []
            for item in saved_state:
                if 'app_' in item:
                    app_items.append(item)
            for item in app_items:
                del saved_state[item]
            state.update(saved_state)

def write_state(statepath):
    """
    Write node state to the state file.
    """
    # TODO:  create checksum for security
    # remove "sys_trees" item from state before writing (it contains binary
    # data this is not supported by yaml)
    if state.get('sys_trees'):
        del state['sys_trees']
    # NOTE: serialize *before* opening the file (see write_config).
    data = yaml.safe_dump(state, allow_unicode=True,
                          default_flow_style=False)
    with open(statepath, 'w') as f:
        f.write(data)

def read_trash(trashpath):
    """
    Read `trash` dictionary from the trash file.
    """
    # TODO:  add checksum check for security
    if os.path.exists(trashpath):
        with open(trashpath) as f:
            data = f.read()
        if data:
            trash.update(yaml.safe_load(data))

def write_trash(trashpath):
    """
    Write `trash` dictionary to the trash file.
    """
    # NOTE: serialize *before* opening the file (see write_config).
    data = yaml.safe_dump(trash, allow_unicode=True,
                          default_flow_style=False)
    with open(trashpath, 'w') as f:
        f.write(data)

