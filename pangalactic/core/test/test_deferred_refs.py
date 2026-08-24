# -*- coding: utf-8 -*-
"""
Tests for object references whose target arrives later in the same batch.

`DESERIALIZATION_ORDER` orders the *classes*, not the objects within a class,
so an attribute pointing at another object of the same class is decided by
which of the two happens to come first in the list.  Setting it to None and
moving on loses the link silently.

That is not hypothetical:  it emptied `component_files` on a client syncing
an imported STEP assembly.  With no component files nothing staged the set
under the names its references use, so the assembly rendered with most of its
geometry missing -- and only the files that happened to already sit in the
vault under plain names appeared, which made it look like a naming problem
rather than a lost link.
"""
import unittest

# set the orb
import pangalactic.core.set_uberorb

from pangalactic.core             import orb
from pangalactic.core.serializers import deserialize

HOME = 'deferred_test'
orb.start(home=HOME)

NOW = '2026-08-26 12:00:00'


def rep_file(oid, name, parent=None):
    """
    A serialized RepresentationFile, optionally referencing another.
    """
    d = dict(_cname='RepresentationFile', oid=oid, id=oid, name=name,
             user_file_name=name, create_datetime=NOW, mod_datetime=NOW)
    if parent:
        d['component_file_of'] = parent
    return d


class DeferredRefsTest(unittest.TestCase):

    def test_01_parent_first(self):
        """
        CASE:  the referenced object comes first.  This always worked.
        """
        deserialize(orb, [rep_file('p1', 'asm.stp'),
                          rep_file('c1', 'part.stp', parent='p1')])
        self.assertEqual('p1', orb.get('c1').component_file_of.oid)
        self.assertEqual(['c1'],
                         [f.oid for f in orb.get('p1').component_files])

    def test_02_child_first(self):
        """
        CASE:  the referenced object comes *second*.  This is the case that
        was silently losing the link.
        """
        deserialize(orb, [rep_file('c2', 'part.stp', parent='p2'),
                          rep_file('p2', 'asm.stp')])
        self.assertEqual('p2', orb.get('c2').component_file_of.oid)
        self.assertEqual(['c2'],
                         [f.oid for f in orb.get('p2').component_files])

    def test_03_deepest_first(self):
        """
        CASE:  a three-deep chain in reverse -- an export set is exactly this
        shape, an assembly naming subassemblies naming parts.
        """
        deserialize(orb, [rep_file('leaf3', 'part.stp', parent='sub3'),
                          rep_file('sub3', 'sub.stp', parent='top3'),
                          rep_file('top3', 'top.stp')])
        self.assertEqual('sub3', orb.get('leaf3').component_file_of.oid)
        self.assertEqual('top3', orb.get('sub3').component_file_of.oid)
        # ... and the closure the viewer stages is complete
        closure = [f.oid for f in orb.get_file_closure(orb.get('top3'))]
        self.assertEqual(['top3', 'sub3', 'leaf3'], closure)

    def test_04_a_target_in_an_earlier_batch(self):
        """
        CASE:  the referenced object is already in the database from a
        previous batch.  A sync arrives in chunks, so this is ordinary.
        """
        deserialize(orb, [rep_file('p4', 'asm.stp')])
        deserialize(orb, [rep_file('c4', 'part.stp', parent='p4')])
        self.assertEqual('p4', orb.get('c4').component_file_of.oid)

    def test_05_a_target_that_never_arrives(self):
        """
        CASE:  the referenced object is nowhere.  The object is still
        deserialized -- discarding received data would be worse -- with the
        reference unset, which is all that can be known.
        """
        deserialize(orb, [rep_file('c5', 'part.stp', parent='nonesuch')])
        obj = orb.get('c5')
        self.assertIsNotNone(obj)
        self.assertIsNone(obj.component_file_of)

    def test_06_an_existing_link_is_not_overwritten(self):
        """
        CASE:  the object already has the reference set.  The deferred pass
        only fills a gap;  it must not reassign one that is already right,
        which is the same guard the act_to_sao pass uses.
        """
        deserialize(orb, [rep_file('p6a', 'a.stp'), rep_file('p6b', 'b.stp'),
                          rep_file('c6', 'part.stp', parent='p6a')])
        self.assertEqual('p6a', orb.get('c6').component_file_of.oid)
        # a later batch naming a different parent does not move it, because
        # the object is unchanged (same mod_datetime) and is not re-created
        deserialize(orb, [rep_file('c6', 'part.stp', parent='p6b')])
        self.assertEqual('p6a', orb.get('c6').component_file_of.oid)

    def test_07_several_deferred_in_one_batch(self):
        """
        CASE:  a whole export set out of order.  Every link is made, not just
        the first -- thirteen files is the real case.
        """
        sobjs = [rep_file(f'f{i}', f'part{i}.stp', parent='root7')
                 for i in range(6)]
        sobjs.append(rep_file('root7', 'root.stp'))
        deserialize(orb, sobjs)
        children = set(f.oid for f in orb.get('root7').component_files)
        self.assertEqual(set(f'f{i}' for i in range(6)), children)


if __name__ == '__main__':
    unittest.main()
