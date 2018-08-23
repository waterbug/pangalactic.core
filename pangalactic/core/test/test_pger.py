"""
Functional test for pangalactic.repo.pger module
"""
from twisted.trial               import unittest
from pangalactic.repo.pger       import PGER

def success(result):
    return result

def failure(f):
    return f

r = PGER.db.registry

class PgerTestCases(unittest.TestCase):

    def test_01_changePassword(self):
        """
        CASE:  changePassword

        (Note:  this should really be a VGER [not PGER] operation.)
        """
        d = PGER.changePassword(
                'admin', 'zaphod@hog.univ', 'sekret')
        expected = ('Password changed for user zaphod@hog.univ '
                    '(requestor: admin).')
        d.addCallbacks(lambda output: self.assertEqual(output, expected),
                       failure)
        return d

    def test_02_addObjects(self):
        """
        CASE:  addObjects
        """
        value = ''
        expected = ''
        self.assertEqual(expected, value)

    def test_02_getObjectByOids(self):
        """
        CASE:  getObjectByOids
        """
        value = ''
        expected = ''
        self.assertEqual(expected, value)

