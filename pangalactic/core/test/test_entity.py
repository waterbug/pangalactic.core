# -*- coding: utf-8 -*-
"""
Unit tests for pangalactic.core.entity
"""
import json, os, unittest

# pangalactic
from pangalactic.core.entity          import Entity, entz, save_entz
from pangalactic.core.parametrics     import DATATYPES
from pangalactic.core.uberorb         import orb
from pangalactic.core.utils.datetimes import dtstamp


orb.start(home='pangalaxian_test')

# create a test entity
e_parent = Entity()
e = Entity(parent_oid=e_parent.oid)

class EntityTest(unittest.TestCase):
    maxDiff = None

    def test_00_new_entity_default_metadata(self):
        """
        CASE:  check default metadata for a new Entity instance.
        """
        value = [e.creator,
                 e.modifier,
                 e_parent.get('assembly_level'),
                 e.get('assembly_level'),
                 e.parent_oid,
                 e_parent.parent_oid
                 ]
        expected = ['pgefobjects:admin', 'pgefobjects:admin', 1, 2,
                    e_parent.oid, None]
        self.assertEqual(expected, value)

    def test_01_new_entity_is_cached(self):
        """
        CASE:  Entity instance is cached in 'entz'.
        """
        value = e.oid in entz
        expected = True
        self.assertEqual(expected, value)

    def test_02_entz_cache_structure(self):
        """
        CASE:  Entity cache 'entz' is serialized correctly.
        """
        save_entz(orb.home)
        fpath = os.path.join(orb.home, 'ents.json')
        with open(fpath) as f:
            data = f.read()
        ent_dict = json.loads(data)
        value = []
        value.append(ent_dict[e.oid]['creator'] == 'pgefobjects:admin')
        value.append(ent_dict[e.oid]['modifier'] == 'pgefobjects:admin')
        value.append(ent_dict[e.oid]['owner'] == 'pgefobjects:PGANA')
        expected = [True, True, True]
        self.assertEqual(expected, value)

    def test_03_entity_set_value_for_defined_parameter(self):
        """
        CASE:  an Entity instance can have a value assigned to a key if it has
        an associated ParameterDefinition.
        """
        e['m'] = 5.0
        value = e['m']
        expected = 5.0
        self.assertEqual(expected, value)

    def test_04_entity_set_value_for_defined_data_element(self):
        """
        CASE:  an Entity instance can have a value assigned to a key if it has
        an associated ParameterDefinition.
        """
        e['Vendor'] = 'Yoyodyne Propulsion Systems'
        value = e['Vendor']
        expected = 'Yoyodyne Propulsion Systems'
        self.assertEqual(expected, value)

    def test_05_entity_cannot_set_value_for_undefined_key(self):
        """
        CASE:  an Entity instance cannot have a value for a key if the key has
        neither a ParameterDefinition nor a DataElementDefinition.
        """

    def test_06_entity_cannot_set_value_for_undefined_key(self):
        """
        CASE:  an Entity instance cannot have a value for a key if the key has
        neither a ParameterDefinition nor a DataElementDefinition.
        """
        e['bogus'] = 5.0
        value = e['bogus']
        expected = None
        self.assertEqual(expected, value)

