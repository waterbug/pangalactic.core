# $Id$

"""
Unit tests for pangalactic.meta.pgefdatatype uncook functions
"""

from twisted.trial import unittest
import pangalactic.meta.datatypes as dt


class UncookTestCases(unittest.TestCase):

    def test_1_uncookString(self):
        """CASE:  String (Functional)"""
        value = dt.UNCOOKERS['datatype', 'str', True]('spam')
        expected = 'spam'
        self.assertEquals(expected, value)

    def test_1_uncookStrings(self):
        """CASE:  String (NonFunctional)"""
        value = dt.UNCOOKERS['datatype', 'str', False](
                            ['spam', 'eggs', 'bacon'])
        expected = set(['spam', 'eggs', 'bacon'])
        self.assertEquals(expected, value)

