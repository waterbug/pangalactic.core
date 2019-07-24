# -*- coding: utf-8 -*-
"""
Create PGEF test data.
"""
from builtins import str
from copy     import deepcopy
import random
from pangalactic.core.parametrics import parm_defz
from pangalactic.core.utils.meta import (get_port_abbr, get_port_id,
                                         get_port_name)
from pangalactic.core.utils.datetimes import dtstamp

NOW = str(dtstamp())

def gen_test_pvals(parms):
    """
    Generate random values for the non-computed float and int types in a set of
    Parameters.

    Args:
        parms (dict):  parameters dict of the form
            {parameter id: {standard parameter dict},
             ...}
            where the standard parameter dict is defined in p.node.parametrics
            and is the value of parameterz[obj.oid] for any object that has
            parameters.
    """
    for pid, parm in parms.items():
        pdz = parm_defz.get(pid, {})
        if pdz.get('computed'):
            # ignore computed parameters
            continue
        if '[Ctgcy]' in pid:
            parm['value'] = 0.30
        elif pdz.get('range_datatype') == 'float':
            if not parm['value']:
                if pdz.get('variable') == 'P':
                    # special case for Power parameters
                    # (can be positive or negative)
                    parm['value'] = float(random.randint(-500, 500))
                else:
                    parm['value'] = float(random.randint(1, 1000))
        # special cases for Data Rate parameters
        elif pdz.get('variable') == 'R_D':
            parm['value'] = random.randint(10000, 100000)
        elif pdz.get('range_datatype') == 'int':
            # make sure no non-zero default has been set
            if not parm['value']:
                parm['value'] = random.randint(1, 10)
        elif pdz.get('range_datatype') == 'text':
            parm['value'] = 'testing...'

def create_test_users():
    """
    Return standard test users from 2 Organizations (Yoyodyne Propulsion
    Systems and Banzai Aerospace).
    """
    objs = [
        dict(
             _cname='Organization', oid='test:yoyodyne', id='yoyodyne',
             id_ns='pangalactic', name='Yoyodyne Propulsion Systems',
             name_code='YPS', city='Grovers Mill',
             state_or_province='NJ'),
        dict(
             _cname='Organization', oid='test:banzai', id='BANZAI',
             id_ns='pangalactic',
             name='Banzai Aerospace', name_code='BA',
             city='White Sands', state_or_province='NM'),
        dict(
            _cname='Person',
            oid='test:steve', id='steve',
            id_ns='pangalactic', name='Steve Waterbury',
            email='waterbug@pangalactic.us', first_name='Stephen',
            mi_or_name='C', last_name='Waterbury',
            org='test:banzai'),
        dict(
            _cname='Person',
            oid='test:zaphod', id='zaphod',
            id_ns='pangalactic', name='Zaphod Z. Beeblebrox',
            org='test:banzai', create_datetime=NOW, mod_datetime=NOW,
            email='zaphod@space.univ', first_name='Zaphod',
            mi_or_name='Z', last_name='Beeblebrox',
            phone='1-800-ZAPHOD'),
        dict(
            _cname='Person',
            oid='test:buckaroo', id='buckaroo',
            id_ns='pangalactic', name='Buckaroo Banzai',
            org='test:banzai', create_datetime=NOW, mod_datetime=NOW,
            email='buckaroo@banzai.earth.milkyway.univ',
            first_name='Buckaroo', mi_or_name='', last_name='Banzai',
            phone='1-800-BANZAI'),
        dict(
            _cname='Person',
            oid='test:whorfin', id='whorfin',
            id_ns='pangalactic', name='John Whorfin (Dr. Emilio Lizardo)',
            org='test:yoyodyne', create_datetime=NOW, mod_datetime=NOW,
            email='whorfin@redlectroids.planet10.univ',
            first_name='John', mi_or_name='', last_name='Whorfin',
            phone='1-Z00-WHORFIN'),
        dict(
            _cname='Person',
            oid='test:bigboote', id='bigboote',
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
            phone='1-Z00-SMALLBE'),
        dict(
            _cname='Person',
            oid='test:thornystick', id='thornystick',
            id_ns='pangalactic', name='John Thornystick',
            org='test:yoyodyne', create_datetime=NOW, mod_datetime=NOW,
            email='thornystick@redlectroids.planet10.univ',
            first_name='John', mi_or_name='', last_name='Thornystick',
            phone='1-Z00-THORNYS'),
        dict(
            _cname='Person',
            oid='test:manyjars', id='manyjars',
            id_ns='pangalactic', name='John Manyjars',
            org='test:yoyodyne', create_datetime=NOW, mod_datetime=NOW,
            email='manyjars@redlectroids.planet10.univ',
            first_name='John', mi_or_name='', last_name='Manyjars',
            phone='1-Z00-MANYJAR')
            ]
    return objs

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
            id_ns='test',
            creator='test:steve', modifier='test:steve',
            create_datetime=NOW, mod_datetime=NOW,
            name='Hitchhikers Guide to the Galaxy',
            name_code='H2G2'),
        dict(
            _cname='Mission', oid='test:Mission.H2G2',
            id='h2g2_mission', id_ns='test', owner='H2G2',
            creator='test:steve', modifier='test:steve',
            create_datetime=NOW, mod_datetime=NOW,
            name='Hitchhike the Galaxy'),
        dict(
            _cname='RoleAssignment',
            oid='test:RA.zaphod_se',
            id='zaphod_se',
            id_ns='test',
            assigned_role='gsfc:Role.systems_engineer',
            assigned_to='test:zaphod',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            oid='test:RA.steve_le',
            id='steve_le',
            id_ns='test',
            assigned_role='gsfc:Role.lead_engineer',
            assigned_to='test:steve',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            oid='test:RA.steve_h2g2_admin',
            id='steve_h2g2_admin',
            id_ns='test',
            assigned_role='pgefobjects:Role.Administrator',
            assigned_to='test:steve',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            oid='test:RA.steve_admin',
            id='steve_admin',
            id_ns='test',
            assigned_role='pgefobjects:Role.Administrator',
            assigned_to='test:steve'),
        dict(
            _cname='RoleAssignment',
            oid='test:RA.buckaroo_propulsion',
            id='buckaroo_propulsion',
            id_ns='test',
            assigned_role='gsfc:Role.propulsion_engineer',
            assigned_to='test:buckaroo',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            oid='test:RA.whorfin_propulsion',
            id='whorfin_propulsion',
            id_ns='test',
            assigned_role='gsfc:Role.propulsion_engineer',
            assigned_to='test:whorfin',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            oid='test:RA.bigboote_acs',
            id='bigboote_acs',
            assigned_role='gsfc:Role.acs_engineer',
            assigned_to='test:bigboote',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            oid='test:RA.smallberries_thermal',
            id='smallberries_thermal',
            assigned_role='gsfc:Role.thermal_engineer',
            assigned_to='test:smallberries',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
            oid='test:RA.thornystick_mechanical',
            id='thornystick_mechanical',
            assigned_role='gsfc:Role.mechanical_engineer',
            assigned_to='test:thornystick',
            role_assignment_context='H2G2'),
        dict(
            _cname='RoleAssignment',
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
            name='Mr. Fusion Series A',
            description='Power Generator, Fusion, Blender-Style',
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
            abbreviation=get_port_abbr('Electrical Power', 0),
            owner='test:yoyodyne',
            name=get_port_name('Gigawatt Magic Twanger',
                               'Electrical Power', 0),
            of_product='test:twanger',
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
            abbreviation=get_port_abbr('Electrical Power', 0),
            owner='test:banzai',
            name=get_port_name('Oscillation Overthruster',
                               'Electrical Power', 0),
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
            abbreviation=get_port_abbr('Electrical Power', 0),
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
            _cname='ParameterDefinition',
            oid='test:ParameterDefinition.X_y',
            id='X_y',
            id_ns='test',
            name='X y',
            description='X y parameter',
            dimensions='mass',
            range_datatype='float',
            public=True,
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
            reference_designator='Propulsion System',
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
            reference_designator='Infinite Improbability Propulsion System',
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
            reference_designator='Photon Propulsion System',
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
            reference_designator='Ship Computer',
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
            reference_designator='Communications System',
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
            reference_designator='Flux Storage Subsystem',
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
            reference_designator='Electrical Power Subsystem',
            creator='test:steve',
            create_datetime=NOW,
            modifier='test:steve',
            mod_datetime=NOW
            )
        ]
    return test_project

parametrized_test_objects = [
    dict(
       _cname='HardwareProduct',
       oid='test:inst2',
       id='Inst-v2',
       id_ns='test',
       owner='test:yoyodyne',
       name='Instrument v.2',
       description='Instrument, version 2, Advanced',
       comment='This instrument is quite advanced.',
       creator='test:steve',
       create_datetime=NOW,
       modifier='test:steve',
       mod_datetime=NOW,
       parameters={
       'P':
         {'mod_datetime': NOW,
          'units': 'W',
          'value': 100.0},
       'm':
         {'mod_datetime': NOW,
          'units': 'kg',
          'value': 1000.0}
       },
       iteration=1,
       version='2',
       version_sequence=2),
     ]

# TODO:  use this to test exporting of simplified parameters ...
parametrized_summary_test_object = [
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
       parameters={'m' : (50.0, 'kg'),
                   'p' : (10.0, 'W')},
       iteration=2,
       version='3',
       version_sequence=3),
     ]

test_parms = {
    "Cost":{
        "mod_datetime":NOW,
        "units":"$",
        "value":0.0
    },
    "P":{
        "mod_datetime":NOW,
        "units":"W",
        "value":0.0
    },
    "R_D":{
        "mod_datetime":NOW,
        "units":"bit/s",
        "value":0
    },
    "TRL":{
        "mod_datetime":NOW,
        "units":"",
        "value":4
    },
    "Vendor":{
        "mod_datetime":NOW,
        "units":"",
        "value":""
    },
    "depth":{
        "mod_datetime":NOW,
        "units":"m",
        "value":0.0
    },
    "height":{
        "mod_datetime":NOW,
        "units":"m",
        "value":0.0
    },
    "m":{
        "mod_datetime":NOW,
        "units":"kg",
        "value":0.0
    },
    "P[Ctgcy]":{
        "mod_datetime":NOW,
        "units":"%",
        "value":0.3
    },
    "m[Ctgcy]":{
        "mod_datetime":NOW,
        "units":"%",
        "value":0.3
    },
    "R_D[Ctgcy]":{
        "mod_datetime":NOW,
        "units":"%",
        "value":0.3
    },
    "width":{
        "mod_datetime":NOW,
        "units":"m",
        "value":0.0
    }
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
        _cname='Project',
        oid='test:OTHEROTHER', id='OTHEROTHER', id_ns='test',
        owner='pgefobjects:PGANA', creator='pgefobjects:system',
        modifier='pgefobjects:system', create_datetime=NOW,
        mod_datetime=NOW, name='The Other Other Project',
        name_code='OTHEROTHER'),
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
        parameters=deepcopy(test_parms),
        comment='Prototype',
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
        project='test:OTHER',
        allocated_to_system='test:OTHER:system-1',
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
        reference_designator='Main Propulsion Subsystem',
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
        reference_designator='Secondary Propulsion System',
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
        reference_designator='Tertiary Propulsion System',
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
        reference_designator='Computer',
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
        reference_designator='Communications System',
        creator='test:steve',
        create_datetime=NOW,
        modifier='test:steve',
        mod_datetime=NOW
        )
        ]

