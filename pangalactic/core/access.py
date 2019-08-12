"""
Functions related to object access permissions
"""
from builtins import str
from pangalactic.core         import state, config
from pangalactic.core.uberorb import orb
from functools import reduce


def get_perms(obj, user=None, permissive=False):
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

    Returns:
        permissions (list of str):  a list that is either empty or
            contains permission codes.  The possible codes are:

            'view'
            'modify'
            'decloak'
            'delete'
    """
    # NOTE:  the authoritative source for data on roles and role assignments
    # will typically be an administrative service, unless the repository is
    # fulfilling the role of the administrative service.  Therefore, because
    # operations to sync such data are expensive, the data are cached in
    # `state` variables rather than stored in the local db.
    orb.log.info('* get_perms ...')
    if obj:
        cname = obj.__class__.__name__
        orb.log.info('  for {} object, id: {}, oid: {}'.format(cname, obj.id,
                                                               obj.oid))
    if config.get('local_admin') or permissive:
        orb.log.info('  "local_admin" or "permissive" configured.')
        perms = ['view', 'modify', 'decloak', 'delete']
        orb.log.info('  perms: {}'.format(perms))
        return perms
    perms = set()
    if not hasattr(obj, 'grantees'):
        # not a ManagedObject -> everyone has 'view' access
        perms.add('view')
    else:
        # ManagedObject (can be "cloaked")
        if getattr(obj, 'public', False):
            # if a ManagedObject is "public", everyone has 'view' access
            perms.add('view')
    if user:
        # user specified -> server-side app
        user_oid = getattr(user, 'oid', None)
        if not user_oid:
            orb.log.info('  specified user has no "oid".')
            orb.log.info('  perms: {}'.format(perms))
            return list(perms)
    else:
        # user not provided -> client app (local user)
        user_oid = state.get('local_user_oid')
        if not user_oid:
            orb.log.info('  no local user configured.')
            orb.log.info('  perms: {}'.format(perms))
            return list(perms)
        user = orb.get(user_oid)
        if not user:
            orb.log.info('  no user object found.')
            orb.log.info('  perms: {}'.format(perms))
            return list(perms)
    if isinstance(obj, orb.classes['ProjectSystemUsage']):
        # access is determined by project/system access for PSU
        if obj.project.oid == 'pgefobjects:SANDBOX':
            orb.log.debug('  ******* SANDBOX PSUs are modifiable by user')
            perms = ['view', 'modify', 'decloak', 'delete']
            return perms
    # if we get this far, we have a user_oid and a user object
    # * first check if the object is a collaborative project
    collab_project = False
    if isinstance(obj, orb.classes['Project']):
        ras = orb.search_exact(cname='RoleAssignment',
                               role_assignment_context=obj)
        if ras:
            orb.log.info('  This object is a collaborative project.')
            collab_project = True
    if is_global_admin(user):
        # global admin is omnipotent, except for deleting projects ...
        orb.log.info('  ******* user is a global admin.')
        if isinstance(obj, orb.classes['Project']):
            # a project can only be deleted by its creator
            perms = ['view', 'modify']
        else:
            perms = ['view', 'modify', 'decloak', 'delete']
            return perms
        orb.log.info('  perms: {}'.format(perms))
    # user has write permissions if Admin for a grantee org or if user
    # has a discipline role in the owner org that corresponds to the
    # object's 'product_type'
    else:
        owner = None
        # did the user create the object?  if so, full perms ...
        if (hasattr(obj, 'creator') and
            obj.creator is user):
            orb.log.info('  user is object creator.')
            if collab_project:
                # a collaborative project cannot be deleted
                orb.log.info('  - object is a collaborative project ...')
                orb.log.info('    cannot be deleted.')
                perms = ['view', 'modify']
            else:
                # a local project can be deleted by its creator
                orb.log.info('  - object is a local project ...')
                orb.log.info('    can be modified or deleted by its creator.')
                perms = ['view', 'modify', 'decloak', 'delete']
            orb.log.info('  perms: {}'.format(perms))
            return perms
        # [1] is this a Product and does it have a relevant product type?
        # (config item "discipline_subsystems" must exist for this to work)
        # OR ...
        discipline_subsystems = config.get('discipline_subsystems', {})
        subsystem_type_ids = list(discipline_subsystems.values())
        orb.log.info('  - user has access to subsystems: {}'.format(
                                                str(subsystem_type_ids)))
        product_type_id = None
        TBD = orb.get('pgefobjects:TBD')
        if (hasattr(obj, 'product_type') and
            getattr(obj.product_type, 'id', '') in subsystem_type_ids):
            orb.log.info('  - object is a Product ...')
            product_type_id = obj.product_type.id
            # owner of Product is the relevant owner
            owner = obj.owner
            orb.log.info('  - obj.product_type: "{}"'.format(product_type_id))
        # [2] is it an Acu with a component that has a relevant product type, and
        # of which the *assembly* is owned by an org in which the user has a
        # relevant role?
        # OR ...
        elif (hasattr(obj, 'component') and
              getattr(obj.component, 'product_type', None) and
              getattr(obj.component.product_type, 'id', '')
                                                in subsystem_type_ids):
            orb.log.info('  - object is an Acu')
            orb.log.info('    whose component product_type is {}'.format(
                                obj.component.product_type.id or 'unknown'))
            product_type_id = obj.component.product_type.id
            # owner of assembly is the relevant owner
            owner = obj.assembly.owner
            orb.log.info('  - assembly owner is {} ...'.format(
                                        getattr(owner, 'id', 'unknown')))
        # [3] is it an Acu with an assembly that has a relevant product type, and
        # which is owned by an org in which the user has a relevant role?
        # OR ...
        elif (hasattr(obj, 'assembly') and
              getattr(obj.assembly, 'product_type', None) and
              getattr(obj.assembly.product_type, 'id', '')
                                                in subsystem_type_ids):
            orb.log.info('  - object is an Acu')
            orb.log.info('    whose assembly product_type is {}'.format(
                                obj.assembly.product_type.id or 'unknown'))
            product_type_id = obj.assembly.product_type.id
            # owner of assembly is the relevant owner
            owner = obj.assembly.owner
            orb.log.info('  - assembly owner is {} ...'.format(
                                        getattr(owner, 'id', 'unknown')))
        # [4] is it a Acu with TBD component and a relevant product type hint?
        elif (getattr(obj, 'component', None) is TBD and
              getattr(obj.product_type_hint, 'id', '') in subsystem_type_ids):
            orb.log.info('  - object is an Acu ...')
            product_type_id = obj.product_type_hint.id
            # owner of assembly is the relevant owner
            owner = obj.assembly.owner
            orb.log.info('  - obj.product_type_hint: "{}"'.format(
                                                            product_type_id))
        # [5] if none of the above, log the relevant info for debugging ...
        else:
            orb.log.debug('  - object type: {}'.format(obj.__class__.__name__))
            orb.log.debug('  - object creator: {}'.format(
                               getattr(obj.creator, 'id', None) or 'unknown'))
            if hasattr(obj, 'owner'):
                orb.log.debug('  - object owner: {}'.format(
                                    getattr(obj, 'owner', None) or 'unknown'))
            else:
                orb.log.debug('  - object has no "owner" attribute.')
        if product_type_id and owner:
            # does user have a relevant discipline role in the project or org
            # that owns the object?
            ras = orb.search_exact(cname='RoleAssignment',
                                   assigned_to=user,
                                   role_assignment_context=owner)
            roles = [ra.assigned_role for ra in ras]
            # look up corresponding disciplines
            drs = set()
            for role in roles:
                drs |= set(orb.search_exact(cname='DisciplineRole',
                                            related_role=role))
            disciplines = [dr.related_to_discipline for dr in drs]
            subsystem_type_ids = [discipline_subsystems.get(d.id)
                                  for d in disciplines]
            if product_type_id in subsystem_type_ids:
                orb.log.info('  user is authorized for product_type.')
                perms = ['view', 'modify', 'decloak', 'delete']
                orb.log.info('  perms: {}'.format(perms))
                return perms
            else:
                orb.log.info('  user is NOT authorized for product_type.')
        # TODO:  more possible permissions for Administrators
        user_orgs = get_user_orgs(user)
        if user_orgs:
            orgs_ac = reduce(lambda x,y: x or y, 
                        [get_org_access(obj, org) for org in user_orgs])
            if orgs_ac:
                perms |= set(['view'])
    orb.log.info('  perms: {}'.format(perms))
    return list(perms)

def get_user_orgs(user):
    """
    Get all orgs in which the user has a role.

    Args:
        user (Person):  user in question

    Returns:
        list of orgs
    """
    # TODO ...
    return []


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


def get_orgs_with_access(obj):
    """
    Get the set of all organizations that have 'view' access to an object.
    (TODO:  "black box" vs. "white box" [internals] view access ...)

    Args:
        obj (Identifiable):  object for which orgs with access are sought

    Returns:
        set of Actor instances
    """
    orb.log.debug('* get_orgs_with_access({})'.format(obj.name))
    obj_oid = getattr(obj, 'oid', None)
    if not obj or not obj_oid:
        orb.log.debug('  [no object or object has no oid]')
        return set()
    if (getattr(obj, 'public', False)
        or obj.__class__.__name__ == 'ParameterDefinition'):
        # NOTE: Parameter Definitions are always public, even though they are
        # ManagedObjects
        orb.log.debug('  object is public')
        return set()
    if isinstance(obj, orb.classes['ManagedObject']):
        # access is granted directly for ManagedObjects
        grants = orb.search_exact(cname='ObjectAccess', accessible_object=obj)
        orgs = set([grant.grantee for grant in grants])
        orb.log.debug('  {}'.format(str([o.name for o in orgs])))
        return orgs
    elif isinstance(obj, orb.classes['Acu']):
        # access is determined by assembly/component access for Acu
        assembly_grants = orb.search_exact(
                        cname='ObjectAccess',
                        accessible_object=obj.assembly)
        if getattr(obj.component, 'public', False):
            # if component is 'public', access depends only on assembly
            if getattr(obj.assembly, 'public', False):
                orb.log.debug('  Acu between public objects is public.')
                return set()
            else:
                orgs = set([grant.grantee for grant in assembly_grants])
                orb.log.debug('  {}'.format(str([o.name for o in orgs])))
                return orgs
        else:
            component_grants = orb.search_exact(
                                            cname='ObjectAccess',
                                            accessible_object=obj.component)
            if assembly_grants and component_grants:
                component_grantees = [g.grantee for g in component_grants]
                orgs = set([g.grantee for g in assembly_grants
                            if g.grantee in component_grantees])
                orb.log.debug('  {}'.format(str([o.name for o in orgs])))
                return orgs
            else:
                orb.log.debug('  no orgs have access to this object.')
                return set()
    elif isinstance(obj, orb.classes['ProjectSystemUsage']):
        # access is determined by project/system access for PSU
        if ((not getattr(obj.project, 'oid', None))
            or (obj.project.oid == 'pgefobjects:SANDBOX')):
            orb.log.debug('  PSUs for SANDBOX or None are not accessible.')
            return set()
        # elif not SANDBOX, PSU access depends on system access
        orgs = set([g.grantee for g in orb.search_exact(
                                        cname='ObjectAccess',
                                        accessible_object=obj.system)])
        orb.log.debug('  {}'.format(str([o.name for o in orgs])))
        return orgs
    else:
        # if object is not a ManagedObject, Acu, or PSU, it is public
        orb.log.debug('  object is public [not MO, Acu, or PSU].')
        return set()


def get_org_access(obj, org):
    """
    Get a boolean indicating whether the specified Organization has 'view'
    access to the specified object.

    Args:
        obj (Identifiable):  object for which org access is to be determined
        org (Organization):  org for which access to object is to be determined
    """
    obj_oid = getattr(obj, 'oid', None)
    org_oid = getattr(org, 'oid', None)
    if not org or not org_oid or org_oid == 'pgefobjects:SANDBOX':
        return False
    if not obj or not obj_oid:
        return False
    if getattr(obj, 'public', False):
        return True
    if isinstance(obj, orb.classes['ManagedObject']):
        # access is granted directly for ManagedObjects
        return bool(orb.search_exact(cname='ObjectAccess',
                                     accessible_object=obj, grantee=org))
    elif isinstance(obj, orb.classes['Acu']):
        # access is determined by assembly/component access for Acu
        assembly_granted = bool(orb.search_exact(
                        cname='ObjectAccess',
                        accessible_object=obj.assembly, grantee=org))
        component_granted = bool(orb.search_exact(
                        cname='ObjectAccess',
                        accessible_object=obj.component, grantee=org))
        return (assembly_granted and component_granted)
    elif isinstance(obj, orb.classes['ProjectSystemUsage']):
        # access is determined by system access for PSU
        return bool(orb.search_exact(
                        cname='ObjectAccess',
                        accessible_object=obj.system, grantee=org))
    return False

