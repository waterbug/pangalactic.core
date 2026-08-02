# -*- coding: utf-8 -*-
"""
Unit tests for the offline parameter / data element deletion queue.

These pin down the asymmetry the queue exists because of:  parameter and data
element *additions* travel with the object in its serialization, while
*deletions* cannot, because deserialize_parms() merges rather than replaces.
The first two cases are the design premise -- if either ever changes, the
queue is either unnecessary or insufficient, and this should fail loudly
rather than have the queue quietly do the wrong thing.

See pangalactic.node/NOTES_ON_OFFLINE_AND_SYNC.md section 3.7.
"""
import os
import shutil
import tempfile
import unittest

# pangalactic
from pangalactic.core import (parm_del_queue, read_parm_del_queue,
                              write_parm_del_queue)
from pangalactic.core.parametrics import (parameterz, parm_defz,
                                          add_parameter, serialize_parms,
                                          deserialize_parms)


class ParmDelQueueTests(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix='parm_del_queue_test_')
        self.qpath = os.path.join(self.home, 'parm_del_queue')
        parm_del_queue.clear()
        parm_defz['m'] = {'id': 'm', 'range_datatype': 'float'}
        parm_defz['P'] = {'id': 'P', 'range_datatype': 'float'}

    def tearDown(self):
        parm_del_queue.clear()
        parameterz.pop('pdq_test_obj', None)
        shutil.rmtree(self.home, ignore_errors=True)

    def queue(self, oid, item_id, kind='parm'):
        """Mirror of PgxnMainWindow.queue_parm_deletion (no GUI needed)."""
        parm_del_queue[f'{kind}|{oid}|{item_id}'] = {
            'kind': kind, 'oid': oid, 'id': item_id,
            'datetime': '2026-08-02 00:00:00'}
        write_parm_del_queue(self.qpath)

    def test_01_additions_ride_along_with_the_object(self):
        """CASE:  a parameter added offline needs no queue"""
        parameterz['pdq_test_obj'] = {'m': 5.0}
        add_parameter('pdq_test_obj', 'P')
        ser = serialize_parms('pdq_test_obj')
        self.assertIn('P', ser)
        # the repository side: its copy predates the addition
        parameterz['pdq_test_obj'] = {'m': 5.0}
        deserialize_parms('pdq_test_obj', ser)
        self.assertIn('P', parameterz['pdq_test_obj'])

    def test_02_deserialize_parms_merges_so_deletions_cannot(self):
        """CASE:  a parameter deleted offline is NOT removed by a push

        This is the entire reason the queue exists:  the pid is simply absent
        from the pushed dict, and absence is not a signal.
        """
        parameterz['pdq_test_obj'] = {'m': 5.0, 'P': 2.0}
        # what the client pushes after deleting P locally
        deserialize_parms('pdq_test_obj', {'m': 5.0})
        self.assertIn('P', parameterz['pdq_test_obj'],
                      'deserialize_parms no longer merges -- the deletion '
                      'queue design premise has changed')

    def test_03_queue_is_self_deduplicating(self):
        """CASE:  deleting the same parameter twice queues one entry"""
        self.queue('pdq_test_obj', 'P')
        self.queue('pdq_test_obj', 'P')
        self.queue('pdq_test_obj', 'Cost', kind='de')
        self.assertEqual(2, len(parm_del_queue))

    def test_04_queue_survives_a_restart(self):
        """CASE:  the queue round-trips through its file

        Offline work spans sessions, so the queue is written as soon as an
        item is queued and re-read by orb.start().
        """
        self.queue('pdq_test_obj', 'P')
        self.queue('pdq_test_obj', 'Cost', kind='de')
        parm_del_queue.clear()
        read_parm_del_queue(self.qpath)
        self.assertEqual(['de|pdq_test_obj|Cost', 'parm|pdq_test_obj|P'],
                         sorted(parm_del_queue))

    def test_05_entries_carry_what_the_replay_needs(self):
        """CASE:  a 'de' entry has what del_de needs, likewise 'parm'"""
        self.queue('pdq_test_obj', 'Cost', kind='de')
        self.queue('pdq_test_obj', 'P')
        de = parm_del_queue['de|pdq_test_obj|Cost']
        self.assertEqual(('de', 'pdq_test_obj', 'Cost'),
                         (de['kind'], de['oid'], de['id']))
        parm = parm_del_queue['parm|pdq_test_obj|P']
        self.assertEqual(('parm', 'pdq_test_obj', 'P'),
                         (parm['kind'], parm['oid'], parm['id']))

    def test_06_reading_a_missing_queue_file_is_a_noop(self):
        """CASE:  first run, before any deletion has ever been queued"""
        read_parm_del_queue(os.path.join(self.home, 'not_there'))
        self.assertEqual({}, parm_del_queue)


if __name__ == '__main__':
    unittest.main()
