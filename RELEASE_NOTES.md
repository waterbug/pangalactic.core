1.3.8:

* BUG fix:  fixed Reqt. Wizard reqt. id generation regression
* BUG fix:  Reqt Mgr:  parameter edit dialog brought up multiple copies
* BUG fix:  Reqt Mgr: on closing wizard it popped up again.

1.3.7:

* Bug fix:  fixed crash when generating a product (deal with null ids)
* Bug fix:  component mode delete of subject product now displays placeholders
* Bug fix:  cloning a product from a template replicates template parameters
* Bug fix:  data elements are now being populated (fixed `set/get_dval`)
* Bug fix:  Person object creator/modifier caused recursion in serializer
* Bug fix:  cloning in component mode now displays the diagram of the clone
* Bug fix:  fixed crash when setting units on a blank field

1.3.6:

* Bug fixes:  fixed critical db problems when deleting Ports/Flows

1.3.5:

* Bug fixes:  fixed regressions introduced by parameter / data element split

1.3.4:

* Unreleased due to bugs

1.3.3:

* Bug fix: Diagrams did not sync properly with system tree and diagram.
  With this bug fix, users can now edit a system or component in "component"
  mode by drag/dropping library objects onto its block diagram and/or removing
  components from the diagram (see context menus, below) and it will sync
  properly with users who are operating in "system" mode (i.e. the system tree
  and diagram will sync).

* Bug fix: (Windows only):  drop on diagram was not updating the system tree

* Feature: Context menus for blocks in the diagram
  Right click on a block to see its context menu:
  - View this object (brings up the object viewer/editor, same as in the system
    tree)
  - Show allocated requirements (shows all requirements allocated to the block)
  - Remove this component (leaves a TBD block in the diagram and an "empty
    bucket" in the system tree)
  - Remove this assembly position (or system) (removes the block entirely, and
    removes its node from the system tree)

* Feature: New product types for "Fuel", "Oxidizer", "Latch Valve", "Pressure
  Transducer" (from Kan's examples in the CATTENS Priority Actions)

