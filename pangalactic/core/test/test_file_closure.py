# -*- coding: utf-8 -*-
"""
Tests for assembling a file and the files it references into a readable set.

A CAD assembly may be exported as several files, each referring to the others
*by name* and resolving them relative to its own directory.  The vault cannot
serve that: a vault file is named `<oid>_<user_file_name>`, so an assembly
opened from there finds none of its references even when all of them have
been downloaded.  Staging is what turns the vault back into a directory a
STEP reader can read.
"""
import os
import unittest

# set the orb
import pangalactic.core.set_uberorb

from pangalactic.core            import orb
from pangalactic.core.clone      import clone
from pangalactic.core.serializers import deserialize
from pangalactic.core.test.utils import create_test_users, create_test_project

HOME = 'closure_test'
orb.start(home=HOME)
deserialize(orb, create_test_users())
deserialize(orb, create_test_project())


def make_rep_file(name, parent=None, content=b'ISO-10303-21;'):
    """
    A RepresentationFile with a physical file in the vault.

    Keyword Args:
        parent (RepresentationFile):  the file that references this one
        content (bytes):  written to the vault, so "is it there" is real
    """
    rf = clone('RepresentationFile', user_file_name=name,
               id=name.replace('.', '_'), name=name)
    if parent is not None:
        rf.component_file_of = parent
    orb.save([rf])
    if content is not None:
        with open(orb.get_vault_fpath(rf), 'wb') as f:
            f.write(content)
    return rf


class FileClosureTest(unittest.TestCase):

    def test_01_closure_of_a_lone_file_is_itself(self):
        """
        CASE:  a file that references nothing.
        """
        rf = make_rep_file('lonely.stp')
        self.assertEqual([rf.oid],
                         [f.oid for f in orb.get_file_closure(rf)])

    def test_02_closure_is_transitive(self):
        """
        CASE:  an assembly naming a subassembly which names a part.  All
        three come back -- the level below the first is the one a
        non-recursive implementation would miss.
        """
        top = make_rep_file('top.stp')
        sub = make_rep_file('sub.stp', parent=top)
        part = make_rep_file('part.stp', parent=sub)
        oids = [f.oid for f in orb.get_file_closure(top)]
        self.assertEqual([top.oid, sub.oid, part.oid], oids)

    def test_03_closure_starts_at_the_file_asked_for(self):
        """
        CASE:  asked about a subassembly rather than the top.  The answer is
        that subassembly's own set, not the whole export.
        """
        top = make_rep_file('top3.stp')
        sub = make_rep_file('sub3.stp', parent=top)
        part = make_rep_file('part3.stp', parent=sub)
        oids = [f.oid for f in orb.get_file_closure(sub)]
        self.assertEqual([sub.oid, part.oid], oids)

    def test_04_staging_writes_every_file_under_its_own_name(self):
        """
        CASE:  the whole point.  Each file is staged under its
        user_file_name, which is the name the references use -- not the
        vault name, which no reference will ever match.
        """
        top = make_rep_file('asm.stp')
        sub = make_rep_file('subasm.stp', parent=top)
        part = make_rep_file('prt.stp', parent=sub)
        staged_root = orb.stage_file_closure(top)
        self.assertTrue(staged_root)
        directory = os.path.dirname(staged_root)
        self.assertEqual('asm.stp', os.path.basename(staged_root))
        for name in ('asm.stp', 'subasm.stp', 'prt.stp'):
            self.assertTrue(os.path.exists(os.path.join(directory, name)),
                            f'{name} not staged')
        # and the content is the file's, not an empty placeholder
        with open(os.path.join(directory, 'prt.stp'), 'rb') as f:
            self.assertEqual(b'ISO-10303-21;', f.read())
        # the vault name appears nowhere -- that is what defeated resolution
        self.assertNotIn(part.oid, os.listdir(directory))

    def test_05_a_lone_file_is_not_copied(self):
        """
        CASE:  a file referencing nothing is readable where it is, so
        staging returns the vault path rather than making a copy of it.
        """
        rf = make_rep_file('single.stp')
        self.assertEqual(orb.get_vault_fpath(rf),
                         orb.stage_file_closure(rf))

    def test_06_missing_root_file_stages_nothing(self):
        """
        CASE:  the file itself has not been downloaded.  There is nothing to
        open, and the caller has to fetch it first.
        """
        rf = make_rep_file('absent.stp', content=None)
        self.assertEqual('', orb.stage_file_closure(rf))

    def test_07_a_partial_set_stages_what_it_has(self):
        """
        CASE:  some referenced files are not downloaded yet.

        Staged as far as possible rather than refused:  a reader given a
        partial set renders what it can, which beats rendering nothing, and
        the caller cannot always tell in advance what is present.
        """
        top = make_rep_file('partial.stp')
        here = make_rep_file('here.stp', parent=top)
        make_rep_file('notyet.stp', parent=top, content=None)
        staged_root = orb.stage_file_closure(top)
        self.assertTrue(staged_root)
        directory = os.path.dirname(staged_root)
        self.assertTrue(os.path.exists(os.path.join(directory,
                                                    here.user_file_name)))
        self.assertFalse(os.path.exists(os.path.join(directory,
                                                     'notyet.stp')))

    def test_08_staging_refreshes_a_stale_copy(self):
        """
        CASE:  a file staged earlier, since replaced in the vault.  The
        vault copy is the authority, so the staged one is overwritten -- a
        new version must not be shadowed by the previous staging.
        """
        top = make_rep_file('stale.stp')
        sub = make_rep_file('substale.stp', parent=top)
        staged_root = orb.stage_file_closure(top)
        directory = os.path.dirname(staged_root)
        with open(orb.get_vault_fpath(sub), 'wb') as f:
            f.write(b'NEW CONTENT')
        orb.stage_file_closure(top)
        with open(os.path.join(directory, 'substale.stp'), 'rb') as f:
            self.assertEqual(b'NEW CONTENT', f.read())

    def test_09_two_assemblies_do_not_collide(self):
        """
        CASE:  two assemblies each referencing a part file of the same name.
        Staged apart, or one would overwrite the other's part with a
        different file that happens to share its name.
        """
        top_a = make_rep_file('a_asm.stp')
        make_rep_file('shared_prt.stp', parent=top_a, content=b'A')
        top_b = make_rep_file('b_asm.stp')
        make_rep_file('shared_prt.stp', parent=top_b, content=b'B')
        dir_a = os.path.dirname(orb.stage_file_closure(top_a))
        dir_b = os.path.dirname(orb.stage_file_closure(top_b))
        self.assertNotEqual(dir_a, dir_b)
        with open(os.path.join(dir_a, 'shared_prt.stp'), 'rb') as f:
            self.assertEqual(b'A', f.read())
        with open(os.path.join(dir_b, 'shared_prt.stp'), 'rb') as f:
            self.assertEqual(b'B', f.read())


if __name__ == '__main__':
    unittest.main()
