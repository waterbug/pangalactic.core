# $Id$

"""
Unit tests for pangalactic.node.cache
"""

import os, shutil
from twisted.trial import unittest
from pangalactic.node.cache import ObjectCache
from pangalactic.meta.registry import PanGalacticRegistry as R
from pangalactic.test.utils4test import gen_linked_test_objects

# make sure object cache is initially empty
datapath = os.path.join('pangalaxian_test', 'data')
if os.path.exists(datapath):
    shutil.rmtree(datapath)
r = R(home='pangalaxian_test', newcore=1)
c = ObjectCache(schemas=r.schemas.values(), home='pangalaxian_test')

class ObjectCacheTestCases(unittest.TestCase):

    def test_01_cacheGotRegisteredInterfaces(self):
        """CASE:  cache initialized with all registered schemas"""
        value = set(c.schemas)
        expected = set(r.schemas)
        self.assertEqual(expected, value)

    def test_02_saveObjects(self):
        """CASE:  save objects (and retrieve by oids)"""
        objs = gen_linked_test_objects('test_02_saveObjects', r, printout=0)
        odict = dict([(o.oid, o) for o in objs])
        c.saveObjects(objs)
        value = set([c.objs[oid] for oid in odict])
        expected = set(objs)
        self.assertEqual(expected, value)


