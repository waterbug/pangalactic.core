# -*- coding: utf-8 -*-
"""
Serializers / deserializers for pangalactic domain objects and parameters.
"""
from datetime import date, datetime

# Louie
# from louie import dispatcher

# python-dateutil
import dateutil.parser as dtparser

from pangalactic.core.meta import asciify, M2M, ONE2M
from pangalactic.core.refdata     import ref_oids
from pangalactic.core.utils.datetimes import earlier, EPOCH, EPOCH_DATE
from pangalactic.core.parametrics import (deserialize_des,
                                          deserialize_parms,
                                          refresh_componentz,
                                          refresh_systemz,
                                          refresh_req_allocz,
                                          serialize_des, serialize_parms,
                                          update_de_defz, update_parm_defz,
                                          update_parmz_by_dimz)

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


def serialize(orb, objs, include_components=False,
              include_sub_activities=False, include_refdata=False,
              include_inverse_attrs=False):
    """
    Args:
        orb (UberORB): the (singleton) `orb` instance
        objs (iterable of objects):  the objects to be serialized.

    Keyword Args:
        include_components (bool):  if True:
            * for Products, components (items linked by Assembly Component
              Usage relationships), ports, and internal flows (connections
              among components) will be included in the serialization -- i.e.,
              a "white box" representation
            ******************************************************************
            *** NOTE that for Acus and PSUs, the following behavior is
            *NOT* dependent on `include_components`:
            * for Acus, assembly and component objects will always be
              included
            * for PSUs, system object will always be included
            ******************************************************************
            *** NOTE also, for RoleAssignments, the following behavior is
            *NOT* dependent on `include_components`:
            * 'assigned_role' (Role) object will always be included
            * 'assigned_to' (Person) object will always be included
            * 'role_assignment_context' (Org) object will always be included
            ******************************************************************
        include_refdata (bool):  [default: False] if True, serialize
            reference data -- in general, it is not necessary to include
            reference data, since it is known to both client and server; it is
            only desirable to include reference data when data is to be
            exchanged with an external application, in which case a standard
            data exchange format would be preferable.

    Serialize a collection or iterable of objects into a data structure
    consisting of primitive types; specifically, into a list of canonical
    dictionaries based on their class schemas.

    The primary purpose of this function is to produce a data structure
    that supports transmitting PanGalactic objects among client nodes and
    service nodes in the PanGalactic network architecture.  It is intended
    to be compatible with conversion to MessagePack, JSON, or YAML.

    Secondary purposes are to enable (1) saving of objects when the
    application schema is changed so they can be reloaded into a new
    database with a different schema, and (2) exporting objects to files
    for data exchange with other applications.

    Values of dates and datetimes are "asciified"; values of unicode fields
    are encoded as UTF-8 strings; objects are replaced by their 'oid'
    values.  For full detail, see the 'cookers' and 'uncookers' functions
    in pangalactic.meta.utils.

    PGEF schemas have the following form (may have additional keys):

        {'field_names'    : [field names in the order defined in the model],
         'base_names'     : [names of immediate superclasses for the schema],
         'definition'     : [ontological class definition],
         'pk_name'        : [name of the primary key field for this model],
         'fields' : {
            field-1-name  : { [field-1-attrs] },
            field-2-name  : { [field-2-attrs] },
            ...           
            field-n-name  : { [field-n-attrs] }
            }
        }

    ... where the field schemas (field-n-attrs) are of the form specified
    in `pangalactic.meta.utils.property_to_field`.

    The serialization has the following form (where the 'parameters' attribute
    is a special case to enable the object's parameters to be deserialized
    along with the object):

        {'_cname'        : [class name for the object],
         field-1-name    : [field-1-value],
         field-2-name    : [field-2-value],
         ...
         'data_elements' : serialized data elements dictionary
         'parameters'    : serialized parameters dictionary
         }

    If an object has data elements in 'data_elementz', their dictionary (the value of
    data_elementz[obj.oid]) is serialized and assigned to the serialized object as
    the 'data_elements' key.

    If an object has parameters in 'parameterz', their dictionary (the value of
    parameterz[obj.oid]) is serialized and assigned to the serialized object as
    the 'parameters' key.
    """
    # orb.log.info('* serializing objects ...')
    if not objs:
        return []
    serialized = []
    # NOTE [SCW 2020-05-22]:  previously, the Person and Organization objects
    # for the creator, modifier, owner attributes were all included in
    # serializations -- they are not necessary now that all Person and
    # Organization objects are being synced first.
    # NOTE [SCW 2020-05-22]:  previously, the ProductType and ActivityType objects
    # for the product_type, product_type_hint, and activity_type attributes
    # were included in serializations -- this is not necessary because they are
    # refdata objects.
    for obj in objs:
        if not obj:
            # orb.log.debug('  - null object "{}"'.format(obj))
            # don't include the null object in serialized
            # serialized.append(obj)
            continue
        # orb.log.info('  - obj.id: {}'.format(obj.id))
        # orb.log.debug('  - {}'.format(obj.id))
        cname = obj.__class__.__name__
        schema = orb.schemas[cname]
        d = {}
        d['_cname'] = cname
        # serialize data elements and parameters, if any
        # (they can only be assigned to subclasses of Modelable)
        if isinstance(obj, orb.classes['Modelable']):
            # serialize data elements
            d['data_elements'] = serialize_des(obj.oid)
            # serialize parameters
            d['parameters'] = serialize_parms(obj.oid)
        for name in schema['fields']:
            if getattr(obj, name, None) is None:
                # ignore None values
                continue
            elif schema['fields'][name]['field_type'] == 'object':
                if schema['fields'][name]['is_inverse']:
                    if include_inverse_attrs:
                        # inverse properties will be serialized if
                        # 'include_inverse_attrs' is True and they are not
                        # empty, but will never be deserialized, since they
                        # are inferred from db operations
                        # d[name] = '[inverse property]'  # <- for testing
                        rel_objs = getattr(obj, name)
                        if rel_objs:
                            # d[name] = [asciify(o.oid) for o in rel_objs]
                            d[name] = [o.oid for o in rel_objs]
                    else:
                        continue
                else:
                    # d[name] = asciify(getattr(getattr(obj, name), 'oid'))
                    d[name] = getattr(getattr(obj, name), 'oid')
            else:
                datatype = schema['fields'][name]['range']
                d[name] = cookers[datatype](getattr(obj, name))
        serialized.append(d)
        if getattr(obj, 'component', None):
            # Acu:  always include both assembly and component ...
            serialized += serialize(orb, [obj.assembly, obj.component])
        elif getattr(obj, 'system', None):
            # PSU:  always include `system`; `project` should be present
            serialized += serialize(orb, [obj.system])
        # 'include_components' only applies to Products ... and only
        # "direct components" will be included (not entire assemblies)
        if include_components and getattr(obj, 'components', None):
            sacus = serialize(orb, obj.components)
            serialized += sacus
            scomps = serialize(orb, [acu.component
                                     for acu in obj.components])
            serialized += scomps
        # 'include_sub_activities' only applies to Activities ... and only
        # "direct sub_activities" will be included (not recursive)
        if include_sub_activities and getattr(obj, 'sub_activities', None):
            ser_acrs = serialize(orb, obj.sub_activities)
            serialized += ser_acrs
            ser_acts = serialize(orb, [acr.sub_activity
                                       for acr in obj.sub_activities])
            serialized += ser_acts
        ###################################################################
        # NOTE:  Ports and Flows need to be part of a "product definition"
        # abstraction -- i.e., the "white box" model of the product
        # TODO:  implement "white box" vs. "black box" serializations and,
        # more broadly, white/black box Product objects!  Maybe use a new
        # 'product_definition' attribute that can be white or black box ...
        if isinstance(obj, orb.classes['Product']):
            # + for now, ALWAYS include ports (white box)
            if obj.ports:
                s_ports = serialize(orb, obj.ports)
                serialized += s_ports
            # + for now, ALWAYS include flows (white box)
            #   NOTE: technically any ManagedObject can be a flow_context but
            #   as a practical matter, only Products are currently supported
            flows = orb.get_internal_flows_of(obj)
            if flows:
                s_flows = serialize(orb, flows)
                serialized += s_flows
        ###################################################################
        if isinstance(obj, orb.classes['RoleAssignment']):
            # include Role object
            serialized += serialize(orb, [obj.assigned_role])
            # include Person object
            serialized += serialize(orb, [obj.assigned_to])
            # include Organization object
            serialized += serialize(orb, [obj.role_assignment_context])
        if isinstance(obj, orb.classes['Requirement']):
            # include 'computable_form' (a Relation object)
            if obj.computable_form:
                serialized += serialize(orb, [obj.computable_form])
                # include any relevant ParameterRelation objects)
                if obj.computable_form.correlates_parameters:
                    for pr in obj.computable_form.correlates_parameters:
                        serialized += serialize(orb, [pr])
    # orb.log.info('  serialized {} objects.'.format(len(serialized)))
    # make sure there is only 1 serialized object per oid ...
    so_by_oid = {so['oid'] : so for so in serialized}
    if not include_refdata:
        # exclude reference data objects
        so_by_oid = {oid: so_by_oid[oid] for oid in so_by_oid
                     if oid not in ref_oids}
    return list(so_by_oid.values())

# DESERIALIZATION_ORDER:  order in which to deserialize classes so that
# object properties (relationships) are assigned properly (i.e., assemblies are
# assigned their components, etc.)
# ****************************************************************************
# NOTE: this ordering is EXTREMELY important in that if it is not correct, the
# deserialization process will encounter ForeignKeyViolation errors from the
# database if expected objects do not exist when an object that depends on
# them is being deserialized -- obviously, the ordering is from the simplest
# objects to the most complex, but it must specifically take into account the
# relationships in the schema.
# ****************************************************************************
DESERIALIZATION_ORDER = [
                    'Relation',
                    'Discipline',
                    'Role',
                    'Organization',
                    'Project',
                    'Person',
                    'RoleAssignment',
                    'DataElementDefinition',
                    'ParameterDefinition',
                    'ParameterRelation',
                    'PortType',
                    'PortTemplate',
                    'ProductType',
                    'ActivityType',
                    'Product',
                    'Template',
                    'HardwareProduct',
                    'SoftwareProduct',
                    'DigitalProduct',
                    'Acu',
                    'ProjectSystemUsage',
                    'Activity', # Activity references Acu and PSU
                    'Mission',
                    'ActCompRel',
                    'Model',
                    'Port',
                    'Flow',
                    'Representation',
                    'RepresentationFile',
                    'Requirement'
                    ]


def deserialize(orb, serialized, include_refdata=False, dictify=False,
                force_no_recompute=False, force_update=False):
    """
    Args:
        orb (UberORB): the (singleton) `orb` instance
        serialized (iterable of dicts):  the serialized objects

    Keyword Args:
        include_refdata (bool):  [default: False] if True, deserialize
            reference data -- this option is *ONLY* to be used for the
            orb.load_reference_data() and orb.load_and_transform_data()
            functions
        dictify (bool):  [default: False] if True, return the result as
            a dictionary with keys 'new', 'modified', 'unmodified' and
            'error':

            [1] new:  objects that did not exist in the database
            [2] modified:  objects that existed in the database but the
                serialized object had a later mod_datetime
            [3] unmodified:  objects that existed in the database and the
                serialized object's mod_datetime was the same or earlier
            [4] error:  deserialization encountered an error
        force_no_recompute (bool):  [default: False] if True, do not recompute
            parameters -- this is used when further deserializations are
            planned that will trigger the recomputation of parameters
        force_update (bool):  [default: False] if True, update objects even if
            the datetimes are earlier than the existing objects'

    Deserialize a collection of objects that have been serialized using
    `serialize()`.

    For a given object:
        (0) Check for 'oid' in db; if found, check the db obj.mod_datetime:
            (a) if mod_datetime is same or earlier, ignore the object
            (b) if mod_datetime is later, update the object
            (c) if oid not found in db, deserialize the object
        (1) Include all datatype properties
        (2) Other object properties will be deserialized only if
            they are direct (not inverse) properties
    """
    # orb.log.debug('* deserializing ...')
    if not serialized:
        # orb.log.debug('  no objects provided -- returning []')
        return []
    # SCW 2017-08-24  Deserializer ignores objects that don't have an oid!
    # input_len = len(serialized)
    serialized = [so for so in serialized if so and so.get('oid')]
    new_len = len(serialized)
    # NOTE: this signal was part of a progress method that didn't work
    # dispatcher.send(signal='deserializing', n=new_len)
    # if new_len < input_len:
        # orb.log.debug('  {} empty objects removed.'.format(
                                                    # input_len - new_len))
    if new_len == 0:
        # orb.log.debug('  all objects were empty -- returning []')
        return []
    # else:
        # orb.log.debug('* deserializing {} object(s) ...'.format(new_len))
        # objoids = [so['oid'] for so in serialized]
        # orb.log.debug('  {}'.format(pprint.pformat(objoids)))

    one2m_or_m2m = list(ONE2M) + list(M2M)
    recompute_parmz_required = False
    refresh_componentz_required = False
    refresh_systemz_required = False
    req_oids = set()
    acus = set()
    psus = set()
    # objs: list of all deserialized objects
    objs = []
    # products: list of deserialized objects that are instances of Product
    # subclasses
    products = []
    # requirements: list of deserialized objects that are Requirement instances
    requirements = []
    # created: list of all deserialized objects which are new
    created = []
    # updates: list of all deserialized objects which are updates
    updates = {}
    # ignores: list of serialized object oids for which local objects exist
    # that have the same or later mod_datetime or should be ignored for some
    # other reason (e.g. invalid Port and Flow instances)
    ignores = []
    # loadable: dict mapping class names to lists of serialized objects of the
    # class, used to implement DESERIALIZATION_ORDER for the objects to be
    # deserialized
    loadable = {}
    loadable['other'] = []
    if dictify:
        output = dict(new=[], modified=[], unmodified=[], error=[])
    if not include_refdata:
        # exclude reference data objects
        serialized = [so for so in serialized
                      if not so.get('oid', '') in ref_oids]
                      # if not asciify(so.get('oid', '')) in ref_oids]
    # if len(serialized) < new_len:
        # orb.log.info('  {} ref data object(s) found, ignored.'.format(
                                               # new_len - len(serialized)))
    current_oids = orb.get_oids()
    # incoming_oids = [so['oid'] for so in serialized]
    for so in serialized:
        so_cname = so.get('_cname')
        if not so_cname:
            # ignore objects without a '_cname'
            # orb.log.debug('  object has no _cname, ignoring:')
            # orb.log.debug('  {}'.format(so))
            continue
        if so_cname not in orb.classes:
            # ignore objects with '_cname' not in pangalactic classes
            # orb.log.debug('  object _cname unrecognized, ignoring:')
            # orb.log.debug('  {}'.format(so))
            continue
        if so['_cname'] in DESERIALIZATION_ORDER:
            if so['_cname'] in loadable:
                loadable[so['_cname']].append(so)
            else:
                loadable[so['_cname']] = [so]
        else:
            loadable['other'].append(so)
    order = [c for c in DESERIALIZATION_ORDER if c in loadable]
    order.append('other')
    # NOTE: this `i` was part of a progress method that didn't work
    # keep count of deserialized objs for progress signal
    # i = 0
    for group in order:
        for d in loadable[group]:
            cname = d.get('_cname', '')
            schema = orb.schemas[cname]
            field_names = schema['field_names']
            if not cname:
                raise TypeError('class name not specified')
            # orb.log.debug('* deserializing serialized object:')
            # orb.log.debug('  %s' % str(d))
            # oid = asciify(d['oid'])
            oid = d['oid']
            # if oid:
            if cname == 'Flow' and d.get('flow_context'):
                ###########################################################
                # SPECIAL CASE: convert pre-3.0 Flow instances
                ###########################################################
                flow_id = d['id']
                orb.log.debug('  pre-3.0 schema Flow object:')
                orb.log.debug(f'  id: "{flow_id}" [oid: {oid}]')
                start_port = orb.get(d.get('start_port'))
                end_port = orb.get(d.get('end_port'))
                flow_context = orb.get(d.get('flow_context'))
                if start_port and end_port and flow_context:
                    txt = "start port, end port and flow context found."
                    orb.log.debug(f'    {txt}')
                    # flow_context is assembly
                    assembly = flow_context
                    component = None
                    port_is_on_assembly = False
                    if start_port.of_product.oid == flow_context.oid:
                        port_is_on_assembly = True
                        txt = "start port is a port on the assembly"
                        orb.log.debug(f'    {txt}')
                        start_port_context = None
                        end_port_context = flow_context.oid
                        component = end_port.of_product
                        assembly = start_port.of_product
                    elif end_port.of_product.oid == flow_context.oid:
                        port_is_on_assembly = True
                        txt = "end port is a port on the assembly"
                        orb.log.debug(f'    {txt}')
                        start_port_context = flow_context.oid
                        end_port_context = None
                        component = start_port.of_product
                        assembly = end_port.of_product
                    if port_is_on_assembly:
                        if assembly and component:
                            rel_acus = orb.search_exact(cname='Acu',
                                                        assembly=assembly,
                                                        component=component)
                            if rel_acus and (start_port_context is None):
                                d['end_port_context'] = rel_acus[0].oid
                                d['start_port_context'] = ''
                                orb.log.debug('  - success:')
                                orb.log.debug('    contexts defined.')
                            elif rel_acus and (end_port_context is None):
                                d['start_port_context'] = rel_acus[0].oid
                                d['end_port_context'] = ''
                                orb.log.debug('  - success:')
                                orb.log.debug('    contexts defined.')
                    else:
                        # flow is between components within an assembly
                        assembly = flow_context
                        start_component = start_port.of_product
                        end_component = end_port.of_product
                        start_acus = orb.search_exact(
                                            cname='Acu',
                                            assembly=assembly,
                                            component=start_component)
                        end_acus = orb.search_exact(
                                            cname='Acu',
                                            assembly=assembly,
                                            component=end_component)
                        if start_acus and end_acus:
                            d['start_port_context'] = start_acus[0].oid
                            d['end_port_context'] = end_acus[0].oid
                            orb.log.debug('  - success:')
                            orb.log.debug('    contexts defined.')
                        else:
                            # new Flow MUST have both contexts
                            orb.log.debug('  - ignored:')
                            orb.log.debug('    indeterminable contexts.')
                            ignores.append(oid)
                else:
                    # pre-3.0 Flow must have start_port, end_port, and
                    # flow_context
                    orb.log.debug('  - ignored:')
                    txt = "missing start port, end port or flow context."
                    orb.log.debug(f'    {txt}')
                    ignores.append(oid)
            if oid in current_oids:
                # orb.log.debug('  - object exists in db ...')
                # the serialized object exists in the db
                db_obj = orb.get(oid)
                # check against db object's mod_datetime
                so_datetime = uncook_datetime(d.get('mod_datetime'))
                if force_update and db_obj:
                    # orb.log.debug('    forcing update ... ')
                    updates[oid] = db_obj
                    orb.db.add(db_obj)
                    if dictify:
                        output['modified'].append(db_obj)
                elif not (so_datetime and db_obj and
                          earlier(db_obj.mod_datetime, so_datetime)):
                    # txt = '    object "{}" has same or older'.format(oid)
                    # orb.log.debug('{} mod_datetime, ignoring.'.format(txt))
                    # if not, ignore it
                    ignores.append(oid)
                    # NOTE: do not return "ignored" objs SCW 2019-09-05
                    # objs.append(db_obj)
                    if dictify:
                        output['unmodified'].append(db_obj)
                    continue
                else:
                    # orb.log.debug('    object has later '
                                  # 'mod_datetime, saving it.')
                    # if it is newer, update the object
                    if db_obj:
                        updates[oid] = db_obj
                        orb.db.add(db_obj)
                        if dictify:
                            output['modified'].append(db_obj)
                    else:
                        continue
            # first do datatype properties (non-object properties)
            kw = dict([(name, d.get(name))
                           for name in field_names
                           if (schema['fields'][name]['range']
                                        not in orb.classes)])
            # include 'unicode' in case string (byte) serialization used
            specials = [name for name in field_names
                        if schema['fields'][name]['range']
                        in ['date', 'datetime']]
            for name in specials:
                kw[name] = uncookers[
                                    (schema['fields'][name]['range'],
                                     schema['fields'][name]['functional'])
                                        ](d.get(name))
            # NOTE: special case for 'data_elements' section
            de_dict = d.get('data_elements')
            if de_dict:
                # orb.log.debug('  + data elements found: {}'.format(de_dict))
                # orb.log.debug('    deserializing data elements ...')
                deserialize_des(oid, de_dict, cname=cname)
            else:
                pass
                # orb.log.debug('  + no data elements found for this object.')
            # NOTE: special case for 'parameters' section
            parm_dict = d.get('parameters')
            if parm_dict:
                recompute_parmz_required = True
                # orb.log.debug('  + parameters found: {}'.format(parm_dict))
                # orb.log.debug('    deserializing parameters ...')
                deserialize_parms(oid, parm_dict, cname=cname)
            else:
                pass
                # orb.log.debug('  + no parameters found for this object.')
            # identify fk values; explicitly ignore inverse properties
            # (even though d should not have any)
            # orb.log.debug('  + checking for fk fields')
            fks = [a for a in field_names
                   if ((not schema['fields'][a]['is_inverse'])
                        and (schema['fields'][a].get('related_cname')
                             in orb.classes))]
            if fks:
                # orb.log.debug('    fk fields found: {}'.format(asciify(fks)))
                for fk in fks:
                    # get the related object by its oid (i.e. d[fk])
                    # orb.log.debug('    * rel obj oid: "{}"'.format(
                                   # asciify(d.get(asciify(fk)))))
                    # if d.get(asciify(fk)):
                    if d.get(fk):
                        # orb.log.debug('      rel obj found.')
                        # kw[asciify(fk)] = orb.get(asciify(d[asciify(fk)]))
                        kw[fk] = orb.get(d[fk])
                    else:
                        # "of_product" is REQUIRED for a Port (it is NOT
                        # required for a PortTemplate, a subtype of Port)
                        if fk == 'of_product' and cname == 'Port':
                            orb.log.debug('      invalid Port instance:')
                            oid = d['oid']
                            orb.log.debug(f'      - oid: "{oid}"')
                            orb.log.debug('        is missing of_product;')
                            orb.log.debug('        will be ignored.')
                            ignores.append(oid)
                        # a Flow MUST have "start_port", "end_port",
                        # "start_port_context" and "end_port_context" objects
                        if fk in ["start_port", "end_port",
                                  "start_port_context", "end_port_context"]:
                            orb.log.debug('      invalid Flow instance:')
                            oid = d['oid']
                            orb.log.debug(f'      - oid: "{oid}"')
                            orb.log.debug('        is missing start_port,')
                            orb.log.debug('        end_port,')
                            orb.log.debug('        start_port_context,')
                            orb.log.debug('        or end_port_context;')
                            orb.log.debug('        will be ignored.')
                            ignores.append(oid)
            cls = orb.classes[cname]
            if d['oid'] in updates and d['oid'] not in ignores:
                # orb.log.debug('* updating object with oid "{}"'.format(
                                                             # d['oid']))
                obj = updates[d['oid']]
                for a, val in kw.items():
                    setattr(obj, a, val)
                objs.append(obj)
                if cname == 'Acu':
                    refresh_componentz_required = True
                if cname == 'ProjectSystemUsage':
                    refresh_systemz_required = True
                if cname in ['Acu', 'ProjectSystemUsage', 'Requirement']:
                    recompute_parmz_required = True
                elif cname == 'ParameterDefinition':
                    update_parm_defz(obj)
                    update_parmz_by_dimz(obj)
                elif cname == 'DataElementDefinition':
                    update_de_defz(obj)
                orb.log.debug('* updated object: [{}] {}'.format(cname,
                                                      obj.id or '(no id)'))
            elif d['oid'] not in ignores:
                # orb.log.debug('* creating new object ...')
                # don't use inverse or M2M attrs in class initializations
                kwargs = {k:kw[k] for k in kw if k not in one2m_or_m2m}
                # orb.log.debug('  kwargs: {}'.format(str(list(kwargs))))
                obj = cls(**kwargs)
                if obj:
                    obj_id = obj.id or '(no id)'
                    msg = f'* new object: [{cname}] {obj_id}'
                    orb.log.debug(msg)
                    # NOTE: this was a progress method that didn't work
                    # i += 1
                    # dispatcher.send(signal='deserialized object',
                                    # msg=msg, n=new_len, i=i)
                    orb.db.add(obj)
                    objs.append(obj)
                    created.append(obj.id)
                    current_oids.append(obj.oid)
                    if dictify:
                        output['new'].append(obj)
                    if cname == 'Acu':
                        acus.add(obj)
                        refresh_componentz_required = True
                    elif cname in ['ProjectSystemUsage']:
                        refresh_systemz_required = True
                        psus.add(obj)
                    elif isinstance(obj, orb.classes['Product']):
                        products.append(obj)
                    elif cname == 'Requirement':
                        requirements.append(obj)
                    if cname in ['Acu', 'ProjectSystemUsage', 'Requirement']:
                        recompute_parmz_required = True
                # else:
                    # orb.log.debug('  object creation failed for kwargs:')
                    # orb.log.debug('  {}'.format(str(kwargs)))
            if refresh_componentz_required:
                if getattr(obj, 'assembly', None):
                    refresh_componentz(obj.assembly)
                    refresh_componentz_required = False
            if refresh_systemz_required:
                if getattr(obj, 'project', None):
                    refresh_systemz(obj.project)
                    refresh_systemz_required = False
    orb.db.commit()
    # log_txt = '* deserializer:'
    # if created:
        # orb.log.info('{} new object(s) deserialized: {}'.format(
                                                        # log_txt, str(created)))
    # if updates:
        # ids = str([o.id for o in updates.values()])
        # orb.log.info('{} updated object(s) deserialized: {}'.format(
                                                        # log_txt, ids))
    for product in products:
        acus.update(product.where_used)
        psus.update(product.projects_using_system)
    for acu in acus:
        # look for requirement allocations to acus ...
        if acu.allocated_requirements:
            req_oids.update([r.oid for r in acu.allocated_requirements])
    for psu in psus:
        # look for requirement allocations to psus ...
        if psu.allocated_requirements:
            req_oids.update([r.oid for r in psu.allocated_requirements])
    if recompute_parmz_required and not force_no_recompute:
        # orb.log.debug('  - deserialize recomputing parameters ...')
        orb.recompute_parmz()
        # orb.log.debug('    done.')
    for req in requirements:
        # if there are any Requirement objects, refresh the req_allocz cache
        refresh_req_allocz(req)
    if dictify:
        return output
    else:
        return objs

