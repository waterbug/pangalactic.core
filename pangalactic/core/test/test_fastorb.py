# -*- coding: utf-8 -*-
"""
Unit tests for pangalactic.core.fastorb.orb
"""
# from math import fsum
import os, shutil
import unittest

# yaml
# import ruamel_yaml as yaml

# pangalactic

# set the orb
import pangalactic.core.set_fastorb

# core
from pangalactic.core              import orb, refdata, prefs
                                           # write_config, write_prefs)
from pangalactic.core.parametrics  import (componentz, data_elementz,
                                           parameterz, rqt_allocz,
                                           serialize_des,
                                           serialize_parms)
from pangalactic.core.test         import data as test_data_module
from pangalactic.core.test         import vault as vault_module
from pangalactic.core.test.utils   import (create_test_users,
                                           create_test_project,
                                           locally_owned_test_objects,
                                           owned_test_objects,
                                           related_test_objects)
from pangalactic.core.utils.datetimes import dtstamp

from pangalactic.core.smerializers import serialize, deserialize

# =============================================================================
# for testing purposes, create data_elements.json and parameter.json files with
# the data elements and parameters of the test data so they are loaded during
# orb.start() and are usable by tests ...
# =============================================================================
home = 'marvin_test'
if not os.path.exists(home):
    os.makedirs(home, 0o775)
parms_path = os.path.join(home, 'parameters.json')
shutil.copyfile('parameters_test_fastorb.json', parms_path)  
des_path = os.path.join(home, 'data_elements.json')
shutil.copyfile('data_elements_test_fastorb.json', des_path)  
orb.start(home=home, debug=True)
serialized_test_objects = create_test_users()
serialized_test_objects += create_test_project()
prefs['default_data_elements'] = ['TRL', 'Vendor']
prefs['default_parms'] = [
    'm[CBE]',
    'm[Ctgcy]',
    'm[MEV]',
    'P[CBE]',
    'P[Ctgcy]',
    'P[MEV]',
    'R_D[CBE]',
    'R_D[Ctgcy]',
    'R_D[MEV]',
    'Cost',
    'height',
    'width',
    'depth']

NOW = str(dtstamp())


class OrbTest(unittest.TestCase):
    maxDiff = None

    def test_00_home_dir_created(self):
        """
        CASE:  home directory is created
        """
        value = os.path.exists(orb.home)
        expected = True
        self.assertEqual(expected, value)

    def test_01_home_dir_has_expected_subdirs(self):
        """
        CASE:  expected subdirectories of home directory exist
        """
        value = [os.path.exists(os.path.join(orb.home, 'vault')),
                 os.path.exists(os.path.join(orb.home, 'test_data'))]
        expected = [True, True]
        self.assertEqual(expected, value)

    def test_02_vault_contains_expected_test_files(self):
        """
        CASE:  vault contains the files from p.test.vault
        """
        # files in pangalactic/test/vault should be copied to orb.vault dir
        vault_module_path = vault_module.__path__[0]
        vault_module_files = set([s for s in os.listdir(vault_module_path)
                                  if not s.startswith('__init__')])
        test_vault_files = set(os.listdir(orb.vault))
        value = test_vault_files.issubset(vault_module_files)
        expected = True
        self.assertEqual(expected, value)

    def test_03_test_data_dir_contains_expected_test_files(self):
        """
        CASE:  test_data_dir contains the files from p.test.data
        """
        # files in pangalactic/test/data should be copied to orb.test_data_dir
        test_data_mod_path = test_data_module.__path__[0]
        test_data_mod_files = set([s for s in os.listdir(test_data_mod_path)
                                   if not s.startswith('__init__')])
        test_data_files = set(os.listdir(orb.test_data_dir))
        value = test_data_files.issubset(test_data_mod_files)
        expected = True
        self.assertEqual(expected, value)

    def test_04_load_reference_data(self):
        """
        CASE:  deserialize the data in p.repo.refdata
        """
        # Reference data in p.repo.refdata should be deserialized into objects
        # and saved in the db:  this test simply verifies that for each
        # serialized object in refdata, there is an object in the db with the
        # same 'oid'.  (orb.start() calls load_reference_data(), so it has
        # always been run before this test runs.  It is possible to delete a
        # refdata object in an installed application, but this test always
        # starts with a fresh test "installation" so should always pass.)
        # oids = [o['oid'] for o in refdata.initial]
        # oids += [o['oid'] for o in refdata.core]
        oids = (set(refdata.ref_oids)
                - set(refdata.ref_pd_oids)
                - set(refdata.ref_de_oids))
        res = orb.get(oids=oids)
        found_oids = [o.oid for o in res]
        value = set(oids) - set(found_oids)
        expected = set()
        self.assertEqual(expected, value)

    def test_05_check_serialized_test_objects(self):
        """
        CASE:  check serialized test objects
        """
        # Trivial, tests that the serialized test objects are as specified.
        value = create_test_users() + create_test_project()
        expected = serialized_test_objects
        self.assertEqual(expected, value)

    def test_06_load_serialized_test_objects(self):
        """
        CASE:  load the serialized test objects into the db
        """
        # orb.load_serialized_test_objects(None, test=True) deserializes the
        # serialized test objects returned by create_test_objects() and saves
        # them in the db:  this test simply verifies that for each serialized
        # test object there is an object in the db with the same 'oid'.
        oids = []
        for serialized_object in serialized_test_objects:
            if not serialized_object['oid'].startswith('pgefobjects:'):
                oids.append(serialized_object['oid'])
        deserialize(orb, serialized_test_objects)
        # assign test parameters and data elements to HWProducts for use in
        # subsequent tests ...
        objs = orb.get_by_type('HardwareProduct')
        orb.assign_test_parameters(objs)
        value = len(orb.get(oids=oids))
        expected = len(oids)
        self.assertEqual(expected, value)

    def test_07_verify_deserialized_requirement_with_alloc(self):
        """
        CASE:  verify that deserialized requirement has an allocation.
        """
        req = orb.get('test:H2G2:Spacecraft-Mass')
        alloc_oid = getattr(req.allocated_to, 'oid', '')
        comp_form_oid = getattr(req.computable_form, 'oid', '')
        value = [alloc_oid, comp_form_oid]
        expected = ['test:H2G2:system-1',
                    'test:H2G2:Spacecraft-Mass-Computable-Form']
        self.assertEqual(expected, value)

    # ===================================================================
    # NOTE: test_08 is not appicable to fastorb as it does not have a
    # recompute_parmz() method.
    # ===================================================================
    # def test_08_test_assigned_parameters_and_data_elements(self):
        # """
        # CASE:  test the parameters and data elements assigned to the serialized
        # test objects.

        # This tests the 'add_parameter()', 'add_default_parameters()',
        # 'add_data_element()', and 'add_default_data_elements()'
        # functions of the p.core.parametrics module since
        # 'assign_test_parameters' uses them.
        # """
        # # for debugging, write config and prefs files to home dir ...
        # write_config(os.path.join(orb.home, 'config'))
        # write_prefs(os.path.join(orb.home, 'prefs'))
        # orb.recompute_parmz()
        # self.test_hw = []
        # hw = orb.get_by_type('HardwareProduct')
        # for h in hw:
            # if h.oid.startswith('test:'):
                # self.test_hw.append(h)
        # # test that the configured default parameters and their related base
        # # parameters have been added to the test HardwareProducts and assigned
        # # values of the correct type
        # all_pids = prefs['default_parms'] + ['m', 'P', 'R_D']
        # all_deids = prefs['default_data_elements']
        # expected = []
        # value = []
        # for h in self.test_hw:
            # for pid in all_pids:
                # pval = get_pval(h.oid, pid)
                # value.append(type(pval) in [int, float])
                # expected.append(True)
            # for deid in all_deids:
                # dval = get_dval(h.oid, deid)
                # value.append(type(dval) in [str, int, float])
                # expected.append(True)
        # self.assertEqual(expected, value)

    def test_09_get(self):
        """
        CASE:  test orb.get()
        """
        obj = orb.get('H2G2')   # Project 'H2G2' test object
        test_obj_attrs = dict(oid='H2G2', id='H2G2', id_ns='test',
                              name='Hitchhikers Guide to the Galaxy',
                              name_code='H2G2')
        obj_attrs = {a: getattr(obj, a) for a in test_obj_attrs}
        self.assertEqual(test_obj_attrs, obj_attrs)

    # def test_09_save(self, savelist):
        # pass
    # test_save.todo = 'not done.'

    def test_10_search_exact(self):
        """
        CASE:  test orb.search_exact()
        """
        sc_type = orb.get('pgefobjects:ProductType.spacecraft')
        value = orb.search_exact(cname='HardwareProduct', product_type=sc_type)
        sc0 = orb.get('test:spacecraft0')
        sc1 = orb.get('test:spacecraft1')
        sc2 = orb.get('test:spacecraft2')
        expected = [sc0, sc1, sc2]
        self.assertEqual(expected, value)

    # def test_11_select(self, ...):
        # pass
    # test_search.todo = 'not done.'

    def test_11_serialize_simple(self):
        """
        CASE:  serialize a simple object (no parameters, no components)
        """
        # This test verifies that the values in the serialized
        # object match the values of the object attributes.
        h2g2 = orb.get('H2G2')   # Project 'H2G2' test object
        res = serialize(orb, [h2g2])
        value = [len(res)]
        for sobj in res:
            if sobj['oid'] == h2g2.oid:
                value.append(sobj['_cname'])
                value.append(sobj['create_datetime'])
                value.append(sobj['mod_datetime'])
                value.append(sobj['id'])
                value.append(sobj['name'])
        # serialized form includes only the original object
        expected = [1,
                    h2g2._cname,
                    h2g2.create_datetime,
                    h2g2.mod_datetime,
                    h2g2.id,
                    h2g2.name]
        self.assertEqual(expected, value)

    def test_12_yaml_dump_and_load_numeric_string_attr(self):
        """
        CASE:  Use yaml to dump and load a serialized object that has an
        attribute whose value is a string consisting of all numeric characters
        with a leading zero (0).  This case is needed to test the dump and load
        of Person instances for which the 'oid' attribute is a string that is
        sometimes required to have that format (numeric characters with a
        leading zero) and retain its leading zero in the dump/load round trip
        -- in the field, this has caused errors when the yaml dump does not
        quote the string and it is then loaded by yaml as an integer rather
        than a string.
        """
        obj = orb.create_or_update_thing('Person', oid='0123456789',
                                         name='John Icecicleboy')
        res = serialize(orb, [obj])
        # data = yaml.safe_dump(res)
        # out_data = yaml.safe_load(data)
        out_objs = deserialize(orb, res)
        # serialized form includes only the original object
        out_obj = out_objs[0]
        value = out_obj.oid
        expected = obj.oid
        self.assertEqual(expected, value)

    def test_13_serialize_with_parameters_no_components(self):
        """
        CASE:  serialize an object with parameters but do not include
        components (i.e. use default:  include_components=False)
        """
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
            if so['oid'] == 'test:port.twanger.0':
                value['port_oid'] = 'test:port.twanger.0'
                value['port_of_product'] = 'test:twanger'
                value['type_of_port'] = 'pgefobjects:PortType.electrical_power'
                # derived values to test parameters & data elements
                directionality = so['data_elements']['directionality']
                value['directionality'] = directionality
                voltage = so['parameters']['V']
                value['voltage'] = voltage
        # serialized form includes 2 objects:
        # the twanger + 1 port
        expected = dict(
            length=2,
            twanger_id=obj.id,
            twanger_parameters=serialize_parms(obj.oid),
            twanger_product_type=obj.product_type.oid,
            port_oid=obj.ports[0].oid,
            port_of_product=obj.ports[0].of_product.oid,
            type_of_port=obj.ports[0].type_of_port.oid,
            directionality='input',
            voltage=28.0
            )
        self.assertEqual(expected, value)

    def test_14_serialize_with_parameters_and_components(self):
        """
        CASE:  serialize an object including its components (use
        include_components=True)
        """
        # This test verifies that the values in the serialized
        # object match the "cooked" values of the object attributes.
        obj = orb.get('test:spacecraft0')   # HardwareProduct test object
        serialized = serialize(orb, [obj], include_components=True)
        acus = 0
        products = 0
        for so in serialized:
            if so['_cname'] == 'HardwareProduct':
                products += 1
            if so['oid'] == 'test:spacecraft0':
                main_object = so
            elif so['_cname'] == 'Acu':
                acus += 1
        value = (main_object, products, acus)
        expected = ({
            '_cname': obj._cname,
            'comment': obj.comment,
            'create_datetime': obj.create_datetime,
            'creator': obj.creator.oid,
            'data_elements': serialize_des(obj.oid),
            'description': obj.description,
            'id': obj.id,
            'id_ns': obj.id_ns,
            'iteration': obj.iteration,
            'mod_datetime': obj.mod_datetime,
            'modifier': obj.modifier.oid,
            'name': obj.name,
            'oid': obj.oid,
            'owner': obj.owner.oid,
            'parameters': serialize_parms(obj.oid),
            'product_type': obj.product_type.oid,
            'public': True,
            'version': obj.version,
            'version_sequence': obj.version_sequence
            },
            7, 6)
        self.assertEqual(expected, value)

    def test_15_deserialize_simple(self):
        """
        CASE:  deserialize a simple object (no parameters)
        """
        serialized_obj = {
            '_cname': 'Project',
            'create_datetime': '2017-01-22 00:00:00.0',
            'id': 'TEST',
            'id_ns': 'test',
            'mod_datetime': '2017-01-22 00:00:00.0',
            'name': 'Test Project',
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
                 obj.oid,
                 ]
        expected = [
                    serialized_obj['create_datetime'],
                    serialized_obj['id'],
                    serialized_obj['id_ns'],
                    serialized_obj['mod_datetime'],
                    serialized_obj['name'],
                    serialized_obj['oid']
                    ]
        self.assertEqual(expected, value)

    def test_16_deserialize_modified(self):
        """
        CASE:  deserialize a modified object that exists in db
        """
        serialized_obj = {
            '_cname': 'Project',
            'create_datetime': '2017-01-22 00:00:00.0',
            'id': 'TEST',
            'id_ns': 'test',
            'mod_datetime': '2019-01-23 00:00:00.0',
            'name': 'Test Project',
            'name_code': 'TEST',
            'oid': 'pgef:Project:TEST',
            # test that unrecognized attributes are ignored:
            'foo': 'pgefobjects:PGANA'}
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
                    serialized_obj['create_datetime'],
                    serialized_obj['id'],
                    serialized_obj['id_ns'],
                    serialized_obj['mod_datetime'],
                    serialized_obj['name'],
                    serialized_obj['name_code'],
                    serialized_obj['oid']
                    ]
        self.assertEqual(expected, value)

    def test_17_deserialize_object_with_new_owner(self):
        """
        CASE:  deserialize an object whose owner is unknown to the db
        """
        objs = deserialize(orb, owned_test_objects)
        for o in objs:
            if o._cname == 'HardwareProduct':
                obj = o
        value = obj.owner
        expected = orb.get('test:yoyoinst')
        self.assertEqual(expected, value)

    def test_18_deserialize_object_with_known_owner(self):
        """
        CASE:  deserialize an object whose owner is already in the db
        """
        objs = deserialize(orb, locally_owned_test_objects)
        for o in objs:
            if o._cname == 'HardwareProduct':
                obj = o
        value = obj.owner
        expected = orb.get('test:yoyodyne')
        self.assertEqual(expected, value)


    def test_21_deserialize_related_objects(self):
        """
        CASE:  deserialize a collection of related objects.  Note that this
        also tests the deserializer's refreshing of the requirement allocation
        cache, 'rqt_allocz', since 'related_test_objects' contains an allocated
        requirement and its allocation, which will be further exercised in
        'test_22_compute_margin' and 'test_23_compute_requirement_margin'.
        """
        # TODO: add rqt_allocz and then fix "value" ...
        objs = deserialize(orb, related_test_objects)
        by_oid = {o.oid : o for o in objs}
        sc_acu_oids = [f'test:spacecraft3-acu-{n}' for n in range(1, 7)]
        value = [
            # bool('test:OTHER:Spacecraft-Mass' in rqt_allocz),
            by_oid['test:OTHER:system-1'].project,
            by_oid['test:OTHER:system-1'].system,
            by_oid['test:spacecraft3'].components,
            by_oid['test:spacecraft3'].has_models,
            by_oid['test:spacecraft3'].owner,
            by_oid['test:spacecraft3.mcad.model.0'].of_thing,
            by_oid['test:spacecraft3.mcad.model.0'].has_files,
            by_oid['test:spacecraft3.mcad.0.RepresentationFile.0'].of_object,
            by_oid['test:spacecraft3.mcad.0.RepresentationFile.0'].url
            ]
        expected = [
            # True,
            by_oid['test:OTHER'],
            by_oid['test:spacecraft3'],
            [by_oid[acu_oid] for acu_oid in sc_acu_oids],
            [by_oid['test:spacecraft3.mcad.model.0']],
            by_oid['test:OTHER'],
            by_oid['test:spacecraft3'],
            [by_oid['test:spacecraft3.mcad.0.RepresentationFile.0']],
            by_oid['test:spacecraft3.mcad.model.0'],
            'vault://Other_0_MCAD_0_R0_File0.step'
            ]
        self.assertEqual(expected, value)



    # TODO:  revise this test!
    # def test_27_deserialize_object_with_modified_parameters(self):
        # """
        # CASE:  deserialize an object with modified parameters
        # """
        # deserialize(orb, parametrized_test_object)
        # oid = parametrized_test_object[0]['oid']
        # obj = orb.get(oid)
        # # assumed to be a local action -> mod_datetime will be generated
        # set_pval(oid, 'm', 42)
        # set_pval(oid, 'P', 33)
        # set_pval(oid, 'R_D', 400, units='Mbit/s')
        # value = parameterz[obj.oid]
        # deser_parms = deepcopy(parameters)
        # expected = deser_parms
        # # save parameters.json file for forensics ...
        # orb._save_parmz()
        # self.assertEqual(expected, value)

    def test_28_is_a_subtype_of(self):
        """
        CASE:  test the orb 'is_a_subtype_of' method.
        """
        hw = orb.get_by_type('HardwareProduct')
        h2g2 = orb.get('H2G2')
        value = [orb.is_a(hw[0], 'Product'),
                 orb.is_a(hw[0], 'Project'),
                 orb.is_a(h2g2, 'Product'),
                 orb.is_a(h2g2, 'Organization')]
        expected = [True, False, False, True]
        self.assertEqual(expected, value)

    # TODO:  does the orb need to write a MEL?  if so, fix it!
    # def test_50_write_mel(self):
        # """
        # CASE:  test success of mel_writer
        # """
        # # verify that the `write_mel_xlsx_from_model` function succeeds
        # obj = orb.get('H2G2')   # Project 'H2G2' test object
        # fpath = os.path.join(orb.vault, 'mel_writer_output.xlsx')
        # write_mel_xlsx_from_model(obj, file_path=fpath)
        # expected = 1
        # value = 1
        # self.assertEqual(expected, value)

    # def test_upload_file(self, obj_oid, file_name):
        # pass

    # def test_get_files(self, ...):
        # pass

