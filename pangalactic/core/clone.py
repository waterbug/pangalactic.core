# -*- coding: utf-8 -*-
"""
Create new objects from existing ones, or from nothing.
"""
from copy import deepcopy
from uuid import uuid4

# Louie
from pydispatch import dispatcher

from pangalactic.core             import orb, state
from pangalactic.core.names       import (get_acu_id, get_acu_name,
                                          get_next_port_seq, get_next_ref_des,
                                          get_port_abbr, get_port_id,
                                          get_port_name)
from pangalactic.core.parametrics import (add_default_data_elements,
                                          add_default_parameters,
                                          data_elementz, get_pval,
                                          parameterz, set_pval,
                                          refresh_componentz)
from pangalactic.core.utils.datetimes import dtstamp


def clone(what, include_ports=True, include_components=True,
          include_specified_components=None, generate_id=False,
          flatten=False, save_hw=True, **kw):
    """
    Create a new object either (1) from a class using keywords or (2) by
    copying an existing object.  NOTE:  clone() does not save/commit the
    object, so orb.save() or orb.db.commit() must be called after cloning --
    *but* "HardwareProduct" is a special case: unless the "save_hw" kw arg is
    set to False, the dispatcher signal "new hardware clone" is sent, which
    triggers pangalaxian to switch to Component Mode and send the "vger.save()"
    rpc with the HardwareProduct object and any newly created associated
    objects (e.g. Port instances and/or, for white box clones, Acu instances).

    (1) If `what` is a string, create a new instance of the class with
    that name, and assign it the values in the `kw` dict.  If the named
    class is a subtype of 'Product', the new instance will be a
    "working version" and will receive a version and version_sequence only
    when frozen.

    (2) If `what` is an instance of a subtype of `Identifiable`, create a
    clone of that instance.  If it is a subtype of 'Product', it will be
    checked for 'version' -- if not None, it is versioned.

    Any keyword arguments supplied will be used as attributes if they are
    in the schema (overriding those of the provided object in case 2).  If a
    oid is not provided, a new oid guaranteed to be unique will be generated.
    If not specified, the following attributes will also be generated:

        creator and modifier = local_user
        owner = current project or PGANA
        [create|mod]_datetime = current datetime

    Default values are used where appropriate.

    Args:
        what (str or Identifiable): class name or object to be cloned

    Keyword Args:
        include_ports (bool): if an object with ports is being cloned, give the
            clone the same ports
        include_components (bool): if the object being cloned has components,
            create new Acus for the clone to have all the same components
        include_specified_components (list of Acu instances or None): create
            new Acus for the clone to have ONLY the specified components (NOTE
            THAT include_specified_components OVERRIDES include_components)
        generate_id (bool): if True, an id will be auto-generated -- always
            True if obj is a subclass of Product
        flatten (bool):  for a black box clone (no components), populate the
            Mass, Power, and Data Rate parameters with the corresponding 'CBE'
            parameter values from the original object
        save_hw (bool): applies to clones of HardwareProduct -- if True, the
            dispatcher "new hardware clone" is sent, which triggers pangalaxian
            to switch to Component Mode and send the "vger.save()" rpc;
            if False, that will not be done, so the clone must be explicitly
            saved.
    Mode and to send the "vger.save()" rpc
        kw (dict):  attributes for the clone
    """
    orb.log.info('* clone({})'.format(what))
    from_object = True
    recompute_needed = False
    if what in orb.classes:
        # 'what' is a class name -- create a new instance from scratch
        # TODO:  validation: every new object *must* have 'id' value, which
        # *should* be unique (at least within its Class of objects)
        from_object = False
        cname = what
        schema = orb.schemas[cname]
        fields = schema['fields']
        cls = orb.classes[cname]
        newkw = dict([(a, kw[a]) for a in kw if a in fields])
    else:
        # 'what' is a domain object -- clone it to create a new instance
        # TODO: URGENT!!  add logic above to object clones
        # TODO: URGENT!!  exception handling in case what is not a domain obj
        obj = what
        cname = obj.__class__.__name__
        schema = orb.schemas[cname]
        fields = schema['fields']
        non_fk_fields = {a : fields[a] for a in fields
                         if fields[a]['field_type'] != "object"}
        cls = obj.__class__
        newkw = {}
        # populate all fields passed in kw args and all non-fk fields from obj
        # -- fk fields will be handled in special cases ...
        for a in fields:
            # exclude "derived_from"
            if a in kw and a != 'derived_from':
                newkw[a] = kw[a]
            elif a in non_fk_fields:
                newkw[a] = getattr(obj, a)
        # new generated oid
        newkw['oid'] = str(uuid4())
        # standard attributes of any Identifiable ...
        newkw['name'] = 'clone of ' + (obj.name or 'anonymous')
        newkw['description'] = obj.description
    # generate a unique oid if one is not provided
    if not newkw.get('oid'):
        newkw['oid'] = str(uuid4())
    orb.new_oids.append(newkw['oid'])
    if ((generate_id and not issubclass(cls, orb.classes['Product']))
        and not newkw.get('id')):
        orb.log.info('  generating arbitrary id ...')
        # this is only needed for objects for which an 'id' is required
        # but does not need to be significant and/or human-intelligible
        # (ids for subclasses of 'Product' will be autogenerated below ...)
        newkw['id'] = '-'.join([cname, newkw['oid'][:5]])
        orb.log.info('  id: "{}"'.format(newkw['id']))
    orb.log.info('  new %s oid: %s)' % (cname, newkw['oid']))
    NOW = dtstamp()
    newkw.update(dict([(dts, NOW) for dts in ['create_datetime',
                                              'mod_datetime']]))
    local_user = orb.get(state.get('local_user_oid'))
    project = orb.get(state.get('project'))  # None if not set
    if issubclass(cls, orb.classes['Modelable']) and local_user:
        if 'creator' in fields:
            newkw['creator'] = local_user
        if 'modifier' in fields:
            newkw['modifier'] = local_user
    if from_object and issubclass(cls, orb.classes['Product']):
        # TODO:  add interface functions for "clone to create new version"
        # current clone "copies" (i.e. creates a new object, not a version)
        ver_seq = kw.get('version_sequence')
        if isinstance(ver_seq, int):
            # if an integer version_sequence is specified, use it (this will be
            # the case if clone() is being used to create a new version)
            newkw['version_sequence'] = ver_seq
        else:
            # otherwise, assume this is a distinct object, not a new version of
            # the cloned object, and set to 0
            newkw['version_sequence'] = 0
        newkw['version'] = None
        newkw['frozen'] = False
        newkw['iteration'] = 0
        if isinstance(obj, orb.classes['HardwareProduct']):
            # the clone gets the product_type of the original object
            newkw['product_type'] = obj.product_type
    if issubclass(orb.classes[cname], orb.classes['ManagedObject']):
        # in the absence of a specified owner, use the project ...
        if not newkw.get('owner'):
            if project:
                newkw['owner'] = project
            else:
                # use PGANA
                pgana = orb.get('pgefobjects:PGANA')
                newkw['owner'] = pgana
    new_obj = cls(**newkw)
    if orb.is_fastorb:
        new_obj = orb.create_or_update_thing(cname, **newkw)
    else:
        orb.db.add(new_obj)
    # When cloning an existing object that has parameters or data elements,
    # copy them to the clone
    if from_object:
        if parameterz.get(getattr(obj, 'oid', None)):
            new_parameters = deepcopy(parameterz[obj.oid])
            parameterz[newkw['oid']] = new_parameters
            recompute_needed = True
        if data_elementz.get(getattr(obj, 'oid', None)):
            new_data = deepcopy(data_elementz[obj.oid])
            data_elementz[newkw['oid']] = new_data
    # operations specific to HardwareProducts ...
    if isinstance(new_obj, orb.classes['HardwareProduct']):
        new_ports = []
        new_acus = []
        recompute_needed = True
        if from_object:
            # DO NOT use "derived_from"!  It creates an FK relationship that
            # prohibits the original object from being deleted -- the
            # "derived_from" attribute is deprecated and will be removed at
            # some point.
            # new_obj.derived_from = obj
            # if we are including ports, add them ...
            if include_ports and getattr(obj, 'ports', None):
                Port = orb.classes['Port']
                for port in obj.ports:
                    seq = get_next_port_seq(new_obj, port.type_of_port)
                    port_oid = str(uuid4())
                    port_id = get_port_id(port.of_product.id,
                                          port.type_of_port.id,
                                          seq)
                    port_name = get_port_name(port.of_product.name,
                                              port.type_of_port.name, seq)
                    port_abbr = get_port_abbr(port.type_of_port.abbreviation,
                                              seq)
                    if orb.is_fastorb:
                        p = orb.create_or_update_thing('Port',
                                oid=port_oid, id=port_id, name=port_name,
                                abbreviation=port_abbr,
                                type_of_port=port.type_of_port,
                                of_product=new_obj, creator=new_obj.creator,
                                modifier=new_obj.creator, create_datetime=NOW,
                                mod_datetime=NOW)
                        new_ports.append(p)
                    else:
                        p = Port(oid=port_oid, id=port_id, name=port_name,
                                 abbreviation=port_abbr,
                                 type_of_port=port.type_of_port,
                                 of_product=new_obj, creator=new_obj.creator,
                                 modifier=new_obj.creator, create_datetime=NOW,
                                 mod_datetime=NOW)
                        new_ports.append(p)
                        orb.db.add(p)
            # if we are including components, add them ...
            # NOTE:  "include_specified_components" overrides
            # "include_components" -- if components are specified, ONLY those
            # components will be included
            if (include_specified_components and
                isinstance(include_specified_components, list)):
                orb.log.debug('  - include_specified_components ...')
                Acu = orb.classes['Acu']
                for acu in include_specified_components:
                    if not isinstance(acu, orb.classes['Acu']):
                        orb.log.debug(f'    non-Acu skipped: {acu.id}')
                        continue
                    acu_oid = str(uuid4())
                    ref_des = get_next_ref_des(new_obj, acu.component)
                    if orb.is_fastorb:
                        acu = orb.create_or_update_thing('Acu',
                                  oid=acu_oid, id=get_acu_id(new_obj.id,
                                  ref_des), name=get_acu_name(new_obj.name,
                                  ref_des), assembly=new_obj,
                                  component=acu.component,
                                  product_type_hint=acu.product_type_hint,
                                  reference_designator=ref_des,
                                  creator=new_obj.creator,
                                  modifier=new_obj.creator,
                                  create_datetime=NOW, mod_datetime=NOW)
                    else:
                        acu = Acu(oid=acu_oid,
                                  id=get_acu_id(new_obj.id, ref_des),
                                  name=get_acu_name(new_obj.name, ref_des),
                                  assembly=new_obj, component=acu.component,
                                  product_type_hint=acu.product_type_hint,
                                  reference_designator=ref_des,
                                  creator=new_obj.creator,
                                  modifier=new_obj.creator, create_datetime=NOW,
                                  mod_datetime=NOW)
                        orb.db.add(acu)
                    new_acus.append(acu)
                if orb.is_fastorb:
                    orb.adjust_componentz()
                else:
                    refresh_componentz(new_obj)
            elif include_components and getattr(obj, 'components', None):
                Acu = orb.classes['Acu']
                for acu in obj.components:
                    acu_oid = str(uuid4())
                    ref_des = get_next_ref_des(new_obj, acu.component)
                    if orb.is_fastorb:
                        acu = orb.create_or_update_thing('Acu',
                                  oid=acu_oid, id=get_acu_id(new_obj.id,
                                  ref_des), name=get_acu_name(new_obj.name,
                                  ref_des), assembly=new_obj,
                                  component=acu.component,
                                  product_type_hint=acu.product_type_hint,
                                  reference_designator=ref_des,
                                  creator=new_obj.creator,
                                  modifier=new_obj.creator,
                                  create_datetime=NOW, mod_datetime=NOW)
                    else:
                        acu = Acu(oid=acu_oid,
                                  id=get_acu_id(new_obj.id, ref_des),
                                  name=get_acu_name(new_obj.name, ref_des),
                                  assembly=new_obj, component=acu.component,
                                  product_type_hint=acu.product_type_hint,
                                  reference_designator=ref_des,
                                  creator=new_obj.creator,
                                  modifier=new_obj.creator,
                                  create_datetime=NOW, mod_datetime=NOW)
                        orb.db.add(acu)
                    new_acus.append(acu)
                refresh_componentz(new_obj)
            elif (not include_components and not include_specified_components
                  and flatten):
                # black box clone with m, P, R_D assigned the CBE values from
                # the original object
                for pid in ['m', 'P', 'R_D']:
                    pid_cbe = pid + '[CBE]'
                    cbe_val = get_pval(obj.oid, pid_cbe)
                    set_pval(new_obj.oid, pid, cbe_val)
        new_obj.id = orb.gen_product_id(new_obj)
        new_objs = []
        new_objs += new_ports
        new_objs += new_acus
        # the "new hardware clone" signal causes pangalaxian to switch to
        # Component Mode
        if save_hw:
            dispatcher.send(signal='new hardware clone', product=new_obj,
                            objs=new_objs)
    add_default_data_elements(new_obj)
    add_default_parameters(new_obj)
    if recompute_needed:
        if state.get('connected'):
            dispatcher.send(signal='get parmz')
        elif not orb.is_fastorb:
            orb.recompute_parmz()
    return new_obj

