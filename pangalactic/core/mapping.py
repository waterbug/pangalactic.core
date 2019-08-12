"""
Functions for data conversion between releases.

Note that not all schema modifications require data conversion functions; in
some cases, the serialization/db-drop-create/deserialization process will
suffice.

Examples of schema mods that do not require a conversion function include:

* Adding or renaming an unpopulated class or attribute
* Removing an attribute (populated or not)

Examples of schema mods that require a conversion function include:

* Renaming a populated class or attribute
* Removing a populated class
* Adding an attribute with a non-null default value

`schema_mods`:  a list of the releases that include schema modifications

`fns`: a dictionary that maps release numbers to the data conversion functions
they require
"""
schema_version = '1.0.4'

def to_01devXX(sos):
    """
    Convert data to 0.1.devXX schema.

    Args:
        sos (list):  serialized objects to be transformed
    """
    for so in sos:
        pass

# `schema_maps` dictionary maps versions to conversion functions
schema_maps = {'0.1.devXX' : to_01devXX}

