# -*- coding: utf-8 -*-
"""
Serializers / deserializers for pangalactic domain objects and parameters.
"""
# pangalactic

from pangalactic.core.parametrics  import (Comp, System,
                                           serialize_des, serialize_parms,
                                           componentz, systemz)
from pangalactic.core.refdata      import ref_oids
from pangalactic.core.tachistry    import matrix, schemas


def serialize(orb, objs, include_components=False,
              include_sub_activities=False, include_refdata=False,
              include_inverse_attrs=False):
    """
    Args:
        orb (Tachyorb): the (singleton) `orb` instance
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
    objs = [obj for obj in objs if obj is not None]
    if not objs:
        return []
    serialized = []
    for obj in objs:
        d = {}
        cname = obj.__class__.__name__
        d['_cname'] = cname
        d.update(matrix[obj.oid])
        if not obj:
            # orb.log.debug('  - null object "{}"'.format(obj))
            # don't include the null object in serialized
            continue
        if cname in orb.get_subclass_names('Modelable'):
            # serialize data elements
            d['data_elements'] = serialize_des(obj.oid)
            # serialize parameters
            d['parameters'] = serialize_parms(obj.oid)
        serialized.append(d)
        if getattr(obj, 'component', None):
            # Acu:  always include both assembly and component ...
            serialized += serialize(orb, [obj.assembly, obj.component])
        elif getattr(obj, 'system', None):
            # PSU:  always include `system`; `project` should be present
            serialized += serialize(orb, [obj.system])
        # 'include_components' only applies to Products ... and only
        # "direct components" will be included (not entire assemblies)
        if include_components and obj.oid in componentz:
            acus = [orb.get(comp.usage_oid) for comp in componentz[obj.oid]]
            sacus = serialize(orb, acus)
            serialized += sacus
            scomps = serialize(orb, [acu.component for acu in acus])
            serialized += scomps
        # 'include_sub_activities' only applies to Activities ... and only
        # "direct sub_activities" will be included (not recursive)
        # *********************************************************************
        # TODO:  create an "activitiez" cache and use that, not .sub_activities
        # if include_sub_activities and getattr(obj, 'sub_activities', None):
            # ser_acrs = serialize(orb, obj.sub_activities)
            # serialized += ser_acrs
            # ser_acts = serialize(orb, [acr.sub_activity
                                       # for acr in obj.sub_activities])
            # serialized += ser_acts
        # *********************************************************************
        ###################################################################
        # NOTE:  Ports and Flows need to be part of a "product definition"
        # abstraction -- i.e., the "white box" model of the product
        # TODO:  implement "white box" vs. "black box" serializations and,
        # more broadly, white/black box Product objects!  Maybe use a new
        # 'product_definition' attribute that can be white or black box ...
        if cname in orb.get_subclass_names('Product'):
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
        if cname == 'RoleAssignment':
            # include Role object
            serialized += serialize(orb, [obj.assigned_role])
            # include Person object
            serialized += serialize(orb, [obj.assigned_to])
            # include Organization object, if any
            serialized += serialize(orb, [obj.role_assignment_context])
        if cname == 'Requirement':
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

# ****************************************************************************
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
                    'Activity',  # Activity.activity_of references Products
                    'Mission',
                    'ActCompRel',
                    'Acu',
                    'ProjectSystemUsage',
                    'Model',
                    'Port',
                    'Flow',
                    'Representation',
                    'RepresentationFile',
                    'Requirement'
                    ]

def deserialize(orb, serialized, include_refdata=False,
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
        force_no_recompute (bool): do not recompute parameters
        force_update (bool): force updates of all objects, even if the
            mod_datetime is later than the deserialized data -- this is only
            used with the "force full re-sync" option on the client.  It will
            be ignored for now ...

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
    orb.log.debug('* deserialize()')
    if not serialized:
        # orb.log.debug('  no objects provided -- returning []')
        return []
    pgef_cnames = list(schemas)
    valid_sos = [so for so in serialized
                 if so and so.get('oid') and so.get('_cname')
                 and so['_cname'] in pgef_cnames]
    if not include_refdata:
        valid_sos = [so for so in valid_sos
                     if not so.get('oid', '') in ref_oids]
    new_len = len(valid_sos)
    if new_len == 0:
        orb.log.debug('  all objects were invalid -- returning []')
        return []
    else:
        orb.log.debug(f'* deserializing {new_len} object(s) ...')
    objs = []
    loadable = {}
    loadable['other'] = []
    for so in valid_sos:
        _cname = so['_cname']
        orb.log.debug(f'  - {_cname}')
        if _cname in DESERIALIZATION_ORDER:
            if _cname in loadable:
                loadable[_cname].append(so)
            else:
                loadable[_cname] = [so]
        else:
            loadable['other'].append(so)
    order = [c for c in DESERIALIZATION_ORDER if c in loadable]
    order.append('other')
    for group in order:
        for so in loadable[group]:
            _cname = so.pop('_cname')
            # [0] special case for ProjectSystemUsage
            if _cname == 'ProjectSystemUsage':
                if orb.get(so.get('project')) and orb.get(so.get('system')):
                    # we have the associated project and system
                    objs.append(orb.create_or_update_thing(_cname, **so))
                    # do a temp update to systemz, pending a full refresh
                    s = System(so['system'], so['oid'],
                               so.get('system_role', 'system'))
                    orb.log.debug('  - System:')
                    orb.log.debug(f'      oid: {s.oid}')
                    orb.log.debug(f'      usage_oid: {s.usage_oid}')
                    orb.log.debug(f'      system_role: {s.system_role}')
                    if systemz.get(so['project']):
                        systemz[so['project']].append(s)
                    else:
                        systemz[so['project']] = [s]
                else:
                    # ignore if we don't have both the project and the system
                    continue
            # [1] special case for Acu
            elif _cname == 'Acu':
                if (orb.get(so.get('assembly'))
                    and orb.get(so.get('component'))):
                    # we have the associated assembly and component
                    objs.append(orb.create_or_update_thing(_cname, **so))
                    # do a temp update to componentz, pending a full refresh
                    c = Comp(so['component'], so['oid'],
                             so.get('quantity', 1),
                             so.get('reference_designator', 'no_ref_des'))
                    orb.log.debug('  - Comp:')
                    orb.log.debug(f'      oid: {c.oid}')
                    orb.log.debug(f'      usage_oid: {c.usage_oid}')
                    orb.log.debug(f'      quantity: {c.quantity}')
                    orb.log.debug(f'      ref des: {c.reference_designator}')
                    if componentz.get(so['assembly']):
                        componentz[so['assembly']].append(c)
                    else:
                        componentz[so['assembly']] = [c]
                else:
                    # ignore if we don't have both the assembly and the
                    # component
                    continue
            # [2] non-special cases
            else:
                objs.append(orb.create_or_update_thing(_cname, **so))
    orb.save(objs)
    return objs

