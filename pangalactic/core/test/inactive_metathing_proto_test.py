# -*- coding: utf-8 -*-
"""
Prototype testing for "metathing" metaclass
"""
import unittest
from pprint import pformat

# pangalactic
# set "orb" to fastorb instance
import pangalactic.core.set_fastorb

from pangalactic.core.fastorb      import metathing, orb
from pangalactic.core.smerializers import serialize, deserialize
from pangalactic.core.tachistry    import matrix, schemas
from pangalactic.core.test.utils   import (create_test_users,
                                           create_test_project)
                                           # locally_owned_test_objects,
                                           # owned_test_objects,
                                           # related_test_objects)



# registry = Tachistry()
orb.start()
serialized_test_objects = create_test_users()
serialized_test_objects += create_test_project()
deserialize(orb, serialized_test_objects)

# class Project(metaclass=metathing):
    # pass

# thing = Identifiable()
# thing = Identifiable(oid='foo')
# thing = Identifiable(oid='foo', id='spam', name='eggs')
# thing = Project(oid='foo', id='spam', id_ns='test', name='eggs',
                # name_code='SPAM')

if __name__ == '__main__':
    # for name in schemas:
        # schema = schemas[name]['field_names']
        # print(f'* {name} fields are: "{pformat(schema)}"')
    sc = orb.get('test:spacecraft0')
    print(f'* spacecraft is: {sc.name}')
    print(f'  spacecraft _cname is: {sc._cname}')
    inst = orb.get('test:inst1')
    print(f'* instrument is: {inst.name}')
    print(f'  instrument _cname is: {inst._cname}')
    Acu = orb.classes['Acu']
    acu = Acu(id='acu-sc-inst',
              oid='test-acu-sc-inst',
              assembly=sc,
              component=inst,
              reference_designator='Instrument-1',
              product_type_hint=inst.product_type)
    print('* created acu:')
    print(f'  id: {acu.id}')
    print(f'  oid: {acu.oid}')
    print(f'  assembly: {acu.assembly.id}')
    print(f'  component: {acu.component.id}')
    print(f'  ref des: {acu.reference_designator}')
    print(f'  product type hint: {acu.product_type_hint.id}')
    # thing = orb.get('H2G2')
    # res = serialize(orb, [thing])
    # print(f'  - serialize() result is: {res}')
    # objs = deserialize(orb, res)
    # if objs:
        # out = [obj.id for obj in objs]
    # print(f'  - dserialize() result is: {objs}')
    # print('Hi, I am a Identifiable ...')
    # print('Hi, I am a Project ...')
    # print('Hi, I am the H2G2 Project ...')
    # print(f'  - my slots are "{thing.__slots__}"')
    # print(f'  - my dict is "{thing.__dict__}"')
    # field_names = thing.schema['field_names']
    # print(f'  - my fields are "{field_names}"')
    # print(f'  - my oid is "{thing.oid}"')
    # print(f'  - my id is "{thing.id}"')
    # print(f'  - my id_ns is "{thing.id_ns}"')
    # print(f'  - my name is "{thing.name}"')
    # print(f'  - my name_code is "{thing.name_code}"')
    # print('  - my matrix is:')
    # print(f'{pformat(matrix[thing.oid])}')

