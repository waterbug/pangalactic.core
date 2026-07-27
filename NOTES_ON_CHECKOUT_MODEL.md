# Design note: explicit check-out model for offline work

Written 2026-07-26. Companion to
`pangalactic.node/NOTES_ON_OFFLINE_AND_SYNC.md`, which assesses the current
offline/sync behaviour and validates it against the live test server. This
note proposes the check-out model itself.

Placed in `pangalactic.core` because the load-bearing pieces — a new
ontology class and changes to `access.py` — are core's; the RPCs are
`vger`'s and the workflow is `node`'s.

---

## 1. Why this, and how it fits what already exists

`NOTES_FOR_DEVELOPERS.md` ("Write (Edit) Access") states the authorization
model as: Person A may edit Object X if A is X's `creator`, **or** X is
owned by Organization Z and A is an Administrator there or a Global
Administrator, **or** A holds a Role in Z associated with a Discipline that
uses X's ProductType.

Note what that model does **not** mention: connectivity. The documented
model is purely about *entitlement* — may this person edit this thing at
all. The requirement to be connected is an undocumented implementation
layer added on top (`server_or_connected_client` in `access.py`), and it is
currently the source of the offline permission defects.

The check-out model separates the two questions that are presently
conflated:

- **Entitlement** — may this user edit this object at all? Role, creator,
  ownership, CM state. Connectivity is irrelevant. This is what
  `NOTES_FOR_DEVELOPERS.md` already describes, and it does not change.
- **Exclusivity** — is it safe for this user to edit it *right now, while
  disconnected*, without risking a conflict? This question has no
  representation in the system today. Check-out answers it.

Relationship to the existing CM mechanism: **freeze** marks an object as a
repository-wide, indefinite, read-only baseline. **Check-out** marks it as
temporarily, exclusively writable by one person. They are complementary and
mutually exclusive per object — a frozen object cannot be checked out, and
a checked-out object cannot be frozen until it is checked in.

## 2. The concept

A **check-out** is a claim, recorded in the repository, that a named user
intends to make changes to a set of objects and that no one else may change
them until the claim is released. It is:

- **explicit** — the user chooses what to take, before going offline;
- **exclusive** — one holder at a time (this is what removes conflicts);
- **time-bounded** — it expires, so a forgotten check-out cannot block a
  team indefinitely;
- **visible** — published on the existing project channels, so collaborators
  see who holds what.

The payoff, in terms of the behaviour measured in the companion note: for a
checked-out object the stale-edit conflict (scenario C, where an authorized
offline edit is silently discarded because someone else touched the object
meanwhile) becomes **impossible by construction** rather than something the
reconciliation layer must detect and report.

## 3. Ontology addition: a `CheckOut` class

There is no lock/check-out concept in the ontology today (confirmed with
the author). Proposed as a new class rather than an attribute on `Product`,
for three reasons: it must apply to more than Products (`Acu`,
`ProjectSystemUsage`, `Model`, `Document` …); it carries data beyond a
boolean (holder, times, purpose); and it needs to be queryable,
serializable, and publishable — all of which come free for a domain class.
It follows the shape of `RoleAssignment`, which reifies a similar
"who ↔ what ↔ context" relationship.

Suggested properties (subclass of `Identifiable`, or `ManagedObject` if it
should itself be ownable):

| property | range | notes |
|---|---|---|
| `checked_out_item` | `Identifiable` | the object claimed |
| `checked_out_by` | `Person` | the holder |
| `checkout_datetime` | datetime | when granted |
| `expiry_datetime` | datetime | when it lapses; server-enforced |
| `purpose` | str | free text shown to collaborators |

Release is modelled as **deletion** of the `CheckOut` instance rather than a
`released` flag — it keeps queries simple ("is there a CheckOut for this
oid?") and matches how `RoleAssignment` revocation already works. If an
audit trail of past check-outs is wanted, that is a separate decision and
argues for the flag instead.

Schema change implications: a version bump plus a `schema_maps` entry in
`mapping.py`; `MINIMUM_CLIENT_VERSION` already exists to force client
upgrades (the live server currently reports `4.3`).

## 4. Granularity — what gets checked out

The natural unit of work in this application is not a single object but a
**usage-rooted subtree**: a product, its `Acu`s, and the component products
beneath it. Editing a subsystem design means touching all of them.

Proposal: the atomic unit is the individual object (one `CheckOut` per
oid), but the client offers "check out this assembly", which expands the
selection to the working set — the product, its `Acu`s, and those
components the user is entitled to edit — and requests them as one batch.
Partial grants are reported per-oid so the user knows exactly what they got.

Two things travel implicitly with an object and need no separate treatment,
because both caches are keyed by object oid: its **parameters**
(`parameterz`) and its **data elements** (`data_elementz`).

**`mode_defz` is the exception and needs a decision.** It is project-scoped
shared state, not object-scoped, and `vger.update_mode_defs` currently
allows any user with project access to replace a project's mode
definitions wholesale. It cannot be covered by object check-out. Options: a
project-level check-out for modes; treat modes as connected-only editing;
or leave as-is and accept last-write-wins there. See §9.

## 5. Permission integration — replacing the load-bearing bug

This is the part that matters most, and the reason check-out cannot be
bolted on without touching `access.py`.

As measured in the companion note: today every normal grant of
`modify`/`delete` is gated on `server_or_connected_client`, so the **only**
path granting write permission offline is the `object_not_synced` branch —
which is defective, and which currently makes offline editing work *only by
accident*. Correcting `synced_oids` in isolation would leave the user
view-only on everything, including their own work.

Check-out supplies the missing legitimate path. Proposed shape:

```python
# entitlement: unchanged, exactly as NOTES_FOR_DEVELOPERS describes
#   (creator / admin / role+product_type), and CM state (frozen)

# exclusivity: replaces the bare "connected" test
writable_now = (
    server                                   # server side: always
    or (client and connected)                # online: as today
    or (client and obj.oid in state.get('checked_out_oids', []))
    or (client and obj.oid in state.get('locally_created_oids', []))
)
```

`checked_out_oids` mirrors the server's authoritative `CheckOut` records,
refreshed at sync and updated by pub/sub. `locally_created_oids` covers the
genuine case the current `object_not_synced` branch was reaching for —
objects created on this client that the repository has never seen — and can
be maintained precisely rather than inferred.

Two consequences worth stating plainly:

1. Offline permissions become exactly **online permissions ∩ checked-out
   set**. No over-permission (the 428-object problem), and no
   under-permission (view-only on your own work).
2. `synced_oids` stops being load-bearing and can then be fixed to mean
   what its name says — every oid confirmed present on the server — or
   retired entirely in favour of `locally_created_oids`, which is the
   property the code actually wants.

## 6. Protocol

New `vger` RPCs, following existing conventions (`cb_details` for caller
identity, dict/tuple returns, pub/sub on the project channels):

- `vger.check_out(oids, expiry=None, purpose='')`
  → `{'granted': [oids], 'denied': {oid: reason}}`
  with reasons drawn from a fixed set: `already_held_by:<userid>`,
  `frozen`, `no_permission`, `unknown_oid`. Authorization reuses
  `get_perms` server-side, so entitlement rules stay in one place.
- `vger.check_in(oids, serialized_objs=None)` — applies the edits **and**
  releases the claims in one operation, so there is no window in which the
  objects are released but the changes have not landed.
- `vger.release(oids)` — abandon without saving.
- `vger.get_checkouts(project_oid=None)` — current state, for display and
  for populating `checked_out_oids` at sync.

Pub/sub on existing channels: `{'checked out': [(oid, userid, expiry)]}`
and `{'checked in': [oids]}`, so other clients grey out affected objects
live. This reuses the machinery that already carries `frozen`/`thawed`.

Server-side expiry sweep releases lapsed claims and publishes the release.

## 7. Interaction with existing mechanisms

- **Freeze / thaw.** Both already require connectivity, which is correct —
  CM state changes are repository-wide facts. Add: a frozen object cannot
  be checked out; a checked-out object cannot be frozen until checked in.
- **Deletion.** Deleting a checked-out object offline is legitimate. It
  should be recorded in the offline deletion queue proposed in the
  companion note and replayed as part of `check_in`, which is also the
  natural moment to authorize it.
- **Creator-based entitlement.** Unchanged. A user editing their own
  never-synced object needs no check-out — that is what
  `locally_created_oids` covers.
- **SANDBOX.** Already universally modifiable; simplest to exempt it from
  check-out entirely.
- **Conflict policy.** For checked-out objects the question disappears.
  For everything else, the current newer-timestamp-wins/older-silently-
  dropped behaviour remains, and still needs the reporting fix — check-out
  narrows the problem rather than eliminating it.
- **Dependent objects must inherit the claim (phase 2, confirmed by the
  author).** Some objects have no independent existence and are always
  worked on through an owning object: a `Port` (only ever added or removed
  as part of work on its `Product`), a `Flow` (belongs to the `Acu` context
  it connects), a `RepresentationFile` (the payload of a `Model` or
  `Document`), and `Relation`/`ParameterRelation` (reify a relationship of
  another object). `PrepareForOfflineDialog` already declines to *offer*
  these, since a claim on one alone would mean nothing.

  Enforcement has to complete the other half: **a claim on an object must
  extend to its dependent objects, in both directions.** The holder must be
  able to edit them (otherwise a checked-out Product would still refuse
  edits to its own Ports), and everyone else must be prevented from editing
  them (otherwise the claim protects the Product but leaves its Ports open,
  which defeats the purpose). So the phase-2 change to `access.py` cannot
  simply test `obj.oid in checked_out_oids` — it needs to resolve an
  object's *owning* item first and test the claim on that. The mapping is
  the one listed above.

## 8. Client workflow

- **Prepare for offline work**: a dialog listing the current project /
  selected assembly, showing what would be claimed, what is unavailable and
  why, and the expiry. One confirmation, one batched `check_out` call.
- **Indicator**: a toolbar/tree icon in the manner of the existing `frozen`
  icon, showing "checked out by *you*" versus "checked out by *X*".
- **"My check-outs"**: a list with per-item check-in and release.
- **On reconnect**: run check-in, then show the reconciliation summary
  described in the companion note — what was applied, refused, restored,
  conflicted.
- **Disconnecting with nothing checked out** should warn plainly that no
  editing will be possible offline. Under this model that is the correct
  behaviour rather than a bug, but it must not be a silent surprise.

## 9. Decisions required

1. **Exclusive or advisory?** This note assumes exclusive. Advisory
   (record and display, do not block) is less disruptive and could be
   phase 1, but does not eliminate conflicts.
2. **Default expiry**, and what happens to local edits when a claim lapses
   while the user is still offline. Suggest: the edits survive locally and
   are treated as ordinary conflicted changes at reconnect — which makes
   the reconciliation report a prerequisite.
3. **Admin override.** Presumably a Global Administrator may force-release,
   as with `thaw`. Should the holder be notified?
4. **`mode_defz`** (§4) — project-level check-out, connected-only editing,
   or accept last-write-wins.
5. **Audit trail** — delete `CheckOut` records on release, or retain them.
6. **Scope limits** — should checking out an entire project be permitted,
   rate-limited, or require an administrator?

## 10. Suggested phasing

0. **Fix silent discards** (companion note §3.4) — independent of all of
   this, small, and immediately makes current behaviour honest.
1. **`CheckOut` class + RPCs + display, advisory only.** No enforcement, no
   `access.py` change. Gains real usage data on how people would use it,
   at low risk.
2. **Enforce server-side**, wire `checked_out_oids` into `access.py`,
   introduce `locally_created_oids`, and fix/retire `synced_oids`. This is
   the step that repairs the offline permission model. Note the
   dependent-object requirement in §7: the check must resolve an object's
   owning item rather than testing the object's own oid, or claims will
   protect a Product while leaving its Ports editable by others.
3. **Offline deletion queue**, replayed at check-in, plus the full
   reconciliation report.

Phase 1 is deliberately reversible: if the model turns out not to fit how
teams actually work, nothing in `access.py` has been disturbed.
