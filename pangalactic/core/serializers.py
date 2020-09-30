# -*- coding: utf-8 -*-
"""
Serializers / deserializers for pangalactic domain objects and parameters.
"""
# SQLAlchemy
from sqlalchemy import ForeignKey

# PanGalactic
from pangalactic.core.refdata     import ref_oids
from pangalactic.core.utils.meta  import cookers, uncookers, uncook_datetime
from pangalactic.core.utils.datetimes  import earlier
from pangalactic.core.parametrics import (add_parameter,
                                          deserialize_des,
                                          deserialize_parms,
                                          parameterz,
                                          refresh_componentz,
                                          refresh_req_allocz,
                                          serialize_des, serialize_parms,
                                          update_de_defz, update_parm_defz,
                                          update_parmz_by_dimz)


def serialize(orb, objs, view=None, include_components=False,
              include_refdata=False, include_inverse_attrs=False):
    """
    Args:
        orb (UberORB): the (singleton) `orb` instance
        objs (iterable of objects):  the objects to be serialized.

    Keyword Args:
        view (iterable):  an iterable containing the names of the fields to
            be included; if None, all populated fields are included.
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

    The serialization has the following form (where the 'parameters'
    attribute is a special case to enable the object's parameter-objects to
    be deserialized along with the object):

        {'_cname'      : [class name for the object],
         field-1-name  : [field-1-value],
         field-2-name  : [field-2-value],
         ...           
         'parameters'  : serialized parameters dictionary
         }

    If an object has parameters in parms, their dictionary (the value of
    parameterz[obj.oid]) is serialized and assigned to the serialized
    object as the 'parameters' key.
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
            elif schema['fields'][name]['field_type'] is ForeignKey:
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
                    'ProductType',
                    'Mission',
                    'ActivityType',
                    'Activity',
                    'Product',
                    'Template',
                    'HardwareProduct',
                    'SoftwareProduct',
                    'DigitalProduct',
                    'Acu',
                    'ProjectSystemUsage',
                    'Model',
                    'Port',
                    'Flow',
                    'Representation',
                    'RepresentationFile',
                    'Requirement'
                    ]

def deserialize(orb, serialized, include_refdata=False, dictify=False,
                force_no_recompute=False):
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

    recompute_parmz_required = False
    refresh_componentz_required = False
    req_oids = set()
    acus = set()
    psus = set()
    objs = []
    products = []
    created = []
    updates = {}
    ignores = []
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
    incoming_oids = [so['oid'] for so in serialized]
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
    ports_and_flows_to_be_deleted = []
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
            if oid in current_oids:
                # orb.log.debug('  - object exists in db ...')
                # the serialized object exists in the db
                db_obj = orb.get(oid)
                # check against db object's mod_datetime
                so_datetime = uncook_datetime(d.get('mod_datetime'))
                if not (so_datetime and
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
                    updates[oid] = db_obj
                    orb.db.add(db_obj)
                    if dictify:
                        output['modified'].append(db_obj)
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
                # orb.log.debug('  + no parameters found for this object.')
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
                    # else:
                        # orb.log.debug('      rel obj NOT found.')
            cls = orb.classes[cname]
            if d['oid'] in updates:
                # orb.log.debug('* updating object with oid "{}"'.format(
                                                             # d['oid']))
                obj = updates[d['oid']]
                for a, val in kw.items():
                    setattr(obj, a, val)
                objs.append(obj)
                if cname == 'Acu':
                    refresh_componentz_required = True
                if cname in ['Acu', 'ProjectSystemUsage', 'Requirement']:
                    recompute_parmz_required = True
                elif issubclass(cls, orb.classes['Product']):
                    # NOTE:  the following assumes "white box" Product, which
                    # includes the internals: ports, flows, components.
                    # Removed components are covered by deleted Acus; ports and
                    # flows are handled here ...
                    for port in obj.ports:
                        if port.oid not in incoming_oids:
                            ports_and_flows_to_be_deleted.append(port)
                    flows = orb.get_internal_flows_of(obj)
                    if flows:
                        for flow in flows:
                            if flow.oid not in incoming_oids:
                                ports_and_flows_to_be_deleted.append(flow)
                    recompute_parmz_required = True
                elif cname == 'ParameterDefinition':
                    update_parm_defz(orb, obj)
                    update_parmz_by_dimz(orb, obj)
                elif cname == 'DataElementDefinition':
                    update_de_defz(orb, obj)
                orb.log.debug('* updated object: [{}] {}'.format(cname,
                                                          obj.id or '(no id)'))
            elif d['oid'] not in ignores:
                # orb.log.debug('* creating new object ...')
                obj = cls(**kw)
                if obj:
                    orb.log.debug('* new object: [{}] {}'.format(cname,
                                                          obj.id or '(no id)'))
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
                        psus.add(obj)
                    elif isinstance(obj, orb.classes['Product']):
                        products.append(obj)
                        if cname == 'HardwareProduct':
                            # make sure HW Products have mass, power, data rate
                            if obj.oid not in parameterz:
                                parameterz[obj.oid] = {}
                            for pid in ['m', 'P', 'R_D']:
                                if not parameterz[obj.oid].get(pid):
                                     add_parameter(obj.oid, pid)
                    if cname in ['Acu', 'ProjectSystemUsage', 'Requirement']:
                        recompute_parmz_required = True
                else:
                    orb.log.debug('  object creation failed for kw dict:')
                    orb.log.debug('  {}'.format(str(kw)))
            if refresh_componentz_required:
                if getattr(obj, 'assembly', None):
                    refresh_componentz(obj.assembly)
                    refresh_componentz_required = False
    orb.db.commit()
    if ports_and_flows_to_be_deleted:
        orb.log.debug('  need to delete some ports and flows ...')
        for obj in ports_and_flows_to_be_deleted:
            orb.db.delete(obj)
        orb.db.commit()
        orb.log.debug('  ports and flows deleted.')
    # log_txt = '* deserializer:'
    # if created:
        # orb.log.info('{} new object(s) deserialized: {}'.format(
                                                        # log_txt, str(created)))
    # if updates:
        # ids = str([o.id for o in updates.values()])
        # orb.log.info('{} updated object(s) deserialized: {}'.format(
                                                        # log_txt, ids))
    # if there are any Requirement objects or Product, Acu, PSU with allocated
    # requirements, refresh the req_allocz cache for the relevant requirements
    for product in products:
        acus.update(product.where_used)
        psus.update(product.projects_using_system)
    for acu in acus:
        # look for requirement allocations to acus ...
        if acu.allocated_requirements:
            req_oids.update([r.oid for r in acu.allocated_requirements])
    for psu in psus:
        # look for requirement allocations to psus ...
        if psu.system_requirements:
            req_oids.update([r.oid for r in psu.system_requirements])
    if req_oids:
        orb.log.debug('  - relevant req oids: {}'.format(str(req_oids)))
        orb.log.debug('    req_allocz is being refreshed ...')
        for req_oid in req_oids:
            req = orb.get(req_oid)
            refresh_req_allocz(req)
        orb.log.debug('    done.')
        # orb.log.debug('  - recomputing parameters ...')
        recompute_parmz_required = True
        # orb.log.debug('    done.')
    if recompute_parmz_required and not force_no_recompute:
        orb.log.debug('  - deserialize recomputing parameters ...')
        orb.recompute_parmz()
        # orb.log.debug('    done.')
    if dictify:
        return output
    else:
        return objs

