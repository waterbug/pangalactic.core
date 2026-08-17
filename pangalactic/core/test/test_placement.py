# -*- coding: utf-8 -*-
"""
Unit tests for the component placement classes -- Axis2Placement3D and
ContextDependentShapeRepresentation -- which position the component of an Acu
within the coordinate frame of that Acu's assembly.

See pangalactic.node/NOTES_ON_STEP_IMPORT.md for the design and its mapping
to STEP.
"""
import random
import unittest

# set the orb
import pangalactic.core.set_uberorb

from pangalactic.core             import orb
from pangalactic.core.access      import get_owner_id, get_perms, is_cloaked
from pangalactic.core.serializers import (DESERIALIZATION_ORDER, deserialize,
                                          serialize)
from pangalactic.core.test.utils  import create_test_users, create_test_project
from pangalactic.core.utils.datetimes import dtstamp

HOME = 'placement_test'
orb.start(home=HOME)
serialized_test_objects = create_test_users()
serialized_test_objects += create_test_project()
deserialize(orb, serialized_test_objects)

NOW = dtstamp()
# an Acu that exists in the test project:  the propulsion subsystem's usage
# within spacecraft0
TEST_ACU_OID = 'test:H2G2:acu-sc0-propsys'
PLACEMENT_OID = 'test:H2G2:placement-sc0-propsys'
CDSR_OID = 'test:H2G2:cdsr-sc0-propsys'

# a placement with a real rotation:  local z along -y, local x along -z, which
# is the orientation OCC reports for the l-bracket in the AS1 test assembly
SERIALIZED_PLACEMENT = [
    dict(_cname='Axis2Placement3D',
         oid=PLACEMENT_OID,
         id='placement-sc0-propsys',
         id_ns='test',
         name='Propulsion Subsystem Placement',
         location_x=0.125, location_y=0.125, location_z=0.08,
         axis_x=0.0, axis_y=-1.0, axis_z=0.0,
         ref_direction_x=0.0, ref_direction_y=0.0, ref_direction_z=-1.0,
         create_datetime=NOW, mod_datetime=NOW),
    dict(_cname='ContextDependentShapeRepresentation',
         oid=CDSR_OID,
         id='cdsr-sc0-propsys',
         id_ns='test',
         name='Propulsion Subsystem Shape Representation',
         represented_usage=TEST_ACU_OID,
         placement=PLACEMENT_OID,
         create_datetime=NOW, mod_datetime=NOW),
    ]


class PlacementTest(unittest.TestCase):
    maxDiff = None

    def test_00_classes_exist(self):
        """
        CASE:  both placement classes were built from the ontology
        """
        expected = [True, True]
        value = ['Axis2Placement3D' in orb.classes,
                 'ContextDependentShapeRepresentation' in orb.classes]
        self.assertEqual(expected, value)

    def test_01_placement_has_geometry_fields(self):
        """
        CASE:  Axis2Placement3D has the location, axis and ref_direction
        components of a STEP axis2_placement_3d
        """
        expected = ['axis_x', 'axis_y', 'axis_z',
                    'location_x', 'location_y', 'location_z',
                    'ref_direction_x', 'ref_direction_y', 'ref_direction_z']
        fields = orb.schemas['Axis2Placement3D']['field_names']
        value = sorted([f for f in fields
                        if f.startswith(('location_', 'axis_',
                                         'ref_direction_'))])
        self.assertEqual(expected, value)

    def test_02_cdsr_relates_usage_to_placement(self):
        """
        CASE:  ContextDependentShapeRepresentation points at an Acu and at an
        Axis2Placement3D
        """
        fields = orb.schemas['ContextDependentShapeRepresentation']['fields']
        expected = ['Acu', 'Axis2Placement3D']
        value = [fields['represented_usage']['related_cname'],
                 fields['placement']['related_cname']]
        self.assertEqual(expected, value)

    def test_03_acu_has_inverse_attribute(self):
        """
        CASE:  an Acu can be navigated to its shape representations
        """
        expected = True
        value = ('shape_representations' in
                 orb.schemas['Acu']['field_names'])
        self.assertEqual(expected, value)

    def test_04_deserialization_order(self):
        """
        CASE:  ContextDependentShapeRepresentation is deserialized after both
        of the classes it references.

        Without this the objects fall into the unordered "other" bucket and a
        representation can be deserialized before the placement it points at,
        which is a foreign key violation that depends on dict ordering -- i.e.
        an intermittent failure.
        """
        order = DESERIALIZATION_ORDER
        expected = [True, True]
        value = [order.index('ContextDependentShapeRepresentation') >
                 order.index('Acu'),
                 order.index('ContextDependentShapeRepresentation') >
                 order.index('Axis2Placement3D')]
        self.assertEqual(expected, value)

    def test_05_deserialize_in_any_order(self):
        """
        CASE:  a placement and its representation deserialize correctly no
        matter what order they arrive in
        """
        results = []
        for _ in range(5):
            sos = SERIALIZED_PLACEMENT[:]
            random.shuffle(sos)
            deserialize(orb, sos)
            cdsr = orb.get(CDSR_OID)
            results.append(cdsr is not None and
                           cdsr.placement is not None and
                           cdsr.placement.oid == PLACEMENT_OID)
        expected = [True] * 5
        self.assertEqual(expected, results)

    def test_06_placement_values_survive_the_round_trip(self):
        """
        CASE:  the location and both directions come back as they went in
        """
        deserialize(orb, SERIALIZED_PLACEMENT)
        p = orb.get(PLACEMENT_OID)
        expected = [0.125, 0.125, 0.08,
                    0.0, -1.0, 0.0,
                    0.0, 0.0, -1.0]
        value = [p.location_x, p.location_y, p.location_z,
                 p.axis_x, p.axis_y, p.axis_z,
                 p.ref_direction_x, p.ref_direction_y, p.ref_direction_z]
        self.assertEqual(expected, value)

    def test_07_representation_points_at_its_usage(self):
        """
        CASE:  the representation resolves to the Acu it positions
        """
        deserialize(orb, SERIALIZED_PLACEMENT)
        cdsr = orb.get(CDSR_OID)
        expected = TEST_ACU_OID
        value = cdsr.represented_usage.oid
        self.assertEqual(expected, value)

    def test_08_usage_navigates_to_its_representations(self):
        """
        CASE:  the inverse attribute finds the representation from the Acu
        """
        deserialize(orb, SERIALIZED_PLACEMENT)
        acu = orb.get(TEST_ACU_OID)
        expected = [CDSR_OID]
        value = [c.oid for c in acu.shape_representations]
        self.assertEqual(expected, value)

    def test_09_serialize_round_trip(self):
        """
        CASE:  serializing the representation emits its usage and placement as
        oid references
        """
        deserialize(orb, SERIALIZED_PLACEMENT)
        cdsr = orb.get(CDSR_OID)
        so = serialize(orb, [cdsr])[0]
        expected = ['ContextDependentShapeRepresentation', TEST_ACU_OID,
                    PLACEMENT_OID]
        value = [so['_cname'], so['represented_usage'], so['placement']]
        self.assertEqual(expected, value)

    def test_10_placements_are_universally_modifiable(self):
        """
        CASE:  placements are modifiable by any user, like the other objects
        that exist only in association with a parent object.

        They are reachable only by way of an Acu, so the permissions that
        matter are the ones on the assembly.
        """
        deserialize(orb, SERIALIZED_PLACEMENT)
        user = orb.get('test:zaphod')
        expected = [True, True]
        value = ['modify' in get_perms(orb.get(PLACEMENT_OID), user=user),
                 'modify' in get_perms(orb.get(CDSR_OID), user=user)]
        self.assertEqual(expected, value)


    def test_11_placement_navigates_back_to_its_representation(self):
        """
        CASE:  the inverse of "placement" finds the representation, which is
        what makes a placement's assembly -- and therefore its project --
        reachable
        """
        deserialize(orb, SERIALIZED_PLACEMENT)
        p = orb.get(PLACEMENT_OID)
        expected = [CDSR_OID]
        value = [c.oid for c in p.placement_of]
        self.assertEqual(expected, value)

    def test_12_owner_resolves_through_the_usage(self):
        """
        CASE:  both placement classes resolve to the project that owns the
        assembly.

        vger publishes an object's "new"/"modified" notification on the
        project channel named by this id, so a class that resolves to '' syncs
        only on the next full sync rather than in real time.
        """
        deserialize(orb, SERIALIZED_PLACEMENT)
        acu = orb.get(TEST_ACU_OID)
        expected_owner = get_owner_id(acu)
        expected = [expected_owner, expected_owner]
        value = [get_owner_id(orb.get(CDSR_OID)),
                 get_owner_id(orb.get(PLACEMENT_OID))]
        self.assertEqual(expected, value)
        # and the assembly's owner really is a project, not ''
        self.assertNotEqual('', expected_owner)

    def test_13_cloaking_follows_the_assembly(self):
        """
        CASE:  a placement is cloaked exactly when the assembly it positions
        is cloaked -- the geometry of a proprietary design is as proprietary
        as the design.
        """
        deserialize(orb, SERIALIZED_PLACEMENT)
        acu = orb.get(TEST_ACU_OID)
        cdsr = orb.get(CDSR_OID)
        placement = orb.get(PLACEMENT_OID)
        assembly = acu.assembly
        was_public = assembly.public
        results = []
        try:
            for public in (True, False):
                assembly.public = public
                results.append((is_cloaked(acu), is_cloaked(cdsr),
                                is_cloaked(placement)))
        finally:
            assembly.public = was_public
        # whatever the assembly's cloaking is, all three agree
        expected = [(False, False, False), (True, True, True)]
        self.assertEqual(expected, results)


if __name__ == '__main__':
    unittest.main()
