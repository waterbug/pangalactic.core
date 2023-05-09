"""
Functions related to object access permissions
"""
import traceback
from pangalactic.core         import state, config
from pangalactic.core.uberorb import orb


modifiables = [
        'ActCompRel',
        'ParameterRelation',
        'Relation',
        'Representation',
        'RequirementAncestry']


def get_perms(obj, user=None, permissive=False, debugging=False):
    """
    Get the permissions of the specified user relative to the specified object.
    If used as a client-side function, no user is supplied and the local user
    is looked up.  On the client side it is assumed that the existence of the
    object locally (either by retrieval from the server or by local creation)
    signifies that the user has at least "view" permission.

    Args:
        obj (Identifiable):  the object

    Keyword Args:
        user (Person):  the user object (None -> local user)
        permissive (bool):  sets "permissive" mode
        debugging (bool):  add explanation string if debugging

    Returns:
        permissions (list of str):  a list that is either empty or
            contains permission codes.  The possible codes are:

            'view'
            'modify'
            'delete'
    """
    # NOTE:  the authoritative source for data on roles and role assignments
    # will typically be an administrative service, unless the repository is
    # fulfilling the role of the administrative service.  Therefore, because
    # operations to sync such data are expensive, the data are cached in
    # `state` variables rather than stored in the local db.
    # orb.log.info('* get_perms ...')
    # empty or None objects have no permissions
    if not obj:
        return ['no obj']
    if obj:
        cname = obj.__class__.__name__
        # orb.log.debug('  for {} object, id: {}, oid: {}'.format(cname,
                                                        # obj.id, obj.oid))
    if obj.oid == 'pgefobjects:SANDBOX':
        # anyone can "modify" the SANDBOX (i.e. add systems to it)
        return ['view', 'modify', 'object is SANDBOX']
    if obj.oid == 'pgefobjects:TBD':
        # no one can "modify" the TBD object
        return ['view', 'object is TBD']
    if config.get('local_admin') or permissive:
        # *********************************************************************
        # NOTE: USE WITH EXTREME CAUTION! These settings can lead to major
        # malfunctions in collaborative projects if repository objects are
        # edited or deleted offline and then the client is synced with a
        # repository!
        # *********************************************************************
        # orb.log.debug('  "local_admin" or "permissive" configured.')
        perms = ['view', 'modify', 'delete', 'local admin or permissive']
        # orb.log.debug('  perms: {}'.format(perms))
        return perms
    perms = set()
    frozen = getattr(obj, 'frozen', False)
    # Products can be "frozen", in which case if they would otherwise be
    # viewable (i.e. either "public" or the user has a role in the project that
    # owns them) then they are view-only
    # an Acu in a frozen assembly
    if (hasattr(obj, 'assembly') and
        getattr(obj.assembly, 'frozen', False)):
        # orb.log.debug('  Any Acu in a frozen assembly is frozen')
        frozen = True
    if frozen:
        # orb.log.debug(f'* object {obj.oid} is frozen.')
        return set(['view'])
    if isinstance(obj, orb.classes['Product']):
        # Products can be "cloaked" ("non-public")
        if getattr(obj, 'public', False):
            # Product is "public" -> everyone has 'view' access;
            # determine other perms by logic below ...
            perms.add('view')
    else:
        # not a Product -> everyone has 'view' access
        perms.add('view')
    if user:
        user_oid = getattr(user, 'oid', None)
        if not user_oid:
            # orb.log.debug('  specified user has no "oid".')
            # orb.log.debug('  perms: {}'.format(perms))
            perms = list(perms)
            if debugging:
                perms.append('no user oid')
            return perms
    else:
        # user not provided -> find local user (client-side)
        user_oid = state.get('local_user_oid')
        if not user_oid:
            # orb.log.debug('  no local user configured.')
            # orb.log.debug('  perms: {}'.format(perms))
            perms = list(perms)
            if debugging:
                perms.append('no local user oid')
            return perms
        user = orb.get(user_oid)
        if not user:
            # orb.log.debug('  no user object found.')
            # orb.log.debug('  perms: {}'.format(perms))
            perms = list(perms)
            if debugging:
                perms.append('no local user object found')
            return perms
    # avoid crash if PSU instances have 'project' attr of None -- this has been
    # observed, although the PSU is obviously corrupted in this case
    if (isinstance(obj, orb.classes['ProjectSystemUsage'])
        and getattr(obj.project, 'oid', None) == 'pgefobjects:SANDBOX'):
        # orb.log.debug('  *** SANDBOX PSUs are modifiable by any user')
        perms = ['view', 'modify', 'delete', 'SANDBOX PSU']
        return perms
    # Instances of these classes are refdata and cannot be modified or deleted.
    # NOTE that ParameterDefinition is a subclass of DataElementDefinition, so is
    # implicitly included here.
    unmodifiables = (
        orb.classes['ActivityType'],
        orb.classes['DataElementDefinition'],
        orb.classes['Discipline'],
        orb.classes['DisciplineProductType'],
        orb.classes['DisciplineRole'],
        orb.classes['ModelFamily'],
        orb.classes['ModelType'],
        orb.classes['ParameterContext'],
        orb.classes['PortTemplate'],
        orb.classes['PortType'],
        orb.classes['ProductType'],
        orb.classes['Role'])
    if isinstance(obj, unmodifiables):
        # orb.log.debug('  *** reference data cannot be modified or deleted.')
        perms = ['view', 'ref data: view only']
        return perms
    # Instances of these classes are modifiable by any user -- they are
    # typically only created in association with other objects and usually only
    # accessible via their associated objects
    if obj.__class__.__name__ in modifiables:
        perms = ['view', 'modify', 'delete', 'universally modifiable']
        return perms
    # if we get this far, we have a user_oid and a user object

    # set up some convenience values
    server = not state.get('client')
    client = state.get('client')
    connected = state.get('connected')
    server_or_connected_client = server or (client and connected)
    object_not_synced = obj.oid not in state.get('synced_oids', [])
    if is_global_admin(user):
        # global admin is omnipotent, except for deleting projects ...
        # orb.log.debug('  ******* user is a global admin.')
        perms = ['view']
        # if (state.get('client') and
            # (state.get('connected') or
             # obj.oid not in state.get('synced_oids', []))):
        if server or (client and (connected or object_not_synced)):
            # deletions and mods are only allowed on the client if connected or
            # object has not been synced to the server
            perms += ['modify', 'delete']
        # orb.log.debug('  perms: {}'.format(perms))
        if debugging:
            perms.append('global admin perms')
        return perms
    if client and not connected and object_not_synced:
        # client user always has full perms when not connected AND the object
        # has not been synced to the repo (which implies that the user created
        # the object)
        # orb.log.debug('  full perms: offline & object not synced.')
        perms = ['view', 'modify', 'delete', 'offline & object not synced']
        return perms
    else:
        # -------------------------------------------------------------------
        # user has write permissions if Admin for owner org or if user has a
        # discipline role in the owner org that corresponds to the object's
        # 'product_type'
        # -------------------------------------------------------------------
        # Did the user create the object?  Then if the object is not an
        # instance of Person, full perms ...
        if (hasattr(obj, 'creator') and obj.creator is user and
            not isinstance(obj, orb.classes['Person'])):
            # orb.log.debug('  user is object creator.')
            perms = ['view']
            if server_or_connected_client:
                perms += ['delete', 'modify']
            # orb.log.debug('  perms: {}'.format(perms))
            if debugging:
                perms.append('object creator perms')
            return perms
        if isinstance(obj, orb.classes['ManagedObject']):
            ras = orb.search_exact(cname='RoleAssignment',
                                   assigned_to=user,
                                   role_assignment_context=obj.owner)
            role_ids = set([ra.assigned_role.id for ra in ras])
        # From here on, access depends on roles and product_types
        TBD = orb.get('pgefobjects:TBD')
        # [1] is the object a Product?
        if isinstance(obj, orb.classes['Product']):
            # orb.log.debug('  - object is a Product ...')
            if not obj.owner:
                # orb.log.debug('    owner not specified -- view only.')
                return ['view']
            # orb.log.debug('  user has roles: {}'.format(role_ids))
            if isinstance(obj, orb.classes['HardwareProduct']):
                # permissions determined by product_type only apply to HW
                subsystem_types = set()
                if role_ids:
                    rpt = [orb.role_product_types.get(r, set())
                           for r in role_ids]
                    if rpt:
                        subsystem_types = set.union(*rpt)
                # orb.log.debug('  user is authorized for subsystem types:')
                # orb.log.debug('  {}'.format(subsystem_types))
                pt_id = getattr(obj.product_type, 'id', 'unknown')
                # orb.log.debug('  this ProductType is "{}"'.format(pt_id))
                if pt_id in subsystem_types:
                    # orb.log.debug(
                        # '  user is authorized for ProductType "{}".'.format(
                        # pt_id))
                    perms = ['view']
                    if server_or_connected_client:
                        # mods and deletions are only allowed on the server or
                        # a connected client
                        perms += ['modify', 'delete']
                    # orb.log.debug('  perms: {}'.format(perms))
                    if debugging:
                        perms.append('role-based product type perms (HW)')
                    return perms
                else:
                    # txt = f'  user NOT authorized for ProductType "{pt_id}")
                    # orb.log.debug(txt)
                    perms = ['view']
                    # orb.log.debug('  perms: {}'.format(perms))
                    if debugging:
                        perms.append('role-based product type perms (HW)')
                    return perms
        if isinstance(obj, orb.classes['Requirement']):
            # Requirements (subclass of ManagedObject) are a special case
            req_mgrs = set(['Administrator', 'systems_engineer',
                            'lead_engineer'])
            if req_mgrs & role_ids:
                perms = ['view']
                if server_or_connected_client:
                    # mods and deletions are only allowed on server or a
                    # connected client
                    perms += ['modify', 'delete']
                # orb.log.debug('  perms: {}'.format(perms))
                if debugging:
                    perms.append('role-based perms (Requirement)')
                return perms
            else:
                perms = ['view']
                # orb.log.debug('  perms: {}'.format(perms))
                if debugging:
                    perms.append('role-based perms (Requirement)')
                return perms
        # [2] is it an Acu?
        # if so, the user can modify it if any of the following is true:
        # [2z] ITS ASSEMBLY IS NOT FROZEN **AND** ONE OF a, b, c:
        # [2a] the user has a role in the context of the assembly's "owner"
        #      that relates to the assembly's product_type
        # [2b] its component is real and the user has a role in the context of
        #      the assembly's "owner" that relates to the component's
        #      product_type (regardless of the assembly's product type)
        # [2c] its component is "TBD" and the user has a role in the context of
        #      the assembly's "owner" that relates to the Acu's
        #      product_type_hint (regardless of the assembly's product type)
        elif isinstance(obj, orb.classes['Acu']):
            # orb.log.debug('  - object is an Acu')
            # access will depend on ownership of its assembly
            if not obj.assembly.owner:
                # orb.log.debug('    assmb. owner not specified -- view only!')
                return ['view']
            ras = orb.search_exact(cname='RoleAssignment',
                                   assigned_to=user,
                                   role_assignment_context=obj.assembly.owner)
            role_ids = set([ra.assigned_role.id for ra in ras])
            # orb.log.debug('    + assigned roles of user "{}" on {}:'.format(
                                            # user.id, obj.assembly.owner.id))
            # orb.log.debug('      {}'.format(str(role_ids)))
            subsystem_types = []
            rpt = [orb.role_product_types.get(r, set()) for r in role_ids]
            if rpt:
                subsystem_types = set.union(*rpt)
            # orb.log.debug('    + authorized subsystem types: {}:'.format(
                                                    # str(subsystem_types)))
            assembly_type = getattr(obj.assembly.product_type, 'id', '')
            # orb.log.debug('    assembly product_type is "{}"'.format(
                          # assembly_type))
            # [2a] assembly with a relevant product type
            if assembly_type in subsystem_types:
                # orb.log.debug('  - assembly product_type is relevant.')
                perms = ['view']
                if server_or_connected_client:
                    # mods and deletions are only allowed on server or a
                    # connected client
                    perms += ['modify', 'delete']
                # orb.log.debug('    perms: {}'.format(perms))
                if debugging:
                    perms.append('[2a] role-based perms (Acu)')
                return perms
            # [2b] real component with a relevant product type
            elif (getattr(obj.component.product_type, 'id', None)
                  in subsystem_types):
                # orb.log.debug('  - component product_type is relevant.')
                perms = ['view']
                if server_or_connected_client:
                    perms += ['modify', 'delete']
                # orb.log.debug('    perms: {}'.format(perms))
                if debugging:
                    perms.append('[2b] role-based perms (Acu)')
                return perms
            # [2c] TBD component with a relevant product type hint
            elif getattr(obj, 'component', None) is TBD:
                pt = getattr(obj.product_type_hint, 'id', '')
                if pt in subsystem_types:
                    # orb.log.debug('  - TBD product_type_hint is relevant.')
                    perms = ['view']
                    if server_or_connected_client:
                        perms += ['modify', 'delete']
                    # orb.log.debug('    perms: {}'.format(perms))
                    if debugging:
                        perms.append('[2c] role-based perms (Acu)')
                    return perms
                else:
                    # orb.log.debug('  - TBD product_type_hint not relevant.')
                    perms = ['view']
                    # orb.log.debug('    perms: {}'.format(perms))
                    if debugging:
                        perms.append('[2c] role-based perms (Acu)')
                    return perms
        # [3] is it a ProjectSystemUsage or a Project?
        elif isinstance(obj, (orb.classes['ProjectSystemUsage'],
                              orb.classes['Project'])):
            # orb.log.debug('  - object is a Project or ProjectSystemUsage')
            # access will depend on the user's role in the project
            if isinstance(obj, orb.classes['ProjectSystemUsage']):
                ras = orb.search_exact(cname='RoleAssignment',
                                       assigned_to=user,
                                       role_assignment_context=obj.project)
            elif isinstance(obj, orb.classes['Project']):
                ras = orb.search_exact(cname='RoleAssignment',
                                       assigned_to=user,
                                       role_assignment_context=obj)
            roles = set([ra.assigned_role.id for ra in ras])
            auth_roles = set(['administrator', 'lead_engineer',
                              'systems_engineer'])
            if roles & auth_roles:
                # orb.log.debug('  - user is authorized by role(s) ...')
                # orb.log.debug('    {}'.format(list(roles & auth_roles)))
                perms = ['view']
                if server_or_connected_client:
                    perms += ['modify', 'delete']
                # orb.log.debug('    perms: {}'.format(perms))
                if debugging:
                    perms.append('[3] role-based perms (PSU)')
                return perms
        # [4] is it a Port?
        elif cname == 'Port':
            # access will depend on the user's permissions on 'of_product'
            perms = get_perms(obj.of_product, user=user)
            if debugging:
                perms.append('[4] role-based perms (Port)')
            return perms
        # [5] is it a Flow?
        elif isinstance(obj, orb.classes['Flow']):
            # orb.log.debug('* get_perms for Flow ...')
            # any user with permissions on 'context' *or* on either Port of the
            # Flow will have the superset of those permissions
            perms = []
            try:
                s = set(get_perms(obj.start_port_context, user=user))
                s |= set(get_perms(obj.end_port_context, user=user))
                s |= set(get_perms(obj.end_port.of_product, user=user))
                s |= set(get_perms(obj.start_port.of_product, user=user))
                perms = list(s)
                # orb.log.debug(f'  perms: {perms}')
            except:
                # perms could not be determined
                orb.log.debug('* get_perms() encountered an exception:')
                orb.log.debug(f'  {traceback.format_exc}')
                perms = []
            if debugging:
                perms.append('[5] role-based perms (Flow)')
            return perms
        # [6] if none of the above, log the relevant info for debugging ...
        else:
            return list(perms)
            # orb.log.debug('  - object type: {}'.format(obj.__class__.__name__))
            # creator_id = '[undefined]'
            # if hasattr(obj, 'creator'):
                # creator_id = getattr(obj.creator, 'id', None) or '[unknown]'
            # orb.log.debug('  - object creator: {}'.format(creator_id))
            # owner_id = '[undefined]'
            # if hasattr(obj, 'owner'):
                # owner_id = getattr(obj.owner, 'id', None) or '[unknown]'
            # orb.log.debug('  - object owner: {}'.format(owner_id))
        # TODO:  more possible permissions for Administrators
    # orb.log.info('  perms: {}'.format(perms))
    return list(perms)

def get_user_orgs(user):
    """
    Get all orgs in which the user has a role.

    Args:
        user (Person):  user in question

    Returns:
        list of orgs
    """
    ras = orb.search_exact(cname='RoleAssignment', assigned_to=user)
    return set([ra.role_assignment_context for ra in ras])


def is_global_admin(user):
    """
    Return True if the user is a global admin; otherwise False.

    Args:
        user (Person):  user in question

    Returns:
        boolean
    """
    admin_role = orb.get('pgefobjects:Role.Administrator')
    global_admin = orb.select('RoleAssignment',
                              assigned_role=admin_role,
                              assigned_to=user,
                              role_assignment_context=None)
    return bool(global_admin)


def is_cloaked(obj):
    """
    Return the cloaking status of an object.

    Args:
        obj (Identifiable):  object for cloaking state is sought

    Returns:
        status (bool): True if cloaked
    """
    # orb.log.debug('* is_cloaked({})'.format(obj.name))
    obj_oid = getattr(obj, 'oid', None)
    if not obj or not obj_oid:
        # orb.log.debug('  [no object or object has no oid]')
        return False
    if hasattr(obj, 'public') and obj.public:
        # orb.log.debug('  object is public.')
        return False
    elif isinstance(obj, (orb.classes['Organization'],
                          orb.classes['ParameterDefinition'])):
        # NOTE: Parameter Definitions and Organizations/Projects are always
        # public, even though they are ManagedObjects
        return False
    elif isinstance(obj, orb.classes['Acu']):
        # cloaking for Acu is determined by assembly cloaking
        return is_cloaked(obj.assembly)
    elif isinstance(obj, orb.classes['ProjectSystemUsage']):
        if (getattr(obj, 'project', None) and
            getattr(obj.project, 'id', '') == 'SANDBOX'):
            # SANDBOX PSUs are always cloaked
            return True
        else:
            # otherwise, cloaking for PSU is determined by system cloaking
            return is_cloaked(obj.system)
    elif hasattr(obj, 'public') and not obj.public:
        return True
    else:
        # if object is not a ManagedObject, Acu, or PSU, it is public
        # orb.log.debug('  object is public.')
        return False

