# -*- coding: utf-8 -*-
"""
Serializers / deserializers for pangalactic domain objects and parameters.
"""
from builtins import str
from copy import deepcopy

# SQLAlchemy
from sqlalchemy import ForeignKey

# PanGalactic
from pangalactic.core.meta        import DESERIALIZATION_ORDER
from pangalactic.core.utils.meta  import (asciify, cookers, uncookers,
                                          cook_datetime, uncook_datetime)
from pangalactic.core.parametrics import parameterz, refresh_componentz


def serialize_parms(obj_parms):
    """
    Args:
        obj_parms (dict):  a dictionary containing the parameters
            associated with an object (for a given object `obj`, its
            parameters dictionary will be `parameterz[obj.oid]`).

    Serialize the dictionary of parameters associated with an object.
    Basically, this function is only required to serialize the
    `mod_datetime` value of each parameter -- the parameter's other values
    do not require special serialization.

    IMPLEMENTATION NOTE:  uses deepcopy() to avoid side-effects to the
    `parameterz` dict.
    """
    if obj_parms:
        ser_parms = deepcopy(obj_parms)
        for parm in list(ser_parms.values()):
            parm['mod_datetime'] = cook_datetime(parm['mod_datetime'])
        return ser_parms
    else:
        return {}

def serialize(orb, objs, view=None, include_components=False,
              include_inverse_attrs=False):
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
            **********************************************************
            *** NOTE that for Acus and PSUs, the following behavior is
            *NOT* dependent on `include_components`:
            * for Acus, assembly and component objects will always be
              included
            * for PSUs, system object will always be included
            **********************************************************

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
    orb.log.info('* serializing objects ...')
    if not objs:
        return []
    serialized = []
    person_objs = set()
    product_type_objs = set()
    for obj in objs:
        if not obj:
            orb.log.debug('  - null object "{}"'.format(obj))
            # don't include the null object in serialized
            # serialized.append(obj)
            continue
        orb.log.info('  - obj.id: {}'.format(obj.id))
        orb.log.debug('  - {}'.format(obj.id))
        cname = obj.__class__.__name__
        schema = orb.schemas[cname]
        d = {}
        d['_cname'] = cname
        # serialize parameters, if any
        obj_parms = parameterz.get(obj.oid, {})
        if obj_parms:
            # NOTE:  serialize_parms() uses deepcopy()
            d['parameters'] = serialize_parms(obj_parms)
            orb.log.info('  - parameters found, serialized.')
        else:
            orb.log.info('  - no parameters found.')
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
                            d[name] = [asciify(o.oid) for o in rel_objs]
                    else:
                        continue
                else:
                    d[name] = asciify(getattr(getattr(obj, name), 'oid'))
            else:
                datatype = schema['fields'][name]['range']
                d[name] = cookers[datatype](getattr(obj, name))
        serialized.append(d)
        if hasattr(obj, 'creator'):
            # for Modelables, creator and modifier must be included
            if obj.creator:
                person_objs.add(obj.creator)
            if obj.modifier:
                person_objs.add(obj.modifier)
        if hasattr(obj, 'product_type'):
            # for Products, product_type must be included
            if obj.product_type:
                product_type_objs.add(obj.product_type)
        elif hasattr(obj, 'product_type_hint'):
            # for Acus, product_type_hint must be included
            if obj.product_type_hint:
                product_type_objs.add(obj.product_type_hint)
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
        # be sure to include Ports!
        if hasattr(obj, 'ports'):
            if obj.ports:
                s_ports = serialize(orb, obj.ports)
                serialized += s_ports
        # ... and Flows (if including components)!
        if include_components and getattr(obj, 'components', None):
            flows = orb.get_internal_flows_of(obj)
            if flows:
                s_flows = serialize(orb, flows)
                serialized += s_flows
    if person_objs:
        orb.log.debug('  including {} Person objects.'.format(
                                                    len(person_objs)))
        serialized += serialize(orb, person_objs)
    if product_type_objs:
        orb.log.debug('  including {} ProductType objects.'.format(
                                                len(product_type_objs)))
        serialized += serialize(orb, product_type_objs)
    orb.log.info('  returning {} objects.'.format(len(serialized)))
    # make sure there is only 1 serialized object per oid ...
    so_by_oid = {so['oid'] : so for so in serialized}
    return list(so_by_oid.values())

def deserialize_parms(oid, ser_parms):
    """
    Deserialize a serialized object `parms` dictionary.

    Args:
        ser_parms (dict):  the serialized parms dictionary
    """
    for parm in list(ser_parms.values()):
        parm['mod_datetime'] = uncook_datetime(parm['mod_datetime'])
    parameterz[oid] = ser_parms

def deserialize(orb, serialized, include_refdata=False, dictify=False):
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
        (0) Check for 'oid'
            (b) if found and dts is later, update the object
            (c) if not found, generate a new oid
        (1) All datatype properties will be deserialized
        (2) Any included Parameters will be deserialized only if
            (a) is true and either (b) or (c) is true
            (a) they do not exist in the db
            (b) their 'definition' (ParameterDefinition) already exists in
                the database
            (c) their 'definition' (ParameterDefinition) is included in the
                the set of serialized objects (in which case it will have
                been deserialized first)
        (3) Other object properties will be deserialized only if
            (a) they are direct (not inverse) properties
            -- AND --
            (b) their values are either included in the collection of
                serialized objects or present in the database.
    """
    orb.log.info('* deserialize()')
    created = 0
    if not serialized:
        orb.log.info('  no objects provided -- returning []')
        return []
    input_len = len(serialized)
    # SCW 2017-08-24  Deserializer ignores objects that don't have an oid!
    serialized = [so for so in serialized if so and so.get('oid')]
    new_len = len(serialized)
    if new_len < input_len:
        orb.log.info('  {} empty objects removed.'.format(
                                                    input_len - new_len))
    if new_len == 0:
        orb.log.info('  all objects were empty -- returning []')
        return []
    recompute_parms_required = False
    refresh_componentz_required = False
    objs = []
    updates = {}
    ignores = []
    loadable = {}
    loadable['other'] = []
    if dictify:
        output = dict(new=[], modified=[], unmodified=[], error=[])
    if not include_refdata:
        # ignore reference data objects ('pgefobjects' namespace)
        serialized = [so for so in serialized
                  if not asciify(so.get('oid', '')).startswith('pgefobjects:')]
    if len(serialized) < new_len:
        orb.log.info('  {} ref data object(s) found, ignored.'.format(
                                               new_len - len(serialized)))
    current_oids = orb.get_oids()
    for so in serialized:
        so_cname = so.get('_cname')
        if not so_cname:
            # ignore objects without a '_cname'
            orb.log.debug('  object has no _cname, ignoring:')
            orb.log.debug('  {}'.format(so))
            continue
        if so_cname not in orb.classes:
            # ignore objects with '_cname' not in pangalactic classes
            orb.log.debug('  object _cname unrecognized, ignoring:')
            orb.log.debug('  {}'.format(so))
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
    orb.log.info('  deserializing objects ...')
    for group in order:
        for d in loadable[group]:
            cname = d.get('_cname', '')
            schema = orb.schemas[cname]
            field_names = schema['field_names']
            if not cname:
                raise TypeError('class name not specified')
            orb.log.debug('* deserializing serialized object:')
            orb.log.debug('  %s' % str(d))
            oid = str(d['oid'])
            # if oid:
            if oid in current_oids:
                orb.log.debug('  - object exists in db ...')
                # the serialized object exists in the db
                db_obj = orb.get(oid)
                # check against db object's mod_datetime
                so_datetime = uncook_datetime(d.get('mod_datetime'))
                if so_datetime and so_datetime > db_obj.mod_datetime:
                    orb.log.debug('    serialized obj has newer '
                                   'mod_datetime, saving it.')
                    # if it is newer, update the object
                    updates[oid] = db_obj
                    orb.db.add(db_obj)
                    if dictify:
                        output['modified'].append(db_obj)
                else:
                    orb.log.debug('    serialized obj has same or '
                                   'older mod_datetime, ignoring it.')
                    # if not, ignore it
                    ignores.append(oid)
                    objs.append(db_obj)
                    if dictify:
                        output['unmodified'].append(db_obj)
            else:
                # object will be appended to output['new'] after it is
                # created (below)
                orb.log.debug('  - object is new (oid not in db).')
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
            # special case:  'parameters' key
            parm_dict = d.get('parameters')
            if parm_dict:
                recompute_parms_required = True
                orb.log.debug('  + parameters found, deserializing ...')
                deserialize_parms(d['oid'], parm_dict)
            else:
                orb.log.debug('  + no parameters found for this object.')
            # identify fk values; explicitly ignore inverse properties
            # (even though d should not have any)
            orb.log.debug('  + checking for fk fields')
            fks = [a for a in field_names
                   if ((not schema['fields'][a]['is_inverse'])
                        and (schema['fields'][a].get('related_cname')
                             in orb.classes))]
            if fks:
                orb.log.debug('    fk fields found: {}'.format(asciify(fks)))
                for fk in fks:
                    # get the related object by its oid (i.e. d[fk])
                    orb.log.debug('    * rel obj oid: "{}"'.format(
                                   asciify(d.get(asciify(fk)))))
                    if d.get(asciify(fk)):
                        orb.log.debug('      rel obj found.')
                        kw[asciify(fk)] = orb.get(asciify(d[asciify(fk)]))
                    else:
                        orb.log.debug('      rel obj NOT found.')
            cls = orb.classes[cname]
            if d['oid'] in updates:
                orb.log.debug('* updating existing object {}'.format(
                                                                d['oid']))
                obj = updates[d['oid']]
                for a, val in list(kw.items()):
                    setattr(obj, a, val)
                objs.append(obj)
                if cname == 'Acu':
                    refresh_componentz_required = True
                    recompute_parms_required = True
            elif d['oid'] not in ignores:
                orb.log.debug('* creating new object ...')
                obj = cls(**kw)
                if obj:
                    orb.log.debug('  object created:')
                    orb.log.debug('    oid: {}'.format(obj.oid))
                    orb.log.debug('    id: {}'.format(obj.id))
                    orb.log.debug('    name: {}'.format(obj.name))
                    orb.db.add(obj)
                    objs.append(obj)
                    created += 1
                    current_oids.append(obj.oid)
                    if dictify:
                        output['new'].append(obj)
                    if cname == 'Acu':
                        refresh_componentz_required = True
                        recompute_parms_required = True
                else:
                    orb.log.debug('  object creation failed:')
                    orb.log.debug('    obj: {}'.format(obj))
            if refresh_componentz_required:
                refresh_componentz(orb, obj.assembly)
                refresh_componentz_required = False
    orb.db.commit()
    orb.log.debug('***************************')
    orb.log.debug('* deserialization complete:')
    orb.log.debug('    {} objects created'.format(created))
    orb.log.debug('    {} objects updated'.format(len(updates)))
    orb.log.debug('***************************')
    if recompute_parms_required:
        orb.recompute_parms()
    if dictify:
        return output
    else:
        return objs

