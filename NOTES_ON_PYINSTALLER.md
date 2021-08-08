=============
General Notes
=============

To run pyinstaller, cp either win_main.spec (on Windows) or mac_main.spec (on
OSX) to [app]/[app]/__main__.spec and execute this command:

    pyinstaller __main__.spec

If successful this will create 2 subdirectories, 'dist' and 'build'
In the 'build' dir there should be a directory 'appza' that contains all
generated files, including one called 'run_[app]', the executable.

------------------------------------
Twisted runtime hook bug work-around
------------------------------------

* the runtime hook for twisted is bad (installs default reactor)

  comment out the contents of the file "pyi_rth_twisted.py" --
  note that its location is different for different versions of PyInstaller
  - pyinstaller 3.6:
    ...\Lib\site-packages\PyInstaller\loader\rthooks
  - pyinstaller 4.x (uses a separte pkg "pyinstaller-hooks-contrib"):
    .../envs/[env-name]/lib/python3.7/site-packages/_pyinstaller_hooks_contrib/hooks/rthooks

-----------------------------
PyQt5 plugins bug work-around
-----------------------------

* for python 3.6, pyinstaller 3.4, pyqt 5.6.0, the error:
  "pyinstaller cannot find existing pyqt5 plugin directories"
  can be fixed by modifying the file:

    ...\Lib\site-packages\PyInstaller\utils\hooks\qt.py

  as follows:
-------------------------------------------------------------------
    json_str = exec_statement("""
        import sys

        # exec_statement only captures stdout. If there are
        # errors, capture them to stdout so they can be displayed to the
        # user. Do this early, in case PyQt5 imports produce stderr
        # output.
        sys.stderr = sys.stdout

        import json
        from %s.QtCore import QLibraryInfo, QCoreApplication

        # QLibraryInfo isn't always valid until a QCoreApplication is
        # instantiated.
        app = QCoreApplication([])
        paths = [x for x in dir(QLibraryInfo) if x.endswith('Path')]
        location = {x: QLibraryInfo.location(getattr(QLibraryInfo, x))
                    for x in paths}
        try:
            version = QLibraryInfo.version().segments()
        except AttributeError:
            version = None
        print(str(json.dumps({
            'isDebugBuild': QLibraryInfo.isDebugBuild(),
            'version': version,
            'location': location,
        })))
    """ % self.namespace)  
-------------------------------------------------------------------
  (per https://stackoverflow.com/questions/52376313/converting-py-file-to-exe-cannot-find-existing-pyqt5-plugin-directories/52376965
-------------------------------------------------------------------

-------------------------------------------------------------------
PyInstaller will put the PyQt5 plugins into:

[exe dir]/PyQt5/Qt/plugins

The subdirectory 'platforms' contains a critical dll, 'qwindows.dll'.  Move all
the subdirectories directly under the [exe dir], and the executable will find
them.

-------------------------------------------------------------------

* on Windows, pythonocc needs "CASROOT" defined as an env var pointing to
Library/share/oce ... which contains a "src" directory with data files (which
is part of the conda installation).

  - copy Library/share/opencascade directory to [app]_home/casroot and set
    that as "CASROOT" env variable.

=============
OSX Notes
=============

---------------------------------------------------------
'PyQt5 module has no "__version__" attribute' work-around
---------------------------------------------------------

This problem appeared on OSX with pyinstaller 4.4 and python 3.8 or 3.9.
Running 'pip install pyqt5' was suggested in a stack overflow conversation --
it worked, but it seems weird since pyqt5 was already installed as a conda
package.

-------------------------------------------------------------------

=============
Windows Notes
=============

-----------------------------
PyQt5 Qt5Core.dll work-around
-----------------------------

Error in pyinstaller-created stuff when trying to run
'run_[app].exe' in Windows Command Prompt:

    ImportError: unable to find Qt5Core.dll on PATH

... but './run_[app].exe' works in gitbash.

WORK-AROUND:  fix_qt_import_error.py
(must be imported before any PyQt stuff)

