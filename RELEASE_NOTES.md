NOTICE:
Copyright 2022 United States Government as represented by the Administrator
of the National Aeronautics and Space Administration.  No copyright is
claimed in the United States under Title 17, U.S. Code.  All Other Rights
Reserved.

Disclaimer:
No Warranty: THE SUBJECT SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTY OF
ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
TO, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL CONFORM TO SPECIFICATIONS,
ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
OR FREEDOM FROM INFRINGEMENT, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL BE
ERROR FREE, OR ANY WARRANTY THAT DOCUMENTATION, IF PROVIDED, WILL CONFORM TO
THE SUBJECT SOFTWARE. THIS AGREEMENT DOES NOT, IN ANY MANNER, CONSTITUTE AN
ENDORSEMENT BY GOVERNMENT AGENCY OR ANY PRIOR RECIPIENT OF ANY RESULTS,
RESULTING DESIGNS, HARDWARE, SOFTWARE PRODUCTS OR ANY OTHER APPLICATIONS
RESULTING FROM USE OF THE SUBJECT SOFTWARE.  FURTHER, GOVERNMENT AGENCY
DISCLAIMS ALL WARRANTIES AND LIABILITIES REGARDING THIRD-PARTY SOFTWARE, IF
PRESENT IN THE ORIGINAL SOFTWARE, AND DISTRIBUTES IT "AS IS."
Waiver and Indemnity: RECIPIENT AGREES TO WAIVE ANY AND ALL CLAIMS AGAINST
THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS
ANY PRIOR RECIPIENT.  IF RECIPIENT'S USE OF THE SUBJECT SOFTWARE RESULTS IN
ANY LIABILITIES, DEMANDS, DAMAGES, EXPENSES OR LOSSES ARISING FROM SUCH USE,
INCLUDING ANY DAMAGES FROM PRODUCTS BASED ON, OR RESULTING FROM, RECIPIENT'S
USE OF THE SUBJECT SOFTWARE, RECIPIENT SHALL INDEMNIFY AND HOLD HARMLESS THE
UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY
PRIOR RECIPIENT, TO THE EXTENT PERMITTED BY LAW.  RECIPIENT'S SOLE REMEDY FOR
ANY SUCH MATTER SHALL BE THE IMMEDIATE, UNILATERAL TERMINATION OF THIS
AGREEMENT.

1.4.11:

* New: use "block mod" dispatcher signal to update modified block in-place
* Bug Fix: use "trash" to track deleted objects on server so they are not
           "resurrected" by a user sync

1.4.10:

* New:
  - ProductType: "Thermal Interface Material" (TIM)
  - ParameterDefinition:  "radius", "diameter", "velocity", "omega" (angular
    velocity), frequency (cycles/second)
  - ParameterContext:  "inner", "outer", "Average", "Peak", "Nominal", "max",
    "min", "Orbital"
* Bug Fix: top system(s) in ConOps no longer have to be Spacecraft -- can be
           any product type
* Bug Fix: [schema change] cattens sometimes crashed randomly (segfault) when
           it exited -- turned out to be a sqlalchemy-related bug in the
           schema: tables managed_object_, actor_, organization_, person_ had
           ambiguous fk relationships (interpreted as cyclic).  Fixed by making
           Actor a subclass of Identifiable, and Organization a subclass of
           Modelable (both are more appropriate and simpler -- also, not a very
           disruptive schema change).

1.4.9:

* New: added a function in diagram block context menu to identify all flows
       associated with a block
* Bug Fix: fixed MEL generator to make format conform to Code 100 standard
* Bug Fix: fixed flow deletion algorithm coverage of cases in which a
           component is deleted or modified

1.4.8:

* New: can now modify reference designator for empty (TBD) positions in an
       assembly, indicating function
* New: can now drag/drop a "product type" onto a diagram to create an empty
       assembly position of that type
* Bug Fix: bug in clone:  it only updated the primary object that was cloned,
           but ancillary objects (e.g. for Hardware, Components and Ports)
           that were added to the local db were not live-synced to the
           repository db -- clone now uses dispatches signals for any cloned
           Components and Ports so they are synced at the same time
* Bug Fix: diagram fixed so that a system block always contains its component
           blocks (previously a component could sometimes be drawn outside of
           the system block, which confused users) also, the system block now
           has a constant width (to accommodate 2 columns of blocks), and
           looks more like what it is:  the outer boundary of an "Internal
           Block Diagram" (IBD)
* Bug Fix: "Export Project Requirements to a File" works again

1.4.7:

* New: improved user instructions (James's suggestions) on "System/Component
       Wizard"
* New: repository service backs up database and parameter cache at completion
       of startup
* Bug Fix: trigger tree refresh for drops of systems on Project subject block
           in diagram

1.4.6:

* Fixed MEL generator again!
* Data Element Definitions Library

1.4.5:

* Fixed loading of data into the server database

1.4.1-4:

* Special admin function to assign global admin role
* Improved DataGrid MEL generation (DataMatrix and Entity, etc.)
* admin tool listens for role assignments and refreshes its display if
  applicable
* deserialization exception tracebacks are logged
* syncing shows status message after each chunk is synced and how many more are
  coming.

1.4.0:

* Service ("vger") dockerized
* Public key auth ("cryptosign")
* Admin dialog enhancements:
  - "Add User" can update with new LDAP info
  - Loads public key from file and adds to auth db
  - Interface improvements
* Deploy "production" and "dev" servers

1.3.9 (05/21/20):

* More sync performance optimizations

1.3.8 (05/15/20):

* BUG fix: fixed Reqt. Wizard reqt. id generation regression
* BUG fix: Reqt Mgr:  parameter edit dialog brought up multiple copies
* BUG fix: Reqt Mgr: on closing wizard it popped up again.

1.3.7 (05/12/20):

* Bug fix: fixed crash when generating a product (deal with null ids)
* Bug fix: component mode delete of subject product now displays placeholders
* Bug fix: cloning a product from a template replicates template parameters
* Bug fix: data elements are now being populated (fixed `set/get_dval`)
* Bug fix: Person object creator/modifier caused recursion in serializer
* Bug fix: cloning in component mode now displays the diagram of the clone
* Bug fix: fixed crash when setting units on a blank field

1.3.6 (05/06/20):

* Bug fixes: fixed critical db problems when deleting Ports/Flows

1.3.5 (04/24/20):

* Bug fixes: fixed regressions introduced by parameter / data element split

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

