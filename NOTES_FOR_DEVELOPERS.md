# PANGALACTIC DEVELOPER NOTES

## Structure of the `pangalactic` Namespace Packages

### `core`: base pangalactic package: ontology, registry, orb, reference data
  - `ontology ... pgef.owl [file in OWL format]`
  - `test ....... unit tests`
    + `data ..... test data files`
    + `vault .... test data files [copied to app_home/vault]`
  - `utils ...... general utility modules`

### `node`: GUI client package
  - `cad ........ CAD modules`
  - `diagrams ... block diagram modules`
  - `icons ...... app icons [copied to app_home/icons]`
  - `images ..... app images [copied to app_home/images]`
  - `test ....... GUI test client`

### `vger`: network repository service
  - `vger ........ repository service interface`
  - `userdir ..... LDAP directory search interface`

## Contents of App Home Directory (`[app]_home`) created at start-up

* holds configuration data (some of which may be user-specific) that
  persists when a new version of the app is installed

* note that if schemas change between versions, some of this data may need
  to be modified to conform to the new schemas

    `cache/ ............ internal metadata structures (used by registry)`

    `config ............ config file (yaml) -- see *Settings* section below`

    `diagrams.json ..... diagram geometry storage`

    `icons/ ............ "built-in" icons (icons generated at runtime are saved
                         in vault/icons; all other data files are simply
                         added to the `vault` directory`)

    `images/ ........... images  (application-specific images)`

    `local.db .......... node local object store (sqlite db)`

    `log/ .............. logs`

    `onto/ ............. contains pgef.owl (OWL ontology file)`

    `parameters.json ... parameter storage`

    `prefs ............. saved preferences (yaml) -- see *Settings* section below`

    `server_cert.pem ... certificate for message bus host (enables TLS connection)`

    `state ............. saved state (yaml) -- see *Settings* section below`

    `test_data/ ........ files for user access in testing of data importing, etc.`

    `trash ............. trash file (yaml) containing serialized deleted objects
                         {obj.oid : orb.serialize([obj]), ...}`

    `vault/ ............ files created/accessed internally by pangalactic
                         applications (includes icons generated at runtime and
                         files referenced by the database, e.g. files
                         corresponding to DigitalFile objects)`

## Settings

* config
    admin_package_name: (str)  name of admin package
    admin_script_name:  (str)  name of admin script
    app_channel:        (str)  app channel url or name
    app_name:           (str)  app name
    app_package_name:   (str)  app package name
    dashboards:         (dict) named dashboards (lists of parameter ids)
    dashboard_names:    (list) ordering of keys in `dashboards`
    db_url:             (str)  sqlalchemy-style db url (only used by vger)
    default_parms:      (list) ids of default parameters to assign to objs
    host:               (list) fqdn of message bus host
    local_admin:        (bool) if `true`, user can edit any item locally
    load_extra_data[2]: (list) names of files containing data to load
    logo:               (str)  logo icon file name
    p_defaults:         (dict) default parameter values {id: val (string)}
    port:               (str)  port to use for message bus host connection
    tall_logo:          (str)  "tall" logo icon file name
    units:              (str)  unit system (default: 'mks')

* prefs
    dashboards:         (dict) named dashboards (lists of parameter ids)
    dashboard_names:    (list) ordering of keys in `dashboards`
    default_parms:      (list) ids of default parameters to assign to objs
    editor:
        parameters:     (list) [ids] order of parameters in pgxnobject panels
    model_types:        (list) oids of ModelTypes that pangalaxian can "render"

* state
    admin_of:         (list) oids of Projects in which user has admin role
    assigned_roles[3]: (dict) maps proj/org oids to assigned role names for user
    cloaked:          (list) oids of local cloaked objects
    connected:        (bool) true if logged in to message bus
    current_cname:    (str)  name of currently selected db table class
    dashboard_name:   (str)  name of currently selected dashboard
    dataset:          (str)  name of currently selected dataset
    datasets:         (list) names of currently stored datasets
    height:           (int)  pixel height of pangalaxian gui
    width:            (int)  pixel width of pangalaxian gui
    disabled:         (bool) true if user has `Disabled` role (global)
    height:           (int)  current pixel height of pangalaxian gui
    icon_type:        (str)  suffix for platform-specific icons [e.g., '.ico']
    last_path:        (str)  most recent path in file selections
    local_user_oid:   (str)  oid of Person object for local user 
    mode:             (str)  current Pangalaxian gui mode (e.g. 'system')
    product:          (str)  oid of currently selected Product
    project:          (str)  oid of currently selected Project
    role_oids[4]:     (dict) maps names of Roles to their oids
    synced[5]:        (bool) keeps track of whether session has been synced
    synced_oids[6]:   (list) oids of user-created objects that have been synced
    synced_projects[7]: (list) oids of projects that have been synced
    sys_trees[8]:     (dict) maps project ids to system tree attributes
    userid:           (str)  most recent userid used in login
    version:          (str)  version of client
    width:            (int)  current pixel width of pangalaxian gui

    [2]: `load_extra_data` is intended for use primarily on the server (vger)
         for special data not included in `refdata`, such as data specific to
         local organizations, etc.

    [3]: `assigned_roles` data structure:

        {project oid: [list of names of assigned roles on the project]}

        NOTE:  for project-independent role assignments, 'global' is used in
        place of a project oid.

    [4]: `role_oids` data structure:

        {role name : role oid}

    [5]: `synced` is set to False when the mbus is first joined upon login, and
         set to True when initial sync operations are completed.  (This enabled
         sync operations to be factored into a separate `sync_with_services`
         method so it could be called by `check_version`, which is only done on
         Windows [the `win32` platform] for now.)

    [6]: the "synced_oids" list is used in determining whether an object may be
         deleted while the client is offline (not connected to the repository):
         any object that has been synced to the repository *cannot* be deleted
         while offline, because it may be used in an assembly by another user
         and deleting it before removing it from the assembly would break
         referential integrity.

    [7]: Projects only need to be synced when a project is first used during an
         online session because objects may have been added, deleted, or
         modified while the user was offline. During a session, the bulk
         project sync is only done once because during the online session all
         objects are kept in sync by messages. The "synced_projects" list is
         used to keep track of which projects have been synced during the
         current online session.  The 'vger.sync_project' rpc is only called
         when the user selects a project using the project selector -- after
         the sync completes, the oid for that project is added to
         "synced_projects".  The "synced_projects" list is cleared when the
         session ends.

    [8]: `sys_trees` data structure:

        {project id : {nodes : (int) # of nodes in sys tree (used in
                               calculating progress bar for tree rebuilds)
                       expanded : (list) indexes of expanded nodes in sys tree
                                  (used in restoring state when tree is rebuilt)
                      }}

## Modes and Views

* Modes are set by selecting one of the mode icons at top right corner of the
  main window
* `mode` is a state of the main pangalaxian main window
* `view` [not implemented yet] is orthogonal to `mode`, set using `view` combo

### Modes

mode            context                     types
----            -------                     -----
System          system modeler              Mission, System
Component       component modeler, library  Part, etc.
Data            datasets                    DataSet
DB              database                    All Types
Admin           admin                       Project, Mission Study, Role

#### Mode: `data`

* Operates on flat `DataSet` instances

  + MainWindow layout:
    - if no datasets ... left: `No Data`, center: empty
    - if 1 dataset ..... left:  metadata, center: data table
    - if > 1 dataset ... left:  metadata of selected ds, center: data table

* `DataSet`: data that is typically imported from some external source --
  usually from a file.

* represented internally as pandas DataFrame (hdf5) or xray DataSet
  (multi-dimensional with units, etc.)

* saved as HDF5

* To be implemented:

  - [possibly] use `xray` `Dataset` to represent `pgef` `DataSet`

  - unit conversion

  - have a DataSet reference object in db, referencing its serialized form
    (can this be queried using Blaze?)

  - operations on DataSets, to be supported by wizards:

    * join datasets
    * map a dataset into a type (i.e. collection of objects of a
      specified type -- e.g. Requirement)

  - DataSet Properties:

    * name:     string identifier
    * source:   file name/path or other url / location identifier
    * target:   serialized file or db name / table / file (.db)
    * sheet:    for excel files, the sheet name
    * mapping:  [fk] names of fields/columns in file mapped to table name/column(s)
                and types
    * key:      (optional) primary key column
    * dtstamp:  date/time imported

#### Mode:  `db`

* View/edit objects in local db

#### Modes:  `system` and `component`

* Component Modeler and System Modeler

* Create/modify systems and component models
  + MainWindow layout:
    - if no models ... left: `No Model`, center: empty
    - if 1 model ..... left:  tree structure + metadata,
                       center: diagram
    - if > 1 model ... left:  tree structure + metadata of selected model,
                       center: diagram

### Views [not implemented yet]

view            context                     types
----            -------                     -----
Documentation   docs                        Document + subtypes
Requirements    reqt mgt                    Requirement
Models          models                      Model
DataSets        data                        DataSet

## Diagrams (used in `system` and `component` modes)

* See `NOTES_ON_DIAGRAMS`

## Application-level Signals (louie)

The `louie` package provides the capability to broadcast signals among any
objects active within a python application.  This mechanism can be used, e.g.,
for propagating events related to context items [`mode`, `project`, `system`,
etc.]

Note that in pangalactic, `louie` is used *only* on the client side

* define a signal:
    dispatcher.connect(handler, signal_name)`,
  where `handler` is a callable and `signal_name` is a string -- e.g.:  
  `dispatcher.connect(self.on_deleted_object_signal, 'deleted object')`

* create senders for signals in context of item events  
  e.g., `deleted object` (of some type):  
  `dispatcher.send(signal='deleted object', [kwargs for signal content])`

* create handler functions to trigger respons(es) to the signal  
  e.g., `on_deleted_object_signal([kwargs for signal content])`

* NOTE: signals are used in some `pangalaxian.Main` `property` constructs:
  - setter dispatches the signal `[item] changed`
  - getter gets the value from `state["item"]`

## Random notes on the orb

(0) the orb is used on both the client and server sides, so it must be kept
    free of:
    * 'louie' events -- they are used *only* in the client gui environment
    * `local_user` -- exists solely in the client environment
    * any awareness of the network or network-related events

(1) orb.save() *NEVER* changes the `mod_datetime` of objects, because it
    saves both local objects and those received from remote sources --
    therefore, locally created or modified objects must be time-stamped before
    they are passed to orb.save().

(2) orb.clone() *ALWAYS* sets the `mod_datetime` of the clone

## Behavior of Project and System selector states

* Project selector
  - component mode:  any Parts or Models created will have the selected
                     Project as their `owner` (person creating them will be
                     `creator`)
  - systems mode:    left dock systems tree will be for the selected Project
                     (if no system is selected -- see below)

* System selector
  - component mode:  not visible [may change if needed]
  - systems mode:    selected system will be shown as root of left dock
                     systems tree

## Representation of Many-to-Many Relationships in the UI

* the PGEF ontology contains several m2m (many-to-many) relationships, which
  are represented using a "reified" relationship class (a.k.a. in database
  parlance a "join object").  For example, the `Acu` (Assembly Component Usage)
  class represents a many-to-many relationship between `Product` instances, in
  which the assembly `Product` is built from one or more component `Product`
  instances, and an `Acu` exists for each assembly-component relationship
  between 2 `Product` instances.

  For all many-to-many relationship classes in PGEF, once the m2m class is
  defined, 4 "Object Properties" are defined:  2 of the properties are from the
  relationship object to each of the related instances and the other 2
  properties are the inverses of the first 2 properties.

  To make this more concrete, here are the 4 properties for `Acu`:

    property/attribute      domain             range
    ------------------      ------             -----
  - `assembly`:             Acu             -> Product (assembly)
    1 to 1 (directly populated)
  - `component`:            Acu             -> Product (used in assembly)
    1 to 1 (directly populated)
  - `components`:           Product         -> Acu
    1 to many: inverse of `assembly` property (computed by sqlalchemy)
  - `where_used`:           Product         -> Acu
    1 to many: inverse of `component` property (computed by sqlalchemy)

* The two 1-to-1 attributes are simply the two "sides" of the Acu relationship,
  its `assembly` and `component` properties.  The 1-to-many attributes are
  "computed attributes", which are automatically implemented using SqlAlchemy
  when the `PanGalacticRegistry` and `KM` translate the ontology into runtime
  classes.

* Only one of the 1-to-many attributes should be used to implement the user
  interface through which the 1-to-1 "join" objects are created.  Since it
  isn't possible to algorithmically determine which of the 1-to-many properties
  to use for the UI widget, those properties will be defined in
  `p.meta.defaults.M2M_PROPERTIES`, which will be used when constructing the UI
  elements.

* Note that the 1-to-many attribute *itself* will not be editable -- it is
  computed -- but rather the object editor will have a "drop zone" widget
  associated with the 1-to-many attribute.  The default widget will be an
  editable list widget (QListWidget) into which object instances can be
  dropped, which triggers the creation of an instance of the m2m object that
  links the object being edited to the object that was dropped onto it.

## Parameters / ParameterDefinitions

The object dropped onto the `Parameters` list widget in the Component Modeler
is a ParameterDefinition (not a Parameter), which will trigger the creation
of a Parameter instance of the type specified by the ParameterDefinition,
along with a ModelParameter object linking the Model with the new Parameter.
The drop area will be a simple panel, on which the drop will trigger a data
field widget to be created in which the Parameter value can be displayed and
edited.  It will also be possible to remove the data field widget (which will
destroy the associated Parameter and ModelParameter objects) by a right-click
menu option (or something else TBD).

## Domain Objects

### Versioning Scheme

* A canonical versioning scheme will be used by default but the user is allowed
  to customize it within limits

* If an object has a `version` attribute:
  - its use is optional (if not populated the object is not versioned)
  - if the object is to be versioned, its `id` attribute should remain the same
    across all versions

* Canonical versioning:
  - the canonical scheme uses `0` as the initial version, and sequential
    integers for subsequent versions.
  - the canonical scheme uses `0` as the initial iteration, and sequential
    integers for subsequent iterations.

* Customized versioning:
  - the user can specify any string for the version attribute, and the system
    will set and increment the `version_sequence` attribute with an integer
    that tracks the sequence of versions
  - iterations are numbered the same as in the "canonical" scheme

* "Freezing" versions and creating new versions:
  - the object viewer/editor (PgxnObject) provides [TODO!] a `freeze` button
    that will put the object into a temporary `frozen` state.
  - a `frozen` object can be `thawed` to make corrections but is otherwise
    not editable

### Authorization / Object Access 

#### Read (View) Access

Read access is only controlled for `ManagedObject` instances and their related
objects (`Model`, `DigitalFile`, etc.) -- all other objects are visible to
everyone.

Read access to `ManagedObject` instances and objects related to a
`ManagedObject` is determined by

(1) the `public` attribute:
    - if True, read access is granted to the world
    - if False, read access is controlled by `ObjectAccess` relationships
(2) `ObjectAccess` relationships:
    - an ObjectAccess instance reifies the relationship between a
      ManagedObject and the Actors (Organizations, Projects, etc.) that have
      been granted read access to the ManagedObject.

If a Person has been assigned a Role in an Organization that has been
granted access to a ManagedObject (i.e. via an ObjectAccess instance), then the
Person has *read* access to the ManagedObject instance and its related objects.

* The `creator` of a `ManagedObject` instance can `decloak` the object to an
  `Organization` or to the world -- the `decloak` function creates an
  `ObjectAccess` instance for which the `grantee` is an Organization and the
  `accessible_object` is the object; if the `grantee` is `None`, read access to
  the object is granted to the world.

* A `Person` who has a `RoleAssignment` in the context of an `Organization` is
  granted read access to any `ManagedObject` that has been decloaked to that
  Organization and to any relationships (e.g. Acu) for which both related
  `ManagedObjects` are accessible.

The authoritative source for data on roles and role assignments will typically
be an administrative service, unless the repository is fulfilling the role of
the administrative service.  Therefore, because operations to sync such data
are expensive, the data are cached in `state` variables rather than stored in
the local db.

#### Write (Edit) Access

The following conditions must be met for Person A to have permission to edit
Object X:

  * Person A is the `creator` of Object X

  OR

  * Object X is owned by Organization Z

  AND EITHER

  * Person A is assigned the Administrator Role in Organization Z

  OR

  * Person A is assigned a Role in Organization Z that is associated
    with Discipline D that uses Products having the Product Type of
    Product X.

### Object Viewer / Editor:  PgxnObject

* module:  pangalactic.node.gui.pgxnobject

* Object editor that can view or edit any `PanGalactic` domain object
  - the `Edit` button will only be visible if the user has `write` access (for
    now, that means the user must be the `creator` of the object)
  - can be used as a dialog or an embedded widget -- e.g., the left dock panel
    in component (`Component Modeler`) mode.
  - validation uses `p.meta.meta.PGXN_REQD` -- a dictionary that maps class
    names to lists of required fields (required -> not allowed to be null)

* PgxnObject is highly configurable -- for more detail, see documentation
  within the p.n.g.pgxnobject module

### Object Deletions

* A user with `write` access to an object can use the Object Editor to delete
  the object if it is not used in any assemblies or projects.

* The deletion process removes the object from the session and the database
  (see below for details) after serializing the object and adding it to the
  `pangalactic` module-level list variable `trash`, which is managed by the
  orb.  `trash` is managed in the same way as the module-level variables
  `config`, `prefs`, and `state`.

* The behavior of `Delete` differs for online and offline states:

  - Offline: the object is serialized and appended to `trash`, an in-memory
    list of serialized objects, and deleted from the local db and the current
    session.

  - Online: in addition to the offline behavior, the object is deleted from the
    repository.

  - Upon login, when the local user's objects are synced, any objects in the
    repository that were created by the local user and neither exist locally
    nor are present in the user's trash are pushed to the client (i.e., any
    locally "missing" objects created by the user are "restored").

## Installation and Configuration of Crossbar

[TBD]

## Configuration for Testing the Client with a Local Crossbar and Repo Service

The `Pangalaxian` desktop application can be tested using a local crossbar
server and repository service (`pangalactic.repo.pger`) by configuring it as
follows:

0. start up the client (which creates its home directory)
1. stop the client and cd to its home directory
2. copy or link the local crossbar server's `server_cert.pem` file to the
    client's home directory, replacing any `server_cert.pem` that was there.
3. edit the `config` file:
    - set 'host' to 'localhost'
    - set 'port' to the port that crossbar is running on
4. start up the client again using the flags:
    - '-t' (test mode)
    - '-d' (debug level logging)
    - '-n' ('pger' will stand in for the admin service)

You should now be able to log in to your local crossbar and access your local
repository service.


## Package Installation and Management

The `conda` package manager is used to manage the installation and updating of
`pangalactic` for both the client and server.

### Client Installation and Updates

For the Windows platform, `conda-constructor` is used to create an installer
for the client package.  When run, the installer creates a `conda` installation
(which includes `conda` itself) in the user's home directory.  

The client includes a self-updating mechanism that can be invoked from the menu
by the user and will use conda to check for updates to the package in the
pre-configured `conda` repository.  The client update process works as follows:

#### Server-Initiated

0.  upon login, client issues rpc checking for new version release
1.  server response includes new release metadata with `schema_changed` flag
2.  if schema changed:
    - serialize all objects (db-independent form)
    - backup the serialized objects (old schema) into yaml file(s)
3.  install new version
4.  restart cattens (i.e. tell user to restart; offer to exit now)
5.  at startup, the client compares its `state['schema_version']` to the
    package version and, if different, it checks whether the schema has been
    modified (same as step 1); if it has, the client looks for a serialized
    data file.
6.  if a serialized data file is found, the client checks to see if the current
    version is found in the `mappings.fns` dictionary; if it is, the client
    imports the serialized data and runs the conversion function
    `mappings.fns[version]` on the data, then deserializes it; if the version
    is not found in the `mappings.fns` dictionary, it means that no conversion
    function is required for the schema mod, so the data is simply deserialized
    as is (which loads it into the db).

#### Client-Initiated

0.  the client package is updated, either by:
    [a] the client's menu item "Tools/Update <client name>..." or
    [b] by using `conda update <client name>..." at the command line
1.  the client reloads the `mapping` module and checks whether the package
    version is in the `mappings.schema_mods` version list -- if so, its schema
    has been modified
2.  if the schema changed, the client serializes all db data to a file
3.  restart cattens (i.e. tell user to restart; offer to exit now)
4.  replicate steps [5] and [6] above.

### Repository Service Installation and Updates

Since the repository service is only supported on Linux and does not have a
GUI, the server package is installed and updated using the `conda` command line
interface.

### Notes on Deserialization Profiling and Optimization

It would be great if 'deserialize()' performance could be improved, but it is a
tough nut.  Profiling shows that about 62% of its time is spent in sqlalchemy
operations, which are not amenable to optimization, so even if everything else
could be optimized to zero time (unlikely!) it would not even be a 50%
improvement.

A simple experiment with directly compiling 'deserialize()' using Cython
yielded no noticeable gain (less than 1%), and it is difficult to see any
operations within the function that could be formulated to compile into pure C,
anyway.

