# TO DO

Things worth doing, across all four PGEF repositories.  Deliberately without
priorities or a timeline -- it is a list of what is worth doing, not a plan
for when.  Anything with a decided shape gets a `NOTES_ON_*.md` design note
of its own and is referenced from here rather than described at length.

Kept in `pangalactic.core` because it spans the repositories and belongs
under version control;  it lived in the author's sandbox until 2026-08-22.

* Hardware Library:
  - Add "Only Non-Project Specs" filter to HW library (filters out
    Project-owned items)
  - Develop AI method to find and scrape product data sheets and add library
    components
  - Add CubeSat and SmallSat components
    ... coordinate with SpaceCube community -- get data sheets and parameters
  - import Mechanical component data (mass, dimensions, etc.) from STEP files
  - provide STEP models of library components ... possibly "simplified" (e.g.
    form factor)
* Synthesize a STEP assembly file from a PGEF assembly
  - a "STEP assembly template" file to which component references are added
  - discovered 2026-08-22: substituting a file name in a reference
    substitutes the component, because the assembly file holds only a stub
    shape rep for a referenced child -- name and content are independent
  - PGEF already holds every input (Acu ref des, placements, and
    RepresentationFile.user_file_name for the file names)
  - see pangalactic.node/NOTES_ON_STEP_EXTERNAL_REFS.md section 6
  - orientation may be derivable from interfaces (ports) rather than entered
* Excel interface (on Windows use COM ...?)
  - installs as an independent "plugin"
  - can use as interface to repo
  - top priority function areas:
    - Hardware Library
    - Requirements
* Refactor modeler.py to use QStackedWidget and add a mode that uses the
  pythonocc viewer (CAD/STL model viewing)
* Fix HW Product version management so can do real CM
  - Track version history / change logging
* Misc
  - Add functionality to handle redundant (e.g. flight backup) items in the MEL
    -- e.g. set their Power to Off in all normal operational modes:  add a
    DataElement that will be assignable to an Acu indicating what form of
    redundancy, if any, applies -- which will determine whether the item's
    parameters will be rolled up as part of the assembly's parameters
  - Make a view for pgxno parameter panels by "topic" (e.g. "sensitivities",
    "geometry", "mechanical", etc.)

Other External Interfaces:

* 42
  - create .stl from STEP using pythonocc, then use meshio to gen .obj
* GMAT
* Dakota/Dakotathon
* OpenMDAO
* SysML
  - v. 1.x data exchange via Excel / tsv
  - v. 2 API
* SymPy

