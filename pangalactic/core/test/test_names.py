"""
Unit tests for pangalactic.meta.names
"""
from StringIO import StringIO
import pkgutil

# Twisted
from twisted.trial import unittest

# rdflib
from rdflib.term import URIRef

# PanGalactic
from pangalactic.core                import names
from pangalactic.core.datastructures import OrderedSet

xmlds = pkgutil.get_data('pangalactic.core.test.data', 'test_data.owl')


class NamesTests(unittest.TestCase):

    ns = names.NS('spam', 'http://testing.spam/spam',
                  names=['a', 'b', 'c'], complete=True, iteration=1,
                  version='a', meta_level=3)

    def test_00_Namespace__init__(self):
        """CASE:  Namespace__init__"""
        value = [self.ns.prefix, self.ns.uri, self.ns.names,
                 self.ns.complete, self.ns.iteration, self.ns.version,
                 self.ns.meta_level]
        expected = ['spam', 'http://testing.spam/spam',
                    OrderedSet(['a', 'b', 'c']), True, 1, 'a', 3]
        self.assertEqual(expected, value)

    def test_01_Namespace_extract(self):
        """CASE:  Namespace_extract"""
        ext = self.ns.extract()
        value = [ext['_meta_id'] == 'Namespace',
                 ext['prefix'] == 'spam',
                 ext['uri'] == 'http://testing.spam/spam',
                 ext['complete'] == True,
                 ext['meta_level'] == 3,
                 ext['iteration'] == 1,
                 ext['version'] == 'a',
                 ext['names'] == ['a', 'b', 'c']]
        expected = [True, True, True, True, True, True, True, True]
        self.assertEqual(expected, value)

    def test_02_register_namespaces(self):
        """CASE:  register_namespaces"""
        names.register_namespaces(StringIO(xmlds))
        a = ('pgef' in names.namespaces)
        b = ('space_mission' in names.namespaces)
        c = names.namespaces['space_mission'].prefix
        d = names.namespaces['space_mission'].names
        value = [a, b, c, d]
        expected = [True, True, 'space_mission',
                    OrderedSet(['', 'part_number', 'payload_instruments',
                    'Instrument', 'Spacecraft', 'mass'])]
        self.assertEqual(expected, value)

    def test_03_register_ns(self):
        """CASE:  register_ns"""
        names.register_ns(self.ns)
        value = self.ns
        expected = names.namespaces['spam']
        self.assertEqual(expected, value)

    def test_04_transliterate_unicode(self):
        """CASE:  transliterate_unicode"""
        # this is essentially a rehash of the unidecode tests
        a = names.transliterate_unicode("Hello World Wooo")
        tu_a = "HelloWorldWooo"
        b = names.transliterate_unicode("hello world woooo")
        tu_b = "hello_world_woooo"
        c = names.transliterate_unicode(u"\u5317\u4EB0")
        tu_c = "BeiJing"
        value = [a, b, c]
        expected = [tu_a, tu_b, tu_c]
        self.assertEqual(expected, value)

    def test_05_u2q(self):
        """CASE:  u2q"""
        a = names.u2q("http://pangalactic.us/objects/chumble")
        u2q_a = "pgefobjects:chumble"
        b = names.u2q("http://pangalactic.us/sandbox/spuz")
        u2q_b = "sandbox:spuz"
        c = names.u2q("http://pangalactic.us/namespaces/gazork")
        u2q_c = "pgefns:gazork"
        d = names.u2q("http://www.w3.org/2002/07/owl#Class")
        u2q_d = "owl:Class"
        value = [a, b, c, d]
        expected = [u2q_a, u2q_b, u2q_c, u2q_d]
        self.assertEqual(expected, value)

    def test_06_q2u(self):
        """CASE:  q2u"""
        a = names.q2u("pgefobjects:chumble")
        q2u_a = URIRef(u"http://pangalactic.us/objects/chumble")
        b = names.q2u("sandbox:spuz")
        q2u_b = URIRef(u"http://pangalactic.us/sandbox/spuz")
        c = names.q2u("pgefns:gazork")
        q2u_c = URIRef(u"http://pangalactic.us/namespaces/gazork")
        d = names.q2u("owl:Class")
        q2u_d = URIRef(u"http://www.w3.org/2002/07/owl#Class")
        try:
            error = names.q2u("#foo")
        except ValueError, err:
            e = str(err)
        q2u_e = "invalid qname"
        try:
            error = names.q2u("ni:knightswhosay")
        except ValueError, err:
            f = str(err)
        q2u_f = "unknown prefix: ni"
        value = [a, b, c, d, e, f]
        expected = [q2u_a, q2u_b, q2u_c, q2u_d, q2u_e, q2u_f]
        self.assertEqual(expected, value)

    def test_07_get_uri(self):
        """CASE:  get_uri"""
        a = names.get_uri("pgefobjects:chumble")
        ga_a = URIRef("http://pangalactic.us/objects/chumble")
        b = names.get_uri("sandbox:spuz")
        ga_b = URIRef("http://pangalactic.us/sandbox/spuz")
        c = names.get_uri("pgefns:gazork")
        ga_c = URIRef("http://pangalactic.us/namespaces/gazork")
        d = names.get_uri("owl:Class")
        ga_d = URIRef("http://www.w3.org/2002/07/owl#Class")
        e = names.get_uri("#foo")
        ga_e = URIRef("#foo")
        f = names.get_uri("http://www.w3.org/2002/07/owl#Class")
        ga_f = URIRef("http://www.w3.org/2002/07/owl#Class")
        try:
            error = names.get_uri("ni:knightswhosay")
        except ValueError, err:
            g = str(err)
        ga_g = "unknown prefix: ni"
        value = [a, b, c, d, e, f, g]
        expected = [ga_a, ga_b, ga_c, ga_d, ga_e, ga_f, ga_g]
        self.assertEqual(expected, value)

