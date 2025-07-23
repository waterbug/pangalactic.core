What is the Pan Galactic Engineering Framework?
-----------------------------------------------
The Pan Galactic Engineering Framework (pangalactic) is an open-architecture,
standards-based software framework for engineering applications such as systems
engineering data and tool integration, product lifecycle management (PLM),
computer-aided tools (CAX) integration, collaborative systems engineering,
design, and analysis, and multi-disciplinary product model capture,
integration, synthesis, and transformation.

The framework consists of 3 Python "namespace packages":

  - **`pangalactic.core`** (this package) contains the [ontology](https://pangalactic.us/pgef_ontology.html), a sqlalchemy-based object-relational api (the "uberorb"), and various utility functions, reference data, and metadata definitions.
  - **`pangalactic.node`** contains the pyqt-based GUI client, "pangalaxian".
  - **`pangalactic.vger`** contains the repository service.

As you might guess, **`pangalactic.node`** and **`pangalactic.vger`** both depend on
**`pangalactic.core`** for their infrastructure. The client and repository service
both have databases with the same schema, although the client uses sqlite and
the repository uses postgresql.

Platform Notes
--------------

  - **`pangalactic.node`**: the GUI client, **`pangalaxian.py`**, should run on
    any OS for which its dependencies are supported; it is currently tested on
    Windows 10, OSX (macOS Sonoma), and Linux (Ubuntu and Pop!_OS).

  - **`pangalactic.vger`**: the repository service, **`vger.py`**,
    (the Virtual Galactic Engineering Repository) is only supported on Linux.

Installation
------------
There are several installation options:

  - for testing and experimentation, the packages can be installed in
    **development mode** using conda:

        0. create a .condarc file with these contents:

            --------------------------------------
            channel_priority: strict
            channels:
              - conda-forge
              - https://pangalactic.us:/conda_repo

            report_errors: true
            --------------------------------------

        1. clone the client constituent packages:

            * pangalactic.core
            * pangalactic.node
            * marvin

        2. execute the following:

            cd [directory in which the packages have been cloned]
            conda install --only-deps pangalactic.node
            conda remove pangalactic.core
            conda install --only-deps pangalactic.core
            conda develop pangalactic.core
            conda develop pangalactic.node
            conda develop marvin

        3. to run the client:

            cd pangalactic.node/pangalactic/node
            ./pangalaxian.py

            (basic help is available using `./pangalaxian.py --help`)

        4. to start the server, clone the pangalactic.vger package and
           see the instructions contained in the pangalactic.vger package -- it
           can be run interactively (for debugging), as a stand-alone process,
           or in a Docker container (see the "docker" directory inside the
           package). The vger server requires a 'crossbar' message server
           to be running -- instructions on how to get and configure crossbar
           are in the vger package.

  - the conda packages themselves can be installed:

        1. create a .condarc file with these contents:

            --------------------------------------
            channel_priority: strict
            channels:
              - conda-forge
              - https://pangalactic.us:/conda_repo

            report_errors: true
            --------------------------------------

        2. execute the following:

            (to install the client)
            conda install marvin
            (this will install pangalactic.core and pangalactic.node)

            (to install the server)
            conda install pangalactic.vger
            (this will install pangalactic.core)

    - the server (pangalactic.vger) can be deployed in a Docker container --
      see documentation in the pangalactic.vger/pangalactic/vger/docker
      directory.

  - for the **Marvin** client, there is a self-contained Windows installer that
    can be downloaded from **[pangalactic.us](https://pangalactic.us)** ... its
    **[user guide](https://pangalactic.us/pgxn_doc/user_guide.html)** and
    **[reference](https://pangalactic.us/pgxn_doc/reference.html)** can also be
    found there (they are also included in the "marvin" repository).


Developer Documentation
-----------------------
Developer documentation for **`pangalactic.core`** is in the
NOTES_FOR_DEVELOPERS.md and other "NOTES" files in this directory. The "doc"
directory contains documentation of the underlying PGEF ontology, which is in
the pangalactic/core/ontology/pgef.owl file.

Acknowledgments
---------------
**`pangalactic.core`** depends on several excellent open source libraries,
most notably:

  - **[Python](http://www.python.org)**
  - **[Rdflib](https://rdflib.readthedocs.io/en/stable/)**
  - **[SQLAlchemy](https://pypi.org/project/SQLAlchemy/)**
  - **[Pint](https://pypi.org/project/Pint/)**

Thanks to all the talented and dedicated folks who have developed and
continue to maintain those packages and others in the formidable open
source code base that makes the Pan Galactic Engineering Framework
possible!

----------------------------------------------------------------------------

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

