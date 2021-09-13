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
from pangalactic.core.meta import (PLURALS, ATTR_EXT_NAMES, EXT_NAMES,
                                   EXT_NAMES_PLURAL, MAX_LENGTH, READONLY)
from pangalactic.core.utils.datetimes import EPOCH, EPOCH_DATE

_inf = inflect.engine()


def asciify(u):
    """
    "Intelligently" convert a unicode string to the ASCII character set --
    a.k.a. "The Stupid American", a.k.a. "The UNICODE Hammer".  Its main
    purpose is to convert things that might be used in Python identifiers so
    they can be typed on an en-us encoded keyboard!

    Credit: http://code.activestate.com/recipes/251871/ (this is not that
    recipe but an elegant one-liner from one of the comments on the recipe).

    Args:
        u (str or bytes): input value

    Returns:
        str
    """
    # Python 3: returns utf-8 string
    if isinstance(u, str):
        return unicodedata.normalize('NFKD', u).encode(
                                'ASCII', 'ignore').decode('utf-8')
    elif isinstance(u, bytes):
        return u.decode('utf-8')
    # allow only printable chars
    printable = set(string.printable)
    clean = filter(lambda x: x in printable, str(u))
    return clean

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
     'max_length'    : [maximum length of a string field],
     'null'          : [bool:  whether the field can be null],
     'editable'      : [bool:  opposite of read-only],
     'unique'        : [bool:  same as the sql concept],
     'external_name' : [name displayed in user interfaces],
     'definition'    : [definition of the field],
     'help_text'     : [extra help text, in addition to definition],
     'db_column'     : [name of the db column (default is field name)]
    }

    The 'fields' key in a schema dict will consist of a dict that maps
    field names to field dicts of this form.
    """
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
        field['max_length'] = MAX_LENGTH.get(pe['id'], 80)
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

def get_attr_ext_name(cname, aname):
    return (ATTR_EXT_NAMES.get(cname) or {}).get(
                                            aname, ' '.join(aname.split('_')))

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
        tname = (parts[0] + parts[1]).lower()
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
        tname = (parts[0] + parts[1]).lower()
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

def get_data_element_definition_oid(deid):
    """
    Return the oid of the DataElementDefinition for the specified data element
    id.

    Args:
        deid (str): the 'id' defined in the DataElementDefinition
    """
    return 'pgef:DataElementDefinition.' + deid

def get_parameter_definition_oid(variable):
    """
    Return the oid of the ParameterDefinition for the specified variable.

    Args:
        variable (str): the variable defined by the ParameterDefinition
    """
    return 'pgef:ParameterDefinition.' + variable

def get_parameter_context_oid(pcid):
    """
    Return the oid of the ParameterContext with the specified 'id'.

    Args:
        pcid (str): the ParameterContext 'id'
    """
    return 'pgef:ParameterContext.' + pcid

def get_state_oid(sid):
    """
    Return the oid of the State with the specified 'id'.

    Args:
        sid (str): the State 'id'
    """
    return 'pgef:State.' + sid

def get_ra_id(ra_context_id, role_id, fname, mi, lname):
    """
    Create an 'id' for a new RoleAssignment.

    Args:
        ra_context_id: 'id' of the role_assignment_context (Org)
        role_id:  the 'id' of the Role
        fname:  first name of the Person
        mi:  middle name or initial of the Person
        lname:  last name of the Person
    """
    if ra_context_id:
        return '-'.join([ra_context_id, role_id,
                         '_'.join([lname, fname, mi])])
    else:
        return '-'.join([role_id, '_'.join([lname, fname, mi])])

def get_next_ref_des(assembly, component, prefix=None, product_type=None):
    """
    Get the next reference designator for the specified assembly and component.

    This function assumes that reference designators are strings of the form
    'prefix-n', where 'n' can be cast to an integer.

    Args:
        assembly (Product): the product containing the component
        component (Product): the constituent product

    Keyword Args:
        prefix (str): a string to be used as the prefix of the reference
            designator
        product_type (ProductType): a product type to use if component is None
            or does not have a product_type
    """
    prefix = ''
    if getattr(component, 'product_type', None):
        prefix = (component.product_type.abbreviation or
                  component.product_type.name)
    if not prefix and product_type:
        prefix = product_type.abbreviation or product_type.name
    if not prefix:
        prefix = 'Generic'
    acus = assembly.components
    if acus:
        rds = [acu.reference_designator for acu in acus]
        # product_type abbreviation should not contain '-', but it can
        all_prefixes = [(''.join(rd.split('-')[:-1])) for rd in rds if rd]
        these_prefixes = [p for p in all_prefixes if p == prefix]
        new_nbr = len(these_prefixes) + 1
        refdes = prefix + '-' + str(new_nbr)
        while 1:
            if refdes not in rds:
                break
            else:
                new_nbr += 1
                refdes = prefix + '-' + str(new_nbr)
        return refdes
    else:
        return prefix + '-1'

def get_ra_name(ra_context_id, role_id, fname, mi, lname):
    """
    Create a 'name' for a new RoleAssignment.

    Args:
        ra_context_id:  the id of the ra 'context' (Org or Project)
        role_id:  the id of the assigned Role
        fname:  first name of the assignee
        mi:  middle initial of the assignee
        lname:  last name of the assignee
    """
    if ra_context_id:
        return ': '.join([ra_context_id, role_id,
                         ' '.join([lname, fname, mi])])
    else:
        return ': '.join([role_id, ' '.join([lname, fname, mi])])

def get_acr_id(comp_act_id, sub_act_role):
    """
    Create an 'id' for a new ActCompRel.

    Args:
        comp_act_id:  the 'id' of the composite activity (Activity)
        sub_act_role:  the sub_activity_role
    """
    return comp_act_id + '-' + '-'.join(sub_act_role.split(' '))

def get_acr_name(comp_act_name, sub_act_role):
    """
    Create a 'name' for a new ActCompRel.

    Args:
        comp_act_name:  the 'name' of the composite activity (Activity)
        sub_act_role:  the sub_activity_role
    """
    return comp_act_name + '-' + '-'.join(sub_act_role.split(' '))

def get_acu_id(assembly_id, ref_des):
    """
    Create an 'id' for a new Acu.

    Args:
        assembly_id:  the 'id' of the assembly (Product)
        ref_des:  the reference_designator of the Acu, created using
            get_next_ref_des()
    """
    return assembly_id + '-' + '-'.join(ref_des.split(' '))

def get_acu_name(assembly_name, ref_des):
    """
    Create a 'name' for a new Acu.

    Args:
        assembly_name:  the 'name' of the assembly (Product)
        ref_des:  the reference_designator of the Acu, created using
            get_next_ref_des()
    """
    return assembly_name + ' : ' + ref_des

def get_mel_item_name(usage):
    """
    Create a unique name for a line item in a MEL (Master Equipment List).

    Args:
        usage (Acu or ProjectSystemUsage):  the item usage
    """
    # newlines *should* not occur in a product name but have been known to --
    # hence the '\n' replacements ...
    if hasattr(usage, 'component'):
        # usage is an Acu instance
        name = (getattr(usage.component, 'name', '') or 'unknown').replace(
                '\n', ' ').strip()
        if usage.reference_designator:
            return '[' + usage.reference_designator + '] ' + name
        else:
            return name
    elif hasattr(usage, 'system'):
        # usage is an ProjectSystemUsage instance
        name = (getattr(usage.system, 'name', '') or 'unknown').replace(
                '\n', ' ').strip()
        if usage.system_role:
            return '[' + usage.system_role + '] ' + name
        else:
            return name
    else:
        return 'NO ITEM'

def get_rel_id(context_id, role_id):
    """
    Create an 'id' for a new Relation.

    Args:
        context_id (str):  the 'id' of related context (a Requirement, e.g.)
        role_id (str):  the role of the Relation in the specified context
    """
    return context_id + '-' + role_id + '-relation'

def get_rel_name(context_name, role_name):
    """
    Create a name for a new Relation.

    Args:
        context_name (str):  the name of related context (a Requirement, e.g.)
        role_name (str):  its role name in the specified context
    """
    return context_name + ' ' + role_name + ' Relation'

def get_parm_rel_id(rel_id, pid):
    """
    Create an 'id' for a new ParameterRelation.

    Args:
        rel_id (str):  the 'id' of related Relation
        pid (str):  the parameter id of the related ParameterDefinition
    """
    return rel_id + '-' + pid + '-parm-rel'

def get_parm_rel_name(rel_name, pname):
    """
    Create a name for a new ParameterRelation.

    Args:
        rel_name (str):  the name of related Relation
        pname (str):  the parameter name of the related ParameterDefinition
    """
    return rel_name + ' ' + pname + ' Parameter Relation'

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

def get_port_id(port_type_id, seq):
    """
    Create an id for a new Port.

    Args:
        port_type_id (str):  the id of the port's type_of_port (PortType)
        seq (int):  the sequence number assigned to the port
    """
    return '-'.join([port_type_id, str(seq)])

def get_port_name(port_type_name, seq):
    """
    Create a name for a new Port.

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
    version = getattr(obj, 'version', None)
    obj_id = getattr(obj, 'id', None) or 'unknown'
    if version:
        return obj_id + '.v.' + version
    else:
        return obj_id

def get_display_name(obj):
    """
    Return a string to display as 'name' that will include, if `obj` is an
    instance of Product, its 'version' string if it is not null.

    Args:
        obj (Identifiable):  object whose name is to be displayed
    """
    version = getattr(obj, 'version', None)
    name = getattr(obj, 'name', None) or 'Unidentified'
    if version:
        return ' v. '.join([name, version])
    else:
        return name

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
    return ' '.join([get_display_name(obj), 'Pgx IBD'])

def get_block_model_file_name(obj):
    """
    Get canonical file name for a pgx block model.

    Args:
        obj (Modelable):  the object that is the subject of the model
    """
    return get_block_model_id(obj) + '.json'

def dump_metadata(extr, fpath):
    """
    JSON-serialize an extract and write it utf-8-encoded into file.
    """
    f = codecs.open(fpath, 'w', 'utf-8')
    json.dump(extr, f, sort_keys=True, indent=4, ensure_ascii=True)
    f.close()

def ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('utf-8') if isinstance(x, str) else x
    return dict(list(map(ascii_encode, pair)) for pair in list(data.items()))

def load_metadata(fpath):
    """
    Read and deserialize a utf-8-encoded JSON-serialized extract from a file.
    """
    f = codecs.open(fpath, 'r', 'utf-8')
    data = f.read()
    f.close()
    # return json.loads(data, object_hook=ascii_encode_dict)
    return json.loads(data)

def cook_string(value):
    return asciify(value)

def cook_unicode(value):
    return value

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
           # 'bytes'    : cook_string,
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
# * they cast a "cooked" [serialized] value to the specified range type
#
# * the uncookers dictionary is an optimization to enable quick look-up of
#   deserialization functions

def uncook_string(value):
    """
    Deserialize a string or bytes field.

    Args:
        value (str, bytes, or None):  the value being "uncooked"
    """
    return asciify(value) if value is not None else None

def uncook_strings(value):
    """
    Deserialize a set or list of strings.

    Args:
        value (set or list of strs):  the value being "uncooked"
    """
    if type(value) is set:
        return set(asciify(s) for s in value)
    return list(asciify(s) for s in value)

def uncook_unicode(value):
    """
    Deserialize a unicode field.

    Args:
        value (unicode or None):  the value being "uncooked"
    """
    return asciify(value)

def uncook_unicodes(value):
    """
    Deserialize a set or list of strings that represents a set or list of
    unicode objects, respectively.

    Args:
        value (set or list of strs):  the value being "uncooked"
    """
    if type(value) is set:
        return set(asciify(s) for s in value)
    return list(asciify(s) for s in value)

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
    Deserialize a string value that represents a date.  If value *is* a date,
    return it; otherwise try to parse it; if that fails, return EPOCH_DATE.

    Args:
        value (str):  the value being "uncooked"
    """
    if type(value) is date:
        return value
    elif value is None:
        return None
    try:
        return dtparser.parse(value).date()
    except:
        return EPOCH_DATE

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
    Deserialize a string value that represents a datetime.  If value *is* a
    datetime, return it; otherwise try to parse it; if that fails, return
    EPOCH.

    Args:
        value (str):  the value being "uncooked"
    """
    if type(value) is datetime:
        return value
    elif value is None:
        return None
    try:
        return dtparser.parse(value)
    except:
        return EPOCH

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
             # ('bytes', True)     : uncook_string,
             # ('bytes', False)    : uncook_strings,
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

