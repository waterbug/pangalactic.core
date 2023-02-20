# PANGALACTIC DEVELOPER NOTES

## Structure of the `pangalactic` Namespace Packages

### `core`: base pangalactic package: ontology, registry, orb, reference data
  - `access.py ............ computes user permissions for objects`
  - `datastructures.py .... some custom data structures`
  - `entity.py ............ a data object for a collaborative spreadsheet`
  - `kb.py ................ "knowledgebase" api: OWL ontology import/export`
  - `log.py ............... loggers, used by the "orb"`
  - `ontology ............. pgef.owl [file in OWL format]`
  - `test ................. unit tests`
    + `data ............... test data files`
    + `vault .............. test data files [copied to app_home/vault]`
  - `utils ................ general utility modules`

### `node`: GUI client package
  - `cad ........ CAD modules`
  - `diagrams ... block diagram modules`
  - `icons ...... app icons [copied to app_home/icons]`
  - `images ..... app images [copied to app_home/images]`
  - `test ....... GUI test client`

### `vger`: network repository service
  - `vger.py ........ repository service module`
  - `userdir.py ..... LDAP directory search interface`
  - `transform.py ... data migration script (for schema changes)`

## Contents of App Home Directory (`[app]_home`) created at start-up

* holds configuration data (some of which may be user-specific) that
  persists when a new version of the app is installed

* note that if schemas change between versions, some of this data may need
  to be modified to conform to the new schemas

    `cache/ ........... internal metadata structures derived from the ontology, and used by the "registry" module to generate the domain classes and properties that sqlalchemy uses to define the database structure`

    `config ..........  config file (yaml) -- see *Settings* section below`

    `data_elements.json ... persistent form of "data_elementz" runtime cache -- see p.core.parametrics module`

    `diagrams.json .... diagram geometry storage`

    `dms.json ......... persistent form of "dmz" cache of DataMatrix instances`

    `icons/ ........... "built-in" icons (icons generated at runtime are saved in vault/icons; all other data files are simply added to the "vault" directory)`

    `images/ .......... images  (application-specific images)`

    `local.db ......... node local object store (sqlite db)`

    `log/ ............. logs`

    `modes.yaml ....... persistent form of "modez" runtime cache -- see p.core.parametrics module`

    `mode_defs.yaml ... persistent form of "mode_defz" runtime cache -- see p.core.parametrics module`

    `onto/ ............ contains pgef.owl (OWL ontology file)`

    `parameters.json .. persistent form of "parameterz" runtime cache -- see p.core.parametrics module`

    `prefs ............ saved preferences (yaml) -- see *Settings* section below`

    `schemas.json ..... persistent form of "schemaz" cache, used by DataMatrix`

    `server_cert.pem .. certificate for message bus host (enables TLS connection)`

    `state ............ saved state (yaml) -- see *Settings* section below`

    `test_data/ ....... files for user access in testing of data importing, etc.`

    `trash ............ trash file (yaml) containing serialized deleted objects {obj.oid : orb.serialize([obj]), ...}`

    `vault/ ........... files created/accessed internally by pangalactic applications (includes icons generated at runtime and files referenced by the database, e.g. files corresponding to DigitalFile objects)`

## Settings

* **config**

    `admin_package_name:    (str)  name of admin package`

    `admin_script_name:     (str)  name of admin script`

    `app_channel:           (str)  app channel url or name`

    `app_name:              (str)  app name`

    `app_package_name:      (str)  app package name`

    `dashboards:            (dict) named dashboards (lists of parameter ids)`

    `dashboard_names:       (list) ordering of keys in "dashboards"`

    `db_url:                (str)  sqlalchemy-style db url (only used by vger)`

    `default_parms:         (list) ids of default parameters`

    `default_data_elements: (list) ids of default data elements`

    `de_defz:               (dict) pre-configured data element definitions`

    `host:                  (list) fqdn of message bus host`

    `ldap_schema:           (dict) schema for use with local ldap service`

    `local_admin:           (bool) if "true", user can edit any item locally`

    `load_extra_data[1]:    (list) names of files containing data to load`

    `logo:                  (str)  logo icon file name`

    `p_defaults:            (dict) default parameter values {id: val (string)}`

    `port:                  (str)  port to use for message bus host connection`


    `tall_logo:             (str)  "tall" logo icon file name`

    `units:                 (str)  unit system (default: 'mks')`

* **prefs**

    `dashboards:         (dict) named dashboards (lists of parameter ids)`

    `dashboard_names:    (list) ordering of keys in "dashboards"`

    `default_parms:      (list) ids of default parameters to assign to objs`

    `editor:`

    `    parameters:     (list) [ids] order of parameters in pgxnobject panels`

    `model_types:        (list) oids of ModelTypes that pangalaxian can "render"`

    `views:              (dict) preferred ordering of table columns by class (maps class name to list of field names)`

* **state**

    `admin_of:         (list) oids of Projects in which user has admin role`

    `active_users:     (list) ids of users that have registered public keys`

    `client:           (bool) whether running as client (True) or server`

    `cloaked:          (list) oids of local cloaked objects`

    `connected:        (bool) true if logged in to message bus`

    `current_cname:    (str)  name of currently selected db table class`

    `dashboard_name:   (str)  name of currently selected dashboard`

    `dataset:          (str)  name of currently selected dataset`

    `datasets:         (list) names of currently stored datasets`

    `diagram needs refresh: (bool) block diagram needs to be refreshed`

    `height:           (int)  pixel height of pangalaxian gui`

    `width:            (int)  pixel width of pangalaxian gui`

    `disabled:         (bool) true if user has Disabled role (global)`

    `height:           (int)  current pixel height of pangalaxian gui`

    `icon_type:        (str)  suffix for platform-specific icons [e.g., '.ico']`

    `last_path:        (str)  most recent path in file selections`

    `local_user_oid:   (str)  oid of Person object for local user `

    `mode:             (str)  current Pangalaxian gui mode`
    `                         ('system', 'component', 'db', or 'data')`

    `mode_defz_dts:    (str)  last-synced-datetime str of the mode_defz cache`

    `product:          (str)  oid of currently selected Product -- refers to`
    `                         the product selected in 'product modeler'`

    `project:          (str)  oid of currently selected Project`

    `synced_oids[3]:   (list) oids of user-created objects that have been synced`

    `synced_projects[4]: (list) oids of projects that have been synced`

    `sys_tree_expansion[5]: (dict) maps project oids to tree expansion level`

    `system:           (str)  oid of currently selected system (Product or`
    `                         Project) -- may be selected by clicking on an item`
    `                         in the system tree or drilling down into`
    `                         (double-clicking on) a block in the diagram`

    `test_project_loaded (bool) H2G2 test project loaded (server-side only) [6]`

    `userid:           (str)  most recent userid used in login`

    `version:          (str)  version of client`

    `width:            (int)  current pixel width of pangalaxian gui`

    `[1]: "load_extra_data" is intended for use on the server (vger)`
    `     for special data not included in "refdata", such as data specific to`
    `     local organizations, etc.  Specifically, it is intended to be used`
    `     to reload data from a database backup when a new docker`
    `     image/container is started.`

    `[2]: "assigned_roles" data structure:`

    `    {project oid: [list of names of assigned roles on the project]}`

    `    NOTE:  for project-independent role assignments, 'global' is used in`
    `    place of a project oid.`

    `[3]: the "synced_oids" list is used in determining whether an object may`
    `     be modified or deleted while the client is offline (not connected to`
    `     the repository): any object that has been synced to the repository`
    `     *cannot* be modified or deleted while offline, because it may be`
    `     used in an assembly by another user.`

    `[4]: Projects only need to be synced when a project is first used during`
    `     an online session because objects may have been added, deleted, or`
    `     modified while the user was offline. During a session, the bulk`
    `     project sync is only done once because during the online session all`
    `     objects are kept in sync by messages. The "synced_projects" list is`
    `     used to keep track of which projects have been synced during the`
    `     current online session.  The 'vger.sync_project' rpc is only called`
    `     when the user selects a project using the project selector -- after`
    `     the sync completes, the oid for that project is added to`
    `     "synced_projects".  The "synced_projects" list is cleared when the`
    `     session ends.`

    `[5]: "sys_tree_expansion" data structure:`

    `    {project oid : (int) index in the "levels" combo (2 to 5 levels)`
                              for state of sys tree expansion in that project}`

    `[6]: (server only) for vger, if "test" arg is true and`
    `     state["test_project_loaded"] is false, the H2G2 test project and its`
    `     data will be loaded; if true, H2G2 has already been loaded -- see`
    `     pangalactic.vger.vger.RepositoryService.`

## Runtime Caches

Certain data structures are maintained in python dictionaries at runtime to
optimize performance.

* `componentz` (defined in "parameters" module)
  - cache of assembly components:  
* `data_elementz` (defined in "parameters" module)
* `de_defz` (defined in "parameters" module)
* `dmz` (defined in "entity" module)
  - cache of DataMatrix instances:  {oid: DataMatrix}
* `parameterz` (defined in "parameters" module)
* `parm_defz` (defined in "parameters" module)
* `schemaz` (defined in "entity" module)
  - cache of schemas:  {schema name: [col1, col2, ...]}

## Modes and Views

* Modes are set by selecting one of the mode icons at top right corner of the
  main window
* "mode" is a state of the main pangalaxian main window

#### Modes:  "system" and "component"

* Component Modeler and System Modeler

* Create/modify systems and component models
  + MainWindow layout:
    - if no models ... left: "No Model", center: empty
    - if 1 model ..... left:  tree structure + metadata,
                       center: diagram
    - if > 1 model ... left:  tree structure + metadata of selected model,
                       center: diagram

#### Mode:  "db"

* View/edit objects in local db

#### Mode: "data"

* Main widget is DataGrid, which uses a "DataMatrix" as its underlying model

## Diagrams (used in "system" and "component" modes)

* See `NOTES_ON_DIAGRAMS`

## DEPRECATED: "louie" ("dispatcher") signals

------------------------------------------------------------------------------

"louie" (a.k.a. "dispatcher") signals are now deprecated in pangalactic because
they can cause paint errors, crashes, and segfaults due to not playing nice
with the underling Qt event loop -- they are being replaced by the Qt signals
and slots mechanism (in pyqt, pyqtSignal and pyqtSlot).

------------------------------------------------------------------------------

## Random notes on the orb

(0) the orb is used on both the client and server sides, so it must be kept
    free of:
    * 'louie' events -- they are used *only* in the client gui environment
    * `local_user` -- exists solely in the client environment
    * any awareness of the network or network-related events

(1) orb.save() *NEVER* sets the `mod_datetime` of objects, because it
    saves both local objects and those received from remote sources --
    therefore, locally created or modified objects must be time-stamped
    *before* they are passed to orb.save().

(2) orb.clone() *ALWAYS* sets the `mod_datetime` of the clone

## Behavior of Project and System selection states

* Project selection
  - component mode:  any Parts or Models created will have the selected
                     Project as their `owner` (person creating them will be
                     `creator`)
  - systems mode:    left dock systems tree will be for the selected Project
                     (if no system is selected -- see below)

* System selection
  - component mode:  is displayed in the product info panel (dropped there)
  - systems mode:    is selected the systems tree

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

* **IMPORTANT**: avoidance of Qt paint errors and segfaults requires that
  if the Hardware Library is currently instantiated and a HardwareProduct
  instance is to be deleted, its row in the HW Library must first be removed
  (using the `del_object` method of the ObjectTableModel) before the object
  is deleted using orb.delete() ... this is done by doing (almost) all object
  deletions in the `pangalaxian.delete_object()` method).

## Features Requiring Platform Detection

Some features require the desktop application to detect the platform on which
it is running and adapt itself accordingly.

* CAD Viewer

  - Windows:  viewer can only run in the main app process

    The use of the python `multiprocessing` module to enable the viewer to run
    in a separate process introduces an incompatibility when PyInstaller and
    Innosetup are used to create a self-contained application from a conda
    package that uses PyQt5.  Note that the application works when run as a
    conda package, and also works after the processing by PyInstaller, but does
    not work when installed using the setup.exe produced by Innosetup.  The
    following code enables PyInstaller to handle the `multiprocessing` module
    on the Windows platform:

        # multiprocessing.freeze_support is needed for multiprocessing to work
        # with PyInstaller on Windows -- and it must be invoked *immediately*
        # after if __name__ == "__main__":
        multiprocessing.freeze_support()

    However, since the Innosetup-created `setup.exe` installed version does not
    work properly, that code cannot be used.

  - Mac:  viewer can only run in a separate process (can have multiple viewers
    running simultaneously)

  - Linux:  can run either a single viewer in the main process or multiple
    viewers in separate process(es)

## Installation and Configuration of Crossbar

[TBD]

## Configuration for Testing the Client with a Local Crossbar and Repo Service

The `Pangalaxian` desktop application can be tested using a local crossbar
server and repository service (`pangalactic.vger.vger`) by configuring it as
follows:

0. start up the client (which creates its home directory)
1. stop the client and cd to its home directory
2. copy or link the `localhost` `server_cert.pem` file to the client's home
   directory, replacing any `server_cert.pem` that was there.
3. edit the `config` file:
    - set 'host' to `localhost`
    - set 'port' to the port that crossbar is running on (`8080` is default)
4. start up the client again using the flags:
    - '-t' (test mode)
    - '-d' (debug level logging)

You should now be able to log in to your local crossbar and access your local
repository service.

## Repository Service Installation and Updates

Since the repository service is only supported on Linux and does not have a
GUI, the server package is installed and updated using the `conda` command line
interface.

### Notes on Deserialization Profiling and Optimization

It would be great if 'deserialize()' performance could be improved, but that is
difficult.  Profiling shows that about 62% of its time is spent in sqlalchemy
operations, which are not amenable to optimization, so even if everything else
could be optimized to zero time (unlikely!) it would not even be a 50%
improvement.

A simple experiment with directly compiling 'deserialize()' using Cython
yielded no noticeable gain (less than 1%), and it is difficult to see any
operations within the function that could be formulated to compile into pure C,
anyway.

## Windows Desktop Application Installation and Management

On the Windows platform, **PyInstaller** and **Innosetup** are used to create
a `setup.exe` installer for the desktop application package.  When run, the
application is installed in the user's home directory and does not require
admin privileges.  

### Process for Building Windows Desktop App Releases / Installers

1. Bump version for all packages (pangalactic.core, pangalactic.node, pangalactic.vger, any application-level packages):

   * Edit the `sedscr` sed script to increment the version string
   * Run the `bump_version.sh` shell script (which runs the sed script)
   * git commit
   * git push

2. Build all conda packages:

   * Remove all __pycache__ directories inside packages:
 
        `find . -name __pycache__ -exec rm -r {} \;`

   * Edit conda recipe "meta.yaml" files to update versions and dependencies
   * Run `conda build [pkg name] [--python=[python version]]` ("python version"
     is only needed if different than the env's python)
   * NOTE: for compatibility it may be necessary to install "conda-build" into
     the virtual env where the build is being done, rather than the base env.

3. Put conda packages into an accessible conda repository

4. Install conda packages from the conda repository specified in step 3 (which
   should either be referenced in `.condarc` or specified using `-c`):

        `conda install [app]`

5. Run pyinstaller on the app-level package -- e.g.:

        `pyinstaller [app].spec`

   ... where "app.spec" is the pyinstaller spec file for the app, created by
   running pyinstaller and then modifying as necessary.

6. Test the .exe:

   * cd to the "dist" directory, and to the app subdirectory, whose name is
     specified in the spec file
   * execute the command:

        `./run_[app].exe`

7. Use Inno Setup to build the "setup.exe" installer for Windows.


