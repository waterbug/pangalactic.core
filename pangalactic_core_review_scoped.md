# pangalactic.core review — rescoped pass (2026-07-19)

This revisits `pangalactic_core_review.md` and `parametrics_review.md` under
two new constraints for this review activity:

1. **Excluded files** (experimental, not in production use):
   `fastorb.py`, `smerializers.py`, `tachistry.py`. Every finding that lived
   only in one of these files has been dropped from this pass. Where a bug
   was duplicated between an excluded file and an in-scope file (e.g.
   `registry.py`/`tachistry.py`), only the in-scope copy is retained below.
2. **Excluded topic**: requirements management (`Requirement` objects,
   requirement allocation/margin computation, and the caches that back them:
   `rqt_allocz`, `allocz`, `refresh_rqt_allocz`, `compute_margin`,
   `compute_requirement_margin`, `recompute_margins`, `get_next_rqt_seq`,
   `gen_rqt_id`). This is broader than "files with 'rqt' in the name" — for
   example `parametrics.py`'s `compute_margin()` looks generic but is
   entirely built on `rqt_allocz` and requirement `Constraint` objects, so it
   and its `recompute_margins()`/`compute_requirement_margin()` companions
   are excluded even though they live in an in-scope file.

Every surviving finding below was **re-verified against the current source**
(current HEAD `b4b1a44` plus uncommitted working-tree changes to
`fastorb.py`/`parametrics.py`/`uberorb.py`, none of which touch anything
in-scope here) — not just carried forward from the prior doc. Line numbers
are current as of this pass.

## Resolved since the last review

- **`UberORB.get_project_parameters`** (`uberorb.py:2327`) — the
  `UnboundLocalError` when a project has no Observatory/Spacecraft/Launch
  Vehicle is fixed (commit `b4b1a44`). Verified by reading the current
  implementation.
- The three requirements-scoped fixes from the last pass
  (`get_next_rqt_seq`, `gen_rqt_id`, regression tests) are out of scope for
  this pass per the exclusion above, but remain fixed.

---

## Findings (most severe first)

### 1. `parametrics.py`: a failed cache write destroys the file it was writing — on vger, that is the authoritative copy
`pangalactic/core/parametrics.py:443-449` (`save_parmz`), `1793-1799`
(`save_data_elementz`), `2181-2187` (`save_mode_defz`)

*(New finding, surfaced by the author's explanation of the cache
architecture — see the note at the end of this entry.)*

All three use the same truncate-then-serialize shape that was just fixed in
`__init__.py`:
```python
with open(fpath, 'w') as f:                  # truncates immediately
    f.write(json.dumps(stored_parameterz, ...))   # raises -> file left empty
except:
    log.debug('  ... writing parameters.json file failed!')
```
`open(..., 'w')` truncates before `json.dumps` runs, so any value the JSON
encoder can't handle empties the file. **Verified by execution:** seeding
`parameterz` with two objects' parameters, saving (132 bytes), then putting
a `Decimal` in one value and saving again leaves `parameters.json` at
**0 bytes**; the next `load_parmz()` returns `'fail'` and the cache comes
back empty. A partial `f.write()` (ENOSPC/quota) is a second route to the
same outcome, leaving truncated, invalid JSON.

Three things compound it:
- **No upstream to recover from (server side).** Per the author, these
  three caches are the only ones not derivable from the database —
  `parameterz`, `data_elementz`, and `mode_defz` persist *solely* as
  `parameters.json`, `data_elements.json`, and `mode_defs.json`. Every
  other cache is a runtime performance optimization rebuilt from the db.
- **The same call zeroes the backup too.** `uberorb.save_caches()`
  (`uberorb.py:602-617`) calls each `save_*` twice — once for `self.home`,
  once for the backup dir — so an unserializable value fails identically in
  both. Only *previous days'* dated backup dirs survive (the dir name is a
  date stamp), so recovery costs everything since the last good day.
  `vger.py`'s `shutdown()` reaches this on every server exit.
- **It is reported as success.** Each `save_*` swallows the exception into
  a `log.debug` (`parametrics.py:449, 1799, 2187`), while `save_caches()`
  unconditionally logs `'cache saves completed ...'` and `'cache backup
  completed.'` at `log.info` (`uberorb.py:606, 621`). At default INFO level
  the operator is told the save succeeded.

**Severity is asymmetric between client and server** (per the author): on
the client these files are a local working copy that re-syncs from the
repository on the next connection, so the exposure is limited to
extended disconnected use. On **vger** they are the authoritative store,
with nothing to re-sync from — that is where this is critical. The
client-side synchronization behavior will be assessed during the
`pangalactic.node` review.

Fix is the same one applied to `__init__.py`: build the JSON string first,
then open and write. Worth pairing with raising the failure log from
`debug` to `error`, and having `save_caches()` report actual per-file
outcomes rather than unconditional success.

### 2. `serializers.py`: no FK-integrity guard for `Acu`/`ProjectSystemUsage` (unlike `Port`/`Flow`)
`pangalactic/core/serializers.py:821-850`
Missing `of_product` on `Port` and missing `start_port`/`end_port` on `Flow`
are explicitly special-cased and added to `ignores`; there's no equivalent
branch for `Acu` missing `assembly`/`component` or `PSU` missing
`project`/`system` — such objects get constructed anyway. A single bad FK
can raise an `IntegrityError` at the shared `orb.db.commit()` (~913),
**aborting the entire deserialize batch**, including unrelated valid
objects.

    **NOTE**: added fk integrity check for Acu and PSU.

### 3. `parametrics.py`: `get_flight_units()` indexes a `Comp` namedtuple with dict syntax
`pangalactic/core/parametrics.py:1524-1541`
`componentz[assembly_oid]` holds a list of `Comp` namedtuples (built via
`Comp._make(...)` at line 141), but `get_flight_units` does
`component['oid']` / `component['quantity']` — dict-style subscripting on a
namedtuple raises `TypeError: tuple indices must be integers`. Guaranteed
crash if this function is ever called; no callers found in this checkout
(caveat below applies).

    **NOTE**: this is indeed a bug; however, the fix is not to use integer
    indices but rather to use the special capability of namedtuples (versus
    tuples) -- i.e., access fields using "readable dot notation" (in this case,
    component.oid and component.quantity), rather than integer indexing.

### 4. `registry.py`: `report_html()` mutates a shared schema cache as a side effect
`pangalactic/core/registry.py:793`
`field_names = schema['field_names']; field_names.sort()` — not a copy, the
live cached list returned by `self.schemas`. The docstring for `schemas`
says field order is "the order defined in the model," implying downstream
consumers (e.g. UI table columns) rely on it. Generating an HTML report
permanently re-sorts it for the rest of the process.

    **NOTE**: although this is true, the HTML report is only used for
    documentation (e.g. as seen in https://pangalactic.us/pgef_ontology.html),
    and is never invoked in a running application instance, so irrelevant.

### 5. `UberORB.rebuild_de_defz` shadows the global `de_defz` cache — the method is a no-op
`pangalactic/core/uberorb.py:1444-1459`
`de_defz = {}` at line 1450 creates a local variable shadowing the
module-level `de_defz` imported from `parametrics.py`; the function builds
and discards a throwaway dict instead of updating the real cache. Contrast
with the correct `create_de_defz()` (1105-ish), which does
`de_defz.update(...)`. No in-repo callers currently found, but it's a public
method on the singleton `orb`.

    **NOTE**: unused; removed.

### 6. `registry.py`: `self.apps += app_prefix` corrupts the list instead of appending
`pangalactic/core/registry.py:664`
`list += str` extends element-by-element (`self.apps` becomes
`['a','c','m','e']` instead of `['acme']`). `self.apps_dict` (line 151) is
explicitly commented "not currently used," and nothing in this checkout
reads `self.apps` back, but it's silently wrong the moment something does.

      **NOTE**: self.apps etc. was some fairly ancient cruft ... removed.

### 7. `names.py`: `get_next_ref_des` — dead `prefix` parameter + inconsistent zero-padding
`pangalactic/core/names.py:871-912`
`prefix = ''` at line 888 unconditionally discards the caller-supplied
`prefix` argument before it's ever read (current callers, `clone.py:248,280`
in the earlier pass, don't pass it, so this is latent). Separately, the
first candidate ref-des uses 3-digit padding (`n:03`, line 903) but the
collision-retry loop uses 2-digit padding (`n:02`, line 909) — a collision
on the first candidate produces a ref-des like `ANT-04` alongside existing
`ANT-001`-style ids in the same assembly.

    **NOTE**: fixed.

### 8. Systemic: bare `except:` clauses in in-scope files
`uberorb.py` (18), `parametrics.py` (21), `names.py` (5), `validation.py`
(2). All swallow `KeyboardInterrupt`/`SystemExit` and hide real bugs behind
generic fallback/failure behavior — e.g. a JSON load failure in
`load_parmz`/`load_de_defz`/`load_data_elementz`/`load_mode_defz` just
returns the string `'fail'` with no indication of what actually went wrong.

---

## Other correctness bugs worth fixing

- **`registry.py:595`** — `find_app_ontologies`'s
  `'pgef.owl' in app_owl_file_paths` check compares a bare filename against
  a list of full paths from `glob.glob`, so it never matches (dead code, no
  callers found).

      **NOTE**: this was also some ancient cruft ... removed.

- **`uberorb.py:1966-1970`** — `get_oid_cnames`'s `cname`-only branch
  references `oids` (unset when only `cname` is passed) instead of filtering
  purely by `cname` — calling `get_oid_cnames(cname='Foo')` without `oids`
  raises `UnboundLocalError`. No current callers found.

    **NOTE**: the error I got was ArgumentError, which was easy to fix. Not
    sure how UnboundLocalError occurs, could not reproduce.

- **`uberorb.py:220, 503-514`** — `orb.start(home=X)` where `X` does not yet
  exist creates `X` as a *file* and then crashes. `start()` calls
  `setup_ref_db_and_version(home, ...)` at line 220, before the home
  directory is created (that happens later, via `init_registry` →
  `PanGalacticRegistry`). `setup_ref_db_and_version` does
  `shutil.copy(<ref_db file>, home)`, and `shutil.copy` with a non-existent
  destination directory writes the *source file* to that path — so `home`
  becomes a copy of `local.db`. The next line,
  `open(os.path.join(home, 'VERSION'), 'w')`, then raises
  `NotADirectoryError`. **Verified by execution:** `orb.start(home='newdir')`
  in an empty directory leaves a 331 KB file named `newdir` and raises.
  Low impact in practice — the applications pass a home that already exists,
  and in the test suite `test_registry.py` creates `pangalaxian_test` before
  `test_orb.py` uses it — but it makes a genuine first-run/fresh-install
  path fail with a confusing error and a bogus artifact that must be deleted
  by hand (an `rm -rf` of the directory name won't remove it, since it's a
  file).

    There is a **second, related ordering problem** in the same few lines:
    `setup_ref_db_and_version` is called with the **raw `home` kwarg**,
    *before* the A/B/C home-precedence resolution (lines 221-245) has run.
    So when `home` is not passed at all, the ref db is set up against `''`
    (i.e. the current working directory) while `init_registry()` later opens
    `sqlite:///[pgx_home]/local.db` against the *resolved* home — a
    different place, and not pre-populated. The natural fix addresses both:
    move the `setup_ref_db_and_version()` call to just after `pgx_home` is
    resolved and created, pass it `pgx_home`, and add a
    "path exists but is not a directory" guard. Verified working in a
    scratch checkout (fresh non-existent home → starts cleanly, `local.db`
    and `VERSION` both present in the new directory), then **reverted**.

    **STATUS: deferred, by author's decision.** Application startup
    responsibility is split between `orb.start()` and
    `p.node.pangalaxian` (plus wrappers such as `gargleblaster`) — e.g.
    pangalaxian always creates and populates the home directory from config
    and/or user preferences before calling `orb.start()`, which is why this
    path was never hit in practice. Any change to `orb.start()` should wait
    until `pangalactic.node` has been reviewed and the full startup picture
    is understood, so the split of responsibilities can be settled
    deliberately rather than piecemeal. Revisit during/after the
    `pangalactic.node` pass.
  *(Found incidentally while re-running the suite, not part of the original
  pass.)*

- **`serializers.py:110-119`** — `uncook_int(0)` returns `None` instead of
  `0` (falsy-value bug); low impact today since only date/datetime fields
  are routed through `uncookers` in practice.

    **NOTE**: the value being "uncooked" is always a string (it only occurs in
    a object serialized by the application, and the application controls both
    ends of the wire, so nothing "random"), so this is not a bug:  the string
    '0' will return a value of 0; only an empty string or None will return
    None, which is appropriate in this context.

- **`parametrics.py:2333-2375`** (`set_modal_context`) — can write a
  self-referential entry into `components` when a system sets its own mode,
  making it appear as its own component to anything that iterates
  `mode_defz[project_oid]['components']` directly (rather than via
  `get_modal_context()`, which happens to mask it).

    **NOTE** this is not a concern since cyclic assembly structures are
    prevented in the relevant parts of the application (e.g. where assemblies
    are created or modified).

- **`parametrics.py:625-632`** (`round_to`) — a global `numeric_precision`
  preference silently overrides any explicitly passed `n`, undermining
  callers (e.g. `compute_mev`'s intentional 3-digit contingency rounding at
  line 1495/1501) that expect their `n` to be honored.

    **NOTE** yes, that is intentional: the global numeric_precision is set by
    the application user, typically in accordance with the policy of the
    relevant project. It defaults to the "n" input if no global preference is
    set.

- **`parametrics.py:69`** (`make_parm_html`) — does an unguarded
  `parm_defz[pid]` lookup while sibling functions in the module use
  `.get(pid)`; crashes instead of degrading gracefully for an unknown `pid`.

    **NOTE**: the only app context in which this function is used (in
    p.node.widgets) uses validated pid's -- some other serious error would have
    to occur before this function received an unknown pid.

- **`meta.py:631-656`** (`asciify`) — the fallback branch (non-str,
  non-bytes input) returns a lazy `filter` object instead of a `str`,
  violating its own documented return type (likely unreachable today given
  current call sites, since `namify()`'s only caller of this branch is
  already unreachable per the next item).

    **NOTE** fixed.

- **`names.py:597-755`** — `to_external_name`/`to_table_name`/
  `to_media_name` triplicate the same control-flow block and all three raise
  `UnboundLocalError` if a class name has zero capital letters (low
  real-world odds, but no defensive fallback, and any fix needs to be
  applied three times).

    **NOTE** not a real issue since intended use is only within the application
    for domain classes, which always have at least one capital letter (domain
    classes are those defined in the p.core ontology).

- **`names.py:152-172`** (`namify`) — the bare `except:` branch duplicates
  the `try` branch's logic verbatim (dead duplication, not a real
  fallback), and the trailing `else:` is unreachable since the `try` never
  raises in a way that would skip to it.

    **NOTE** fixed ... this is tested indirectly in the 'test_names.py' test
    suite in the test of 'register_namespaces()' (the only place where namify()
    is used).


## Resource / lifecycle issues

- **Unclosed file handles**: `uberorb.py` — `load_and_transform_data`
  (~line 877, no `with`, no cleanup on error) and `dump_db` (~574-576,
  manual open/write/close with no `try/finally`); `errbudget.py:22-198`
  (`xlsxwriter.Workbook` never wrapped in `try/finally` — a mid-write
  exception leaks/corrupts the `.xlsx`); `__init__.py:138-274` — all of
  `read_config`/`write_config`/`read_prefs`/`write_prefs`/`read_state`/
  `write_state`/`read_deleted`/`write_deleted`/`read_trash`/`write_trash`
  open with plain `f = open(...)` and close explicitly, no `with`
  (commented-out `# try:`/`# except:` lines suggest exception handling was
  deliberately stripped at some point).

    **NOTE**: fixed uberorb.py items
    **NOTE**: ignoring errbudget.py (removed from package)
    **NOTE**: please suggest mods to fix __init__.py read / write functions.

- **Unbounded recursion**: `uberorb.py:805-837` (`get_all_usage_paths`) has
  no cycle detection, unlike `get_bom_from_compz` which wraps the same kind
  of walk in `try/except` to catch `RecursionError` from cyclic assemblies.

    **NOTE**: as mentioned above, cyclic assemblies are prevented in the
    app processes that create or modify assemblies.

- **Cache-load asymmetry**: `load_parmz`, `load_de_defz`,
  `load_data_elementz`, `load_mode_defz` (`parametrics.py:442, 1706, 1825,
  2213`) all `.update()` without clearing first, so reloading these caches
  mid-session leaves stale oids visible. (`load_rqt_allocz`/`load_allocz`
  have the same pattern but are excluded here as requirements-scoped.)
  `load_compz`/`load_systemz` were already fixed to `.clear()` in a prior
  commit.

    **NOTE**: load_de_defz and save_de_defz were not used and have been
    removed. The load_parmz, load_data_elementz, and load_mode_defz functions
    are run only once per application session, within orb.start(), and they
    create the initial contents of those runtime caches -- i.e. there is
    nothing for them to clear.

  **ACCEPTED** — and the reason generalizes into an architectural
  distinction worth recording, since it governs how any cache finding in
  this package should be judged. There are two classes of cache:
  1. **Authoritative** — `parameterz`, `data_elementz`, `mode_defz`. Their
     *only* persistence is `parameters.json`, `data_elements.json`,
     `mode_defs.json`; they are **not derivable from the database**. Loaded
     once per session in `orb.start()` into empty dicts, hence no `.clear()`
     needed. Their *write* path is correspondingly critical — see finding
     #1, which this distinction is what surfaced.
  2. **Derived** — every other cache (`componentz`, `systemz`, `parm_defz`,
     `de_defz`, `parmz_by_dimz`, …). Pure performance optimizations, rebuilt
     at runtime from the database, so staleness is self-correcting and loss
     is harmless.

  A further qualifier from the author: even for class 1, the **server's**
  copies are authoritative and clients re-sync from them on connect. Client
  integrity matters mainly for extended *disconnected* use; the
  client/server synchronization functions live in `pangalactic.node` and
  will be reviewed there.

- **`kb.py:168-256, 440-462`** — several ontology-graph properties
  (`class_nodes_by_type`, `node_names`, etc.) are uncached and re-scan the
  full graph on every access; called once per class name in a loop during
  ontology load, producing avoidable near-quadratic cost.

    **NOTE**: very inefficient but extremely low impact -- the time consumed is
    miniscule compared to other startup operations, especially initial loading
    of the database.

- **`names.py:120-149`** — the module-global `namespaces` registry has no
  reset/unregister path; a long-running process that loads two different
  ontologies reusing the same prefix will keep resolving against the first.

    **NOTE** historically this was a potential use case; however, it is
    extremely doubtful that more than one ontology will ever be used
    within this application! In the unlikely event it is ever required /
    desired, this can be revisited.

## Dead code

- **`parametrics.py:1415`** — `compute_assembly_context_parameter` is
  defined and calls itself recursively but is never wired into the
  `COMPUTES` dispatch table and has no external callers.

    **NOTE** this function has not yet been applied, as it has not yet been
    required by any customer, but it may be useful in the future and can then
    be integrated accordingly.

- **`registry.py`** — `apps_dict` (explicitly commented "not currently
  used" at line 151) and `find_app_ontologies` (dead per the bug above).

    **NOTE**: these are indeed unused and could be removed.

- ~~**`validation.py:320`** — `validate_all()` has zero callers~~ —
  **RETRACTED, not dead code.** The author confirms `validate_all()` is
  called from `p.node.pgxnobject`. My "zero callers repo-wide" claim was
  wrong: the grep behind it only covered this checkout, exactly the failure
  mode the "Caveat carried forward" section below warns about — I flagged
  the caveat and then didn't apply it to this item.

    One minor, purely local sub-issue does survive, though my original
    phrasing of it ("accepted but unused") was also wrong. `ids`
    (`validation.py:321`) is not unused — it's **silently discarded**:
    line 355 does `ids = set([idv[0] for idv in idvs])`, unconditionally
    overwriting the caller's value with one derived from `idvs` before it
    is ever read (line 356 reads only the recomputed set). It's also the
    one keyword arg missing from the docstring. This is the same
    dead-parameter pattern as `get_next_ref_des`'s `prefix` (#6, since
    fixed): a caller passing `ids=` today gets no error and no effect.
    Worth resolving when `pgxnobject.py` is reviewed — check what that
    call site actually passes before deciding whether to drop the
    parameter or honor it.

- **`mapping.py:106,153`** — `schema_mods` is unused (only `schema_maps` is
  consulted for actual conversion), and is inconsistent with it — several
  release strings listed in `schema_mods` have no corresponding
  `schema_maps` entry, so upgrades from those versions would silently skip
  transformation if `schema_mods` were ever wired up as a gate.

    **NOTE**: removed.

## Complexity / duplication worth consolidating

- **`errbudget.py:11-196`** — "Top Down" (line 23) and "Bottom Up" (line
  133) sheet-building loops are ~90% duplicated; also, despite its
  docstring, `gen_error_budget()` barely reads the passed-in `instrument`
  object — most numeric content is a hardcoded `SWFE = 100` (line 92) with
  a leftover commented-out `input()` call (line 93).

    **NOTE** The errbudget.py module is irrelevant to the rest of the package;
    removed from this repository, moved to an external sandbox.

- **`access.py`** — `get_perms`'s `Product` branch (line 226) is a
  standalone `if` outside the `elif` chain that follows it, relying on a
  trailing catch-all `return` — functionally correct today but easy to
  break by a future contributor editing this security-relevant function
  without noticing the branch isn't part of the chain.

    **NOTE** Not important; ignored.

- **`deserialize_parms`/`deserialize_des`** (`parametrics.py:368-430,
  1764-1800ish) still carry an old-format-detection branch ("if the value
  is a dict, format is old") even though the corresponding file-load-time
  format scans were removed in a prior cleanup pass — worth a decision on
  whether "no old format anywhere" is now the invariant (in which case
  these should go too) or whether inline conversion on ingest is still
  needed for some external data source.

    **NOTE** This is not a significant burden, since detection of the old
    format is trivially easy and not a performance hit; also, there is a test
    for the functionality to recognize and convert from the old format.

## Verified correct / no significant findings (unchanged files, re-confirmed)

- **`access.py:73-172, 249-251`** (frozen-assembly enforcement for global
  admins) — **not a bug, intentional configuration-management (CM) design**
  (corrected by the author). Two separate points, both explained:
  - The unconditional Acu-in-frozen-assembly block (78-81, applying even to
    a global admin, before `is_global_admin` is ever consulted) is a
    deliberate CM control: assemblies within a frozen structure must not be
    edited by anyone, admin included, without an explicit, visible
    "unfreeze" step first. The sanctioned emergency path is thaw → edit →
    re-freeze, gated through the "object editor" (`pgxnobject.py`, in
    `pangalactic.node`, not yet reviewed), which layers *additional* logic
    on top of `access.py` to block even a global admin from directly
    editing a frozen `Product` — while still exposing the "thaw" action to
    global admins for exactly this emergency case. (More systematic CM
    capabilities beyond this are a possible future target, not yet
    implemented.) Given that, `access.py`'s own frozen-`Product` check
    (249-251) being reachable only from the non-admin branch is consistent
    with "global admin is omnipotent" at the data-access layer — the
    UI-level editor is where the deliberate friction against *accidental*
    frozen-object edits lives, with the explicit acknowledgment that a
    global admin bypassing the sanctioned workflow (e.g. via a direct
    script/API call rather than the object editor) is a known, accepted CM
    risk tied to the admin role, not a gap to close in `access.py`.
  - The offline-client full-permissions grant on not-yet-synced objects
    (173-180) is not an "unchecked assumption" — it's a structural
    guarantee. `synced_oids` (in the client's local `state`) tracks which
    oids are confirmed to exist in the server-side database; an oid absent
    from that list can only be a locally-created object no other user or
    session could know about, since the client's local db contains nothing
    it didn't either create itself or receive via a completed sync. No
    `obj.creator` check is needed because the situation the check would
    guard against — a not-yet-synced object *not* created by the local
    user — cannot arise given how `synced_oids` is populated.
- **`clone.py:117-120`** (caller-supplied `oid`/`name`/`description` are
  overwritten when cloning from an existing object) — **not a bug,
  intentional by design** (corrected by the author after the initial pass
  flagged this as a top finding). `clone()` has two distinct call modes:
  (1) `what` is a class name — a fresh instance built entirely from `kw`;
  (2) `what` is an existing domain object — a generic copy, used mainly by
  the "object editor" (`pgxnobject.py`, in `pangalactic.node`) so the user
  can then edit the copy's name/description/etc. themselves. In mode (2),
  `oid` is *always* regenerated via `uuid4()` deliberately — the oid is
  intentionally non-semantic and its uniqueness is an invariant that must
  never be caller-overridable — and `name`/`description` are seeded with
  placeholder values (`'clone of ' + obj.name`, copied description) for the
  user to overwrite in the editor, not meant to be set via `kw` in this
  mode. The docstring's general "kwargs override" line describes the common
  case across both modes and is imprecise for these three fields
  specifically, but since `clone()` is called only from internal,
  carefully-controlled call sites (no caller ever passes
  `oid`/`name`/`description` when cloning from an object), this has no
  practical impact.
- `datastructures.py` (`chunkify`, `OrderedSet`) — no bugs found.
- `kb.py`'s OWL/qname logic (`u2q`, `get_ontology_prefix`,
  `get_attrs_of_property`) — internally consistent.
- `meta.py`'s declarative tables (`MAIN_VIEWS`, `PGXN_MASK`, `M2M`,
  `ONE2M`) — no logic bugs.
- `units.py` — no significant findings.
- Utils section (`utils/reports.py`, `styles.py`, `excelreader.py`,
  `xlsxreader.py`, `part21.py`, `datetimes.py`, `__init__.py`, `log.py`) —
  unchanged since the last full pass; see `pangalactic_core_review.md`'s
  "Utils section" (U1-U9) for the still-current findings there, most
  notably **U1** (`write_power_modes_to_xlsx` mutating a list while
  iterating it, a live path from `pangalactic.node/node/powermodeler.py`)
  and **U4** (`write_mel_to_tsv` calling a nonexistent `orb.info()` on its
  error path, live from `pangalactic.node`/`pangalactic.warp`) — spot-checked
  and confirmed both still present at their original line numbers.

---

## Caveat carried forward

This checkout contains only `pangalactic.core`. "No callers found" claims
above mean "no callers within `pangalactic.core`" and should be checked
against `pangalactic.node` and `pangalactic.vger` before treating anything
as safe to delete — `get_project_parameters` was previously flagged as dead
this way and turned out to be called from `pangalactic.vger`.

## Suggested fix order

Items struck through below were addressed by the author in commits
`ce9ee29`, `292a934`, `4334549`, `cd5e7f0`, `45f990d`, `19707fb`,
`ec1479a`, `5305a78`, `696fd29`, `d0b5461`, `5a987f4`, plus the
`__init__.py` read/write rework.

1. **`parametrics.py`'s three `save_*` functions (#1)** — serialize before
   opening, so a JSON failure can't destroy the only copy of the
   `parameterz`/`data_elementz`/`mode_defz` data. Critical on vger, where
   these files are authoritative. Same fix already applied to
   `__init__.py`. Pair with raising the swallowed failure from `debug` to
   `error` and making `save_caches()` report real per-file outcomes.
2. ~~`serializers.py` missing FK guard (#2)~~ — done (`ce9ee29`).
3. ~~Fix `get_flight_units` (#3)~~ — done (`292a934`, dot notation).
4. `report_html()` (#4) — author's call: documentation-only, not worth
   fixing. `self.apps` (#6) ~~removed~~ (`cd5e7f0`).
5. ~~`rebuild_de_defz` (#5)~~ — removed as unused (`4334549`).
6. Sweep bare `except:` in `uberorb.py`/`parametrics.py` hot paths (#8) to
   `except Exception:` with logging, starting with the cache-loader JSON
   parsing (`'fail'` with no detail) and the three `save_*` functions
   covered by #1.
7. Address remaining dead code and duplication items as time allows.
