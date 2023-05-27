# NOTES ON ACTIVITIES

## Ownership and Context

Since `Activity` is a subclass of `ManagedObject`, it has an `owner` property,
which is an Organization, which can be a Project.  If the owner is a Project
(the usual case), the Activity occurs in the context of the Project.

## Function or System Doing the Activity

An `Activity` is performed by something, which is designated by its
`of_function` and `of_system` properties, which are populated by an instance of
`Acu` or `ProjectSystemUsage`, respectively.  All instances of Activity must
have their `of_function` and `of_system` properties populated by a usage that
occurs in their owning `Project`, except for instances of the `Mission`
subclass of `Activity`.

Since `Mission` is a subclass of `Activity`, it also has properties
`of_function` and `of_system`, but for `Mission` instances those properties are
`None`, since the `Mission` instance is an activity of **all** systems owned by
the `Project`.

## Children Activities

Any `Activity` can be decomposed into a set of sequential subsidiary `Activity`
instances, which refer back to their parent activity in their `sub_activity_of`
property (the inverse property, `sub_activities`, points to the list of
children of the parent `Activity`).

## Start, End, Duration

An `Activity` has parameters `start`, `end`, and `duration`.
