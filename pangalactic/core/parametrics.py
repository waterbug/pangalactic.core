"""
Functions to support Parameters and Relations
"""
from collections import namedtuple
from decimal     import Decimal
from math        import floor, fsum, log10

# pangalactic
from pangalactic.core                 import config, prefs
from pangalactic.core.datastructures  import OrderedSet
from pangalactic.core.meta            import (SELECTABLE_VALUES,
                                              DEFAULT_CLASS_PARAMETERS,
                                              DEFAULT_PRODUCT_TYPE_PARAMETERS)
from pangalactic.core.units           import in_si, ureg
from pangalactic.core.utils.meta      import get_parameter_definition_oid
from pangalactic.core.utils.datetimes import dtstamp


DATATYPES = SELECTABLE_VALUES['range_datatype']
# NULL = {True: np.nan, False: 0.0}
TWOPLACES = Decimal('0.01')

# CACHES ##################################################################

# componentz:  runtime component cache
# purpose:  enable fast computation of assembly parameters
# format:  {product.oid : list of Comp('oid', 'quantity') namedtuples}
componentz = {}
Comp = namedtuple('Comp', 'oid quantity')

# parm_defz:  runtime cache of parameter definitions
# purpose:  enable fast lookup of parameter metadata & compact representation
#           of parameters as (value, units, mod_datetime)
# format:  {'parameter_id': {parameter properties}
#                            ...}}
# ... where parameter definition properties are:
# name, variable, context, description, dimensions, range_datatype, computed,
# mod_datetime
parm_defz = {}

# parameterz:  persistent cache of assigned parameter values
# format:  {object.oid : {'parameter_id': {parameter properties}
#                         ...}}
# ... where parameter properties are:
# value, units, mod_datetime
parameterz = {}

# parmz_by_dimz:  runtime cache that maps dimensions to parameter definitions
# format:  {dimension : [ids of ParameterDefinitions having that dimension]}
parmz_by_dimz = {}
###########################################################################


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

def refresh_componentz(orb, product):
    """
    Refresh the `componentz` cache for a Product instance. This must be called
    before calling orb.recompute_parmz() whenever a new Acu is created,
    deleted, or modified.  The 'componentz' dictionary has the form

        {product.oid : list of Comp('oid', 'quantity') namedtuples}

    where the list of `Comp` namedtuples is created from `product.components`
    (Acus of the product), using Acu.component.oid and Acu.quantity.

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
        product (Product):  the Product instance
    """
    if product:
        # orb.log.debug('[orb] refresh_componentz({})'.format(product.id))
        componentz[product.oid] = [Comp._make((acu.component.oid,
                                               acu.quantity or 1))
                                   for acu in product.components
                                   if acu.component
                                   and acu.component.oid != 'pgefobjects:TBD']

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

def create_parm_defz(orb):
    """
    Create the `parm_defz` cache of ParameterDefinitions, in the format:

        {parameter_id : {name, variable, context, context_type, description,
                         dimensions, range_datatype, computed, mod_datetime},
         ...}

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
    """
    orb.log.debug('[orb] create_parm_defz')
    pds = orb.get_by_type('ParameterDefinition')
    # first, the "simple variable" parameters ...
    parm_defz.update(
        {pd.id :
         {'name': pd.name,
          'variable': pd.id,
          'context': None,
          'context_type': None,
          'description': pd.description,
          'dimensions': pd.dimensions,
          'range_datatype': pd.range_datatype,
          'computed': False,
          'mod_datetime':
              str(getattr(pd, 'mod_datetime', '') or dtstamp())
          } for pd in pds}
          )
    # add PDs for the descriptive contexts (CBE, Contingency, MEV) for the
    # variables (Mass, Power, Datarate) for which functions have been defined
    # to compute the CBE and MEV values
    all_contexts = orb.get_by_type('ParameterContext')
    for pid in ['m', 'P', 'R_D']:
        pd = orb.select('ParameterDefinition', id=pid)
        for c in all_contexts:
            add_context_parm_def(orb, pd, c)
    # all float-valued parameters should have associated Contingency parms
    float_pds = [pd for pd in pds if pd.range_datatype == 'float']
    contingency = orb.select('ParameterContext', name='Contingency')
    for float_pd in float_pds:
        contingency_pid = get_parameter_id(float_pd.id, contingency.id)
        if contingency_pid not in parm_defz:
            add_context_parm_def(orb, float_pd, contingency)

def add_context_parm_def(orb, pd, c):
    """
    Add a context parameter definition to the `parm_defz` cache.

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
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

def update_parm_defz(orb, pd):
    """
    Update the `parm_defz` cache when a new ParameterDefinition is created.

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
        pd (ParameterDefinition):  ParameterDefinition being added
    """
    orb.log.debug('[orb] update_parm_defz')
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

def create_parmz_by_dimz(orb):
    """
    Create the `parmz_by_dimz` cache, where the cache has the form

        {dimension : [ids of ParameterDefinitions having that dimension]}

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
    """
    orb.log.debug('[orb] create_parmz_by_dimz')
    pds = orb.get_by_type('ParameterDefinition')
    dimz = set([pd.dimensions for pd in pds])
    parmz_by_dimz.update({dim : [pd.id for pd in pds if pd.dimensions == dim]
                          for dim in dimz})

def update_parmz_by_dimz(orb, pd):
    """
    Refresh the `parmz_by_dimz` cache when a ParameterDefinition is created or
    modified.  The cache has the form

        {dimension : [ids of ParameterDefinitions having that dimension]}

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
        pd (ParameterDefinition):  ParameterDefinition being added or modified
    """
    # orb.log.debug('[orb] refresh_parmz_by_dimz')
    if pd.dimensions in parmz_by_dimz:
        parmz_by_dimz[pd.dimensions].append(pd.id)
    else:
        parmz_by_dimz[pd.dimensions] = [pd.id]

def add_parameter(orb, oid, variable, context=None):
    """
    Add a new parameter to an object, which really means adding a parameter
    data structure to the `p.node.parametrics.parameterz` dictionary under that
    objects's oid.  The parameter data structure format is a dict with the
    following keys:

        value, units, mod_datetime

    NOTE:  'units' here refers to the preferred units in which to *display* the
    parameter's value, not the units of the 'value', which are *always* mks
    base units.

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
        oid (str):  oid of the object that owns the parameter
        variable (str):  the variable of the parameter
        context (str):  the `id` of the context of the parameter
    """
    if oid not in parameterz:
        parameterz[oid] = {}
    pid = get_parameter_id(variable, context)
    # orb.log.debug('[orb] add_parameter "{!s}"'.format(pid))
    if pid in parameterz[oid]:
        # if the object already has that parameter, do nothing
        return
    # check for ParameterDefinition of base variable in db
    pd = orb.get(get_parameter_definition_oid(variable))
    if not pd:
        # for now, if no ParameterDefinition exists for pid, pass
        # (maybe eventually raise TypeError)
        orb.log.debug(
            '* add_parameter: variable "{!s}" is not defined.'.format(
                                                             variable))
        return
    pdz = parm_defz.get(pid)
    if not pdz:
        # if not in parm_defz, add it:
        pdz = {pd.id :
               {'name': pd.name,
                'variable': pd.id,
                'context': None,
                'context_type': None,
                'description': pd.description,
                'dimensions': pd.dimensions,
                'range_datatype': pd.range_datatype,
                'computed': False,
                'mod_datetime':
                    str(getattr(pd, 'mod_datetime', '') or dtstamp())
                }}
        parm_defz.update(pdz)
    # NOTE:  setting the parameter's value is a separate operation -- when a
    # parameter is created, its value is initialized to the appropriate "null"
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
        value=value,   # consistent with datatype defined in `range_datatype`
        units=in_si.get(dims),   # SI units consistent with `dimensions`
        mod_datetime=str(dtstamp()))

def add_default_parameters(orb, obj):
    """
    Assign the configured or preferred default parameters to an object.

    Args:
        orb (Uberorb):  the orb (singleton)
        obj (Identifiable):  the object to receive parameters
    """
    # orb.log.debug('[orb] add default parameters to object "{!s}"'.format(
                                                                # obj.oid))
    # Configured Parameters are currently defined by the 'dashboard'
    # configuration (in future that may be augmented by Parameters
    # referenced by, e.g., a ProductType and/or a ModelTemplate, both of
    # which are essentially collections of ParameterDefinitions.
    pids = OrderedSet()
    cname = obj.__class__.__name__
    pids |= OrderedSet(DEFAULT_CLASS_PARAMETERS.get(cname, []))
    # TODO: let user set default parameters in their prefs
    if isinstance(obj, orb.classes['HardwareProduct']):
        # default for "default_parms" in config:  mass, power, data rate
        # (config is read in p.node.gui.startup, and will be overridden by
        # prefs['default_parms'] if it is set
        pids |= OrderedSet(prefs.get('default_parms')
                           or config.get('default_parms')
                           or ['m', 'P', 'R_D'])
        if obj.product_type:
            pids |= OrderedSet(DEFAULT_PRODUCT_TYPE_PARAMETERS.get(
                               obj.product_type.id, []))
    # add default parameters first ...
    # orb.log.debug('      adding parameters {!s} ...'.format(str(pids)))
    for pid in pids:
        add_parameter(orb, obj.oid, pid)

def add_product_type_parameters(orb, obj, pt):
    """
    Assign the parameters associated with the specified product type to an
    object.

    Args:
        orb (Uberorb):  the orb (singleton)
        obj (Identifiable):  the object to receive parameters
        pt (ProductType):  the product type
    """
    # orb.log.debug('* assigning parameters for product type "{}"'.format(pt.id))
    # then check for parameters specific to the product_type, if any
    if pt:
        # check if the product_type has parameters
        pt_parmz = parameterz.get(pt.oid)
        if pt_parmz:
            # if so, replicate them directly (with values)
            for pid in pt_parmz:
                parameterz[obj.oid][pid] = pt_parmz[pid].copy()

def delete_parameter(orb, oid, pid):
    """
    Delete a parameter from an object.

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
        oid (str):  oid of the object that owns the parameter
        pid (str):  `id` attribute of the parameter
    """
    # TODO (URGENT!): need to dispatch louie & pubsub messages!
    if oid in parameterz:
        if parameterz[oid].get(pid):
            del parameterz[oid][pid]
        else:
            # object doesn't have that parameter; ignore
            return
    else:
        # object doesn't have any parameters; ignore
        return

def get_pval(orb, oid, pid, allow_nan=False):
    """
    Return a cached parameter value in base units.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        obj (Identifiable): the object that has the parameter
        pid (str): the parameter 'id' value
    """
    # Too verbose -- only for extreme debugging ...
    # orb.log.debug('* get_pval() ...')
    pdz = parm_defz.get(pid)
    if not pdz:
        orb.log.debug('* get_pval: "{}" does not have a definition.'.format(
                                                                        pid))
        return
    try:
        # for extreme debugging only ...
        # orb.log.debug('  value of {} is {} ({})'.format(pid, val, type(val)))
        return parameterz[oid][pid]['value']
    except:
        # return NULL[allow_nan]
        return 0

def get_pval_as_str(orb, oid, pid, units=None, allow_nan=False):
    """
    Return a cached parameter value in the specified units (or in base units if
    not specified) as a formatted string, for display in UI.  (Used in the
    object editor, `p.node.gui.pgxnobject.PgxnObject` and the dashboard.)

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        obj (Identifiable): the object that owns the parameter
        pid (str): the `id` of the parameter

    Keyword Args:
        units (str):  units in which the return value should be expressed
        allow_nan (bool):  allow numpy NaN as a return value
    """
    # Too verbose -- only for extreme debugging ...
    # orb.log.debug('* get_pval_as_str(orb, {}, {})'.format(oid, pid))
    pdz = parm_defz.get(pid)
    if not pdz:
        # orb.log.debug('  - "{}" does not have a definition.'.format(pid))
        return '-'
    try:
        # convert based on dimensions/units ...
        dims = pdz.get('dimensions')
        # special cases for 'percent' and 'money'
        if dims == 'percent':
            # show percentage values in interface -- they will
            # later be saved (by set_pval) as .01 * value
            val = 100.0 * get_pval(orb, oid, pid)
        elif dims == 'money':
            # format with 2 decimal places
            val = get_pval(orb, oid, pid)
            if val is None:
                return ''
            elif val:
                return "{:,}".format(Decimal(val).quantize(TWOPLACES))
            else:
                return '0.00'
        else:
            base_val = get_pval(orb, oid, pid)
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
        # msg = '* get_pval_as_str(orb, {}, {})'.format(oid, pid)
        # msg += '  encountered an error.'
        # orb.log.debug(msg)

        # for production use, return '-' if the value causes error
        return '-'

def _compute_pval(orb, oid, variable, context_id, allow_nan=False):
    """
    Get the value of a parameter of the specified object, computing it if it is
    'computed' and caching the computed value in parameterz; otherwise,
    returning its value from parameterz.

    NOTE: this function is intended to be private, called only by the orb's
    `recompute_parmz` method or within `parametrics` module itself.  The
    "public" `get_pval` function should always be used by other modules (which
    will access the cached pre-computed parameter values).

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the Identifiable that has the parameter
        variable (str): the variable whose context value is to be computed
        context_id (str): id of the context

    Keyword Args:
        allow_nan (bool): allow NaN as a value for cases in which the
            object or the parameter doesn't exist or the parameter value is
            not set
    """
    # NOTE: uncomment debug logging for EXTREMELY verbose debugging output
    # orb.log.debug('* _compute_pval() for variable "{}"'.format(variable))
    # orb.log.debug('                  of item with oid "{}"'.format(oid))
    # orb.log.debug('                  in context "{}"'.format(context_id))
    val = 0.0
    # NOTE:  THE OBJECT DOES NOT ALWAYS HAVE TO HAVE THE VARIABLE
    # if oid not in parameterz or not parameterz[oid].get(variable):
        # return val
    pid = get_parameter_id(variable, context_id)
    pdz = parm_defz.get(pid, {})
    if not pdz:
        orb.log.debug('  "{}" not found in parm_defz'.format(pid))
        orb.log.debug('  in _compute_pval for oid "{}"'.format(oid))
    if pdz.get('computed'):
        # orb.log.debug('  "{}" is computed ...'.format(pid))
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
            # orb.log.debug('  compute function is {!s}'.format(getattr(
                                        # compute, '__name__', None)))
            val = compute(orb, oid, variable) or 0.0
            # orb.log.debug('  value is {}'.format(val))
        else:
            return val
            # orb.log.debug('  compute function not found.')
            # val = 'undefined'
        dims = pdz.get('dimensions')
        units = in_si.get(dims)
        if val != 'undefined':
            parameterz[oid][pid] = dict(value=val, units=units,
                                        mod_datetime=str(dtstamp()))
    else:
        # msg = '  "{}" is not computed; getting value ...'.format(pid)
        # orb.log.debug(msg)
        parm = parameterz[oid].get(pid) or {}
        val = parm.get('value') or 0.0
    return val

def set_pval(orb, oid, pid, value, units=None, mod_datetime=None, local=True):
    """
    Set the value of a parameter instance for the specified object to the
    specified value, as expressed in the specified units (or in base units if
    units are not specified).  Note that parameter values are stored in SI
    (mks) base units, so if units other than base units are specified, the
    value is converted to base units before setting.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the Modelable that has the parameter
        pid (str): the parameter 'id'
        value (TBD): value should be of the datatype specified by
            the parameter object's definition.range_datatype

    Keyword Args:
        units (str): the units in which `value` is expressed; None implies
            SI (mks) base units
        mod_datetime (datetime): mod_datetime of the parameter (if the action
            originates locally, this will be None and a datetime stamp will be
            generated)
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # NOTE: uncomment debug logging for EXTREMELY verbose debugging output
    # orb.log.debug('* set_pval({}, {}, {})'.format(oid, pid, str(value)))
    if not oid:
        # orb.log.debug('  no oid provided; ignoring.')
        return
    pd = parm_defz.get(pid)
    if not pd:
        # orb.log.debug('  parameter "{}" is not defined; ignoring.'.format(pid))
        return
    if pd['computed']:
        # orb.log.debug('  parameter is computed -- not setting.')
        return
    ######################################################################
    # NOTE: henceforth, if the parameter whose value is being set is not
    # present it will be added (SCW 2019-09-26)
    ######################################################################
    parm = parameterz.get(oid, {}).get(pid, {})
    if not parm:
        # NOTE:  this is the case if
        # (1) that oid is not in parameterz or
        # (2) the object with that oid doesn't have that parameter
        # ... which should not happen very often, so debug logging is ok
        orb.log.debug('  parameter not found; adding.')
        add_parameter(orb, oid, pd['variable'], context=pd['context'])
    try:
        # cast value to range_datatype before setting
        pdz = parm_defz.get(pid)
        if not pdz:
            orb.log.debug('  parameter definition not found, quitting.')
            return
        dt_name = pdz['range_datatype']
        dtype = DATATYPES[dt_name]
        value = dtype(value)
        if units is not None and units != "$":
            # TODO:  validate units (ensure they are consistent with dims)
            try:
                quan = value * ureg.parse_expression(units)
                quan_base = quan.to_base_units()
                converted_value = quan_base.magnitude
            except:
                # TODO: notify end user if units could not be parsed!
                # ... for now, use base units
                orb.log.debug('  could not parse units "{}" ...'.format(units))
                dims = pdz.get('dimensions')
                units = in_si.get(dims)
                orb.log.debug('  setting to base units: {}'.format(units))
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
        # orb.log.debug('  setting value: {}'.format(value))
        # orb.log.debug('  setting mod_datetime: "{}"'.format(dts))
        orb.recompute_parmz()
    except:
        orb.log.debug('  *** set_pval() failed:')
        msg = '      value {} of datatype {}'.format(value, type(value))
        orb.log.debug(msg)
        msg = '      caused something gnarly to happen ...'
        orb.log.debug(msg)
        msg = '      so parm "{}" was not set for oid "{}"'.format(pid, oid)
        orb.log.debug(msg)

def get_pval_from_str(orb, oid, pid, str_val, units=None, mod_datetime=None,
                      local=True):
    """
    Get the value of a parameter instance for the specified object from a
    string value, as expressed in the specified units (or in base units if
    units are not specified).  (Mainly for use in converting a parameter value
    to different units within the object editor,
    `p.node.gui.pgxnobject.PgxnObject`.)

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the Modelable that has the parameter
        pid (str): the parameter 'id'
        str_val (str): string value

    Keyword Args:
        units (str): the units in which the parameter value is expressed; None
            SI (mks) base units
        mod_datetime (datetime): mod_datetime of the parameter (if the action
            originates locally, this will be None and a datetime stamp will be
            generated)
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # This log msg is only needed for extreme debugging -- `set_pval()` is
    # called at the end and will log essentially the same information ...
    # orb.log.debug('* set_pval_from_str({}, {}, {})'.format(oid, pid,
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
        orb.log.debug('  could not convert string "{}" ...'.format(str_val))
        orb.log.debug('  bailing out.')

def set_pval_from_str(orb, oid, pid, str_val, units=None, mod_datetime=None,
                      local=True):
    """
    Set the value of a parameter instance for the specified object from a
    string value, as expressed in the specified units (or in base units if
    units are not specified).  (Mainly for use in saving input from the object
    editor, `p.node.gui.pgxnobject.PgxnObject`.)

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the Modelable that has the parameter
        pid (str): the parameter 'id'
        str_val (str): string value

    Keyword Args:
        units (str): the units in which the parameter value is expressed; None
            SI (mks) base units
        mod_datetime (datetime): mod_datetime of the parameter (if the action
            originates locally, this will be None and a datetime stamp will be
            generated)
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # This log msg is only needed for extreme debugging -- `set_pval()` is
    # called at the end and will log essentially the same information ...
    # orb.log.debug('* set_pval_from_str({}, {}, {})'.format(oid, pid,
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
        set_pval(orb, oid, pid, val, units=units, mod_datetime=mod_datetime,
                 local=local)
    except:
        # if unable to cast a value, do nothing (and log it)
        # TODO:  more form validation!
        orb.log.debug('  could not convert string "{}" ...'.format(str_val))
        orb.log.debug('  bailing out.')

def compute_assembly_parameter(orb, product_oid, variable):
    """
    Compute the total assembly value of a linearly additive variable (e.g.,
    mass, power consumption, data rate) for a product based on the recursively
    summed values of the parameter over all of the product's known components.
    If no components are defined for the product, simply return the value of
    the parameter as specified for the product, or the default (usually 0).

    CAUTION: this may return a wildly inaccurate value for an incompletely
    specified assembly.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        product_oid (str): the oid of the Product whose total parameter is
            being estimated
        variable (str): variable for which the assembly value is being computed
    """
    # VERY verbose, even for debugging!
    # orb.log.debug('[parametrics] compute_assembly_parameter()')
    if (product_oid in parameterz and variable in parameterz[product_oid]):
        radt = parm_defz[variable]['range_datatype']
        dtype = DATATYPES[radt]
        # cz, if it exists, will be a list of namedtuples ...
        cz = componentz.get(product_oid)
        if cz:
            # dtype cast is used here in case some component didn't have this
            # parameter or didn't exist and we got a 0.0 value for it ...
            summation = fsum(
              [dtype(compute_assembly_parameter(orb, c.oid, variable) * c.quantity)
               for c in cz])
            return round_to(summation)
        else:
            # if the product has no known components, return its specified
            # value for the variable (note that the default here is 0.0)
            return get_pval(orb, product_oid, variable)
    else:
        return 0.0

# NOTE: in the new parameter paradigm, the CBE and Contingency are context
# parameters -- this function must be rewritten!
def compute_mev(orb, oid, variable):
    """
    Compute the Maximum Expected Value of a parameter based on its Current Best
    Estimate (CBE) value and the percent contingency specified for it.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the Modelable containing the parameters
        variable (str): the `variable` of the parameter

    Keyword Args:
        default (any): a value to be returned if the parameter is not found
    """
    # orb.log.debug('* compute_mev "{}": "{}"'.format(oid, variable))
    ctgcy_val = get_pval(orb, oid, variable + '[Ctgcy]')
    if not ctgcy_val:
        # orb.log.debug('  contingency not set --')
        # orb.log.debug('  setting default value (30%) ...')
        # if Contingency value is 0 or not set, set to default value of 30%
        ctgcy_val = 0.3
        pid = variable + '[Ctgcy]'
        parameterz[oid][pid] = {'value': ctgcy_val, 'units': '%',
                                'mod_datetime': str(dtstamp())}
    factor = ctgcy_val + 1.0
    base_val = _compute_pval(orb, oid, variable, 'CBE')
    # extremely verbose logging -- uncomment only for intense debugging
    # orb.log.debug('* compute_mev: base parameter value is {}'.format(base_val))
    # orb.log.debug('           base parameter type is {}'.format(
                                                            # type(base_val)))
    if isinstance(base_val, int):
        return round_to(int(factor * base_val))
    elif isinstance(base_val, float):
        return round_to(factor * base_val)
    else:
        return 0.0

def compute_margin(orb, oid, variable, default=0):
    """
    Compute the "Margin" for the specified parameter (variable) at the
    specified function or system role. So far, "Margin" is only defined for
    performance requirements that specify a maximum or "Not To Exceed" value,
    and is computed as (NTE-CBE)/CBE, where CBE is the Current Best Estimate of
    the corresponding parameter of the system or component to which the
    requirement is currently allocated.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the function (Acu) or system role
            (ProjectSystemUsage) to which a performance requirement for the
            specified variable is allocated
        variable (str): name of the variable associated with parameter
            constrained by the performance requirement

    Keyword Args:
        context (str): the `id` of the context that defines the margin (for
            now, the only supported context is 'NTE', so context is ignored)
        default (any): a value to be returned if the parameter is not found
    """
    allocation_node = orb.get(oid)
    allocated_to_system = False
    if hasattr(allocation_node, 'component'):
        obj_oid = getattr(allocation_node.component, 'oid', None)
    if hasattr(allocation_node, 'system'):
        obj_oid = getattr(allocation_node.system, 'oid', None)
        allocated_to_system = True
    if not obj_oid or obj_oid == 'pgefobjects:TBD':
        # orb.log.debug('  allocation is to unknown or TBD system.')
        return 0
    mev = _compute_pval(orb, obj_oid, variable, 'MEV')
    # find a performance requirement for the specified variable, allocated to
    # the allocation_node
    pd = orb.get(get_parameter_definition_oid(variable))
    if not pd:
        orb.log.info('  no parameter definition found for "{}".'.format(
                                                                variable))
        return 0
    # find all reqts allocated to the node
    if allocated_to_system:
        reqts = orb.search_exact(cname='Requirement',
                                 allocated_to_system=allocation_node)
    else:
        reqts = orb.search_exact(cname='Requirement',
                                 allocated_to_function=allocation_node)
    if not reqts:
        # orb.log.debug('  no reqts found with that allocation.')
        return 0
    # identify the relevant performance requirement
    perf_reqt = None
    for reqt in reqts:
        rel = reqt.computable_form
        if rel:
            prs = rel.correlates_parameters
            if prs:
                pd = prs[0].correlates_parameter
                if pd.id == variable:
                    perf_reqt = reqt
    if not perf_reqt:
        # orb.log.debug('  relevant performance requirement not found.')
        return 0
    # TODO:  here we would identify the type of constraint, but currently we
    # only support the NTE (maximum value) constraint
    try:
        nte = float(perf_reqt.req_maximum_value)
    except:
        # value was None or other non-numeric
        # orb.log.debug('  NTE not specified by the relevant requirement.')
        return 0
    nte_units = perf_reqt.req_units
    # convert NTE value to base units, if necessary
    quan = nte * ureg.parse_expression(nte_units)
    quan_base = quan.to_base_units()
    converted_nte = quan_base.magnitude
    # orb.log.debug('  compute_margin: nte is {}'.format(converted_nte))
    # orb.log.debug('                  mev is {}'.format(mev))
    if mev == 0:   # NOTE: 0 == 0.0 evals to True
        # not defined (division by zero)
        # TODO:  implement a NaN or "Undefined" ...
        return 'undefined'
    msg = '- {} NTE specified for allocation to "{}" -- computing margin ...'
    alloc_ref = ''
    if isinstance(allocation_node, orb.classes['Acu']):
        alloc_ref = (allocation_node.reference_designator or
                     allocation_node.name or
                     allocation_node.component.name)
    elif isinstance(allocation_node, orb.classes['ProjectSystemUsage']):
        alloc_ref = (allocation_node.system_role or
                     allocation_node.name or
                     allocation_node.system.name)
    parm_name = getattr(pd, 'name', 'unspecified')
    orb.log.debug(msg.format(parm_name, alloc_ref))
    margin = round_to(((converted_nte - mev) / converted_nte))
    orb.log.debug('  ... margin is {}%'.format(margin * 100.0))
    return margin

def compute_requirement_margin(orb, oid, default=0):
    """
    Compute the "Margin" for the specified performance requirement. So far,
    "Margin" is only defined for performance requirements that specify a
    maximum or "Not To Exceed" value, and is computed as (NTE-CBE)/CBE, where
    CBE is the Current Best Estimate of the corresponding parameter of the
    system or component to which the requirement is currently allocated.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the performance requirement for which margin is
            to be computed

    Keyword Args:
        context (str): the `id` of the context that defines the margin (for
            now, the only supported context is 'NTE', so context is ignored)
        default (any): a value to be returned if the parameter is not found

    Return:
        allocated_to_oid, parameter_id, margin (tuple)
    """
    req = orb.get(oid)
    # float cast is unnec. because python 3 division will do the right thing
    if not isinstance(req, orb.classes['Requirement']):
        # TODO: notify user 
        msg = 'Requirement with oid {} does not exist.'.format(oid)
        return (None, None, None, None, msg)
    if getattr(req, 'req_type', None) != 'performance':
        # TODO: notify user
        msg = 'Requirement with oid {} is not a performance reqt.'.format(oid)
        return (None, None, None, None, msg)
    # orb.log.debug('* Computing margin for reqt "{}"'.format(req.name))
    rel = getattr(req, 'computable_form', None)
    prs = getattr(rel, 'correlates_parameters', None)
    if not prs:
        msg = 'Performance parameter could not be determined.'
        return (None, None, None, None, msg)
    pd = getattr(prs[0], 'correlates_parameter', None)
    parameter_id = getattr(pd, 'id', None)
    if not parameter_id:
        msg = 'Parameter identity is unknown.'
        return (None, None, None, None, msg)
    nte = req.req_maximum_value
    if not nte:
        msg = 'Requirement is not a "Not To Exceed" (max) type.'
        return (None, parameter_id, None, None, msg)
    nte_units = req.req_units
    acu = req.allocated_to_function
    psu = req.allocated_to_system
    object_oid = None
    if acu:
        allocated_to_oid = acu.oid
        object_oid = getattr(acu.component, 'oid', None)
    elif psu:
        allocated_to_oid = psu.oid
        object_oid = getattr(psu.system, 'oid', None)
    else:
        msg = 'Requirement is not allocated properly (no Acu or PSU).'
        return (None, parameter_id, nte, nte_units, msg)
    if not object_oid or object_oid == 'pgefobjects:TBD':
        msg = 'Margin cannot be computed for unknown or TBD object.'
        return (allocated_to_oid, parameter_id, nte, nte_units, msg)
    mev = _compute_pval(orb, object_oid, parameter_id, 'MEV')
    # convert NTE value to base units, if necessary
    quan = nte * ureg.parse_expression(nte_units)
    quan_base = quan.to_base_units()
    converted_nte = quan_base.magnitude
    # orb.log.debug('  compute_margin: nte is {}'.format(converted_nte))
    # orb.log.debug('                  mev is {}'.format(mev))
    if mev == 0:   # NOTE: 0 == 0.0 evals to True
        # not defined (division by zero)
        # TODO:  implement a NaN or "Undefined" ...
        msg = 'MEV value for {} is 0; cannot compute margin.'.format(
                                                        parameter_id)
        return (allocated_to_oid, parameter_id, nte, nte_units, msg)
    msg = '- {} NTE specified for allocation to "{}" -- computing margin ...'
    alloc_ref = ''
    if acu:
        alloc_ref = acu.reference_designator or acu.name or acu.id
    elif psu:
        alloc_ref = psu.system_role or psu.name or psu.id
    parm_name = getattr(pd, 'name', 'unspecified')
    orb.log.debug(msg.format(parm_name, alloc_ref))
    margin = round_to(((converted_nte - mev) / converted_nte))
    orb.log.debug('  ... margin is {}%'.format(margin * 100.0))
    return (allocated_to_oid, parameter_id, nte, nte_units, margin)

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
# CODE BELOW THIS LINE IS DEPRECATED ...
################################################

# NOTE: this may not be needed
# flow_parmz:  runtime cache that maps parameters to port types
# format:  {parameter.id : port_type}
# flow_parmz = {}

# def refresh_flow_parmz(orb):
    # """
    # Refresh the `flow_parmz` cache.  The purpose of the 'flow_parmz' cache is
    # to avoid db lookups in indentifying flow/port-related parameters, which
    # need to be synchronized with the assignment of Ports to HardwareProducts.

    # This function is called at orb startup and whenever a new
    # ParameterDefinition is saved.  The 'flow_parmz' dictionary has the form

        # {parameter.id : port_type}

    # where the port_type.oid comes from the 'port_type' attribute of the
    # ParameterDefinition.

    # Args:
        # orb (Uberorb):  singleton imported from p.node.uberorb
    # """
    # orb.log.debug('[orb] refresh_flow_parmz()')
    # pds = orb.get_by_type('ParameterDefinition')
    # for pd in pds:
        # port_type = getattr(pd, 'port_type', None)
        # if port_type:
            # flow_parmz[pd.id] = port_type

# OBSOLETE:  original version of compute_assembly_parameter(), using db
# lookups for components (rather than the "componentz" cache)

# def compute_assembly_parameter(orb, product, base_parameters):
    # """
    # Return the total value of an assembly parameter for a product based on the
    # summed values of the base parameter over all of the product's known
    # components.  If no components are defined for the product, simply return
    # the value of the base parameter as specified for the product, or the
    # default.

    # CAUTION: this may return a wildly inaccurate value for an incompletely
    # specified assembly.

    # Args:
        # orb (Uberorb): the orb (see p.node.uberorb)
        # product (Product): the Product whose total parameter is being estimated
        # base_parameters (str): the identifier of the base parameter
    # """
    # # VERY verbose, even for debugging!
    # # orb.log.debug('[parametrics] compute_assembly_parameter()')
    # if product:
        # base_parameter_id = base_parameters 
        # components = [acu.component for acu in product.components
                      # if acu.component
                      # and acu.component.oid != 'pgefobjects:TBD']
        # if components:
            # summation = fsum([compute_assembly_parameter(orb, c, base_parameter_id)
                              # for c in components])
            # if summation:
                # return summation
            # else:   # if component values sum to zero, use base value
                # return _compute_pval(orb, product, base_parameter_id)
        # else:
            # # if the product has no known component, return its specified parameter
            # # value (note that the default here is 0.0)
            # return _compute_pval(orb, product, base_parameter_id)
    # else:
        # return 0.0

# def get_product_parameter(orb, oid, parameter_id, base_parameters,
                          # default=0.0):
    # """
    # Find the product of the base parameters for the specified object.

    # Args:
        # orb (Uberorb): the orb (see p.node.uberorb)
        # oid (str): the oid of the Modelable containing the parameters
        # parameter_id (str): the `id` of the parameter
        # base_parameters (str): a comma-delimited string containing the ids of
            # the parameters to be multiplied

    # Keyword Args:
        # default (any): a value to be returned of the parameter is not found
    # """
    # import operator
    # from functools    import reduce
    # pids = [p.strip() for p in base_parameters.split(',')]
    # vals = [_compute_pval(orb, oid, pid) for pid in pids]
    # return round_to(reduce(operator.mul, vals, 1.0))

