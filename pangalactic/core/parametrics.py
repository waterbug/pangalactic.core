"""
Functions to support Parameters, Relations, and Data Elements
"""
import json, os
from collections import namedtuple
from copy        import deepcopy
from decimal     import Decimal
from math        import floor, fsum, log10

# pangalactic
from pangalactic.core                 import config, prefs
from pangalactic.core.datastructures  import OrderedSet
from pangalactic.core.meta            import (SELECTABLE_VALUES,
                                              DEFAULT_CLASS_DATA_ELEMENTS,
                                              DEFAULT_CLASS_PARAMETERS,
                                              DEFAULT_PRODUCT_TYPE_DATA_ELMTS,
                                              DEFAULT_PRODUCT_TYPE_PARAMETERS)
from pangalactic.core.units           import in_si, ureg
from pangalactic.core.utils.datetimes import dtstamp

# dispatcher (Louie)
from louie import dispatcher


class logger:
    def info(self, s):
        dispatcher.send(signal='log info msg', msg=s)
    def debug(self, s):
        dispatcher.send(signal='log debug msg', msg=s)

log = logger()

DATATYPES = SELECTABLE_VALUES['range_datatype']
# NULL values by dtype:
NULL = {'float': 0.0, 'int': 0, 'str': '', 'bool': False}
TWOPLACES = Decimal('0.01')

# NOTE! #####################################################################
# For Data Element handling, see DATA ELEMENT SECTION, at the end ...
# NOTE! #####################################################################

# PARAMETER CACHES ##########################################################

# componentz:  runtime component cache
# purpose:  enable fast computation of assembly parameters
# format:  {product.oid : list of Comp namedtuples}
#          ... where:
#            oid (str): Acu.component.oid
#            quantity (int): Acu.quantity
#            reference_designator (str): Acu.reference_designator
componentz = {}
Comp = namedtuple('Comp', 'oid quantity reference_designator')

# parm_defz:  runtime cache of parameter definitions (both base and context
#             parameter definitions are included)
# purpose:  enable fast lookup of parameter metadata & compact representation
#           of 'parameterz' cache as (value, units, mod_datetime)
# format:  {'parameter id': {parameter properties}
#                            ...}}
# ... where parameter properties are:
# ---------------------------------------------------------------------------
# name, variable, context, description, dimensions, range_datatype, computed,
# mod_datetime
# ---------------------------------------------------------------------------
parm_defz = {}

# parameterz:  persistent** cache of assigned parameter values
#              ** persisted in the file 'parameters.json' in the
#              application home directory -- see the orb functions
#              `_save_parmz` and `_load_parmz`
# format:  {object.oid : {'parameter id': {parameter properties}
#                         ...}}
# ... where parameter properties are:
# --------------------------
# value, units, mod_datetime
# --------------------------
parameterz = {}

def serialize_parms(oid):
    """
    Output the serialized format for parameters. Note that the values are
    *always* expressed in *base* units and the 'units' field contains the
    preferred units to be used when displaying the value in the user interface
    (i.e., the value must be converted to those units for display).

    Args:
        obj_parms (dict):  a dictionary containing the parameters
            associated with an object (for a given object `obj`, its
            parameters dictionary will be `parameterz[obj.oid]`).

    Serialize the dictionary of parameters associated with an object.

    IMPLEMENTATION NOTE:  uses deepcopy() to avoid side-effects to the
    `parameterz` dict.
    """
    if oid in parameterz:
        return deepcopy(parameterz[oid])
    else:
        return {}

def deserialize_parms(oid, ser_parms, cname=None):
    """
    Output the serialized format for parameters. Note that the values are
    *always* expressed in base units and the 'units' field contains the
    preferred units to be used when displaying the value in the user interface
    (i.e., the value must be converted to those units for display).

    [NOTE: for backwards compatibility, detection of data elements in a
    `parameters` section has been added, because some data elements (such as
    TRL and Vendor) were previously defined as parameters.  Any data elements
    found will be deserialized and added to the `data_elementz` cache.
    - SCW 2020-04-09.]

    Args:
        oid (str):  oid attr of the object to which the parameters are assigned
        ser_parms (dict):  the serialized parms dictionary

    Keyword Args:
        cname (str):  class name of the object to which the parameters are
            assigned (only used for logging)
    """
    # if cname:
        # log.debug('* deserializing parms for {} ({})...'.format(oid,
                                                                    # cname))
        # log.debug('  parms: {}'.format(ser_parms))
    if not ser_parms:
        # log.debug('  object with oid "{}" has no parameters'.format(oid))
        return
    if oid not in parameterz:
        parameterz[oid] = {}
    for pid, parm in ser_parms.items():
        mod_dt = parm['mod_datetime']
        if pid in parm_defz:
            # this is a parameter (has a ParameterDefinition)
            if ((parameterz[oid].get(pid) and
                 mod_dt > parameterz[oid][pid]['mod_datetime'])
                or not parameterz[oid].get(pid)):
                # deserialized parameter value is more recent or that parameter
                # was not previously assigned
                parameterz[oid][pid] = parm
        elif pid in de_defz:
            # this is a data element (has a DataElementDefinition)
            # log_msg = 'data element found in parameters: "{}"'.format(pid)
            # log.debug('  - {}'.format(log_msg))
            if oid not in data_elementz:
                data_elementz[oid] = {}
            de = data_elementz[oid].get(pid)
            if (de and mod_dt > de['mod_datetime']):
                # deserialized value is more recent
                de['mod_datetime'] = parm['mod_datetime']
                de['value'] = parm['value']
            elif not data_elementz[oid].get(pid):
                # that data element was not previously assigned
                de = dict(value=parm['value'],
                          mod_datetime=parm['mod_datetime'])
                data_elementz[oid][pid] = de
            # pid refers to a data element, so it should not be in parameterz
            if pid in parameterz[oid]:
                del parameterz[oid][pid]
        else:
            # log_msg = 'unknown id found in parameters: "{}"'.format(pid)
            # log.debug('  - {}'.format(log_msg))
            # pid has no definition, so it should not be in parameterz or
            # data_elementz
            if pid in parameterz.get(oid, {}):
                del parameterz[oid][pid]
            if pid in data_elementz.get(oid, {}):
                del data_elementz[oid][pid]
    ### FIXME (?): it's dangerous to remove pids not in new_parms, but we
    ### may need at some point to deal with deleted parameters ... (i.e.
    ### remove them from the cache).
    # pids = list(parameterz[oid])
    # for pid in pids:
        # if pid not in new_parms:
            # del parameterz[oid][pid]
    # add base parameters for any context parameters for which the base
    # parameter is absent
    base_pids = set([pid.split('[')[0] for pid in parameterz[oid]])
    for base_pid in base_pids:
        if not base_pid in parameterz[oid]:
            # log_msg = 'base variable not in parameters, adding: "{}"'.format(
                                                                    # base_pid)
            # log.debug('  - {}'.format(log_msg))
            set_pval(oid, base_pid, 0.0)

def load_parmz(json_path):
    """
    Load the `parameterz` dict from json file in cache format.
    """
    # log.debug('* load_parmz() ...')
    if os.path.exists(json_path):
        with open(json_path) as f:
            stored_parameterz = json.loads(f.read())
        for oid, parms in stored_parameterz.items():
            deserialize_parms(oid, parms)
        # log.debug('  - parameterz cache loaded and recomputed.')
    else:
        # log.debug('  - "parameters.json" was not found.')
        pass

def save_parmz(json_path):
    """
    Save `parameterz` dict to a json file in cache format.
    """
    # log.debug('* save_parmz() ...')
    stored_parameterz = {}
    for oid, parms in parameterz.items():
        # NOTE: serialize_parms() uses deepcopy()
        stored_parameterz[oid] = serialize_parms(oid)
    with open(json_path, 'w') as f:
        f.write(json.dumps(stored_parameterz, separators=(',', ':'),
                           indent=4, sort_keys=True))
    # log.debug('  ... parameters.json file written.')

# parmz_by_dimz:  runtime cache that maps dimensions to parameter definitions
# format:  {dimension : [ids of ParameterDefinitions having that dimension]}
# NOTE:  see orb function 'create_parmz_by_dimz'
parmz_by_dimz = {}

# req_allocz:  runtime requirement allocations cache
# purpose:  optimize performance of margin calculations
# format:  {req_oid : [usage_oid, obj_oid, alloc_ref, pid, constraint]}
# ... where:
#   req_oid (str):  the oid of the requirement
#   usage_oid (str): the oid of the Acu or ProjectSystemUsage to which
#       the requirement is allocated
#   obj_oid (str):  the oid of the component or system of the usage
#   alloc_ref (str):  the reference_designator or system_role of the usage
#   pid (str):  the parameter base id
#   constraint (NamedTuple): a named tuple of the form:
#   -----------------------------------------------------------------------
#   (units, target, max, min, tol, upper, lower, constraint_type, tol_type)
#   -----------------------------------------------------------------------
# ... where:
#
#   units (str): units of the numerical quantities
#   target (float): target value (for val with tolerance(s))
#   max (float): maximum value
#   min (float): minimum value
#   tol (float): symmetric tolerance
#   upper (float): upper tolerance if asymmetrical
#   lower (float): lower tolerance if asymmetrical
#   constraint_type (str): name of constraint type, one of:
#       ['single_value' | 'maximum' | 'minimum' ]
#   tol_type (str): name of tolerance type, one of:
#       ['symmetric' | 'asymmetric']
req_allocz = {}
Constraint = namedtuple('Constraint',
             'units target max min tol upper lower constraint_type tol_type')
#############################################################################

def round_to(x, n=4):
    """
    Round the number x to n digits.  (Default: 3)

    Args:
        x (float or int):  input number

    Keyword Args:
        n (int):  number of digits in output (must be > 0)
    """
    if x == 0:
        return 0
    n = int(prefs.get('numeric_precision', n))
    val = round(x, -int(floor(log10(abs(x)))) + (n - 1))
    if type(x) is int:
        return int(val)
    return val

def refresh_componentz(product):
    """
    Refresh the `componentz` cache for a Product instance. This must be called
    before calling orb.recompute_parmz() whenever a new Acu that references
    that Product instance as its assembly is created, deleted, or modified.
    The 'componentz' dictionary has the form

        {product.oid :
          list of Comp('oid', 'quantity', 'reference_designator')}

    where the list of `Comp` namedtuples is created from `product.components`
    (Acus of the product), using Acu.component.oid, Acu.oid, Acu.quantity, and
    Acu.reference_designator.

    Args:
        product (Product):  the Product instance
    """
    if product:
        # log.debug('* refresh_componentz({})'.format(product.id))
        componentz[product.oid] = [Comp._make((
                                        getattr(acu.component, 'oid', None),
                                        acu.quantity or 1,
                                        acu.reference_designator))
                                   for acu in product.components
                                   if acu.component
                                   and acu.component.oid != 'pgefobjects:TBD']

def refresh_req_allocz(req):
    """
    Refresh the `req_allocz` cache for a Requirement instance.  This must be
    called whenever a Requirement instance is created, modified, or deleted or
    an Acu or ProjectSystemUsage is deleted or modified, which could affect the
    'obj_oid' and/or 'alloc_ref' items.

    NOTE:  this function depends only on the database and does not use any
    caches, nor does it update the parameterz cache, so it can be used by any
    margin computation function.

    The 'req_allocz' dictionary has the form:

        {req_oid : [usage_oid, obj_oid, alloc_ref, pid, constraint]}

    ... where:

      req_oid (str):  the oid of the requirement
      usage_oid (str): the oid of the Acu or ProjectSystemUsage to which
          the requirement is allocated
      obj_oid (str):  the oid of the component or system of the usage
      alloc_ref (str):  the reference_designator or system_role of the usage
      pid (str):  the parameter base id
      constraint (NamedTuple): a named tuple of the form:

      (units, target, max, min, tol, upper, lower, constraint_type, tol_type)

    ... where:

      units (str): units of the numerical quantities
      target (float): target value (for val with tolerance(s))
      max (float): maximum value
      min (float): minimum value
      tol (float): symmetric tolerance
      upper (float): upper tolerance if asymmetrical
      lower (float): lower tolerance if asymmetrical
      constraint_type (str): name of constraint type, one of:
          ['single_value' | 'maximum' | 'minimum' ]
      tol_type (str): name of tolerance type, one of:
          ['symmetric' | 'asymmetric']

    Args:
        req (Requirement):  a Requirement instance
    """
    # log.debug('* refresh_req_allocz({})'.format(req.oid))
    if not req and req.oid in req_allocz:
        # the requirement is referenced in req_allocz but the requirement
        # has now been deleted: remove it from req_allocz
        # log.debug('  req was deleted, removing from req_allocz ...')
        del req_allocz[req.oid]
        return
    usage_oid = None
    alloc_ref = None
    obj_oid = None
    if req.allocated_to_function:
        acu = req.allocated_to_function
        alloc_ref = acu.reference_designator or acu.name or acu.id
        usage_oid = acu.oid
        obj_oid = getattr(acu.component, 'oid', None)
    elif req.allocated_to_system:
        psu = req.allocated_to_system
        alloc_ref = psu.system_role or psu.name or psu.id
        usage_oid = psu.oid
        obj_oid = getattr(psu.system, 'oid', None)
    else:
        # req is not allocated; if present, remove it
        # log.debug('  req is not allocated')
        if req.oid in req_allocz:
            del req_allocz[req.oid]
            # log.debug('  + removed from req_allocz.')
        return
    if req.req_type == 'functional':
        # log.debug('  functional req (no parameter or constraint).')
        if usage_oid:
            req_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, None, None]
    relation = req.computable_form
    pid = None
    if relation:
        # look for ParameterRelations to identify parameters
        parm_rels = relation.correlates_parameters
        if parm_rels:
            # for now, there should only be a single correlated parameter (max)
            parm_def = parm_rels[0].correlates_parameter
            pid = parm_def.id
        else:
            # log.debug('  no ParameterRelation found -> functional req.')
            req_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, None, None]
            return
    else:
        # log.debug('  no computable_form found -> functional req.')
        req_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, None, None]
        return
    if pid:
        req_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, pid,
                                 Constraint._make((
                                     req.req_units,
                                     req.req_target_value,
                                     req.req_maximum_value,
                                     req.req_minimum_value,
                                     req.req_tolerance,
                                     req.req_tolerance_upper,
                                     req.req_tolerance_lower,
                                     req.req_constraint_type,
                                     req.req_tolerance_type
                                     ))]
    else:
        # log.debug('  no parameter found; treat as functional req.')
        req_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, None, None]

def node_count(product_oid):
    """
    Get the number of nodes in the assembly tree of the product with the
    specified oid.

    Args:
        product_oid (str):  oid of a Product instance
    """
    count = 0
    if componentz.get(product_oid):
        count += len(componentz[product_oid])
        if count:
            for c in componentz[product_oid]:
                count += node_count(c.oid)
    return count

def get_parameter_id(variable, context_id):
    pid = variable
    if context_id:
        pid += '[' + context_id + ']'
    return pid

def get_parameter_name(variable_name, context_abbr):
    name = variable_name
    if context_abbr:
        name += ' [' + context_abbr + ']'
    return name

def get_parameter_description(variable_desc, context_desc):
    desc = variable_desc
    if context_desc:
        desc += ' [' + context_desc + ']'
    return desc

def split_pid(pid):
    """
    Extract the variable and context from a parameter id.

    Args:
        pid (str):  parameter id
    """
    if pid.endswith(']'):
        return pid.split('[')[0], pid.split('[')[1][:-1]
    else:
        return pid, ''

def add_context_parm_def(pd, c):
    """
    Add a context parameter definition to the `parm_defz` cache.

    Args:
        pd (ParameterDefinition):  ParameterDefinition for the base parameter
        c (ParameterContext):  object representing the context
            of the parameter
    """
    parm_defz[get_parameter_id(pd.id, c.id)] = {
        'name': get_parameter_name(pd.name, c.abbreviation or c.id),
        'variable': pd.id,
        'context': c.id,
        'context_type': c.context_type,
        'description':
              get_parameter_description(pd.description, c.description),
        'dimensions': c.context_dimensions or pd.dimensions,
        'range_datatype': c.context_datatype or pd.range_datatype,
        'computed': c.computed,
        'mod_datetime': str(dtstamp())}

def update_parm_defz(pd):
    """
    Update the `parm_defz` cache when a new ParameterDefinition is created or
    modified.

    Args:
        pd (ParameterDefinition):  ParameterDefinition being added
    """
    # log.debug('* update_parm_defz')
    parm_defz[pd.id] = {
        'name': pd.name,
        'variable': pd.id,
        'context': None,
        'context_type': None,
        'description': pd.description,
        'dimensions': pd.dimensions,
        'range_datatype': pd.range_datatype,
        'computed': False,
        'mod_datetime': str(dtstamp())}

def update_parmz_by_dimz(pd):
    """
    Refresh the `parmz_by_dimz` cache when a ParameterDefinition is created or
    modified.  The cache has the form

        {dimension : [ids of ParameterDefinitions having that dimension]}

    NOTE:  see also the orb function 'create_parmz_by_dimz' ... it may move
    here in the future.

    Args:
        pd (ParameterDefinition):  ParameterDefinition being added or modified
    """
    # log.debug('* refresh_parmz_by_dimz')
    if pd.dimensions in parmz_by_dimz:
        parmz_by_dimz[pd.dimensions].append(pd.id)
    else:
        parmz_by_dimz[pd.dimensions] = [pd.id]

def add_parameter(oid, pid):
    """
    Add a new parameter to an object, which means adding a parameter's data
    structure to the `p.node.parametrics.parameterz` dictionary under that
    objects's oid, if it does not already exist for the specified paramter.
    The parameter data structure format is a dict with the following keys:

        value, units, mod_datetime

    NOTE:  'units' here refers to the preferred units in which to *display* the
    parameter's value, not the units of the 'value', which are *always* mks
    base units.

    Args:
        oid (str):  oid of the object that owns the parameter
        pid (str):  the id of the parameter
    """
    if oid not in parameterz:
        parameterz[oid] = {}
    is_context_parm = False
    if '[' in pid:
        # this is a context parameter id -- find the base pid (variable)
        variable = pid.split('[')[0]
        is_context_parm = True
    else:
        variable = pid
    # log.debug('* add_parameter "{!s}"'.format(pid))
    # [1] check if object already has that parameter
    if pid in parameterz[oid]:
        # if the object already has that parameter, do nothing
        return True
    # [2] check for ParameterDefinition of base variable
    pd = parm_defz.get(variable)
    if not pd:
        # for now, if no ParameterDefinition exists for pid, pass
        # (maybe eventually raise TypeError)
        # log.debug(
            # '* add_parameter(): variable "{}" is not defined.'.format(
                                                              # variable))
        return False
    # [3] check if the variable (base parameter) has been assigned ...
    if not parameterz[oid].get(variable):
        # the variable (base parameter) has not been assigned ... this is
        # rare, so debug logging is ok
        # if is_context_parm:
            # log.debug('* adding base parameter "{}".'.format(variable))
        # else:
            # log.debug('* adding parameter "{}".'.format(variable))
        pdz = parm_defz.get(variable)
        if not pdz:
            # if not in parm_defz, add it:
            pdz = {pd['id'] :
                   {'name': pd['name'],
                    'variable': pd['id'],
                    'context': None,
                    'context_type': None,
                    'description': pd['description'],
                    'dimensions': pd['dimensions'],
                    'range_datatype': pd['range_datatype'],
                    'computed': False,
                    'mod_datetime':
                        str(pd.get('mod_datetime', '') or dtstamp())
                    }}
            parm_defz.update(pdz)
        # NOTE:  setting the parameter's value is a separate operation -- when a
        # parameter is created, its value is initialized to the appropriate "null"
        radt = pdz.get('range_datatype', 'float')
        dims = pdz.get('dimensions')
        p_defaults = config.get('p_defaults') or {}
        if p_defaults.get(variable):
            # if a default value is configured for this variable, override null
            dtype = DATATYPES[radt]
            value = dtype(p_defaults[variable])
        elif radt == 'float':
            value = 0.0
        elif radt == 'int':
            value = 0
        elif radt == 'boolean':
            value = False
        else:  # 'text'
            value = ''
        parameterz[oid][variable] = dict(
            value=value,   # consistent with dtype defined in `range_datatype`
            units=in_si.get(dims),   # SI units consistent with `dimensions`
            mod_datetime=str(dtstamp()))
    if is_context_parm:
        # if this is a context parameter, its base variable has been added by
        # the above clause if it was not already present, so it is safe to add
        # the context parameter now
        pdz = parm_defz.get(pid)
        radt = pdz.get('range_datatype', 'float')
        dims = pdz.get('dimensions')
        p_defaults = config.get('p_defaults') or {}
        if p_defaults.get(pid):
            # if a default value is configured for this pid, override null
            dtype = DATATYPES[radt]
            value = dtype(p_defaults[pid])
        elif radt == 'float':
            value = 0.0
        elif radt == 'int':
            value = 0
        elif radt == 'boolean':
            value = False
        else:  # 'text'
            value = ''
        parameterz[oid][pid] = dict(
            value=value,
            units=in_si.get(dims),   # SI units consistent with `dimensions`
            mod_datetime=str(dtstamp()))
        return True
    else:
        return True

def add_default_parameters(obj):
    """
    Assign the configured or preferred default parameters to an object.

    Args:
        obj (Identifiable):  the object to receive parameters
    """
    # log.debug('* adding default parameters to object "{}"'.format(
                                                                # obj.id))
    # Configured Parameters are currently defined by the 'dashboard'
    # configuration (in future that may be augmented by Parameters
    # referenced by, e.g., a ProductType and/or a ModelTemplate, both of
    # which are essentially collections of ParameterDefinitions.
    pids = OrderedSet()
    cname = obj.__class__.__name__
    pids |= OrderedSet(DEFAULT_CLASS_PARAMETERS.get(cname, []))
    # TODO: let user set default parameters in their prefs
    if cname == 'HardwareProduct':
        # default for "default_parms" in config:  mass, power, data rate
        # (config is read in p.node.gui.startup, and will be overridden by
        # prefs['default_parms'] if it is set
        pids |= OrderedSet(prefs.get('default_parms')
                           or config.get('default_parms')
                           or ['m', 'P', 'R_D',
                               'm[CBE]', 'm[Ctgcy]', 'm[MEV]',
                               'P[CBE]', 'P[Ctgcy]', 'P[MEV]',
                               'R_D[CBE]', 'R_D[Ctgcy]', 'R_D[MEV]',
                               'Cost'])
        if obj.product_type:
            pids |= OrderedSet(DEFAULT_PRODUCT_TYPE_PARAMETERS.get(
                               getattr(obj.product_type, 'id', '') or []))
    # add default parameters first ...
    # log.debug('  - adding parameters {!s} ...'.format(str(pids)))
    for pid in pids:
        add_parameter(obj.oid, pid)

def add_product_type_parameters(obj, pt):
    """
    Assign the parameters associated with the specified product type to an
    object.

    Args:
        obj (Identifiable):  the object to receive parameters
        pt (ProductType):  the product type
    """
    # log.debug('* assigning parameters for product type "{}"'.format(pt.id))
    # then check for parameters specific to the product_type, if any
    if pt:
        # check if the product_type has parameters
        pt_parmz = parameterz.get(pt.oid)
        if pt_parmz:
            # if so, replicate them directly (with values)
            for pid in pt_parmz:
                parameterz[obj.oid][pid] = pt_parmz[pid].copy()

def delete_parameter(oid, pid):
    """
    Delete a parameter from an object.  This should be rare and would only be
    necessary if the parameter is irrelevant to the object; therefore, the base
    variable and all related context parameters would be deleted.

    Args:
        oid (str):  oid of the object that owns the parameter
        pid (str):  `id` attribute of the parameter
    """
    # TODO: need to dispatch louie & pubsub messages!
    if '[' in pid:
        # find the base pid (variable)
        base_pid = pid.split('[')[0]
    if oid in parameterz:
        if parameterz[oid].get(base_pid):
            del parameterz[oid][base_pid]
        # look for all context parameters of that object with that base pid
        for other_pid in parameterz[oid]:
            # if it's a context parameter with the same base pid, delete it
            if '[' in other_pid and base_pid == other_pid.split('[')[0]:
                del parameterz[oid][other_pid]

def get_pval(oid, pid, units='', allow_nan=False):
    """
    Return a cached parameter value in base units or in the units specified.

    Args:
        oid (str): the oid of the object that has the parameter
        pid (str): the parameter 'id' value

    Keyword Args:
        units (str):  units in which the return value should be expressed
    """
    # Too verbose -- only for extreme debugging ...
    # log.debug('* get_pval() ...')
    pdz = parm_defz.get(pid)
    if not pdz:
        # log.debug('* get_pval: "{}" does not have a definition.'.format(
                                                                        # pid))
        return
    try:
        if not units:
            # if no units are specified, return the value in base units
            return parameterz[oid][pid]['value']
        else:
            # convert based on dimensions/units ...
            dims = pdz.get('dimensions')
            # special cases for 'percent' and 'money'
            if dims == 'percent':
                # show percentage values in interface -- they will
                # later be saved (by set_pval) as .01 * value
                return 100.0 * parameterz[oid][pid]['value']
            elif dims == 'money':
                # round to 2 decimal places
                val = get_pval(oid, pid)
                if val is None:
                    return 0.00
                elif val:
                    return float(Decimal(val).quantize(TWOPLACES))
                else:
                    return 0.00
            else:
                base_val = parameterz[oid][pid]['value']
                quan = base_val * ureg.parse_expression(in_si[dims])
                quan_converted = quan.to(units)
                return quan_converted.magnitude
    except:
        return NULL.get(pdz.get('range_datatype', 'float'))

def get_pval_as_str(oid, pid, units='', allow_nan=False):
    """
    Return a cached parameter value in the specified units (or in base units if
    not specified) as a formatted string, for display in UI.  (Used in the
    object editor, `p.node.gui.pgxnobject.PgxnObject` and the dashboard.)

    Args:
        oid (str): the oid of the object that has the parameter
        pid (str): the `id` of the parameter

    Keyword Args:
        units (str):  units in which the return value should be expressed
        allow_nan (bool):  allow numpy NaN as a return value
    """
    # Too verbose -- only for extreme debugging ...
    # log.debug('* get_pval_as_str({}, {})'.format(oid, pid))
    pdz = parm_defz.get(pid)
    if not pdz:
        # log.debug('  - "{}" does not have a definition.'.format(pid))
        return '-'
    try:
        # convert based on dimensions/units ...
        dims = pdz.get('dimensions')
        # special cases for 'percent' and 'money'
        if dims == 'percent':
            # show percentage values in interface -- they will
            # later be saved (by set_pval) as .01 * value
            val = 100.0 * get_pval(oid, pid)
        elif dims == 'money':
            # format with 2 decimal places
            val = get_pval(oid, pid)
            if val is None:
                return ''
            elif val:
                return "{:,}".format(Decimal(val).quantize(TWOPLACES))
            else:
                return '0.00'
        else:
            base_val = get_pval(oid, pid)
            if units:
                # TODO: ignore units if not compatible
                quan = base_val * ureg.parse_expression(in_si[dims])
                quan_converted = quan.to(units)
                val = quan_converted.magnitude
            else:
                val = base_val
        radt = pdz.get('range_datatype')
        if radt in ['int', 'float']:
            dtype = DATATYPES.get(radt)
            numfmt = prefs.get('numeric_format')
            if numfmt:
                if numfmt == 'Thousands Commas':
                    return "{:,}".format(dtype(round_to(val)))
                elif numfmt == 'Scientific Notation':
                    return "{:.4e}".format(dtype(round_to(val)))
                else:   # 'No Commas'
                    return str(round_to(val))
            else:
                # default: Thousands Commas
                return "{:,}".format(dtype(round_to(val)))
        else:
            # if not an int or float, cast directly to string ...
            return str(val)
    except:
        # FOR EXTREME DEBUGGING ONLY:
        # this logs an ERROR for every unpopulated parameter
        # msg = '* get_pval_as_str({}, {})'.format(oid, pid)
        # msg += '  encountered an error.'
        # log.debug(msg)

        # for production use, return '-' if the value causes error
        return '-'

def _compute_pval(oid, variable, context_id, allow_nan=False):
    """
    Get the value of a parameter of the specified object, computing it if it is
    'computed' and caching the computed value in parameterz; otherwise,
    returning its value from parameterz.

    NOTE: this function is intended to be private, called only by the orb's
    `recompute_parmz` method or within `parametrics` module itself.  The
    "public" `get_pval` function should always be used by other modules (which
    will access the cached pre-computed parameter values).

    NOTE: this function will return 0.0 if the parameter is not a computed
    parameter or is not defined for the specified object.

    Args:
        oid (str): the oid of the Identifiable that has the parameter
        variable (str): the variable whose context value is to be computed
        context_id (str): id of the context

    Keyword Args:
        allow_nan (bool): allow NaN as a value for cases in which the
            object or the parameter doesn't exist or the parameter value is
            not set
    """
    # NOTE: uncomment debug logging for EXTREMELY verbose debugging output
    # log.debug('* _compute_pval() for variable "{}"'.format(variable))
    # log.debug('                  of item with oid "{}"'.format(oid))
    # log.debug('                  in context "{}"'.format(context_id))
    val = 0.0
    # NOTE:  THE OBJECT DOES NOT ALWAYS HAVE TO HAVE THE VARIABLE
    # if oid not in parameterz or not parameterz[oid].get(variable):
        # return val
    pid = get_parameter_id(variable, context_id)
    pdz = parm_defz.get(pid, {})
    if not pdz:
        # log.debug('  "{}" not found in parm_defz'.format(pid))
        # log.debug('  in _compute_pval for oid "{}"'.format(oid))
        pass
    if pdz.get('computed'):
        # log.debug('  "{}" is computed ...'.format(pid))
        # look up compute function -- in the future, there may be a Relation
        # expression, found using the ParameterRelation relationship
        if not parameterz.get(oid, {}).get(variable):
            # if object does not have the base parameter (variable), the
            # computed parameter has no meaning for it
            obj_parms = parameterz.get(oid)
            if obj_parms and obj_parms.get(pid):
                # if the object has the computed parameter, it is invalid;
                # delete it ...
                del obj_parms[pid]
            return val
        compute = COMPUTES.get((variable, context_id))
        if compute:
            # log.debug('  compute function is {!s}'.format(getattr(
                                        # compute, '__name__', None)))
            val = compute(oid, variable) or 0.0
            # log.debug('  value is {}'.format(val))
        else:
            return val
            # log.debug('  compute function not found.')
            # val = 'undefined'
        dims = pdz.get('dimensions')
        units = in_si.get(dims)
        if val != 'undefined':
            parameterz[oid][pid] = dict(value=val, units=units,
                                        mod_datetime=str(dtstamp()))
    elif oid in parameterz:
        # msg = '  "{}" is not computed; getting value ...'.format(pid)
        # log.debug(msg)
        parm = parameterz[oid].get(pid) or {}
        val = parm.get('value') or 0.0
    return val

def set_pval(oid, pid, value, units=None, mod_datetime=None, local=True):
    """
    Set the value of a parameter instance for the specified object to the
    specified value, as expressed in the specified units (or in base units if
    units are not specified).  Note that parameter values are stored in SI
    (mks) base units, so if units other than base units are specified, the
    value is converted to base units before setting.

    Args:
        oid (str): the oid of the Modelable that has the parameter
        pid (str): the parameter 'id'
        value (TBD): value should be of the datatype specified by
            the parameter object's definition.range_datatype

    Keyword Args:
        units (str): the units in which `value` is expressed; None implies
            SI (mks) base units
        mod_datetime (str): mod_datetime string of the parameter (if the action
            originates locally, this will be None and a datetime stamp will be
            generated)
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # NOTE: uncomment debug logging for EXTREMELY verbose debugging output
    # log.debug('* set_pval({}, {}, {})'.format(oid, pid, str(value)))
    if not oid:
        # log.debug('  no oid provided; ignoring.')
        return False
    pd = parm_defz.get(pid)
    if not pd:
        # log.debug('  parameter "{}" is not defined; ignoring.'.format(pid))
        return False
    if pd['computed']:
        # log.debug('  parameter is computed -- not setting.')
        return False
    ######################################################################
    # NOTE: henceforth, if the parameter whose value is being set is not
    # present it will be added (SCW 2019-09-26)
    ######################################################################
    parm = parameterz.get(oid, {}).get(pid, {})
    if not parm:
        # NOTE:  add_parameter() now checks if base parameter has been assigned
        # and if not, assigns it and returns True
        added = add_parameter(oid, pid)
        if not added:
            # if the parameter cannot be added, it normally implies that its
            # base parameter has not been defined ...
            # log.debug('  parameter could not be added (see log).')
            return False
        # else:
            # log.debug('  parameter either exists or was added.')
    try:
        # cast value to range_datatype before setting
        pdz = parm_defz.get(pid)
        if not pdz:
            # log.debug('  parameter definition not found, quitting.')
            return False
        dt_name = pdz['range_datatype']
        dtype = DATATYPES[dt_name]
        if value:
            value = dtype(value)
        else:
            value = NULL.get(dt_name, 0.0)
        if units is not None and units not in ["$", "%"]:
            # TODO:  validate units (ensure they are consistent with dims)
            try:
                quan = value * ureg.parse_expression(units)
                quan_base = quan.to_base_units()
                converted_value = quan_base.magnitude
            except:
                # TODO: notify end user if units could not be parsed!
                # ... for now, use base units
                # log.debug('  could not parse units "{}" ...'.format(units))
                dims = pdz.get('dimensions')
                units = in_si.get(dims)
                # log.debug('  setting to base units: {}'.format(units))
                # if units parse failed, assume base units
                converted_value = value
            finally:
                parameterz[oid][pid]['units'] = units
        else:
            # None or "$" for units -> value is already in base units
            converted_value = value
        parameterz[oid][pid]['value'] = converted_value
        if local or mod_datetime is None:
            mod_datetime = str(dtstamp())
        parameterz[oid][pid]['mod_datetime'] = mod_datetime
        # dts = str(mod_datetime)
        # log.debug('  setting value: {}'.format(value))
        # log.debug('  setting mod_datetime: "{}"'.format(dts))
        return True
    except:
        # log.debug('  *** set_pval() failed:')
        # msg = '      value {} of datatype {}'.format(value, type(value))
        # log.debug(msg)
        # msg = '      caused something gnarly to happen ...'
        # log.debug(msg)
        # msg = '      so parm "{}" was not set for oid "{}"'.format(pid, oid)
        # log.debug(msg)
        return False

def get_pval_from_str(oid, pid, str_val, units=None, local=True):
    """
    Get the value of a parameter instance for the specified object from a
    string value, as expressed in the specified units (or in base units if
    units are not specified).  (Mainly for use in converting a parameter value
    to different units within the object editor,
    `p.node.gui.pgxnobject.PgxnObject`.)

    Args:
        oid (str): the oid of the Modelable that has the parameter
        pid (str): the parameter 'id'
        str_val (str): string value

    Keyword Args:
        units (str): the units in which the parameter value is expressed; None
            SI (mks) base units
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # This log msg is only needed for extreme debugging -- `set_pval()` is
    # called at the end and will log essentially the same information ...
    # log.debug('* get_pval_from_str({}, {}, {})'.format(oid, pid,
                                                           # str(str_val)))
    try:
        radt = parm_defz[pid].get('range_datatype')
        if radt in ['int', 'float']:
            dtype = DATATYPES.get(radt)
            num_fmt = prefs.get('numeric_format')
            if num_fmt == 'Thousands Commas' or not num_fmt:
                val = dtype(str_val.replace(',', ''))
            else:
                # this should work for both 'Scientific Notation' and
                # 'No Commas'
                val = dtype(str_val)
        else:
            val = str_val
        if parm_defz[pid].get('dimensions') == 'percent':
            val = 0.01 * float(val)
        return val
    except:
        # if unable to cast a value, do nothing (and log it)
        # TODO:  more form validation!
        # msg = 'get_pval_from_string() could not convert string "{}"'
        # log.debug('* {}'.format(msg.format(str_val)))
        pass

def set_pval_from_str(oid, pid, str_val, units=None, mod_datetime=None,
                      local=True):
    """
    Set the value of a parameter instance for the specified object from a
    string value, as expressed in the specified units (or in base units if
    units are not specified).  (Mainly for use in saving input from the object
    editor, `p.node.gui.pgxnobject.PgxnObject`.)

    Args:
        oid (str): the oid of the Modelable that has the parameter
        pid (str): the parameter 'id'
        str_val (str): string value

    Keyword Args:
        units (str): the units in which the parameter value is expressed; None
            SI (mks) base units
        mod_datetime (str): mod_datetime string of the parameter (if the action
            originates locally, this will be None and a datetime stamp will be
            generated)
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # This log msg is only needed for extreme debugging -- `set_pval()` is
    # called at the end and will log essentially the same information ...
    # log.debug('* set_pval_from_str({}, {}, {})'.format(oid, pid,
                                                           # str(str_val)))
    try:
        pd = parm_defz.get(pid, {})
        radt = pd.get('range_datatype')
        if radt in ['int', 'float']:
            dtype = DATATYPES.get(radt)
            num_fmt = prefs.get('numeric_format')
            if num_fmt == 'Thousands Commas' or not num_fmt:
                val = dtype(str_val.replace(',', ''))
            else:
                # this should work for both 'Scientific Notation' and
                # 'No Commas'
                val = dtype(str_val)
        else:
            val = str_val
        if pd.get('dimensions') == 'percent':
            val = 0.01 * float(val)
        set_pval(oid, pid, val, units=units, mod_datetime=str(mod_datetime),
                 local=local)
    except:
        # if unable to cast a value, do nothing (and log it)
        # TODO:  more form validation!
        # msg = 'set_pval_from_str() could not convert string "{}".'
        # log.debug('* {}'.format(msg.format(str_val)))
        pass

def compute_assembly_parameter(product_oid, variable):
    """
    Compute the total assembly value of a linearly additive variable (e.g.,
    mass, power consumption, data rate) for a product based on the recursively
    summed values of the parameter over all of the product's known components.
    If no components are defined for the product, simply return the value of
    the parameter as specified for the product, or the default (usually 0).

    CAUTION: this will obviously return a wildly inaccurate value if the
    list of components in a specified assembly is incomplete.

    Args:
        product_oid (str): the oid of the Product whose total parameter is
            being estimated
        variable (str): variable for which the assembly value is being computed
    """
    # This logging is VERY verbose, even for debugging!
    # log.debug('* compute_assembly_parameter()')
    if (product_oid in parameterz and variable in parameterz[product_oid]):
        radt = parm_defz[variable]['range_datatype']
        dtype = DATATYPES[radt]
        # cz, if it exists, will be a list of namedtuples ...
        cz = componentz.get(product_oid)
        if cz:
            # dtype cast is used here in case some component didn't have this
            # parameter or didn't exist and we got a 0.0 value for it ...
            summation = fsum(
              [dtype(compute_assembly_parameter(c.oid, variable) * c.quantity)
               for c in cz])
            return round_to(summation)
        else:
            # if the product has no known components, return its specified
            # value for the variable (note that the default here is 0.0)
            return get_pval(product_oid, variable)
    else:
        return 0.0

# NOTE: in the new parameter paradigm, the CBE and Contingency are context
# parameters -- this function must be rewritten!
def compute_mev(oid, variable):
    """
    Compute the Maximum Expected Value of a parameter based on its Current Best
    Estimate (CBE) value and the percent contingency specified for it.

    Args:
        oid (str): the oid of the Modelable containing the parameters
        variable (str): the `variable` of the parameter

    Keyword Args:
        default (any): a value to be returned if the parameter is not found
    """
    # log.debug('* compute_mev "{}": "{}"'.format(oid, variable))
    if oid not in parameterz or variable not in parameterz[oid]:
        return 0.0
    ctgcy_val = get_pval(oid, variable + '[Ctgcy]')
    if not ctgcy_val:
        # log.debug('  contingency not set --')
        # log.debug('  setting default value (30%) ...')
        # if Contingency value is 0 or not set, set to default value of 30%
        ctgcy_val = 0.3
        pid = variable + '[Ctgcy]'
        parameterz[oid][pid] = {'value': ctgcy_val, 'units': '%',
                                'mod_datetime': str(dtstamp())}
    factor = ctgcy_val + 1.0
    base_val = _compute_pval(oid, variable, 'CBE')
    # extremely verbose logging -- uncomment only for intense debugging
    # log.debug('* compute_mev: base parameter value is {}'.format(base_val))
    # log.debug('           base parameter type is {}'.format(
                                                            # type(base_val)))
    if isinstance(base_val, int):
        return round_to(int(factor * base_val))
    elif isinstance(base_val, float):
        return round_to(factor * base_val)
    else:
        return 0.0

def compute_margin(usage_oid, variable, default=0):
    """
    Compute the "Margin" for the specified variable (base parameter) at the
    specified function or system role. So far, "Margin" is only defined for
    performance requirements that specify a maximum or "Not To Exceed" value,
    and is computed as (NTE-CBE)/CBE, where CBE is the Current Best Estimate of
    the corresponding parameter of the system or component to which the
    requirement is currently allocated.

    Args:
        usage_oid (str): the oid of the usage (Acu or ProjectSystemUsage) to
            which a performance requirement for the specified variable is
            allocated
        variable (str): name of the variable associated with parameter
            constrained by the performance requirement

    Keyword Args:
        default (any): a value to be returned if the parameter is not found
    """
    # log.debug('* compute_margin()')
    # log.debug('  using req_allocz: {}'.format(str(req_allocz)))
    # find requirements allocated to the specified usage and constraining the
    # specified variable
    allocated_req_oids = [req_oid for req_oid in req_allocz
                          if req_allocz[req_oid][0] == usage_oid
                          and req_allocz[req_oid][3] == variable]
    if not allocated_req_oids:
        # no requirement constraining the specified variable is allocated to
        # this usage
        # txt = 'usage "{}" has no reqt allocated to it constraining "{}".'
        # log.debug('  {}'.format(txt.format(usage_oid, variable)))
        return 'undefined'
    # for now, assume there is only one reqt that satisfies
    req_oid = allocated_req_oids[0]
    usage_oid, obj_oid, alloc_ref, pid, constraint = req_allocz[req_oid]
    if constraint.constraint_type == 'maximum':
        nte = constraint.max
        nte_units = constraint.units
        # convert NTE value to base units, if necessary
        quan = nte * ureg.parse_expression(nte_units)
        quan_base = quan.to_base_units()
        converted_nte = quan_base.magnitude
    else:
        # txt = 'constraint_type is "{}"; ignored (for now).'
        # log.debug('  {}'.format(txt.format(constraint.constraint_type)))
        return 'undefined'
    mev = _compute_pval(obj_oid, variable, 'MEV')
    # convert NTE value to base units, if necessary
    quan = nte * ureg.parse_expression(nte_units)
    quan_base = quan.to_base_units()
    converted_nte = quan_base.magnitude
    # log.debug('  compute_margin: nte is {}'.format(converted_nte))
    # log.debug('                  mev is {}'.format(mev))
    if mev == 0:   # NOTE: 0 == 0.0 evals to True
        # not defined (division by zero)
        # TODO:  implement a NaN or "Undefined" ...
        return 'undefined'
    # msg = '- {} NTE specified for allocation to "{}" -- computing margin ...'
    # log.debug(msg.format(pid, alloc_ref))
    margin = round_to(((converted_nte - mev) / converted_nte))
    # log.debug('  ... margin is {}%'.format(margin * 100.0))
    return margin

def compute_requirement_margin(req_oid, default=0):
    """
    Compute the "Margin" for the specified performance requirement. So far,
    "Margin" is only defined for performance requirements that specify a
    maximum or "Not To Exceed" value, and is computed as (NTE-CBE)/CBE, where
    CBE is the Current Best Estimate of the corresponding parameter of the
    system or component to which the requirement is currently allocated.

    Args:
        req_oid (str): the oid of the performance requirement for which margin
            is to be computed

    Keyword Args:
        context (str): the `id` of the context that defines the margin (for
            now, the only supported context is 'NTE', so context is ignored)
        default (any): a value to be returned if the parameter is not found

    Return:
        allocated_to_oid, parameter_id, margin (tuple)
    """
    # log.debug('* compute_requirement_margin()')
    if req_oid not in req_allocz:
        # TODO: notify user 
        msg = 'Requirement {} is not allocated.'.format(req_oid)
        return (None, None, None, None, msg)
    usage_oid, obj_oid, alloc_ref, pid, constraint = req_allocz[req_oid]
    if not pid:
        msg = 'Requirement {} is not a performance reqt.'.format(req_oid)
        return (None, None, None, None, msg)
    if constraint.constraint_type == 'maximum':
        nte = constraint.max
        nte_units = constraint.units
        # convert NTE value to base units, if necessary
        quan = nte * ureg.parse_expression(nte_units)
        quan_base = quan.to_base_units()
        converted_nte = quan_base.magnitude
    else:
        msg = 'Constraint type is not "maximum" -- cannot handle (yet).'
        # txt = 'constraint_type is "{}"; ignored (for now).'
        # log.debug('  {}'.format(txt.format(constraint.constraint_type)))
        return (None, pid, None, None, msg)
    if not obj_oid:
        msg = 'Requirement is not allocated properly (no Acu or PSU).'
        return (None, pid, nte, nte_units, msg)
    elif obj_oid == 'pgefobjects:TBD':
        msg = 'Margin cannot be computed for unknown or TBD object.'
        return (usage_oid, pid, nte, nte_units, msg)
    mev = _compute_pval(obj_oid, pid, 'MEV')
    # log.debug('  compute_margin: nte is {}'.format(converted_nte))
    # log.debug('                  mev is {}'.format(mev))
    if mev == 0:   # NOTE: 0 == 0.0 evals to True
        # not defined (division by zero)
        # TODO:  implement a NaN or "Undefined" ...
        msg = 'MEV value for {} is 0; cannot compute margin.'.format(pid)
        return (usage_oid, pid, nte, nte_units, msg)
    # msg = '- {} NTE specified for allocation to "{}" -- computing margin ...'
    # log.debug(msg.format(pid, alloc_ref))
    # float cast is unnec. because python 3 division will do the right thing
    margin = round_to(((converted_nte - mev) / converted_nte))
    # log.debug('  ... margin is {}%'.format(margin * 100.0))
    return (usage_oid, pid, nte, nte_units, margin)

# the COMPUTES dict maps variable and context id to applicable compute
# functions
COMPUTES = {
    ('m', 'CBE'):      compute_assembly_parameter,
    ('m', 'Total'):    compute_assembly_parameter,
    ('m', 'MEV'):      compute_mev,
    ('m', 'Margin'):   compute_margin,
    ('P', 'CBE'):      compute_assembly_parameter,
    ('P', 'Total'):    compute_assembly_parameter,
    ('P', 'MEV'):      compute_mev,
    ('P', 'Margin'):   compute_margin,
    ('R_D', 'CBE'):    compute_assembly_parameter,
    ('R_D', 'Total'):  compute_assembly_parameter,
    ('R_D', 'MEV'):    compute_mev,
    ('R_D', 'Margin'): compute_margin
    }

################################################
# DATA ELEMENT SECTION
################################################

# DATA ELEMENT CACHES ##################################################

# de_defz:  runtime cache of data element definitions
# purpose:  to enable fast lookup of data element metadata
# format:  {data element id: {data element properties}
#                             ...}}
# ... where data element properties are:
# ------------------------------------------------------
# name, description, label, range_datatype, mod_datetime
# ------------------------------------------------------
# NOTE:  although "label" (a formatted label to use as a column header) is not
# an attribute of DataElementDefinition, the label item can be set from a data
# element structure that is set in the application's "config" file, which
# create_de_defz() will use to update de_defz after populating it from the db
# DataElementDefinition objects.
de_defz = {}

# data_elementz:  persistent** cache of assigned data element values
#              ** persisted in the file 'data_elements.json' in the
#              application home directory -- see the orb functions
#              `_save_data_elementz` and `_load_data_elementz`
# format:  {oid : {'data element id': {data element properties}
#                   ...}}
# ... where data element properties are:
# -------------------
# value, mod_datetime
# -------------------
data_elementz = {}

def serialize_des(oid):
    """
    Args:
        oid (str):  the oid of the object whose data elements are to be
            serialized.

    Serialize the data elements associated with an object.  Basically, this
    function is only required to serialize the `mod_datetime` value of each
    data element.

    IMPLEMENTATION NOTE:  uses deepcopy() to avoid side-effects to the
    `data_elementz` dict.
    """
    if oid in data_elementz:
        return deepcopy(data_elementz[oid])
    else:
        return {}

def deserialize_des(oid, ser_des, cname=None):
    """
    Deserialize a serialized object's `data_elements` dictionary.

    Args:
        oid (str):  oid attr of the object to which the data elements are
            assigned
        ser_des (dict):  the serialized data elements dictionary

    Keyword Args:
        cname (str):  class name of the object to which the parameters are
            assigned (only used for logging)
    """
    # if cname and ser_des:
        # log.debug('* deserializing data elements for "{}" ({})...'.format(
                                                                  # oid, cname))
        # log.debug('  - data elements: {}'.format(ser_des))
    # elif ser_des:
        # log.debug('* deserializing data elements for oid "{}")...'.format(
                                                                         # oid))
        # log.debug('  - data elements: {}'.format(ser_des))
    if not ser_des:
        # log.debug('  object with oid "{}" has no data elements'.format(
                                                                      # oid))
        return
    if oid not in data_elementz:
        data_elementz[oid] = {}
    for deid, de in ser_des.items():
        mod_dt = de['mod_datetime']
        if deid in de_defz:
            if ((data_elementz[oid].get(deid) and
                 mod_dt > data_elementz[oid][deid]['mod_datetime'])
                or not data_elementz[oid].get(deid)):
                # deserialized data element value is more recent or that
                # data element was not previously assigned
                data_elementz[oid] = ser_des
        else:
            # log_msg = 'unknown id found in data elements: "{}"'.format(deid)
            # log.debug('  - {}'.format(log_msg))
            # deid has no definition, so it should not be in data_elementz
            if deid in data_elementz.get(oid, {}):
                del data_elementz[oid][deid]
    ### FIXME:  it's dangerous to remove deids not in new_des, but we
    ### must deal with deleted parameters ...
    # deids = list(data_elementz[oid])
    # for deid in deids:
        # if deid not in new_des:
            # del data_elementz[oid][deid]
    # if data_elementz.get(oid):
        # log.debug('  - oid "{}" now has these data elements: {}.'.format(
                                         # oid, str(list(data_elementz[oid]))))

def load_data_elementz(json_path):
    """
    Load `data_elementz` dict from json file.
    """
    # log.debug('* _load_data_elementz() ...')
    if os.path.exists(json_path):
        with open(json_path) as f:
            serialized_des = json.loads(f.read())
        for oid, ser_des in serialized_des.items():
            deserialize_des(oid, ser_des)
        # log.debug('  - data_elementz cache loaded.')
    else:
        # log.debug('  - "data_elements.json" was not found.')
        pass

def save_data_elementz(json_path):
    """
    Save `data_elementz` dict to a json file.
    """
    # log.debug('* _save_data_elementz() ...')
    serialized_data_elementz = {}
    try:
        for oid, obj_des in data_elementz.items():
            # NOTE: serialize_des() uses deepcopy()
            serialized_data_elementz[oid] = serialize_des(oid)
        with open(json_path, 'w') as f:
            f.write(json.dumps(serialized_data_elementz,
                               separators=(',', ':'),
                               indent=4, sort_keys=True))
        # log.debug('  ... data_elements.json file written.')
    except:
        # log.debug('  ... writing data_elements.json file failed!')
        pass

def update_de_defz(de_def_obj):
    """
    Update the `de_defz` cache when a new DataElementDefinition is created or
    modified.

    Args:
        de_def_obj (DataElementDefinition):  DataElementDefinition object
    """
    # log.debug('* update_de_defz')
    de_defz[de_def_obj.id] = {
        'name': de_def_obj.name,
        'description': de_def_obj.description,
        'range_datatype': de_def_obj.range_datatype,
        'mod_datetime': str(dtstamp())}

def add_data_element(oid, deid):
    """
    Add a new data element to an object, which means adding a data element's data
    structure to the `p.node.parametrics.data_elementz` dictionary under that
    objects's oid, if it does not already exist for the specified paramter.
    The data element data structure format is a dict with the following keys:

        value, mod_datetime

    Args:
        oid (str):  oid of the object that owns the data element
        deid (str):  the id of the data element
    """
    if oid not in data_elementz:
        data_elementz[oid] = {}
    # log.debug('* add_data_element("{}")'.format(deid))
    # [1] check if object already has that data element
    if deid in data_elementz[oid]:
        # if the object already has that data element, do nothing
        return True
    # [2] check for DataElementDefinition in db
    de_def = de_defz.get(deid)
    if not de_def:
        # if no DataElementDefinition exists for deid, pass
        # (maybe eventually raise TypeError)
        # log.debug('  - invalid: id "{}" has no definition.'.format(deid))
        return False
    # [3] check whether the data element has been assigned yet ...
    if not data_elementz[oid].get(deid):
        # the data element has not yet been assigned
        # log.debug('  - adding data element "{}" ...'.format(deid))
        # NOTE:  setting the data element's value is a separate operation -- when a
        # data element is created, its value is initialized to the appropriate "null"
        radt = de_def.get('range_datatype', 'str')
        de_defaults = config.get('de_defaults') or {}
        if de_defaults.get(deid):
            # if a default value is configured for this deid, override null
            dtype = DATATYPES[radt]
            value = dtype(de_defaults[deid])
        elif radt == 'float':
            value = 0.0
        elif radt == 'int':
            value = 0
        elif radt == 'boolean':
            value = False
        else:  # 'str' or 'text'
            value = ''
        data_elementz[oid][deid] = dict(
            value=value,   # consistent with dtype defined in `range_datatype`
            mod_datetime=str(dtstamp()))
        # log.debug('    data element "{}" added.'.format(deid))
        return True
    else:
        # log.debug('    data element "{}" was already there.'.format(deid))
        return True

def delete_data_element(oid, deid):
    """
    Delete a parameter from an object.  This should be rare and would only be
    necessary if the parameter is irrelevant to the object; therefore, the base
    variable and all related context parameters would be deleted.

    Args:
        oid (str):  oid of the object that owns the parameter
        deid (str):  `id` attribute of the parameter
    """
    # TODO: need to dispatch louie & pubsub messages!
    if oid in data_elementz and data_elementz[oid].get(deid):
        del parameterz[oid][deid]

def get_dval(oid, deid):
    """
    Return a cached data element value.

    Args:
        oid (str): the oid of the object that has the parameter
        deid (str): the data element 'id' value
    """
    # Too verbose -- only for extreme debugging ...
    # log.debug('* get_dval() ...')
    dedef = de_defz.get(deid)
    if not dedef:
        # log.debug('* get_dval: "{}" does not have a definition.'.format(deid))
        return None
    try:
        # for extreme debugging only ...
        val = data_elementz[oid][deid]['value']
        # log.debug('  value of {} is "{}" ({})'.format(deid, val, type(val)))
        return val
    except:
        val = NULL.get(dedef.get('range_datatype', 'str'))
        # log.debug('  [exception] value of {} is {} ({})'.format(deid,
                                                          # val, type(val)))
        return val

def get_dval_as_str(oid, deid):
    """
    Return a cached data element value a string for display and editing in UI.
    (Used in the object editor, `p.node.gui.pgxnobject.PgxnObject`, the
    dashboard, and the DataGrid.)

    Args:
        oid (str): the oid of the object that has the parameter
        deid (str): the `id` of the data element
    """
    return str(get_dval(oid, deid))

def set_dval(oid, deid, value, mod_datetime=None, local=True):
    """
    Set the value of a data element instance for the specified object to the
    specified value.

    Args:
        oid (str): the oid of the Modelable that has the data element
        deid (str): the data element 'id'
        value (TBD): value should be of the datatype specified by
            the data element object's definition.range_datatype

    Keyword Args:
        mod_datetime (str): string mod_datetime of the data element (if the
            action originates locally, this will be None and a datetime stamp
            will be generated)
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # NOTE: uncomment debug logging for EXTREMELY verbose debugging output
    # log.debug('* set_dval({}, {}, {})'.format(oid, deid, str(value)))
    if not oid:
        # log.debug('  no oid provided; ignoring.')
        return False
    dedef = de_defz.get(deid)
    if not dedef:
        # log.debug('  data element "{}" is not defined; ignoring.'.format(
                                                                    # deid))
        return False
    ######################################################################
    # NOTE: if the data element whose value is being set is not
    # present it will be added
    ######################################################################
    data_element = data_elementz.get(oid, {}).get(deid, {})
    if not data_element:
        if add_data_element(oid, deid):
            # log.debug('  data element either exists or was added.')
            pass
        else:
            # log.debug('  data element could not be added (see log).')
            return False
    try:
        # cast value to range_datatype before setting
        dt_name = dedef['range_datatype']
        dtype = DATATYPES[dt_name]
        if value:
            value = dtype(value)
        else:
            value = NULL.get(dt_name, 0.0)
        data_elementz[oid][deid]['value'] = value
        if local or mod_datetime is None:
            mod_datetime = str(dtstamp())
        data_elementz[oid][deid]['mod_datetime'] = mod_datetime
        # dts = str(mod_datetime)
        # log.debug('  setting value: {}'.format(value))
        # log.debug('  setting mod_datetime: "{}"'.format(dts))
        return True
    except:
        # log.debug('  *** set_dval() failed:')
        # msg = '      setting value {} of type {}'.format(value, type(value))
        # log.debug(msg)
        # msg = '      caused something gnarly to happen ...'
        # log.debug(msg)
        # msg = '      so data element "{}" was not set for oid "{}"'.format(
                                                                 # deid, oid)
        # log.debug(msg)
        return False

def set_dval_from_str(oid, deid, str_val, mod_datetime=None, local=True):
    """
    Set the value of a data element instance for the specified object from a
    string value.  (Mainly for use in saving input from the object editor,
    `p.node.gui.pgxnobject.PgxnObject`.)

    Args:
        oid (str): the oid of the Modelable that has the parameter
        pid (str): the parameter 'id'
        str_val (str): string value

    Keyword Args:
        mod_datetime (str): mod_datetime string of the parameter (if the action
            originates locally, this will be None and a datetime stamp will be
            generated)
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # This log msg is only needed for extreme debugging -- `set_pval()` is
    # called at the end and will log essentially the same information ...
    # log.debug('* set_dval_from_str({}, {}, {})'.format(oid, deid,
                                                           # str(str_val)))
    try:
        de_def = de_defz.get(deid, {})
        radt = de_def.get('range_datatype', 'str')
        if radt in ['int', 'float']:
            dtype = DATATYPES.get(radt)
            num_fmt = prefs.get('numeric_format')
            if num_fmt == 'Thousands Commas' or not num_fmt:
                val = dtype(str_val.replace(',', ''))
            else:
                # this should work for both 'Scientific Notation' and
                # 'No Commas'
                val = dtype(str_val)
        else:
            val = str_val
        set_dval(oid, deid, val, mod_datetime=str(mod_datetime), local=local)
    except:
        # if unable to cast a value, do nothing (and log it)
        # TODO:  more form validation!
        # log.debug('  could not convert string "{}" ...'.format(str_val))
        pass

def add_default_data_elements(obj):
    """
    Assign the configured or preferred default data elements to an object.

    Args:
        obj (Identifiable):  the object to receive data elements
    """
    # log.debug('* adding default data elements to object "{}"'.format(
                                                                 # obj.id))
    # Configured Parameters are currently defined by the 'dashboard'
    # configuration (in future that may be augmented by Parameters
    # referenced by, e.g., a ProductType and/or a ModelTemplate, both of
    # which are essentially collections of ParameterDefinitions.
    deids = OrderedSet()
    cname = obj.__class__.__name__
    deids |= OrderedSet(DEFAULT_CLASS_DATA_ELEMENTS.get(cname, []))
    # TODO: let user set default data elements in their prefs
    if cname == 'HardwareProduct':
        # default for "default_parms" in config:  mass, power, data rate
        # (config is read in p.node.gui.startup, and will be overridden by
        # prefs['default_parms'] if it is set
        deids |= OrderedSet(prefs.get('default_data_elements')
                            or config.get('default_data_elements')
                            or ['TRL', 'Vendor'])
        if obj.product_type:
            deids |= OrderedSet(DEFAULT_PRODUCT_TYPE_DATA_ELMTS.get(
                                obj.product_type.id, []))
    # add default parameters first ...
    # log.debug('  - adding data elements {} ...'.format(str(deids)))
    for deid in deids:
        add_data_element(obj.oid, deid)

