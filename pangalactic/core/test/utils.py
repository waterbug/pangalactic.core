# -*- coding: utf-8 -*-
"""
Create PGEF test data.
"""
from copy import deepcopy
import random
from pangalactic.core.parametrics import de_defz, parm_defz, round_to
from pangalactic.core.names       import (get_port_id, get_port_name,
                                          get_port_abbr)
from pangalactic.core.utils.datetimes import dtstamp

NOW = str(dtstamp())

def gen_test_dvals(data_elements):
    """
    Generate random values for a set of data elements.

    Args:
        data_elements (dict):  data elements dict of the form

            {data element id: value, ...}

            where the standard data element dict is defined in
            p.core.parametrics and is the value of data_elementz[obj.oid] for
            any object that has data elements.
    """
    for deid in data_elements:
        # get the cached data element definition
        de_def = de_defz.get(deid) or {}
        if de_def.get('range_datatype') in ['text', 'str']:
            # make sure no non-null default has been set
            if not data_elements[deid]:
                i = random.randint(0, 1)
                j = random.randint(0, 1)
                k = random.randint(0, 1)
                data_elements[deid] = i * 'Spam' + j * 'Eggs' + k * 'Spam'
        elif de_def.get('range_datatype') == 'int':
            # make sure no non-zero default has been set
            if not data_elements[deid]:
                data_elements[deid] = random.randint(1, 10)
        elif de_def.get('range_datatype') == 'float':
            if not data_elements[deid]:
                data_elements[deid] = float(random.randint(1, 1000))

def gen_test_pvals(parms):
    """
    Generate random values for the non-computed float and int types in a set of
    Parameters.

    Args:
        parms (dict):  parameters dict of the form

            {parameter id: value, ...}

            where the standard parameter dict is defined in p.core.parametrics
            and is the value of parameterz[obj.oid] for any object that has
            parameters.
    """
    for pid in parms:
        pdz = parm_defz.get(pid) or {}
        if pdz.get('computed'):
            # ignore computed parameters
            continue
        if '[Ctgcy]' in pid:
            # assign a random contingency of 10%, 20%, or 30%
            x = random.randint(1, 3)
            parms[pid] = round_to(x * 0.10, n=3)
        elif pdz.get('range_datatype') == 'float':
            if not parms[pid]:
                parms[pid] = float(random.randint(1, 1000))
        # special cases for Data Rate parameters (bigger)
        elif pdz.get('variable') == 'R_D':
            parms[pid] = float(random.randint(10000, 100000))
        elif pdz.get('range_datatype') == 'int':
            # make sure no non-zero default has been set
            if not parms[pid]:
                parms[pid] = random.randint(1, 10)

def create_test_users():
    """
    Return a list of standard test users as serialized Person objects.
    """
    return [
        dict(
             _cname='Organization', oid='test:yoyodyne', id='YOYODYNE',
             id_ns='pangalactic', name='Yoyodyne Propulsion Systems',
             name_code='YPS', city='Grovers Mill',
             state_or_province='NJ', owner='pgefobjects:PGANA'),
        dict(
             _cname='Organization', oid='test:banzai', id='BANZAI',
             id_ns='pangalactic', owner='pgefobjects:PGANA',
             name='Banzai Aerospace', name_code='BA',
             city='White Sands', state_or_province='NM'),
        dict(
            _cname='Person',
            oid='test:steve', id='steve',
            id_ns='pangalactic', name='Steve Waterbury',
            email='waterbug@pangalactic.us', first_name='Stephen',
            mi_or_name='C', last_name='Waterbury',
            org='test:banzai', owner='pgefobjects:PGANA'),
        dict(
            _cname='Person',
            oid='test:zaphod', id='zaphod', owner='pgefobjects:PGANA',
            id_ns='pangalactic', name='Zaphod Z. Beeblebrox',
            org='test:banzai', create_datetime=NOW, mod_datetime=NOW,
            email='zaphod@space.univ', first_name='Zaphod',
            mi_or_name='Z', last_name='Beeblebrox',
            phone='1-800-ZAPHOD'),
        dict(
            _cname='Person',
            oid='test:buckaroo', id='buckaroo', owner='pgefobjects:PGANA',
            id_ns='pangalactic', name='Buckaroo Banzai',
            org='test:banzai', create_datetime=NOW, mod_datetime=NOW,
            email='buckaroo@banzai.earth.milkyway.univ',
            first_name='Buckaroo', mi_or_name='', last_name='Banzai',
            phone='1-800-BANZAI'),
        dict(
            _cname='Person',
            oid='test:whorfin', id='whorfin', owner='pgefobjects:PGANA',
            id_ns='pangalactic', name='John Whorfin (Dr. Emilio Lizardo)',
            org='test:yoyodyne', create_datetime=NOW, mod_datetime=NOW,
            email='whorfin@redlectroids.planet10.univ',
            first_name='John', mi_or_name='', last_name='Whorfin',
            phone='1-Z00-WHORFIN'),
        dict(
            _cname='Person',
            oid='test:bigboote', id='bigboote', owner='pgefobjects:PGANA',
            id_ns='pangalactic', name='John Bigboote',
            org='test:yoyodyne', create_datetime=NOW, mod_datetime=NOW,
            email='bigboote@redlectroids.planet10.univ',
            first_name='John', mi_or_name='', last_name='Bigboote',
            phone='1-Z00-BIGBOOT'),
        dict(
            _cname='Person',
            oid='test:smallberries', id='smallberries',
            id_ns='pangalactic', name='John Smallberries',
            org='test:yoyodyne', create_datetime=NOW, mod_datetime=NOW,
            email='smallberries@redlectroids.planet10.univ',
            first_name='John', mi_or_name='', last_name='Smallberries',
            phone='1-Z00-SMALLBE', owner='pgefobjects:PGANA'),
        dict(
            _cname='Person',
            oid='test:thornystick', id='thornystick',
            id_ns='pangalactic', name='John Thornystick',
            org='test:yoyodyne', create_datetime=NOW, mod_datetime=NOW,
            email='thornystick@redlectroids.planet10.univ',
            first_name='John', mi_or_name='', last_name='Thornystick',
            phone='1-Z00-THORNYS', owner='pgefobjects:PGANA'),
        dict(
            _cname='Person',
            oid='test:carefulwalker', id='carefulwalker',
            id_ns='pangalactic', name='John Carefulwalker',
            org='test:yoyodyne', create_datetime=NOW, mod_datetime=NOW,
            email='carefulwalker@redlectroids.planet10.univ',
            first_name='John', mi_or_name='', last_name='Carefulwalker',
            phone='1-Z00-CAREFUL', owner='pgefobjects:PGANA'),
        dict(
            _cname='Person',
            oid='test:manyjars', id='manyjars',
            id_ns='pangalactic', name='John Manyjars',
            org='test:yoyodyne', create_datetime=NOW, mod_datetime=NOW,
            email='manyjars@redlectroids.planet10.univ',
            first_name='John', mi_or_name='', last_name='Manyjars',
            phone='1-Z00-MANYJAR', owner='pgefobjects:PGANA'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.steve_admin',
            id='steve_admin',
            id_ns='test',
            assigned_role='pgefobjects:Role.Administrator',
            assigned_to='test:steve')
            ]

def create_test_project():
    """
    Return a set of objects in a serialized test project, H2G2.

    NOTE:  if this project is loaded in the client, all of its objects will be
    deleted when the user logs in (since they are all created by other [test]
    users) unless the user logs in as one of the test users.
    """
    test_project = [
        dict(
            _cname='Project', oid='H2G2', id='H2G2',
            id_ns='test', owner='pgefobjects:PGANA',
            creator='test:steve', modifier='test:steve',
            create_datetime=NOW, mod_datetime=NOW,
            name='Hitchhikers Guide to the Galaxy',
            name_code='H2G2'),
        dict(
            _cname='Mission', oid='test:Mission.H2G2',
            id='h2g2_mission', id_ns='test',
            creator='test:steve', modifier='test:steve',
            create_datetime=NOW, mod_datetime=NOW,
            name='Hitchhike the Galaxy'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.zaphod_se',
            id='zaphod_se',
            id_ns='test',
            assigned_role='gsfc:Role.systems_engineer',
            assigned_to='test:zaphod',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.carefulwalker_le',
            id='carefulwalker_le',
            id_ns='test',
            assigned_role='gsfc:Role.lead_engineer',
            assigned_to='test:carefulwalker',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.steve_h2g2_admin',
            id='steve_h2g2_admin',
            id_ns='test',
            assigned_role='pgefobjects:Role.Administrator',
            assigned_to='test:steve',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.buckaroo_propulsion',
            id='buckaroo_propulsion',
            id_ns='test',
            assigned_role='gsfc:Role.propulsion_engineer',
            assigned_to='test:buckaroo',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.whorfin_propulsion',
            id='whorfin_propulsion',
            id_ns='test',
            assigned_role='gsfc:Role.propulsion_engineer',
            assigned_to='test:whorfin',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.bigboote_acs',
            id='bigboote_acs',
            assigned_role='gsfc:Role.acs_engineer',
            assigned_to='test:bigboote',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.smallberries_thermal',
            id='smallberries_thermal',
            assigned_role='gsfc:Role.thermal_engineer',
            assigned_to='test:smallberries',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.thornystick_mechanical',
            id='thornystick_mechanical',
            assigned_role='gsfc:Role.mechanical_engineer',
            assigned_to='test:thornystick',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            creator='pgefobjects:admin', modifier='pgefobjects:admin',
            create_datetime=NOW, mod_datetime=NOW,
            oid='test:RA.manyjars_power',
            id='manyjars_power',
            assigned_role='gsfc:Role.power_engineer',
            assigned_to='test:manyjars',
            role_assignment_context='H2G2'),
        dict(
            _cname='HardwareProduct',
            oid='test:spacecraft0',
            id='Rocinante',
            id_ns='test',
            product_type='pgefobjects:ProductType.spacecraft',
            owner='H2G2',
            name='Rocinante Spacecraft',
            description='A Martian Navy gunship',
            data_elements=deepcopy(test_data_elements),
            parameters=deepcopy(test_parms),
            comment='Prototype',
            public=True,
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW,
            iteration=0,
            version='0',
            version_sequence=0),
        dict(
            _cname='HardwareProduct',
            oid='test:spacecraft1',
            id='Rocinante',
            id_ns='test',
            product_type='pgefobjects:ProductType.spacecraft',
            owner='H2G2',
            name='Rocinante Spacecraft',
            description='A Martian Navy gunship',
            data_elements=deepcopy(test_data_elements),
            parameters=deepcopy(test_parms),
            comment='Prototype',
            public=True,
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW,
            iteration=0,
            version='1',
            version_sequence=1),
        dict(
            _cname='HardwareProduct',
            oid='test:spacecraft2',
            id='Rocinante',
            id_ns='test',
            product_type='pgefobjects:ProductType.spacecraft',
            version='2',
            iteration=0,
            version_sequence=2,
            frozen=True,
            owner='H2G2',
            name='Rocinante Spacecraft',
            description='A Martian Navy gunship',
            data_elements=deepcopy(test_data_elements),
            parameters=deepcopy(test_parms),
            comment='Prototype',
            public=True,
            creator='test:zaphod',
            create_datetime=NOW,
            modifier='test:zaphod',
            mod_datetime=NOW
            ),
        dict(
            _cname='HardwareProduct',
            oid='test:inst0',
            id='Inst-v0',
            id_ns='test',
            product_type='pgefobjects:ProductType.instrument',
            owner='test:yoyodyne',
            name='Instrument, v.0',
            description='Instrument, Advanced',
            data_elements=deepcopy(test_data_elements),
            parameters={
                "Cost" : 1000000.0,
                "P" : 100.0,
                "P[CBE]" : 0.0,
                "P[MEV]" : 0.0,
                "R_D" : 0.0,
                "R_D[CBE]" : 0.0,
                "R_D[MEV]" : 0.0,
                "depth" : 0.0,
                "height" : 0.0,
                "width" : 0.0,
                "m" : 0.0,
                "m[CBE]" : 0.0,
                "m[MEV]" : 0.0,
                "P[Ctgcy]" : 0.3,
                "m[Ctgcy]" : 0.3,
                "R_D[Ctgcy]" : 0.3
                },
            comment='This instrument is quite advanced.',
            public=True,
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW,
            iteration=0,
            version='0',
            version_sequence=0),
        dict(
            _cname='HardwareProduct',
            oid='test:inst1',
            id='Inst-v1',
            id_ns='test',
            product_type='pgefobjects:ProductType.instrument',
            owner='test:yoyodyne',
            name='Instrument v.1',
            description='Instrument, Advanced',
            data_elements=deepcopy(test_data_elements),
            parameters=deepcopy(test_parms),
            comment='This instrument is quite advanced.',
            public=True,
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW,
            iteration=1,
            version='1',
            version_sequence=1),
        dict(
            _cname='HardwareProduct',
            oid='test:twanger',
            id='GMT',
            id_ns='test',
            product_type='pgefobjects:ProductType.communications_system',
            owner='test:yoyodyne',
            name='Gigawatt Magic Twanger',
            description='Twanger, Magic, Heavy-Duty',
            data_elements=deepcopy(test_data_elements),
            parameters={
                "Cost" : 10.0,
                "P" : 50.0,
                "P[CBE]" : 0.0,
                "P[MEV]" : 0.0,
                "R_D" : 0.0,
                "R_D[CBE]" : 0.0,
                "R_D[MEV]" : 0.0,
                "depth" : 0.0,
                "height" : 0.0,
                "width" : 0.0,
                "m" : 0.0,
                "m[CBE]" : 0.0,
                "m[MEV]" : 0.0,
                "P[Ctgcy]" : 0.3,
                "m[Ctgcy]" : 0.3,
                "R_D[Ctgcy]" : 0.3
                },
            comment='Prototype Plasma-Drive Magic Twanger',
            public=True,
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='HardwareProduct',
            oid='test:photon_drive',
            id='PDrive',
            id_ns='test',
            product_type='pgefobjects:ProductType.propulsion_system',
            owner='test:yoyodyne',
            name='Photon Drive v1',
            description='Photon Drive, v1',
            data_elements=deepcopy(test_data_elements),
            parameters={
                "Cost" : 100.0,
                "P" : 30.0,
                "P[CBE]" : 30.0,
                "P[MEV]" : 39.0,
                "R_D" : 0.0,
                "R_D[CBE]" : 0.0,
                "R_D[MEV]" : 0.0,
                "depth" : 0.0,
                "height" : 0.0,
                "width" : 0.0,
                "m" : 0.0,
                "m[CBE]" : 0.0,
                "m[MEV]" : 0.0,
                "P[Ctgcy]" : 0.3,
                "m[Ctgcy]" : 0.3,
                "R_D[Ctgcy]" : 0.3
                },
            comment='Propagate! Propagate!',
            public=True,
            creator='test:zaphod',
            create_datetime=NOW,
            modifier='test:zaphod',
            mod_datetime=NOW
            ),
        dict(
            _cname='HardwareProduct',
            oid='test:iidrive',
            id='IIDrive',
            id_ns='test',
            product_type='pgefobjects:ProductType.propulsion_system',
            owner='test:yoyodyne',
            name='Infinite Improbability Drive',
            description='Infinite Improbability Drive',
            data_elements=deepcopy(test_data_elements),
            parameters={
                "Cost" : 1000.0,
                "P" : 300.0,
                "P[CBE]" : 300.0,
                "P[MEV]" : 390.0,
                "R_D" : 0.0,
                "R_D[CBE]" : 0.0,
                "R_D[MEV]" : 0.0,
                "depth" : 0.0,
                "height" : 0.0,
                "width" : 0.0,
                "m" : 0.0,
                "m[CBE]" : 0.0,
                "m[MEV]" : 0.0,
                "P[Ctgcy]" : 0.3,
                "m[Ctgcy]" : 0.3,
                "R_D[Ctgcy]" : 0.3
                },
            comment='VROOM! VROOM!',
            public=True,
            creator='test:zaphod',
            create_datetime=NOW,
            modifier='test:zaphod',
            mod_datetime=NOW
            ),
        dict(
            _cname='HardwareProduct',
            oid='test:computer',
            id='B52SMB',
            id_ns='test',
            product_type='pgefobjects:ProductType.computer',
            owner='test:yoyodyne',
            name='Bambleweeny 52 Sub-Meson Brain',
            description='Computer, Hyper-Quantum, Subfemto',
            data_elements=deepcopy(test_data_elements),
            parameters={
                "Cost" : 10000.0,
                "P" : 3.0,
                "P[CBE]" : 3.0,
                "P[MEV]" : 3.9,
                "R_D" : 0.0,
                "R_D[CBE]" : 0.0,
                "R_D[MEV]" : 0.0,
                "depth" : 0.0,
                "height" : 0.0,
                "width" : 0.0,
                "m" : 0.0,
                "m[CBE]" : 0.0,
                "m[MEV]" : 0.0,
                "P[Ctgcy]" : 0.3,
                "m[Ctgcy]" : 0.3,
                "R_D[Ctgcy]" : 0.3
                },
            comment='Ridiculously powerful microscopic computer',
            public=True,
            creator='test:zaphod',
            create_datetime=NOW,
            modifier='test:zaphod',
            mod_datetime=NOW
            ),
        dict(
            _cname='HardwareProduct',
            oid='test:flux_capacitor',
            id='FX-CAP-1.21',
            id_ns='test',
            product_type='pgefobjects:ProductType.power_system',
            owner='test:yoyodyne',
            name='Flux Capacitor, 1.21 GW',
            description='Capacitor, Flux, 1.21 GW',
            data_elements=deepcopy(test_data_elements),
            parameters={
                "Cost" : 100000.0,
                "P" : 4.0,
                "P[CBE]" : 4.0,
                "P[MEV]" : 5.2,
                "R_D" : 0.0,
                "R_D[CBE]" : 0.0,
                "R_D[MEV]" : 0.0,
                "depth" : 0.0,
                "height" : 0.0,
                "width" : 0.0,
                "m" : 0.0,
                "m[CBE]" : 0.0,
                "m[MEV]" : 0.0,
                "P[Ctgcy]" : 0.3,
                "m[Ctgcy]" : 0.3,
                "R_D[Ctgcy]" : 0.3
                },
            comment='Quantum Chromolytic Flux Capacitor',
            public=True,
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='HardwareProduct',
            oid='test:mr_fusion',
            id='MF-A',
            id_ns='test',
            product_type='pgefobjects:ProductType.power_system',
            owner='test:yoyodyne',
            name='Mr. Fusion',
            description='Power Generator, Fusion, Blender-Style',
            data_elements=deepcopy(test_data_elements),
            parameters={
                "Cost" : 50.0,
                "P" : 15.0,
                "P[CBE]" : 15.0,
                "P[MEV]" : 19.5,
                "R_D" : 0.0,
                "R_D[CBE]" : 0.0,
                "R_D[MEV]" : 0.0,
                "depth" : 0.0,
                "height" : 0.0,
                "width" : 0.0,
                "m" : 0.0,
                "m[CBE]" : 0.0,
                "m[MEV]" : 0.0,
                "P[Ctgcy]" : 0.3,
                "m[Ctgcy]" : 0.3,
                "R_D[Ctgcy]" : 0.3
                },
            comment='Fuels: banana peels, orange rinds, coffee grounds',
            public=True,
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='HardwareProduct',
            oid='test:overthruster',
            id='OO',
            id_ns='test',
            product_type='pgefobjects:ProductType.propulsion_system',
            owner='test:banzai',
            name='Oscillation Overthruster',
            description='Overthruster, Oscillation',
            data_elements=deepcopy(test_data_elements),
            parameters={
                "Cost" : 500.0,
                "P" : 25.0,
                "P[CBE]" : 25.0,
                "P[MEV]" : 32.5,
                "R_D" : 0.0,
                "R_D[CBE]" : 0.0,
                "R_D[MEV]" : 0.0,
                "depth" : 0.0,
                "height" : 0.0,
                "width" : 0.0,
                "m" : 0.0,
                "m[CBE]" : 0.0,
                "m[MEV]" : 0.0,
                "P[Ctgcy]" : 0.3,
                "m[Ctgcy]" : 0.3,
                "R_D[Ctgcy]" : 0.3
                },
            comment='Extreme overthrust levels are untested',
            public=True,
            creator='test:buckaroo',
            create_datetime=NOW,
            modifier='test:buckaroo',
            mod_datetime=NOW
            ),
        dict(
            _cname='HardwareProduct',
            oid='test:overthruster_b',
            id='OO-B',
            id_ns='test',
            product_type='pgefobjects:ProductType.propulsion_system',
            owner='test:yoyodyne',
            name='Oscillation Overthruster B',
            description='Overthruster, Oscillation (B Movie)',
            data_elements=deepcopy(test_data_elements),
            parameters=deepcopy(test_parms),
            comment='DO NOT USE THIS PART -- EXPLOSION RISK!',
            public=True,
            creator='test:whorfin',
            create_datetime=NOW,
            modifier='test:whorfin',
            mod_datetime=NOW
            ),
        dict(
            _cname='HardwareProduct',
            oid='test:esm0',
            id='ESM',
            id_ns='test',
            product_type='pgefobjects:ProductType.propulsion_system',
            owner='test:yoyodyne',
            name='Illudium Q-36 Explosive Space Modulator',
            description='Space Modulator, Explosive, Illudium',
            data_elements=deepcopy(test_data_elements),
            parameters=deepcopy(test_parms),
            comment='Capable of clearing obstructed view of Venus.',
            public=True,
            creator='test:whorfin',
            create_datetime=NOW,
            modifier='test:whorfin',
            mod_datetime=NOW
            ),
        dict(
            _cname='Port',
            oid='test:port.twanger.0',
            id=get_port_id('GMT', 'electrical_power', 0),
            id_ns='test',
            abbreviation=get_port_abbr('Power', 0),
            data_elements={'directionality': 'input'},
            owner='test:yoyodyne',
            name=get_port_name('Gigawatt Magic Twanger', 'Electrical Power',
                               0),
            of_product='test:twanger',
            parameters={'V': 28.0},
            type_of_port='pgefobjects:PortType.electrical_power',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Port',
            oid='test:port.overthruster.0',
            id=get_port_id('OO', 'electrical_power', 0),
            id_ns='test',
            abbreviation=get_port_abbr('Power', 0),
            owner='test:banzai',
            name=get_port_name('Oscillation Overthruster', 'Electrical Power',
                               0),
            of_product='test:overthruster',
            type_of_port='pgefobjects:PortType.electrical_power',
            creator='test:buckaroo',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Port',
            oid='test:port.iidrive.0',
            id=get_port_id('IIDrive', 'electrical_power', 0),
            id_ns='test',
            abbreviation=get_port_abbr('Power', 0),
            owner='test:yoyodyne',
            name=get_port_name('Infinite Improbability Drive',
                               'Electrical Power', 0),
            of_product='test:iidrive',
            type_of_port='pgefobjects:PortType.electrical_power',
            creator='test:zaphod',
            create_datetime=NOW,
            modifier='test:zaphod',
            mod_datetime=NOW
            ),
        dict(
            # using a CAX-IF STEP model for test purposes
            _cname='Model',
            oid='test:Rocinante.0.MCAD.Model.0',
            id='Rocinante.0.MCAD.Model',
            id_ns='test',
            iteration=0,
            version='0',
            version_sequence=0,
            owner='H2G2',
            name='MCAD Model of Rocinante Spacecraft',
            of_thing='test:spacecraft0',
            model_definition_context='gsfc:Discipline.mechanical',
            type_of_model='step:203',
            description='MCAD Model, v0, of Rocinante Spacecraft, v0',
            public=True,
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Representation',
            oid='test:Rocinante.0.MCAD.0.Representation',
            id='Rocinante.0.MCAD.0.Representation',
            id_ns='test',
            name='Rocinante v0 MCAD v0 Representation',
            description='Rocinante v0 MCAD v0 Representation',
            of_object='test:Rocinante.0.MCAD.Model.0',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='RepresentationFile',
            oid='test:Rocinante.0.MCAD.0.RepresentationFile.0',
            id='Rocinante.0.MCAD.0.RepresentationFile.0',
            id_ns='test',
            name='Rocinante v0 MCAD v0 Representation File 0',
            description='Rocinante v0 MCAD v0 Representation File 0',
            of_representation='test:Rocinante.0.MCAD.0.Representation',
            mime_type='application/step',
            url='vault://Rocinante_0_MCAD_0_R0_File0.step',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW),
        dict(
            _cname='ProjectSystemUsage',
            oid='test:H2G2:system-1',
            id='system-1',
            id_ns='test',
            name='H2G2 Rocinante Spacecraft',
            project='H2G2',
            system='test:spacecraft0',
            system_role='Spacecraft',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Acu',
            oid='test:H2G2:acu-1',
            id='acu-1',
            id_ns='test',
            name='Oscillation Overthruster Component Usage',
            assembly='test:spacecraft0',
            component='test:overthruster',
            reference_designator='Prop-1',
            product_type_hint='pgefobjects:ProductType.propulsion_system',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Acu',
            oid='test:H2G2:acu-2',
            id='acu-2',
            id_ns='test',
            name='Infinite Improbability Drive in Rocinante Spacecraft',
            assembly='test:spacecraft0',
            component='test:iidrive',
            reference_designator='Prop-2',
            product_type_hint='pgefobjects:ProductType.propulsion_system',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Acu',
            oid='test:H2G2:acu-3',
            id='acu-3',
            id_ns='test',
            name='Photon Drive in Rocinante Spacecraft',
            assembly='test:spacecraft0',
            component='test:photon_drive',
            reference_designator='Prop-3',
            product_type_hint='pgefobjects:ProductType.propulsion_system',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Acu',
            oid='test:H2G2:acu-4',
            id='acu-4',
            id_ns='test',
            name='Bambleweeny Sub-Meson Brain in Rocinante Spacecraft',
            assembly='test:spacecraft0',
            component='test:computer',
            reference_designator='Comp-1',
            product_type_hint='pgefobjects:ProductType.computer',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Acu',
            oid='test:H2G2:acu-5',
            id='acu-5',
            id_ns='test',
            name='Magic Twanger in Rocinante Spacecraft',
            assembly='test:spacecraft0',
            component='test:twanger',
            reference_designator='Comm-1',
            product_type_hint='pgefobjects:ProductType.spacecraft',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Acu',
            oid='test:H2G2:acu-6',
            id='acu-6',
            id_ns='test',
            name='Instrument 0 in Rocinante Spacecraft',
            assembly='test:spacecraft0',
            component='test:inst0',
            reference_designator='Inst-1',
            product_type_hint='pgefobjects:ProductType.instrument',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Acu',
            oid='test:H2G2:acu-7',
            id='acu-7',
            id_ns='test',
            name='Mr. Fusion in Instrument 0',
            assembly='test:inst0',
            component='test:mr_fusion',
            reference_designator='Power-1',
            product_type_hint='pgefobjects:ProductType.instrument',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Acu',
            oid='test:BOZO:acu-1',
            id='acu-5',
            id_ns='test',
            name='Flux Capacitor in Magic Twanger',
            assembly='test:twanger',
            component='test:flux_capacitor',
            reference_designator='Power-1',
            product_type_hint='pgefobjects:ProductType.power_system',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Acu',
            oid='test:BOZO:acu-2',
            id='acu-6',
            id_ns='test',
            name='Fusion energy source in Magic Twanger',
            assembly='test:twanger',
            component='test:mr_fusion',
            reference_designator='Power-2',
            product_type_hint='pgefobjects:ProductType.power_system',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='ParameterRelation',
            oid='test:H2G2:Spacecraft-Mass-Computable-Form-PR',
            id='H2G2.1.0.SC-Mass-ParmRel',
            id_ns='test',
            name='H2G2 1.0 Spacecraft Mass Computable Form',
            referenced_relation='test:H2G2:Spacecraft-Mass-Computable-Form',
            correlates_parameter='pgef:ParameterDefinition.m',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Relation',
            oid='test:H2G2:Spacecraft-Mass-Computable-Form',
            id='H2G2.1.0.SC-Mass-Comp-Form',
            id_ns='test',
            name='H2G2 1.0 Spacecraft Mass Computable Form',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            ),
        dict(
            _cname='Requirement',
            oid='test:H2G2:Spacecraft-Mass',
            id='H2G2.1.0.Spacecraft-Mass',
            id_ns='test',
            name='H2G2 1.0 Spacecraft Mass',
            owner='H2G2',
            allocated_to='test:H2G2:system-1',
            req_type='performance',
            req_constraint_type='maximum',
            req_maximum_value=5000.0,
            req_units='kg',
            computable_form='test:H2G2:Spacecraft-Mass-Computable-Form',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            )
        ]
    return test_project

owned_test_objects = [
    dict(
         _cname='Organization', oid='test:yoyoinst', id='YOYOINST',
         id_ns='test', name='Yoyodyne Instrument Systems',
         name_code='YIS', city='Grovers Mill',
         state_or_province='NJ', owner='pgefobjects:PGANA'),
    dict(
       _cname='HardwareProduct',
       oid='test:inst2',
       id='Inst-v2',
       id_ns='test',
       owner='test:yoyoinst',
       name='Instrument v.2',
       description='Instrument, version 2, Advanced',
       comment='This instrument is quite advanced.',
       creator='test:steve',
       create_datetime=NOW,
       modifier='test:steve',
       mod_datetime=NOW,
       parameters={'P': 50.0,
                   'm': 500.0},
       iteration=1,
       version='2',
       version_sequence=2),
     ]

locally_owned_test_objects = [
    dict(
         _cname='Organization', oid='test:yoyodyne', id='YOYODYNE',
         id_ns='test', name='Yoyodyne Propulsion Systems',
         name_code='YPS', city='Grovers Mill',
         state_or_province='NJ', owner='pgefobjects:PGANA'),
    dict(
       _cname='HardwareProduct',
       oid='test:prop10',
       id='prop10',
       id_ns='test',
       owner='test:yoyodyne',
       name='Yoyomatic Propulsion System',
       description='Yoyomatic system, Advanced',
       comment='This propulsion system is very advanced.',
       creator='test:steve',
       create_datetime=NOW,
       modifier='test:steve',
       mod_datetime=NOW,
       parameters={'P': 50000.0,
                   'm': 1000.0},
       iteration=1,
       version='0',
       version_sequence=0),
     ]

parametrized_test_object = [
    dict(
       _cname='HardwareProduct',
       oid='test:inst3',
       id='Inst-v3',
       id_ns='test',
       owner='test:yoyodyne',
       name='Instrument v.3',
       description='Instrument, version 3, Advanced',
       comment='This instrument is quite advanced.',
       creator='test:steve',
       create_datetime=NOW,
       modifier='test:steve',
       mod_datetime=NOW,
       parameters={'P': 100.0,
                   'R_D': 1000000.0,
                   'm': 1000.0},
       iteration=1,
       version='3',
       version_sequence=3),
     ]

# TODO:  use this to test exporting of simplified parameters ...
parametrized_summary_test_object = [
    dict(
       _cname='HardwareProduct',
       oid='test:inst4',
       id='Inst-v4',
       id_ns='test',
       owner='test:yoyodyne',
       name='Instrument v.4',
       description='Instrument, version 4, Advanced',
       comment='This instrument is quite advanced.',
       creator='test:steve',
       create_datetime=NOW,
       modifier='test:steve',
       mod_datetime=NOW,
       parameters={'m' : 50.0,
                   'P' : 10.0},
       iteration=1,
       version='4',
       version_sequence=4),
     ]

test_data_elements = dict(
    TRL=4,
    Vendor="Yoyodyne"
    )

test_parms = {
    "Cost" : 0.0,
    "P" : 0.0,
    "P[CBE]" : 0.0,
    "P[MEV]" : 0.0,
    "R_D" : 0.0,
    "R_D[CBE]" : 0.0,
    "R_D[MEV]" : 0.0,
    "depth" : 0.0,
    "height" : 0.0,
    "width" : 0.0,
    "m" : 0.0,
    "m[CBE]" : 0.0,
    "m[MEV]" : 0.0,
    "P[Ctgcy]" : 0.3,
    "m[Ctgcy]" : 0.3,
    "R_D[Ctgcy]" : 0.3
    }

# A collection of related serialized test objects to be used for unit testing.
# The main purposes in having a separate set of serialized objects are:
# (1) they will not collide with the objects created by 'create_test_project()'
#     when deserialized and saved to the db.
# (2) for testing of parameter operations
related_test_objects = [
    dict(
        _cname='Project',
        oid='test:OTHER', id='OTHER', id_ns='test',
        owner='pgefobjects:PGANA', creator='pgefobjects:system',
        modifier='pgefobjects:system', create_datetime=NOW,
        mod_datetime=NOW, name='The Other Project',
        name_code='OTHER'),
    dict(
        _cname='HardwareProduct',
        oid='test:spacecraft3',
        id='Rocinante',
        id_ns='test',
        version='3',
        iteration=0,
        version_sequence=3,
        frozen=True,
        owner='test:OTHER',
        name='Rocinante Spacecraft',
        description='A Martian Navy gunship',
        data_elements=deepcopy(test_data_elements),
        parameters=deepcopy(test_parms),
        product_type='pgefobjects:ProductType.spacecraft',
        comment='Prototype',
        creator='test:bigboote',
        create_datetime=NOW,
        modifier='test:bigboote',
        mod_datetime=NOW
        ),
    dict(
        _cname='HardwareProduct',
        oid='test:sc3-thermal-system',
        id='SC3-Thermal-System-0001',
        id_ns='test',
        version='',
        iteration=0,
        version_sequence=0,
        frozen=True,
        owner='test:OTHER',
        name='Rocinante Thermal System',
        description='Thermal System',
        data_elements=deepcopy(test_data_elements),
        parameters=deepcopy(test_parms),
        product_type='pgefobjects:ProductType.thermal_control_system',
        comment='',
        creator='test:bigboote',
        create_datetime=NOW,
        modifier='test:bigboote',
        mod_datetime=NOW
        ),
    dict(
        _cname='HardwareProduct',
        oid='test:thermistor-0001',
        id='thermistor-0001',
        id_ns='test',
        version='',
        iteration=0,
        version_sequence=0,
        frozen=True,
        owner='test:OTHER',
        name='Thermistor 0001',
        description='Thermistor 0001',
        data_elements=deepcopy(test_data_elements),
        parameters={
            "m" : 0.003
            },
        product_type='pgefobjects:ProductType.temperature_sensor',
        comment='',
        creator='test:bigboote',
        create_datetime=NOW,
        modifier='test:bigboote',
        mod_datetime=NOW
        ),
    dict(
        _cname='ProjectSystemUsage',
        oid='test:OTHER:system-1',
        id='system-1',
        id_ns='test',
        name='OTHER Rocinante Spacecraft',
        project='test:OTHER',
        system='test:spacecraft3',
        system_role='Spacecraft',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
    dict(
        _cname='ParameterRelation',
        oid='test:OTHER:Spacecraft-Mass-Computable-Form-PR',
        id='OTHER.1.0.Spacecraft-Mass-Computable-Form',
        id_ns='test',
        name='OTHER 1.0 Spacecraft Mass Computable Form',
        referenced_relation='test:OTHER:Spacecraft-Mass-Computable-Form',
        correlates_parameter='pgef:ParameterDefinition.m',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
    dict(
        _cname='Relation',
        oid='test:OTHER:Spacecraft-Mass-Computable-Form',
        id='OTHER.1.0.Spacecraft-Mass-Computable-Form',
        id_ns='test',
        name='OTHER 1.0 Spacecraft Mass Computable Form',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
    dict(
        _cname='Requirement',
        oid='test:OTHER:Spacecraft-Mass',
        id='OTHER.1.0.Spacecraft-Mass',
        id_ns='test',
        name='OTHER 1.0 Spacecraft Mass',
        owner='test:OTHER',
        allocated_to='test:OTHER:system-1',
        # DEPRECATED:
        # allocated_to_system='test:OTHER:system-1',
        req_type='performance',
        req_constraint_type='maximum',
        req_maximum_value=4000.0,
        req_units='kg',
        computable_form='test:OTHER:Spacecraft-Mass-Computable-Form',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),

     # using a CAX-IF STEP model for test purposes
     dict(
        _cname='Model',
        oid='test:spacecraft3.mcad.model.0',
        id='spacecraft3.mcad.model.0',
        id_ns='test',
        iteration=0,
        version='0',
        version_sequence=0,
        owner='test:OTHER',
        name='MCAD Model of Rocinante Spacecraft',
        of_thing='test:spacecraft3',
        model_definition_context='gsfc:Discipline.mechanical',
        type_of_model='step:203',
        description='MCAD Model, v0, of Rocinante Spacecraft',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
     dict(
        _cname='Representation',
        oid='test:spacecraft3.mcad.0.representation',
        id='spacecraft3.mcad.0.representation',
        id_ns='test',
        name='Rocinante v3 MCAD v0 Representation',
        description='Rocinante v3 MCAD v0 Representation',
        of_object='test:spacecraft3.mcad.model.0',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
     dict(
        _cname='RepresentationFile',
        oid='test:spacecraft3.mcad.0.representationfile.0',
        id='spacecraft3.mcad.0.representationfile.0',
        id_ns='test',
        name='Rocinante v3 MCAD v0 Representation File 0',
        description='Rocinante v3 MCAD v0 Representation File 0',
        of_representation='test:spacecraft3.mcad.0.representation',
        mime_type='application/step',
        # (same file as used for 'test:spacecraft0')
        url='vault://Rocinante_0_MCAD_0_R0_File0.step',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW),
    dict(
        _cname='Acu',
        oid='test:spacecraft3-acu-1',
        id='spacecraft3-acu-1',
        id_ns='test',
        name='Oscillation Overthruster Component Usage',
        assembly='test:spacecraft3',
        component='test:overthruster',
        reference_designator='Prop-1',
        creator='test:whorfin',
        create_datetime=NOW,
        modifier='test:whorfin',
        mod_datetime=NOW
        ),
    dict(
        _cname='Acu',
        oid='test:spacecraft3-acu-2',
        id='spacecraft3-acu-2',
        id_ns='test',
        name='Infinite Improbability Drive in Rocinante Spacecraft',
        assembly='test:spacecraft3',
        component='test:iidrive',
        reference_designator='Prop-2',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
    dict(
        _cname='Acu',
        oid='test:spacecraft3-acu-3',
        id='spacecraft3-acu-3',
        id_ns='test',
        name='Photon Drive in Rocinante Spacecraft',
        assembly='test:spacecraft3',
        component='test:photon_drive',
        reference_designator='Prop-3',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
    dict(
        _cname='Acu',
        oid='test:spacecraft3-acu-4',
        id='spacecraft3-acu-4',
        id_ns='test',
        name='Bambleweeny Sub-Meson Brain in Rocinante Spacecraft',
        assembly='test:spacecraft3',
        component='test:computer',
        reference_designator='Comp-1',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
    dict(
        _cname='Acu',
        oid='test:spacecraft3-acu-5',
        id='spacecraft3-acu-5',
        id_ns='test',
        name='Magic Twanger in Rocinante Spacecraft',
        assembly='test:spacecraft3',
        component='test:twanger',
        reference_designator='Comm-1',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
    dict(
        _cname='Acu',
        oid='test:spacecraft3-acu-6',
        id='spacecraft3-acu-6',
        id_ns='test',
        name='Thermal System in Rocinante Spacecraft',
        assembly='test:spacecraft3',
        component='test:sc3-thermal-system',
        reference_designator='Thermal',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
    dict(
        _cname='Acu',
        oid='test:thermal-system-acu-7',
        id='sc-thermistors-acu-7',
        id_ns='test',
        name='Spacecraft Temp Sensors',
        assembly='test:sc3-thermal-system',
        component='test:thermistor-0001',
        # a ridiculously large quantity is used here so that the very small
        # mass of the thermistors will not get wiped out by rounding in the
        # "compute_cbe..." tests
        quantity=1600,
        reference_designator='SC-Temp-Sensors',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        ),
    dict(
        _cname='Acu',
        oid='test:thermal-system-acu-8',
        id='propulsion-thermistors-acu-8',
        id_ns='test',
        name='Propulsion Systemm Temp Sensors',
        assembly='test:sc3-thermal-system',
        component='test:thermistor-0001',
        # a ridiculously large quantity is used here so that the very small
        # mass of the thermistors will not get wiped out by rounding in the
        # "compute_cbe..." tests
        quantity=3200,
        reference_designator='Prop-Temp-Sensors',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        )
        ]

