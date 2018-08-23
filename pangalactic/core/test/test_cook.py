# $Id: test_cook.py,v da39ea7970bd 2007/07/27 18:02:33 waterbug $

"""
Unit tests for pangalactic.meta.pgefdatatype.cook
"""

from datetime                    import date, datetime
from twisted.trial               import unittest
from pangalactic.core.utils.meta import cookers


class CookTestCases(unittest.TestCase):

    def test_01_cook_string(self):
        """CASE:  string (Functional)"""
        value = cookers['str']('spam')
        expected = 'spam'
        self.assertEqual(expected, value)

    def test_02_cook_int(self):
        """CASE:  int (Functional)"""
        value = cookers['int'](42)
        expected = 42
        self.assertEqual(expected, value)

    def test_03_cook_float(self):
        """CASE:  float (Functional)"""
        value = cookers['float'](4.2)
        expected = '4.2'
        self.assertEqual(expected, value)

    def test_04_cook_bool_true(self):
        """CASE:  bool (Functional)"""
        value = cookers['bool'](True)
        expected = True
        self.assertEqual(expected, value)

    def test_05_cook_bool_false(self):
        """CASE:  bool (Functional)"""
        value = cookers['bool'](False)
        expected = False
        self.assertEqual(expected, value)

    def test_06_cook_datetime(self):
        """CASE:  datetime (Functional)"""
        dt = datetime(2006, 12, 9, 11, 20, 49)
        value = cookers['datetime'](dt)
        expected = str(dt)
        self.assertEqual(expected, value)

    def test_07_cook_date(self):
        """CASE:  date (Functional)"""
        d = date(2006, 12, 9)
        value = cookers['date'](d)
        expected = str(d)
        self.assertEqual(expected, value)

    def test_08_cook_unicode(self):
        """CASE:  unicode (Functional)"""
        value = cookers['unicode'](u'spam')
        expected = value.encode('utf-8')
        self.assertEqual(expected, value)

    # def test_11_cook_datetimes(self):
        # """CASE:  set of datetimes (NonFunctional)"""
        # dt1 = datetime(2006, 12, 9, 11, 20, 49)
        # dt2 = datetime(2005, 1, 10, 10, 0, 0)
        # dt3 = datetime(2004, 1, 1, 0, 0, 0)
        # value = cook(set([dt1, dt2, dt3]))
        # expected = set([str(dt1), str(dt2), str(dt3)])
        # self.assertEqual(expected, value)

    # def test_13_cook_dates(self):
        # """CASE:  set of dates (NonFunctional)"""
        # d1 = date(2006, 12, 9)
        # d2 = date(2005, 1, 10)
        # d3 = date(2004, 1, 1)
        # value = cook(set([d1, d2, d3]))
        # expected = set([str(d1), str(d2), str(d3)])
        # self.assertEqual(expected, value)

    # def test_15_cook_unicodes(self):
        # """CASE:  set of unicode values (NonFunctional)"""
        # value = cook(set([u'spam', u'eggs', u'bacon']))
        # expected = set([u'spam', u'eggs', u'bacon'])
        # self.assertEqual(expected, value)

