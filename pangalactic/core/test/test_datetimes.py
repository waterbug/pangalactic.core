# $Id$

"""
Unit tests for pangalactic.core.kb
"""

from twisted.trial import unittest
from pangalactic.core.utils import datetimes
from datetime import datetime, date, time


class DatetimesTests(unittest.TestCase):

    def test_01_str2date(self):
        """CASE:  str2date (convert string to date)"""
        value = [datetimes.str2date(s) for s in ['2006-12-17',
                                                 'Sun 17 Dec 2006',
                                                 '2006/12/17',
                                                 '12/17/2006']]
        expected = [date(2006, 12, 17) for x in range(4)]
        self.assertEqual(expected, value)

    def test_02_date2str(self):
        """CASE:  date2str (convert date to string)"""
        value = datetimes.date2str(date(2006, 12, 17))
        expected = '2006-12-17'
        self.assertEqual(expected, value)

    def test_03_str2dt(self):
        """CASE:  str2dt (convert string to datetime)"""
        value = datetimes.str2dt('2006-12-17 12:38:14')
        expected = datetime(2006, 12, 17, 12, 38, 14)
        self.assertEqual(expected, value)

    def test_04_str2dt_no_tz(self):
        """CASE:  str2dt (convert string to datetime w/o timezone info)"""
        value = datetimes.str2dt('2006-12-17 12:38:14')
        expected = datetime(2006, 12, 17, 12, 38, 14)
        self.assertEqual(expected, value)

    def test_05_dt2str(self):
        """CASE:  date2str (convert date to string)"""
        value = datetimes.dt2str(datetime(2006, 12, 17, 12, 38, 14))
        expected = '2006-12-17 12:38:14'
        self.assertEqual(expected, value)

    def test_06_dt2str_no_tz(self):
        """CASE:  date2str (convert date to string w/o timezone info)"""
        value = datetimes.dt2str(datetime(2006, 12, 17, 12, 38, 14))
        expected = '2006-12-17 12:38:14'
        self.assertEqual(expected, value)

    def test_07_str2time(self):
        """CASE:  str2time (converts string to time)"""
        value = datetimes.str2time('12:38:14')
        expected = time(12, 38, 14)
        self.assertEqual(expected, value)

    def test_08_time2str(self):
        """CASE:  time2str (converts time to string)"""
        value = datetimes.time2str(time(12, 38, 14))
        expected = '12:38:14'
        self.assertEqual(expected, value)


