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

* Entity == row == GridTreeItem
  - a dict that is semantically analogous to a domain object (and may be
    "linked" to one), and whose items are parameters and data elements
  - has a unique "oid", same as an object, so can also have parameters
  - future:
    + if mirroring a Product (same oid), parameter fields will be synced
    + can reference a ProductType and use associated parameters / templates

* DataMatrix (grid: rows and columns)
  - attrs:
    + 'oid': ([`project_id`]-[`system_id`]) -- unique
    + `level_map`:  maps entity oids to assembly level (int) --
      "level" will be used to identify "child" nodes, etc.
    + 'schema': list of data element ids
    + 'data': its internal list, a list of entity oids
  - methods:
    + serialize (returns a list of dicts)
    + dump (save to a .tsv file)
    + load (read from a .tsv file)
  - history tracking (for undo):
    + entity-level history:  `ent_histz` cache
    + edits are tracked by cell for each user
    + cell-specific undo (as long as the edit is not "obe" -- i.e. no other
      edits have a later time-date stamp)

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
  - data storage is the `app_home/data` directory
  - datamatrices are stored as tsv files
  - data element definitions ('dedz' dict cache) is stored as a yaml file

* RPC / PubSub signatures

  - data_dm_save(project_id, datamatrix, schema)
    + saves and publishes a serialized DataMatrix object and schema
    + perm:  Admin, LE, SE

  - data_create_element(project_id, element, metadata)
    + saves and publishes a new data element definition (metadata)
    + perm:  Admin, LE, SE

  - data_dm_schema_add_element(project_id, dm_id, element)
    + adds element to datamatrix schema / publishes
    + perm:  Admin, LE, SE

  - data_dm_schema_del_element(project_id, dm_id, element)
    + deletes element from dm schema / publishes
    + perm:  Admin, LE, SE

  - data_dm_add_row(project_id, dm_id, row_oid)
    + adds row oid to a datamatrix
    + perm:  Admin, LE, SE

  - data_dm_remove_row_from_dm(project_id, dm_id, row_oid)
    + deletes row from the specified dm
    + perm:  Admin, LE, SE

  - data_delete_row(project_id, row_oid)
    + deletes row oid from any dm(s) in which it occurs
    + perm:  Admin, LE, SE

  - data_update_item(project_id, row_oid, element_id**, value)
    + saves element value / publishes to project
    + perm:  Admin, LE, SE, Discipline of row

* dispatcher signal signatures

  Local events:

  - "dm saved" (serialized dm)
    + deserialize dm, add to dm store

  - "data element created" (element_id, value)
    + add element definition to data element dictionary

  - "dm element added" (dm_id, element_id)
    + add element_id to dm schema

  - "dm row added" (dm_id, row_oid)
    + add to specified dm

  - "dm row removed" (dm_id, row_oid)
    + remove row from specified dm

  - "row deleted" (row_oid)
    + remove row from all dm's

  - "item updated" (row_oid, element_id, value)
    + update item in all instances of row

  Remote events:

  - "remote dm saved" (serialized dm)
    + deserialize dm, add to dm store

  - "remote data element created" (element_id, value)
    + add element definition to data element dictionary ('dedz')

  - "remote dm element added" (dm_id, element_id)
    + add element_id to dm schema

  - "remote dm row added" (dm_id, row_oid)
    + add row to specified dm

  - "remote dm row removed" (dm_id, row_oid)
    + remove row from specified dm

  - "remote row deleted" (row_oid)
    + remove row from all dm's

  - "remote item updated" (row_oid, element_id, value)
    + update item in all instances of row

