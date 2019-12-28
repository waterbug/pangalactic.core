# -*- coding: utf-8 -*-
"""
Pan Galactic meta characteristics
"""
# NOTE:  As a "simplest thing that works", this module adds interface default
# settings that reference the classes of the PGEF ontology (which is not an
# appropriate vehicle to specify interface characteristics).
#
# Ultimately both aspects will be loosely coupled via a "master model", but
# that architecture is still being worked out.

from collections import OrderedDict
from pangalactic.core.units import in_si

# PGXN_REQD:  Properties that are validated by PgxnObject to be non-empty
# SEE ALSO:  PGXN_HIDE and PGXN_MASK (fields never shown for a class -- defined
# below)
IDENTITY = ['id', 'name', 'url', 'description']
PRODUCT_ID = ['id', 'version', 'name', 'url', 'description']
PGXN_REQD = dict(
    HardwareProduct=(PRODUCT_ID + ['owner', 'product_type']),
    ParameterDefinition=['id', 'name', 'description', 'dimensions',
                         'range_datatype'],
    Project=IDENTITY,
    ProductType=IDENTITY,
    Requirement=(IDENTITY + ['rationale']),
    Test=(IDENTITY + ['verifies', 'purpose'])
    )

# MAIN_VIEWS:  Class-specific default fields for the PgxnObject "main" tab and
# ObjectTable.  This dictionary is intended to be added to and/or overridden by
# app-specific settings defined in the 'pangalactic.config' module-level
# dictionary.
# TODO:  support for field "aliases" (a.k.a. "display names")
SYSTEM = ['version_sequence', 'iteration', 'frozen', 'derived_from']
MAIN_VIEWS = dict(
    Activity=(IDENTITY + ['activity_type', 'activity_of']),
    Acu=['id', 'assembly', 'component', 'quantity', 'reference_designator',
         'assembly_level', 'product_type_hint'],
    Discipline=IDENTITY,
    DisciplineProductType=['used_in_discipline', 'relevant_product_type'],
    DisciplineRole=['related_to_discipline', 'related_role'],
    Flow=['flow_context', 'start_port', 'end_port'],
    HardwareProduct=(PGXN_REQD['HardwareProduct'] + ['public'] + SYSTEM),
    Model=(IDENTITY + ['type_of_model', 'of_thing']),
    ModelFamily=IDENTITY,
    ModelType=(IDENTITY + ['model_type_family']),
    ObjectAccess=['accessible_object', 'grantee'],
    Organization=(IDENTITY + ['name_code', 'cage_code', 'parent_organization',
                              'sub_organizations', 'street_address', 'city',
                              'state_or_province', 'zip_or_postal_zone']),
    Person=(IDENTITY + ['last_name', 'mi_or_name', 'first_name',
                        'preferred_name', 'employer', 'org', 'work_email',
                        'work_phone']),
    ParameterDefinition=(IDENTITY + ['range_datatype', 'dimensions']),
    ParameterRelation=['referenced_relation', 'correlates_parameter'],
    Port=['id', 'name', 'of_product', 'type_of_port'],
    Product=(PGXN_REQD['HardwareProduct'] + ['public'] + SYSTEM),
    ProductType=['abbreviation'] + IDENTITY,
    ProductTypeParameterDefinition=['used_in_product_type',
                                    'parameter_definition'],
    Project=(IDENTITY + ['parent_organization']),
    ProjectSystemUsage=['id', 'project', 'system', 'system_role'],
    Relation=(IDENTITY + ['formulation']),
    Representation=(IDENTITY + ['of_object', 'representation_purpose']),
    RepresentationFile=(IDENTITY + ['of_representation']),
    Requirement=(IDENTITY + ['owner', 'req_type', 'allocated_to_function',
                 'allocated_to_system', 'req_level', 'version',
                 'version_sequence', 'iteration', 'validated', 'public',
                 'frozen']),
    RoleAssignment=['assigned_role', 'assigned_to', 'role_assignment_context'],
    Test=(IDENTITY + ['verifies', 'purpose', 'comment']),
    )

# PGXN_VIEWS:  Default fields/ordering for the PgxnObject "info", "narrative"
# and "admin" tabs
PGXN_VIEWS = dict(
    info=['public', 'computable_form', 'req_type', 'req_constraint_type',
          'req_dimensions', 'req_target_value', 'req_tolerance',
          'req_tolerance_type', 'req_tolerance_lower', 'req_tolerance_upper',
          'req_maximum_value', 'req_minimum_value', 'validated',
          'verification_method'],
    narrative=['comment', 'rationale', 'purpose', 'req_epilog',
               'req_min_max_phrase', 'req_shall_phrase', 'req_subject'],
    admin=['oid', 'creator', 'create_datetime', 'modifier', 'mod_datetime'])

# PGXN_PARAMETERS:  preferred ordering for parameters in PgxnObject parameter
# forms
PGXN_PARAMETERS = ['m', 'P', 'R_D', 'Vendor', 'Cost', 'TRL', 'height', 'width',
                   'depth', 'CoM_X', 'CoM_Y', 'CoM_Z']

# DEFAULT_CLASS_PARAMETERS:  default parameters of objects by class
DEFAULT_CLASS_PARAMETERS = {'Activity': ['duration', 't_start'],
                            'Mission': ['duration']}

# DEFAULT_PRODUCT_TYPE_PARAMETERS:  default parameters by ProductType id
DEFAULT_PRODUCT_TYPE_PARAMETERS = {'': []}

# PGXN_PLACEHOLDERS:  Placeholder text for fields in PgxnObject forms
PGXN_PLACEHOLDERS = {'id': 'abbreviated name; no spaces',
                     'id_ns': 'namespace for id',
                     'name': 'verbose name; spaces ok',
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
                     'range'  : 'ProductTypeParameterDefinition'},

       # *** M2M:  ObjectAccess
       # inverse of 'accessible_object'
       # complementary to 'accessible_objects'
       'grantees' : {
                     'domain' : 'Product',
                     'range'  : 'ObjectAccess'},
       # inverse of 'grantee'
       # complementary to 'grantees'
       'accessible_objects' : {
                     'domain' : 'Actor',
                     'range'  : 'ObjectAccess'}
       }

# Special properties that get a customized droppable interface to enable
# populating a one-to-many relationship with objects.
# Format is {property name : one2m relationship range class name}
ONE2M = {
         # inverse of 'creator'
         'created_objects' :      {'domain' : 'Actor',
                                   'range'  : 'Modelable'},
         # inverse of 'of_thing'
         'has_models' :           {'domain' : 'Modelable',
                                   'range'  : 'Model'},
         # inverse of 'of_object'
         'has_representations' :  {'domain' : 'DigitalProduct',
                                   'range'  : 'Representation'},
         # inverse of 'of_representation'
         'has_files' :            {'domain' : 'Representation',
                                   'range'  : 'RepresentationFile'},
         # inverse of 'allocated_to_function'
         'allocated_requirements' : {'domain' : 'Acu',
                                   'range'  : 'Requirement'},
         # inverse of 'allocated_to_system'
         'system_requirements' :  {'domain' : 'ProjectSystemUsage',
                                   'range'  : 'Requirement'},
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
# the pangalaxian object editor
PGXN_MASK = dict(
    ParameterDefinition=(PGXN_HIDE + ['base_parameters', 'computed_by_default',
                         'generating_function', 'used_in_disciplines']),
    Requirement=(PGXN_HIDE + ['components', 'derived_from', 'fsc_code',
                 'has_models', 'ports', 'product_type',
                 'specification_number']),
    Test=(PGXN_HIDE + ['components', 'fsc_code', 'product_type'])
    )

# PGXN_HIDE_PARMS:  Subclasses of Modelable for which 'parameters' panel should
# be hidden
PGXN_HIDE_PARMS = [
                   'Actor',
                   'Acu',
                   'Organization',
                   'ParameterDefinition',
                   'ParameterRelation',
                   'Person',
                   'ProductRequirement',
                   'ProductTypeParameterDefinition',
                   'Project',
                   'ProjectSystemUsage',
                   'Representation'
                   ]

# MODEL_TYPE_PREFS:  preferred model types
# (for now, the only ones we can render ... ;)
MODEL_TYPE_PREFS = ['step:203', 'step:214', 'step:242', 'pgefobjects:Block']

# SELECTION_VIEWS:  Class-specific default sets of columns for tabular display
# of objects in the foreign key object selection dialog for PgxnObject
SELECTION_VIEWS = dict(
    Domain=['id', 'description']
    )

# SELECTION_FILTERS:  Field-specific filters for valid objects to be included
# in the tabular display of objects in the foreign key object selection dialog
# for PgxnObject in format:
#   {field: {class_name_1: filter1,
#            class_name_2: filter2}, ...}
# ... where a filter is a dict or None, which means "all".
SELECTION_FILTERS = dict(
    owner={'Project': None,
           'Organization': None},
    product_type_hint={'ProductType': None},
    product_type={'ProductType': None}
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
    range_datatype=OrderedDict([
        ('float', float),
        ('int', intconv),
        ('text', str),
        ('boolean', bool)]),
    dimensions=OrderedDict(
        [(dim, dim) for dim in in_si]),
    directionality=OrderedDict([
        # null -> bidirectional
        ('', ''),
        ('input', 'input'),
        ('output', 'output')
        ]))

# TEXT_PROPERTIES:  Properties that get a TextWidget interface
TEXT_PROPERTIES = ['comment', 'description', 'rationale', 'purpose']

# NUMERIC_FORMATS:  Formatting used to display numbers in UI
NUMERIC_FORMATS = ['Thousands Commas', 'No Commas', 'Scientific Notation']

# NUMERIC_PRECISION:  Maximum precision assumed for parameter values
NUMERIC_PRECISION = ['3', '4', '5', '6', '7', '8', '9']

# Special external names of PGEF classes
EXT_NAMES = {
    'Acu'                 : 'Assembly Component Usage',
    'EeePart'             : 'EEE Part',
    'Mime'                : 'MIME Type',
    'ParameterDefinition' : 'Parameter Definition',
    }

# Special plurals of external names of PGEF classes
EXT_NAMES_PLURAL = {
    'Activity'            : 'Activities',
    'Acu'                 : 'Assembly Component Usages',
    'EeePart'             : 'EEE Parts',
    'HardwareProduct'     : 'Hardware Products',
    'Mime'                : 'MIME Types',
    'ParameterDefinition' : 'Parameter Definitions',
    'Port'                : 'Ports',
    'Property'            : 'Properties',
    }

# Special external names of attributes of PGEF classes
ATTR_EXT_NAMES = {
    'Requirement' :
        {
         'description' : 'text',
         'req_type' : 'reqt type',
         'req_level' : 'level',
         'req_constraint_type' : 'constraint type',
         'req_dimensions' : 'dimensions',
         'req_maximum_value' : 'maximum',
         'req_minimum_value' : 'minimum',
         'req_tolerance': 'tolerance (+/-)',
         'req_tolerance_lower': 'lower tolerance',
         'req_tolerance_upper': 'upper tolerance'
        }
    }

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
            'representations',
            'abbreviation'
            ]

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
            'id': 150,
            'id_ns': 100,
            'iteration': 50,
            'modifier': 100,
            'mod_datetime': 100,
            'name': 200,
            'owner': 100,
            'oid': 100,
            'product_type': 150,
            'purpose': 250,
            'range_datatype': 50,
            'rationale': 250,
            'representations': 100,
            'req_type': 50,
            'url': 100,
            'version': 50,
            'version_sequence': 50
            }

# Column names to use for specified properties
PGEF_COL_NAMES = {
            'version': 'ver.',
            'iteration': 'iter.',
            'version_sequence': 'seq.',
            'range_datatype': 'range',
            'abbreviation': 'abbrev.'
            }

# Properties displayed as READ-ONLY by the PgxnObject viewer/editor
# TODO:  do this in a configurable way, as part of the Schemas
# TODO:  for m2m attributes, these may eventually become editable, when
# PgxnObject implements that capability
READONLY = [
            'allocated_to_functions', # m2m (Requirement:Acu)
            'allocated_to_systems', # m2m (Requirement:ProjectSystemUsage)
            'components',       # m2m (Acu)
            'creator',          #  "   "    "   "
            'create_datetime',  # tds
            'has_models',       # inverse of 'of_thing' property of Model
            'id_ns',            # derive from 'owner'; might be YAGNI ...
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

# "Internal" plurals of PGEF class names, particularly for use in "back
# references" in a foreign key relationship

PLURALS = {
    'Activity'           : 'Activities',
    'Acu'                : 'Acus',
    'DataPackage'        : 'DataPackages',
    'DataSet'            : 'DataSets',
    'DigitalProduct'     : 'DigitalProducts',
    'DigitalFile'        : 'DigitalFiles',
    'Document'           : 'Documents',
    'EeePart'            : 'EeeParts',
    'Identifiable'       : 'Identifiables',
    'Mime'               : 'Mimes',
    'Model'              : 'Models',
    'Organization'       : 'Organizations',
    'ManagedObject'      : 'ManagedObjects',
    'ProductInstance'    : 'ProductInstances',
    'Product'            : 'Products',
    'PartModel'          : 'PartModels',
    'PartsListItem'      : 'PartsListItems',
    'PartsList'          : 'PartsLists',
    'Person'             : 'Persons',
    'Product'            : 'Products',
    'Project'            : 'Projects',
    'Property'           : 'Properties',
    'Representation'     : 'Representations',
    'RoleAssignment'     : 'RoleAssignments',
    'Role'               : 'Roles'
    }

