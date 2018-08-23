# -*- coding: utf-8 -*-
"""
Utilities for doing meta stuff
"""
import codecs
import inflect
import json
import re
import string
import unicodedata
from datetime import date, datetime
from textwrap import wrap

# SqlAlchemy
from sqlalchemy import ForeignKey

# python-dateutil
import dateutil.parser as dtparser

# PanGalactic
from pangalactic.core      import datatypes
from pangalactic.core.meta import (PLURALS, EXT_NAMES, EXT_NAMES_PLURAL,
                                   READONLY)

_inf = inflect.engine()


def asciify(u):
    """
    "Intelligently" convert unicode to ascii -- a.k.a. "The Stupid American",
    a.k.a. "The UNICODE Hammer".  Its main purpose is to convert things that
    are going to be used in Python identifiers ... so they can be typed on an
    en-us encoded keyboard!

    Credit: http://code.activestate.com/recipes/251871/ (this is not that
    recipe but an elegant one-liner from one of the comments on the recipe).
    """
    if type(u) == unicode:
        return unicodedata.normalize('NFKD', u).encode('ASCII', 'ignore')
    return u

def property_to_field(name, pe):
    """
    Create a field dict from a property extract.  The field dict has the
    following form (terminology adopted from django-metaservice api):

    {
     'id'            : [the name of the field],
     'id_ns'         : [namespace in which name of the field exists],
     'field_type'    : [the field type, a SqlAlchemy class],
     'local'         : [bool:  True -> locally defined; False -> inherited],
     'related_cname' : [for fk fields, name of the related class],
     'functional'    : [bool:  True -> single-valued],
     'range'         : [python datatype name or, if fk, related class name],
     'inverse_functional' : [bool:  True -> one-to-one],
     'is_inverse'    : [bool:  True -> property is an inverse ("backref")],
     'inverse_of'    : [name of property of which this one is an inverse],
     'choices'       : [choices list -- i.e., a discrete range],
     'null'          : [bool:  whether the field can be null],
     'editable'      : [bool:  opposite of read-only],
     'unique'        : [bool:  same as the sql concept],
     'external_name' : [name displayed in user interfaces]
     'definition'    : [definition of the field],
     'help_text'     : [extra help text, in addition to definition]
     'db_column'     : [name of the db column (default is field name)],
    }

    The 'fields' key in a schema dict will consist of a dict that maps
    field names to field dicts of this form.
    """
    # TODO:  add max_length and/or other applicable constraints
    field = {}
    field['id'] = pe['id']
    field['id_ns'] = pe['id_ns']
    field['definition'] = pe['definition']
    field['functional'] = pe['functional']
    field['range'] = pe['range']
    field['editable'] = not name in READONLY
    field['external_name'] = ' '.join(pe['id'].split('_'))
    if pe['is_datatype']:
        field['field_type'] = datatypes[(pe['is_datatype'],
                                         pe['range'],
                                         pe['functional'])]
        field['is_inverse'] = False
        field['inverse_of'] = ''
    else:
        field['field_type'] = ForeignKey
        field['related_cname'] = pe['range']
        field['is_inverse'] = pe['is_inverse']
        field['inverse_of'] = pe['inverse_of']
    return field

def get_external_name(cname):
    return EXT_NAMES.get(cname, to_external_name(cname))

def get_external_name_plural(cname):
    return EXT_NAMES_PLURAL.get(cname,
                                to_external_name(cname)+'s')

def to_external_name(cname):
    """
    Convert a standard metaobject (class, interface, or schema) camelcase name
    into a user-interface-friendly name.

    @param cname: a camelcase metaobject name
    @type  cname: L{str}

    @return: an "external name"
    @rtype:  L{str}
    """
    patt = re.compile('([A-Z])')
    l = re.split(patt, cname)
    parts = l[1:]
    if 0 < len(parts) < 3:
        vname = parts[0] + parts[1]
    elif len(parts) > 2:
        vname = parts[0] + parts[1]
        i = 2
        while i < len(parts):
            if i % 2 == 0:
                vname += ' '
            vname += parts[i]
            i += 1
    return vname

def to_table_name(cname):
    """
    Convert a standard (camelcase) class name into an underscore-delimited,
    lowercase table name.

    @param cname: a camelcase class name
    @type  cname: L{str}

    @return: a table name
    @rtype:  L{str}
    """
    patt = re.compile('([A-Z])')
    l = re.split(patt, cname)
    parts = l[1:]
    if 0 < len(parts) < 3:
        tname = string.lower(parts[0] + parts[1])
    elif len(parts) > 2:
        tname = parts[0] + parts[1]
        i = 2
        while i < len(parts):
            if i % 2 == 0:
                tname += '_'
            tname += parts[i]
            i += 1
        tname = tname.lower()
    return tname +  '_'

def pname_to_header_label(pname):
    """
    Convert a standard property name into a header-friendly name.

    @param pname: a Property name
    @type  pname: L{str}

    @return: an "external name"
    @rtype:  L{str}
    """
    parts = ' '.join(pname.split('_'))
    wrapped = ' \n '.join(wrap(parts, width=7, break_long_words=False))
    return ' ' + wrapped + ' '

def to_media_name(cname):
    """
    Convert a standard (camelcase) class name into a media name (primarily for
    use with pyqt drag and drop data).

    @param cname: a camelcase class name
    @type  cname: L{str}

    @return: a media name
    @rtype:  L{str}
    """
    patt = re.compile('([A-Z])')
    l = re.split(patt, cname)
    parts = l[1:]
    if 0 < len(parts) < 3:
        tname = string.lower(parts[0] + parts[1])
    elif len(parts) > 2:
        tname = parts[0] + parts[1]
        i = 2
        while i < len(parts):
            if i % 2 == 0:
                tname += '-'
            tname += parts[i]
            i += 1
        tname = tname.lower()
    return "application/x-pgef-" + tname

def to_collection_name(cname):
    """
    Convert a standard metaobject (class, interface, or schema) camelcase name
    into the name of an attribute that refers to a collection of that kind of
    object -- e.g.: 'Class' -> 'classes', 'Person' -> 'people', etc.

    @param cname: a camelcase metaobject name
    @type  cname: L{str}

    @return: a table name
    @rtype:  L{str}
    """
    return str(to_table_name(PLURALS.get(
                        cname, _inf.plural(cname)))[:-1])

def to_class_name(table_name):
    """
    Convert an underscore-delimited, lowercase table name into a
    metaobject (class, interface, or schema) camelcase name.

    @param table_name: table name
    @type  table_name: L{str}

    @return: C{Interface} name
    @rtype:  L{str}
    """
    tn = table_name[:-1] # drop trailing '_'
    parts = tn.split('_')
    i = 0
    metaobject_name = ''
    while i < len(parts):
        metaobject_name += parts[i].capitalize()
        i += 1
    return str(metaobject_name)

def classnamify(base, tablename, table):
    """
    Specifically for use as the value of SqlAlchemy AutomapBase argument
    `classname_for_table`.  Clearly, it is simply a wrapper for
    `to_class_name`, converting a table name (with trailing underscore) to
    the corresponding class name.
    """
    return to_class_name(tablename)

def get_parameter_definition_oid(parameter_id):
    """
    Return the oid of a ParameterDefinition instance based on its `id`.

    Args:
        parameter_id (str): the ParameterDefinition `id` value
    """
    return 'pgef:ParameterDefinition.' + parameter_id

def get_acu_id(assembly_id, ref_des):
    """
    Create an 'id' for a new Acu.

    Args:
        assembly_id:  the 'id' of the assembly (Product)
        ref_des:  the reference_designator of the Acu, created using
            orb.get_next_ref_des()
    """
    return 'acu-' + assembly_id + '-' + ref_des

def get_acu_name(assembly_name, ref_des):
    """
    Create a 'name' for a new Acu.

    Args:
        assembly_name:  the 'name' of the assembly (Product)
        ref_des:  the reference_designator of the Acu, created using
            orb.get_next_ref_des()
    """
    return 'acu: ' + ref_des + ' of ' + assembly_name

def get_next_port_seq(obj, port_type):
    """
    Get the next sequence number for an object and a type of port.

    Args:
        obj (Modelable):  object that may have ports
        port_type (PortType):  the PortType to be considered
    """
    if not getattr(obj, 'ports', None):
        return 0
    try:
        seq_ints = [int(port.id.split('-')[-1]) for port in obj.ports
                    if port.type_of_port is port_type]
        if seq_ints:
            return max(seq_ints) + 1
        else:
            return 0
    except:
        return 0

def get_port_id(obj_id, port_type_id, seq):
    """
    Create an id for a new Port.

    Args:
        obj_id (str):  the id of the object that owns the port
        port_type_id (str):  the id of the port's type_of_port (PortType)
        seq (int):  the sequence number assigned to the port
    """
    return '-'.join([obj_id, port_type_id, str(seq)])

def get_port_name(obj_name, port_type_name, seq):
    """
    Create a name for a new Port.

    Args:
        obj_name (str):  the name of the object that owns the port
        port_type_name (str):  the name of the port's type_of_port (PortType)
        seq (int):  the sequence number assigned to the port
    """
    return ' '.join([obj_name, port_type_name, str(seq)])

def get_port_abbr(port_type_name, seq):
    """
    Create an abbreviation for a new Port (to be shown in tooltip).

    Args:
        port_type_name (str):  the name of the port's type_of_port (PortType)
        seq (int):  the sequence number assigned to the port
    """
    return ' '.join([port_type_name, str(seq)])

def get_flow_id(start_port_id, end_port_id):
    """
    Create an id for a new Flow.

    Args:
        start_port_id:  the id of the start_port
        end_port_id:  the id of the end_port
    """
    return '-'.join(['flow', start_port_id, end_port_id])

def get_flow_name(start_port_name, end_port_name):
    """
    Create a name for a new Flow.

    Args:
        start_port_name:  the name of the start_port
        end_port_name:  the name of the end_port
    """
    return ' '.join(['Flow:', start_port_name, 'to', end_port_name])

def display_id(obj):
    """
    Return a string to display as 'id' that will include, if `obj` is an
    instance of Product, its 'version' string if it is not null.

    Args:
        obj (Identifiable):  object whose id is to be displayed
    """
    if getattr(obj, 'version', None):
        return obj.id + '.v' + obj.version
    else:
        return getattr(obj, 'id', 'TBD')

def display_name(obj):
    """
    Return a string to display as 'name' that will include, if `obj` is an
    instance of Product, its 'version' string if it is not null.

    Args:
        obj (Identifiable):  object whose name is to be displayed
    """
    if getattr(obj, 'version', None):
        return ' v. '.join([obj.name, obj.version])
    else:
        return getattr(obj, 'name', 'TBD')

def get_block_model_id(obj):
    """
    Get canonical 'id' for a pgx block model.

    Args:
        obj (Modelable):  the object that is the subject of the model
    """
    return '_'.join([display_id(obj), 'pgx_ibd'])

def get_block_model_name(obj):
    """
    Get canonical 'name' for a pgx block model.

    Args:
        obj (Modelable):  the object that is the subject of the model
    """
    return ' '.join([display_name(obj), 'Pgx IBD'])

def get_block_model_file_name(obj):
    """
    Get canonical file name for a pgx block model.

    Args:
        obj (Modelable):  the object that is the subject of the model
    """
    return get_block_model_id(obj) + '.json'

def dump_metadata(extr, fpath):
    """
    JSON-serialize an extract and write it ascii-encoded into file.
    """
    f = codecs.open(fpath, 'w', 'ascii')
    json.dump(extr, f, sort_keys=True, indent=4, ensure_ascii=True)
    f.close()

def ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('ascii') if isinstance(x, unicode) else x
    return dict(map(ascii_encode, pair) for pair in data.items())

def load_metadata(fpath):
    """
    Read and deserialize an ascii-encoded JSON-serialized extract from a file.
    """
    
    f = codecs.open(fpath, 'r', 'ascii')
    data = f.read()
    f.close()
    return json.loads(data, object_hook=ascii_encode_dict)

def cook_string(value):
    return asciify(value)

def cook_unicode(value):
    return value.encode('utf-8')

def cook_int(value):
    return value

def cook_float(value):
    return str(value)

def cook_bool(value):
    return value

def cook_date(value):
    return str(value)

def cook_time(value):
    return str(value)

def cook_datetime(value):
    return str(value)

# python 2 strings, obviously
cookers = {
           'bytes'    : cook_string,
           'str'      : cook_string,
           'unicode'  : cook_unicode,
           'int'      : cook_int,
           'float'    : cook_float,
           'bool'     : cook_bool,
           'date'     : cook_date,
           'time'     : cook_time,
           'datetime' : cook_datetime
           }


# * "uncookers" are deserializing functions
#
# * they cast a "cooked" [serialized value to the specified range type
#
# * the uncookers dictionary is an optimization to enable quick look-up of
#   deserialization functions

def uncook_string(value):
    """
    Deserialize a string field.

    Args:
        value (str or None):  the value being "uncooked"
    """
    return str(value) if value is not None else None

def uncook_strings(value):
    """
    Deserialize a set or list of strings.

    Args:
        value (set or list of strs):  the value being "uncooked"
    """
    if type(value) is set:
        return set(value)
    return list(value)

def uncook_unicode(value):
    """
    Deserialize a unicode field.

    Args:
        value (unicode or None):  the value being "uncooked"
    """
    return unicode(value).decode('utf-8') if value is not None else None

def uncook_unicodes(value):
    """
    Deserialize a set or list of strings that represents a set or list of
    unicode objects, respectively.

    Args:
        value (set or list of strs):  the value being "uncooked"
    """
    if type(value) is set:
        return set(value)
    return list(value)

def uncook_int(value):
    """
    Deserialize a string that represents an integer.

    Args:
        value (str):  the value being "uncooked"
    """
    if value:
        return int(value)
    return None

def uncook_ints(value):
    """
    Deserialize a set or list of strings that represents a set or list of
    ints, respectively.

    Args:
        value (set or list of strs):  the value being "uncooked"
    """
    if type(value) is set:
        return set([uncook_int(v) for v in value])
    return [int(v) for v in value]

def uncook_float(value):
    """
    Deserialize a string that represents a float.

    Args:
        value (str):  the value being "uncooked"
    """
    if type(value) is float:
        return value
    elif value:
        return float(value)
    return None

def uncook_floats(value):
    """
    Deserialize a set or list of strings that represents a set or list of
    floats, respectively.

    Args:
        value (set or list of strs):  the value being "uncooked"
    """
    if type(value) is set:
        return set([uncook_float(v) for v in value])
    return [uncook_float(v) for v in value]

def uncook_bool(value):
    """
    Deserialize a string that represents a boolean.

    Args:
        value (str):  the value being "uncooked"
    """
    if type(value) is bool:
        return value
    return (value == 'True') if value is not None else None

def uncook_bools(value):
    """
    Deserialize a set or list of strings that represents a set or list of
    bools, respectively.

    Args:
        value (set or list of strs):  the value being "uncooked"
    """
    if type(value) is set:
        return set([uncook_bool(v) for v in value])
    return [uncook_bool(v) for v in value]

def uncook_date(value):
    """
    Deserialize a string that represents a date.

    Args:
        value (str):  the value being "uncooked"
    """
    if type(value) is date:
        return value
    elif value is None:
        return None
    return dtparser.parse(value).date()

def uncook_dates(value):
    """
    Deserialize a set or list of strings that represents a set or list of
    dates, respectively.

    Args:
        value (set or list of strs):  the value being "uncooked"
    """
    if type(value) is set:
        return set([uncook_date(v) for v in value])
    return [uncook_date(v) for v in value]

def uncook_datetime(value):
    """
    Deserialize a string that represents a datetime.

    Args:
        value (str):  the value being "uncooked"
    """
    if type(value) is datetime:
        return value
    elif value is None:
        return None
    return dtparser.parse(value)

def uncook_datetimes(value):
    """
    Deserialize a set or list of strings that represents a set or list of
    datetimes, respectively.

    Args:
        value (set or list of strs):  the value being "uncooked"
    """
    if type(value) is set:
        return set([uncook_datetime(v) for v in value])
    return [uncook_datetime(v) for v in value]

# dictionary of uncook functions, indexed by the Property attributes
# (range, functional)

uncookers = {
             ('bytes', True)     : uncook_string,
             ('bytes', False)    : uncook_strings,
             ('str', True)       : uncook_string,
             ('str', False)      : uncook_strings,
             ('unicode', True)   : uncook_unicode,
             ('unicode', False)  : uncook_unicodes,
             ('int', True)       : uncook_int,
             ('int', False)      : uncook_ints,
             ('float', True)     : uncook_float,
             ('float', False)    : uncook_floats,
             ('bool', True)      : uncook_bool,
             ('bool', False)     : uncook_bools,
             ('date', True)      : uncook_date,
             ('date', False)     : uncook_dates,
             ('datetime', True)  : uncook_datetime,
             ('datetime', False) : uncook_datetimes
             }

