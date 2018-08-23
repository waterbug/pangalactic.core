"""
Functions to support Parameters and Relations
"""
import operator
from collections  import namedtuple
from decimal      import Decimal
from functools    import reduce
from importlib    import import_module
from math         import floor, fsum, log10

# pangalactic
from pangalactic.core                 import config, prefs
from pangalactic.core.meta            import SELECTABLE_VALUES
from pangalactic.core.units           import in_si, ureg
from pangalactic.core.utils.meta      import get_parameter_definition_oid
from pangalactic.core.utils.datetimes import dtstamp

# numpy
import numpy as np


DATATYPES = SELECTABLE_VALUES['range_datatype']
NULL = {True: np.nan, False: 0.0}
TWOPLACES = Decimal('0.01')

# CACHES ##################################################################

# componentz:  runtime component cache
# format:  {product.oid : list of Comp('oid', 'quantity') namedtuples}
componentz = {}
Comp = namedtuple('Comp', 'oid quantity')

# parameterz:  persistent parameter cache
# format:  {product.oid : {'parameter_id': {parameter properties}
#                              ...}}
# ... where parameter properties are:
# name, description, value, units, dimensions, range_datatype, computed,
# generating_function, base_parameters, state_id, variable_id, mod_datetime
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
    before calling orb.recompute_parms() whenever a new Acu is created,
    deleted, or modified.  The 'componentz' dictionary has the form

        {product.oid : list of Comp('oid', 'quantity') namedtuples}

    where the list of `Comp` namedtuples is created from `product.components`
    (Acus of the product), using Acu.component.oid and Acu.quantity.

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
        product (Product):  the Product instance
    """
    if product:
        global componentz
        orb.log.info('[orb] refresh_componentz({})'.format(product.id))
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
    global componentz
    count = 0
    if componentz.get(product_oid):
        count += len(componentz[product_oid])
        if count:
            for c in componentz[product_oid]:
                count += node_count(c.oid)
    return count

def create_parmz_by_dimz(orb):
    """
    Create the `parmz_by_dimz` cache, where the cache has the form

        {dimension : [ids of ParameterDefinitions having that dimension]}

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
    """
    orb.log.info('[orb] create_parmz_by_dimz')
    global parmz_by_dimz
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
    orb.log.info('[orb] refresh_parmz_by_dimz')
    global parmz_by_dimz
    if pd.dimensions in parmz_by_dimz:
        parmz_by_dimz[pd.dimensions].append(pd.id)
    else:
        parmz_by_dimz[pd.dimensions] = [pd.id]

def add_parameter(orb, oid, pid):
    """
    Add a new parameter to an object, which really means adding a parameter
    data structure to the `p.node.parametrics.parameterz` dictionary under that
    objects's oid.  The parameter data structure format is a dict with the
    following keys:

        name, description, value, units, dimensions, range_datatype, computed,
        generating_function, base_parameters, state_id, variable_id,
        mod_datetime

    ... where items `dimensions`, `range_datatype`, `computed`,
    `generating_function`, `base_parameters`, `state_id`, and `variable_id`
    come from the associated ParameterDefinition.

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
        oid (str):  oid of the object that owns the parameter
        pid (str):  `id` attribute of the parameter
    """
    orb.log.info('[orb] add_parameter({})'.format(pid))
    global parameterz
    if oid not in parameterz:
        parameterz[oid] = {}
    elif pid in parameterz[oid]:
        # if the object already has that parameter, do nothing
        return
    pd = orb.get(get_parameter_definition_oid(pid))
    if pd:
        name = pd.name
        desc = pd.description
        dims = pd.dimensions
        radt = pd.range_datatype
        comp = pd.computed_by_default
        genf = pd.generating_function
        basp = pd.base_parameters
    else:
        # for now, if no ParameterDefinition exists for pid, pass
        # (maybe eventually raise TypeError)
        return
    # NOTE:  setting the parameter's value is a separate operation -- when a
    # parameter is created, its value is initialized to the appropriate "null"
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
        name=name,
        description=desc,
        value=value,   # consistent with datatype defined in `range_datatype`
        units=in_si.get(dims),   # SI units consistent with `dimensions`
        mod_datetime=dtstamp(),
        dimensions=dims,
        range_datatype=radt,
        computed=comp,
        generating_function=genf,
        base_parameters=basp)

def add_default_parameters(orb, obj):
    """
    Assign the configured or preferred default parameters to an object.

    Args:
        orb (Uberorb):  the orb (singleton)
        obj (Identifiable):  the object to receive parameters
    """
    # Configured Parameters are currently defined by the 'dashboard'
    # configuration (in future that may be augmented by Parameters
    # referenced by, e.g., a ProductType and/or a ModelTemplate, both of
    # which are essentially collections of ParameterDefinitions.
    # TODO: should all object dashboards be updated if dashboard config is
    # modified?  Hmm ... definitely should at least be an option --
    # probably need a progress bar since it could be time-consuming ...
    orb.log.info('* assigning default parameters to "{}"'.format(obj.id))
    pids = []
    # NOTE:  this is the collection of parameters defined in the
    # `p.repo.refdata` module, hard-coded as a set of default parameters
    pids = []
    # TODO: let user set default parameters in their prefs
    if isinstance(obj, orb.classes['HardwareProduct']):
        # default for "default_parms" in config:  mass, power, data rate
        # (config is read in p.node.gui.startup, and will be overridden by
        # prefs['default_parms'] if it is set
        pids = (prefs.get('default_parms') or config.get('default_parms')
                or ['m', 'P', 'R_D'])
    # add default parameters first ...
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
    orb.log.debug('* assigning parameters for product type "{}"'.format(pt.id))
    # then check for parameters specific to the product_type, if any
    if pt:
        global parameterz
        # check if the product_type has parameters
        pt_parmz = parameterz.get(pt.oid)
        if pt_parmz:
            # if so, replicate them directly (with values)
            for parm_id in pt_parmz:
                parameterz[obj.oid][parm_id] = pt_parmz[parm_id].copy()

def delete_parameter(orb, oid, pid):
    """
    Delete a parameter from an object.

    Args:
        orb (Uberorb):  singleton imported from p.node.uberorb
        oid (str):  oid of the object that owns the parameter
        pid (str):  `id` attribute of the parameter
    """
    # TODO (URGENT!): need to dispatch louie & pubsub messages!
    global parameterz
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
    global parameterz
    try:
        # for extreme debugging only ...
        # orb.log.debug('  value of {} is {} ({})'.format(pid, val, type(val)))
        return parameterz[oid][pid]['value']
    except:
        return NULL[allow_nan]

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
    global parameterz
    try:
        parm = parameterz[oid][pid]
    except:
        # orb.log.debug('* get_pval_as_str failed for oid "{}"'.format(oid))
        # orb.log.debug('  - obj does not have "{}" parameter.'.format(pid))
        return '-'
    try:
        # convert based on dimensions/units ...
        dims = parm.get('dimensions')
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
        radt = parm.get('range_datatype')
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
        # extremely verbose:  logs an ERROR for every unpopulated parameter
        # msg = '* get_pval_as_str(orb, {}, {})'.format(oid, pid)
        # msg += '  encountered an error.'
        # orb.log.debug(msg)
        # if the value causes error, return '-'
        return '-'

def _compute_pval(orb, oid, pid, allow_nan=False):
    """
    Get the value of a parameter of the specified object, computing it if it is
    'computed'; otherwise, returning its value from parameterz.

    NOTE: this function is intended to be private, used only by the `orb`
    or within `parametrics` module itself.  The "public" `get_pval` function
    should always be used by other modules (which will access pre-computed
    parameter values).

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the Identifiable that has the parameter
        pid (str): the parameter 'id' value

    Keyword Args:
        allow_nan (bool): allow NaN as a value for cases in which the
            object or the parameter doesn't exist or the parameter value is
            not set
    """
    # TODO:  astropy-style value with units
    # orb.log.debug('* _compute_pval() ...')
    # orb.log.debug('  {}.{}'.format(oid, pid))
    global parameterz
    if oid in parameterz:
        parm = parameterz[oid].get(pid) or {}
        if parm.get('computed'):
            # orb.log.debug('  "{}" is computed ...'.format(pid))
            # use generating_function -- in the future, there may be a Relation
            # expression, found using the ParameterRelation relationship
            gen_fn_name = parm.get('generating_function')
            # orb.log.debug('  generating function is {}'.format(gen_fn_name))
            base_parms = parm.get('base_parameters')
            # orb.log.debug('  base_parameters: "{}"'.format(base_parms))
            if gen_fn_name and base_parms:
                # TODO:  this is WAY too cumbersome ...
                mod_fn_name = gen_fn_name.split('.')
                mod_name = '.'.join(mod_fn_name[:-1])
                fn_name = mod_fn_name[-1]
                module = import_module(mod_name)
                if hasattr(module, fn_name):
                    gen_fn = getattr(module, fn_name)
                    # the generating function's first arg is now 'orb'
                    value = gen_fn(orb, oid, pid, base_parms)
                    # orb.log.debug('  value is {}'.format(value))
                    return value
                else:
                    return NULL[allow_nan]
            return NULL[allow_nan]
        # msg = '  "{}" is not computed; calling get_pval() ...'.format(pid)
        # orb.log.debug(msg)
        return get_pval(orb, oid, pid, allow_nan=allow_nan)
    else:
        # orb.log.debug('  this object has no parameters defined yet.')
        return NULL[allow_nan]

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
    # orb.log.debug('* set_pval({}, {}, {})'.format(oid, pid, str(value)))
    global parameterz
    if not oid:
        # orb.log.debug('  no oid provided; ignoring.')
        return
    parm = parameterz.get(oid, {}).get(pid, {})
    if not parm:
        # NOTE:  this is the case if
        # (1) that oid is not in parameterz or
        # (2) the object with that oid doesn't have that parameter
        # orb.log.debug('  parameter not found; ignoring.')
        return
    if parm['computed']:
        # orb.log.debug('  parameter is computed -- not setting.')
        return
    try:
        # cast value to range_datatype before setting
        dt_name = parameterz[oid][pid]['range_datatype']
        dtype = DATATYPES[dt_name]
        value = dtype(value)
        if units is not None:
            # TODO:  validate units (ensure they are consistent with dims)
            try:
                quan = value * ureg.parse_expression(units)
                quan_base = quan.to_base_units()
                converted_value = quan_base.magnitude
                parameterz[oid][pid]['units'] = units
            except:
                # if problem with units, do nothing
                orb.log.info('  could not parse units "{}" ...'.format(units))
                orb.log.info('  bailing out.')
                return
        else:
            # None for units -> value is already in base units
            converted_value = value
        parameterz[oid][pid]['value'] = converted_value
        if local or mod_datetime is None:
            mod_datetime = dtstamp()
        parameterz[oid][pid]['mod_datetime'] = mod_datetime
        # dts = str(mod_datetime)
        # orb.log.debug('  setting value: {}'.format(value))
        # orb.log.debug('  setting mod_datetime: "{}"'.format(dts))
        orb.recompute_parms()
    except:
        msg = '  value {} of datatype {} '.format(value, type(value))
        msg += 'not compatible with parameter datatype `{}`'.format(dt_name)
        orb.log.info(msg)

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
    global parameterz
    radt = parameterz[oid][pid].get('range_datatype')
    try:
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
        if parameterz[oid][pid].get('dimensions') == 'percent':
            val = 0.01 * float(val)
        return val
    except:
        # if unable to cast a value, do nothing (and log it)
        # TODO:  more form validation!
        orb.log.info('  could not convert string "{}" ...'.format(str_val))
        orb.log.info('  bailing out.')

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
    global parameterz
    radt = parameterz[oid][pid].get('range_datatype')
    try:
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
        if parameterz[oid][pid].get('dimensions') == 'percent':
            val = 0.01 * float(val)
        set_pval(orb, oid, pid, val, units=units, mod_datetime=mod_datetime,
                 local=local)
    except:
        # if unable to cast a value, do nothing (and log it)
        # TODO:  more form validation!
        orb.log.info('  could not convert string "{}" ...'.format(str_val))
        orb.log.info('  bailing out.')

def get_assembly_parameter(orb, product_oid, parameter_id, base_parameters):
    """
    Return the total value of an assembly parameter for a product based on the
    summed values of the base parameter over all of the product's known
    components.  If no components are defined for the product, simply return
    the value of the base parameter as specified for the product, or the
    default.

    CAUTION: this may return a wildly inaccurate value for an incompletely
    specified assembly.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        product_oid (str): the oid of the Product whose total parameter is
            being estimated
        parameter_id (str): the `id` of the parameter
        base_parameters (str): the `id` of the base parameter
    """
    # VERY verbose, even for debugging!
    # orb.log.debug('[parametrics] get_assembly_parameter()')
    global parameterz
    if product_oid in parameterz and parameter_id in parameterz[product_oid]:
        base_pid = base_parameters 
        radt = parameterz[product_oid][parameter_id].get('range_datatype')
        dtype = DATATYPES[radt]
        # cz, if it exists, will be a list of namedtuples ...
        cz = componentz.get(product_oid)
        if cz:
            # dtype cast is used here in case some component didn't have this
            # parameter or didn't exist and we got a 0.0 value for it ...
            summation = fsum([dtype(get_assembly_parameter(
                              orb, c.oid, parameter_id, base_pid) * c.quantity)
                              for c in cz])
            return round_to(summation)
        else:
            # if the product has no known components, return its specified base
            # parameter value (note that the default here is 0.0)
            return _compute_pval(orb, product_oid, base_pid)
    else:
        return 0.0

def get_mev(orb, oid, parameter_id, base_parameters, default=0.0):
    """
    Find the Maximum Expected Value based on the percent contingency specified
    for the specified base parameter.  Assumes that base_parameters contains
    the ids for the base parameter and contingency factor, in that order.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the Modelable containing the parameters
        parameter_id (str): the `id` of the parameter
        base_parameters (str): a comma-delimited string containing the ids of
            the base parameter and contingency factor.

    Keyword Args:
        default (any): a value to be returned if the parameter is not found
    """
    base, contingency = [p.strip() for p in base_parameters.split(',')]
    factor = _compute_pval(orb, oid, contingency) + 1.0
    base_val = _compute_pval(orb, oid, base)
    # extremely verbose logging -- uncomment only for intense debugging
    # orb.log.debug('* get_mev: base parameter value is {}'.format(base_val))
    # orb.log.debug('           base parameter type is {}'.format(
                                                            # type(base_val)))
    if isinstance(base_val, int):
        return round_to(int(factor * base_val))
    elif isinstance(base_val, float):
        return round_to(factor * base_val)
    else:
        return default

def get_margin(orb, oid, parameter_id, base_parameters, default=0.0):
    """
    Find the "Margin", (NTE-CBE)/CBE, for the specified base parameter.
    Assumes that `base_parameters` contains the ids for the NTE (Not To Exceed)
    and CBE (Current Best Estimate), in that order.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the Modelable containing the parameters
        parameter_id (str): the `id` of the parameter
        base_parameters (str): a comma-delimited string containing the ids of
            the NTE and CBE parameters.

    Keyword Args:
        default (any): a value to be returned if the parameter is not found
    """
    nte, cbe = [p.strip() for p in base_parameters.split(',')]
    # in case these are integers, cast to float
    nte_val = float(get_pval(orb, oid, nte))
    cbe_val = float(_compute_pval(orb, oid, cbe))
    # extremely verbose logging -- uncomment only for intense debugging
    # orb.log.debug('* get_margin: nte is {}'.format(nte_val))
    # orb.log.debug('              cbe is {}'.format(cbe_val))
    if nte_val == 0.0:
        return default  # not defined (division by zero)
    else:
        margin = round_to((nte_val - cbe_val) / nte_val)
        # uncomment only for intense debugging
        # orb.log.debug('  ... margin is {}'.format(margin))
        return margin

def get_product_parameter(orb, oid, parameter_id, base_parameters,
                          default=0.0):
    """
    Find the product of the base parameters for the specified object.

    Args:
        orb (Uberorb): the orb (see p.node.uberorb)
        oid (str): the oid of the Modelable containing the parameters
        parameter_id (str): the `id` of the parameter
        base_parameters (str): a comma-delimited string containing the ids of
            the parameters to be multiplied

    Keyword Args:
        default (any): a value to be returned of the parameter is not found
    """
    pids = [p.strip() for p in base_parameters.split(',')]
    vals = [_compute_pval(orb, oid, pid) for pid in pids]
    return round_to(reduce(operator.mul, vals, 1.0))


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
    # global flow_parmz
    # orb.log.info('[orb] refresh_flow_parmz()')
    # pds = orb.get_by_type('ParameterDefinition')
    # for pd in pds:
        # port_type = getattr(pd, 'port_type', None)
        # if port_type:
            # flow_parmz[pd.id] = port_type

# OBSOLETE CODE:  original version of get_assembly_parameter(), using db
# lookups for components (rather than the "componentz" cache)

# def get_assembly_parameter(orb, product, base_parameters):
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
    # # orb.log.debug('[parametrics] get_assembly_parameter()')
    # if product:
        # base_parameter_id = base_parameters 
        # components = [acu.component for acu in product.components
                      # if acu.component
                      # and acu.component.oid != 'pgefobjects:TBD']
        # if components:
            # summation = fsum([get_assembly_parameter(orb, c, base_parameter_id)
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

