# -*- coding: utf-8 -*-
"""
Dump a PGEF database to serialized-object yaml *without* the ORM.

This exists for one purpose:  the schema migration in `orb.start()` drops and
recreates the database, so the data has to be written out first, and at that
moment the ORM cannot be used to do it.

Why it cannot:  `registry.py` has a single module-level SQLAlchemy
declarative `Base`, and every registry builds its classes onto it.  Building
one registry for the *old* schema (to read the existing database) and then
another for the new one raises

    InvalidRequestError: Table 'identifiable_' is already defined for this
    MetaData instance.

-- verified, not assumed.  And the cached ontology extracts in the home are
no help either:  `_cache_is_stale()` rebuilds them from `pgef.owl` when they
disagree with it, which after an ontology change they always do.  So the only
way to read the old database from the new code is to go around the ORM.

SQLAlchemy *Core* reflection does exactly that.  It introspects whatever
tables happen to be there, needs no mapped classes, touches no declarative
`Base`, and works against postgresql as well as sqlite -- which matters,
because the server migrates through the same code path.

The dump is possible at all because of how PGEF stores objects:

  * every table is keyed on `oid`, and there are no association tables
    without one, so an object can be reassembled by merging the rows that
    share its oid across tables (this is joined-table inheritance:  a
    HardwareProduct has a row in `identifiable_`, `modelable_`,
    `managed_object_`, `product_` and `hardware_product_`);
  * `identifiable_.pgef_type` names the class;
  * an object-valued attribute is a column named `<attr>_oid` holding the
    referenced oid, which is exactly what `serialize()` emits for it.

Parameters and data elements are *not* in the database -- they live in the
`parameters.json` and `data_elements.json` caches -- so they are read from
the home directory and attached, which is what `serialize()` does too.

Validated against `serialize()` on the reference database:  same 1035
objects, same oids, and identical field sets once the caches are attached.
"""
import os

import yaml

from sqlalchemy import create_engine, MetaData, select


def read_cache(home, name):
    """
    Read one of the json caches from a home directory.

    Args:
        home (str):  the home directory
        name (str):  cache file base name ('parameters' or 'data_elements')

    Returns:
        dict:  the cache, or {} if it is absent or unreadable.  A missing
        cache is not an error:  a home that has never had any parameters set
        does not have one.
    """
    import json
    fpath = os.path.join(home or '', name + '.json')
    if not os.path.exists(fpath):
        return {}
    try:
        with open(fpath) as f:
            return json.loads(f.read()) or {}
    except Exception:
        return {}


def dump_db_to_yaml(db_url, fpath, home=None, log=None):
    """
    Dump a PGEF database to `fpath` as serialized objects, without the ORM.

    The output is the same shape `serialize()` produces and `deserialize()`
    consumes, so `load_and_transform_data()` reads it unchanged.

    Args:
        db_url (str):  SQLAlchemy url of the database to dump
        fpath (str):  path of the yaml file to write

    Keyword Args:
        home (str):  home directory, for the parameter and data element
            caches.  Without it those are omitted, which loses them.
        log:  a logger, if progress should be reported

    Returns:
        int:  the number of objects written

    Raises:
        whatever the database or the file system raises.  The caller must
        treat a failure as fatal to the migration:  the next step drops the
        database, and a migration that proceeds without a dump destroys the
        data it was meant to preserve.
    """
    def note(msg):
        if log:
            log.info(msg)

    note('* dump_db_to_yaml() -- reading the database without the ORM ...')
    engine = create_engine(db_url)
    md = MetaData()
    md.reflect(bind=engine)
    by_oid = {}
    with engine.connect() as conn:
        for name, table in md.tables.items():
            if 'oid' not in table.columns:
                # nothing that holds an object;  PGEF has none of these
                # today, but a stray table should not break the dump
                continue
            # NOTE: the column *names* are taken from the table and zipped
            # with the row, rather than iterating a RowMapping.  A mapping
            # built from a Core select is keyed by Column objects, not
            # strings, and those go straight into the output dict and then
            # into yaml, where they fail as "cannot represent an object".
            # str() is not redundant:  a reflected column's name is a
            # SQLAlchemy "quoted_name", a str *subclass*, and yaml's
            # SafeDumper dispatches on exact type -- so an unconverted name
            # used as a dict key fails with "cannot represent an object",
            # naming a key that prints as an ordinary string
            names = [str(c.name) for c in table.columns]
            for row in conn.execute(select(table)):
                values = dict(zip(names, row))
                obj = by_oid.setdefault(values['oid'], {})
                for col, value in values.items():
                    if value is None:
                        # an unset attribute:  omitted rather than written as
                        # null, matching serialize(), which only emits what
                        # an object actually has
                        continue
                    if col.endswith('_oid') and col != 'oid':
                        # object-valued attribute:  the column holds the
                        # referenced oid and the attribute is the column name
                        # without the suffix
                        col = col[:-4]
                    obj[col] = value
    note(f'  {len(by_oid)} objects read from {len(md.tables)} tables.')

    parameterz = read_cache(home, 'parameters')
    data_elementz = read_cache(home, 'data_elements')

    sobjs = []
    for oid, obj in by_oid.items():
        cname = obj.pop('pgef_type', None)
        if not cname:
            # a row with no class cannot be deserialized;  skip it rather
            # than write something that will fail on the way back in
            note(f'  ** no pgef_type for oid "{oid}" -- skipped.')
            continue
        obj['_cname'] = cname
        for key, value in list(obj.items()):
            # datetimes are written as strings, as serialize() writes them;
            # deserialize() parses either, but the file should look the same
            # whichever route wrote it
            if hasattr(value, 'isoformat'):
                obj[key] = str(value)
        if oid in parameterz:
            obj['parameters'] = parameterz[oid]
        if oid in data_elementz:
            obj['data_elements'] = data_elementz[oid]
        sobjs.append(obj)

    dir_path = os.path.dirname(fpath)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(fpath, 'w') as f:
        f.write(yaml.safe_dump(sobjs, default_flow_style=False))
    note(f'  {len(sobjs)} objects written to "{fpath}".')
    return len(sobjs)
