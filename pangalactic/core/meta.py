# -*- coding: utf-8 -*-
"""
Pan Galactic meta characteristics and utilities
"""
import codecs
import json
import string
import unicodedata

from pangalactic.core       import datatypes
from pangalactic.core.units import in_si

# NOTE:  As a "simplest thing that works", this module adds interface default
# settings that reference the classes of the PGEF ontology (which is not an
# appropriate vehicle to specify interface characteristics).
#
# Ultimately both aspects will be loosely coupled via a "master model", but
# that architecture is still being worked out.

# PGXN_REQD:  Properties that are validated by PgxnObject to be non-empty
# SEE ALSO:  PGXN_HIDE and PGXN_MASK (fields never shown for a class -- defined
# below)
IDENTITY = ['id', 'id_ns', 'name', 'abbreviation', 'description']
PRODUCT_ID = ['id', 'version', 'name', 'description']
PGXN_REQD = dict(
    HardwareProduct=['name', 'description', 'owner', 'product_type'],
    ParameterDefinition=['id', 'name', 'description', 'dimensions',
                         'range_datatype'],
    Product=['id', 'name', 'description', 'owner'],
    Project=IDENTITY,
    ProductType=IDENTITY,
    Requirement=(IDENTITY + ['rationale']),
    Test=(IDENTITY + ['verifies', 'purpose'])
    )

# MAIN_VIEWS:  Class-specific default fields for the PgxnObject "main" tab and
# "db" mode tables.  This dictionary is intended to be added to and/or
# overridden by app-specific settings defined in the 'pangalactic.config'
# module-level dictionary.
# TODO:  support for field "aliases" (a.k.a. "display names")
SYSTEM = ['version', 'version_sequence', 'iteration']
MAIN_VIEWS = dict(
    Activity=['name', 'description', 'owner', 'activity_type', 'of_system',
              'sub_activity_of'],
    Acu=['id', 'assembly', 'component', 'quantity', 'reference_designator',
         'assembly_level', 'product_type_hint'],
    Discipline=IDENTITY,
    DisciplineProductType=['id', 'used_in_discipline', 'relevant_product_type'],
    DisciplineRole=['id', 'related_to_discipline', 'related_role'],
    DocumentReference=['id', 'name', 'document', 'related_item'],
    Flow=['id', 'start_port', 'start_port_context', 'end_port',
          'end_port_context'],
    HardwareProduct=(PGXN_REQD['Product']
                     + ['id_ns', 'abbreviation', 'product_type', 'public']
                     + SYSTEM),
    Mission=(IDENTITY + ['owner']),
    Model=(IDENTITY + ['type_of_model', 'of_thing']),
    ModelFamily=IDENTITY,
    ModelType=(IDENTITY + ['model_type_family']),
    Organization=IDENTITY,
    Person=(IDENTITY + ['last_name', 'mi_or_name', 'first_name',
                        'employer', 'org']),
    ParameterDefinition=(IDENTITY + ['range_datatype', 'dimensions']),
    ParameterRelation=['id', 'referenced_relation', 'correlates_parameter'],
    Port=['id', 'name', 'of_product', 'type_of_port'],
    Product=(PGXN_REQD['Product']
             + ['id_ns', 'abbreviation', 'public']
             + SYSTEM),
    ProductType=IDENTITY,
    ProductTypeParameterDefinition=['id', 'used_in_product_type',
                                    'parameter_definition'],
    Project=(IDENTITY + ['parent_organization']),
    ProjectSystemUsage=['id', 'project', 'system', 'system_role'],
    Relation=(IDENTITY + ['formulation']),
    RepresentationFile=(IDENTITY + ['of_object']),
    Requirement=['id', 'rqt_level', 'name', 'rqt_type', 'rqt_compliance',
                 'description', 'rationale', 'justification', 'comment'],
    RoleAssignment=['id', 'assigned_role', 'assigned_to',
                    'role_assignment_context'],
    Test=(IDENTITY + ['verifies', 'purpose', 'comment']),
    )

# PGXN_VIEWS:  Default fields/ordering for the PgxnObject "info", "narrative"
# and "admin" tabs
PGXN_VIEWS = dict(
    info=['public', 'computable_form', 'rqt_type', 'rqt_constraint_type',
          'rqt_dimensions', 'rqt_target_value', 'rqt_tolerance',
          'rqt_tolerance_type', 'rqt_tolerance_lower', 'rqt_tolerance_upper',
          'rqt_maximum_value', 'rqt_minimum_value', 'validated',
          'verification_method'],
    narrative=['comment', 'rationale', 'purpose', 'rqt_subject',
               'rqt_predicate', 'rqt_object'],
    admin=['oid', 'url', 'creator', 'create_datetime', 'modifier',
           'mod_datetime'])

# PGXN_PARAMETERS:  preferred ordering for parameters in PgxnObject parameter
# forms
PGXN_PARAMETERS = ['m', 'P', 'R_D', 'Cost', 'height', 'width',
                   'depth', 'CoM_X', 'CoM_Y', 'CoM_Z']

# DEFAULT_CLASS_DATA_ELEMENTS:  default data elements of objects by class
DEFAULT_CLASS_DATA_ELEMENTS = {'HardwareProduct': ['Vendor', 'TRL',
                                                   'reference_missions']}

# DEFAULT_CLASS_PARAMETERS:  default parameters of objects by class
DEFAULT_CLASS_PARAMETERS = {'Activity': ['duration', 't_start', 't_end'],
                            'Mission': ['duration'],
                            'HardwareProduct': [
                                'm', 'm[CBE]', 'm[Ctgcy]', 'm[MEV]',
                                'P', 'P[CBE]', 'P[Ctgcy]', 'P[MEV]',
                                'P[peak]', 'P[standby]', 'P[survival]',
                                'T[operational_max]', 'T[operational_min]',
                                'T[survival_max]', 'T[survival_min]',
                                'R_D', 'R_D[CBE]', 'R_D[Ctgcy]',
                                'R_D[MEV]', 'height', 'width', 'depth', 'Cost']}

# DEFAULT_DASHBOARD_SCHEMAS:  default sets of parameters shown in dashboards
DEFAULT_DASHBOARD_SCHEMAS = {
        'MEL' :
            ['m[CBE]', 'm[Ctgcy]', 'm[MEV]',
             'P[CBE]', 'P[Ctgcy]', 'P[MEV]', 'P[peak]',
             'R_D[CBE]', 'R_D[Ctgcy]', 'R_D[MEV]',
             'Vendor', 'Cost', 'TRL'],
        'Mass':
            ['m[CBE]', 'm[Ctgcy]', 'm[MEV]'],
        'Power':
            ['P[CBE]', 'P[Ctgcy]', 'P[MEV]', 'P[peak]', 'P[standby]',
             'P[survival]', 'Area_active', 'Area_substrate'],
        'Data Rates':
            ['R_D[CBE]', 'R_D[Ctgcy]', 'R_D[MEV]'],
        'Mechanical':
            ['m[CBE]', 'm[Ctgcy]', 'm[MEV]', 'height', 'width', 'depth'],
        'Thermal':
            ['T[operational_max]', 'T[operational_min]', 'T[survival_max]',
             'T[survival_min]', 'P[CBE]', 'P[Ctgcy]', 'P[MEV]', 'P[peak]',
             'P[survival]'],
        'System Resources':
            ['m[CBE]', 'm[Ctgcy]', 'm[MEV]', 'm[NTE]', 'm[Margin]',
             'P[CBE]', 'P[Ctgcy]', 'P[MEV]', 'P[peak]', 'P[NTE]',
             'P[Margin]', 'R_D[CBE]', 'R_D[Ctgcy]', 'R_D[MEV]',
             'R_D[NTE]', 'R_D[Margin]']
        }

# DEFAULT_PRODUCT_TYPE_DATA_ELMTS:  default data elements by ProductType id
DEFAULT_PRODUCT_TYPE_DATA_ELMTS = {
    'heater':
        ['mounting_material', # acrylic adhesive
         ],
    'heat_pipe':
        ['working_fluid', # Ammonia, Ethane
         'extrusion'     # Aluminum
         ],
    'multi_layer_insulation':
        ['size',          # Large, Small, Cable Wrap
         'layup'          # Number of Layers
         ],
    'thermal_fabric':
        ['material'
         ],
    'thermal_louver':
        ['temp_range_closed_open'
         ],
    }

# DEFAULT_PRODUCT_TYPE_PARAMETERS:  default parameters by ProductType id
DEFAULT_PRODUCT_TYPE_PARAMETERS = {
    'antenna': ['Gain_antenna'],
    'omni_antenna': ['Gain_antenna'],
    'medium_gain_antenna': ['Gain_antenna'],
    'heater': ['Density_areal', 'T[max]', 'T[min]'],
    'heat_pipe': ['d', 'Density_linear', 'FreezingPoint',
                  'HeatTransportCapacity'],
    'high_gain_antenna': ['Gain_antenna'],
    'multi_layer_insulation': ['Density_areal'],
    'power_amplifier': ['Gain'],
    'optical_component': ['RoC', 'K'],
    'temperature_sensor': ['T[max]', 'T[min]'],
    'thermal_coating': ['Density_areal', 'Emittance', 'Absorptance',
                        'thickness'],
    'thermal_fabric': ['Density_areal', 'Emittance', 'Absorptance',
                       'thickness'],
    'thermal_louver': ['Density_areal', 'EffectiveEmittance_closed',
                       'EffectiveEmittance_open'],
    'thermostat': ['T[max]', 'T[min]'],
    'transponder': ['f_downlink', 'f_uplink'],
    'transmitter': ['f_downlink', 'f_uplink'],
    'receiver': ['f_downlink', 'f_uplink']
    }

DEFAULT_EDITABLE_POWER_CONTEXTS = ['nominal', 'peak', 'standby', 'survival']

# NOTE: these parameters go into the Acu that connects an optical component to
# an optical system -- for now, just keep them handy ...

OPTICAL_SYSTEM_PARAMETERS = [
    'X_vertex',
    'Y_vertex',
    'Z_vertex',
    'RotX_vertex',
    'RotY_vertex',
    'RotZ_vertex',
    'dRMSWFE_dx', 'dRMSWFE_dy', 'dRMSWFE_dz',
    'dRMSWFE_rx', 'dRMSWFE_ry', 'dRMSWFE_rz',
    'dLOSx_dx', 'dLOSx_dy', 'dLOSx_dz',
    'dLOSx_rx', 'dLOSx_ry', 'dLOSx_rz',
    'dLOSy_dx', 'dLOSy_dy', 'dLOSy_dz',
    'dLOSy_rx', 'dLOSy_ry', 'dLOSy_rz']

# PGXN_PLACEHOLDERS:  Placeholder text for fields in PgxnObject forms
PGXN_PLACEHOLDERS = {'id': 'unique identifier; no spaces',
                     'id_ns': 'namespace for id',
                     'name': '~25 characters; spaces ok',
                     'version': 'blank ok; id+version must be unique'
                     }

# PGXN_OBJECT_MENU:  Classes that Pangalaxian "New Object" dialog offers to
# create [NOT IMPLEMENTED YET]
PGXN_OBJECT_MENU = [
                    'Activity',
                    'Document',
                    'EeePart',
                    'Model',
                    'Mission',
                    'ParameterDefinition',
                    'Product',
                    'ProductInstance',
                    'HardwareProduct',
                    'Software',
                    'PartsList',
                    'Project'
                    ]

# PGXN_ADMIN_MENU:  Classes for which Pangalaxian has ADMIN menu items
# [NOT IMPLEMENTED YET]
PGXN_ADMIN_MENU = [
                    'Organization',
                    'Person',
                    'Project',
                    'RoleAssignment',
                    'Role',
                    ]

# M2M:  Reified many-to-many relationships ("join classes")
#       computed inverse (non-functional) properties
# format is {
       # *** M2M:  m2m relationship join class name
#      property name : {'domain' : class name,
#                       'range'  : m2m relationship join class name},
#            ...}
M2M = {
       # *** M2M:  Acu (Assembly Component Usage)
       # inverse of 'assembly'
       'components' :           {'domain' : 'Product',
                                 'range'  : 'Acu'},
       # inverse of 'component'
       # complementary to 'components'
       'where_used' :           {'domain' : 'Product',
                                 'range'  : 'Acu'},

       # *** M2M:  Qacu (Quantified Assembly Component Usage)
       # inverse of ''
       'q_components' :         {'domain' : 'ContinuousProduct',
                                 'range'  : 'Qacu'},
       # inverse of 'q_component'
       # complementary to 'q_components'
       'q_where_used' :         {'domain' : 'ContinuousProduct',
                                 'range'  : 'Qacu'},

       # *** M2M:  RoleAssignment
       # inverse of 'assigned_to'
       'roles' :                {'domain' : 'Person',
                                 'range'  : 'RoleAssignment'},
       # inverse of 'assigned_role'
       # complementary to 'roles'
       'assignments_of_role' :  {'domain' : 'Role',
                                 'range'  : 'RoleAssignment'},

       # *** M2M:  RequirementAncestry
       # inverse of 'parent_requirement'
       # complementary to 'parent_requirements'
       'child_requirements' :     {'domain' : 'Requirement',
                                   'range'  : 'RequirementAncestry'},
       # inverse of 'child_requirement'
       # complementary to 'child_requirements'
       'parent_requirements' :    {'domain' : 'Requirement',
                                   'range'  : 'RequirementAncestry'},

       # *** M2M:  VerificationTest
       # inverse of 'test'
       # complementary to 'verification_tests'
       'verifies_requirements' :  {'domain' : 'Test',
                                   'range'  : 'VerificationTest'},
       # inverse of 'verifies'
       # complementary to 'verifies_requirements'
       'verification_tests' :     {'domain' : 'Requirement',
                                   'range'  : 'VerificationTest'},

       # *** M2M:  ProjectSystemUsage
       # inverse of 'system'
       # complementary to 'systems'
       'projects_using_system': {'domain' : 'Product',
                                 'range'  : 'ProjectSystemUsage'},
       # inverse of 'project'
       # complementary to 'projects_using_system'
       'systems':               {'domain' : 'Project',
                                 'range'  : 'ProjectSystemUsage'},

       # *** M2M:  ParameterRelation
       # inverse of 'correlates_parameter'
       # complementary to 'correlates_parameters'
       'is_correlated_by':         {'domain' : 'ParameterDefinition',
                                    'range'  : 'ParameterRelation'},
       # inverse of 'referenced_relation'
       # complementary to 'is_correlated_by'
       'correlates_parameters':    {'domain' : 'Relation',
                                    'range'  : 'ParameterRelation'},

       # *** M2M:  DisciplineProductType
       # inverse of 'relevant_product_type'
       # complementary to 'used_in_discipline'
       'used_in_disciplines' : {
                     'domain' : 'ProductType',
                     'range'  : 'DisciplineProductType'},
       # inverse of 'used_in_discipline'
       # complementary to 'relevant_product_type'
       'relevant_product_types' : {
                     'domain' : 'Discipline',
                     'range'  : 'DisciplineProductType'},

       # *** M2M:  DocumentReference
       # inverse of 'related_item'
       # complementary to 'item_relationships'
       'doc_references' : {
                     'domain' : 'Modelable',
                     'range'  : 'DocumentReference'},
       # inverse of 'document'
       # complementary to 'related_item'
       'item_relationships' : {
                     'domain' : 'Document',
                     'range'  : 'DocumentReference'},

       # *** M2M:  ProductTypeParameterDefinition
       # inverse of 'used_in_product_type'
       # complementary to 'used_in_product_types'
       'parameter_definitions' : {
                     'domain' : 'ProductType',
                     'range'  : 'ProductTypeParameterDefinition'},
       # inverse of 'parameter_definition'
       # complementary to 'parameter_definitions'
       'used_in_product_types' : {
                     'domain' : 'ParameterDefinition',
                     'range'  : 'ProductTypeParameterDefinition'}
       }

# Special properties that get a customized droppable interface to enable
# populating a one-to-many relationship with objects.
# Format is {property name : one2m relationship range class name}
ONE2M = {
         # inverse of 'of_system'
         'activities' :           {'domain' : 'Modelable',
                                   'range'  : 'Activity'},
         # inverse of 'creator'
         'created_objects' :      {'domain' : 'Actor',
                                   'range'  : 'Modelable'},
         # inverse of 'of_thing'
         'has_models' :           {'domain' : 'Modelable',
                                   'range'  : 'Model'},
         # inverse of 'of_object'
         'has_files' :            {'domain' : 'DigitalProduct',
                                   'range'  : 'RepresentationFile'},
         # DEPRECATED:  inverse of 'allocated_to_function'
         # NEW:  inverse of 'allocated_to'
         'allocated_requirements' : {'domain' : 'Modelable',
                                     'range'  : 'Requirement'},
         # inverse of 'allocated_to_system'
         # 'system_requirements' :  {'domain' : 'ProjectSystemUsage',
                                   # 'range'  : 'Requirement'},
         # inverse of 'role_assignment_context'
         'organizational_role_assignments' : {'domain' :
                                              'Organization',
                                   'range' :  'RoleAssignment'},
         # inverse of 'owner'
         'owned_objects' :        {'domain' : 'Organization',
                                   'range'  : 'ManagedObject'},
         # inverse of 'of_product'
         'ports' :                {'domain' : 'Product',
                                   'range'  : 'Port'},
         # inverse of 'product_type'
         'products_of_type' :     {'domain' : 'ProductType',
                                   'range'  : 'Product'},
         # inverse of 'parent_parts_list'
         'parts_list_items' :     {'domain' : 'PartsList',
                                   'range'  : 'PartsListItem'},
         # inverse of 'parent_organization'
         'sub_organizations' :    {'domain' : 'Organization',
                                   'range'  : 'Organization'}
         }


# PGXN_HIDE:  Fields not to be shown for any object
# [TODO:  implement support for these in PgxnObject editor]
PGXN_HIDE = list(ONE2M.keys()) + list(M2M.keys())

# PGXN_MASK:  Fields that should not be displayed for the specified classes in
# the object editor
PGXN_MASK = dict(
    DataElementDefinition=(PGXN_HIDE + ['owner']),
    HardwareProduct=(PGXN_HIDE + ['frozen']),
    ParameterDefinition=(PGXN_HIDE + ['base_parameters', 'computed_by_default',
                         'generating_function', 'used_in_disciplines']),
    Requirement=(PGXN_HIDE + ['fsc_code', 'has_models', 'ports',
                 'product_type', 'specification_number']),
    Test=(PGXN_HIDE + ['fsc_code', 'product_type'])
    )

# PGXN_DATA_VIEW:  minimal set of Data Elements to be displayed in the object
# editor
PGXN_DATA_VIEW = [
                  'TRL',
                  'directionality',
                  'Vendor'
                  ]

# PGXN_HIDE_PARMS:  Subclasses of Modelable for which 'parameters' and 'data'
# panels should be hidden
PGXN_HIDE_PARMS = [
                   'Actor',
                   'Acu',
                   'DataElementDefinition',
                   'Organization',
                   'ParameterDefinition',
                   'ParameterRelation',
                   'Person',
                   'ProductRequirement',
                   'ProductTypeParameterDefinition',
                   'Project',
                   'ProjectSystemUsage',
                   'RepresentationFile',
                   'RoleAssignment'
                   ]

# SELECTION_VIEWS:  Class-specific default sets of columns for tabular display
# of objects in the foreign key object selection dialog for PgxnObject
SELECTION_VIEWS = dict(
    Domain=['id', 'description']
    )

# SELECTION_FILTERS:  class names of the valid objects to be included in the
# tabular display of objects in the foreign key object selection dialog for
# PgxnObject
SELECTION_FILTERS = dict(
    owner=['Project', 'Organization'],
    product_type_hint=['ProductType'],
    product_type=['ProductType']
    )

def intconv(val):
    """
    Return supplied value cast to an integer. This is a workaround for int()
    not liking exponential notation, so for example '1e6' can be converted to
    an int.
    """
    return int(float(val or 0))

# SELECTABLE_VALUES:  Dictionaries of values for Properties or Parameters with
# a finite range of selectable values -- the form is:
# ([combo-box string value] : value)
SELECTABLE_VALUES = dict(
    range_datatype=dict([
        ('float', float),
        ('int', intconv),
        ('text', str),
        ('str', str),
        ('boolean', bool),
        ('array', dict)]),
    dimensions=dict(
        [(dim, dim) for dim in in_si]),
    directionality=dict([
        # null -> bidirectional
        ('', ''),
        ('input', 'input'),
        ('output', 'output')
        ]),
    rqt_type=dict([
        ('functional', 'functional'),
        ('performance', 'performance')]),
    rqt_compliance=dict([
        ('None', 'None'),
        ('Partial', 'Partial'),
        ('Full', 'Full')])
        )

# TEXT_PROPERTIES:  Properties that get a TextWidget interface
TEXT_PROPERTIES = ['comment', 'description', 'justification', 'rationale',
                   'purpose']

# NUMERIC_FORMATS:  Formatting used to display numbers in UI
NUMERIC_FORMATS = ['Thousands Commas', 'No Commas', 'Scientific Notation']

# NUMERIC_PRECISION:  Maximum precision assumed for parameter values
NUMERIC_PRECISION = ['3', '4', '5', '6', '7', '8', '9']

# Default ordering of the important ManagedObject properties
PGEF_PROPS_ORDER = [
            'oid',
            'id',
            'id_ns',
            'name',
            'description',
            'version',
            'iteration',
            'version_sequence',
            'owner',
            'creator',
            'comment',
            'create_datetime',
            'modifier',
            'mod_datetime',
            'url',
            'abbreviation'
            ]

# Default ordering and naming of dimensions (used in sorting parameters)
PGEF_DIMENSION_ORDER = {
            'mass': 'Mass',
            'power': 'Power',
            'bitrate': 'Data Rate',
            'length': 'Length',
            'temperature': 'Temperature',
            'area': 'Area',
            'moment of inertia': 'Moment of Inertia',
            'frequency': 'Frequency',
            'decibels': 'Gain',
            'decibels-isotropic': 'Antenna Gain',
            'electrical potential': 'Voltage',
            'time': 'Time',
            'substance': 'Moles',
            'money': 'Cost',
            '': 'Dimensionless',
            None: 'Dimensionless',
            'None': 'Dimensionless',
            'dimensionless': 'Dimensionless',
            }
all_dims = {dim: dim.title() for dim in in_si
            if dim and dim not in PGEF_DIMENSION_ORDER}
PGEF_DIMENSION_ORDER.update(all_dims)

# max length of string fields (default: 80)
MAX_LENGTH = {
            'abbreviation': 50,
            'id': 150,
            'name': 150,
            'url': 250,
            }

# Default column widths (in pixels) for specified properties
PGEF_COL_WIDTHS = {
            'abbreviation': 100,
            'creator': 100,
            'create_datetime': 100,
            'comment': 200,
            'description': 200,
            'frozen': 50,
            'id': 200,
            'id_ns': 100,
            'iteration': 50,
            'justification': 200,
            'modifier': 100,
            'mod_datetime': 100,
            'name': 200,
            'org': 200,
            'owner': 100,
            'oid': 100,
            'product_type': 100,
            'purpose': 250,
            'range_datatype': 50,
            'rationale': 200,
            'rqt_compliance': 100,
            'rqt_level': 50,
            'rqt_type': 100,
            'text': 300,
            'url': 100,
            'version': 50,
            'version_sequence': 50
            }

# Properties displayed as READ-ONLY by the PgxnObject viewer/editor
# TODO:  do this in a configurable way, as part of the Schemas
# TODO:  for m2m attributes, these may eventually become editable, when
# PgxnObject implements that capability
READONLY = [
            'allocated_to', # m2m (Requirement:Modelable)
            # DEPRECATED: allocated_to_[x] is just 'allocated_to' now
            # 'allocated_to_functions', # m2m (Requirement:Acu)
            # 'allocated_to_systems', # m2m (Requirement:ProjectSystemUsage)
            'creator',          #  "   "    "   "
            'create_datetime',  # tds
            'has_models',       # inverse of 'of_thing' property of Model
            'iteration',
            'modifier',         # set from user id
            'mod_datetime',     # tds
            'of_thing',         # inverse of 'of_thing' property of Model
            'oid',              # generated (uuid) at creation-time
            'ports',            # fk (inv. of Port.of_product)
            # 'product_type',     # fk (property of Product -- set when created)
            'projects_using_system', # m2m (ProjectSystemUsage)
            'satisfies',        # m2m (Product:ProductRequirement)
            'type_of_port',     # PortType (can't be changed once Port created)
            'version_sequence',
            'where_used'        # m2m (Acu)
            ]

# This is a temporary way of filtering namespaces, just until a more rational
# way is implemented

READONLYNS = [
              'pgef',
              'pgefobjects',
              'pgeftest',
              'pgeftesttmp',
              'owl',
              'rdf',
              'rdfs',
              'dc',
              'dcterms',
              'daml',
              'xml',
              'xsd'
              ]

def asciify(u):
    """
    "Intelligently" convert a unicode string to the ASCII character set --
    a.k.a. "The Stupid American", a.k.a. "The UNICODE Hammer".  Its main
    purpose is to convert things that might be used in Python identifiers so
    they can be typed on an en-us encoded keyboard!

    Credit: http://code.activestate.com/recipes/251871/ (this is not that
    recipe but an elegant one-liner from one of the comments on the recipe).

    Args:
        u (str or bytes): input value

    Returns:
        str
    """
    # Python 3: returns utf-8 string
    if isinstance(u, str):
        return unicodedata.normalize('NFKD', u).encode(
                                'ASCII', 'ignore').decode('utf-8')
    elif isinstance(u, bytes):
        return u.decode('utf-8')
    # allow only printable chars
    printable = set(string.printable)
    clean = filter(lambda x: x in printable, str(u))
    return clean


def property_to_field(name, pe):
    """
    Create a field dict from a property extract.  The field dict has the
    following form (terminology adopted from django-metaservice api):

    {
     'id'            : [the name of the field],
     'id_ns'         : [namespace in which name of the field exists],
     'field_type'    : [the field type, a SqlAlchemy class],
     'local'         : [bool:  True -> locally defined; False -> inherited],
     'related_cname' : [for fk fields, name of the related class],
     'functional'    : [bool:  True -> single-valued],
     'range'         : [python datatype name or, if fk, related class name],
     'inverse_functional' : [bool:  True -> one-to-one],
     'is_inverse'    : [bool:  True -> property is an inverse ("backref")],
     'inverse_of'    : [name of property of which this one is an inverse],
     'choices'       : [choices list -- i.e., a discrete range],
     'max_length'    : [maximum length of a string field],
     'null'          : [bool:  whether the field can be null],
     'editable'      : [bool:  opposite of read-only],
     'unique'        : [bool:  same as the sql concept],
     'external_name' : [name displayed in user interfaces],
     'definition'    : [definition of the field],
     'help_text'     : [extra help text, in addition to definition],
     'db_column'     : [name of the db column (default is field name)]
    }

    The 'fields' key in a schema dict will consist of a dict that maps
    field names to field dicts of this form.
    """
    field = {}
    field['id'] = pe['id']
    field['id_ns'] = pe['id_ns']
    field['definition'] = pe['definition']
    field['functional'] = pe['functional']
    field['range'] = pe['range']
    field['editable'] = not name in READONLY
    field['external_name'] = ' '.join(pe['id'].split('_'))
    if pe['is_datatype']:
        field['field_type'] = datatypes[(pe['is_datatype'],
                                         pe['range'],
                                         pe['functional'])]
        field['is_inverse'] = False
        field['inverse_of'] = ''
        field['max_length'] = MAX_LENGTH.get(pe['id'], 80)
    else:
        field['field_type'] = 'object'
        field['related_cname'] = pe['range']
        field['is_inverse'] = pe['is_inverse']
        field['inverse_of'] = pe['inverse_of']
    return field

def dump_metadata(extr, fpath):
    """
    JSON-serialize an extract and write it utf-8-encoded into file.
    """
    f = codecs.open(fpath, 'w', 'utf-8')
    json.dump(extr, f, sort_keys=True, indent=4, ensure_ascii=True)
    f.close()

def load_metadata(fpath):
    """
    Read and deserialize a utf-8-encoded JSON-serialized extract from a file.
    """
    f = codecs.open(fpath, 'r', 'utf-8')
    data = f.read()
    f.close()
    return json.loads(data)

