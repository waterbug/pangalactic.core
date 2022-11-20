# -*- coding: utf-8 -*-
"""
Unit tests for pangalactic.core.uberorb.orb
"""
from math import fsum
import os, shutil
import unittest

# yaml
import ruamel_yaml as yaml

# python-dateutil
import dateutil.parser as dtparser

# pangalactic
from pangalactic.core             import (refdata, state, prefs,
                                          write_config, write_prefs)
from pangalactic.core.access      import get_perms
from pangalactic.core.parametrics import (compute_margin,
                                          compute_requirement_margin,
                                          deserialize_des,
                                          deserialize_parms,
                                          get_dval, data_elementz,
                                          get_pval, parameterz,
                                          load_parmz, load_data_elementz,
                                          req_allocz, round_to,
                                          serialize_des,
                                          serialize_parms,
                                          save_parmz, save_data_elementz)
from pangalactic.core.serializers import serialize, deserialize
from pangalactic.core.test        import data as test_data_module
from pangalactic.core.test        import vault as vault_module
from pangalactic.core.test.utils  import (create_test_users,
                                          create_test_project,
                                          locally_owned_test_objects,
                                          owned_test_objects,
                                          related_test_objects)
from pangalactic.core.uberorb     import orb
from pangalactic.core.utils.reports   import write_mel_xlsx_from_model

orb.start(home='pangalaxian_test')
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
        CASE:  verify that the data in p.repo.refdata has been deserialized.
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
        oids = refdata.ref_oids
        Identifiable = orb.classes['Identifiable']
        res = orb.db.query(Identifiable).filter(
                                            Identifiable.oid.in_(oids))
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
        objs = deserialize(orb, serialized_test_objects)
        orb.db.commit()
        # assign test parameters and data elements to HWProducts for use in
        # subsequent tests ...
        hw = orb.get_by_type('HardwareProduct')
        orb.assign_test_parameters(hw)
        save_parmz('pangalaxian_test')
        save_data_elementz('pangalaxian_test')
        value_oids = set(oids) - set([o.oid for o in objs])
        expected_oids = set()
        req = orb.select('Requirement', id_ns='test')
        expected_req_oid = 'test:H2G2:Spacecraft-Mass'
        value = [value_oids, req.oid]
        expected = [expected_oids, expected_req_oid]
        self.assertEqual(expected, value)

    def test_07_verify_deserialized_requirement_with_alloc(self):
        """
        CASE:  verify that deserialized requirement has an allocation.
        """
        req = orb.get('test:H2G2:Spacecraft-Mass')
        value = getattr(req.allocated_to, 'oid', '')
        expected = 'test:H2G2:system-1'
        self.assertEqual(expected, value)

    def test_08_test_assigned_parameters_and_data_elements(self):
        """
        CASE:  test the parameters and data elements assigned to the serialized
        test objects.

        This tests the 'add_parameter()', 'add_default_parameters()',
        'add_data_element()', and 'add_default_data_elements()'
        functions of the p.core.parametrics module since
        'assign_test_parameters' uses them.
        """
        # for debugging, write config and prefs files to home dir ...
        write_config(os.path.join(orb.home, 'config'))
        write_prefs(os.path.join(orb.home, 'prefs'))
        orb.recompute_parmz()
        self.test_hw = []
        hw = orb.get_by_type('HardwareProduct')
        for h in hw:
            if h.oid.startswith('test:'):
                self.test_hw.append(h)
        # test that the configured default parameters and their related base
        # parameters have been added to the test HardwareProducts and assigned
        # values of the correct type
        all_pids = prefs['default_parms'] + ['m', 'P', 'R_D']
        all_deids = prefs['default_data_elements']
        expected = []
        value = []
        for h in self.test_hw:
            for pid in all_pids:
                pval = get_pval(h.oid, pid)
                value.append(type(pval) in [int, float])
                expected.append(True)
            for deid in all_deids:
                dval = get_dval(h.oid, deid)
                value.append(type(dval) in [str, int, float])
                expected.append(True)
        self.assertEqual(expected, value)

    def test_09_get(self):
        """
        CASE:  test orb.get()
        """
        obj = orb.get('H2G2')   # Project 'H2G2' test object
        test_obj_attrs = dict(oid='H2G2', id='H2G2', id_ns='test',
                              name=u'Hitchhikers Guide to the Galaxy',
                              name_code='H2G2')
        obj_attrs = {a: getattr(obj, a) for a in test_obj_attrs}
        self.assertEqual(test_obj_attrs, obj_attrs)

    # def test_09_save(self, savelist):
        # pass
    # test_save.todo = 'not done.'

    # def test_10_search_exact(self, ...):
        # pass
    # test_search.todo = 'not done.'

    # def test_11_select(self, ...):
        # pass
    # test_search.todo = 'not done.'

    def test_11_serialize_simple(self):
        """
        CASE:  serialize a simple object (no parameters, no components)
        """
        # This test verifies that the values in the serialized
        # object match the "cooked" values of the object attributes.
        obj = orb.get('H2G2')   # Project 'H2G2' test object
        res = serialize(orb, [obj])
        value = [len(res)]
        for sobj in res:
            if sobj['oid'] == obj.oid:
                value.append(sobj['_cname'])
                value.append(sobj['create_datetime'])
                value.append(sobj['mod_datetime'])
                value.append(sobj['id'])
                value.append(sobj['name'])
                value.append(sobj['name_code'])
        # serialized form includes only the original object
        expected = [1,
                    obj.__class__.__name__,
                    str(obj.create_datetime),
                    str(obj.mod_datetime),
                    obj.id,
                    obj.name,
                    obj.name_code]
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
        Person = orb.classes['Person']
        obj = Person(oid='0123456789', name='John Icecicleboy')
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
            if so['_cname'] == 'Port' and so['oid'] == 'test:port.twanger.0':
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
            '_cname': obj.__class__.__name__,
            'comment': obj.comment,
            'create_datetime': str(obj.create_datetime),
            'creator': obj.creator.oid,
            'data_elements': serialize_des(obj.oid),
            'description': obj.description,
            'id': obj.id,
            'id_ns': obj.id_ns,
            'iteration': obj.iteration,
            'mod_datetime': str(obj.mod_datetime),
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
                    str(serialized_obj['name']),
                    str(serialized_obj['name_code']),
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
            'mod_datetime': '2017-01-23 00:00:00.0',
            'name': 'Test Project',
            'name_code': 'TEST',
            'oid': 'TEST',
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
                    dtparser.parse(serialized_obj['create_datetime']),
                    serialized_obj['id'],
                    serialized_obj['id_ns'],
                    dtparser.parse(serialized_obj['mod_datetime']),
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
            if o.__class__.__name__ == 'HardwareProduct':
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
            if o.__class__.__name__ == 'HardwareProduct':
                obj = o
        value = obj.owner
        expected = orb.get('test:yoyodyne')
        self.assertEqual(expected, value)

    def test_18_1_deserialize_object_with_known_owner(self):
        """
        CASE:  test for existence of a parameter
        """
        actual = bool(parameterz['test:iidrive'].get('m'))
        expected = True
        self.assertEqual(expected, actual)

    def test_19_deserialize_new_parameter_values(self):
        """
        CASE:  test pangalactic.core.parametrics.deserialize_parms function.

        Tests parameter deserialization.
        """
        test_oid = 'test:iidrive'
        serialized_parms= {
            'P': 100.0,
            'R_D': 1000000.0,
            'm': 1000.0
            }
        deserialize_parms(test_oid, serialized_parms)
        orb.recompute_parmz()
        expected = [True, True, True, True, True, True,
                    100.0, 1000000.0, 1000.0, 100.0, 1000000.0, 1000.0]
        test_parms = parameterz.get(test_oid, {})
        actual = [('P[CBE]' in test_parms),
                  ('R_D[CBE]' in test_parms),
                  ('m[CBE]' in test_parms),
                  ('P' in test_parms),
                  ('R_D' in test_parms),
                  ('m' in test_parms),
                  get_pval(test_oid, 'P[CBE]'),
                  get_pval(test_oid, 'R_D[CBE]'),
                  get_pval(test_oid, 'm[CBE]'),
                  get_pval(test_oid, 'P'),
                  get_pval(test_oid, 'R_D'),
                  get_pval(test_oid, 'm')]
        self.assertEqual(expected, actual)

    def test_19_0_deserialize_new_data_element_values(self):
        """
        CASE:  test pangalactic.core.parametrics.deserialize_des function.

        Tests data element deserialization.
        """
        test_oid = 'test:iidrive'
        serialized_des= {
            'TRL': 3,
            'Vendor': 'Yoyodyne'
            }
        deserialize_des(test_oid, serialized_des)
        expected = [True, True, 3, 'Yoyodyne']
        test_des = data_elementz.get(test_oid, {})
        actual = [('TRL' in test_des),
                  ('Vendor' in test_des),
                  get_dval(test_oid, 'TRL'),
                  get_dval(test_oid, 'Vendor')]
        self.assertEqual(expected, actual)

    def test_19_1_load_parameters_from_old_format(self):
        """
        CASE:  test pangalactic.core.parametrics.load_parmz function.

        Tests ability of load_parms() to load parameters from a parameters.json
        file in the old format and convert them to the new format.
        """
        parms_path = os.path.join('pangalaxian_test', 'parameters.json')
        parms_bkup_path = os.path.join('pangalaxian_test',
                                       'parameters_backup.json')
        shutil.move(parms_path, parms_bkup_path)  
        shutil.copyfile('parameters_old_test.json', parms_path)  
        load_parmz(orb.home)
        oid1_parmz = parameterz.get('oid1')
        # oid2_parmz = parameterz.get('oid2')
        # oid3_parmz = parameterz.get('oid3')
        expected = [True, True, 0.0, 300.0]
        actual = [("P" in oid1_parmz),
                  ("P[NTE]" in oid1_parmz),
                  (get_pval('oid1', 'P')),
                  (get_pval('oid1', 'P[NTE]'))]
        shutil.move(parms_bkup_path, parms_path)  
        self.assertEqual(expected, actual)

    def test_19_2_load_data_elements_from_old_format(self):
        """
        CASE:  test pangalactic.core.parametrics.load_data_elementz function.

        Tests ability of load_parms() to load parameters from a parameters.json
        file in the old format and convert them to the new format.
        """
        des_path = os.path.join('pangalaxian_test', 'data_elements.json')
        des_bkup_path = os.path.join('pangalaxian_test',
                                     'data_elements_backup.json')
        shutil.move(des_path, des_bkup_path)  
        shutil.copyfile('data_elements_old_test.json', des_path)  
        load_data_elementz(orb.home)
        oid1_dez = data_elementz.get('oid1')
        oid2_dez = data_elementz.get('oid2')
        oid3_dez = data_elementz.get('oid3')
        expected = [True, True, True, 'input', 7, 'Sheldahl']
        actual = [("directionality" in oid1_dez),
                  ("TRL" in oid2_dez),
                  ("Vendor" in oid3_dez),
                  (get_dval('oid1', 'directionality')),
                  (get_dval('oid2', 'TRL')),
                  (get_dval('oid3', 'Vendor'))]
        # shutil.move(des_bkup_path, des_path)  
        self.assertEqual(expected, actual)

    def test_20_deserialize_object_with_simple_parameters(self):
        """
        CASE:  deserialize an object with simple parameters
        """
        f = open('parm_test.yaml')
        data = f.read()
        f.close()
        sobjs = yaml.safe_load(data)
        objs = deserialize(orb, sobjs)
        parameters = sobjs[0]['parameters']
        for o in objs:
            if o.__class__.__name__ == 'HardwareProduct':
                obj = o
        m = get_pval(obj.oid, 'm')
        P = get_pval(obj.oid, 'P')
        R_D = get_pval(obj.oid, 'R_D')
        value = [m, P, R_D]
        expected = [parameters['m'],
                    parameters['P'],
                    parameters['R_D']]
        self.assertEqual(expected, value)

    def test_21_deserialize_related_objects(self):
        """
        CASE:  deserialize a collection of related objects.  Note that this
        also tests the deserializer's refreshing of the requirement allocation
        cache, 'req_allocz', since 'related_test_objects' contains an allocated
        requirement and its allocation, which will be further exercised in
        'test_22_compute_margin' and 'test_23_compute_requirement_margin'.
        """
        objs = deserialize(orb, related_test_objects)
        by_oid = {o.oid : o for o in objs}
        sc_acu_oids = [f'test:spacecraft3-acu-{n}' for n in range(1, 7)]
        value = [
            bool('test:OTHER:Spacecraft-Mass' in req_allocz),
            by_oid['test:OTHER:system-1'].project,
            by_oid['test:OTHER:system-1'].system,
            by_oid['test:spacecraft3'].components,
            by_oid['test:spacecraft3'].has_models,
            by_oid['test:spacecraft3'].owner,
            by_oid['test:spacecraft3.mcad.model.0'].of_thing,
            by_oid['test:spacecraft3.mcad.model.0'].has_representations,
            by_oid['test:spacecraft3.mcad.0.representation'].of_object,
            by_oid['test:spacecraft3.mcad.0.representation'].has_files,
            by_oid['test:spacecraft3.mcad.0.representationfile.0'
                   ].of_representation,
            by_oid['test:spacecraft3.mcad.0.representationfile.0'].url
            ]
        expected = [
            True,
            by_oid['test:OTHER'],
            by_oid['test:spacecraft3'],
            [by_oid[acu_oid] for acu_oid in sc_acu_oids],
            [by_oid['test:spacecraft3.mcad.model.0']],
            by_oid['test:OTHER'],
            by_oid['test:spacecraft3'],
            [by_oid['test:spacecraft3.mcad.0.representation']],
            by_oid['test:spacecraft3.mcad.model.0'],
            [by_oid['test:spacecraft3.mcad.0.representationfile.0']],
            by_oid['test:spacecraft3.mcad.0.representation'],
            'vault://Rocinante_0_MCAD_0_R0_File0.step'
            ]
        self.assertEqual(expected, value)

    def test_22_0_compute_cbe_with_component_vars(self):
        """
        CASE:  compute the mass CBE (Current Best Estimate)
        """
        orb.recompute_parmz()
        value = get_pval('test:spacecraft3', 'm[CBE]')
        sc = orb.get('test:spacecraft3')
        expected  = fsum([get_pval(acu.component.oid, 'm')
                          for acu in sc.components])
        # the Magic Twanger has components Flux Capacitor and Mr. Fusion
        expected -= get_pval('test:twanger', 'm')
        expected += get_pval('test:flux_capacitor', 'm')
        expected += get_pval('test:mr_fusion', 'm')
        # the Thermal System has Thermistors
        expected -= get_pval('test:sc3-thermal-system', 'm')
        expected += get_pval('test:thermistor-0001', 'm') * 1600
        expected += get_pval('test:thermistor-0001', 'm') * 3200
        expected = round_to(expected)
        self.assertEqual(expected, value)

    def test_22_1_compute_cbe_with_component_cbes(self):
        """
        CASE:  compute the mass CBE (Current Best Estimate)
        """
        orb.recompute_parmz()
        value = get_pval('test:spacecraft3', 'm[CBE]')
        sc = orb.get('test:spacecraft3')
        expected  = round_to(fsum([get_pval(acu.component.oid, 'm[CBE]')
                                  for acu in sc.components]))
        self.assertEqual(expected, value)

    def test_22_2_compute_cbe_without_components(self):
        """
        CASE:  compute the mass CBE (Current Best Estimate) of a product whose
        components are not specified (i.e. it does not occur as the "assembly"
        attribute of any Acu).  Its CBE value ('m[CBE]') should be the same as
        its spec value ('m').
        """
        orb.recompute_parmz()
        # NOTE:  get_pval() for a computed parameter will fetch the cached
        # (pre-computed) value from the 'parameterz' cache (rather than
        # computing it)
        value = get_pval('test:iidrive', 'm[CBE]')
        expected = get_pval('test:iidrive', 'm')
        self.assertEqual(expected, value)

    def test_23_compute_mev(self):
        """
        CASE:  compute the mass MEV (Maximum Estimated Value)
        """
        orb.recompute_parmz()
        value = get_pval('test:spacecraft3', 'm[MEV]')
        sc = orb.get('test:spacecraft3')
        expected = round_to(fsum([get_pval(acu.component.oid, 'm[MEV]')
                                  for acu in sc.components]))
        self.assertEqual(expected, value)

    def test_24_compute_margin(self):
        """
        CASE:  compute the mass margin ((NTE - MEV) / MEV) for a node to which
        a performance requirement is allocated
        """
        # compute mass margin at ProjectSystemUsage for spacecraft3
        value = compute_margin('test:OTHER:system-1', 'm')
        mev = get_pval('test:spacecraft3', 'm[MEV]')
        perf_reqt = orb.get('test:OTHER:Spacecraft-Mass')
        nte = perf_reqt.req_maximum_value
        expected = round_to(((nte - mev) / nte))
        self.assertEqual(expected, value)

    def test_25_compute_requirement_margin(self):
        """
        CASE:  compute the margin associated with a performance requirement
        """
        # compute margin for the specified performance requirement
        value = compute_requirement_margin('test:OTHER:Spacecraft-Mass')
        mev = get_pval('test:spacecraft3', 'm[MEV]')
        perf_reqt = orb.get('test:OTHER:Spacecraft-Mass')
        nte = perf_reqt.req_maximum_value
        margin = round_to(((nte - mev) / nte))
        # expected output is (oid of allocated node, parameter id, margin)
        expected = ('test:OTHER:system-1', 'm', nte, perf_reqt.req_units, margin)
        self.assertEqual(expected, value)

    def test_26_role_based_perms(self):
        """
        CASE:  test role-based permissions on project objects
        """
        # Steve has Administrator role on H2G2
        steve = orb.get('test:steve')
        # John Carefulwalker has Lead Engineer role on H2G2
        carefulwalker = orb.get('test:carefulwalker')
        # Zaphod Beeblebrox has Systems Engineer role on H2G2
        zaphod = orb.get('test:zaphod')
        # Buckaroo Banzai has Propulsion Engineer role on H2G2
        buckaroo = orb.get('test:buckaroo')
        sc = orb.get('test:spacecraft0')
        # perms on Assembly Component Usages are based on owner of assembly,
        # which determines the role context, and product type of the component
        acu1 = orb.get('test:H2G2:acu-1')  # SC/Oscillation Overthruster acu
        acu2 = orb.get('test:H2G2:acu-2')  # SC/Infinite Improbability Drive acu
        acu4 = orb.get('test:H2G2:acu-4')  # SC/Bambleweeny Sub-Meson Brain acu
        acu6 = orb.get('test:H2G2:acu-6')  # SC/Instrument0 acu
                                           # carefulwalker is an SE in H2G2
        acu7 = orb.get('test:H2G2:acu-7')  # Instrument0/Mr. Fusion acu **
                                           # NOTE: Yoyodyne owns Instrument0
                                           # carefulwalker not SE in Yoyodyne
        # perms on ProjectSystemUsage are determined by project roles: only the
        # Systems Engineer, Lead Engineer, and Administrator have full perms
        psu = orb.get('test:H2G2:system-1') # Rocinante SC usage on H2G2
        req = orb.get('test:H2G2:Spacecraft-Mass') # Req for SC mass on H2G2
        state["connected"] = False
        # ***************************************************************
        # TODO: test for full perms when offline and object is not synced
        # ***************************************************************
        state["synced_oids"] = ['test:spacecraft0', 'test:H2G2:acu-1',
                                'test:H2G2:acu-2', 'test:H2G2:acu-4',
                                'test:H2G2:acu-6', 'test:H2G2:acu-7',
                                'test:H2G2:system-1',
                                'test:H2G2:Spacecraft-Mass']
        value = [
            set(get_perms(sc, user=steve)),           #  1 Adm/sc:  view only
            set(get_perms(sc, user=carefulwalker)),   #  2 SE/sc:   view only
            set(get_perms(sc, user=zaphod)),          #  3 LE/sc:   view only
            set(get_perms(sc, user=buckaroo)),        #  4 PE/sc:   view only
            set(get_perms(acu1, user=steve)),         #  5 Adm/acu: view only
            set(get_perms(acu1, user=carefulwalker)), #  5a SE/acu: view only
            set(get_perms(acu1, user=buckaroo)),      #  6 PE/acu:  view only
            set(get_perms(acu2, user=buckaroo)),      #  7 PE/acu:  view only
            set(get_perms(acu4, user=buckaroo)),      #  8 PE/acu:  view only
            set(get_perms(acu6, user=carefulwalker)), #  8a SE/acu: view only
            set(get_perms(acu7, user=carefulwalker)), #  8b acu:    view only
            set(get_perms(psu, user=steve)),          #  9 Adm/psu: view only
            set(get_perms(psu, user=carefulwalker)),  # 10 SE/psu:  view only
            set(get_perms(psu, user=zaphod)),         # 11 LE/psu:  view only
            set(get_perms(psu, user=buckaroo)),       # 12 PE/psu:  view only
            set(get_perms(req, user=steve)),          # 13 Adm/req: view only
            set(get_perms(req, user=carefulwalker)),  # 14 SE/req:  view only
            set(get_perms(req, user=zaphod)),         # 15 LE/req:  view only
            set(get_perms(req, user=buckaroo))        # 16 PE/req:  view only
            ]
        state["connected"] = True
        value += [
            set(get_perms(sc, user=steve)),           #  1 Adm/sc:  full perms
            set(get_perms(sc, user=carefulwalker)),   #  2 SE/sc:   full perms
            set(get_perms(sc, user=zaphod)),          #  3 LE/sc:   full perms
            set(get_perms(sc, user=buckaroo)),        #  4 PE/sc:   view only
            set(get_perms(acu1, user=steve)),         #  5 Adm/acu: view only
            set(get_perms(acu1, user=carefulwalker)), #  5a SE/acu: full perms
            set(get_perms(acu1, user=buckaroo)),      #  6 PE/acu:  full perms
            set(get_perms(acu2, user=buckaroo)),      #  7 PE/acu:  full perms
            set(get_perms(acu4, user=buckaroo)),      #  8 PE/acu:  view only
            set(get_perms(acu6, user=carefulwalker)), #  8a SE/acu: full perms
            set(get_perms(acu7, user=carefulwalker)), #  8b acu: view only **
            set(get_perms(psu, user=steve)),          #  9 Adm/psu: full perms
            set(get_perms(psu, user=carefulwalker)),  # 10 SE/psu:  full perms
            set(get_perms(psu, user=zaphod)),         # 11 LE/psu:  full perms
            set(get_perms(psu, user=buckaroo)),       # 12 PE/psu:  view only
            set(get_perms(req, user=steve)),          # 13 Adm/req: full perms
            set(get_perms(req, user=carefulwalker)),  # 14 SE/req:  full perms
            set(get_perms(req, user=zaphod)),         # 15 LE/req:  full perms
            set(get_perms(req, user=buckaroo))        # 16 PE/req:  view only
            ]
        expected = [
            # non-connected state
            set(['view']),                     #  1
            set(['view']),                     #  2
            set(['view']),                     #  3
            set(['view']),                     #  4
            set(['view']),                     #  5
            set(['view']),                     #  5a
            set(['view']),                     #  6
            set(['view']),                     #  7
            set(['view']),                     #  8
            set(['view']),                     #  8a
            set(['view']),                     #  8b
            set(['view']),                     #  9
            set(['view']),                     # 10
            set(['view']),                     # 11
            set(['view']),                     # 12
            set(['view']),                     # 13
            set(['view']),                     # 14
            set(['view']),                     # 15
            set(['view']),                     # 16
            # connected state
            set(['view', 'modify', 'delete']), #  1
            set(['view', 'modify', 'delete']), #  2
            set(['view', 'modify', 'delete']), #  3
            set(['view']),                     #  4
            set(['view', 'modify', 'delete']), #  5
            set(['view', 'modify', 'delete']), #  5a
            set(['view', 'modify', 'delete']), #  6
            set(['view', 'modify', 'delete']), #  7
            set(['view']),                     #  8
            set(['view', 'modify', 'delete']), #  8a
            set(['view']),                     #  8b
            set(['view', 'modify', 'delete']), #  9
            set(['view', 'modify', 'delete']), # 10
            set(['view', 'modify', 'delete']), # 11
            set(['view']),                     # 12
            set(['view', 'modify', 'delete']), # 13
            set(['view', 'modify', 'delete']), # 14
            set(['view', 'modify', 'delete']), # 15
            set(['view'])                      # 16
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

    def test_50_write_mel(self):
        """
        CASE:  test success of mel_writer
        """
        # verify that the `write_mel_xlsx_from_model` function succeeds
        obj = orb.get('H2G2')   # Project 'H2G2' test object
        fpath = os.path.join(orb.vault, 'mel_writer_output.xlsx')
        write_mel_xlsx_from_model(obj, file_path=fpath)
        expected = 1
        value = 1
        self.assertEqual(expected, value)

    # def test_upload_file(self, obj_oid, file_name):
        # pass

    # def test_get_files(self, ...):
        # pass

