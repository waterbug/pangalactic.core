# NOTES ON COLLABORATION ARCHITECTURE

## Projects

  - a project can serve as a single-user workspace or a multi-user
    collaboration, and a single-user project can potentially be "converted"
    into a multi-user collaborative space if/when desired.

  - the PGER repository service (see below) will publish project-related events
    on project channels named as `pger.[project.id]`

  - PGER will maintain a runtime cache of references to "objects of interest"
    to a project (e.g. products used on the project, assembly relationships and
    other relationships between objects used on the project, etc.) and will
    send events pertaining to those objects (e.g. decloak, modify) to the
    project channel.

  - new projects:

    + when connected, call admin tool to create it and get the admin role.
    + if project was created when not connected, create and sync it when
      connected, and get the admin role.

## Client (Pangalaxian)

  * Login ->
    - `pger.get_role_assignments`
    - sync current project (if one is selected) and user's SANDBOX
    - identify all projects / orgs user currently has RoleAssignments on
    - subscribe to pubsub channels
      + check whether user is subscribed to the pubsub channels for all
        their assigned projects and orgs (and subscribe to any not already
        subscribed)

  * Select Project [using Project selector]
    - sync the selected project

## Virtual Galactic Entropy Reverser (VGER) Repository Service Interface

  * RPC

    - `pger.get_object(oid)`
    - `pger.save(objects)`
    - `pger.modify(oid, **kw)`
    - `pger.decloak(obj.oid, actor.oid)`
    - [for testing only]
      `pger.get_role_assignments()`
      -- return data mimics the structure of
      `pgefadmin.state.query`

  * Pub/Sub

    - a pub/sub channel is created for each Organization and Project, and also
      a "public" channel
    - channel names are of the form:  `pger.[org/project]`
    - message structures are of the form:  {subject: content}
      + `{u'decloaked': [obj.oid, actor.oid]}`
      + `{u'modified':  [obj.oid, str(obj.mod_datetime)]}`

## Person / Role / Organization Service (PROS) Interface

  * RPC

    - `create_project(id=None, name=None)`

  * Pub/Sub

    - `role_assignment({project, user, roles_added, roles_revoked})`

         where ...  

           project: oid  
           user: oid  
           roles_added: list of oids  
           roles_revoked: list of oids

    - `role_list({change=[add|edit|delete], role=None})`
      where
        role: oid

    - `new_project()`

## Authorization and Access Control

  * access.py (object access)

    - public objects are accessible to any authenticated user.

    - any non-public object is only accessible to projects to which it has been
      explicitly "decloaked".

    - an object that has been decloaked to a project is only accessible to
      project users when it has been used somewhere (i.e. in an assembly or as
      a top-level system) on the project.

