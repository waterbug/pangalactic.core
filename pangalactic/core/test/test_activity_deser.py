# -*- coding: utf-8 -*-
"""
Unit tests for the reconstruction of Activity parent links ("sub_activity_of")
during deserialization -- the "act_to_sao" fix-up pass in serializers.py.

A sub-activity is created exclusively within the ConOps / timeline modeler, in
the context of its parent, and is never re-parented (see
pangalactic.core/NOTES_ON_ACTIVITIES.md), so its parent is always created
before it and always travels with it.  The fix-up pass exists only because the
two can arrive in either order within a single batch; a parent that cannot be
found at all means the data received was incomplete, and that is reported.
"""
import unittest

from pydispatch import dispatcher

# set the orb
import pangalactic.core.set_uberorb

from pangalactic.core             import orb
from pangalactic.core.serializers import deserialize
from pangalactic.core.test.utils  import create_test_users, create_test_project
from pangalactic.core.utils.datetimes import dtstamp

HOME = 'activity_deser_test'
orb.start(home=HOME)
deserialize(orb, create_test_users())
deserialize(orb, create_test_project())

NOW = dtstamp()

# an Activity in the test project and its parent
CHILD_OID = 'test:Launch.H2G2'
PARENT_OID = 'test:Mission.H2G2'


def serialized_activity(oid, name, sao_oid):
    """
    Build a serialized Activity naming `sao_oid` as its parent.
    """
    return dict(_cname='Activity',
                activity_type='pgefobjects:ActivityType.Operation',
                oid=oid,
                id=name.replace(' ', '-'),
                id_ns='test',
                name=name,
                owner='H2G2',
                creator='test:steve',
                modifier='test:steve',
                sub_activity_of=sao_oid,
                sub_activity_sequence=0,
                create_datetime=NOW,
                mod_datetime=NOW)


class UnresolvedParentListener:
    """
    Capture the "unresolved activity parents" dispatcher signal.
    """
    def __init__(self):
        self.calls = []
        dispatcher.connect(self.on_signal, 'unresolved activity parents')

    def on_signal(self, activities=None):
        self.calls.append(activities or [])

    def disconnect(self):
        dispatcher.disconnect(self.on_signal, 'unresolved activity parents')

    @property
    def names(self):
        return [(getattr(a, 'name', '') or a.oid)
                for call in self.calls for a in call]


class ActivityDeserTest(unittest.TestCase):

    def setUp(self):
        self.listener = UnresolvedParentListener()

    def tearDown(self):
        self.listener.disconnect()

    def test_01_parent_link_from_test_project(self):
        """
        CASE:  the test project's activities, as deserialized at module load.
        """
        act = orb.get(CHILD_OID)
        self.assertIsNotNone(act)
        self.assertIsNotNone(act.sub_activity_of)
        self.assertEqual(PARENT_OID, act.sub_activity_of.oid)

    def test_02_child_before_parent_in_same_batch(self):
        """
        CASE:  a child is deserialized *before* its parent within one batch.
        This is the case the fix-up pass exists for:  when the child is
        created its parent does not yet exist, so the link cannot be set then.
        """
        parent_oid = 'test:act-parent-02'
        child_oid = 'test:act-child-02'
        # child first, parent second
        sos = [serialized_activity(child_oid, 'Child Two', parent_oid),
               serialized_activity(parent_oid, 'Parent Two', '')]
        deserialize(orb, sos)
        child = orb.get(child_oid)
        parent = orb.get(parent_oid)
        self.assertIsNotNone(child)
        self.assertIsNotNone(parent)
        self.assertIsNotNone(child.sub_activity_of)
        self.assertEqual(parent_oid, child.sub_activity_of.oid)
        # nothing was unresolved
        self.assertEqual([], self.listener.calls)

    def test_03_parent_already_in_db(self):
        """
        CASE:  the parent is not in the batch at all but is already in the
        database.  Also normal:  a sub-activity added to an existing timeline.
        """
        child_oid = 'test:act-child-03'
        deserialize(orb, [serialized_activity(child_oid, 'Child Three',
                                              PARENT_OID)])
        child = orb.get(child_oid)
        self.assertIsNotNone(child.sub_activity_of)
        self.assertEqual(PARENT_OID, child.sub_activity_of.oid)
        self.assertEqual([], self.listener.calls)

    def test_04_top_level_activity_is_not_an_orphan(self):
        """
        CASE:  an Activity with no parent at all.  Normal -- a top-level
        activity -- and must NOT be reported as unresolved.
        """
        oid = 'test:act-toplevel-04'
        deserialize(orb, [serialized_activity(oid, 'Top Level Four', '')])
        act = orb.get(oid)
        self.assertIsNotNone(act)
        self.assertIsNone(act.sub_activity_of)
        self.assertEqual([], self.listener.calls)

    def test_05_unresolvable_parent_is_reported(self):
        """
        CASE:  a child names a parent that is neither in the batch nor in the
        database.  The data is incomplete:  the signal must fire, naming the
        affected activity.
        """
        child_oid = 'test:act-child-05'
        deserialize(orb, [serialized_activity(child_oid, 'Child Five',
                                              'test:no-such-parent')])
        child = orb.get(child_oid)
        # the child itself is still deserialized -- it is not discarded
        self.assertIsNotNone(child)
        self.assertIsNone(child.sub_activity_of)
        # ... but it was reported
        self.assertEqual(1, len(self.listener.calls))
        self.assertIn('Child Five', self.listener.names)

    def test_06_only_the_unresolvable_ones_are_reported(self):
        """
        CASE:  a batch containing both a resolvable and an unresolvable
        parent.  Only the unresolvable one is reported, and the resolvable one
        is still linked.
        """
        parent_oid = 'test:act-parent-06'
        ok_oid = 'test:act-child-06-ok'
        bad_oid = 'test:act-child-06-bad'
        sos = [serialized_activity(parent_oid, 'Parent Six', ''),
               serialized_activity(ok_oid, 'Child Six OK', parent_oid),
               serialized_activity(bad_oid, 'Child Six Bad',
                                   'test:no-such-parent-6')]
        deserialize(orb, sos)
        self.assertEqual(parent_oid, orb.get(ok_oid).sub_activity_of.oid)
        self.assertIsNone(orb.get(bad_oid).sub_activity_of)
        self.assertEqual(1, len(self.listener.calls))
        self.assertEqual(['Child Six Bad'], self.listener.names)


if __name__ == '__main__':
    unittest.main()
