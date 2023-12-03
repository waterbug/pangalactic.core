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

## Start, End, Duration

An `Activity` has parameters `start`, `end`, and `duration`.
