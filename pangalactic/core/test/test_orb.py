# -*- coding: utf-8 -*-
"""
Unit tests for pangalactic.core.uberorb.orb
"""
import os
import unittest

# python-dateutil
import dateutil.parser as dtparser

# pangalactic
from pangalactic.core.parametrics import parameterz
from pangalactic.core.serializers import (deserialize, serialize,
                                          serialize_parms)
from pangalactic.core.uberorb     import orb
from pangalactic.core             import refdata
from pangalactic.core.test        import data as test_data_module
from pangalactic.core.test        import vault as vault_module
from pangalactic.core.test.utils  import (create_test_users,
                                          create_test_project,
                                          parametrized_test_objects,
                                          related_test_objects)
from pangalactic.core.utils.reports import write_mel_xlsx

orb.start(home='pangalaxian_test')
serialized_test_objects = create_test_users()
serialized_test_objects += create_test_project()

class OrbTest(unittest.TestCase):

    def test_00_home_dir_created(self):
        """CASE:  home directory is created"""
        value = os.path.exists(orb.home)
        expected = True
        self.assertEqual(expected, value)

    def test_01_home_dir_has_expected_subdirs(self):
        """CASE:  expected subdirectories of home directory exist"""
        value = [os.path.exists(os.path.join(orb.home, 'vault')),
                 os.path.exists(os.path.join(orb.home, 'test_data'))]
        expected = [True, True]
        self.assertEqual(expected, value)

    def test_02_vault_contains_expected_test_files(self):
        """CASE:  vault contains the files from p.test.vault"""
        # files in pangalactic/test/vault should be copied to orb.vault dir
        vault_module_path = vault_module.__path__[0]
        vault_module_files = set([s for s in os.listdir(vault_module_path)
                                  if not s.startswith('__init__')])
        test_vault_files = set(os.listdir(orb.vault))
        value = test_vault_files.issubset(vault_module_files)
        expected = True
        self.assertEqual(expected, value)

    def test_03_test_data_dir_contains_expected_test_files(self):
        """CASE:  test_data_dir contains the files from p.test.data"""
        # files in pangalactic/test/data should be copied to orb.test_data_dir
        test_data_mod_path = test_data_module.__path__[0]
        test_data_mod_files = set([s for s in os.listdir(test_data_mod_path)
                                   if not s.startswith('__init__')])
        test_data_files = set(os.listdir(orb.test_data_dir))
        value = test_data_files.issubset(test_data_mod_files)
        expected = True
        self.assertEqual(expected, value)

    def test_04_load_reference_data(self):
        """CASE:  deserialize the data in p.repo.refdata"""
        # Reference data in p.repo.refdata should be deserialized into objects
        # and saved in the db:  this test simply verifies that for each
        # serialized object in refdata, there is an object in the db with the
        # same 'oid'.  (orb.start() calls load_reference_data(), so it has
        # always been run before this test runs.  It is possible to delete a
        # refdata object in an installed application, but this test always
        # starts with a fresh test "installation" so should always pass.)
        oids = [o['oid'] for o in refdata.initial]
        oids += [o['oid'] for o in refdata.core]
        Identifiable = orb.classes['Identifiable']
        value = orb.db.query(Identifiable).filter(
                                            Identifiable.oid.in_(oids)).count()
        expected = len(oids)
        self.assertEqual(expected, value)

    def test_05_check_serialized_test_objects(self):
        """CASE:  check serialized test objects"""
        # Trivial, tests that the serialized test objects are as specified.
        value = create_test_users() + create_test_project()
        expected = serialized_test_objects
        self.assertEqual(expected, value)

    def test_06_load_serialized_test_objects(self):
        """CASE:  load the serialized test objects into the db"""
        # orb.load_serialized_test_objects(None, test=True) deserializes the
        # serialized test objects returned by create_test_objects() and saves
        # them in the db:  this test simply verifies that for each serialized
        # test object there is an object in the db with the same 'oid'.
        oids = []
        for serialized_object in serialized_test_objects:
            if not serialized_object['oid'].startswith('pgefobjects:'):
                oids.append(serialized_object['oid'])
        Identifiable = orb.classes['Identifiable']
        deserialize(orb, serialized_test_objects)
        objs = orb.get_by_type('HardwareProduct')
        orb.assign_test_parameters(objs)
        value = orb.db.query(Identifiable).filter(
                                            Identifiable.oid.in_(oids)).count()
        expected = len(oids)
        self.assertEqual(expected, value)

    def test_07_get(self):
        obj = orb.get('H2G2')   # Project 'H2G2' test object
        test_obj_attrs = dict(oid='H2G2', id='H2G2', id_ns='test',
                              name=u'Hitchhikers Guide to the Galaxy',
                              name_code='H2G2')
        obj_attrs = {a: getattr(obj, a) for a in test_obj_attrs}
        self.assertEqual(test_obj_attrs, obj_attrs)

    # def test_08_save(self, savelist):
        # pass
    # test_save.todo = 'not done.'

    # def test_09_search_exact(self, ...):
        # pass
    # test_search.todo = 'not done.'

    # def test_10_select(self, ...):
        # pass
    # test_search.todo = 'not done.'

    def test_11_serialize_simple(self):
        """CASE:  serialize a simple object (no parameters, no components)"""
        # This test verifies that the values in the serialized
        # object match the "cooked" values of the object attributes.
        obj = orb.get('H2G2')   # Project 'H2G2' test object
        value = serialize(orb, [obj])
        expected = [{
            '_cname': obj.__class__.__name__,
            'create_datetime': str(obj.create_datetime),
            'id': obj.id.encode('utf-8'),
            'id_ns': obj.id_ns.encode('utf-8'),
            'mod_datetime': str(obj.mod_datetime),
            'name': obj.name.encode('utf-8'),
            'name_code': obj.name_code.encode('utf-8'),
            'oid': obj.oid.encode('utf-8')}]
        self.assertEqual(expected, value)

    def test_12_serialize_with_parameters_no_components(self):
        """CASE:  serialize object with parameters
        (use default:  include_components=False)"""
        # This test verifies that the values in the serialized
        # object match the "cooked" values of the object attributes.
        obj = orb.get('test:twanger')   # HardwareProduct 'GMT' test object
        serialized = serialize(orb, [obj])
        value = dict(length=len(serialized))
        for so in serialized:
            if so['oid'] == 'test:twanger':
                value['twanger_id'] = so['id']
                value['twanger_parameters'] = so['parameters']
                value['twanger_product_type'] = so['product_type']
            if so['_cname'] == 'Port':
                value['port_oid'] = 'test:port.twanger.0'
                value['port_of_product'] = 'test:twanger'
                value['type_of_port'] = 'pgefobjects:PortType.electrical_power'
        expected = dict(
            length=5,
            twanger_id=obj.id.encode('utf-8'),
            twanger_parameters=serialize_parms(parameterz.get(obj.oid, {})),
            twanger_product_type=obj.product_type.oid.encode('utf-8'),
            port_oid=obj.ports[0].oid.encode('utf-8'),
            port_of_product=obj.ports[0].of_product.oid.encode('utf-8'),
            type_of_port=obj.ports[0].type_of_port.oid.encode('utf-8')
            )
        self.assertEqual(expected, value)

    def test_13_serialize_with_parameters_and_components(self):
        """CASE:  serialize an object using include_components=True"""
        # This test verifies that the values in the serialized
        # object match the "cooked" values of the object attributes.
        obj = orb.get('test:hog0')   # HardwareProduct 'HOG' test object
        serialized = serialize(orb, [obj], include_components=True)
        acus = 0
        products = 0
        for so in serialized:
            if so['_cname'] == 'HardwareProduct':
                products += 1
            if so['oid'] == 'test:hog0':
                main_object = so
            elif so['_cname'] == 'Acu':
                acus += 1
        value = (main_object, products, acus)
        expected = ({
            '_cname': obj.__class__.__name__,
            'comment': obj.comment.encode('utf-8'),
            'create_datetime': str(obj.create_datetime),
            'creator': obj.creator.oid.encode('utf-8'),
            'description': obj.description.encode('utf-8'),
            'id': obj.id.encode('utf-8'),
            'id_ns': obj.id_ns.encode('utf-8'),
            'iteration': obj.iteration,
            'mod_datetime': str(obj.mod_datetime),
            'modifier': obj.modifier.oid.encode('utf-8'),
            'name': obj.name.encode('utf-8'),
            'oid': obj.oid.encode('utf-8'),
            'owner': obj.owner.oid.encode('utf-8'),
            'parameters': serialize_parms(parameterz.get(obj.oid, {})),
            'product_type': obj.product_type.oid.encode('utf-8'),
            'public': True,
            'version': obj.version.encode('utf-8'),
            'version_sequence': obj.version_sequence
            },
            6, 5)
        self.assertEqual(expected, value)

    def test_14_deserialize_simple(self):
        """CASE:  deserialize a simple object (no parameters)"""
        serialized_obj = {
            '_cname': 'Project',
            'create_datetime': '2017-01-22 00:00:00.0',
            'id': 'TEST',
            'id_ns': 'test',
            'mod_datetime': '2017-01-22 00:00:00.0',
            'name': 'Test Project',
            'name_code': 'TEST',
            'oid': 'TEST',
            # test that deprecated attrs are ignored:
            'owner': 'H2G2'}
        objs = deserialize(orb, [serialized_obj])
        obj = objs[0]
        value = [
                 obj.create_datetime,
                 obj.id,
                 obj.id_ns,
                 obj.mod_datetime,
                 obj.name,
                 obj.name_code,
                 obj.oid,
                 ]
        expected = [
                    dtparser.parse(serialized_obj['create_datetime']),
                    serialized_obj['id'],
                    serialized_obj['id_ns'],
                    dtparser.parse(serialized_obj['mod_datetime']),
                    unicode(serialized_obj['name']),
                    unicode(serialized_obj['name_code']),
                    serialized_obj['oid']
                    ]
        self.assertEqual(expected, value)

    def test_15_deserialize_modified(self):
        """CASE:  deserialize a modified object that exists in db"""
        serialized_obj = {
            '_cname': 'Project',
            'create_datetime': '2017-01-22 00:00:00.0',
            'id': 'TEST',
            'id_ns': 'test',
            'mod_datetime': '2017-01-22 00:00:00.0',
            'name': 'Test Project',
            'name_code': 'TEST',
            'oid': 'TEST',
            # test that deprecated attributes are ignored:
            'owner': 'pgefobjects:PGANA'}
        objs = deserialize(orb, [serialized_obj])
        obj = objs[0]
        value = [
                 obj.create_datetime,
                 obj.id,
                 obj.id_ns,
                 obj.mod_datetime,
                 obj.name,
                 obj.name_code,
                 obj.oid
                 ]
        expected = [
                    dtparser.parse(serialized_obj['create_datetime']),
                    serialized_obj['id'],
                    serialized_obj['id_ns'],
                    dtparser.parse(serialized_obj['mod_datetime']),
                    unicode(serialized_obj['name']),
                    unicode(serialized_obj['name_code']),
                    serialized_obj['oid']
                    ]
        self.assertEqual(expected, value)

    def test_16_deserialize_object_with_parameters(self):
        """CASE:  deserialize an object with parameters in object form"""
        objs = deserialize(orb, parametrized_test_objects)
        parameters = parametrized_test_objects[0]['parameters']
        for o in objs:
            if o.__class__.__name__ == 'HardwareProduct':
                obj = o
        value = parameterz[obj.oid]
        expected = parameters
        self.assertEqual(expected, value)

    def test_17_deserialize_related_objects(self):
        """CASE:  deserialize a collection of related objects"""
        # TODO:  rather than using existing components from the other test
        # data, create a new set of [serialized] HardwareProduct objects for
        # the components, which would make the data set completely
        # self-contained and would demonstrate the "serializability" of an
        # entire project.  :)
        objs = deserialize(orb, related_test_objects)
        by_oid = {o.oid : o for o in objs}
        acu_oids = ['test:hog3-acu-'+str(n) for n in range(1, 6)]
        value = [
            by_oid['test:OTHER:system-1'].project,
            by_oid['test:OTHER:system-1'].system,
            by_oid['test:hog3'].components,
            by_oid['test:hog3'].has_models,
            by_oid['test:hog3.mcad.model.0'].of_thing,
            by_oid['test:hog3.mcad.model.0'].has_representations,
            by_oid['test:hog3.mcad.0.representation'].of_object,
            by_oid['test:hog3.mcad.0.representation'].has_files,
            by_oid['test:hog3.mcad.0.representationfile.0'].of_representation,
            by_oid['test:hog3.mcad.0.representationfile.0'].url
            ]
        expected = [
            by_oid['test:OTHER'],
            by_oid['test:hog3'],
            [by_oid[acu_oid] for acu_oid in acu_oids],
            [by_oid['test:hog3.mcad.model.0']],
            by_oid['test:hog3'],
            [by_oid['test:hog3.mcad.0.representation']],
            by_oid['test:hog3.mcad.model.0'],
            [by_oid['test:hog3.mcad.0.representationfile.0']],
            by_oid['test:hog3.mcad.0.representation'],
            'vault://HOG_0_MCAD_0_R0_File0.step'
            ]
        self.assertEqual(expected, value)

    def test_50_write_mel(self):
        """CASE:  test output of mel_writer"""
        # This test verifies that the `write_mel_xlsx` function succeeds
        obj = orb.get('H2G2')   # Project 'H2G2' test object
        fpath = os.path.join(orb.vault, 'mel_writer_output.xlsx')
        write_mel_xlsx(obj, file_path=fpath)
        expected = 1
        value = 1
        self.assertEqual(expected, value)

    # def test_change_passwd(self, login_pwd, new_pwd, userid="", secure=1):
        # """CASE:  change_passwd"""
        # pass

    # def test_upload_file(self, obj_oid, file_name):
        # pass

    # def test_get_files(self, ...):
        # pass

