# -*- coding: utf-8 -*-
"""
Unit tests for pangalactic.core.entity
"""
import unittest

# pangalactic
from pangalactic.core.entity          import Entity, entz
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
                 e_parent.get('level'),
                 e.get('level'),
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

    def test_02_entity_set_value_for_defined_parameter(self):
        """
        CASE:  an Entity instance can have a value assigned to a key if it has
        an associated ParameterDefinition.
        """
        e['m'] = 5.0
        value = e['m']
        expected = 5.0
        self.assertEqual(expected, value)

    def test_03_entity_set_value_for_defined_data_element(self):
        """
        CASE:  an Entity instance can have a value assigned to a key if it has
        an associated ParameterDefinition.
        """
        e['Vendor'] = 'Yoyodyne Propulsion Systems'
        value = e['Vendor']
        expected = 'Yoyodyne Propulsion Systems'
        self.assertEqual(expected, value)

    def test_04_entity_cannot_set_value_for_undefined_key(self):
        """
        CASE:  an Entity instance cannot have a value for a key if the key has
        neither a ParameterDefinition nor a DataElementDefinition.
        """

    def test_04_entity_cannot_set_value_for_undefined_key(self):
        """
        CASE:  an Entity instance cannot have a value for a key if the key has
        neither a ParameterDefinition nor a DataElementDefinition.
        """
        e['bogus'] = 5.0
        value = e['bogus']
        expected = None
        self.assertEqual(expected, value)

