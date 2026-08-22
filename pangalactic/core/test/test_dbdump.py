# -*- coding: utf-8 -*-
"""
Tests for the ORM-free database dump used by the schema migration.

This is the file the migration reloads from *after* it drops the database, so
if the dump is wrong the data is gone.  What matters is therefore not that it
runs but that it captures what serialize() captures -- these compare the two
directly, on the same database.
"""
import os
import unittest

# set the orb
import pangalactic.core.set_uberorb

from pangalactic.core             import orb
from pangalactic.core.dbdump      import dump_db_to_yaml, read_cache
from pangalactic.core.serializers import serialize
from pangalactic.core.test.utils  import create_test_users, create_test_project
from pangalactic.core.serializers import deserialize

import yaml

HOME = 'dbdump_test'
orb.start(home=HOME)
deserialize(orb, create_test_users())
deserialize(orb, create_test_project())

DUMP = os.path.join(HOME, 'test-dump.yaml')


def dump():
    """
    Dump the test home's database and read the result back.
    """
    n = dump_db_to_yaml(orb.db_url if hasattr(orb, 'db_url') else
                        'sqlite:///' + os.path.join(orb.home, 'local.db'),
                        DUMP, home=orb.home)
    with open(DUMP) as f:
        return n, yaml.safe_load(f.read())


class DbDumpTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # parameters and data elements live in the json caches, not the db,
        # and the dump reads them from disk.  A real home has them written by
        # the last shutdown;  a test home does not until it is asked.
        orb.save_caches()
        cls.count, cls.dumped = dump()
        cls.by_oid = {so['oid']: so for so in cls.dumped}
        objs = orb.get_all_subtypes('Identifiable')
        cls.serialized = {so['oid']: so for so in
                          serialize(orb, objs, include_refdata=True)}

    def test_01_every_object_is_dumped(self):
        """
        CASE:  the dump holds exactly the objects serialize() would emit.
        A missing object here is an object destroyed by the migration.
        """
        self.assertEqual(set(self.serialized), set(self.by_oid))

    def test_02_count_matches_what_was_written(self):
        """
        CASE:  the returned count is the number of objects in the file.  The
        migration logs it, and a caller may want to check it.
        """
        self.assertEqual(len(self.dumped), self.count)

    def test_03_every_object_has_a_class(self):
        """
        CASE:  every dumped object carries "_cname".  deserialize() skips
        anything without one, so an object missing it is silently dropped on
        the way back in.
        """
        missing = [oid for oid, so in self.by_oid.items()
                   if not so.get('_cname')]
        self.assertEqual([], missing)

    def test_04_classes_agree_with_serialize(self):
        """
        CASE:  the class recorded for each object is the one serialize()
        records.  pgef_type is read straight from the table, so this pins
        that the column means what the dump assumes.
        """
        wrong = {oid: (so['_cname'], self.serialized[oid]['_cname'])
                 for oid, so in self.by_oid.items()
                 if so['_cname'] != self.serialized[oid]['_cname']}
        self.assertEqual({}, wrong)

    def test_05_no_field_serialize_has_is_missing(self):
        """
        CASE:  no object loses a populated field.

        Compared against serialize() rather than against a fixed list, so
        that an attribute added to the ontology later is covered without
        anyone remembering to add it here.
        """
        losses = {}
        for oid, s in self.serialized.items():
            d = self.by_oid[oid]
            for k, v in s.items():
                if v in (None, '', [], {}):
                    continue
                if k not in d:
                    losses.setdefault(k, 0)
                    losses[k] += 1
        self.assertEqual({}, losses)

    def test_06_object_valued_attributes_keep_their_oids(self):
        """
        CASE:  an attribute referring to another object holds that object's
        oid, under the attribute name rather than the column name.  The
        column is "<attr>_oid" and the dump has to strip the suffix, or
        deserialize() would not recognize the attribute.
        """
        acu = orb.get('test:H2G2:acu-sc0-propsys')
        self.assertIsNotNone(acu)
        dumped = self.by_oid[acu.oid]
        expected = [acu.assembly.oid, acu.component.oid]
        value = [dumped.get('assembly'), dumped.get('component')]
        self.assertEqual(expected, value)
        self.assertNotIn('assembly_oid', dumped)

    def test_07_parameters_and_data_elements_are_included(self):
        """
        CASE:  parameters and data elements are attached.  They are not in
        the database at all -- they live in the json caches -- so nothing
        about reading tables would pick them up, and the migration removes
        those caches immediately afterwards.
        """
        with_parms = [oid for oid, s in self.serialized.items()
                      if s.get('parameters')]
        self.assertTrue(with_parms, 'no parameters in the test data')
        oid = with_parms[0]
        self.assertEqual(self.serialized[oid]['parameters'],
                         self.by_oid[oid].get('parameters'))

    def test_08_the_migration_can_read_the_file(self):
        """
        CASE:  the file is readable by load_and_transform_data(), which is
        what the migration actually calls on it.

        Deliberately not "deserialize it and check the objects appear":  the
        migration deserializes into an *empty* database, and re-deserializing
        into the one just dumped is a no-op, since nothing in it is newer
        than what is already there.  A second orb cannot be started in the
        same process to do it properly (one declarative Base), which is the
        same constraint that makes this module necessary at all.
        """
        loaded = orb.load_and_transform_data(DUMP)
        self.assertEqual(len(self.dumped), len(loaded))
        self.assertEqual(set(self.by_oid),
                         set(so['oid'] for so in loaded))

    def test_09_missing_caches_are_not_an_error(self):
        """
        CASE:  a home with no parameter cache.  A home that has never had a
        parameter set does not have one, and that must not stop a migration.
        """
        self.assertEqual({}, read_cache(orb.home, 'no_such_cache'))
        self.assertEqual({}, read_cache('/no/such/home', 'parameters'))


if __name__ == '__main__':
    unittest.main()
