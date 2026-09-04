# -*- coding: utf-8 -*-
"""
Serializers / deserializers for pangalactic domain objects and parameters.
"""
from datetime import date, datetime

# python-dateutil
import dateutil.parser as dtparser

# dispatcher (Louie)
from pydispatch import dispatcher

from pangalactic.core.meta import asciify, M2M, ONE2M
from pangalactic.core.refdata     import ref_oids
from pangalactic.core.utils.datetimes import earlier, EPOCH, EPOCH_DATE
from pangalactic.core.parametrics import (add_default_parameters,
                                          add_default_data_elements,
                                          deserialize_des,
                                          deserialize_parms,
                                          recompute_parmz,
                                          refresh_componentz,
                                          refresh_systemz,
                                          refresh_rqt_allocz,
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


def serialize(orb, objs, include_components=False, include_models=False,
              include_sub_activities=False, include_refdata=False,
              include_inverse_attrs=False, _seen=None):
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
        include_models (bool):  [default: False] if True, a Product's Models
            and DocumentReferences are included -- and, by way of the Model
            case below, each Model's RepresentationFiles.

            Off by default because this is not wanted in every direction:  a
            client saving a product to the repository has no reason to send
            the models back with it, and an export would grow a copy of every
            file record.  The server turns it on when *sending* a product to
            a client, where the opposite is true (see below).

        include_refdata (bool):  [default: False] if True, serialize
            reference data -- in general, it is not necessary to include
            reference data, since it is known to both client and server; it is
            only desirable to include reference data when data is to be
            exchanged with an external application, in which case a standard
            data exchange format would be preferable.

        _seen (frozenset):  **internal.**  The oids already being serialized
            on the way down to this call, used only to break the one cycle
            in the "always include" rules:  a Model carries its
            RepresentationFiles and a RepresentationFile carries its Model,
            which are the two directions of the same relationship.  It
            accumulates along a single descent and is never shared between
            branches, so it is a recursion guard and not a deduplication --
            objects reached by two different routes are still serialized
            twice and reconciled by oid at the end, which is what lets the
            richer serialization of an object win over a plainer one.

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
    _seen = _seen if _seen is not None else frozenset()
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
            # include_models carries down:  a component's model is as much
            # part of what the client should hold as the assembly's own, and
            # for a STEP assembly it is where the component's geometry is
            scomps = serialize(orb, [acu.component
                                     for acu in obj.components],
                               include_models=include_models)
            serialized += scomps
        # 'include_sub_activities' only applies to Activities ... and only
        # "direct sub_activities" will be included (not recursive)
        if include_sub_activities and getattr(obj, 'sub_activities', None):
            ser_acts = serialize(orb, obj.sub_activities)
            serialized += ser_acts
        ###################################################################
        # NOTE:  Ports and Flows need to be part of a "product definition"
        # abstraction -- i.e., the "white box" model of the product
        # TODO:  implement "white box" vs. "black box" serializations and,
        # more broadly, white/black box Product objects!  Maybe use a new
        # 'product_definition' attribute that can be white or black box ...
        if isinstance(obj, orb.classes['Product']):
            # ---------------------------------------------------------------
            # + Models and RepresentationFiles are not included by *default*,
            #   because a client saving a product has no reason to send them
            #   back and an export would grow a copy of every file record.
            #
            #   They ARE included when the caller asks, and the server asks
            #   whenever it sends a product to a client.  A product whose
            #   model is a STEP assembly is *incomplete* without that model
            #   and its files -- there is nothing to render and nothing to
            #   compute mass properties from -- and PGEF's master-model
            #   paradigm says the client should hold everything the server
            #   knows about a product (author, 2026-08-25).
            #
            #   The earlier note here gave differing "owners" and access
            #   controls as the reason for withholding them.  That concern is
            #   answered structurally rather than by withholding:  a
            #   project-owned object can only be built from objects that are
            #   public or owned by that project, so a requester entitled to
            #   the product is entitled to what it is made of (author).
            # ---------------------------------------------------------------
            if include_models:
                if getattr(obj, 'has_models', None):
                    serialized += serialize(orb, obj.has_models)
                if getattr(obj, 'doc_references', None):
                    serialized += serialize(orb, obj.doc_references)
            # + ALWAYS include ports (white box)
            if obj.ports:
                s_ports = serialize(orb, obj.ports)
                serialized += s_ports
            # + ALWAYS include flows (white box)
            #   NOTE: technically any ManagedObject can be a flow_context but
            #   as a practical matter, only Products are currently supported
            flows = orb.get_internal_flows_of(obj)
            if flows:
                s_flows = serialize(orb, flows)
                serialized += s_flows
        ###################################################################
        if isinstance(obj, orb.classes['Model']):
            # + ALWAYS include related RepresentationFile instances
            #   (skipping any this descent is already inside of -- see the
            #   RepresentationFile case below, which is the other direction
            #   of this same relationship)
            files = [f for f in (obj.has_files or []) if f.oid not in _seen]
            if files:
                s_rfiles = serialize(orb, files, _seen=_seen | {obj.oid})
                serialized += s_rfiles
        ###################################################################
        if isinstance(obj, orb.classes['RepresentationFile']):
            # + ALWAYS include the object the file represents.
            #
            # Every other reference an object cannot exist without is
            # carried with it -- an Acu brings its assembly and component, a
            # RoleAssignment its role, person and context, a Model its files
            # -- so that a batch can be deserialized on its own:
            # DESERIALIZATION_ORDER puts the classes in dependency order, and
            # that is worth nothing if the object depended on is not in the
            # set.  This one relationship was carried downward (Model ->
            # has_files) and never upward, so a RepresentationFile
            # serialized by itself named a Model that was not there.
            #
            # It is not hypothetical:  a "modified object" signal serializes
            # the one object it is given, and one sent for a newly imported
            # STEP file reached the repository with no Model in the batch.
            # The file was stored with of_object = None -- a file nothing
            # cloaks and nobody may fetch ("download not authorized",
            # 2026-09-03).  REQUIRED_REFS now refuses to build that object;
            # this makes it unnecessary to, by making the batch complete.
            #
            # "_seen" is what keeps this from recurring forever against the
            # Model case above:  the Model that sent us here is in it.
            subject = getattr(obj, 'of_object', None)
            if subject is not None and subject.oid not in _seen:
                serialized += serialize(orb, [subject],
                                        _seen=_seen | {obj.oid})
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
                    'Document',
                    'DocumentReference',
                    'Acu',
                    'Axis2Placement3D',
                    # ContextDependentShapeRepresentation references both Acu
                    # and Axis2Placement3D, so it must follow both
                    'ContextDependentShapeRepresentation',
                    'ProjectSystemUsage',
                    'Mission',
                    'Activity', # Activity references Acu, PSU, and Mission
                    'Model',
                    'Port',
                    'Flow',
                    'RepresentationFile',
                    'Requirement'
                    ]


# REQUIRED_REFS:  object-valued attributes without which an instance of the
# class is not a thing.  A RepresentationFile with no "of_object" is the
# example that prompted this list:  its whole purpose is to connect a file to
# the object it represents, so one without that connection is not a degraded
# RepresentationFile, it is not a RepresentationFile at all -- nothing can
# say who may fetch it (access.may_fetch_file), what cloaks it
# (access.is_cloaked), or which project owns it (access.get_owner_id),
# because every one of those questions is answered by "of_object".
#
# **The deserializer is the only thing that ever made one.**  Nothing in the
# application does:  the three creation sites (digital_files.py) all pass
# "of_object", and there is nowhere else to make one.  But deserialize()
# builds every class the same way -- cls(**kwargs) -- and an object-valued
# attribute whose target was not in the database yet simply became None.
#
# Refusing them here is not new;  it is what the deserializer already did
# for a Port with no of_product, a Flow with no ports, an Acu with no
# assembly or component and a PSU with no project or system.  That was an
# if-chain of special cases which (a) omitted RepresentationFile, (b) fired
# only when the attribute was *absent* from the serialization and not when
# it named an object that could not be found -- which is the case that
# actually occurs, and the one that produced the null -- and (c) had a
# precedence bug: "if ((fk == 'assembly') or (fk == 'component') and cname
# == 'Acu')" binds as "or (... and ...)", so any class with an "assembly"
# attribute took the Acu branch.  Declaring the invariant instead of coding
# it four times fixes all three.
#
# Keyed on the exact class name, not by isinstance:  "of_product" is
# required for a Port and NOT for a PortTemplate, which is a Port subclass.
# PortTemplate is the only subclass any of these classes has.
#
# NOTE: this belongs in the ontology, as a cardinality restriction on the
# property.  It cannot live there yet:  meta.property_to_field() documents a
# "null" key in its docstring and never sets one, and registry.py builds
# every foreign key as a bare Column(ForeignKey(...)), so "required" is not
# expressible in the schema or enforceable in the database.  Until it is,
# this is the one place that knows.
REQUIRED_REFS = {
    'Acu':                ('assembly', 'component'),
    'Flow':               ('start_port', 'end_port'),
    'Port':               ('of_product',),
    'ProjectSystemUsage': ('project', 'system'),
    'RepresentationFile': ('of_object',),
    }


def repair_null_fks(orb, obj, so, schema):
    """
    Fill in an existing object's object-valued attributes that are null and
    that this serialization can now resolve.

    An object already in the database is not necessarily *whole*.  A
    reference whose target had not arrived when the object was created was
    left null -- `deserialize()` remembers those in `deferred_fks` and tries
    again at the end of the batch, but a target that came in a *later*
    message is past the end of that batch, and nothing ever set it.  A
    RepresentationFile sent one message ahead of its Model is the case this
    was written for:  it was stored with no `of_object`, which makes it a
    file that nobody may fetch (`access.may_fetch_file`) and that nothing
    cloaks (`access.is_cloaked`).

    The repair is deliberately one-directional:  **only attributes that are
    still null are set.**  This runs on objects the deserializer is
    otherwise ignoring, whose incoming mod_datetime is no later than the one
    held -- so the serialization is not authority for anything, and the one
    thing it can safely do is supply a link that is missing altogether.
    Overwriting a link that exists would let a stale copy of an object
    re-point a reference that someone else has since changed.

    Args:
        orb (UberORB):  the (singleton) `orb` instance
        obj (Identifiable):  the object in the database
        so (dict):  its serialization, as received
        schema (dict):  the schema of its class

    Returns:
        list of str:  names of the attributes that were set
    """
    repaired = []
    one2m_or_m2m = list(ONE2M) + list(M2M)
    for name, field in schema['fields'].items():
        if (field['is_inverse'] or name in one2m_or_m2m
            or field.get('range') not in orb.classes):
            continue
        if not so.get(name) or getattr(obj, name, None) is not None:
            continue
        target = orb.get(so[name])
        if target is not None:
            setattr(obj, name, target)
            repaired.append(name)
    return repaired


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
        (3) An object missing a reference it cannot exist without is not
            deserialized at all -- see REQUIRED_REFS.  A reference that is
            not required and cannot be resolved is left unset and retried
            when the batch is done (deferred_fks), or when the object is
            sent again (repair_null_fks).
    """
    # orb.log.debug('* deserializing ...')
    if not serialized:
        # orb.log.debug('  no objects provided -- returning []')
        return []
    # SCW 2017-08-24  Deserializer ignores objects that don't have an oid!
    # input_len = len(serialized)
    serialized = [so for so in serialized if so and so.get('oid')]
    new_len = len(serialized)
    if new_len == 0:
        # orb.log.debug('  all objects were empty -- returning []')
        return []
    one2m_or_m2m = list(ONE2M) + list(M2M)
    recompute_parmz_required = False
    refresh_componentz_required = False
    refresh_systemz_required = False
    rqt_oids = set()
    acus = set()
    psus = set()
    # objs: list of all deserialized objects
    objs = []
    # hwproducts: list of deserialized objects that are instances of
    # HardwareProduct
    # subclasses
    hwproducts = []
    # requirements: list of deserialized objects that are Requirement instances
    requirements = []
    # deferred_fks: (oid, attribute, target oid) for object-valued attributes
    # whose target was not in the database when the object was created.  Set
    # after the batch, when it may well be.
    deferred_fks = []
    # act_to_sao: mapping of Activity oids to oids of their "sub_activity_of"
    # ... needed in case Activity instances get deserialized before their
    # "sub_activity_of" has been deserialized.
    act_to_sao = {}
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
        if so['_cname'] == 'Activity':
            act_to_sao[so['oid']] = so.get('sub_activity_of', '')
    # if act_to_sao:
        # n = len(act_to_sao)
        # orb.log.debug(f'* deser: {n} activities with parents found.')
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
                so_dt_str = d.get('mod_datetime')
                so_datetime = uncook_datetime(so_dt_str)
                if force_update and db_obj:
                    # orb.log.debug('    forcing update ... ')
                    updates[oid] = db_obj
                    orb.db.add(db_obj)
                    if dictify:
                        output['modified'].append(db_obj)
                elif not (so_datetime and db_obj and
                          earlier(db_obj.mod_datetime, so_datetime)):
                    # ridiculously verbose debug logging! (was for earlier())
                    # orb.log.debug(f'    serialized object with oid "{oid}"')
                    # orb.log.debug(f'    has mod_datetime "{so_dt_str}"')
                    # orb.log.debug('    but existing object')
                    # obj_dts = str(db_obj.mod_datetime)
                    # orb.log.debug(f'    has mod_datetime "{obj_dts}"')
                    # orb.log.debug('    so ignoring submitted object.')
                    # if not, ignore it
                    ignores.append(oid)
                    # NOTE: do not return "ignored" objs SCW 2019-09-05
                    # objs.append(db_obj)
                    if dictify:
                        output['unmodified'].append(db_obj)
                    # "unmodified" is not the same as "complete":  a link
                    # whose target had not arrived when this object was
                    # created is still null, and the deferred pass below
                    # only reaches the end of the batch that created it.
                    # The serialization naming that target is in hand right
                    # now, so fill in what is still missing -- and only what
                    # is still missing.  See repair_null_fks().
                    if db_obj is not None:
                        repaired = repair_null_fks(orb, db_obj, d, schema)
                        if repaired:
                            obj_id = getattr(db_obj, 'id', '') or oid
                            orb.log.debug(f'* deser: "{obj_id}" was missing '
                                          f'{repaired}; set from the '
                                          'serialization received.')
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
                        and (schema['fields'][a].get('range')
                             in orb.classes))]
            required = REQUIRED_REFS.get(cname, ())
            if fks:
                # orb.log.debug(f'    fk fields found: {fks}')
                for fk in fks:
                    # get the related object by its oid (i.e. d[fk])
                    # orb.log.debug('    * rel obj oid: "{}"'.format(
                                   # d.get(fk)))
                    target = orb.get(d[fk]) if d.get(fk) else None
                    if target is not None:
                        # orb.log.debug('      rel obj found.')
                        kw[fk] = target
                    elif fk in required:
                        # The object cannot exist without this, so it is not
                        # created (or, if it is an update, not applied).  Two
                        # ways to get here and both are refused:  the
                        # attribute was not sent at all, or it named an
                        # object that is not here.
                        #
                        # The second is what happened to a RepresentationFile
                        # sent one vger.save() ahead of its Model:  the
                        # attribute was there and named the Model correctly,
                        # the Model just had not arrived, so the file was
                        # created with of_object = None and nothing ever
                        # repaired it -- a file record that nothing cloaked
                        # and nobody could fetch, "download not authorized"
                        # to its own project (observed 2026-09-03).
                        #
                        # Refusing it is what makes that self-correcting.
                        # The repository does not report a refused object in
                        # "new_obj_dts", so the client leaves it in
                        # "locally_created_oids" and sends it again at the
                        # next sync -- by which time its Model is here.  A
                        # client refusing one off the pubsub gets it from
                        # the next sync of the project, with its Model.
                        # Half an object, stored, corrects itself never.
                        named = d.get(fk)
                        why = (f'"{fk}" names "{named}", which is not here'
                               if named else f'no "{fk}"')
                        obj_id = d.get('id') or '[no id]'
                        orb.log.debug(f'      invalid {cname} instance:')
                        orb.log.debug(f'      - oid: "{oid}"')
                        orb.log.debug(f'        id:  "{obj_id}"')
                        orb.log.debug(f'        {why};')
                        orb.log.debug('        will be ignored.')
                        if oid not in ignores:
                            ignores.append(oid)
                    elif d.get(fk):
                        # The named object is not here *yet*.  It may be
                        # later in this very batch:  DESERIALIZATION_ORDER
                        # orders the classes but not the objects within a
                        # class, so a self-referential attribute --
                        # RepresentationFile.component_file_of, for one --
                        # is decided by which of the two happens to come
                        # first in the list.
                        #
                        # Setting it to None here and moving on loses the
                        # link silently.  That is what emptied
                        # "component_files" on a client syncing an
                        # imported STEP assembly:  with no component
                        # files, nothing staged the set under the names
                        # its references use, and only the files that
                        # happened to already sit in the vault under
                        # plain names resolved (author, 2026-08-26).
                        #
                        # So remember it and try again when the batch is
                        # done.  This is the general form of the
                        # "act_to_sao" pass below, which does the same
                        # thing for one attribute of one class.
                        #
                        # "kw" is left without the key rather than carrying
                        # None:  on an update, every key in "kw" is
                        # setattr()ed, so a None here would erase a link
                        # that is currently right because the object naming
                        # it happens to be unknown to this database.
                        deferred_fks.append((oid, fk, d[fk]))
            # else:
                # orb.log.debug('    no fk fields found.')
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
                    elif isinstance(obj, orb.classes['HardwareProduct']):
                        hwproducts.append(obj)
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
    all_proj_ids = orb.get_ids(cname='Project')
    for hwproduct in hwproducts:
        acus.update(hwproduct.where_used)
        psus.update(hwproduct.projects_using_system)
        ptid = getattr(hwproduct.product_type, 'id', None)
        add_default_parameters(hwproduct.oid, cname='HardwareProduct',
                               ptid=ptid)
        add_default_data_elements(hwproduct.oid, cname='HardwareProduct',
                               ptid=ptid)
        # fix hwproduct id's to conform to new format (as of 3.2.dev9)
        orb.fix_hwproduct_id(hwproduct, all_proj_ids)
    for acu in acus:
        # look for requirement allocations to acus ...
        if acu.allocated_requirements:
            rqt_oids.update([r.oid for r in acu.allocated_requirements])
    for psu in psus:
        # look for requirement allocations to psus ...
        if psu.allocated_requirements:
            rqt_oids.update([r.oid for r in psu.allocated_requirements])
    if recompute_parmz_required and not force_no_recompute:
        # orb.log.debug('  - deserialize recomputing parameters ...')
        recompute_parmz()
        # orb.log.debug('    done.')
    for req in requirements:
        # if there are any Requirement objects, refresh the rqt_allocz cache
        refresh_rqt_allocz(req)
    # NOTE: an empty sao_oid is normal -- it means a top-level Activity, which
    # has no parent.  A *non-empty* sao_oid that cannot be resolved is not
    # normal:  sub-activities are only ever created in the ConOps / timeline
    # modeler, in the context of their parent, and are never re-parented (see
    # NOTES_ON_ACTIVITIES.md), so the parent is always created before the child
    # and always travels with it.  If it is missing, the data is incomplete --
    # so collect those and report them rather than dropping them silently.
    # Set the links whose targets were missing when their objects were made.
    # Ordered before the act_to_sao pass so that it sees the result:  an
    # Activity's parent may equally have been later in the batch, and there
    # is no reason for the two passes to disagree.
    if deferred_fks:
        resolved = 0
        for obj_oid, fk, target_oid in deferred_fks:
            obj = orb.get(obj_oid)
            target = orb.get(target_oid)
            if obj is None or target is None:
                continue
            if getattr(obj, fk, None) is None:
                setattr(obj, fk, target)
                resolved += 1
        if resolved:
            orb.db.commit()
            n = len(deferred_fks)
            orb.log.debug(f'* deser: {resolved} of {n} deferred reference(s) '
                          'resolved after the batch.')
    orphans = []
    for act_oid, sao_oid in act_to_sao.items():
        if not sao_oid:
            continue
        act = orb.get(act_oid)
        sao = orb.get(sao_oid)
        if act and sao:
            if not act.sub_activity_of:
                # orb.log.debug(f'  deser: setting parent {sao.name} for '
                              # f'{act.name}')
                act.sub_activity_of = sao
                orb.db.commit()
        elif act and not sao:
            orphans.append(act)
    if orphans:
        names = [(getattr(a, 'name', '') or a.oid) for a in orphans]
        orb.log.debug(f'* deser: {len(orphans)} activities have a parent that '
                      f'could not be found: {names}')
        dispatcher.send(signal='unresolved activity parents',
                        activities=orphans)
    if dictify:
        return output
    else:
        return objs

