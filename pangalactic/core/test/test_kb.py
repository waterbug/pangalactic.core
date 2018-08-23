# $Id$

"""
Unit tests for pangalactic.core.kb
"""
# Python
import os

# Twisted
from twisted.trial import unittest

# PanGalactic
from pangalactic.core import kb

# RDFlib
import rdflib

cwd = os.getcwd()
source = os.path.join(cwd, 'data/test_data.owl')
k = kb.PanGalacticKnowledgeBase(source)


class KBTests(unittest.TestCase):

    def test_01_fix_funky_uris_single_slash(self):
        """CASE:  fix_funky_uris"""
        value = kb.fix_funky_uris('file:/x/y/z')
        expected = 'file:///x/y/z'
        self.assertEqual(expected, value)

    def test_02_fix_funky_uris_double_slash(self):
        """CASE:  fix_funky_uris"""
        value = kb.fix_funky_uris('file://x/y/z')
        expected = 'file:///x/y/z'
        self.assertEqual(expected, value)

    def test_03_fix_funky_uris_triple_slash(self):
        """CASE:  fix_funky_uris"""
        value = kb.fix_funky_uris('file:///x/y/z')
        expected = 'file:///x/y/z'
        self.assertEqual(expected, value)

    def test_04_get_ontology_prefix(self):
        """CASE:  get_ontology_prefix"""
        value = kb.get_ontology_prefix(source)
        expected = u'space_mission'
        self.assertEqual(expected, value)

    def test_05_del_class_node_names(self):
        """CASE:  del_class_node_names"""
        value = False
        try:
            k.del_class_node_names()
        except TypeError:
            value = True
        expected = True
        self.assertEqual(expected, value)

    def test_07_del_node_names(self):
        """CASE:  del_node_names"""
        value = False
        try:
            k.del_node_names()
        except TypeError:
            value = True
        expected = True
        self.assertEqual(expected, value)

    def test_08_del_property_node_names(self):
        """CASE:  del_property_node_names"""
        value = False
        try:
            k.del_property_node_names()
        except TypeError:
            value = True
        expected = True
        self.assertEqual(expected, value)

    def test_09_get_base_names(self):
        """CASE:  get_base_names"""
        value = k.get_base_names('space_mission', 'Spacecraft')
        expected = ['HardwareProduct']
        self.assertEqual(expected, value)

    def test_10_get_class_names(self):
        """CASE:  get_class_names"""
        value = k.get_class_names('space_mission')
        expected = set(['Spacecraft',
                        'Instrument'])
        self.assertEqual(expected, value)

    def test_11_get_class_node_names(self):
        """CASE:  get_class_node_names"""
        value = set(k.get_class_node_names())
        expected = set([u'space_mission:Spacecraft',
                        u'space_mission:Instrument',
                        u'pgef:HardwareProduct'
                        ])
        self.assertEqual(expected, value)

    def test_12_get_node_names(self):
        """CASE:  get_node_names"""
        value = k.get_node_names()
        expected = set([u'space_mission:Spacecraft',
                        u'space_mission:mass',
                        u'space_mission:part_number',
                        u'space_mission:Instrument',
                        u'pgef:HardwareProduct',
                        u'space_mission:payload_instruments'])
        self.assertEqual(expected, value)

    def test_13_get_property_names(self):
        """CASE:  get_property_names"""
        value = k.get_property_names('space_mission')
        expected = set(['part_number',
                        'mass',
                        'payload_instruments'])
        self.assertEqual(expected, value)

    def test_14_get_property_node_names(self):
        """CASE:  get_property_node_names"""
        value = k.get_property_node_names()
        expected = set([u'space_mission:mass',
                        u'space_mission:part_number',
                        u'space_mission:payload_instruments'])
        self.assertEqual(expected, value)

    def test_15_get_triple_objects(self):
        """CASE:  get_triple_objects"""
        value = k.get_triple_objects(
                         u'space_mission:payload_instruments', u'rdfs:range')
        expected = [rdflib.URIRef(
                    'http://testing.spam/space_mission/Instrument')]
        self.assertEqual(expected, value)

    def test_16_set_class_node_names(self):
        """CASE:  set_class_node_names"""
        value = False
        try:
            k.set_class_node_names()
        except TypeError:
            value = True
        expected = True
        self.assertEqual(expected, value)

    def test_17_set_node_names(self):
        """CASE:  set_node_names"""
        value = False
        try:
            k.set_node_names()
        except TypeError:
            value = True
        expected = True
        self.assertEqual(expected, value)

    def test_18_set_property_node_names(self):
        """CASE:  set_property_node_names"""
        value = False
        try:
            k.set_property_node_names()
        except TypeError:
            value = True
        expected = True
        self.assertEqual(expected, value)

    def test_19_import_ontology(self):
        """CASE:  import_ontology
        (Note:  import_ontology is called in KB.__init__())"""
        value = k.class_node_names | k.property_node_names
        expected = set([u'space_mission:part_number',
                        u'space_mission:payload_instruments',
                        u'space_mission:mass',
                        u'space_mission:Spacecraft',
                        u'space_mission:Instrument',
                        u'pgef:HardwareProduct'
                        ])
        self.assertEqual(expected, value)

    def test_20_readRdf(self):
        value = k.class_node_names | k.property_node_names
        expected = set([u'space_mission:part_number',
                        u'space_mission:payload_instruments',
                        u'space_mission:mass',
                        u'space_mission:Spacecraft',
                        u'space_mission:Instrument',
                        u'pgef:HardwareProduct'
                        ])
        self.assertEqual(expected, value)

    # def test_21_report(self):
    #     expected = report_output
    #     self.assertEqual(expected, k.report())


report_output = """
==========
Namespaces
==========
- owl:  http://www.w3.org/2002/07/owl#
  - DatatypeProperty
  - InverseFunctionalProperty
  - imports
  - FunctionalProperty
  - ObjectProperty
  - Ontology
  - Class
----------------------------------------
- pgef:  http://pangalactic.us/pgef/
  - HardwareProduct
----------------------------------------
- space_mission:  http://testing.spam/space_mission/
  - Instrument
  - Spacecraft
  - mass
  - payload_instruments
  - part_number
----------------------------------------
- pgefobjects:  http://pangalactic.us/objects/
----------------------------------------
- rdfs:  http://www.w3.org/2000/01/rdf-schema#
  - comment
  - range
  - domain
  - subClassOf
  - Class
----------------------------------------
- pgefns:  http://pangalactic.us/namespaces/
----------------------------------------
- testtmp:  http://pangalactic.us/test/tmp/
----------------------------------------
- sandbox:  http://pangalactic.us/sandbox/
----------------------------------------
- rdf:  http://www.w3.org/1999/02/22-rdf-syntax-ns#
  - type
----------------------------------------
- mime:  http://www.iana.org/assignments/media-types/
----------------------------------------
- xsd:  http://www.w3.org/2001/XMLSchema
  - gDay
  - hexBinary
  - nonPositiveInteger
  - float
  - boolean
  - long
  - unsignedLong
  - normalizedString
  - NMTOKEN
  - negativeInteger
  - anyURI
  - positiveInteger
  - unsignedShort
  - int
  - base64Binary
  - unsignedByte
  - string
  - date
  - integer
  - byte
  - gMonth
  - short
  - language
  - gMonthDay
  - double
  - decimal
  - unsignedInt
  - gYearMonth
  - dateTime
  - nonNegativeInteger
  - gYear
  - token
  - time
  - Name
  - NCName
----------------------------------------
- test:  http://pangalactic.us/test/
----------------------------------------
- world:  http://earth.milkyway.universe/
----------------------------------------
=======
Classes
=======
3 Class nodes found:
  - space_mission:Spacecraft
  - space_mission:Instrument
  - pgef:HardwareProduct
----------------------------------------
==========
Properties
==========
3 Property nodes found:
  - space_mission:part_number
  - space_mission:payload_instruments
  - space_mission:mass
----------------------------------------
- end -
=================================================================
"""

