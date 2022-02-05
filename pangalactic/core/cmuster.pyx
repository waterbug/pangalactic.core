# -*- coding: utf-8 -*-
"""
Cython deserializer for pangalactic domain objects and parameters.
"""
# SQLAlchemy
from sqlalchemy import ForeignKey

# PanGalactic
from pangalactic.core.meta        import M2M, ONE2M
from pangalactic.core.refdata     import ref_oids
from pangalactic.core.utils.meta  import cookers, uncookers, uncook_datetime
from pangalactic.core.utils.datetimes  import earlier
from pangalactic.core.parametrics import (deserialize_des,
                                          deserialize_parms,
                                          refresh_componentz,
                                          refresh_req_allocz,
                                          serialize_des, serialize_parms,
                                          update_de_defz, update_parm_defz,
                                          update_parmz_by_dimz)

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

    one2m_or_m2m = list(ONE2M) + list(M2M)
    recompute_parmz_required = False
    refresh_componentz_required = False
    req_oids = set()
    acus = set()
    psus = set()
    # objs: list of all deserialized objects
    objs = []
    # products: list of deserialized objects that are instances of Product
    # subclasses
    products = []
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
                        # a Flow MUST have "start_port", "end_port" and
                        # "flow_context" objects
                        if fk in ["start_port", "end_port", "flow_context"]:
                            orb.log.debug('      invalid Flow instance:')
                            oid = d['oid']
                            orb.log.debug(f'      - oid: "{oid}"')
                            orb.log.debug('        is missing start_port,')
                            orb.log.debug('        end_port, or flow_context;')
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
                    if cname in ['Acu', 'ProjectSystemUsage', 'Requirement']:
                        recompute_parmz_required = True
                # else:
                    # orb.log.debug('  object creation failed for kwargs:')
                    # orb.log.debug('  {}'.format(str(kwargs)))
            if refresh_componentz_required:
                if getattr(obj, 'assembly', None):
                    refresh_componentz(obj.assembly)
                    refresh_componentz_required = False
    orb.db.commit()
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
        # orb.log.debug('  - deserialize recomputing parameters ...')
        orb.recompute_parmz()
        # orb.log.debug('    done.')
    if dictify:
        return output
    else:
        return objs

