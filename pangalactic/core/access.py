"""
Functions related to object access permissions
"""
import traceback
from pangalactic.core import orb, state, config


# Instances of these classes are modifiable by any user.  They are created
# only in association with another object and are reachable only through it,
# so the permission that matters is the one on that object.
#
# NOTE on DocumentReference (2026-08-29):  it is here because it is also the
# only way the repository can accept one.  vger.save() authorizes a new object
# by "the caller is its creator", and a DocumentReference has no creator --
# it is an Identifiable, and it cannot be made a Modelable, because
# `related_item` points at Modelable and sqlalchemy's joined table
# inheritance cannot then tell that foreign key from the inheritance one.
# See pangalactic.core.digital_files.new_doc_with_file().
modifiables = [
        'Axis2Placement3D',
        'ContextDependentShapeRepresentation',
        'DocumentReference',
        'ParameterRelation',
        'Relation',
        'RepresentationFile',
        'RequirementAncestry']

# Instances of these classes are reference data:  they are created on both the
# client and the server by load_reference_data() from refdata.py, and are
# never authored by a user.  Held as class *names* rather than classes because
# orb.classes is not populated when this module is imported.
# NOTE that ParameterDefinition is a subclass of DataElementDefinition, so is
# implicitly included -- which is why is_reference_data() tests by isinstance
# rather than by class name.
unmodifiables = [
        'ActivityType',
        'ContinuousProductType',
        'DataElementDefinition',
        'Discipline',
        'DisciplineProductType',
        'DisciplineRole',
        'ModelType',
        'ParameterContext',
        'PortTemplate',
        'PortType',
        'ProductType',
        'PropertyDefinition',
        'Role']


def is_reference_data(obj):
    """
    Say whether an object is reference data -- created from refdata.py at
    start-up rather than authored by a user, and therefore never modifiable
    and never worth pushing to the repository, which generates its own copy
    the same way.

    Args:
        obj (Identifiable):  the object

    Returns:
        bool:  True if the object is an instance of a reference data class
    """
    classes = tuple(orb.classes[cname] for cname in unmodifiables
                    if cname in orb.classes)
    return bool(classes) and isinstance(obj, classes)


# Instances of these classes cannot be edited while disconnected, and cannot
# be checked out.  They are the objects a timeline is made of, and a timeline
# does not decompose into independently editable parts:  an Activity's
# duration and start/stop times are interrelated with those of every other
# Activity in the timeline, and the ActivityControls sequence them, so an
# edit to any one of them is an edit to the timeline.  A claim on a single
# one would not cover the work it enables, and claiming a whole timeline is a
# different and larger design.  See NOTES_ON_CHECKOUT_MODEL.md section 13.
#
# Held as class *names* rather than classes because orb.classes is not
# populated when this module is imported;  is_offline_excluded() tests by
# isinstance, so the subclasses come with them -- Mission and Test with
# Activity, Decision and Merge with ActivityControl.
#
# This is the single definition of the rule:  the offline dialog and
# vger.check_out() both consult it, so it cannot be extended in one place and
# missed in another.
offline_excluded = [
        'Activity',
        'ActivityControl']


def is_offline_excluded(obj):
    """
    Say whether an object is excluded from offline work -- neither editable
    while disconnected nor available to be checked out.

    Args:
        obj (Identifiable):  the object

    Returns:
        bool:  True if the object is an instance of an excluded class
    """
    classes = tuple(orb.classes[cname] for cname in offline_excluded
                    if cname in orb.classes)
    return bool(classes) and isinstance(obj, classes)


def get_checkout_holder(obj):
    """
    Get the userid of the user currently holding a check-out claim on an
    object, or '' if it is not claimed.

    Reads state['checkouts'], which mirrors the repository's active CheckOut
    records in the form {oid: {'userid': str, 'expiry_datetime': str,
    'purpose': str}}.  Both ends maintain it:  the client refreshes it from
    vger.get_checkouts() at sync and updates it from the "checked out" /
    "checked in" pubsub messages; vger maintains its own copy as claims are
    granted and released.  Keeping one shape means this function -- and
    therefore get_perms() -- has a single code path on both sides.

    Args:
        obj (Identifiable):  the object

    Returns:
        str:  the holder's userid, or '' if unclaimed
    """
    oid = getattr(obj, 'oid', '')
    if not oid:
        return ''
    return ((state.get('checkouts') or {}).get(oid) or {}).get('userid', '')


def is_writable_now(obj, user):
    """
    Answer the *exclusivity* question:  may this user write to this object
    right now?

    This is deliberately separate from *entitlement* -- whether the user may
    ever edit the object at all, which is a matter of creator/role/ownership
    and is decided by the rest of get_perms().  Connectivity and check-out
    claims have nothing to say about entitlement; they say only whether it is
    safe to exercise it at this moment.  See
    pangalactic.core/NOTES_ON_CHECKOUT_MODEL.md section 5, which describes the
    conflation of these two questions as the source of the offline permission
    defects this replaces.

    The rules:

      [1] A claim is **exclusive**.  While an object is checked out, only the
          holder may write to it -- online or offline, and **including a
          Global Administrator**.  This is a deliberate change from the
          previous "global admin is omnipotent at the data-access layer"
          stance (author, 2026-08-02):  it parallels the frozen-object rule,
          where even a GA gets no Edit button.  The difference is that freeze
          can be enforced in the object editor, because that is the only way
          in, whereas a claim must also hold against vger.save() -- so it has
          to be enforced here.  A GA who needs the object force-releases it
          with vger.release() and then edits it, exactly as they would thaw a
          frozen object first.

      [2] The server may always write to an unclaimed object;  it is applying
          changes on behalf of callers whose own permissions were already
          checked.

      [3] A connected client may write to an unclaimed object, as before.

      [4] A disconnected client may write only to objects it created itself
          and the repository has never seen (state['locally_created_oids']).
          This replaces the old "object_not_synced" test, which was derived
          from state['synced_oids'] -- a list of only the user's *own*
          objects -- and so granted offline write access to precisely the
          objects the user had NOT created.  See NOTES_ON_OFFLINE_AND_SYNC.md
          section 2.

      [5] **The objects a timeline is made of are never writable while
          disconnected** -- not even a locally created one, and not on the
          strength of a claim (author, 2026-08-21).  See
          `offline_excluded` above for which classes and why:  in short, a
          timeline does not decompose into independently editable parts, so a
          claim on one of them would not cover the work it enables.
          PrepareForOfflineDialog does not offer them and vger.check_out()
          refuses them, both by way of is_offline_excluded().

          Revisit if a priority use case for offline timeline work appears.

    Args:
        obj (Identifiable):  the object
        user (Person):  the user

    Returns:
        bool:  True if the user may write to the object at this moment
    """
    client = bool(state.get('client'))
    if client and not state.get('connected') and is_offline_excluded(obj):
        # [5] first, and unconditionally:  a timeline object cannot be edited
        # offline whatever else is true of it, including a claim that
        # predates this rule
        return False
    holder = get_checkout_holder(obj)
    if holder:
        # [1] claimed: the holder, and only the holder
        return holder == getattr(user, 'id', '')
    if not client:
        # [2] server
        return True
    if state.get('connected'):
        # [3]
        return True
    # [4] disconnected client, unclaimed object
    oid = getattr(obj, 'oid', '')
    return bool(oid) and oid in (state.get('locally_created_oids') or [])


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
            'add docs'
            'add models'
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
        perms = ['view', 'modify', 'delete', 'add docs', 'add models',
                 'local admin or permissive']
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
        return ['view', 'Acu in frozen assembly is frozen']
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
    if is_reference_data(obj):
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
    # ------------------------------------------------------------------
    # NOTE: "server_or_connected_client" (and the "object_not_synced" test
    # derived from state['synced_oids']) used to gate every grant of
    # modify/delete below.  Both are replaced by is_writable_now(), which
    # answers the same question -- may this user write *right now* -- but
    # takes check-out claims into account and fixes the inverted offline
    # test.  Entitlement (creator / admin / role+product_type) is unchanged
    # and is still decided by the branches below.
    # See NOTES_ON_CHECKOUT_MODEL.md section 5.
    # ------------------------------------------------------------------
    writable_now = is_writable_now(obj, user)
    if is_global_admin(user):
        # NOTE: a global admin is no longer omnipotent here.  They remain
        # entitled to everything, but a check-out claim held by someone else
        # withholds write access from them too, exactly as a freeze does --
        # see is_writable_now() [1].  The remedy is vger.release(), the
        # counterpart of thaw.
        perms = ['view', 'add docs', 'add models']
        if writable_now:
            perms += ['modify', 'add docs', 'add models', 'delete']
        # orb.log.debug('  perms: {}'.format(perms))
        if debugging:
            perms.append('global admin perms')
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
            if writable_now:
                perms += ['delete', 'add docs', 'add models', 'modify']
            # orb.log.debug('  perms: {}'.format(perms))
            if debugging:
                perms.append('object creator perms')
            return perms
        # --------------------------------------------------------------------
        # NOTE: THIS SETS ROLE_IDS FOR PROJECT-OWNED ITEMS:
        # only users with an appropriate discipline role assigned in the
        # context of the project (obj.owner) have "modify" permission
        # --------------------------------------------------------------------
        role_ids = set()
        if isinstance(obj, orb.classes['ManagedObject']):
            ras = orb.search_exact(cname='RoleAssignment',
                                   assigned_to=user,
                                   role_assignment_context=obj.owner)
            role_ids = set([ra.assigned_role.id for ra in ras])
        # --------------------------------------------------------------------
        # NOTE: THIS OVERRIDES ROLE_IDS FOR NON-PROJECT (I.E. REUSABLE) ITEMS:
        # users with an appropriate discipline role in ANY context (not just
        # the "owner" context) have "modify" perm for the object -- so ANY
        # discipline engineer can help maintain reusable library items in their
        # discipline!
        # --------------------------------------------------------------------
        if (isinstance(obj, orb.classes['HardwareProduct'])
            and not isinstance(obj.owner, orb.classes['Project'])):
            ras = orb.search_exact(cname='RoleAssignment',
                                   assigned_to=user)
            role_ids = set([ra.assigned_role.id for ra in ras])
        # From here on, access depends on roles, product_types, and "public"
        # status of the object
        TBD = orb.get('pgefobjects:TBD')
        # [1] is the object a Product?
        if isinstance(obj, orb.classes['Product']):
            # orb.log.debug('  - object is a Product ...')
            if not obj.owner:
                # orb.log.debug('    owner not specified -- view only.')
                return ['view', 'add docs', 'add models']
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
                    perms = ['view', 'add docs', 'add models']
                    if frozen:
                        # orb.log.debug(f'* object {obj.oid} is frozen.')
                        return perms
                    if writable_now:
                        # mods and deletions are only allowed on the server or
                        # a connected client
                        perms += ['modify', 'delete']
                    if debugging:
                        perms.append('role-based product type perms (HW)')
                    # orb.log.debug('  perms: {}'.format(perms))
                    return perms
                else:
                    if obj.public:
                        # txt = ' "public" -- any user can add docs/models'
                        # orb.log.debug(txt)
                        perms = ['view', 'add docs', 'add models']
                    else:
                        # txt = f'  unauthorized to modify ProductType "{pt_id}"'
                        # orb.log.debug(txt)
                        perms = ['view']
                    # orb.log.debug('  perms: {}'.format(perms))
                    if debugging:
                        perms.append('role-based product type perms (HW)')
                    return perms
            else:
                # ------------------------------------------------------------
                # A Product that is NOT a HardwareProduct:  a Model, a
                # Document, a Template.  Product type has nothing to say
                # about these -- the discipline logic above is about who may
                # engineer a subsystem -- so access follows ownership alone:
                # ANY user with a role in the organization that owns the
                # object may see it, and may attach documents and models to
                # it.
                #
                # There was no branch here at all until 2026-08-29 (author's
                # rule).  A cloaked Model or Document therefore matched
                # nothing in this block and fell through to [7], which
                # returns the accumulated perms -- and 'view' is seeded above
                # only for a Product that is public.  So no member of the
                # owning project had even 'view' on their own project's
                # models and documents;  only the creator, by the branch
                # above, and a global admin.
                #
                # Nothing depended on that until vger.download_chunk() began
                # asking, and then a project's files were withheld from the
                # project:  a STEP import synced its products to the other
                # members and its files reached none of them.
                #
                # 'modify' and 'delete' are deliberately not granted.  The
                # creator keeps them by the branch above;  for anyone else,
                # changing another user's model or document is not implied by
                # membership of the project.
                # ------------------------------------------------------------
                if role_ids:
                    perms = ['view', 'add docs', 'add models']
                    if debugging:
                        perms.append('role-based owner perms (non-HW Product)')
                    # orb.log.debug('  perms: {}'.format(perms))
                    return perms
                # no role in the owner:  fall through to [7], which answers
                # 'view' if the object is public and nothing if it is not
        if isinstance(obj, orb.classes['Requirement']):
            # Requirements (subclass of ManagedObject) are a special case
            rqt_mgrs = set(['Administrator', 'systems_engineer',
                            'lead_engineer'])
            if rqt_mgrs & role_ids:
                perms = ['view', 'add docs']
                if writable_now:
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
                if writable_now:
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
                if writable_now:
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
                    if writable_now:
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
                if writable_now:
                    perms += ['modify', 'add docs', 'delete']
                # orb.log.debug('    perms: {}'.format(perms))
                if debugging:
                    perms.append('[3] role-based perms (PSU)')
                return perms
        # [4] is it a Port?
        elif cname == 'Port':
            # access will depend on the user's permissions on 'of_product'
            perms = get_perms(obj.of_product, user=user,
                              permissive=permissive, debugging=debugging)
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
                s = set(get_perms(obj.start_port_context, user=user,
                                  permissive=permissive, debugging=debugging))
                s |= set(get_perms(obj.end_port_context, user=user,
                                   permissive=permissive, debugging=debugging))
                s |= set(get_perms(obj.end_port.of_product, user=user,
                                   permissive=permissive, debugging=debugging))
                s |= set(get_perms(obj.start_port.of_product, user=user,
                                   permissive=permissive, debugging=debugging))
                perms = list(s)
                # orb.log.debug(f'  perms: {perms}')
            except Exception:
                # perms could not be determined
                orb.log.debug('* get_perms() encountered an exception:')
                orb.log.debug(f'  {traceback.format_exc()}')
                perms = []
            if debugging:
                perms.append('[5] role-based perms (Flow)')
            return perms
        # [6] is it an Activity?
        elif isinstance(obj, orb.classes['Activity']):
            ras = orb.search_exact(cname='RoleAssignment',
                                   assigned_to=user,
                                   role_assignment_context=obj.owner)
            roles = set([ra.assigned_role.id for ra in ras])
            auth_roles = set(['administrator', 'lead_engineer',
                              'systems_engineer'])
            if roles & auth_roles:
                # orb.log.debug('  - user is authorized by role(s) ...')
                # orb.log.debug('    {}'.format(list(roles & auth_roles)))
                perms = ['view', 'add docs']
                if writable_now:
                    perms += ['modify', 'delete']
                # orb.log.debug('    perms: {}'.format(perms))
                if debugging:
                    perms.append('[6] role-based perms (Activity)')
                return perms
            # otherwise, perms are those of the "of_system"
            elif getattr(obj, 'of_system', None):
                return get_perms(obj.of_system, user=user,
                                 permissive=permissive, debugging=debugging)
        # [7] if none of the above, return whatever perms have accumulated
        else:
            return list(perms)
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


def get_owner_id(obj):
    """
    Get the id of the organization or project that owns an object, following
    the same delegation `is_cloaked()` uses:  objects that are not themselves
    owned take their owner from the object they are subsidiary to.

    Used by the repository service to decide which project channel an object's
    "new" or "modified" notification should be published on.  An object whose
    owner cannot be resolved is not published to any project channel, so a
    class that reaches this function and falls through will sync only on the
    next full sync, not in real time.

    Args:
        obj (Identifiable):  the object

    Returns:
        str:  the owner's id, or '' if none could be resolved
    """
    if obj is None:
        return ''
    if hasattr(obj, 'owner'):
        return getattr(obj.owner, 'id', '') or ''
    elif isinstance(obj, orb.classes['ProjectSystemUsage']):
        return get_owner_id(getattr(obj, 'system', None))
    elif isinstance(obj, orb.classes['Acu']):
        return get_owner_id(getattr(obj, 'assembly', None))
    elif isinstance(obj, orb.classes['ContextDependentShapeRepresentation']):
        return get_owner_id(obj.represented_usage)
    elif isinstance(obj, orb.classes['Axis2Placement3D']):
        for cdsr in (obj.placement_of or []):
            owner_id = get_owner_id(cdsr)
            if owner_id:
                return owner_id
    elif isinstance(obj, orb.classes['RepresentationFile']):
        # a file takes its owner from what it is a representation of.
        # RepresentationFile descends from DigitalFile, not ManagedObject, so
        # it has no owner of its own -- and without this it fell through to
        # '' and was published on no project channel at all.
        return get_owner_id(getattr(obj, 'of_object', None))
    return ''


def may_fetch_file(rep_file, user):
    """
    Say whether a user may be given the bytes of a file.

    **The file's own permissions cannot answer this.**  RepresentationFile is
    in `modifiables`, so every user has view, modify and delete on one;  a
    gate built on that would authorize everybody.  What decides is the object
    the file represents -- "authorization is the model's, since that is what
    gains a file", as vger.add_component_file() puts it -- so this asks
    get_perms() about `of_object`.

    That is only a sound question because a Product which is not a
    HardwareProduct now has a role-based branch in get_perms().  Until
    2026-08-29 it had none, so a cloaked Model or Document answered the empty
    set to everyone but its creator, and this gate -- which did ask
    get_perms() -- withheld a project's own files from the project.  The
    first repair was to reimplement the rule here, in terms of is_cloaked()
    and a role lookup;  the author's is better, and this defers to it:  one
    definition of who may see an object, which the bytes then follow.

    Args:
        rep_file (RepresentationFile):  the file whose bytes are wanted
        user (Person):  the user asking

    Returns:
        bool:  True if the user may be given the file
    """
    if user is None or rep_file is None:
        return False
    subject = getattr(rep_file, 'of_object', None)
    if subject is None:
        # a file that represents nothing has nothing to inherit access from,
        # and nothing in the application makes one
        return False
    return 'view' in get_perms(subject, user=user)


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
    elif isinstance(obj, orb.classes['ContextDependentShapeRepresentation']):
        # cloaking for a shape representation is determined by the usage it
        # positions -- the geometry of a cloaked assembly is as proprietary
        # as the assembly is
        return is_cloaked(obj.represented_usage)
    elif isinstance(obj, orb.classes['Axis2Placement3D']):
        # a placement has meaning only through the representations that use
        # it; it is cloaked if any of them is
        return any(is_cloaked(cdsr) for cdsr in (obj.placement_of or []))
    elif isinstance(obj, orb.classes['RepresentationFile']):
        # cloaking for a file is determined by what it represents:  the CAD
        # file of a cloaked assembly is as proprietary as the assembly.
        #
        # Without this branch a RepresentationFile fell through to the final
        # "not a ManagedObject, so public" case, because `public` is declared
        # on ManagedObject and DigitalFile is not one.  That did not matter
        # while these objects were only ever created by
        # vger.add_update_model(), which publishes on the owner's channel
        # directly;  it matters as soon as they arrive through vger.save(),
        # which asks this.
        #
        # It mattered more when this was written:  vger.download_chunk()
        # authorized nothing, so the oid of a file *was* access to the file,
        # and publishing a cloaked file's oid on the public channel handed it
        # out.  That rpc now asks may_fetch_file() (2026-08-29), which asks
        # this -- so the two agree by construction:  the channel an object is
        # published on and the people who may fetch its bytes are decided by
        # the same answer.
        return is_cloaked(getattr(obj, 'of_object', None))
    elif hasattr(obj, 'public') and not obj.public:
        return True
    else:
        # if object is not a ManagedObject, Acu, or PSU, it is public
        # orb.log.debug('  object is public.')
        return False

