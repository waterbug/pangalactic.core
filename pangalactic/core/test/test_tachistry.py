# -*- coding: utf-8 -*-
"""
Functional tests for pangalactic.core.tachistry module
  - builds SemanticRegistry from kb .owl and .rdf files
"""
import unittest
from functools import reduce

# PanGalactic
from pangalactic.core.tachistry import Tachistry, schemas

r = Tachistry(home='marvin_test', force_new_core=1)


class TachistryTests(unittest.TestCase):

    def test_01__create_extracts_from_source(self):
        """
        CASE:  _create_extracts_from_source

        Compares the return value of _create_extracts_from_source with a set of
        meta objects corresponding to the source's model.
        """
        # use space_mission.owl
        # (trial runs tests from '_trial_temp' dir, inside 'test' dir)
        source = 'data/test_data.owl'
        r._create_extracts_from_source(source)
        value = [set([e['oid'] for e in r.ces.values()
                     if e['id_ns'] == 'space_mission']),
                 set([e['oid'] for e in r.pes.values()
                     if e['id_ns'] == 'space_mission'])]
        expected = [set(['space_mission:Spacecraft',
                         'space_mission:Instrument']),
                    set(['space_mission:payload_instruments',
                         'space_mission:part_number',
                         'space_mission:mass'])]
        self.assertEqual(expected, value)

    def test_02__extract_basewalk(self):
        """
        CASE:  _extract_basewalk

        Compares the return value of _extract_basewalk(e) with the C{id}s of
        all known ancestors of e (incluing e).
        """
        e = r.ces['HardwareProduct']
        value = set(r._extract_basewalk(e))
        expected = set(['Identifiable', 'Modelable', 'Product',
                        'HardwareProduct', 'ManagedObject'])
        self.assertEqual(expected, value)

    def test_03_all_your_base(self):
        """
        CASE:  all_your_base

        Compares the return value of _all_your_base(e) with the C{id}s of all
        known ancestors of e (exluding e's C{id}).
        """
        e = r.ces['HardwareProduct']
        value = set(r.all_your_base(e))
        expected = set(['Identifiable', 'Modelable', 'ManagedObject',
                        'Product'])
        self.assertEqual(expected, value)

    def test_03_all_your_sub(self):
        """
        CASE:  all_your_sub

        Compares the return value of _all_your_sub(e_id) with the C{id}s of all
        known children of e (exluding e's C{id}).
        """
        e = r.ces['Product']
        value = set(r.all_your_sub(e))
        expected = set(['Product', 'DigitalProduct', 'Software',
                        'HardwareProduct', 'Template', 'ContinuousProduct',
                        'Document', 'Model', 'Instrument', 'Spacecraft'])
        self.assertEqual(expected, value)

    def test_04_metaobject_build_order(self):
        """
        CASE:  metaobject_build_order

        Checks that, for all registered class extracts [r.ces], all bases of
        the class extract id appear in the schema build order before that class
        extract id ('before' condition) and that none of the class ids that
        come *after* a given class extract id in the mbo are in the latter's
        bases ('after' condition).
        """
        mbo = r.metaobject_build_order()
        _or = lambda x, y: x or y
        after = reduce(_or, [reduce(_or, [(b in r.all_your_base(r.ces[a]))
                                          for b in mbo[mbo.index(a):]])
                             for a in mbo])
        _and = lambda x, y: x and y
        before = reduce(_and, [reduce(_and,
                                      [(b in mbo[:mbo.index(a)])
                                       for b in r.all_your_base(r.ces[a])])
                              for a in mbo[1:]])
        value = before, after
        expected = True, False
        self.assertEqual(expected, value)

    def test_05__update_schemas_from_extracts(self):
        """
        CASE:  _update_schemas_from_extracts

        Inspects the schemas created by update_schemas_from_extracts to see
        whether they are Zope Schemas, behave properly, and contain the right
        stuff.

        * N.B.:  depends on success of C{test_03__create_extracts_from_source}.

        This test depends on the current state of the registry as a result of
        the previous tests -- i.e., some extracts may have been created for
        which there are not yet schemas -- specifically, the extracts for the
        Classes of the space_mission ontology (currently Spacecraft and
        Instrument but they could be any) may have been created (this is done
        in test_03__create_extracts_from_source) and no schemas may have been
        created for them yet.
        """
        # this will use space_mission.owl
        # first, check that schemas are registered for the specified extracts
        r._update_schemas_from_extracts()
        value_1 = len([e for e in list(r.ces) if e not in list(schemas)])
        expected_1 = 0
        # FIXME!
        # TODO:  second, that the new schemas are consistent with the extracts
        # from which they were created -- specifically, that the id's of the
        # property extracts whose domain is the meta_id of a created schema
        # appear in the schema (i.e. are in list(schema)).
        value_2 = True
        expected_2 = True
        value = [value_1, value_2]
        expected = [expected_1, expected_2]
        self.assertEqual(expected, value)

