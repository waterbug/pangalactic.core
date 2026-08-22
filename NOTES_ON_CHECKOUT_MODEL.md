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

Two things belong to an object rather than standing alone, and both caches
are keyed by object oid: its **parameters** (`parameterz`) and its **data
elements** (`data_elementz`).

**Why they are caches rather than ontology properties** (author, 2026-07-31):
this is deliberate and load-bearing. There are — conservatively — an order of
magnitude more parameters than there are properties (attributes) in the
ontology, so representing each as an ontology property would make the
ontology explode, and every addition would be a database schema change.
Keeping them in oid-keyed caches means new parameters and data elements can
be introduced in a new release **without touching the ontology or the
database schema**. They cannot be added at runtime (that was contemplated
once, but is not supported), so the set is fixed per release.

The consequence for check-out is that parameters and data elements are *not*
a side channel to be treated loosely — they are the bulk of the engineering
content, and they need the same rigour as attribute edits.

**Correction to an earlier draft of this section.** It previously said these
two "travel implicitly with an object and need no separate treatment". That
is true of the *serialization* — `serialize()` emits `d['parameters']` and
`d['data_elements']` with every `Modelable`, and `deserialize()` applies them
— but **not of the edit path**, and the difference is where offline work
breaks. Measured (see `pangalactic.node/pangalaxian_handlers_review.md` #2):
a parameter-only edit in `pgxnobject` returns before stamping
`mod_datetime`, so the object never enters the sync's "needs pushing" set;
`on_parms_set` is connectivity-gated and queues nothing; and on reconnect
`parameterz.update(<entire server cache>)` replaces each per-oid dict
wholesale. Net effect: **an offline parameter edit is silently reverted, and
a parameter added offline is silently dropped.** Data elements happen to
survive only because the code paths that change them do stamp and save the
object.

### 4a. Requirement: parameter and data-element edits are governed by the claim

Author's decision (2026-07-31): **offline parameter and data-element adds,
modifications and deletions must be permitted only for checked-out
("locked") objects, and must behave exactly as regular attribute editing
does.** Both are edited only through the `pgxnobject` editor, so there is a
single place to enforce it.

That gives three concrete requirements:

1. **Permission** — the same `access.py` test that governs attribute editing
   governs parameter and data-element editing. Under the §5 shape, offline
   that means the object is in `checked_out_oids` (or
   `locally_created_oids`); there is no separate, looser rule for
   parameters. `pgxnobject` should decline to offer editable parameter
   widgets when the object is not editable, exactly as it declines to create
   the Edit button today.
2. **Persistence — DONE.** A parameter or data-element change must mark the
   object as needing to be pushed, the same way an attribute change does.
   `pgxnobject.on_save`'s parameter-only branch now sets `modifier` and
   `mod_datetime` and calls `orb.save([self.obj])` before sending
   `"parms set"` — the same three assignments the general path makes further
   down. **Decision (author, 2026-07-31): stamp always, not only while
   disconnected** — simpler and more honest, since the object genuinely did
   change; the cost is some additional sync churn while connected, where
   `vger.set_parameters` already handles the change live.

   This is sufficient on its own, because `serialize()` already carries
   `d['parameters']` and `d['data_elements']` with the object: once the
   object is classified as newer than the server's copy, it enters
   `objs_to_save` and the values travel with it. **Verified by execution:**

   | | newer than server? | m after reconnect |
   |---|---|---|
   | before stamping | no — never pushed | 0.46 (edit lost) |
   | after stamping | yes | 999.0 (edit survived) |
3. **Reconciliation** — on check-in, parameter and data-element changes are
   part of what is applied and reported, not a side channel. The rule is
   **push before pull**: any replay of queued parameter changes must be
   sequenced *before* `get_parmz()`, exactly as the offline deletion queue
   must be replayed before `sync_project`/`sync_library_objects`.

   **`on_vger_get_parmz_result`'s wholesale `parameterz.update()` must be
   left alone.** An earlier draft of this section proposed merging per-oid
   instead, to protect un-pushed local values. That is wrong (author,
   2026-07-31): merging *was* implemented at one point, and in highly active
   collaborative use clients drifted out of sync; full replacement fixed it.
   It is inefficient but sufficiently performant, and since the server's copy
   is authoritative, replacement is what guarantees the client converges on a
   correct version.

   The replacement is a **convergence mechanism**, not a naive overwrite: any
   local drift — a failed push, a race, a partially applied update — is
   corrected on the next sync, whereas a merge lets a divergent local entry
   survive indefinitely with nothing able to remove it. This is also why
   `get_parmz` sits at the *tail* of the save chain: the local changes have
   already landed on the server before the pull replaces the cache. Protect
   offline work by guaranteeing the push, never by weakening the pull.

With (1) in place, the loss path closes at the source for everything else:
an object that is not checked out is not editable offline, so there are no
orphaned offline parameter edits to lose.

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

**All settled as of 2026-08-04.** 4, 5 and 6 were decided explicitly and are
struck through below. 1, 2 and 3 were settled in the course of building
phases 1 and 2 rather than as separate decisions; they are left un-struck
because the text still describes the reasoning, but here is where each landed:

- **1 (exclusive or advisory)** — exclusive. Phase 2 enforces claims in
  `access.py` via `is_writable_now()`; see §11.
- **2 (default expiry, and lapsed claims)** — 7 days, from `config`
  `checkout_days` (`DEFAULT_CHECKOUT_DAYS` in `vger.py`). On a claim lapsing
  while the user is still offline, the author's decision was *keep editing,
  reconcile at check-in*, which is what the reconciliation report in phase 3
  provides.
- **3 (admin override)** — implemented: `vger.release()` is restricted to a
  Global Administrator or the holder. The sub-question *"should the holder be
  notified?"* is the one piece never explicitly decided; today the release is
  published as `'checked in'` on the public channel, so the holder's client
  learns of it the same way every other client does, but there is no
  targeted notification.

1. **Exclusive or advisory?** This note assumes exclusive. Advisory
   (record and display, do not block) is less disruptive and could be
   phase 1, but does not eliminate conflicts.
2. **Default expiry**, and what happens to local edits when a claim lapses
   while the user is still offline. Suggest: the edits survive locally and
   are treated as ordinary conflicted changes at reconnect — which makes
   the reconciliation report a prerequisite.
3. **Admin override.** Presumably a Global Administrator may force-release,
   as with `thaw`. Should the holder be notified?
4. ~~**`mode_defz`** (§4) — project-level check-out, connected-only editing,
   or accept last-write-wins.~~
   **DECIDED (2026-08-04): accept last-write-wins, and fix the
   authorization gap.** Object check-out cannot cover project-scoped shared
   state, and a project-level claim type would be a new claim kind, new RPCs
   and new UI for one cache. Mode editing is a specialised, low-concurrency
   activity, and the client already guards its own copy by comparing
   `mode_defz_dts` before applying an incoming update.

   **The gap was worse than this note described.** It said
   `vger.update_mode_defs` "allows any user with project access to replace a
   project's mode definitions wholesale". In fact nothing tested for project
   access at all: `userid` was read and then used only in the published
   message, so *any authenticated user* could replace *any* project's mode
   definitions. The handler's own comment ("all users with access to the
   project are authorized") described an intent the code did not implement.
   The client had already been written for the refusal — it tests the result
   against `'unauthorized'` — so only the server half was missing.

   Now any role in the project authorizes, or global admin. Deliberately
   *any* role, not an admin one: discipline engineers add subsystems to
   `mode_defz` when defining modes at component level. The update remains a
   wholesale replacement with no server-side dts comparison, which is the
   accepted last-write-wins behaviour, and both facts are marked at the site.
   Tests: `test_sync.py` cases 11-13; the two refusal cases fail against the
   pre-fix code.
4a. ~~**Stamping** (§4a (2)) — always, or only while disconnected?~~
   **DECIDED (2026-07-31): always.** Simpler and more honest. Applied and
   verified; see §4a (2).
5. ~~**Audit trail** — delete `CheckOut` records on release, or retain
   them.~~
   **DECIDED (2026-08-04): keep deleting.** This is the status quo —
   `check_in()` and `release()` both `orb.delete()` the records — and it
   matches how `RoleAssignment` revocation already works, per §3. It keeps
   "is there an active claim?" a simple existence query; retaining would mean
   a `released` flag and updating every such query
   (`get_active_checkout`, `refresh_checkouts_state`, `check_out`'s
   already-held test), plus unbounded table growth. If history is wanted
   later, the `'checked in'` message already published on the public channel
   is a live record that can be logged without changing the model.
6. ~~**Scope limits** — should checking out an entire project be permitted,
   rate-limited, or require an administrator?~~
   **DECIDED (2026-08-04): leave as-is, no explicit limit.** The structural
   limits already bite, and are stronger than they look: expansion is one hop
   (§11.2), and **`Project` is not in `CHECKOUT_EXPANSION` at all**, so
   checking out a project claims only the Project object — not its systems.
   "Check out an entire project" is therefore not expressible in one call; a
   client would have to enumerate the oids itself. An arbitrary cap can be
   added later if real usage shows a need; adding one now would be a number
   chosen without evidence.

## 10. Suggested phasing

0. **Fix silent discards** (companion note §3.4) — independent of all of
   this, small, and immediately makes current behaviour honest.
1. **`CheckOut` class + RPCs + display, advisory only.** No enforcement, no
   `access.py` change. Gains real usage data on how people would use it,
   at low risk.
2. **DONE (2026-08-02).** See "Phase 2 as built" below.

   **Enforce server-side**, wire `checked_out_oids` into `access.py`,
   introduce `locally_created_oids`, and fix/retire `synced_oids`. This is
   the step that repairs the offline permission model. Two requirements
   attach here:
   - the dependent-object requirement in §7 — the check must resolve an
     object's owning item rather than testing the object's own oid, or claims
     will protect a Product while leaving its Ports editable by others;
   - the parameter/data-element requirement in §4a — the same permission test
     must gate parameter and data-element editing in `pgxnobject`, so that
     offline parameter work is confined to claimed objects rather than being
     allowed and then silently lost.
3. **DONE (2026-08-02).** See "Phase 3 as built" below.

   **Offline deletion queue**, replayed at check-in, plus the full
   reconciliation report. The parameter/data-element persistence and
   reconciliation items from §4a (2) and (3) belong here too: they share the
   queue-and-replay machinery, and the same ordering constraint — replay
   before the pull that would otherwise overwrite the replayed values
   (`vger.delete` before `sync_project`/`sync_library_objects`; queued
   parameter changes before `get_parmz`).

   Built as **two** queues rather than one, and the replay is chained inside
   `get_parmz()` rather than placed early in the sync chain — see §12.1 and
   §12.2 for why neither followed from the sketch above.

Phase 1 is deliberately reversible: if the model turns out not to fit how
teams actually work, nothing in `access.py` has been disturbed.

---

## 11. Phase 2 as built (2026-08-02)

Four differences from the sketch in sections 5 and 7, each of which turned
out to matter.

### 11.1 `state['checkouts']`, not `checked_out_oids`

Section 5 proposed `obj.oid in state['checked_out_oids']`. Phase 1 had
already built `state['checkouts']` as a **dict carrying the holder**:

    {oid: {'userid': str, 'expiry_datetime': str, 'purpose': str}}

which is the right shape, because a client's mirror contains **other
people's** claims too. The test is therefore "checked out *by me*", not
merely "checked out" — `access.get_checkout_holder()` returns the holder and
`is_writable_now()` compares it to the user.

### 11.2 Claims are expanded at check-out time, not resolved dynamically

Section 7 says the `access.py` check "needs to resolve an object's *owning*
item first and test the claim on that". It does not — resolution happens
once, server-side, when the claim is granted:

- `meta.CHECKOUT_EXPANSION` declares, per class, which attributes a claim
  extends along;
- `orb.get_checkout_set(obj)` walks them (MRO-aware, so `Model` inherits
  both `DigitalProduct`'s `has_files` and `Product`'s list);
- `vger.expand_checkout_oids()` applies it in `check_out`, `check_in` **and**
  `release`, so the set released is always the set claimed.

Two reasons. `get_perms()` is called in tight loops — every object in a save
batch, every row of a library refresh — so walking relationships per call
would be costly, whereas explicit records make it a dict lookup. And
`get_checkouts` and the pub/sub announcement then report the *true* claimed
set, so other clients grey out exactly the right things.

**The expansion rules** (author, 2026-08-02), which differ from section 7's
dependent-object list:

- one hop only — a checked-out assembly does **not** claim its components'
  own components;
- `components`/`q_components` expand to the **Acu**/**Qacu**, *not* to the
  component Products. A component is usually somebody else's part; what the
  holder needs is the ability to change the *usage* — which component, its
  reference designator, its quantity — and that is the Acu.

Measured: checking out one assembly granted 6 claims (the assembly, its 4
Acus, its Model), with the 4 component Products correctly unclaimed.

### 11.3 The server keeps a mirror too

`access.py` is shared, and the claim data otherwise lives in two places (db
on the server, mirror on the client). vger now maintains `state['checkouts']`
in the same shape — primed at startup, refreshed after every claim mutation
and on `get_checkouts` — so `get_perms()` has one code path on both sides and
does not query the db per call.

Without this the server's mirror would be empty and **every claim would be
invisible to `vger.save()`**, i.e. enforcement would be inert.

### 11.4 Section 4a(1) needed no code

The requirement that parameter and data-element editing be governed by the
same permission test turned out to be satisfied by the `access.py` change
alone. `pgxnobject` already gates parameter widgets on `self.edit_mode`,
which derives from `'modify' in get_perms(obj)`. Verified:

| state | `edit_mode` | editable parameter widgets |
|---|---|---|
| online, unclaimed | True | 2 |
| online, claimed by someone else | False | 0 |
| offline, unclaimed | False | 0 |
| offline, claimed by me | True | 2 |

### 11.5 What `synced_oids` became

It is no longer consulted for permissions. `state['locally_created_oids']`
replaces it, maintained precisely: objects are added when created locally
(`on_mod_object_signal`, `new=True`) and removed only when the repository
confirms them (`on_vger_save_result`, from `new_obj_dts`/`mod_obj_dts`).

Deliberately **not** cleared wholesale at sync: an object whose save was
*refused* must stay locally created, and therefore still editable offline,
rather than being forgotten because a sync happened to run.

**`synced_oids` was retired on 2026-08-04.** It had become write-only:
maintained in three places, consulted by nothing. Removed were the single
assignment in `pangalaxian.on_sync_result`, the two per-oid removals (in
`on_rpc_vger_delete_result` and the project-deletion path), the state-key
entry and footnote in `NOTES_FOR_DEVELOPERS.md`, and 38 fixture assignments
in `test_orb.py`. The `_checkout_state` helper lost its `synced` keyword.
Nothing else changed: the key was already inert, so all 87 core tests pass
before and after.

### 11.6 Tests

Six cases added to `test_orb.py` (37-42), in the existing style. Against the
**old** `access.py`, five of the six fail — so they discriminate the change
rather than merely describing it. Case 42 passes both ways by design: it
asserts that a claim is *necessary but not sufficient*, since entitlement is
unchanged.

Case 40 is the one worth keeping in view: it covers **offline with the object
absent from `synced_oids`**, which no existing case reached — every case from
1-36 puts its object *in* `synced_oids`. That absence is exactly the branch
that used to grant full permissions on objects the user had not created.

---

## 12. Phase 3 as built (2026-08-02)

Phase 3 (§10 item 3) is complete: the offline deletion queue, the full
reconciliation report, and the parameter/data-element items from §4a (2)
and (3). Four things are worth recording, because in each case what was
built differs from what §10 anticipated.

### 12.1 Two queues, not one — and for different reasons

§10 treats "queued parameter changes" as the same machinery as the object
deletion queue. It is the same *machinery*, but it turned out not to be
needed for the same *things*, and the asymmetry is not obvious:

- **Parameter and data-element additions and modifications need no queue at
  all.** They are carried in the object's own serialization (`parameters` /
  `data_elements`), so they reach the repository whenever the object is
  pushed. What was actually missing was the push — the parameter drop
  handlers in `pgxnobject` did not stamp `mod_datetime`, so the object was
  never classified as modified. The data-element drop handler beside them
  *did* stamp; the two paths had simply drifted apart. This is §4a (2)
  applied to the one path it had not yet reached.
- **Deletions cannot travel that way and do need a queue.**
  `deserialize_parms()` *merges*: it assigns each pid present in the incoming
  dict and never removes one that is absent, so "this pid is gone" and "this
  pid was not mentioned" are indistinguishable to the server. Note this is
  **not** a defect to fix in `deserialize_parms` — merge-on-deserialize is
  what makes a partial push safe. The deletion needs its own explicit signal.

So `p.core.parm_del_queue` records only deletions, keyed `kind|oid|id` so it
is self-deduplicating, written to its own file the moment an item is queued,
and re-read in `orb.start()` because offline work spans sessions. Both halves
of the asymmetry were verified by execution rather than by reading, since the
whole design rests on them.

### 12.2 Ordering is enforced where the hazard is, not early in the chain

§10 says the replay must be sequenced before `get_parmz()`, and the obvious
reading is "put it early in the sync chain", which is what the object
deletion queue does (`replay_deletion_queue` is first, before
`sync_project`/`sync_library_objects`).

That is not sufficient for parameters. `get_parmz()` is *also* reached
directly from the "parameters set" pubsub handler, which can arrive at any
moment after reconnecting — so early placement would have made the ordering
incidental rather than guaranteed. `replay_parm_del_queue()` therefore
returns a `DeferredList` and is chained ahead of the rpc **inside**
`get_parmz()` itself, so the pull genuinely waits on the push. It is a no-op
when the queue is empty, which is the usual case.

### 12.3 Refusals are settled, not retried — and are reported

Neither §10 nor §4a says what happens when the repository *refuses* a
replayed operation. The rule adopted, for both queues:

**settle the entry, and report it.** Retrying is pointless — the user will
not acquire the permission by trying again, and an entry that can never
succeed would replay on every sync forever. But the local state is about to
be corrected by the authoritative server copy, and that correction must not
be silent. This is the §3.4 principle of the companion note applied to
replay.

Refusals are reported on the *live* path too, not only the queued one: a
connected user whose deletion is refused has already had it applied locally
and would otherwise watch it revert at the next sync with no explanation.

### 12.4 Phase 3 forced an authorization fix that phase 2 had missed

`vger.add_parm()`, `del_parm()`, `add_de()` and `del_de()` performed **no
authorization check at all** — any user could add or remove any parameter or
data element on any object, and all four always reported success. Their batch
equivalents `set_parameters()`/`set_data_elements()` had always checked
`"modify"`; these four had simply been missed.

This matters more than a routine gap, because §4a's whole premise is that
parameter editing is governed by the claim. Phase 2 put `is_writable_now()`
inside `get_perms()`, but these four never called `get_perms()`, so the claim
did not reach them. Routing them through it closed both holes at once. Until
that landed, a claim protected an object's attributes while leaving its
parameters editable by anyone — and parameters are the bulk of engineering
content (§4).

### 12.5 What is deliberately *not* enforced

Read access is not applied to the parameter caches: `vger.get_parmz()`
returns the whole `parameterz` cache to any caller and does not take
`cb_details` at all. Decided and left as-is (2026-08-02) — the per-oid filter
costs ~45 ms per oid and does not warm up, which is minutes-to-an-hour on a
call made every sync, and the caches are keyed by opaque oid with no
identifying fields. Full reasoning in `NOTES_FOR_DEVELOPERS.md` under
"Read access is NOT applied to the parameter caches".

### 12.6 Still open after phase 3

- ~~**`synced_oids`**~~ — **RETIRED 2026-08-04.** See §11.5. The test-suite
  question that made it a decision rather than a chore turned out to be
  answerable: the ~38 fixture lines were assignments, not assertions, so
  removing them could not change what the tests prove, and the one case whose
  *description* depended on the key (case 40) was reframed rather than
  deleted — it is still the negative baseline of the check-out series, now
  pinned on the absence of a claim and of a locally-created record, which is
  what actually decides the outcome.
- **§9 decisions 4, 5 and 6** — `mode_defz` scope, audit trail on release,
  and check-out scope limits — are untouched and remain prerequisites for
  calling the model finished.
- **`vger.update_mode_defs`** still allows any user with project access to
  replace a project's mode definitions wholesale (§4a), which is decision 4.

## 13. Timeline objects are excluded from offline work (2026-08-21)

**Decision (author):** Activities and ActivityControls can be edited only
while connected. They are not offered for check-out, and cannot be written
while disconnected — not by a holder, not even by the client that created
them.

(Activities were excluded first, with the controls left open; the author
extended it to them the same day. The reasoning below is what covers both.)

**Why.** §4 chose the granularity of a claim by asking what a user actually
edits while working on an object. A timeline object does not answer that
question the way a Product does. An Activity's `duration` and its start and
stop times are interrelated with those of every other Activity in its
timeline, and the ConOps modeler adjusts the others as one is changed — so an
edit to one activity is an edit to the timeline. A claim on a single activity
therefore does not cover the work it enables, which is the one property a
claim has to have.

`ActivityControl` and its subclasses (`Decision`, `Merge`) are not
Activities, but they sequence the activities in a timeline, so the same
reasoning reaches them.

Claiming the whole timeline would fix that, and is a coherent idea, but it is
a different and larger one than claiming an object: what counts as the
timeline, what happens to a claim on a Mission versus one of its
sub-activities, and how it interacts with the modeler's own editing model are
all open. The timeline widget is also still evolving and has not yet been
used in the field (author, 2026-08-21), which is a poor moment to fix a
locking design around it.

So rather than support offline timeline work badly, it is excluded. This is
reversible: nothing here forecloses a timeline-level claim later, and the
exclusion is expressed in four places that would each be removed.

**Where it is enforced.**

The rule itself is **one definition**: `access.offline_excluded`, a list of
class names, and `access.is_offline_excluded()`, which tests an object
against them by `isinstance` — so the subclasses come along (Mission and Test
with Activity, Decision and Merge with ActivityControl) and extending the
rule is a one-line edit in one file. Three of the four enforcement points
below consult it rather than repeating the class list, which is what
extending it from Activities to the controls made obviously necessary: the
first version had the same `isinstance` written out in three repos.

1. `access.is_writable_now()` rule [5] — the substantive one. Placed *ahead*
   of the holder test, not after it, so that a claim predating this rule
   cannot grant offline write access.
2. `PrepareForOfflineDialog.classify()` — they are not offered, since
   offering a claim that access.py will not honour would promise something
   that does not work.
3. `vger.check_out()` — refuses them with `not_offline_editable`. The server
   decides, so a client that asks anyway has to get the same answer.
4. `meta.CHECKOUT_EXPANSION` — `'activities'` was removed from the `Product`
   expansion. Left there, every check-out of a product with activities would
   have reported denials the user never asked for. (Nothing expands to an
   ActivityControl, so there was nothing to remove for them.)

**One consequence for testing.** Because the rule resolves its class names
through the *access* module's orb, a test that stubs `vger.orb` has to stub
`access.orb` as well — `test_vger.CheckOutRpcTests` does, with a note saying
why.

**Consequences in the interface.** `timeline.set_table()` now composes the
role test (entitlement) with `is_writable_now()` (exclusivity), exactly as
`get_perms()` does, so the Mission Details table is read-only while
disconnected — that table is where durations are edited, and editing one
adjusts the rest, which is the whole hazard. The two drop guards in
`timeline.py` already consulted `get_perms()` and so needed no change, but
their popup said the user's *roles* did not permit the operation, which for a
disconnected user is both wrong and a waste of their time; `not_permitted()`
now distinguishes the two causes.

**Still not covered:** nothing else in a timeline is a distinct persisted
object — `Flow` was already excluded from claims by §4's independent-existence
rule, and the timeline's structure otherwise lives in the activities' own
attributes. If a new timeline class is ever added, it belongs in
`access.offline_excluded`.

