# -*- coding: utf-8 -*-
"""
The Pan Galactic Engineering Framework (PGEF) core package.
"""
import os

# RDFLib
from rdflib import URIRef

# SqlAlchemy
from sqlalchemy import (Boolean, Date, DateTime, Float, Integer, LargeBinary,
                        String, Time)

# ruamel_yaml
import ruamel_yaml as yaml

# pangalactic version
__version__ = '3.0'

# `diagramz` is a module-level variable for the diagram cache
# (see pangalactic.node.gui.diagrams.view for more detail)
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

def my_unicode_repr(self, data):
    """
    Encode dumped unicode as utf-8.
    """
    return self.represent_str(data.encode('utf-8'))

yaml.representer.Representer.add_representer(str, my_unicode_repr)

def read_config(configpath):
    """
    Read node config from the config file.
    """
    # TODO:  add checksum check for security
    if os.path.exists(configpath):
        f = open(configpath)
        data = f.read()
        if data:
            config.update(yaml.safe_load(data))
        f.close()

def write_config(configpath):
    """
    Write node config to the config file.
    """
    # TODO:  create checksum for security
    # try:
    f = open(configpath, 'w')
    f.write(yaml.safe_dump(config, allow_unicode=True,
                           default_flow_style=False))
    f.close()
    # except:
    # raise ValueError, 'Could not write config.'

def read_deleted(deletedpath):
    """
    Read data from the deleted file.  NOTE: the 'deleted' cache is only used on
    the server side (vger), where it is used to ensure permanence of deletions.
    """
    # TODO:  add checksum check for security
    if os.path.exists(deletedpath):
        f = open(deletedpath)
        data = f.read()
        if data:
            deleted.update(yaml.safe_load(data))
        f.close()

def write_deleted(deletedpath):
    """
    Write data to the deleted file.  NOTE: the 'deleted' cache is only used on
    the server side (vger), where it is used to ensure permanence of deletions.
    """
    # TODO:  create checksum for security
    # try:
    f = open(deletedpath, 'w')
    f.write(yaml.safe_dump(deleted, allow_unicode=True,
                           default_flow_style=False))
    f.close()
    # except:
    # raise ValueError, 'Could not write deleted.'

def read_prefs(prefspath):
    """
    Read user preferences from the prefs file.
    """
    # TODO:  add checksum check for security
    if os.path.exists(prefspath):
        f = open(prefspath)
        data = f.read()
        if data:
            prefs.update(yaml.safe_load(data))
        f.close()

def write_prefs(prefspath):
    """
    Write user preferences to the prefs file.
    """
    # try:
    f = open(prefspath, 'w')
    f.write(yaml.safe_dump(prefs, allow_unicode=True,
                           default_flow_style=False))
    f.close()
    # except:
    # raise ValueError, 'Could not write prefs.'

def read_state(statepath):
    """
    Read node state from the state file.
    """
    # TODO:  add checksum check for security
    if os.path.exists(statepath):
        f = open(statepath)
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
        f.close()

def write_state(statepath):
    """
    Write node state to the state file.
    """
    # TODO:  create checksum for security
    # try:
    f = open(statepath, 'w')
    # remove "sys_trees" item from state before writing (it contains binary
    # data this is not supported by yaml)
    if state.get('sys_trees'):
        del state['sys_trees']
    f.write(yaml.safe_dump(state, allow_unicode=True,
                           default_flow_style=False))
    f.close()
    # except:
    # raise ValueError, 'Could not write state.'

def read_trash(trashpath):
    """
    Read `trash` dictionary from the trash file.
    """
    # TODO:  add checksum check for security
    if os.path.exists(trashpath):
        f = open(trashpath)
        data = f.read()
        if data:
            trash.update(yaml.safe_load(data))
        f.close()

def write_trash(trashpath):
    """
    Write `trash` dictionary to the trash file.
    """
    # try:
    f = open(trashpath, 'w')
    f.write(yaml.safe_dump(trash, allow_unicode=True,
                           default_flow_style=False))
    f.close()
    # except:
    # raise ValueError, 'Could not write trash.'

