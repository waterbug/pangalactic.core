# -*- coding: utf-8 -*-
"""
Tests for what goes with a Product when it is deleted.

A Model exists to describe one object and a RepresentationFile to carry one
Model's file, so neither has any meaning once that object is gone.  Deleting
a Product used to leave all three behind:  a Model of nothing, a file record
nobody may fetch -- access.may_fetch_file() answers on "of_object" -- and
bytes in the vault that nothing can name, a vault file being named for the
oid of the object that describes it.
"""
import os
import unittest

# set the orb
import pangalactic.core.set_uberorb

from pangalactic.core             import orb, state
from pangalactic.core.serializers import deserialize
from pangalactic.core.test.utils  import (create_test_users,
                                          create_test_project)

HOME = 'delete_cascade_test'
orb.start(home=HOME)
deserialize(orb, create_test_users() + create_test_project())

from pangalactic.core.digital_files import (new_doc_with_file,
                                            new_model_with_file,
                                            stage_in_vault, vault_path)

MCAD = 'pgefobjects:ModelType.MCAD'
USER_OID = 'test:zaphod'


class DeleteCascadeTest(unittest.TestCase):

    def setUp(self):
        self.was_user = state.get('local_user_oid')
        state['local_user_oid'] = USER_OID
        self.tmpdir = os.path.join(orb.home, 'delete_test_files')
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)

    def tearDown(self):
        state['local_user_oid'] = self.was_user

    def a_file(self, name):
        fpath = os.path.join(self.tmpdir, name)
        with open(fpath, 'wb') as f:
            f.write(b'ISO-10303-21; /* ' + name.encode() + b' */\n' * 40)
        return fpath

    def a_product(self, name):
        from pangalactic.core.clone import clone
        p = clone('HardwareProduct', id=f'{name}-id', name=name,
                  save_hw=False)
        orb.db.commit()
        return p

    def a_product_with_a_model(self, name):
        """
        A product, a Model of it, the Model's file, and the file's bytes in
        the vault -- what a STEP import leaves behind.
        """
        product = self.a_product(name)
        fpath = self.a_file(f'{name}.stp')
        model, rep_file = new_model_with_file(
                MCAD, fpath,
                {'file name': f'{name}.stp',
                 'file size': str(os.path.getsize(fpath)),
                 'mime_type': 'application/step', 'name': name,
                 'of_thing_oid': product.oid, 'owner_oid': 'H2G2',
                 'project_oid': 'H2G2'})
        orb.save([model, rep_file])
        orb.db.commit()
        stage_in_vault(rep_file, fpath)
        return product, model, rep_file

    def test_01_the_model_and_its_file_go_with_the_product(self):
        """
        CASE:  the case reported.  Deleting the product left the Model, its
        RepresentationFile and the vault file behind.
        """
        product, model, rep_file = self.a_product_with_a_model('Cascade One')
        oids = (product.oid, model.oid, rep_file.oid)
        orb.delete([product])
        expected = [None, None, None]
        value = [orb.get(oid) for oid in oids]
        self.assertEqual(expected, value)

    def test_02_the_bytes_go_too(self):
        """
        CASE:  the vault file.  A vault file is named for the oid of the
        object that describes it, so bytes whose object is gone can never be
        found again -- and nothing would ever remove them.
        """
        product, model, rep_file = self.a_product_with_a_model('Cascade Two')
        path = vault_path(rep_file)
        was_there = os.path.exists(path)
        orb.delete([product])
        self.assertEqual([True, False], [was_there, os.path.exists(path)])

    def test_03_chunk_files_go_with_the_file(self):
        """
        CASE:  vger.download_chunk() leaves the chunks it cut beside the
        file, as a cache.  They are as unreachable as the file once its
        object is gone.
        """
        product, model, rep_file = self.a_product_with_a_model('Cascade Three')
        path = vault_path(rep_file)
        chunks = [f'{path}_{i}' for i in range(3)]
        for chunk in chunks:
            with open(chunk, 'wb') as f:
                f.write(b'a chunk')
        orb.delete([product])
        self.assertEqual([], [c for c in chunks if os.path.exists(c)])

    def test_04_deleting_a_model_on_its_own_takes_its_file(self):
        """
        CASE:  one rule, wherever the deletion starts.  A Model deleted in
        its own right takes its files with it.
        """
        product, model, rep_file = self.a_product_with_a_model('Cascade Four')
        path = vault_path(rep_file)
        orb.delete([model])
        expected = [None, False, product.oid]
        value = [orb.get(rep_file.oid), os.path.exists(path),
                 getattr(orb.get(product.oid), 'oid', None)]
        self.assertEqual(expected, value)

    def test_05_a_product_with_no_model_is_unaffected(self):
        """CASE:  nothing to cascade to."""
        product = self.a_product('Cascade Five')
        oid = product.oid
        orb.delete([product])
        self.assertIsNone(orb.get(oid))

    def test_06_a_document_attached_to_nothing_else_goes_too(self):
        """
        CASE:  a document attached only to this product.  The reference is
        the attachment;  a document nothing refers to any more is an orphan
        and goes with it, its file and bytes included.
        """
        product = self.a_product('Cascade Six')
        fpath = self.a_file('cascade-six.pdf')
        document, doc_ref, rep_file = new_doc_with_file(
                fpath, {'file name': 'cascade-six.pdf',
                        'file size': str(os.path.getsize(fpath)),
                        'name': 'Cascade Six Doc',
                        'rel_obj_oid': product.oid,
                        'owner_oid': 'H2G2', 'project_oid': 'H2G2'})
        orb.save([document, doc_ref, rep_file])
        orb.db.commit()
        stage_in_vault(rep_file, fpath)
        path = vault_path(rep_file)
        oids = (doc_ref.oid, document.oid, rep_file.oid)
        orb.delete([product])
        expected = [None, None, None, False]
        value = [orb.get(oid) for oid in oids] + [os.path.exists(path)]
        self.assertEqual(expected, value)

    def test_07_a_document_attached_elsewhere_stays(self):
        """
        CASE:  the same document attached to two products.  A document is
        not the property of any one item that refers to it, so deleting one
        of them removes only that attachment.
        """
        from pangalactic.core.clone import clone
        product = self.a_product('Cascade Seven')
        other = self.a_product('Cascade Seven Other')
        fpath = self.a_file('cascade-seven.pdf')
        document, doc_ref, rep_file = new_doc_with_file(
                fpath, {'file name': 'cascade-seven.pdf',
                        'file size': str(os.path.getsize(fpath)),
                        'name': 'Cascade Seven Doc',
                        'rel_obj_oid': product.oid,
                        'owner_oid': 'H2G2', 'project_oid': 'H2G2'})
        second_ref = clone('DocumentReference', id='cascade-seven-ref2',
                           name='second reference', document=document,
                           related_item=other)
        orb.save([document, doc_ref, rep_file, second_ref])
        orb.db.commit()
        stage_in_vault(rep_file, fpath)
        path = vault_path(rep_file)
        orb.delete([product])
        expected = [None, document.oid, rep_file.oid, True]
        value = [orb.get(doc_ref.oid),
                 getattr(orb.get(document.oid), 'oid', None),
                 getattr(orb.get(rep_file.oid), 'oid', None),
                 os.path.exists(path)]
        self.assertEqual(expected, value)


if __name__ == '__main__':
    unittest.main()
