# NOTES ON ACTIVITIES

## Ownership and Context

Since **Activity** is a subclass of **ManagedObject**, it has an **owner**
property, which is an **Organization**, which can be a **Project**.  If the
**owner** is a **Project** (the usual case), the **Activity** occurs in the
context of the **Mission**, a special subclass of **Activity** that is defined
as the top level **Activity** of a **Project**, so all other **Activity**
instances that occur within the **Mission** are **sub_activities** either of
the **Mission** itself or of another **Activity** within the scope of the
**Mission** **Activities**.

## Function or System Doing the Activity

In general, an **Activity** is performed by an item, which is designated by the
`of_system` property, which can be populated by an instance of either `Acu` or
`ProjectSystemUsage`.  All instances of Activity must have their `of_system`
properties populated by a usage that occurs in their owning `Project`, except
for instances of the `Mission` subclass of `Activity`, for which `of_system` is
not populated since the Mission is not an activity of a specific system but of
all project systems.

## Children Activities

Any `Activity` instance can be decomposed into a set of sequential subsidiary
`Activity` instances. The `sub_activity_of` property refers back to the parent
activity and is the inverse property of `sub_activities`, which points to the
list of children of the parent activity.

### How Activities are created

Activities are not created or edited like other objects.  `p.node.timeline`
provides a timeline widget that accepts a block dragged from a palette,
creating an Activity at the position it is dropped; double-clicking an
existing Activity opens *its* timeline, and blocks dropped there become its
sub-activities.  The user guide (`p.node.docs/user_guide.md`) describes the
workflow.

The consequence for this module:  **sub-activities are created exclusively in
that context, are never re-parented, and are not to be edited through the
`PgxnObject` editor.**

### Deserializing the parent link -- `act_to_sao`, and what is untested

`sub_activity_of` is the one *self-referential* link among Activities, and
that makes deserialization order awkward: `DESERIALIZATION_ORDER` can place
`Activity` after the classes an Activity refers to (Acu, PSU, Mission), but it
cannot order Activities *among themselves*, so a child may be deserialized
before its parent exists.

`serializers.deserialize()` handles this in two passes. During the main loop
it records every Activity's intended parent:

```python
if so['_cname'] == 'Activity':
    act_to_sao[so['oid']] = so.get('sub_activity_of', '')
```

and after everything is deserialized it sets the links:

```python
for act_oid, sao_oid in act_to_sao.items():
    act = orb.get(act_oid)
    sao = orb.get(sao_oid)
    if act and sao and not act.sub_activity_of:
        act.sub_activity_of = sao
        orb.db.commit()
```

**There is no test coverage of any of this** -- searching all three repos for
`sub_activity_of` or `act_to_sao` in test modules returns nothing (2026-08-21).
It is worth writing, because reading the fix-up pass suggests several
behaviours that may or may not be intended, and nothing currently
distinguishes them:

* **A parent outside the batch is silently dropped.** If `sao_oid` names an
  Activity that is neither in the batch nor already in the database,
  `orb.get()` returns None and the link is simply not made -- no warning, no
  record that a parent was expected. That is the same shape of silent loss
  that the `db.yaml` and STEP external-reference bugs turned out to be.
* **`not act.sub_activity_of` means a parent is never *changed* -- and that
  is correct.** *(Answered by the author, 2026-08-21.)* Sub-activities are
  intended to be created **exclusively** in the ConOps / timeline modeller,
  by double-clicking an existing Activity to open its timeline and dropping
  a block from the palette onto it; they are **never re-parented**, and are
  never to be edited through the `PgxnObject` editor. So the guard is not
  defensive, it is the model: a parent is assigned once, at creation.

  The code bears this out. Every assignment of `sub_activity_of` outside the
  fix-up pass is a *constructor argument* at creation time, all of them in
  `p.node.timeline` (`clone(..., sub_activity_of=...)` at three sites). The
  only other write anywhere is `orb.delete()`, which sets it to `None` on the
  children of an Activity being deleted -- i.e. orphaning, not re-parenting.

  Note that this makes the *first* bullet sharper rather than softer: if a
  parent cannot be resolved, that is not a routine ordering artefact but a
  sign that something is wrong, since in normal use the parent is created
  before the child and travels with it.
* **An empty string is a legitimate value here.** `so.get('sub_activity_of',
  '')` yields `''` for a top-level Activity, which then makes a pointless
  `orb.get('')` call per top-level Activity. Harmless, but it means the map
  does not distinguish "no parent" from "parent not yet resolved".
* **`orb.db.commit()` is inside the loop**, so a batch of *n* re-parented
  Activities costs *n* commits.

None of these is known to be a bug. They are the questions a test would have
to answer, which is the reason to write one.

## Start, End, Duration

An `Activity` has parameters `start`, `end`, and `duration`.
