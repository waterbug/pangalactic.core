"""
Functions related to object access permissions
"""
from builtins import str
from pangalactic.core         import state, config
from pangalactic.core.uberorb import orb
from functools import reduce


def get_perms(obj, user=None):
    """
    Get the permissions of the specified user relative to the specified object.
    If used as a client-side function, it is assumed that the existence of the
    object on the client side (either by retrieval from the server or by local
    creation) signifies that it is readable.

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
    if config.get('local_admin'):
        return ['view', 'modify', 'decloak', 'delete']
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
            return list(perms)
    else:
        # user not provided -> client app (local user)
        user_oid = state.get('local_user_oid')
        if not user_oid:
            return list(perms)
        user = orb.get(user_oid)
        if not user:
            return list(perms)
    # if we get this far, we have a user_oid and a user object
    if is_global_admin(user):
        perms |= set(['modify', 'decloak', 'delete'])
    # user has write permissions if Admin for a grantee org or if user
    # has a discipline role in the owner org that corresponds to the
    # product type
    else:
        if (hasattr(obj, 'creator') and
            getattr(obj.creator, 'oid', False) and
            obj.creator.oid == user_oid):
            perms |= set(['modify', 'decloak', 'delete'])
        # TODO:  more possible permissions for Administrators
        user_orgs = get_user_orgs(user)
        if user_orgs:
            orgs_ac = reduce(lambda x,y: x or y, 
                        [get_org_access(obj, org) for org in user_orgs])
            if orgs_ac:
                perms |= set(['view'])
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
    return False


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
        # NOTE: Parameter Definitions are always public
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

