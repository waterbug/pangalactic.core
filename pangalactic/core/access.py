"""
Functions related to object access permissions
"""
from builtins import str
from pangalactic.core         import state, config
from pangalactic.core.uberorb import orb


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
    # if obj:
        # cname = obj.__class__.__name__
        # orb.log.debug('  for {} object, id: {}, oid: {}'.format(cname,
                                                        # obj.id, obj.oid))
    if config.get('local_admin') or permissive:
        orb.log.debug('  "local_admin" or "permissive" configured.')
        perms = ['view', 'modify', 'decloak', 'delete']
        orb.log.debug('  perms: {}'.format(perms))
        return perms
    perms = set()
    # NOTE: don't need "grantees" any more -- only one possibility!
    # (the "owner" project or org) ... use "is_decloaked"
    if not hasattr(obj, 'grantees'):
        # not a ManagedObject -> everyone has 'view' access
        perms.add('view')
    else:
        # ManagedObject (can be "cloaked")
        if getattr(obj, 'public', False):
            # if a ManagedObject is "public", everyone has 'view' access
            perms.add('view')
    if user:
        # user specified -> server-side
        user_oid = getattr(user, 'oid', None)
        if not user_oid:
            orb.log.debug('  specified user has no "oid".')
            orb.log.debug('  perms: {}'.format(perms))
            return list(perms)
    else:
        # user not provided -> client-side (local user)
        user_oid = state.get('local_user_oid')
        if not user_oid:
            orb.log.debug('  no local user configured.')
            orb.log.debug('  perms: {}'.format(perms))
            return list(perms)
        user = orb.get(user_oid)
        if not user:
            orb.log.debug('  no user object found.')
            orb.log.debug('  perms: {}'.format(perms))
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
            orb.log.debug('  This object is a collaborative project.')
            collab_project = True
    if is_global_admin(user):
        # global admin is omnipotent, except for deleting projects ...
        orb.log.debug('  ******* user is a global admin.')
        if collab_project:
            # collaborative projects cannot be deleted
            # TODO: allow deletion of collaborative projects but revert
            # ownership of any owned objects to the project's parent org
            perms = ['view', 'modify']
        else:
            perms = ['view', 'modify', 'decloak', 'delete']
            return perms
        orb.log.debug('  perms: {}'.format(perms))
    # user has write permissions if Admin for a grantee org or if user
    # has a discipline role in the owner org that corresponds to the
    # object's 'product_type'
    else:
        # did the user create the object?  if so, full perms ...
        if (hasattr(obj, 'creator') and
            obj.creator is user):
            orb.log.debug('  user is object creator.')
            if collab_project:
                # a collaborative project cannot be deleted
                orb.log.debug('  - object is a collaborative project ...')
                orb.log.debug('    cannot be deleted.')
                perms = ['view', 'modify']
            else:
                # any other object can be deleted by its creator
                orb.log.debug('  - object is not a collaborative project ...')
                orb.log.debug('    can be modified or deleted by its creator.')
                perms = ['view', 'modify', 'decloak', 'delete']
            orb.log.debug('  perms: {}'.format(perms))
            return perms
        # From here on, access depends on roles and product_types
        TBD = orb.get('pgefobjects:TBD')
        # [1] is the object a Product?
        if isinstance(obj, orb.classes['Product']):
            # orb.log.debug('  - object is a Product ...')
            if not obj.owner:
                # orb.log.debug('    owner not specified -- view only.')
                return ['view']
            ras = orb.search_exact(cname='RoleAssignment',
                                   assigned_to=user,
                                   role_assignment_context=obj.owner)
            role_ids = [ra.assigned_role.id for ra in ras]
            # orb.log.debug('  user has roles: {}'.format(role_ids))
            subsystem_types = set()
            if role_ids:
                subsystem_types = set.union(
                                        *[orb.role_product_types.get(r, set())
                                          for r in role_ids])
            # orb.log.debug('  user is authorized for subsystem types:')
            # orb.log.debug('  {}'.format(subsystem_types))
            pt_id = getattr(obj.product_type, 'id', 'unknown')
            # orb.log.debug('  this ProductType is "{}"'.format(pt_id))
            if pt_id in subsystem_types:
                # orb.log.debug(
                    # '  user is authorized for ProductType "{}".'.format(pt_id))
                perms = ['view', 'modify', 'decloak', 'delete']
                # orb.log.debug('  perms: {}'.format(perms))
                return perms
            else:
                txt = '  user is NOT authorized for ProductType "{}".'.format(
                                                                        pt_id)
                orb.log.debug(txt)
        # [2] is it an Acu?
        # if so, the user can modify it if any of the following is true:
        # [2a] the user has a role in the context of the assembly's "owner"
        #      that relates to the assembly's product_type
        # [2b] its component is real and the user has a role in the context of
        #      the assembly's "owner" that relates to the component's
        #      product_type (regardless of the assembly's product type)
        # [2c] its component is "TBD" and the user has a role in the context of
        #      the assembly's "owner" that relates to the Acu's
        #      product_type_hint (regardless of the assembly's product type)
        elif isinstance(obj, orb.classes['Acu']):
            orb.log.debug('  - object is an Acu')
            # access will depend on ownership of its assembly
            if not obj.assembly.owner:
                orb.log.debug('    assembly owner not specified -- view only!')
                return ['view']
            ras = orb.search_exact(cname='RoleAssignment',
                                   assigned_to=user,
                                   role_assignment_context=obj.assembly.owner)
            role_ids = [ra.assigned_role.id for ra in ras]
            # orb.log.debug('    + assigned roles of user "{}" on {}:'.format(
                                            # user.id, obj.assembly.owner.id))
            # orb.log.debug('      {}'.format(str(role_ids)))
            subsystem_types = set.union(*[orb.role_product_types.get(r, set())
                                          for r in role_ids])
            # orb.log.debug('    + authorized subsystem types: {}:'.format(
                                                    # str(subsystem_types)))
            assembly_type = getattr(obj.assembly.product_type, 'id', '')
            orb.log.debug('    assembly product_type is "{}"'.format(
                          assembly_type))
            # [2a] assembly with a relevant product type
            if assembly_type in subsystem_types:
                # orb.log.debug('  - assembly product_type is relevant.')
                perms = ['view', 'modify', 'decloak', 'delete']
                # orb.log.debug('    perms: {}'.format(perms))
                return perms
            # [2b] real component with a relevant product type
            elif (getattr(obj.component.product_type, 'id', None)
                  in subsystem_types):
                # orb.log.debug('  - component product_type is relevant.')
                perms = ['view', 'modify', 'decloak', 'delete']
                # orb.log.debug('    perms: {}'.format(perms))
                return perms
            # [2c] TBD component with a relevant product type hint
            elif getattr(obj, 'component', None) is TBD:
                pt = getattr(obj.product_type_hint, 'id', '')
                if pt in subsystem_types:
                    # orb.log.debug('  - TBD product_type_hint is relevant.')
                    perms = ['view', 'modify', 'decloak', 'delete']
                    # orb.log.debug('    perms: {}'.format(perms))
                    return perms
                else:
                    # orb.log.debug('  - TBD product_type_hint is not relevant.')
                    perms = ['view']
                    # orb.log.debug('    perms: {}'.format(perms))
                    return perms
        # [3] is it a ProjectSystemUsage?
        elif isinstance(obj, orb.classes['ProjectSystemUsage']):
            # orb.log.debug('  - object is a ProjectSystemUsage')
            # access will depend on the user's role in the project
            ras = orb.search_exact(cname='RoleAssignment',
                                   assigned_to=user,
                                   role_assignment_context=obj.project)
            roles = set([ra.assigned_role.id for ra in ras])
            auth_roles = set(['administrator', 'lead_engineer',
                              'systems_engineer'])
            if roles & auth_roles:
                # orb.log.debug('  - user is authorized by role(s) ...')
                # orb.log.debug('    {}'.format(list(roles & auth_roles)))
                perms = ['view', 'modify', 'decloak', 'delete']
                # orb.log.debug('    perms: {}'.format(perms))
                return perms
        # [4] if none of the above, log the relevant info for debugging ...
        else:
            orb.log.debug('  - object type: {}'.format(obj.__class__.__name__))
            orb.log.debug('  - object creator: {}'.format(
                               getattr(obj.creator, 'id', None) or 'unknown'))
            if hasattr(obj, 'owner'):
                orb.log.debug('  - object owner: {}'.format(
                                    getattr(obj, 'owner', None) or 'unknown'))
            else:
                orb.log.debug('  - object has no "owner" attribute.')
        # TODO:  more possible permissions for Administrators
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


def is_cloaked(obj):
    """
    Return the cloaking status of an object.

    Args:
        obj (Identifiable):  object for which orgs with access are sought

    Returns:
        status (bool): True if cloaked
    """
    orb.log.debug('* get_cloaked({})'.format(obj.name))
    obj_oid = getattr(obj, 'oid', None)
    if not obj or not obj_oid:
        orb.log.debug('  [no object or object has no oid]')
        return False
    if (getattr(obj, 'public', False)
        or obj.__class__.__name__ == 'ParameterDefinition'):
        # NOTE: Parameter Definitions are always public, even though they are
        # ManagedObjects
        orb.log.debug('  object is public')
        return False
    if isinstance(obj, orb.classes['ManagedObject']):
        # access is granted directly for ManagedObjects
        grants = orb.search_exact(cname='ObjectAccess', accessible_object=obj)
        return not bool(grants)
    elif isinstance(obj, orb.classes['Acu']):
        # access for Acu is determined by assembly/component access
        assembly_grants = orb.search_exact(
                        cname='ObjectAccess',
                        accessible_object=obj.assembly)
        if getattr(obj.component, 'public', False):
            # if component is 'public', access depends only on assembly
            if getattr(obj.assembly, 'public', False):
                orb.log.debug('  Acu in a public assembly is public.')
                return False
            else:
                # if assembly is cloaked, Acu is cloaked
                grants = orb.search_exact(cname='ObjectAccess',
                                          accessible_object=obj.assembly)
                return not bool(grants)
        else:
            component_grants = orb.search_exact(
                                            cname='ObjectAccess',
                                            accessible_object=obj.component)
            if assembly_grants and component_grants:
                return False
            else:
                return True
    elif isinstance(obj, orb.classes['ProjectSystemUsage']):
        # access is determined by project/system access for PSU
        if ((not getattr(obj.project, 'oid', None))
            or (obj.project.oid == 'pgefobjects:SANDBOX')):
            orb.log.debug('  PSUs for SANDBOX or None are not accessible.')
            return True
        # elif not SANDBOX, PSU access depends on system access
        orgs = set([g.grantee for g in orb.search_exact(
                                        cname='ObjectAccess',
                                        accessible_object=obj.system)])
        orb.log.debug('  {}'.format(str([o.name for o in orgs])))
        return not bool(orgs)
    else:
        # if object is not a ManagedObject, Acu, or PSU, it is public
        orb.log.debug('  object is public [not MO, Acu, or PSU].')
        return False


