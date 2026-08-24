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


class StagedCleanupTest(unittest.TestCase):
    """
    Staging leaves a copy of every viewable file of every assembly looked at.
    Nothing removed them, so they accumulated for the life of the home.
    """

    def test_15_restaging_clears_what_was_there(self):
        """
        CASE:  an assembly restaged after losing a component -- someone
        swapped a part, which is a thing people do.

        The directory is cleared, not added to.  A STEP reader resolves by
        name, so a stale file left behind would be found and the wrong
        assembly rendered, without complaint.
        """
        top = make_rep_file('swap_asm.stp')
        old_part = make_rep_file('old_part.stp', parent=top)
        directory = os.path.dirname(orb.stage_file_closure(top))
        self.assertTrue(os.path.exists(os.path.join(directory,
                                                    'old_part.stp')))
        # the component is replaced
        old_part.component_file_of = None
        make_rep_file('new_part.stp', parent=top)
        orb.save([old_part])
        orb.stage_file_closure(top)
        self.assertFalse(os.path.exists(os.path.join(directory,
                                                     'old_part.stp')),
                         'a file no longer in the set was left staged')
        self.assertTrue(os.path.exists(os.path.join(directory,
                                                    'new_part.stp')))

    def test_16_pruning_removes_orphaned_directories(self):
        """
        CASE:  a staged directory whose RepresentationFile is gone.  It can
        never be wanted again.
        """
        staged = os.path.join(orb.home, 'staged')
        orphan = os.path.join(staged, 'no-such-rep-file-oid')
        os.makedirs(orphan, exist_ok=True)
        with open(os.path.join(orphan, 'x.stp'), 'w') as f:
            f.write('x')
        removed = orb.prune_staged_files()
        self.assertTrue(removed >= 1)
        self.assertFalse(os.path.exists(orphan))

    def test_17_pruning_keeps_live_directories(self):
        """
        CASE:  a staged directory whose file is still here.  Kept -- it is
        the cache for an assembly that can still be viewed, and rebuilding it
        costs a copy of every file in the set.
        """
        top = make_rep_file('live_asm.stp')
        make_rep_file('live_part.stp', parent=top)
        directory = os.path.dirname(orb.stage_file_closure(top))
        orb.prune_staged_files()
        self.assertTrue(os.path.exists(directory))

    def test_18_pruning_a_home_that_has_staged_nothing(self):
        """
        CASE:  no staged directory at all.  Start-up calls this, so it has to
        cope with a home that has never viewed a model.
        """
        import shutil as _shutil
        staged = os.path.join(orb.home, 'staged')
        if os.path.exists(staged):
            _shutil.rmtree(staged)
        self.assertEqual(0, orb.prune_staged_files())


class McadModelFileTest(unittest.TestCase):
    """
    Which of a Model's files is *the* file to open.

    Two shapes have to work.  In one, every file of an export set hangs off
    the assembly's Model, and the file to open is the one the others are
    referenced by.  In the other -- what an import produces now -- each file
    is the Model of its own product, so a subassembly can be opened by
    itself, and that file *is* referenced by its parent, which belongs to a
    different model.
    """

    def mcad_model(self, id_):
        mtype = orb.get('pgefobjects:ModelType.MCAD')
        product = orb.get('test:spacecraft0')
        m = clone('Model', of_thing=product, type_of_model=mtype,
                  id=id_, name=id_)
        orb.save([m])
        return m

    def test_20_the_assembly_file_is_chosen_over_its_components(self):
        """
        CASE:  one Model holding a whole export set.  The assembly file is
        returned, not one of the parts -- opening a part would render a
        component instead of the assembly.
        """
        model = self.mcad_model('one-model-set')
        master = make_rep_file('whole_asm.stp')
        part = make_rep_file('whole_part.stp', parent=master)
        master.of_object = model
        part.of_object = model
        orb.save([master, part])
        got = orb.get_mcad_model_file_path(model)
        self.assertTrue(got.endswith('whole_asm.stp'), got)

    def test_21_a_subassembly_model_returns_its_own_file(self):
        """
        CASE:  a Model of a subassembly, whose single file is referenced by
        the parent assembly's file -- which belongs to a different Model.

        Testing component_file_of alone would skip it and leave the model
        with no file at all, which is exactly what "open this subassembly in
        the viewer" needs to work.
        """
        parent_model = self.mcad_model('parent-model')
        parent_file = make_rep_file('parent_asm.stp')
        parent_file.of_object = parent_model
        sub_model = self.mcad_model('sub-model')
        sub_file = make_rep_file('sub_asm.stp', parent=parent_file)
        sub_file.of_object = sub_model
        orb.save([parent_file, sub_file])
        got = orb.get_mcad_model_file_path(sub_model)
        self.assertTrue(got.endswith('sub_asm.stp'), got)
        # ... and the parent still returns its own
        got_parent = orb.get_mcad_model_file_path(parent_model)
        self.assertTrue(got_parent.endswith('parent_asm.stp'), got_parent)


class SerializeModelsTest(unittest.TestCase):
    """
    A product sent to a client must carry what the server knows about it.

    A product whose model is a STEP assembly is incomplete without that model
    and its files -- there is nothing to render and nothing to compute mass
    properties from -- so `include_models` exists and the server turns it on
    whenever it sends a product.  It is off by default because a client
    saving a product has no reason to send the models back.
    """

    @classmethod
    def setUpClass(cls):
        from pangalactic.core.serializers import serialize
        cls.serialize = staticmethod(serialize)
        cls.product = orb.get('test:spacecraft0')
        assert cls.product is not None
        mtype = orb.get('pgefobjects:ModelType.MCAD')
        cls.model = clone('Model', of_thing=cls.product, type_of_model=mtype,
                          id='sc0-mcad', name='sc0 mcad model')
        orb.save([cls.model])
        cls.master = make_rep_file('sc0_asm.stp')
        cls.master.of_object = cls.model
        cls.part = make_rep_file('sc0_part.stp', parent=cls.master)
        cls.part.of_object = cls.model
        orb.save([cls.master, cls.part])

    def oids(self, **kw):
        return set(so['oid'] for so in
                   self.serialize(orb, [self.product], **kw))

    def test_10_models_are_left_out_by_default(self):
        """
        CASE:  an ordinary serialization.  No models -- this is the direction
        a client saves in, and the models would be freight.
        """
        self.assertNotIn(self.model.oid, self.oids())

    def test_11_models_come_when_asked_for(self):
        """
        CASE:  include_models.  The model travels with its product.
        """
        self.assertIn(self.model.oid, self.oids(include_models=True))

    def test_12_the_model_brings_its_files(self):
        """
        CASE:  the files come too, without being asked for separately -- a
        Model always carries its has_files, which is why the component-file
        work needed no further plumbing to reach the client.
        """
        oids = self.oids(include_models=True)
        self.assertIn(self.master.oid, oids)
        self.assertIn(self.part.oid, oids)

    def test_13_component_models_come_too(self):
        """
        CASE:  an assembly's components have models of their own.

        They travel as well:  a component's model is as much part of what the
        client should hold as the assembly's own, and for a STEP assembly it
        is where that component's geometry is.
        """
        acus = self.product.components
        self.assertTrue(acus, 'test assembly has no components')
        component = acus[0].component
        mtype = orb.get('pgefobjects:ModelType.MCAD')
        comp_model = clone('Model', of_thing=component, type_of_model=mtype,
                           id='comp-mcad', name='component mcad model')
        orb.save([comp_model])
        oids = self.oids(include_components=True, include_models=True)
        self.assertIn(comp_model.oid, oids)
        # ... and not when models were not asked for
        self.assertNotIn(comp_model.oid, self.oids(include_components=True))
