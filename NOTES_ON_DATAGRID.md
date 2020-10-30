PGEF "DataGrid" Widget

## Features

* Both "spreadsheet-like" AND "database-like" (has a schema)
  - individually-addressable cells
  - dynamically-configurable schema (column label/definition/datatype)
  - cells with same oid/column-id are synced in every local matrix in which they occur
  - import/export data from/to Excel
  - row can represent / be linked to a Product (e.g. a library item)

* Collaborative
  - a given cell "instance" [oid/column-id] can exist in multiple matrices
  - near-real-time update of edits in all replicated instances
  - change nofications by cell color change + flashing
  - [low priority?] write access to a cell is controlled by user role

## Implementation

* cell == a parameter or data element instance in context of a GridTreeItem
  - addressable using (`row_oid`, `column_id`, value) tuple
  - synonyms:  "field", "column", "parameter", "attribute", "property"
               "data element"
  - data element definitions are in a dict with the following keys:
    + id: unique identifier (unique among data elements AND parameters)
    + datatype:  int, float, str, bool
    + name: also must be unique
    + label: "external" name (table column label; may contain line breaks)
    + description: definition

* Entity == row -> GridTreeItem
  - a dict subclass that is semantically analogous to a domain object (and may
    be "linked" to one by way of its "system_oid" metadata), and whose items
    are parameters and data elements

  - attributes:
    + `oid`: same implementation as for domain objects, so an entity can also
      have parameters and data elements, to which [set|get][_pval|_dval] can be
      applied, as with objects
    + `parent_oid`: can either be None or can reference an existing Entity oid
    + `system_oid`: can either be None or can reference an existing Product oid
    + `assembly_level`: a property, computed by following the chain of
      `parent_oid` attributes, ending with a None (level 1).

      NOTE 0: `assembly_level` takes into account the contingency that a
      component can occur at more than one level in an assembly -- e.g., a
      thermal sensor that is placed at arbitrary locations in an assembly or a
      chip that occurs in multiple boards or boxes:  multiple Entity instances
      in an assembly can reference the same product via their `system_oid`, and
      each can have its own value of the `assembly_level` attribute.

      NOTE 1: the "where-used" function reports which assemblies a given part
      occurs in but does not have level information, since a given assembly
      may occur as a component at different levels in different systems.

      NOTE 2: this use case occurs in the STEP example file as1-oc-214.stp, in
      which the 'nut' product occurs in both the 'nut-bolt-assembly' [level 3]
      and the 'rod-assembly' [level 2].

      NOTE 3: `assembly_level` is returned from the Entity dictionary as the
      value of the `level` key.

  - can address the use case of a DataMatrix that represents a parts list, such
    as the GSFC "Master Equipment List" (MEL)
  - history tracking (for undo):
    + `ent_histz` cache
    + edits datetime-stamped (`mod_datetime` of the parameter or data element)
      and are tracked by user ('modifier')
  - future:
    + can reference a ProductType and use associated parameters / templates

* DataMatrix
  - a list of Entity instances ... equivalent to a grid: rows and columns)
  - a DataMatrix is basically a way of saying "show me *this* information about
    *these* entities".  The information to be shown is specified by the
    'schema' of the DataMatrix -- conceptually, a "view" -- which specifies the
    columns (ids of data elements and parameters) to be displayed.  The
    entities do not all have to have the same set of data elements and
    parameters, nor do they have to have everything that is in the DataMatrix
    schema -- if they are missing anything in the schema, that cell will just
    be displayed as empty (and the DataGrid will enable it to be assigned a
    value, updating the underlying Entity).
  - attrs:
    + 'oid': ([`project_id`]-[`system_id`]) -- unique identifier, implemented
      as a read-only property
    + 'schema': list of data element ids
    -------------------------------------------------------------------------
    `level_map` is CURRENTLY NOT IMPLEMENTED (not clear that it was needed)
    + `level_map`:  maps entity oids to assembly level (an integer) --
      "level" will be used to identify "child" nodes, etc.:
      - level 0 ................................ root (not assembly)
      - next node 0 < level < this level ....... higher assembly
      - next node level = this level ........... peer
      - next node level = this level + 1 ....... child
      - next node level > this level + 1 ....... error
    -------------------------------------------------------------------------
  - methods:
    + "cell-specific" undo based on Entity 'undo' method, which uses the
      Entity's history (as long as the edit is not "obe" -- i.e. no other edits
      have a later datetime stamp)

* GridTreeView(QTreeView)
  - cells addressable by row + column
  - NOTE:  hideColumn(0) does hide the first column but also hides the tree
    node expansion interface!  :P  To hide the initial columns (e.g. the "oid"
    and "row" columns), they will need to be removed from the model before
    creating the view.
  - NOTE: setTabKeyNavigation(True) works but navigates vertically!
    ... I think that's because the "Items" in the model are tree nodes,
    which translates to "rows", basically ... so the navigation is
    between the rows, not cells -- so kind of useless.

    In QWidget.setTabOrder(a, b) a and b must be *widgets*, and the "cells" in
    the QTreeView, while indexed, are not widgets.  Tab navigation between
    cells may be possible but would probably require a LOT of work (assign a
    widget [Delegate] to each cell and use QWidget.setTabOrder(a, b) between
    each pair of cell delegates -- sheesh! :P)

    Bottom line:  selecting a cell by double-clicking on it will be the *only*
    way to edit a cell, for now.

* access control
  - DataMatrix
    + is readable by any person with a role in its 'owner' Project
    + can only be created or deleted by Project Admin, Lead Engineer, or
      Systems Engineer
  - entity (row)
    + readable by anyone with access to its DataMatrix (the Project)
    + writeable by Project Admin, LE, SE, or Discipline
  - cell (entity data element value)
    + readable by anyone with access to its DataMatrix (the Project)
    + writeable by anyone with write access to its entity
  - use a "permissions dict":
    {userid: roles vector}
    where roles vector is a list of [project-role, ...]

* persistence
  - data is persisted in files in the `app_home` directory
    + dms.json .............. metadata for DataMatrix instances
    + data_elements.json .... serialized data elemenets
    + ent_hists.json ........ serialized entity histories
    + ents.json ............. metadata for entity instances
    + parameters.json ....... serialized parameters
    + schemas.json .......... schemas for DataMatrix instances
  - data element definitions are cached at runtime in the 'dedz' dict

* RPC and PubSub message signatures

  - [rpc] `save_dm(project_id, datamatrix)`
    + saves a serialized DataMatrix object
    + [pubsub] subject: "dm saved" content: serialized dm
    + perm:  Admin, LE, SE

  - [rpc] `save_dm_schema(serialized schema)`
    + a dm schema is a list of registered Parameter and DataElement ids
    + creates or modifies a dm schema
    + [pubsub] subject: "new dm schema", content: schema
    + perm:  Admin, LE, SE

  - [rpc] `add_dm_entity(dm_oid, entity_oid)`
    + adds an entity to a DataMatrix
    + [pubsub] subject: "dm entity added", content: `(dm_oid, entity_oid)`
    + perm:  Admin, LE, SE

  - [rpc] `rm_dm_entity(dm_oid, entity_oid)`
    + removes an entity from a DataMatrix
    + [pubsub] subject: "dm entity removed", content: `(dm_oid, entity_oid)`
    + perm:  Admin, LE, SE

  - [rpc] `save_entity(serialized entity)`
    + creates or modifies an entity
    + [pubsub] subject: "entity saved", content: serialized entity
    + perm:  Admin, LE, SE

  - [rpc] `delete_entity(entity_oid)`
    + deletes an entity and removes it from any DataMatrix in which it occurs
    + [pubsub] subject: "entity deleted", content: `entity_oid`
    + perm:  Admin, LE, SE

  - [rpc] `set_parameter(oid, pid, value, units, mod_datetime)`
    + sets parameter value
    + [pubsub] subject: "parameter set",
               content: `(oid, pid, value, units, mod_datetime)`
    + perm:  Admin, LE, SE

  - [rpc] `set_data_element(oid, deid, value, units, mod_datetime)`
    + sets data element value
    + [pubsub] subject: "data element set",
               content: `(oid, deid, value, units, mod_datetime)`
    + perm:  Admin, LE, SE

* dispatcher signal signatures

  Local events:

  - "dm saved" (serialized dm)
    + deserialize dm, add to dm store

  - "entity saved" (serialized entity)
    + deserialize entity, add to `entz` cache

  - "dval set" `(oid, deid, value, units, mod_datetime)`
    + add a data element and value to an entity or object

  - "pval set" `(oid, pid, value, units, mod_datetime)`
    + add a parameter and value to an entity or object

  Remote events (corresponding to pubsub messages):

  - "remote dm saved" (serialized dm)
    + deserialize dm, add to dm store

  - "remote entity saved" (serialized entity)
    + deserialize entity, add to `entz` cache

  - "remote dval set" `(oid, deid, value, units, mod_datetime)`
    + add a data element and value to an entity or object

  - "remote pval set" `(oid, pid, value, units, mod_datetime)`
    + add a parameter and value to an entity or object

