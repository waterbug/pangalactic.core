"""
PanGalactic reference data
"""
epoch = '2017-01-01 00:00:00'


initial = [
{   '_cname': 'Actor',
    'oid': 'pgefobjects:system',
    'description': 'A really huge infundibulum',
    'id': 'Infundibulum',
    'name': 'The Chronosynclastic Infundibulum',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Organization',
    'oid': 'pgefobjects:PGANA',
    'description': 'The mysterious cabal behind it all',
    'id': 'PGANA',
    'name': 'Pan Galactic Assigned Names Authority',
    'abbreviation': 'PGANA',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Person',
    'oid': 'pgefobjects:admin',
    'description': 'Pan Galactic Administrator',
    'id': 'admin',
    'first_name': 'TheGreatAndPowerful',
    'last_name': 'Oz',
    'name': 'The Great And Powerful Oz',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Person',
    'oid': 'pgefobjects:Person.TBD',
    'description': 'TBD',
    'id': 'TBD',
    'first_name': 'TBD',
    'last_name': 'Person',
    'name': 'TBD Person',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Role',
    'oid': 'pgefobjects:Role.Disabled',
    'description': 'Indicates that all assigned roles are inactive',
    'id': 'Disabled',
    'name': 'Disabled',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Role',
    'oid': 'pgefobjects:Role.Administrator',
    'description': 'Administrator in an organizational context',
    'id': 'Administrator',
    'name': 'Administrator',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Role',
    'oid': 'pgefobjects:Role.Observer',
    'description': 'Read-only accesss in an organizational context',
    'id': 'Observer',
    'name': 'Observer',
    'create_datetime': epoch,
    'mod_datetime': epoch
    }
]

# parameter_definitions_and_contexts
pdc = [
{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.m',
    'id': 'm',
    'name': 'Mass',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'mass',
    'range_datatype': 'float',
    'description': 'Quantity of matter'
    },

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.height',
    'id': 'height',
    'name': 'Height',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'length',
    'range_datatype': 'float',
    'description': 'Length in y direction'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.width',
    'id': 'width',
    'name': 'Width',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'length',
    'range_datatype': 'float',
    'description': 'Length in x direction'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.depth',
    'id': 'depth',
    'name': 'Depth',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'length',
    'range_datatype': 'float',
    'description': 'Length in z direction'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.CoM_X',
    'id': 'CoM_X',
    'name': 'X Center of Mass',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'length',
    'range_datatype': 'float',
    'description': 'X coordinate of the Center of Mass'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.CoM_Y',
    'id': 'CoM_Y',
    'name': 'Y Center of Mass',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'length',
    'range_datatype': 'float',
    'description': 'Y coordinate of the Center of Mass'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.CoM_Z',
    'id': 'CoM_Z',
    'name': 'Z Center of Mass',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'length',
    'range_datatype': 'float',
    'description': 'Z coordinate of the Center of Mass'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.Cost',
    'id': 'Cost',
    'name': 'Cost',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'money',
    'range_datatype': 'float',
    'description': 'Unit cost of an item'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.D_Capacity',
    'id': 'D_Capacity',
    'name': 'Data Capacity',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'data',
    'range_datatype': 'int',
    'description': 'Data storage capacity'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.R_D',
    'id': 'R_D',
    'name': 'Data Rate',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': '2018-05-25 00:00:00',
    'dimensions': 'bitrate',
    'port_type': 'pgefobjects:PortType.digital_data',
    'range_datatype': 'int',
    'description': 'Flow of bits per unit time through a data port.'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.P',
    'id': 'P',
    'name': 'Power',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'power',
    'port_type': 'pgefobjects:PortType.electrical_power',
    'range_datatype': 'float',
    'description': 'Nominal electrical power consumption.'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.V',
    'id': 'V',
    'name': 'Voltage',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': '2018-05-25 00:00:00',
    'dimensions': 'electrical potential',
    'port_type': 'pgefobjects:PortType.digital_data',
    'range_datatype': 'float',
    'description': 'Voltage'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.Area_active',
    'id': 'Area_active',
    'name': 'Active Area',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'area',
    'range_datatype': 'float',
    'description': 'The active area of a product, such as a solar panel, for which that is a well-defined functional property. For a solar panel, this is the exposed area that takes part in collecting energy from the Sun.  Generally it is the solar cell area though there is some top side conductor area that exists on each cell.'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.Area_substrate',
    'id': 'Area_substrate',
    'name': 'Substrate Area',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'area',
    'range_datatype': 'float',
    'description': 'On a solar panel, Substrate Area includes the Active Area plus the mounting substrate or mesh area, including all stiffeners, areas for mounting sensors, wiring harnesses (if on the top side, facing the Sun), expansion/contraction relief areas around the solar cells, hold down or pre-deployed clamping areas, and other top side mounted equipment areas.'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.TRL',
    'id': 'TRL',
    'name': 'TRL',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': None,
    'range_datatype': 'int',
    'description': 'Technology Readiness Level (TRL)'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.Vendor',
    'id': 'Vendor',
    'name': 'Vendor',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': None,
    'range_datatype': 'text',
    'description': 'Entity from which a thing is procured.'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.duration',
    'id': 'duration',
    'name': 'Duration',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'time',
    'range_datatype': 'float',
    'description': 'Length of time during which an activity proceeds.'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.t_start',
    'id': 't_start',
    'name': 'Start Time',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'time',
    'range_datatype': 'float',
    'description': 'Time at which an activity begins.'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.t_end',
    'id': 't_end',
    'name': 'End Time',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'time',
    'range_datatype': 'float',
    'description': 'Time at which an activity ceases.'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.f_downlink',
    'id': 'f_downlink',
    'name': 'Downlink Frequency',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'frequency',
    'range_datatype': 'float',
    'description': 'Frequency of downlink signal'},

{   '_cname': 'ParameterDefinition',
    'oid': 'pgef:ParameterDefinition.f_uplink',
    'id': 'f_uplink',
    'name': 'Uplink Frequency',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'dimensions': 'frequency',
    'range_datatype': 'float',
    'description': 'Frequency of uplink signal'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.CBE',
    'id': 'CBE',
    'name': 'Current Best Estimate',
    'abbreviation': 'CBE',
    'context_type': 'descriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': True,
    'description': 'Current Best Estimate'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.Assembly',
    'id': 'Assembly',
    'name': 'Assembly',
    'abbreviation': 'Assembly',
    'context_type': 'descriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': True,
    'description': 'Total value summed over assembly'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.Ctgcy',
    'id': 'Ctgcy',
    'name': 'Contingency',
    'abbreviation': 'Ctgcy',
    'context_type': 'descriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': 'percent',
    'context_datatype': 'float',
    'computed': False,
    'description': 'Contingency'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.MEV',
    'id': 'MEV',
    'name': 'Maximum Estimated Value',
    'abbreviation': 'MEV',
    'context_type': 'descriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': True,
    'description': 'CBE * (1 + Ctgcy)'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.NTE',
    'id': 'NTE',
    'name': 'Not To Exceed',
    'abbreviation': 'NTE',
    'context_type': 'prescriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': False,
    'description': 'Maximum allowable value'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.NLT',
    'id': 'NLT',
    'name': 'Not Less Than',
    'abbreviation': 'NLT',
    'context_type': 'prescriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': False,
    'description': 'Minimum allowable value'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.Target',
    'id': 'Target',
    'name': 'Target Value',
    'abbreviation': 'Target',
    'context_type': 'prescriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': False,
    'description': 'Target value associated with a tolerance'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.Tolerance',
    'id': 'Tolerance',
    'name': 'Symmetric Tolerance',
    'abbreviation': 'Tol',
    'context_type': 'prescriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': False,
    'description': 'Symmetric tolerance value'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.Tolerance_Upper',
    'id': 'Tolerance_Upper',
    'name': 'Upper Tolerance',
    'abbreviation': 'Upper Tol',
    'context_type': 'prescriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': False,
    'description': 'Upper value in asymmetric tolerance'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.Tolerance_Lower',
    'id': 'Tolerance_Lower',
    'name': 'Lower Tolerance',
    'abbreviation': 'Lower Tol',
    'context_type': 'prescriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': False,
    'description': 'Lower value in asymmetric tolerance'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.Limit_Max',
    'id': 'Limit_Max',
    'name': 'Maximum Limit',
    'abbreviation': 'Max Lmt',
    'context_type': 'prescriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': False,
    'description': 'Maximum value of range'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.Limit_Min',
    'id': 'Limit_Min',
    'name': 'Minimum Limit',
    'abbreviation': 'Min Lmt',
    'context_type': 'prescriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': None,
    'context_datatype': None,
    'computed': False,
    'description': 'Minimum value of range'},

{   '_cname': 'ParameterContext',
    'oid': 'pgef:ParameterContext.Margin',
    'id': 'Margin',
    'name': 'Margin',
    'abbreviation': 'Margin',
    'context_type': 'prescriptive',
    'owner': 'pgefobjects:PGANA',
    'creator': 'pgefobjects:admin',
    'create_datetime': epoch,
    'mod_datetime': epoch,
    'context_dimensions': 'percent',
    'context_datatype': 'float',
    'computed': True,
    'description': '(NTE-MEV)/NTE'}
]

core = [
{   '_cname': 'Project',
    'oid': 'pgefobjects:SANDBOX',
    'id': 'SANDBOX',
    'name': 'Sandbox Project',
    'name_code': 'SANDBOX',
    'description': 'Sandbox for experimentation',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ActivityType',
    'oid': 'pgefobjects:ActivityType.Operation',
    'id': 'operation',
    'name': 'Operation',
    'abbreviation': 'Op',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ActivityType',
    'oid': 'pgefobjects:ActivityType.Event',
    'id': 'event',
    'name': 'Event',
    'abbreviation': 'Evt',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ActivityType',
    'oid': 'pgefobjects:ActivityType.Cycle',
    'id': 'cycle',
    'name': 'Cycle',
    'abbreviation': 'Cyc',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Product',
    'oid': 'pgefobjects:TBD',
    'id': 'TBD',
    'name': 'TBD',
    'public': True,
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.science',
    'id': 'science',
    'name': 'Science',
    'abbreviation': 'Sci',
    'description': 'Science',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.engineering',
    'id': 'engineering',
    'name': 'Engineering',
    'abbreviation': 'Eng',
    'description': 'Engineering',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.acs',
    'id': 'acs',
    'name': 'Attitude Control Systems',
    'abbreviation': 'ACS',
    'description': 'Design of Attitude Control Systems',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.avionics',
    'id': 'avionics',
    'name': 'Avionics',
    'abbreviation': 'Avionics',
    'description': 'Avionics Engineering',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.power',
    'id': 'power',
    'name': 'Power Systems',
    'abbreviation': 'Power',
    'description': 'Design of Electrical Power Systems',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.fsw',
    'id': 'fsw',
    'name': 'Flight Software',
    'abbreviation': 'FSW',
    'description': 'Flight software methodology, reuse, estimate of labor, required test beds',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.flight_dynamics',
    'id': 'flight_dynamics',
    'name': 'Flight Dynamics',
    'abbreviation': 'FD',
    'description': 'Trajectory files and outputs from STK, EMTG, GMAT, or John Downings brain with required propulsion, eclipses, range to earth, angles for comm, etc.',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.mechanical',
    'id': 'mechanical',
    'name': 'Mechanical Systems',
    'abbreviation': 'Mechanical',
    'description': 'Design of Mechanical Structures and Systems',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.misson_ops',
    'id': 'mission_ops',
    'name': 'Mission Operations',
    'abbreviation': 'Mission Ops',
    'description': 'Mission Operations Engineering',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.propulsion',
    'id': 'propulsion',
    'name': 'Propulsion Systems',
    'abbreviation': 'Propulsion',
    'description': 'Propulsion Systems Engineering',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.rf_comm',
    'id': 'rf_comm',
    'name': 'RF Communications Systems',
    'abbreviation': 'RF Comm',
    'description': 'RF Communications Engineering',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.radiation',
    'id': 'radiation',
    'name': 'Radiation Analysis',
    'abbreviation': 'Radiation',
    'description': 'Analyzed trajectory radiation characterization and SPENVIS results',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.reliability',
    'id': 'reliability',
    'name': 'Reliability',
    'abbreviation': 'Reliability',
    'description': 'Reliability modeling and analysis.',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.systems',
    'id': 'systems',
    'name': 'Systems Engineering',
    'abbreviation': 'SE',
    'description': 'Systems Engineering',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.thermal',
    'id': 'thermal',
    'name': 'Thermal Systems',
    'abbreviation': 'Thermal',
    'description': 'Analysis of mission thermal environment, thermal characteristics of mission systems, and required thermal control systems',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.i_and_t',
    'id': 'i_and_t',
    'name': 'Integration and Test',
    'abbreviation': 'I/T',
    'description': 'Verification, integration flow, facilities required, cost estimate',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'Discipline',
    'oid': 'pgefobjects:Discipline.orbital_debris',
    'id': 'orbital_debris',
    'name': 'Orbital Debris',
    'abbreviation': 'Orbital Debris',
    'description': 'Modeling and analysis of expected debris for planned orbits',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

# Goddard Engineering and Scientific Discipline-related Roles
dict(
     _cname='Role',
     oid='gsfc:Role.pi',
     id='principal_investigator',
     abbreviation='PI',
     name='Principal Investigator'),
dict(
     _cname='Role',
     oid='gsfc:Role.systems_engineer',
     id='systems_engineer',
     abbreviation='SE',
     name='Systems Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.lead_engineer',
     id='lead_engineer',
     abbreviation='LE',
     name='Lead Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.acs_engineer',
     id='acs_engineer',
     abbreviation='ACS Engineer',
     name='Attitude Control Systems Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.avionics_engineer',
     id='avionics_engineer',
     abbreviation='Avionics Engineer',
     name='Avionics Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.power_engineer',
     id='power_engineer',
     abbreviation='Power Engineer',
     name='Power Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.fsw_engineer',
     id='flight_software_engineer',
     abbreviation='FSW Engineer',
     name='Flight Software Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.flight_dynamics_engineer',
     id='flight_dynamics_engineer',
     abbreviation='FD Engineer',
     name='Flight Dynamics Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.mission_ops_engineer',
     id='mission_ops_engineer',
     abbreviation='Mission Ops Engineer',
     name='Mission Operations Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.mechanical_engineer',
     id='mechanical_engineer',
     abbreviation='Mechanical Engineer',
     name='Mechanical Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.propulsion_engineer',
     id='propulsion_engineer',
     abbreviation='Propulsion Engineer',
     name='Propulsion Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.rf_comm_engineer',
     id='rf_comm_engineer',
     abbreviation='RF Comm Engineer',
     name='RF Communications Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.radiation_engineer',
     id='radiation_engineer',
     abbreviation='Radiation Engineer',
     name='Radiation Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.reliability_engineer',
     id='reliability_engineer',
     abbreviation='Reliability Engineer',
     name='Reliability Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.thermal_engineer',
     id='thermal_engineer',
     abbreviation='Thermal Engineer',
     name='Thermal Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.i_and_t_engineer',
     id='i_and_t_engineer',
     abbreviation='I/T Engineer',
     name='Integration and Test Engineer'),
dict(
     _cname='Role',
     oid='gsfc:Role.orbital_debris_engineer',
     id='orbital_debris_engineer',
     abbreviation='Orbital Debris Engineer',
     name='Orbital Debris Engineer'),

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.instrument',
    'id': 'instrument',
    'name': 'Instrument',
    'abbreviation': 'Instrument',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.observatory',
    'id': 'observatory',
    'name': 'Observatory',
    'abbreviation': 'Observ',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.spacecraft',
    'id': 'spacecraft',
    'name': 'Spacecraft',
    'abbreviation': 'SC',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.launch_vehicle',
    'id': 'launch_vehicle',
    'name': 'Launch Vehicle',
    'abbreviation': 'LV',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.attitude_control_system',
    'id': 'attitude_control_system',
    'name': 'Attitude Control System',
    'abbreviation': 'ACS',
    'description': 'Attitude Control Systems',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.c_and_dh_system',
    'id': 'c_and_dh_system',
    'name': 'Command and Data Handling System',
    'abbreviation': 'CDH',
    'description': 'Command and Data Handling System',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.diplexer',
    'id': 'diplexer',
    'name': 'Diplexer',
    'abbreviation': 'Diplexer',
    'description': 'Diplexer',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.electronics_box',
    'id': 'electronics_box',
    'name': 'Electronics Box',
    'abbreviation': 'Box',
    'description': 'Electronics Box',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.board',
    'id': 'board',
    'name': 'Electronic Circuit Board',
    'abbreviation': 'Board',
    'description': 'Electronic Circuit Board',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.eee_part',
    'id': 'eee_part',
    'name': 'EEE Part',
    'abbreviation': 'EEE Part',
    'description': 'Electrical, Electronic, or Electromechanical Component',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.communications_system',
    'id': 'communications_system',
    'name': 'Communications System',
    'abbreviation': 'Comm',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.power_system',
    'id': 'power_system',
    'name': 'Power System',
    'abbreviation': 'Power',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.mechanical_system',
    'id': 'mechanical_system',
    'name': 'Mechanical System',
    'abbreviation': 'Mech',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.propulsion_system',
    'id': 'propulsion_system',
    'name': 'Propulsion System',
    'abbreviation': 'Propulsion',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.thermal_control_system',
    'id': 'thermal_control_system',
    'name': 'Thermal Control System',
    'abbreviation': 'Thermal',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.computer',
    'id': 'computer',
    'name': 'Computer System',
    'abbreviation': 'Comp',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.star_tracker',
    'id': 'star_tracker',
    'name': 'Star Tracker',
    'abbreviation': 'ST',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.imu',
    'id': 'imu',
    'name': 'Inertial Measurement Unit',
    'abbreviation': 'IMU',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.iru',
    'id': 'iru',
    'name': 'Inertial Rate Unit',
    'abbreviation': 'IRU',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.control_moment_gyro',
    'id': 'control_moment_gyro',
    'name': 'Control Moment Gyro',
    'abbreviation': 'CMG',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.reaction_wheel',
    'id': 'reaction_wheel',
    'name': 'Reaction Wheel',
    'abbreviation': 'RW',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.momentum_wheel',
    'id': 'momentum_wheel',
    'name': 'Momentum Wheel',
    'abbreviation': 'MW',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.magnetic_torquer',
    'id': 'magnetic_torquer',
    'name': 'Magnetic Torquer',
    'abbreviation': 'MT',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.magnetometer',
    'id': 'magnetometer',
    'name': 'Magnetometer',
    'abbreviation': 'Magnetometer',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.digital_sun_sensor',
    'id': 'digital_sun_sensor',
    'name': 'Digital Sun Sensor',
    'abbreviation': 'DSS',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.coarse_sun_sensor',
    'id': 'coarse_sun_sensor',
    'name': 'Coarse Sun Sensor',
    'abbreviation': 'CSS',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.horizon_sensor',
    'id': 'horizon_sensor',
    'name': 'Horizon Sensor',
    'abbreviation': 'HS',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.tank',
    'id': 'tank',
    'name': 'Tank',
    'abbreviation': 'Tank',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

# {   '_cname': 'ProductType',
    # 'oid': 'pgefobjects:ProductType.oxidizer_tank',
    # 'id': 'oxidizer_tank',
    # 'name': 'Oxidizer Tank',
    # 'abbreviation': 'Oxidizer Tank',
    # 'create_datetime': epoch,
    # 'mod_datetime': epoch
    # },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.pyro_isolation_valve',
    'id': 'pyro_isolation_valve',
    'name': 'Pyro Isolation Valve',
    'abbreviation': 'Pyro Isolation Valve',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.propellant_filter',
    'id': 'propellant_filter',
    'name': 'Propellant Filter',
    'abbreviation': 'Filter',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.manifold',
    'id': 'manifold',
    'name': 'Manifold',
    'abbreviation': 'Manifold',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.fill_drain_valve',
    'id': 'fill_drain_valve',
    'name': 'Fill/Drain Valve',
    'abbreviation': 'Valve',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.thruster',
    'id': 'thruster',
    'name': 'Thruster',
    'abbreviation': 'Thruster',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

# {   '_cname': 'ProductType',
    # 'oid': 'pgefobjects:ProductType.propellant_tank',
    # 'id': 'propellant_tank',
    # 'name': 'Propellant Tank',
    # 'abbreviation': 'Tank',
    # 'create_datetime': epoch,
    # 'mod_datetime': epoch
    # },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.power_processing_unit',
    'id': 'power_processing_unit',
    'name': 'Power Processing Unit',
    'abbreviation': 'PPU',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.sep_engine',
    'id': 'sep_engine',
    'name': 'SEP Engine',
    'abbreviation': 'SEP Engine',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.sep_engine_gimbal',
    'id': 'sep_engine_gimbal',
    'name': 'SEP Engine Gimbal',
    'abbreviation': 'SEP Engine Gimbal',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.heater',
    'id': 'heater',
    'name': 'Heater',
    'abbreviation': 'Heater',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.thermostat',
    'id': 'thermostat',
    'name': 'Thermostat',
    'abbreviation': 'Thermostat',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.temperature_sensor',
    'id': 'temperature_sensor',
    'name': 'Temperature Sensor',
    'abbreviation': 'Temp Sensor',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.thermal_controller',
    'id': 'thermal_controller',
    'name': 'Thermal Controller',
    'abbreviation': 'Thermal Controller',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.multi_layer_insulation',
    'id': 'multi_layer_insulation',
    'name': 'Multi Layer Insulation',
    'abbreviation': 'Multi Layer Insulation',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.thermal_coating',
    'id': 'thermal_coating',
    'name': 'Thermal Coating',
    'abbreviation': 'Thermal Coating',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.radiator_panel',
    'id': 'radiator_panel',
    'name': 'Radiator Panel',
    'abbreviation': 'Radiator',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.heat_pipe',
    'id': 'heat_pipe',
    'name': 'Heat Pipe',
    'abbreviation': 'Heat Pipe',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.thermal_strap',
    'id': 'thermal_strap',
    'name': 'Thermal Strap',
    'abbreviation': 'Thermal Strap',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.thermal_louver',
    'id': 'thermal_louver',
    'name': 'Thermal Louver',
    'abbreviation': 'Louver',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.mechanical_structure',
    'id': 'mechanical_structure',
    'name': 'Mechanical Structure',
    'abbreviation': 'Mechanical Structure',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.instrument_accomodation',
    'id': 'instrument_accomodation',
    'name': 'Instrument Accomodation',
    'abbreviation': 'Inst Accomodation',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.payload_attach_fitting',
    'id': 'payload_attach_fitting',
    'name': 'Payload Attach Fitting',
    'abbreviation': 'Payload Attach Fitting',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.actuator',
    'id': 'actuator',
    'name': 'Actuator',
    'abbreviation': 'Actuator',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.solar_array_actuator',
    'id': 'solar_array_actuator',
    'name': 'Solar Array Actuator',
    'abbreviation': 'Solar Array Actuator',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.antenna_gimbal',
    'id': 'antenna_gimbal',
    'name': 'Antenna Gimbal',
    'abbreviation': 'Antenna Gimbal',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.boom',
    'id': 'boom',
    'name': 'Boom',
    'abbreviation': 'Boom',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.deployment_system',
    'id': 'deployment_system',
    'name': 'Deployment System',
    'abbreviation': 'Deployment System',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.solar_array',
    'id': 'solar_array',
    'name': 'Solar Array',
    'abbreviation': 'Solar Array',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.battery',
    'id': 'battery',
    'name': 'Battery',
    'abbreviation': 'Batt',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.fpga',
    'id': 'fpga',
    'name': 'Field Programmable Gate Array',
    'abbreviation': 'FPGA',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.printed_circuit_board',
    'id': 'printed_circuit_board',
    'name': 'Printed Circuit Board',
    'abbreviation': 'PCB',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.rtg',
    'id': 'rtg',
    'name': 'RadioIsotope Thermal Generator (RTG)',
    'abbreviation': 'RTG',
    'description': 'Pu-238 based very hot power thingy',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.power_harness',
    'id': 'power_harness',
    'name': 'Power Harness',
    'abbreviation': 'Power Harness',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.comsec',
    'id': 'comsec',
    'name': 'Communications Security Box',
    'abbreviation': 'COMSEC',
    'description': 'Communications Security: a box to prevent unauthorized '
                    'access',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.redundancy_management_unit',
    'id': 'redundancy_management_unit',
    'name': 'Redundancy Management Unit',
    'abbreviation': 'RMU',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.omni_antenna',
    'id': 'omni_antenna',
    'name': 'Omni Antenna',
    'abbreviation': 'Omni Antenna',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.medium_gain_antenna',
    'id': 'medium_gain_antenna',
    'name': 'Medium Gain Antenna (MGA)',
    'abbreviation': 'MGA',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.high_gain_antenna',
    'id': 'high_gain_antenna',
    'name': 'High Gain Antenna (HGA)',
    'abbreviation': 'HGA',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.antenna',
    'id': 'antenna',
    'name': 'Antenna',
    'abbreviation': 'Antenna',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.transponder',
    'id': 'transponder',
    'name': 'Transponder',
    'abbreviation': 'Xponder',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.transmitter',
    'id': 'transmitter',
    'name': 'Transmitter',
    'abbreviation': 'Xmitter',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.receiver',
    'id': 'receiver',
    'name': 'Receiver',
    'abbreviation': 'Receiver',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ProductType',
    'oid': 'pgefobjects:ProductType.power_amplifier',
    'id': 'power_amplifier',
    'name': 'Power Amplifier',
    'abbreviation': 'Power Amp',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelFamily',
    'oid': 'pgefobjects:ModelFamily.PGEF',
    'description': 'Pan Galactic Engineering Framework (PGEF) standard '
                   'family of model types.',
    'id': 'PGEF',
    'name': 'PGEF Model Family',
    'abbreviation': 'PGEF Model Family',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelFamily',
    'oid': 'pgefobjects:ModelFamily.SysML',
    'description': 'OMG Systems Modeling Language (SysML) standard family '
                   'of model types.',
    'id': 'SysML',
    'name': 'Systems Modeling Language (SysML)',
    'abbreviation': 'SysML',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelFamily',
    'oid': 'pgefobjects:ModelFamily.STEP',
    'description': 'STEP standard family of model types.',
    'id': 'STEP',
    'name': 'STEP (ISO 10303)',
    'abbreviation': 'STEP',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelFamily',
    'oid': 'pgefobjects:ModelFamily.Modelica',
    'description': 'Modelica standard family of model types.',
    'id': 'Modelica',
    'name': 'Modelica',
    'abbreviation': 'Modelica',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'pgefobjects:Spec',
    'id': 'pgef.Spec',
    'name': 'Specification',
    'abbreviation': 'Spec',
    'description': 'The specification for a part is a model that contains '
                   'a set of testable parameters that define the part.',
    'model_type_family': 'pgefobjects:ModelFamily.PGEF',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'pgefobjects:Block',
    'id': 'pgef.Block',
    'name': 'Block Model',
    'abbreviation': 'Block Model',
    'description': 'Pan Galactic Engineering Framework Block Model',
    'model_type_family': 'pgefobjects:ModelFamily.PGEF',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'pgefobjects:ConOps',
    'id': 'pgef.ConOps',
    'name': 'Concept of Operations Model',
    'abbreviation': 'ConOps Model',
    'description':
        'Pan Galactic Engineering Framework Concept of Operations Model',
    'model_type_family': 'pgefobjects:ModelFamily.PGEF',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'sysml:BDD',
    'description': 'OMG SysML Block Definition Diagram',
    'id': 'SysML.BDD',
    'model_type_family': 'pgefobjects:ModelFamily.SysML',
    'name': 'SysML Block Definition Diagram',
    'abbreviation': 'BDD',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'sysml:IBD',
    'description': 'OMG SysML Internal Block Diagram',
    'id': 'SysML.IBD',
    'model_type_family': 'pgefobjects:ModelFamily.SysML',
    'name': 'SysML Internal Block Diagram',
    'abbreviation': 'IBD',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'sysml:Activity',
    'description': 'OMG SysML Activity Model',
    'id': 'SysML.Activity',
    'model_type_family': 'pgefobjects:ModelFamily.SysML',
    'name': 'SysML Activity Diagram',
    'abbreviation': 'AD',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'sysml:Parametric',
    'description': 'OMG SysML Parametric Diagram',
    'id': 'SysML.Parametric',
    'model_type_family': 'pgefobjects:ModelFamily.SysML',
    'name': 'SysML Parametric Diagram',
    'abbreviation': 'PD',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'step:203',
    'description': 'STEP 3D Mechanical CAD model',
    'id': 'STEP.203',
    'model_type_family': 'pgefobjects:ModelFamily.STEP',
    'name': 'ISO 10303-203: Configuration controlled 3D designs '
            'of mechanical parts and assemblies',
    'abbreviation': 'AP203',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'step:209',
    'description': 'STEP 3D FEA / Composite analysis model',
    'id': 'STEP.209',
    'model_type_family': 'pgefobjects:ModelFamily.STEP',
    'name': 'ISO 10303-209: Composite and metallic structural '
            'analysis and related design',
    'abbreviation': 'AP209',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'step:210',
    'description': 'STEP 3D Electronic CAD model',
    'id': 'STEP.210',
    'model_type_family': 'pgefobjects:ModelFamily.STEP',
    'name': 'ISO 10303-210: Electronic assembly, interconnect '
            'and packaging design',
    'abbreviation': 'AP210',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'step:214',
    'description': 'STEP 3D Mechanical CAD model',
    'id': 'STEP.214',
    'model_type_family': 'pgefobjects:ModelFamily.STEP',
    'name': 'ISO 10303-214: Core data for automotive mechanical '
            'design processes',
    'abbreviation': 'AP214',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'step:242',
    'description': 'STEP 3D Mechanical CAD model',
    'id': 'STEP.242',
    'model_type_family': 'pgefobjects:ModelFamily.STEP',
    'name': 'ISO 10303-242: Managed model-based 3D engineering',
    'abbreviation': 'AP242',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'ModelType',
    'oid': 'step:TAS',
    'description': 'STEP-TAS thermal model',
    'id': 'STEP-TAS',
    'model_type_family': 'pgefobjects:ModelFamily.STEP',
    'name': 'STEP-TAS: Thermal Analysis for Space',
    'abbreviation': 'STEP-TAS',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortType',
    'oid': 'pgefobjects:PortType.electrical_power',
    'description': 'Electrical power port',
    'id': 'electrical_power',
    'name': 'Electrical Power',
    'abbreviation': 'Elec',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortType',
    'oid': 'pgefobjects:PortType.propulsion_power',
    'description': 'Propulsion power port',
    'id': 'propulsion_power',
    'name': 'Propulsion Power',
    'abbreviation': 'Prop',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortType',
    'oid': 'pgefobjects:PortType.electronic_control',
    'description': 'Electronic control signal port',
    'id': 'electronic_control',
    'name': 'Electronic Control',
    'abbreviation': 'Control',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortType',
    'oid': 'pgefobjects:PortType.analog_data',
    'description': 'Analog data port',
    'id': 'analog_data',
    'name': 'Analog Data',
    'abbreviation': 'Analog',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortType',
    'oid': 'pgefobjects:PortType.digital_data',
    'description': 'Digital data port',
    'id': 'digital_data',
    'name': 'Digital Data',
    'abbreviation': 'Digital',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortType',
    'oid': 'pgefobjects:PortType.comm',
    'description': 'Port for wireless communications',
    'id': 'comm',
    'name': 'Communications',
    'abbreviation': 'Comm',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortType',
    'oid': 'pgefobjects:PortType.thermal',
    'description': 'Thermal (power) port',
    'id': 'thermal',
    'name': 'Thermal',
    'abbreviation': 'Thermal',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortType',
    'oid': 'pgefobjects:PortType.gas',
    'description': 'Gas port',
    'id': 'gas',
    'name': 'Gas',
    'abbreviation': 'Gas',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortTemplate',
    'oid': 'pgefobjects:PortTemplate.digital_data.RS422',
    'description': 'RS422 (TIA/EIA-422) digital data port',
    'id': 'digital_data.RS422',
    'name': 'RS422 Digital Data Port',
    'abbreviation': 'RS422',
    'type_of_port': 'pgefobjects:PortType.digital_data',
    'parameters': {
       'R_D':
         {'value': 655e6,
          'mod_datetime': epoch,
          'units': 'Mbit/s'}
          },
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortTemplate',
    'oid': 'pgefobjects:PortTemplate.digital_data.LVDS',
    'description': 'LVDS (TIA/EIA-644) digital data port',
    'id': 'digital_data.LVDS',
    'name': 'LVDS Digital Data Port',
    'abbreviation': 'LVDS',
    'type_of_port': 'pgefobjects:PortType.digital_data',
    'parameters': {
       'R_D':
         {'value': 1e7,  # per Wikipedia: 10 Mbit/s
          'mod_datetime': epoch,
          'units': 'Mbit/s'}
          },
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortTemplate',
    'oid': 'pgefobjects:PortTemplate.digital_data.SpaceWire',
    'description': 'SpaceWire digital data port',
    'id': 'digital_data.SpaceWire',
    'name': 'SpaceWire Digital Data Port',
    'abbreviation': 'SpaceWire',
    'type_of_port': 'pgefobjects:PortType.digital_data',
    'parameters': {
       'R_D':
         {'value': 4e8,  # per Wikipedia: 400 Mbit/s
          'mod_datetime': epoch,
          'units': 'Mbit/s'}
          },
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortTemplate',
    'oid': 'pgefobjects:PortTemplate.digital_data.GPIO',
    'description': 'GPIO (General Purpose Input Output) digital data port',
    'id': 'digital_data.GPIO',
    'name': 'GPIO Digital Data Port',
    'abbreviation': 'GPIO',
    'parameters': {
       'R_D':
         {'value': 0,  # TBD
          'mod_datetime': epoch,
          'units': 'Mbit/s'}
          },
    'type_of_port': 'pgefobjects:PortType.digital_data',
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortTemplate',
    'oid': 'pgefobjects:PortTemplate.electrical_power.28V',
    'description': '28V electrical power port',
    'id': 'electrical_power.28V',
    'name': '28V Electrical Power Port',
    'abbreviation': '28V',
    'type_of_port': 'pgefobjects:PortType.electrical_power',
    'parameters': {
       'V':
         {'value': 28,
          'mod_datetime': epoch,
          'units': 'V'}
          },
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortTemplate',
    'oid': 'pgefobjects:PortTemplate.electrical_power.12V',
    'description': '12V electrical power port',
    'id': 'electrical_power.12V',
    'name': '12V Electrical Power Port',
    'abbreviation': '12V',
    'type_of_port': 'pgefobjects:PortType.electrical_power',
    'parameters': {
       'V':
         {'value': 12,
          'mod_datetime': epoch,
          'units': 'V'}
          },
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortTemplate',
    'oid': 'pgefobjects:PortTemplate.electrical_power.5V',
    'description': '5V electrical power port',
    'id': 'electrical_power.5V',
    'name': '5V Electrical Power Port',
    'abbreviation': '5V',
    'type_of_port': 'pgefobjects:PortType.electrical_power',
    'parameters': {
       'V':
         {'value': 5,
          'mod_datetime': epoch,
          'units': 'V'}
          },
    'create_datetime': epoch,
    'mod_datetime': epoch
    },

{   '_cname': 'PortTemplate',
    'oid': 'pgefobjects:PortTemplate.electrical_power.3.3V',
    'description': '3.3V electrical power port',
    'id': 'electrical_power.3.3V',
    'name': '3.3V Electrical Power Port',
    'abbreviation': '3.3V',
    'type_of_port': 'pgefobjects:PortType.electrical_power',
    'parameters': {
       'V':
         {'value': 3.3,
          'mod_datetime': epoch,
          'units': 'V'}
          },
    'create_datetime': epoch,
    'mod_datetime': epoch
    }
]

core_objs = {so['oid'] : so for so in core}

# oids of reference Parameter Definitions -- used by the repository to identify
# ParameterDefinition objects that do not need to be synced with clients
ref_pd_oids = [d['oid'] for d in core
               if d['_cname'] == 'ParameterDefinition']

# oids of reference Product Types -- used to create DisciplineProductType
# objects to relate ALL ProductType objects to the Engineering discipline
ref_pt_oids = [d['oid'] for d in core
               if d['_cname'] == 'ProductType']

############################################################################
# Generate known DisciplineRole relationships by Discipline

# Systems Engineer Role object (related to multiple disciplines)
se_role_obj = core_objs['gsfc:Role.systems_engineer']

# Lead Engineer Role object (related to same disciplines as SE)
le_role_obj = core_objs['gsfc:Role.lead_engineer']

for discipline_oid in [
    'pgefobjects:Discipline.acs',
    'pgefobjects:Discipline.avionics',
    'pgefobjects:Discipline.flight_dynamics',
    'pgefobjects:Discipline.fsw',
    'pgefobjects:Discipline.i_and_t',
    'pgefobjects:Discipline.mechanical',
    'pgefobjects:Discipline.misson_ops',
    'pgefobjects:Discipline.orbital_debris',
    'pgefobjects:Discipline.power',
    'pgefobjects:Discipline.propulsion',
    'pgefobjects:Discipline.rf_comm',
    'pgefobjects:Discipline.radiation',
    'pgefobjects:Discipline.reliability',
    'pgefobjects:Discipline.systems',
    'pgefobjects:Discipline.thermal'
    ]:
    discipline_obj = core_objs[discipline_oid]
    role_oid = 'gsfc:Role.' + discipline_obj['id'] + '_engineer'
    role_obj = core_objs[role_oid]
    dr_oid = '.'.join(['pgefobjects:DisciplineRole', role_obj['id'],
                       discipline_obj['id']])
    dr_id = role_obj['id'] + '_to_' + discipline_obj['id']
    dr_name = role_obj['name'] + ' / ' + discipline_obj['name']
    core.append(
        dict(_cname='DisciplineRole', oid=dr_oid, id=dr_id, name=dr_name,
             related_role=role_obj['oid'],
             related_to_discipline=discipline_obj['oid']))

    # 'Systems Engineer' Role gets related to all disciplines
    # NOTE:  leave out 'systems' because it was assigned in previous loop
    if discipline_oid != 'pgefobjects:Discipline.systems':
        se_dr_oid = '.'.join(['pgefobjects:DisciplineRole', se_role_obj['id'],
                             discipline_obj['id']])
        se_dr_id = se_role_obj['id'] + '_to_' + discipline_obj['id']
        se_dr_name = 'Systems Engineer / ' + discipline_obj['name']
        core.append(
            dict(_cname='DisciplineRole', oid=se_dr_oid, id=se_dr_id,
                 name=se_dr_name,
                 related_role=se_role_obj['oid'],
                 related_to_discipline=discipline_obj['oid']))

    # 'Lead Engineer' Role gets related to all disciplines
    le_dr_oid = '.'.join(['pgefobjects:DisciplineRole', le_role_obj['id'],
                         discipline_obj['id']])
    le_dr_id = le_role_obj['id'] + '_to_' + discipline_obj['id']
    le_dr_name = 'Lead Engineer / ' + discipline_obj['name']
    core.append(
        dict(_cname='DisciplineRole', oid=le_dr_oid, id=le_dr_id,
             name=le_dr_name,
             related_role=le_role_obj['oid'],
             related_to_discipline=discipline_obj['oid']))

# For Lead Engineer and Systems Engineer roles, add a DisciplineRole
# relationship to the "engineering" meta-discipline so that they will be able
# to edit *ANY* product type (engineering has a DisciplineProductType
# relationship to every ProductType)

se_dr_oid = '.'.join(['pgefobjects:DisciplineRole', se_role_obj['id'],
                     'engineering'])
se_dr_id = se_role_obj['id'] + '_to_engineering'
se_dr_name = 'Systems Engineer / Engineering'
core.append(
    dict(_cname='DisciplineRole', oid=se_dr_oid, id=se_dr_id,
         name=se_dr_name,
         related_role=se_role_obj['oid'],
         related_to_discipline='pgefobjects:Discipline.engineering'))

le_dr_oid = '.'.join(['pgefobjects:DisciplineRole', le_role_obj['id'],
                     'engineering'])
le_dr_id = le_role_obj['id'] + '_to_engineering'
le_dr_name = 'Lead Engineer / Engineering'
core.append(
    dict(_cname='DisciplineRole', oid=le_dr_oid, id=le_dr_id,
         name=le_dr_name,
         related_role=le_role_obj['oid'],
         related_to_discipline='pgefobjects:Discipline.engineering'))

# End of generated DisciplineRole relationships
############################################################################

############################################################################
# Generate known DisciplineProductType relationships

# *ALL* ProductTypes are related to the "Engineering" discipline
eng_discipline_obj = core_objs['pgefobjects:Discipline.engineering']
for pt_oid in ref_pt_oids:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        eng_discipline_obj['id']])
    dpt_id = eng_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=eng_discipline_obj['oid']))

# ACS ProductTypes
acs_discipline_obj = core_objs['pgefobjects:Discipline.acs']
for pt_oid in [
    'pgefobjects:ProductType.attitude_control_system',
    'pgefobjects:ProductType.actuator',
    'pgefobjects:ProductType.star_tracker',
    'pgefobjects:ProductType.imu',
    'pgefobjects:ProductType.iru',
    'pgefobjects:ProductType.control_moment_gyro',
    'pgefobjects:ProductType.reaction_wheel',
    'pgefobjects:ProductType.momentum_wheel',
    'pgefobjects:ProductType.magnetic_torquer',
    'pgefobjects:ProductType.magnetometer',
    'pgefobjects:ProductType.digital_sun_sensor',
    'pgefobjects:ProductType.coarse_sun_sensor',
    'pgefobjects:ProductType.horizon_sensor'
    ]:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        acs_discipline_obj['id']])
    dpt_id = acs_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=acs_discipline_obj['oid']))

# Propulsion ProductTypes
prop_discipline_obj = core_objs['pgefobjects:Discipline.propulsion']
for pt_oid in [
    'pgefobjects:ProductType.propulsion_system',
    'pgefobjects:ProductType.tank',
    # 'pgefobjects:ProductType.oxidizer_tank',
    'pgefobjects:ProductType.pyro_isolation_valve',
    'pgefobjects:ProductType.propellant_filter',
    'pgefobjects:ProductType.manifold',
    'pgefobjects:ProductType.fill_drain_valve',
    'pgefobjects:ProductType.thruster',
    # 'pgefobjects:ProductType.propellant_tank',
    'pgefobjects:ProductType.power_processing_unit',
    'pgefobjects:ProductType.sep_engine',
    'pgefobjects:ProductType.sep_engine_gimbal'
    ]:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        prop_discipline_obj['id']])
    dpt_id = prop_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=prop_discipline_obj['oid']))

# Thermal ProductTypes
thermal_discipline_obj = core_objs['pgefobjects:Discipline.thermal']
for pt_oid in [
    'pgefobjects:ProductType.thermal_control_system',
    'pgefobjects:ProductType.actuator',
    'pgefobjects:ProductType.heater',
    'pgefobjects:ProductType.thermostat',
    'pgefobjects:ProductType.temperature_sensor',
    'pgefobjects:ProductType.thermal_controller',
    'pgefobjects:ProductType.multi_layer_insulation',
    'pgefobjects:ProductType.thermal_coating',
    'pgefobjects:ProductType.radiator_panel',
    'pgefobjects:ProductType.heat_pipe',
    'pgefobjects:ProductType.thermal_strap',
    'pgefobjects:ProductType.thermal_louver'
    ]:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        thermal_discipline_obj['id']])
    dpt_id = thermal_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=thermal_discipline_obj['oid']))

# Mechanical ProductTypes
mech_discipline_obj = core_objs['pgefobjects:Discipline.mechanical']
for pt_oid in [
    'pgefobjects:ProductType.mechanical_system',
    'pgefobjects:ProductType.mechanical_structure',
    'pgefobjects:ProductType.instrument_accomodation',
    'pgefobjects:ProductType.payload_attach_fitting',
    'pgefobjects:ProductType.solar_array_actuator',
    'pgefobjects:ProductType.actuator',
    'pgefobjects:ProductType.antenna_gimbal',
    'pgefobjects:ProductType.boom',
    'pgefobjects:ProductType.deployment_system'
    ]:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        mech_discipline_obj['id']])
    dpt_id = mech_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=mech_discipline_obj['oid']))

# Electrical Power ProductTypes
power_discipline_obj = core_objs['pgefobjects:Discipline.power']
for pt_oid in [
    'pgefobjects:ProductType.power_system',
    'pgefobjects:ProductType.solar_array',
    'pgefobjects:ProductType.solar_array_actuator',
    'pgefobjects:ProductType.battery',
    'pgefobjects:ProductType.rtg',
    'pgefobjects:ProductType.power_harness'
    ]:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        power_discipline_obj['id']])
    dpt_id = power_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=power_discipline_obj['oid']))

# Avionics (C&DH) ProductTypes
avionics_discipline_obj = core_objs['pgefobjects:Discipline.avionics']
for pt_oid in [
    'pgefobjects:ProductType.c_and_dh_system',   # C&DH System
    'pgefobjects:ProductType.board',
    'pgefobjects:ProductType.electronics_box',
    'pgefobjects:ProductType.comsec',
    'pgefobjects:ProductType.computer',
    'pgefobjects:ProductType.redundancy_management_unit'
    ]:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        avionics_discipline_obj['id']])
    dpt_id = avionics_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=avionics_discipline_obj['oid']))

# Comm ProductTypes
comm_discipline_obj = core_objs['pgefobjects:Discipline.rf_comm']
for pt_oid in [
    'pgefobjects:ProductType.communications_system',
    'pgefobjects:ProductType.omni_antenna',
    'pgefobjects:ProductType.medium_gain_antenna',
    'pgefobjects:ProductType.high_gain_antenna',
    'pgefobjects:ProductType.transponder',
    'pgefobjects:ProductType.transmitter',
    'pgefobjects:ProductType.receiver',
    'pgefobjects:ProductType.power_amplifier'
    ]:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        comm_discipline_obj['id']])
    dpt_id = comm_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=comm_discipline_obj['oid']))

# Systems ProductTypes
systems_discipline_obj = core_objs['pgefobjects:Discipline.systems']
for pt_oid in [
    'pgefobjects:ProductType.launch_vehicle',
    'pgefobjects:ProductType.spacecraft',
    'pgefobjects:ProductType.instrument',
    'pgefobjects:ProductType.attitude_control_system',
    'pgefobjects:ProductType.c_and_dh_system',   # C&DH System
    'pgefobjects:ProductType.communications_system',
    'pgefobjects:ProductType.mechanical_system',
    'pgefobjects:ProductType.electronics_box',
    'pgefobjects:ProductType.observatory',
    'pgefobjects:ProductType.power_system',
    'pgefobjects:ProductType.propulsion_system',
    'pgefobjects:ProductType.thermal_control_system'
    ]:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        systems_discipline_obj['id']])
    dpt_id = systems_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=systems_discipline_obj['oid']))

science_discipline_obj = core_objs['pgefobjects:Discipline.science']
for pt_oid in [
    'pgefobjects:ProductType.launch_vehicle',
    'pgefobjects:ProductType.spacecraft',
    'pgefobjects:ProductType.instrument'
    ]:
    pt_obj = core_objs[pt_oid]
    dpt_oid = '.'.join(['pgefobjects:DisciplineProductType', pt_obj['id'],
                        science_discipline_obj['id']])
    dpt_id = science_discipline_obj['id'] + '_to_' + pt_obj['id']
    core.append(
        dict(_cname='DisciplineProductType', oid=dpt_oid, id=dpt_id,
             relevant_product_type=pt_obj['oid'],
             used_in_discipline=science_discipline_obj['oid']))

# End of generated DisciplineProductType relationships
############################################################################
# Deprecated reference data -- will be deleted by orb.load_reference_data()
deprecated = [
    'pgefobjects:ProductType.cdh_electronics_box',
    'pgefobjects:DisciplineProductType.cdh_electronics_box.avionics',
    'pgefobjects:ProductType.power_system_electronics_box',
    'pgefobjects:DisciplineProductType.power_system_electronics_box.power',
    'pgefobjects:ProductType.primary_structure',
    'pgefobjects:DisciplineProductType.primary_structure.mechanical',
    'pgefobjects:ProductType.secondary_structure',
    'pgefobjects:DisciplineProductType.secondary_structure.mechanical',
    'pgefobjects:ProductType.main_cdh_electronics_box',
    'pgefobjects:DisciplineProductType.main_cdh_electronics_box.avionics',
    'pgefobjects:ProductType.aux_cdh_electronics_box',
    'pgefobjects:DisciplineProductType.aux_cdh_electronics_box.avionics'
    ]
############################################################################
"""
Technology Readiness Levels (TRL)

Source:  NASA NPR 7123.1B, Appendix E
"""
trls = [
{   'exit': 'Peer reviewed publication of research underlying the proposed concept/application.',
    'hw_desc': 'Scientific knowledge generated underpinning hardware technology concepts/applications.',
    'name': 'Basic Principles',
    'sw_desc': 'Scientific knowledge generated underpinning basic properties of software architecture and mathematical formulation.',
    'tech_mat': 'Basic principles observed and reported',
    'trl': '1'},
{   'exit': 'Documented description of the application/concept that addresses feasibility and benefit.',
    'hw_desc': 'Invention begins, practical applications is identified but is speculative, no experimental proof or detailed analysis is available to support the conjecture.',
    'name': 'Early Design',
    'sw_desc': 'Practical application is identified but is speculative; no experimental proof or detailed analysis is available to support the conjecture. Basic properties of algorithms, representations, and concepts defined. Basic principles coded. Experiments performed with synthetic data.',
    'tech_mat': 'Technology concept and/or application formulated',
    'trl': '2'},
{   'exit': 'Documented analytical/experimental results validating predictions of key parameters.',
    'hw_desc': 'Analytical studies place the technology in an appropriate context and laboratory demonstrations, modeling and simulation validate analytical prediction.',
    'name': 'Proof-of-Concept',
    'sw_desc': 'Development of limited functionality to validate critical properties and predictions using non-integrated software components.',
    'tech_mat': 'Analytical and experimental critical function and/or characteristic proof-of- concept',
    'trl': '3'},
{   'exit': 'Documented test performance demonstrating agreement with analytical predictions. Documented definition of relevant environment.',
    'hw_desc': 'A low fidelity system/component breadboard is built and operated to demonstrate basic functionality and critical test environments, and associated performance predictions are defined relative to final operating environment.',
    'name': 'Lab Tested Hardware',
    'sw_desc': 'Key, functionality critical software components are integrated and functionally validated to establish interoperability and begin architecture development. Relevant environments defined and performance in the environment predicted.',
    'tech_mat': 'Component and/or breadboard validation in laboratory environment.',
    'trl': '4'},
{   'exit': 'Documented test performance demonstrating agreement with analytical predictions. Documented definition of scaling requirements.',
    'hw_desc': 'A medium fidelity system/component brassboard is built and operated to demonstrate overall performance in a simulated operational environment with realistic support elements that demonstrate overall performance in critical areas. Performance predictions are made for subsequent development phases.',
    'name': 'Components Only',
    'sw_desc': 'End-to-end software elements implemented and interfaced with existing systems/simulations conforming to target environment. End-to-end software system tested in relevant environment, meeting predicted performance. Operational environment performance predicted. Prototype implementations developed.',
    'tech_mat': 'Component and/or breadboard validation in relevant environment.',
    'trl': '5'},
{   'exit': 'Documented test performance demonstrating agreement with analytical predictions.',
    'hw_desc': 'A high fidelity system/component prototype that adequately addresses all critical scaling issues is built and operated in a relevant environment to demonstrate operations under critical environmental conditions.',
    'name': 'Prototype Subsystems',
    'sw_desc': 'Prototype implementations of the software demonstrated on full-scale, realistic problems. Partially integrated with existing hardware/software systems. Limited documentation available. Engineering feasibility fully demonstrated.',
    'tech_mat': 'System/sub-system model or prototype demonstration in a relevant environment.',
    'trl': '6'},
{   'exit': 'Documented test performance demonstrating agreement with analytical predictions.',
    'hw_desc': 'A high fidelity engineering unit that adequately addresses all critical scaling issues is built and operated in a relevant environment to demonstrate performance in the actual operational environment and platform (ground, airborne, or space).',
    'name': 'Engineering Test Units',
    'sw_desc': 'Prototype software exists having all key functionality available for demonstration and test. Well integrated with operational hardware/software systems demonstrating operational feasibility. Most software bugs removed. Limited documentation available.',
    'tech_mat': 'System prototype demonstration in an operational environment.',
    'trl': '7'},
{   'exit': 'Documented test performance verifying analytical predictions.',
    'hw_desc': 'The final product in its final configuration is successfully demonstrated through test and analysis for its intended operational environment and platform (ground, airborne, or space).',
    'name': 'Qualified Hardware',
    'sw_desc': 'All software has been thoroughly debugged and fully integrated with all operational hardware and software systems. All user documentation, training documentation, and maintenance documentation completed. All functionality successfully demonstrated in simulated operational scenarios. Verification and validation completed.',
    'tech_mat': 'Actual system completed and flight qualified through test and demonstration.',
    'trl': '8'},
{   'exit': 'Documented mission operational results.',
    'hw_desc': 'The final product is successfully operated in an actual mission.',
    'name': 'Flight Proven Hardware',
    'sw_desc': 'All software has been thoroughly debugged and fully integrated with all operational hardware and software systems. All documentation has been completed. Sustaining software support is in place. System has been successfully operated in the operational environment.',
    'tech_mat': 'Actual system flight proven through successful mission operations.',
    'trl': '9'}
    ]

