# $Id: test_uncook.py,v da39ea7970bd 2007/07/27 18:02:33 waterbug $

"""
Unit tests for pangalactic.meta.pgefdatatype uncook functions
"""

from datetime                    import date, datetime
from twisted.trial               import unittest
from pangalactic.core.utils.meta import cookers, uncookers


class UncookTestCases(unittest.TestCase):

    def test_01_uncook_string(self):
        """CASE:  string (Functional)"""
        uncooked = 'spam'
        cooked = cookers['str'](uncooked)
        value = uncookers[('str', True)](cooked)
        expected = uncooked
        self.assertEqual(expected, value)

    # def test_02_uncook_set_of_strings(self):
        # """CASE:  set of strings (NonFunctional)"""
        # uncooked = set(['spam', 'eggs', 'bacon'])
        # cooked = cookers(uncooked)
        # value = uncookers[('str', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    # def test_03_uncook_list_of_strings(self):
        # """CASE:  list of strings (NonFunctional)"""
        # uncooked = ['spam', 'eggs', 'bacon']
        # cooked = cookers(uncooked)
        # value = uncookers[('str', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    def test_04_uncook_int(self):
        """CASE:  int (Functional)"""
        uncooked = 42
        cooked = cookers['int'](uncooked)
        value = uncookers[('int', True)](cooked)
        expected = uncooked
        self.assertEqual(expected, value)

    # def test_05_uncook_set_of_ints(self):
        # """CASE:  set of ints (NonFunctional)"""
        # uncooked = set([21, 34, 55])
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('int', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    # def test_06_uncook_list_of_ints(self):
        # """CASE:  list of ints (NonFunctional)"""
        # uncooked = [21, 34, 55]
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('int', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    def test_07_uncook_float(self):
        """CASE:  float (Functional)"""
        uncooked = 4.2
        cooked = cookers['float'](uncooked)
        value = uncookers[('float', True)](cooked)
        expected = uncooked
        self.assertEqual(expected, value)

    # def test_08_uncook_set_of_floats(self):
        # """CASE:  set of float (NonFunctional)"""
        # uncooked = set([2.1, 3.4, 5.5])
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('float', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    # def test_09_uncook_list_of_floats(self):
        # """CASE:  list of float (NonFunctional)"""
        # uncooked = [2.1, 3.4, 5.5]
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('float', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    def test_10_uncook_bool(self):
        """CASE:  bool (Functional)"""
        value = uncookers[('bool', True)]('True')
        expected = True
        self.assertEqual(expected, value)

    # def test_11_uncook_set_of_bools(self):
        # """CASE:  set of bools (NonFunctional)"""
        # uncooked = set([True, False, False])
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('bool', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    # def test_12_uncook_list_of_bools(self):
        # """CASE:  list of bools (NonFunctional)"""
        # uncooked = [True, False, False]
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('bool', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    def test_13_uncook_datetime(self):
        """CASE:  datetime (Functional)"""
        uncooked = datetime(2006, 12, 9, 11, 20, 49)
        cooked = cookers['datetime'](uncooked)
        value = uncookers[('datetime', True)](cooked)
        expected = uncooked
        self.assertEqual(expected, value)

    # def test_14_uncook_set_of_datetimes(self):
        # """CASE:  set of datetimes (NonFunctional)"""
        # uncooked = set([datetime(2006, 12, 9, 11, 20, 49),
                        # datetime(2005, 1, 10, 10, 0, 0), 
                        # datetime(2004, 1, 1, 0, 0, 0)])
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('datetime', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    # def test_15_uncook_list_of_datetimes(self):
        # """CASE:  list of datetimes (NonFunctional)"""
        # uncooked = [datetime(2006, 12, 9, 11, 20, 49),
                    # datetime(2005, 1, 10, 10, 0, 0), 
                    # datetime(2004, 1, 1, 0, 0, 0)]
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('datetime', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    def test_16_uncook_date(self):
        """CASE:  date (Functional)"""
        uncooked = date(2006, 12, 9)
        cooked = cookers['date'](uncooked)
        value = uncookers[('date', True)](cooked)
        expected = uncooked
        self.assertEqual(expected, value)

    # def test_17_uncook_set_of_dates(self):
        # """CASE:  set of dates (NonFunctional)"""
        # uncooked = set([date(2006, 12, 9),
                        # date(2005, 1, 10), 
                        # date(2004, 1, 1)])
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('date', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

    # def test_18_uncook_list_of_dates(self):
        # """CASE:  list of dates (NonFunctional)"""
        # uncooked = [date(2006, 12, 9),
                    # date(2005, 1, 10), 
                    # date(2004, 1, 1)]
        # cooked = cookers['str'](uncooked)
        # value = uncookers[('date', False)](cooked)
        # expected = uncooked
        # self.assertEqual(expected, value)

