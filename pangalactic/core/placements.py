# -*- coding: utf-8 -*-
"""
Read and write the placement of a component within its assembly.

The objects involved -- ContextDependentShapeRepresentation and
Axis2Placement3D -- are described in NOTES_ON_ONTOLOGY_AND_DB.md under
"Component placement".  Placement belongs to the usage (the Acu) rather than
to the component product, because one product used at several places in an
assembly has a different placement at each.

This module knows nothing about CAD or about STEP files:  it is the
repository side of the import, and is equally the API a UI would use.
"""
from uuid import uuid4

from collections import namedtuple

from pangalactic.core import orb
from pangalactic.core.utils.datetimes import dtstamp

# the coordinates that make up an Axis2Placement3D
PLACEMENT_COORDS = ('location_x', 'location_y', 'location_z',
                    'axis_x', 'axis_y', 'axis_z',
                    'ref_direction_x', 'ref_direction_y', 'ref_direction_z')

# NOTE: pangalactic.node.step_import defines an identically shaped namedtuple
# of its own, deliberately:  it must not import the orb, so the two cannot be
# shared.  They are interchangeable by duck typing.
Placement = namedtuple('Placement', 'location axis ref_direction')

# the placement a component has when it sits at its parent's origin, aligned
# with its parent's axes
IDENTITY = Placement(location=(0.0, 0.0, 0.0), axis=(0.0, 0.0, 1.0),
                     ref_direction=(1.0, 0.0, 0.0))


def new_thing(cname, NOW=None, **kw):
    """
    Create a new instance of `cname` with a fresh oid, by whichever route the
    orb in use requires.

    Registers the oid in `orb.new_oids`, as `clone()` does, before adding the
    object to the session.  Without that, a later `orb.save()` call on this
    same object misclassifies it as pre-existing:  `orb.save()` decides "new"
    by `oid in self.new_oids or not self.get(oid)`, and SQLAlchemy's
    autoflush means `self.get(oid)` -- a plain query -- silently flushes the
    pending `add()` first, so the object is already a persisted row by the
    time it is checked.  It is then routed through `self.db.merge()` and
    logged as "is existing X, updating", which is misleading (nothing was
    updated, it is genuinely new) though not destructive for these classes,
    since neither is versioned.  Found by running a real import through the
    app rather than through direct-commit tests, which never exercise
    `orb.save()` at all.

    Args:
        cname (str):  name of the class to instantiate

    Keyword Args:
        NOW (datetime):  timestamp for create_datetime and mod_datetime
        kw (dict):  attributes of the new object
    """
    NOW = NOW or dtstamp()
    kw.update(oid=str(uuid4()), create_datetime=NOW, mod_datetime=NOW)
    if orb.is_fastorb:
        return orb.create_or_update_thing(cname, **kw)
    orb.new_oids.append(kw['oid'])
    obj = orb.classes[cname](**kw)
    orb.db.add(obj)
    return obj


def get_placement(acu):
    """
    Get the placement of an Acu's component within its assembly.

    Args:
        acu (Acu):  the usage

    Returns:
        Placement or None:  None if the usage has no placement, which is the
        normal case for an assembly whose geometry has not been imported.
        Note that this is *not* the same as the identity placement:  "we do
        not know where this sits" and "this sits at the origin" are different
        statements, and only the second is a placement.
    """
    for cdsr in (getattr(acu, 'shape_representations', None) or []):
        p = getattr(cdsr, 'placement', None)
        if p is not None:
            return Placement(
                location=(p.location_x, p.location_y, p.location_z),
                axis=(p.axis_x, p.axis_y, p.axis_z),
                ref_direction=(p.ref_direction_x, p.ref_direction_y,
                               p.ref_direction_z))
    return None


def set_placement(acu, placement, NOW=None):
    """
    Give an Acu's component a placement within its assembly, replacing any
    placement it already has.

    Args:
        acu (Acu):  the usage
        placement (Placement):  where the component sits, in metres, in the
            frame of the Acu's assembly

    Keyword Args:
        NOW (datetime):  timestamp for the new or modified objects

    Returns:
        list:  the objects created or modified, which the caller is
        responsible for saving -- this function does not commit.
    """
    NOW = NOW or dtstamp()
    coords = dict(zip(PLACEMENT_COORDS,
                      tuple(placement.location) + tuple(placement.axis) +
                      tuple(placement.ref_direction)))
    touched = []
    existing = [c for c in (getattr(acu, 'shape_representations', None) or [])
                if getattr(c, 'placement', None) is not None]
    if existing:
        # move the component rather than accumulating representations
        cdsr = existing[0]
        p = cdsr.placement
        for name, value in coords.items():
            setattr(p, name, value)
        p.mod_datetime = NOW
        cdsr.mod_datetime = NOW
        touched += [p, cdsr]
    else:
        p = new_thing('Axis2Placement3D', NOW=NOW,
                      id=f'{acu.id}-placement',
                      name=f'{acu.name} Placement', **coords)
        cdsr = new_thing('ContextDependentShapeRepresentation', NOW=NOW,
                         id=f'{acu.id}-shape-rep',
                         name=f'{acu.name} Shape Representation',
                         represented_usage=acu, placement=p)
        touched += [p, cdsr]
    return touched


def clear_placement(acu):
    """
    Remove an Acu's placement, returning the objects deleted.

    Args:
        acu (Acu):  the usage

    Returns:
        list of str:  the oids of the objects that were deleted
    """
    deleted = []
    for cdsr in list(getattr(acu, 'shape_representations', None) or []):
        p = getattr(cdsr, 'placement', None)
        deleted.append(cdsr.oid)
        orb.delete([cdsr])
        if p is not None:
            deleted.append(p.oid)
            orb.delete([p])
    return deleted
