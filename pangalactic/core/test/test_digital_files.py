# -*- coding: utf-8 -*-
"""
Unit tests for pangalactic.core.digital_files -- the local creation of a
Model and its RepresentationFile, and the staging of the file's bytes that
makes those objects true.

These run without Qt, without a repository and without a network, which is
the point:  attaching a file to a product used to be an rpc, so none of it
could be tested (or done) without a server.

See pangalactic.node/NOTES_ON_STEP_IMPORT.md section 3c.
"""
import os
import unittest

# set the orb
import pangalactic.core.set_uberorb

from pangalactic.core               import orb, state
from pangalactic.core.access        import (get_owner_id, get_perms,
                                            is_cloaked, may_fetch_file)
from pangalactic.core.serializers   import deserialize
from pangalactic.core.test.utils    import (create_test_users,
                                            create_test_project)

HOME = 'digital_files_test'
orb.start(home=HOME)
deserialize(orb, create_test_users() + create_test_project())

from pangalactic.core.digital_files import (documents_of_local_user,
                                            file_checksum, file_size_of,
                                            is_staged, new_component_file,
                                            new_doc_with_file,
                                            new_model_with_file,
                                            stage_in_vault,
                                            staged_files_of_local_user,
                                            vault_path)

MCAD = 'pgefobjects:ModelType.MCAD'
ASSEMBLY_OID = 'test:spacecraft0'
USER_OID = 'test:zaphod'


def parms_for(fpath, **kw):
    """
    The parms the "add update model" signal carries, as its senders build
    them.
    """
    parms = {'file name': os.path.basename(fpath),
             'file size': str(os.path.getsize(fpath)),
             'mime_type': 'application/step',
             'name': 'Test Assembly',
             'description': 'a model for testing',
             'of_thing_oid': ASSEMBLY_OID,
             'owner_oid': 'H2G2',
             'project_oid': 'H2G2'}
    parms.update(kw)
    return parms


class DigitalFilesTest(unittest.TestCase):

    def setUp(self):
        self.was_user = state.get('local_user_oid')
        state['local_user_oid'] = USER_OID
        self.tmpdir = os.path.join(orb.home, 'df_test_files')
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)
        # Every Person in the test data has a role in H2G2, so there is
        # nobody to test a refusal against;  the first version of the
        # download gate looked correct because what it took for an outsider
        # was in fact a member with an unmatching product type.
        if orb.get('test:outsider') is None:
            from pangalactic.core.clone import clone
            clone('Person', oid='test:outsider', id='outsider',
                  name='An Outsider', first_name='An', last_name='Outsider',
                  org=orb.get('test:yoyodyne'))
            orb.db.commit()

    def tearDown(self):
        state['local_user_oid'] = self.was_user

    def a_file(self, name='thing.stp', content=b'ISO-10303-21;\n'):
        fpath = os.path.join(self.tmpdir, name)
        with open(fpath, 'wb') as f:
            f.write(content)
        return fpath

    # ---- the checksum ----------------------------------------------------

    def test_01_checksum_is_the_sha256_of_the_contents(self):
        """
        CASE:  a readable file.  `DigitalFile.checksum` is defined as a
        sha-256 of the contents, so that is what goes in it.
        """
        import hashlib
        fpath = self.a_file('hashed.stp', b'some bytes')
        expected = hashlib.sha256(b'some bytes').hexdigest()
        value = file_checksum(fpath)
        self.assertEqual(expected, value)

    def test_02_unreadable_file_checksums_to_empty(self):
        """
        CASE:  a file that cannot be read.  '' means "cannot compare", which
        callers must not read as "differs".
        """
        expected = ''
        value = file_checksum('/no/such/file/at/all.stp')
        self.assertEqual(expected, value)

    def test_03_size_comes_from_the_file_not_the_caller(self):
        """
        CASE:  parms understate the size.  The file is the authority;  the
        signal's value is a fallback for a file that is not there.
        """
        fpath = self.a_file('sized.stp', b'0123456789')
        expected = [10, 42, 0]
        value = [file_size_of(fpath, {'file size': '3'}),
                 file_size_of('/no/such/file', {'file size': '42'}),
                 file_size_of('/no/such/file', {})]
        self.assertEqual(expected, value)

    # ---- creating the objects --------------------------------------------

    def test_04_a_model_and_a_file_are_created(self):
        """
        CASE:  the ordinary one.  Both objects exist, related to each other
        and to the thing modelled, without any rpc.
        """
        fpath = self.a_file('rover.stp')
        model, rep_file = new_model_with_file(MCAD, fpath, parms_for(fpath))
        orb.db.commit()
        expected = [True, ASSEMBLY_OID, MCAD, 'rover.stp', model.oid]
        value = [model is not None and rep_file is not None,
                 model.of_thing.oid,
                 model.type_of_model.oid,
                 rep_file.user_file_name,
                 rep_file.of_object.oid]
        self.assertEqual(expected, value)

    def test_05_both_objects_are_stamped_with_the_creator(self):
        """
        CASE:  offline creation.  Both must carry a creator or the sync can
        never carry them -- sync_user_created_objs_to_repo() pushes
        created_objects, and the rpc set no creator on the RepresentationFile
        at all.
        """
        fpath = self.a_file('stamped.stp')
        model, rep_file = new_model_with_file(MCAD, fpath, parms_for(fpath))
        orb.save([model, rep_file])
        orb.db.commit()
        created = {o.oid for o in orb.get(USER_OID).created_objects}
        expected = [['zaphod', 'zaphod'], True, True]
        value = [[getattr(model.creator, 'id', None),
                  getattr(rep_file.creator, 'id', None)],
                 model.oid in created,
                 rep_file.oid in created]
        self.assertEqual(expected, value)

    def test_06_the_url_names_the_vault_file(self):
        """
        CASE:  the derivation that was thought to be server knowledge.  It is
        the RepresentationFile's own oid and user file name, so the client
        computes the same name the repository would.
        """
        fpath = self.a_file('vaulted.stp')
        model, rep_file = new_model_with_file(MCAD, fpath, parms_for(fpath))
        orb.db.commit()
        expected = ['vault://' + rep_file.oid + '_vaulted.stp',
                    rep_file.oid + '_vaulted.stp']
        value = [rep_file.url, orb.get_vault_fname(rep_file)]
        self.assertEqual(expected, value)

    def test_07_size_and_checksum_are_recorded(self):
        """
        CASE:  the two attributes nothing populated.  file_size is stored as
        the int its column is declared as, and checksum is stored at all.
        """
        content = b'ISO-10303-21;' + b'x' * 100
        fpath = self.a_file('measured.stp', content)
        model, rep_file = new_model_with_file(MCAD, fpath, parms_for(fpath))
        orb.db.commit()
        expected = [len(content), True, file_checksum(fpath)]
        value = [rep_file.file_size,
                 isinstance(rep_file.file_size, int),
                 rep_file.checksum]
        self.assertEqual(expected, value)

    def test_08_the_model_follows_the_thing_it_models(self):
        """
        CASE:  a model of a cloaked product.  Public-ness follows the thing
        modelled, as it does in the rpc:  leaving it unset is what once kept
        library models from reaching clients.
        """
        fpath = self.a_file('cloaked.stp')
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = False
            orb.db.commit()
            model, rep_file = new_model_with_file(MCAD, fpath,
                                                  parms_for(fpath))
            orb.db.commit()
            expected = [False, True]
            value = [model.public, is_cloaked(model)]
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()

    def test_09_no_thing_and_no_owner_are_refused(self):
        """
        CASE:  the two conditions the rpc refused on.  Refused here too, and
        reported the same way -- an empty result rather than an exception.
        """
        fpath = self.a_file('orphan.stp')
        no_thing = parms_for(fpath, of_thing_oid='no:such:thing')
        no_owner = parms_for(fpath, owner_oid='', project_oid='')
        expected = [(None, None), (None, None)]
        value = [new_model_with_file(MCAD, fpath, no_thing),
                 new_model_with_file(MCAD, fpath, no_owner)]
        self.assertEqual(expected, value)

    def test_10_the_file_is_owned_by_the_project(self):
        """
        CASE:  a file imported into a project.  The Model carries the owner,
        which is what get_owner_id() resolves for publication -- the
        RepresentationFile has no owner of its own and must delegate.
        """
        fpath = self.a_file('owned.stp')
        model, rep_file = new_model_with_file(MCAD, fpath, parms_for(fpath))
        orb.db.commit()
        expected = ['H2G2', 'H2G2']
        value = [get_owner_id(model), get_owner_id(rep_file)]
        self.assertEqual(expected, value)

    def test_10a_a_file_is_as_cloaked_as_what_it_represents(self):
        """
        CASE:  a file of a cloaked assembly's model.  It must not be
        published on the public channel, because vger.download_chunk()
        authorizes nothing:  the oid of a file is access to the file.
        """
        fpath = self.a_file('proprietary.stp')
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = False
            orb.db.commit()
            model, rep_file = new_model_with_file(MCAD, fpath,
                                                  parms_for(fpath))
            orb.db.commit()
            expected = [True, True, 'H2G2']
            value = [is_cloaked(model), is_cloaked(rep_file),
                     get_owner_id(rep_file)]
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()

    def test_10b_a_public_products_file_stays_public(self):
        """
        CASE:  a model of a public library product.  Delegation must not
        cloak what was never cloaked, or library models stop reaching
        clients -- the defect that made the rpc set `public` in the first
        place.
        """
        fpath = self.a_file('library.stp')
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = True
            orb.db.commit()
            model, rep_file = new_model_with_file(MCAD, fpath,
                                                  parms_for(fpath))
            orb.db.commit()
            expected = [False, False]
            value = [is_cloaked(model), is_cloaked(rep_file)]
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()

    # ---- staging the bytes -----------------------------------------------

    def test_11_the_bytes_are_copied_into_the_local_vault(self):
        """
        CASE:  a newly created file object.  Its bytes go into the vault at
        once, so they are recoverable from the object alone and survive the
        user moving or deleting what they imported.
        """
        content = b'ISO-10303-21; /* staged */'
        fpath = self.a_file('staged.stp', content)
        model, rep_file = new_model_with_file(MCAD, fpath, parms_for(fpath))
        orb.db.commit()
        dest = stage_in_vault(rep_file, fpath)
        os.remove(fpath)
        with open(vault_path(rep_file), 'rb') as f:
            kept = f.read()
        expected = [os.path.join(orb.vault, orb.get_vault_fname(rep_file)),
                    content, True]
        value = [dest, kept, is_staged(rep_file)]
        self.assertEqual(expected, value)

    def test_12_a_short_file_is_not_staged(self):
        """
        CASE:  an interrupted copy or download.  A short file must never be
        mistaken for the file, so is_staged() checks the size and not merely
        that something is there.
        """
        fpath = self.a_file('short.stp', b'0123456789')
        model, rep_file = new_model_with_file(MCAD, fpath, parms_for(fpath))
        orb.db.commit()
        stage_in_vault(rep_file, fpath)
        with open(vault_path(rep_file), 'wb') as f:
            f.write(b'012')
        expected = False
        value = is_staged(rep_file)
        self.assertEqual(expected, value)

    def test_13_an_unstaged_file_is_reported_as_such(self):
        """
        CASE:  objects created but the bytes never copied.  is_staged() says
        so rather than raising, since that is the state the sync must be able
        to see and skip.
        """
        fpath = self.a_file('unstaged.stp')
        model, rep_file = new_model_with_file(MCAD, fpath, parms_for(fpath))
        orb.db.commit()
        expected = False
        value = is_staged(rep_file)
        self.assertEqual(expected, value)

    def test_14_staged_files_are_what_the_sync_has_to_send(self):
        """
        CASE:  a mix of staged and unstaged files created by this user.  The
        vault is the record of what can be sent -- there is no separate queue
        to disagree with it.
        """
        staged = self.a_file('to-send.stp', b'ISO-10303-21; /* send me */')
        bare = self.a_file('not-staged.stp')
        m1, sent = new_model_with_file(MCAD, staged, parms_for(staged))
        m2, unsent = new_model_with_file(MCAD, bare, parms_for(bare))
        orb.save([m1, sent, m2, unsent])
        orb.db.commit()
        stage_in_vault(sent, staged)
        oids = [rf.oid for rf in staged_files_of_local_user()]
        expected = [True, False]
        value = [sent.oid in oids, unsent.oid in oids]
        self.assertEqual(expected, value)


    # ---- component files -------------------------------------------------
    #
    # A CAD assembly exported as a *set* needs an object per file, or only
    # the file the user chose reaches the repository.

    def a_model_and_file(self, name='asm.stp'):
        fpath = self.a_file(name)
        model, rep_file = new_model_with_file(MCAD, fpath, parms_for(fpath))
        orb.db.commit()
        return model, rep_file, fpath

    def component_parms(self, fpath):
        return {'file name': os.path.basename(fpath),
                'file size': str(os.path.getsize(fpath)),
                'mime_type': 'application/step'}

    def test_15_a_referenced_file_joins_the_referencing_files_model(self):
        """
        CASE:  a component file whose product is not known.  It is not a
        model of anything in its own right, so it joins the Model of the file
        that names it rather than getting one of its own.
        """
        model, asm_file, _ = self.a_model_and_file('set-asm.stp')
        part = self.a_file('set-part.stp')
        new_model, rep_file = new_component_file(asm_file, part,
                                                 self.component_parms(part))
        orb.db.commit()
        expected = [None, model.oid, asm_file.oid, 'set-part.stp']
        value = [new_model, rep_file.of_object.oid,
                 rep_file.component_file_of.oid, rep_file.user_file_name]
        self.assertEqual(expected, value)

    def test_16_a_file_that_models_a_product_gets_its_own_model(self):
        """
        CASE:  the product is known.  A Model of *that* product is created,
        which is what lets a subassembly be opened in the 3D viewer on its
        own -- and what makes the file graph and the assembly graph two views
        of one thing.
        """
        model, asm_file, _ = self.a_model_and_file('own-asm.stp')
        part = self.a_file('own-part.stp')
        thing = orb.get(ASSEMBLY_OID)
        new_model, rep_file = new_component_file(asm_file, part,
                                                 self.component_parms(part),
                                                 of_thing=thing)
        orb.db.commit()
        expected = [True, thing.oid, MCAD, new_model.oid,
                    getattr(model.owner, 'oid', None)]
        value = [new_model is not None,
                 new_model.of_thing.oid,
                 new_model.type_of_model.oid,
                 rep_file.of_object.oid,
                 getattr(new_model.owner, 'oid', None)]
        self.assertEqual(expected, value)

    def test_17_the_same_file_is_not_recorded_twice(self):
        """
        CASE:  the same component file offered again.  An import can
        legitimately be repeated, and a part shared by two subassemblies is
        named by both of them in one set, so the existing object is returned
        rather than a duplicate created.
        """
        model, asm_file, _ = self.a_model_and_file('dup-asm.stp')
        part = self.a_file('dup-part.stp')
        parms = self.component_parms(part)
        _, first = new_component_file(asm_file, part, parms)
        orb.save([first])
        orb.db.commit()
        second_model, second = new_component_file(asm_file, part, parms)
        orb.db.commit()
        expected = [first.oid, None, 1]
        value = [second.oid, second_model,
                 len(asm_file.component_files or [])]
        self.assertEqual(expected, value)

    def test_18_a_file_belonging_to_no_model_is_refused(self):
        """
        CASE:  a referencing file with no Model.  There is nothing to attach
        to and nothing sensible to guess, so it is refused the way the rpc
        refused it.
        """
        from pangalactic.core.placements import new_thing
        orphan = new_thing('RepresentationFile', id='orphan-rf',
                           name='orphan', user_file_name='orphan.stp')
        orb.db.commit()
        part = self.a_file('orphaned-part.stp')
        expected = (None, None)
        value = new_component_file(orphan, part, self.component_parms(part))
        self.assertEqual(expected, value)

    def test_19_component_files_are_staged_and_synced_like_any_other(self):
        """
        CASE:  a component file created offline.  It carries a creator and
        its bytes go in the vault, so the ordinary sync path picks it up --
        nothing about a file of a set needs its own mechanism.
        """
        model, asm_file, _ = self.a_model_and_file('sync-asm.stp')
        part = self.a_file('sync-part.stp')
        _, rep_file = new_component_file(asm_file, part,
                                         self.component_parms(part))
        orb.save([rep_file])
        orb.db.commit()
        stage_in_vault(rep_file, part)
        oids = [rf.oid for rf in staged_files_of_local_user()]
        expected = ['zaphod', True, True]
        value = [getattr(rep_file.creator, 'id', None),
                 is_staged(rep_file),
                 rep_file.oid in oids]
        self.assertEqual(expected, value)

    def test_20_a_component_file_is_as_cloaked_as_the_set(self):
        """
        CASE:  a file of a cloaked assembly's export set.  Delegation follows
        of_object, which for a component file is either the referencing
        file's Model or the one made for its own product -- both of which
        follow the product.
        """
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = False
            orb.db.commit()
            model, asm_file, _ = self.a_model_and_file('cloaked-asm.stp')
            part = self.a_file('cloaked-part.stp')
            _, rep_file = new_component_file(asm_file, part,
                                             self.component_parms(part))
            orb.db.commit()
            expected = [True, True]
            value = [is_cloaked(asm_file), is_cloaked(rep_file)]
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()


    # ---- who may fetch a file's bytes ------------------------------------
    #
    # vger.download_chunk() asks access.may_fetch_file().  The policy is
    # here, where it lives;  that the rpc applies it is in
    # pangalactic.vger/test/test_vger.py.
    #
    # NOTE the users these use.  "zaphod" is the local user and therefore the
    # *creator* of everything created here, and "steve" is an Administrator
    # -- both get through by branches that have nothing to do with the
    # project.  "buckaroo" is the one that matters:  an ordinary member of
    # H2G2 who created nothing.  Testing with a creator is how the first
    # version of this gate passed while refusing the file to every other
    # member of the project.

    MEMBER = 'test:buckaroo'      # propulsion_engineer on H2G2, creator of
                                  # nothing
    OUTSIDER = 'test:outsider'    # no role anywhere -- made below, because
                                  # every Person in the test data has one

    def test_20a_the_files_own_perms_would_authorize_everyone(self):
        """
        CASE:  one of the two wrong gates.

        RepresentationFile is in access.modifiables, which grants every user
        view/modify/delete -- so a gate on the file's own perms would be no
        gate at all.
        """
        fpath = self.a_file('perms-own.stp')
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = False
            orb.db.commit()
            model, rep_file = new_model_with_file(MCAD, fpath,
                                                  parms_for(fpath))
            orb.db.commit()
            outsider = orb.get(self.OUTSIDER)
            expected = [True, True]
            value = ['view' in get_perms(rep_file, user=outsider),
                     'modify' in get_perms(rep_file, user=outsider)]
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()

    def test_20b_the_models_perms_would_authorize_almost_no_one(self):
        """
        CASE:  the other wrong gate, and the defect it caused.

        Model and Document are Product subclasses but not HardwareProducts,
        and the Product branch of get_perms() handles only HardwareProduct.
        A cloaked Model therefore matches no branch and falls through to an
        empty set:  an ordinary member of the owning project has no 'view' on
        it.  A gate built on this refuses the file to everyone but the
        creator -- which is what happened, and is why may_fetch_file() does
        not ask.
        """
        fpath = self.a_file('perms-model.stp')
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = False
            orb.db.commit()
            model, rep_file = new_model_with_file(MCAD, fpath,
                                                  parms_for(fpath))
            orb.db.commit()
            member = orb.get(self.MEMBER)
            creator = orb.get(USER_OID)
            expected = [[], True]
            value = [get_perms(model, user=member),
                     'view' in get_perms(model, user=creator)]
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()

    def test_20c_a_project_member_may_fetch_a_cloaked_file(self):
        """
        CASE:  the case that was broken.  An ordinary member of the owning
        project, who created nothing, may fetch the file -- they would have
        been sent the object, since a cloaked object is published on the
        owner's channel and they subscribe to it.
        """
        fpath = self.a_file('fetch-member.stp')
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = False
            orb.db.commit()
            model, rep_file = new_model_with_file(MCAD, fpath,
                                                  parms_for(fpath))
            orb.db.commit()
            expected = True
            value = may_fetch_file(rep_file, orb.get(self.MEMBER))
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()

    def test_20d_someone_outside_the_project_may_not(self):
        """
        CASE:  a user with no role in the owning organization.  The object
        would never have been published to them, so neither are its bytes.
        """
        fpath = self.a_file('fetch-outsider.stp')
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = False
            orb.db.commit()
            model, rep_file = new_model_with_file(MCAD, fpath,
                                                  parms_for(fpath))
            orb.db.commit()
            outsider = orb.get(self.OUTSIDER)
            # asserted, because may_fetch_file(rep_file, None) is also False
            # -- without this the test would pass for the wrong reason if the
            # outsider were never created
            expected = [True, False]
            value = [outsider is not None,
                     may_fetch_file(rep_file, outsider)]
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()

    def test_20e_a_public_products_file_is_for_everyone(self):
        """
        CASE:  a model of a public library product.  Anyone may fetch it --
        shutting the library away is the failure this gate could most easily
        cause.
        """
        fpath = self.a_file('fetch-public.stp')
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = True
            orb.db.commit()
            model, rep_file = new_model_with_file(MCAD, fpath,
                                                  parms_for(fpath))
            orb.db.commit()
            expected = True
            value = may_fetch_file(rep_file, orb.get(self.OUTSIDER))
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()

    def test_20f_a_global_admin_may_fetch_anything(self):
        """
        CASE:  a global admin and a cloaked file of a project they have no
        role in.
        """
        fpath = self.a_file('fetch-admin.stp')
        assembly = orb.get(ASSEMBLY_OID)
        was = assembly.public
        try:
            assembly.public = False
            orb.db.commit()
            model, rep_file = new_model_with_file(MCAD, fpath,
                                                  parms_for(fpath))
            orb.db.commit()
            expected = True
            value = may_fetch_file(rep_file, orb.get('test:steve'))
            self.assertEqual(expected, value)
        finally:
            assembly.public = was
            orb.db.commit()

    def test_20g_a_file_representing_nothing_is_refused(self):
        """
        CASE:  a file with no of_object.  Nothing to inherit access from.
        """
        from pangalactic.core.placements import new_thing
        orphan = new_thing('RepresentationFile', id='fetch-orphan',
                           name='orphan', user_file_name='orphan.stp')
        orb.db.commit()
        expected = [False, False]
        value = [may_fetch_file(orphan, orb.get(USER_OID)),
                 may_fetch_file(None, orb.get(USER_OID))]
        self.assertEqual(expected, value)

    # ---- documents -------------------------------------------------------
    #
    # A Document brings a third object with it, the DocumentReference that
    # attaches it to something -- and that one has no creator, so it cannot
    # travel the way the other two do.

    def doc_parms(self, fpath, **kw):
        parms = {'file name': os.path.basename(fpath),
                 'file size': str(os.path.getsize(fpath)),
                 'name': 'Test Document',
                 'description': 'a document for testing',
                 'rel_obj_oid': ASSEMBLY_OID,
                 'owner_oid': 'H2G2',
                 'project_oid': 'H2G2'}
        parms.update(kw)
        return parms

    def test_21_a_document_its_file_and_its_reference(self):
        """
        CASE:  the ordinary one.  All three objects exist and are related to
        each other and to the item the document is about, without any rpc.
        """
        fpath = self.a_file('spec.pdf', b'%PDF-1.4 test')
        doc, ref, rep_file = new_doc_with_file(fpath, self.doc_parms(fpath))
        orb.db.commit()
        expected = [doc.oid, doc.oid, ASSEMBLY_OID, 'spec.pdf']
        value = [rep_file.of_object.oid, ref.document.oid,
                 ref.related_item.oid, rep_file.user_file_name]
        self.assertEqual(expected, value)

    def test_22_the_document_and_its_file_are_stamped_and_synced(self):
        """
        CASE:  a document created offline.  Document and RepresentationFile
        are Modelables, so a creator makes them reachable by the ordinary
        sync;  the file's bytes go in the vault like any other.
        """
        fpath = self.a_file('stamped-doc.pdf', b'%PDF-1.4 stamped')
        doc, ref, rep_file = new_doc_with_file(fpath, self.doc_parms(fpath))
        orb.save([doc, ref, rep_file])
        orb.db.commit()
        stage_in_vault(rep_file, fpath)
        created = {o.oid for o in orb.get(USER_OID).created_objects}
        oids = [rf.oid for rf in staged_files_of_local_user()]
        expected = [['zaphod', 'zaphod'], True, True, True]
        value = [[getattr(doc.creator, 'id', None),
                  getattr(rep_file.creator, 'id', None)],
                 doc.oid in created, rep_file.oid in created,
                 rep_file.oid in oids]
        self.assertEqual(expected, value)

    def test_23_the_reference_has_no_creator_and_cannot_have_one(self):
        """
        CASE:  the constraint the whole document design turns on.

        A DocumentReference is an Identifiable, so it has no creator and can
        never appear in created_objects.  It cannot be made a Modelable
        either -- `related_item` points at Modelable, which would be its own
        superclass, and sqlalchemy's joined table inheritance cannot tell
        that foreign key from the inheritance one (verified 2026-08-29: the
        orb does not start).  This test records the fact the workaround
        exists for, so that a later attempt to "fix" it finds the reason.
        """
        fpath = self.a_file('unstamped-doc.pdf', b'%PDF-1.4 x')
        doc, ref, rep_file = new_doc_with_file(fpath, self.doc_parms(fpath))
        orb.save([doc, ref, rep_file])
        orb.db.commit()
        created = {o.oid for o in orb.get(USER_OID).created_objects}
        schema = orb.schemas['DocumentReference']
        expected = [False, False,
                    'Modelable', ['Identifiable']]
        value = ['creator' in schema['field_names'],
                 ref.oid in created,
                 schema['fields']['related_item']['range'],
                 sorted(schema['base_names'])]
        self.assertEqual(expected, value)

    def test_24_the_repository_will_accept_a_reference(self):
        """
        CASE:  the workaround's other half.  vger.save() authorizes a new
        object by "the caller is its creator", which a DocumentReference can
        never satisfy -- so it is in access.modifiables, which grants modify
        to any user and is what that list is for.
        """
        from pangalactic.core.access import modifiables
        fpath = self.a_file('accepted-doc.pdf', b'%PDF-1.4 y')
        doc, ref, rep_file = new_doc_with_file(fpath, self.doc_parms(fpath))
        orb.db.commit()
        expected = [True, True]
        value = ['DocumentReference' in modifiables,
                 'modify' in get_perms(ref, user=orb.get(USER_OID))]
        self.assertEqual(expected, value)

    def test_25_a_reference_is_found_by_way_of_its_document(self):
        """
        CASE:  finding what the sync has to carry.  The reference has no
        creator to be found by, so it is found through the Document, which
        does.
        """
        fpath = self.a_file('found-doc.pdf', b'%PDF-1.4 z')
        doc, ref, rep_file = new_doc_with_file(fpath, self.doc_parms(fpath))
        orb.save([doc, ref, rep_file])
        orb.db.commit()
        found = {d.oid: [r.oid for r in refs]
                 for d, refs in documents_of_local_user()}
        expected = [True, [ref.oid]]
        value = [doc.oid in found, found.get(doc.oid)]
        self.assertEqual(expected, value)

    def test_26_the_mime_type_is_guessed_from_the_file_name(self):
        """
        CASE:  a document file.  The import dialog collects no mime type and
        the rpc set none, so every document file in the repository has a null
        one.  The name is the only evidence there is.
        """
        pdf = self.a_file('guessed.pdf', b'%PDF-1.4')
        given = self.a_file('given.stp', b'ISO-10303-21;')
        doc1, _, rf1 = new_doc_with_file(pdf, self.doc_parms(pdf))
        doc2, _, rf2 = new_doc_with_file(
                        given, self.doc_parms(given,
                                              mime_type='application/step'))
        orb.db.commit()
        expected = ['application/pdf', 'application/step']
        value = [rf1.mime_type, rf2.mime_type]
        self.assertEqual(expected, value)

    def test_27_no_related_object_or_owner_is_refused(self):
        """
        CASE:  the two conditions the rpc refused on, refused the same way.
        """
        fpath = self.a_file('refused-doc.pdf', b'%PDF-1.4')
        no_item = self.doc_parms(fpath, rel_obj_oid='no:such:thing')
        no_owner = self.doc_parms(fpath, owner_oid='', project_oid='')
        expected = [(None, None, None), (None, None, None)]
        value = [new_doc_with_file(fpath, no_item),
                 new_doc_with_file(fpath, no_owner)]
        self.assertEqual(expected, value)


if __name__ == '__main__':
    unittest.main()
