"""
Functions to support Parameters, Relations, and Data Elements
"""
import json, os
from collections import namedtuple
from copy        import deepcopy
from decimal     import Decimal
from math        import floor, fsum, log10

# pangalactic
from pangalactic.core                 import config, state, prefs
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

Q_ = ureg.Quantity

class logger:
    def info(self, s):
        dispatcher.send(signal='log info msg', msg=s)
    def debug(self, s):
        dispatcher.send(signal='log debug msg', msg=s)

log = logger()

DATATYPES = SELECTABLE_VALUES['range_datatype']
# NULL values by dtype:
NULL = dict(float=0.0, int=0, str='', bool=False, text='', array=[])
TWOPLACES = Decimal('0.01')

def make_parm_html(pid, tag='p', style='', flag=False):
    """
    HTML-ize a parameter id for use in labels.

    Args:
        pid (str): the parameter id

    Keyword Args:
        tag (str): html tag to use -- default is "p"
        style (str): css spec to use -- default is ""
        flag (bool):  add an asterisk if computed
    """
    begin_tag = tag
    if tag == 'p' and style:
        begin_tag = f'p style="{style}"'
    if not isinstance(pid, str):
        return '<b>oops</b>'
    if '[' in pid:
        base, tail = pid.split('[')
        ctxt = '[' + tail
    else:
        base = pid
        ctxt = ''
    parts = base.split('_')
    if len(parts) > 1:
        pname = f'{parts[0]}<sub>{parts[1]}</sub>{ctxt}'
        # return f'<{begin_tag}>{parts[0]}<sub>{parts[1]}</sub>{ctxt}</{tag}>'
    else:
        pname = f'{base}{ctxt}'
        # return f'<{begin_tag}>{base}{ctxt}</{tag}>'
    if flag and parm_defz[pid].get('computed'):
        pname += ' *'
    return f'<{begin_tag}>{pname}</{tag}>'

def make_de_html(deid, tag='p', style=''):
    """
    HTML-ize a data element id for use in labels -- if "label" field is
    populated in the data element definition, use it.

    Args:
        deid (str): the data element id

    Keyword Args:
        tag (str): html tag to use -- default is "p"
        style (str): css spec to use -- default is ""
    """
    begin_tag = tag
    de_def = de_defz.get(deid)
    if de_def and de_def.get('label'):
        # if label is found, use it
        label = de_def['label']
        return f'<{begin_tag}>{label}</{tag}>'
    else:
        # if label is not found, use deid
        if tag == 'p' and style:
            begin_tag = f'p style="{style}"'
        if not isinstance(deid, str):
            return '<b>oops</b>'
        parts = deid.split('_')
        name_parts = [p.capitalize() for p in parts]
        studly_name = ' '.join(name_parts)
        if len(parts) > 1:
            return f'<{begin_tag}>{studly_name}</{tag}>'
        elif deid == 'TRL':
            # yes, ugly :(
            return f'<{begin_tag}>TRL</{tag}>'
        else:
            return f'<{begin_tag}>{deid.capitalize()}</{tag}>'

# componentz cache **********************************************************

# componentz:  runtime assembly component cache
# purpose:  enable fast computation of assembly parameters *and* determine
#           whether an existing Acu has had its component changed
# format:  {product.oid : list of Comp namedtuples}
#          ... where each Comp is:
#            oid (str): Acu.component.oid
#            usage_oid (str): Acu.oid
#            quantity (int): Acu.quantity
#            reference_designator (str): Acu.reference_designator
componentz = {}
Comp = namedtuple('Comp', 'oid usage_oid quantity reference_designator')

def refresh_componentz(product):
    """
    Refresh the `componentz` cache for a Product instance. This must be called
    before calling orb.recompute_parmz() whenever a new Acu that references
    that Product instance as its assembly is created, deleted, or modified.
    The 'componentz' dictionary has the form

        {product.oid :
          list of Comp('oid', 'usage_oid', 'quantity', 'reference_designator')}

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
                                        acu.oid,
                                        acu.quantity or 1,
                                        acu.reference_designator))
                                   for acu in product.components
                                   if acu.component]

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

def serialize_compz(compz_data):
    """
    Serialize a `componentz` data set to a json-dumpable format.
    """
    log.debug('* serialize_compz() ...')
    ser_compz = {}
    for oid, compz in compz_data.items():
        comps = []
        for comp in compz:
            compdict = comp._asdict()
            comps.append(compdict)
        ser_compz[oid] = comps
    return ser_compz

def deserialize_compz(ser_compz):
    """
    Deserialize a `componentz` data set from a json-dumped format.

    NOTE: the deserialize_compz() function is only used to deserialize
    componentz data received from the server.
    """
    log.debug('* deserialize_compz() ...')
    deser_compz = {}
    for oid, comps in ser_compz.items():
        compz = []
        for comp in comps:
            comptuple = Comp(**comp)
            compz.append(comptuple)
        deser_compz[oid] = compz
    n = len(deser_compz)
    log.debug(f'  - componentz deserialized ({n} product assemblies).')
    return deser_compz

def save_compz(dir_path):
    """
    Save the `componentz` cache to a json file.
    """
    fpath = os.path.join(dir_path, 'components.json')
    ser_compz = serialize_compz(componentz)
    with open(fpath, 'w') as f:
        f.write(json.dumps(ser_compz, separators=(',', ':'),
                           indent=4, sort_keys=True))

def load_compz(dir_path):
    """
    Load the `componentz` cache from a json file.
    """
    fpath = os.path.join(dir_path, 'components.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            try:
                stored_componentz = json.loads(f.read())
            except:
                return 'fail'
        componentz.update(deserialize_compz(stored_componentz))
        return 'success'
    else:
        log.debug('  - "components.json" was not found.')
        return 'not found'

# systemz cache **********************************************************

# systemz:  runtime project systems cache
# purpose:  provide a cache to substitute for the "systems" inverse attr
#           which the "Marvin" thin client cannot use
# format:  {project.oid : list of System namedtuples}
#          ... where each System is:
#            oid (str): ProjectSystemUsage.system.oid
#            usage_oid (str): ProjectSystemUsage.oid
#            system_role (str): ProjectSystemUsage.system_role
systemz = {}
System = namedtuple('System', 'oid usage_oid system_role')

def refresh_systemz(project):
    """
    Refresh the `systemz` cache for a Project instance. This must be called
    whenever a new ProjectSystemUsage that references that Project instance as
    its project is created, deleted, or modified.  The 'systemz' dictionary has
    the form

        {project.oid :
          list of System('oid', 'usage_oid', 'system_role')}

    where the list of `System` namedtuples is created from `project.systems`
    (ProjectSystemUsages of the project), using the system oid, psu oid,
    psu system_role attributes.

    Args:
        project (Project):  the Project instance
    """
    if project:
        # log.debug('* refresh_systemz({})'.format(project.id))
        systemz[project.oid] = [System._make((
                                        getattr(psu.system, 'oid', ''),
                                        psu.oid,
                                        psu.system_role))
                                   for psu in project.systems
                                   if psu.system]

def project_node_count(project_oid):
    """
    Get the number of nodes in the assembly tree of the project with the
    specified oid.

    Args:
        project_oid (str):  oid of a Project instance
    """
    count = 0
    if systemz.get(project_oid):
        count += len(systemz[project_oid])
        if count:
            for system in systemz[project_oid]:
                count += node_count(system.oid)
    return count

def serialize_systemz(systemz_data):
    """
    Serialize a `systemz` data set to a json-dumpable format.
    """
    log.debug('* serialize_systemz() ...')
    ser_systemz = {}
    for oid, systems in systemz_data.items():
        sysdicts = []
        for system in systems:
            sysdict = system._asdict()
            sysdicts.append(sysdict)
        ser_systemz[oid] = sysdicts
    return ser_systemz

def deserialize_systemz(ser_systemz):
    """
    Deserialize a `systemz` data set from a json-dumped format.

    NOTE: the deserialize_systemz() function is only used to deserialize
    systems data received from the server.
    """
    log.debug('* deserialize_systemz() ...')
    deser_systemz = {}
    for oid, sysdicts in ser_systemz.items():
        systemz = []
        for sysdict in sysdicts:
            system = System(**sysdict)
            systemz.append(system)
        deser_systemz[oid] = systemz
    n = len(deser_systemz)
    log.debug(f'  - systemz deserialized ({n} project assemblies).')
    return deser_systemz

def save_systemz(dir_path):
    """
    Save the `systemz` cache to a json file.
    """
    fpath = os.path.join(dir_path, 'systems.json')
    ser_systemz = serialize_systemz(systemz)
    with open(fpath, 'w') as f:
        f.write(json.dumps(ser_systemz, separators=(',', ':'),
                           indent=4, sort_keys=True))

def load_systemz(dir_path):
    """
    Load the `systemz` cache from a json file.
    """
    fpath = os.path.join(dir_path, 'systems.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            try:
                stored_systemz = json.loads(f.read())
            except:
                return 'fail'
        # use clear() first in case any stale entries
        systemz.clear()
        systemz.update(deserialize_systemz(stored_systemz))
        return 'success'
    else:
        log.debug('  - "systems.json" was not found.')
        return 'not found'

# ***************************************************************************

# NOTE #####################################################################
# For Data Element handling, see DATA ELEMENT SECTION
# For Mode handling, see MODE SECTION
# NOTE #####################################################################

################################################
# PARAMETER SECTION
################################################

# PARAMETER CACHES ##########################################################

# parm_defz:  runtime cache of parameter definitions (both base and context
#             parameter definitions are included)
# purpose:  enable fast lookup of parameter metadata & compact representation
#           of the content of ParameterDefinition objects
# format:  {'parameter id': {parameter properties}
#                            ...}}
# ... where "parameter properties" are the attributes of ParameterDefinition:
# -----------------------------------------------------------------------------
# name, label, variable, context, description, dimensions, range_datatype,
# computed, mod_datetime
# -----------------------------------------------------------------------------
parm_defz = {}

# parameterz:  persistent** cache of assigned parameter values
#              ** persisted in the file 'parameters.json' in the
#              application home directory -- see the functions
#              `save_parmz` and `load_parmz`
#
# format:  {object.oid : {'parameter id': value
#                         ...}}
#
# NOTE:  "value" is ALWAYS stored in base mks units
parameterz = {}

def serialize_parms(oid):
    """
    Output the parameters for an object. Note that the values are *always*
    expressed in *base* units and the 'units' field contains the preferred
    units to be used when displaying the value in the user interface (i.e., the
    value must be converted to those units for display).

    Args:
        oid (str):  oid of the object to which the parameters apply.
    """
    if oid in parameterz and parameterz[oid] is not None:
        return {pid: parameterz[oid][pid]
                for pid in parameterz[oid]}
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
        # log.debug('* deserializing parms for {} ({})...'.format(oid, cname))
        # log.debug('  parms: {}'.format(ser_parms))
    if not ser_parms:
        # log.debug('  object with oid "{}" has no parameters'.format(oid))
        return
    # ser_parms is non-empty
    pids = list(ser_parms)
    if ser_parms[pids[0]] and isinstance(ser_parms[pids[0]], dict):
        # if the value is a dict, format is old
        old_ser_parms = deepcopy(ser_parms)
        ser_parms = {}
        for pid, pdict in old_ser_parms.items():
            ser_parms[pid] = pdict['value']
        log.debug('  - parameters converted from old format.')
    pids_to_delete = []
    deids_to_delete = []
    # this covers (1) oid not in parameterz and (2) oid in parameterz but value
    # is None
    if not parameterz.get(oid):
        parameterz[oid] = {}
    for pid, value in ser_parms.items():
        if pid in parm_defz:
            # yes, this is a valid parameter (has a ParameterDefinition)
            parameterz[oid][pid] = value
        elif pid in de_defz:
            # this is a data element (has a DataElementDefinition)
            # log_msg = 'data element found in parameters: "{}"'.format(pid)
            # log.debug('  - {}'.format(log_msg))
            if oid not in data_elementz:
                data_elementz[oid] = {}
            data_elementz[oid][pid] = value
            if pid in parameterz[oid]:
                pids_to_delete.append(pid)
        else:
            # log_msg = 'unknown id found in parameters: "{}"'.format(pid)
            # log.debug('  - {}'.format(log_msg))
            # pid has no definition, so it should not be in parameterz or
            # data_elementz
            if pid in parameterz[oid]:
                pids_to_delete.append(pid)
            if pid in (data_elementz.get(oid) or {}):
                deids_to_delete.append(pid)
    # delete any undefined parameters or data elements
    # de_oids = list(data_elementz)
    # parm_oids = list(parameterz)
    for pid in pids_to_delete:
        if pid in parameterz[oid]:
            del parameterz[oid][pid]
    for deid in deids_to_delete:
        if deid in data_elementz[oid]:
            del data_elementz[oid][deid]

def load_parmz(dir_path):
    """
    Load the `parameterz` cache from json file.
    """
    log.debug('* load_parmz() ...')
    fpath = os.path.join(dir_path, 'parameters.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            try:
                stored_parameterz = json.loads(f.read())
            except:
                log.debug('  - json decoding of "parameters.json" failed.')
                return 'fail'
            # first check for old format and convert if necessary
            old_format = False
            oids = list(stored_parameterz)
            if oids:
                # find first non-empty data element dict
                n = 0
                while 1:
                    test_oid = oids[n]
                    test_dict = stored_parameterz[test_oid]
                    if test_dict:
                        # test_dict is non-empty
                        pids = list(test_dict)
                        if pids:
                            for parm_val in test_dict.values():
                                if parm_val and isinstance(parm_val, dict):
                                    # if the value is a dict, format is old
                                    old_format = True
                    if old_format:
                        break
                    else:
                        n += 1
                        if n == len(oids):
                            break
            if old_format:
                # convert to new format
                ser_parms_old = deepcopy(stored_parameterz)
                stored_parameterz = {}
                for oid, old_parms_dict in ser_parms_old.items():
                    new_parms_dict = {}
                    for pid in old_parms_dict:
                        if old_parms_dict:
                            new_parms_dict[pid] = old_parms_dict[pid]['value']
                        else:
                            dtype = (parm_defz.get(
                                     pid, 'range_datatype', 'float')
                                     or 'float')
                            new_parms_dict[pid] = NULL.get(dtype, '') or ''
                    stored_parameterz[oid] = new_parms_dict
                log.debug('  - parameterz cache converted from old format.')
        for oid, parms in stored_parameterz.items():
            deserialize_parms(oid, parms)
        log.debug('  - parameterz cache loaded.')
        return 'success'
    else:
        log.debug('  - "parameters.json" was not found.')
        return 'not found'

def save_parmz(dir_path):
    """
    Save `parameterz` cache to a json file.
    """
    stored_parameterz = {}
    for oid, parms in parameterz.items():
        # NOTE: serialize_parms() uses deepcopy()
        stored_parameterz[oid] = serialize_parms(oid)
    fpath = os.path.join(dir_path, 'parameters.json')
    try:
        with open(fpath, 'w') as f:
            f.write(json.dumps(stored_parameterz, separators=(',', ':'),
                               indent=4, sort_keys=True))
        log.debug('  ... parameters.json file written.')
    except:
        log.debug('  ... writing parameters.json file failed!')

# parmz_by_dimz:  runtime cache that maps dimensions to parameter definitions
# format:  {dimension : [ids of ParameterDefinitions having that dimension]}
# NOTE:  see orb function 'create_parmz_by_dimz'
parmz_by_dimz = {}

def load_parmz_by_dimz(dir_path):
    """
    Load the `parmz_by_dimz` dict from json file in cache format.
    """
    fpath = os.path.join(dir_path, 'parms_by_dims.json')
    if os.path.exists(fpath):
        try:
            with open(fpath) as f:
                stored_parmz_by_dimz = json.loads(f.read())
        except:
            return 'fail'
        parmz_by_dimz.update(stored_parmz_by_dimz)
        return 'success'
    else:
        return 'not found'

def save_parmz_by_dimz(dir_path):
    """
    Save `parmz_by_dimz` dict to a json file in cache format.
    """
    fpath = os.path.join(dir_path, 'parms_by_dims.json')
    with open(fpath, 'w') as f:
        f.write(json.dumps(parmz_by_dimz, separators=(',', ':'),
                           indent=4, sort_keys=True))

# rqt_allocz:  runtime requirement allocations cache
# purpose:  optimize performance of margin calculations
# format:  {rqt_oid : [usage_oid, obj_oid, alloc_ref, pid, constraint]}
# ... where:
#   rqt_oid (str):  the oid of the requirement
#   usage_oid (str): the oid of the Acu, ProjectSystemUsage, or Project to
#       which the requirement is allocated
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
rqt_allocz = {}
Constraint = namedtuple('Constraint',
             'units target max min tol upper lower constraint_type tol_type')

# allocz:   maps usage oids to a list of the oids of reqts. allocated to them
# purpose:  used in "marv" package reqts. manager
# format:  {usage_oid : [reqt_oids]}
allocz = {}

def serialize_rqt_allocz(rqt_allocz_data):
    """
    Serialize a `rqt_allocz` data set to a json-dumpable format.
    """
    log.debug('* serialize_rqt_allocz() ...')
    ser_rqt_allocz = {}
    for oid, alloc in rqt_allocz_data.items():
        usage_oid, obj_oid, alloc_ref, pid, constraint = alloc
        constraint_dict = constraint._asdict()
        ser_alloc = [usage_oid, obj_oid, alloc_ref, pid, constraint_dict]
        ser_rqt_allocz[oid] = ser_alloc
    return ser_rqt_allocz

def deserialize_rqt_allocz(ser_rqt_allocz):
    """
    Deserialize a `rqt_allocz` data set from a json-dumped format.

    NOTE: the deserialize_rqt_allocz() function is only used to deserialize
    rqt_allocz data received from the server.
    """
    log.debug('* deserialize_rqt_allocz() ...')
    rqt_allocz_data = {}
    for oid, ser_alloc in ser_rqt_allocz.items():
        usage_oid, obj_oid, alloc_ref, pid, ser_constraint = ser_alloc
        constraint = Constraint(**ser_constraint)
        rqt_allocz_data[oid] = [usage_oid, obj_oid, alloc_ref, pid, constraint]
    n = len(rqt_allocz_data)
    log.debug(f'  - rqt_allocz deserialized ({n} req allocations).')
    return rqt_allocz_data

def save_rqt_allocz(dir_path):
    """
    Save the `rqt_allocz` cache to a json file.
    """
    fpath = os.path.join(dir_path, 'rqt_allocs.json')
    ser_rqt_allocz = serialize_rqt_allocz(rqt_allocz)
    with open(fpath, 'w') as f:
        f.write(json.dumps(ser_rqt_allocz, separators=(',', ':'),
                           indent=4, sort_keys=True))

def load_rqt_allocz(dir_path):
    """
    Load the `rqt_allocz` cache from a json file.
    """
    fpath = os.path.join(dir_path, 'rqt_allocs.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            try:
                stored_rqt_allocz = json.loads(f.read())
            except:
                return 'fail'
        rqt_allocz.update(deserialize_rqt_allocz(stored_rqt_allocz))
        return 'success'
    else:
        log.debug('  - "rqt_allocs.json" was not found.')
        return 'not found'

def save_allocz(dir_path):
    """
    Save the `allocz` cache to a json file.
    """
    fpath = os.path.join(dir_path, 'allocs.json')
    with open(fpath, 'w') as f:
        f.write(json.dumps(allocz, separators=(',', ':'),
                           indent=4, sort_keys=True))

def load_allocz(dir_path):
    """
    Load the `allocz` cache from a json file.
    """
    fpath = os.path.join(dir_path, 'allocs.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            try:
                stored_allocz = json.loads(f.read())
            except:
                return 'fail'
        allocz.update(stored_allocz)
        return 'success'
    else:
        log.debug('  - "allocs.json" was not found.')
        return 'not found'

#############################################################################

def round_to(x, n=4):
    """
    Round the number x to n digits.  (Default: 4)

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

def refresh_rqt_allocz(req):
    """
    Refresh the `rqt_allocz` cache for a Requirement instance.  This must be
    called whenever a Requirement instance is created, modified, or deleted or
    an Acu or ProjectSystemUsage is deleted or modified, which could affect the
    'obj_oid' and/or 'alloc_ref' items.

    NOTE:  this function depends only on the database and does not use any
    caches, nor does it update the parameterz cache, so it can be used by any
    margin computation function.

    The 'rqt_allocz' dictionary has the form:

        {rqt_oid : [usage_oid, obj_oid, alloc_ref, pid, constraint]}

    ... where:

      rqt_oid (str):  the oid of the requirement
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
    # rqt_id = getattr(req, 'id', 'no id') or 'no id'
    # log.debug(f'* refresh_rqt_allocz({rqt_id})')
    usage_oid = None
    alloc_ref = None
    obj_oid = None
    # DEPRECATED:  allocated_to_[function|system] is now just allocated_to
    # if req.allocated_to_function:
        # acu = req.allocated_to_function
        # alloc_ref = acu.reference_designator or acu.name or acu.id
        # usage_oid = acu.oid
        # obj_oid = getattr(acu.component, 'oid', None)
    # elif req.allocated_to_system:
        # psu = req.allocated_to_system
        # alloc_ref = psu.system_role or psu.name or psu.id
        # usage_oid = psu.oid
        # obj_oid = getattr(psu.system, 'oid', None)
    if req.allocated_to:
        if hasattr(req.allocated_to, 'component'):
            acu = req.allocated_to
            alloc_ref = acu.reference_designator or acu.name or acu.id
            usage_oid = acu.oid
            obj_oid = getattr(acu.component, 'oid', None)
        elif hasattr(req.allocated_to, 'system'):
            psu = req.allocated_to
            alloc_ref = psu.system_role or psu.name or psu.id
            usage_oid = psu.oid
            obj_oid = getattr(psu.system, 'oid', None)
        else:
            # allocated to a project
            project = req.allocated_to
            alloc_ref = project.id
            usage_oid = project.oid
            obj_oid = getattr(project, 'oid', None)
    else:
        # req is not allocated; if present, remove it
        # log.debug('  req is not allocated')
        if req.oid in rqt_allocz:
            del rqt_allocz[req.oid]
            # log.debug('  + removed from rqt_allocz.')
        return
    if req.rqt_type == 'functional':
        # log.debug('  functional req (no parameter or constraint).')
        if usage_oid:
            rqt_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, None, None]
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
            rqt_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, None, None]
            return
    else:
        # log.debug('  no computable_form found -> functional req.')
        rqt_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, None, None]
        return
    if pid:
        rqt_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, pid,
                                 Constraint._make((
                                     req.rqt_units,
                                     req.rqt_target_value,
                                     req.rqt_maximum_value,
                                     req.rqt_minimum_value,
                                     req.rqt_tolerance,
                                     req.rqt_tolerance_upper,
                                     req.rqt_tolerance_lower,
                                     req.rqt_constraint_type,
                                     req.rqt_tolerance_type
                                     ))]
    else:
        # log.debug('  no parameter found; treat as functional req.')
        rqt_allocz[req.oid] = [usage_oid, obj_oid, alloc_ref, None, None]

def get_parameter_id(variable, context_id):
    """
    Given a variable and a context id, return a parameter id.
    """
    pid = variable
    if context_id:
        pid += '[' + context_id + ']'
    return pid

def get_variable_and_context(parameter_id):
    """
    Given a parameter id, return its variable and context id (substituting
    "Nominal" for "CBE").
    """
    if '[' in parameter_id:
        try:
            var, ctx = parameter_id.split('[')[0], parameter_id.split('[')[1][:-1]
            if ctx == 'CBE':
                return (var, 'Nominal')
            return (var, ctx)
        except:
            return ('', '')
    return (parameter_id, '')

def get_parameter_name(variable_name, context_abbr):
    """
    Given a variable name and a context abbreviation, return a parameter name.
    """
    name = variable_name
    if context_abbr:
        name += ' [' + context_abbr + ']'
    return name

def get_parameter_description(variable_desc, context_desc):
    """
    Given a variable description and a context description, return a parameter
    description.
    """
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
    Add a new parameter to an object, which means adding a parameter's value to
    the `p.node.parametrics.parameterz` dictionary under that objects's oid, if
    it does not already exist for the specified paramter.

    Args:
        oid (str):  oid of the object that owns the parameter
        pid (str):  the id of the parameter
    """
    # log.debug('* add_parameter()')
    # oid could be a key in parameterz but have a value of None -- if so, it
    # needs to be set as an empty dict ...
    if parameterz.get(oid) is None:
        parameterz[oid] = {}
    # NOTE [SCW 2021-03-17] added when refactoring so that the "base variable"
    # is not added when a context parameter is added: it doesn't matter whether
    # the parameter being added is a context parameter or a "variable"
    # parameter -- the function should be the same for both and should not add
    # the "variable" parameter when a context parameter is added: in many cases
    # the "variable" does not make sense as a "spec" parameter (e.g.,
    # Temperature).
    if pid in parameterz[oid]:
        # if the object already has that parameter, do nothing
        # log.debug(f'   obj with oid "{oid}" already has "{pid}"; not adding.')
        return True
    pdz = parm_defz.get(pid)
    if not pdz:
        # log.debug(f'  "{pid}" not in parm_defz; not adding.')
        return False
    range_datatype = pdz.get('range_datatype', 'float')
    p_defaults = state.get('p_defaults') or {}
    if p_defaults.get(pid):
        # if a default value is configured for this pid, override null
        dtype = DATATYPES[range_datatype]
        value = dtype(p_defaults[pid])
    else:    # use a "NULL" value
        value = NULL.get(range_datatype, 0.0)
    parameterz[oid][pid] = value
    # log.debug(f'  "{pid}" added to obj with oid "{oid}"')
    return True

def add_default_parameters(obj, parms=None):
    """
    Assign any specified, configured, or preferred default parameters that are
    missing from an object.

    Args:
        obj (Identifiable):  the object to receive parameters

    Keyword Args:
        parms (list):  (optional) list of parameter id's to add
    """
    pids = OrderedSet()
    cname = obj.__class__.__name__
    pids |= OrderedSet(DEFAULT_CLASS_PARAMETERS.get(cname, []))
    if cname == 'HardwareProduct':
        # default for "default_parms":  mass, power, data rate
        # (state is read in p.node.gui.startup, and will be overridden by
        # prefs['default_parms'] if it is set
        pids |= OrderedSet(parms or prefs.get('default_parms') or [])
        prod_type = obj.product_type
        prod_type_id = getattr(prod_type, 'id', '')
        if prod_type_id:
            def_pids = OrderedSet(DEFAULT_PRODUCT_TYPE_PARAMETERS.get(
                                                       prod_type_id) or [])
            # txt = '  - found default parameters'
            # log.debug(f'{txt} for product type "{prod_type_id}": {def_pids}')
            pids |= def_pids
    pids_to_add =  pids - set(parameterz.get(obj.oid) or [])
    if pids_to_add:
        # log.debug(f'  - adding default parameters {pids_to_add} ...')
        for pid in pids_to_add:
            add_parameter(obj.oid, pid)

def delete_parameter(oid, pid, local=True):
    """
    Delete a parameter from an object.

    Args:
        oid (str):  oid of the object that owns the parameter
        pid (str):  `id` attribute of the parameter

    Keyword Args:
        local (bool):  if True, originated locally
    """
    if pid in (parameterz.get(oid) or {}):
        del parameterz[oid][pid]
        if local:
            dispatcher.send(signal='parm del', oid=oid, pid=pid)

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
        return 0.0
    if not parameterz.get(oid):
        parameterz[oid] = {}
    if not units:
        # if no units are specified, return the value in base units
        return (parameterz[oid].get(pid) or 
                NULL.get(pdz.get('range_datatype', 'float') or 'float'))
    else:
        try:
            # convert based on dimensions/units ...
            dims = pdz.get('dimensions')
            # special cases for 'percent' and 'money'
            if dims == 'percent':
                # show percentage values in interface -- they will
                # later be saved (by set_pval) as .01 * value
                return 100.0 * (parameterz[oid].get(pid) or 0.0)
            elif dims == 'money':
                # round to 2 decimal places
                val = get_pval(oid, pid)
                if val is None:
                    return 0.0
                elif val:
                    return float(Decimal(val).quantize(TWOPLACES))
                else:
                    return 0.0
            else:
                base_val = parameterz[oid][pid]
                quan = Q_(base_val, ureg.parse_expression(in_si[dims]))
                quan_converted = quan.to(units)
                return quan_converted.magnitude
        except:
            # log.debug('  "{}": something bad happened with units.'.format(
                                                                      # pid))
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
        log.debug('  - "{}" does not have a definition.'.format(pid))
        return '0'
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
                return '-'
            elif val:
                return "{:,}".format(Decimal(val).quantize(TWOPLACES))
            else:
                return '0.00'
        else:
            base_val = get_pval(oid, pid)
            if units:
                # TODO: ignore units if not compatible
                quan = Q_(base_val, ureg.parse_expression(in_si[dims]))
                quan_converted = quan.to(units)
                val = quan_converted.magnitude
            else:
                val = base_val
        range_datatype = pdz.get('range_datatype')
        if range_datatype in ['int', 'float']:
            dtype = DATATYPES.get(range_datatype)
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
        # for production use, return '' if the value causes error
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
    # NOTE:  THE OBJECT DOES NOT ALWAYS HAVE TO HAVE THE VARIABLE
    pid = get_parameter_id(variable, context_id)
    # log.debug(f'* _compute_pval() for pid "{pid}"')
    # log.debug('                  of item with oid "{}"'.format(oid))
    # log.debug('                  in context "{}"'.format(context_id))
    val = 0.0
    pdz = parm_defz.get(pid) or {}
    if not pdz:
        # log.debug('  "{}" not found in parm_defz'.format(pid))
        # log.debug('  in _compute_pval for oid "{}"'.format(oid))
        pass
    if pdz.get('computed'):
        # log.debug('  "{}" is computed ...'.format(pid))
        # look up compute function -- in the future, there may be a Relation
        # expression, found using the ParameterRelation relationship
        if not parameterz.get(oid):
            parameterz[oid] = {}
        compute = COMPUTES.get(pid)
        if compute:
            # log.debug('  compute function is {!s}'.format(getattr(
                                        # compute, '__name__', None)))
            val = compute(oid, pid) or 0.0
            # log.debug('  value is {}'.format(val))
        else:
            return val
            # log.debug('  compute function not found.')
            # val = 'undefined'
        if val != 'undefined':
            parameterz[oid][pid] = val
    elif oid in parameterz:
        # msg = '  "{}" is not computed; getting value ...'.format(pid)
        # log.debug(msg)
        val = parameterz[oid].get(pid) or 0.0
    return val

def set_pval(oid, pid, value, units='', local=True):
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
        units (str): the units in which the value is expressed;
            None -> SI (mks) base units
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
    if oid not in parameterz:
        parameterz[oid] = {}
    if pid not in parameterz.get(oid):
        added = add_parameter(oid, pid)
        if not added:
            # log.debug('  parameter could not be added (see log).')
            return False
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
            dims = pdz.get('dimensions')
            try:
                quan = Q_(value, ureg.parse_expression(units))
                quan_base = quan.to_base_units()
                converted_value = quan_base.magnitude
            except:
                # TODO: notify end user if units could not be parsed!
                # ... for now, use base units
                # log.debug('  could not parse units "{}" ...'.format(units))
                units = in_si.get(dims)
                # log.debug('  setting to base units: {}'.format(units))
                # if units parse failed, assume base units
                converted_value = value
        else:
            # None or "$" for units -> value is already in base units
            converted_value = value
        parameterz[oid][pid] = converted_value
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

def get_pval_from_str(oid, pid, str_val, units='', local=True):
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
    # This log msg is only needed for extreme debugging -- `get_pval()` is
    # called at the end and will log essentially the same information ...
    # log.debug('* get_pval_from_str({}, {}, {})'.format(oid, pid,
                                                           # str(str_val)))
    try:
        range_datatype = parm_defz[pid].get('range_datatype')
        if range_datatype in ['int', 'float']:
            # if null string or None, replace with zero
            str_val = str_val or '0'
            dtype = DATATYPES.get(range_datatype)
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

def set_pval_from_str(oid, pid, str_val, units='', local=True):
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
        units (str): the units in which the parameter value is expressed;
            None -> SI (mks) base units
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # This log msg is only needed for extreme debugging -- `set_pval()` is
    # called at the end and will log essentially the same information ...
    # log.debug('* set_pval_from_str({}, {}, {})'.format(oid, pid,
                                                           # str(str_val)))
    try:
        pd = parm_defz.get(pid) or {}
        range_datatype = pd.get('range_datatype')
        if range_datatype in ['int', 'float']:
            dtype = DATATYPES.get(range_datatype)
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
        set_pval(oid, pid, val, units=units, local=local)
    except:
        # if unable to cast a value, do nothing (and log it)
        # TODO:  more form validation!
        # msg = 'set_pval_from_str() could not convert string "{}".'
        # log.debug('* {}'.format(msg.format(str_val)))
        pass

def compute_assembly_parameter(product_oid, pid):
    """
    Compute the total assembly value of a linearly additive variable (e.g.,
    mass, power consumption, data rate) for a product based on the recursively
    summed values of the parameter over all of the product's known components.
    If no components are defined for the product, simply return the value of
    the parameter as specified for the product, or the default (usually 0).
    Note that if the product specified by the oid has components, a value will
    be returned that represents the rolled up assembly parameter even if the
    product specified does not have any parameters assigned to it.

    CAUTION: this will obviously return a wildly inaccurate value if the
    list of components in a specified assembly is incomplete.

    Args:
        product_oid (str): the oid of the Product whose total parameter is
            being estimated
        variable (str): variable for which the assembly value is being computed
    """
    # This logging is VERY verbose, even for debugging!
    # log.debug('* compute_assembly_parameter()')
    variable, context = get_variable_and_context(pid)
    if (product_oid in parameterz):
        range_datatype = parm_defz[variable]['range_datatype']
        dtype = DATATYPES[range_datatype]
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

def compute_assembly_context_parameter(product_oid, pid):
    """
    Compute the total assembly value of a linearly additive context parameter
    (e.g., peak power, survival power) for a product based on the recursively
    summed values of the parameter over all of the product's known components.
    If no components are defined for the product, simply return the value of
    the parameter as specified for the product, or the default (usually 0).
    Note that if the product specified by the oid has components, a value will
    be returned that represents the rolled up assembly parameter even if the
    product specified does not have any parameters assigned to it.

    CAUTION: this will obviously return a wildly inaccurate value if the
    list of components in a specified assembly is incomplete.

    Args:
        product_oid (str): the oid of the Product whose total parameter is
            being estimated
        variable (str): variable for which the assembly value is being computed
    """
    # This logging is VERY verbose, even for debugging!
    # log.debug('* compute_assembly_context_parameter()')
    if (product_oid in parameterz):
        range_datatype = parm_defz[pid]['range_datatype']
        dtype = DATATYPES[range_datatype]
        # cz, if it exists, will be a list of namedtuples ...
        cz = componentz.get(product_oid)
        if cz:
            # dtype cast is used here in case some component didn't have this
            # parameter or didn't exist and we got a 0.0 value for it ...
            summation = fsum(
            [dtype(compute_assembly_context_parameter(c.oid, pid) * c.quantity)
             for c in cz])
            return round_to(summation)
        else:
            # if the product has no known components, return its specified
            # value for the variable (note that the default here is 0.0)
            return get_pval(product_oid, pid)
    else:
        return 0.0

def compute_mev(oid, pid):
    """
    Compute the Maximum Expected Value of a parameter based on either [1] if it
    has components, the sum of their MEVs or [2] if it does not have
    components, its Current Best Estimate (CBE) value and the percent
    contingency specified for it.

    NOTE: MEV was redefined as a conditionally recursive computation in a new
    requirement. [2020-05-26 SCW]

    Args:
        oid (str): the oid of the Modelable containing the parameters
        variable (str): the `variable` of the parameter

    Keyword Args:
        default (any): a value to be returned if the parameter is not found
    """
    variable, context = get_variable_and_context(pid)
    if oid not in parameterz or parameterz[oid] is None:
        parameterz[oid] = {}
    # log.debug('* compute_mev "{}": "{}"'.format(oid, variable))

    # NOTE: variable is not required to be present
    # if variable not in parameterz[oid]:
        # return 0.0

    range_datatype = parm_defz[variable]['range_datatype']
    dtype = DATATYPES[range_datatype]
    # cz, if it exists, will be a list of namedtuples ...
    cz = componentz.get(oid)
    # if components, use recursive sum of MEVs; else compute locally
    if cz:
        # dtype cast is used here in case some component didn't have this
        # parameter or didn't exist and we got a 0.0 value for it ...
        summation = fsum(
          [dtype(compute_mev(c.oid, variable) * c.quantity)
           for c in cz])
        mev = round_to(summation)
        cbe = get_pval(oid, variable + '[CBE]')
        if cbe:
            ctgcy_val = round_to((mev - cbe)/cbe, n=3)
            set_pval(oid, variable + '[Ctgcy]', ctgcy_val)
        return mev
    else:
        ctgcy_val = get_pval(oid, variable + '[Ctgcy]')
        if ctgcy_val:
            ctgcy_val = round_to(ctgcy_val, n=3)
        else:
            # log.debug('  contingency not set --')
            # log.debug('  setting to default value (25%) ...')
            # if Contingency value is 0 or not set, set to default value of 25%
            # [SCW 2021-07-27] Default value changed to 25% (previously 30%)
            # per NASA Gold Rules, etc.
            ctgcy_val = 0.25
            pid = variable + '[Ctgcy]'
            parameterz[oid][pid] = ctgcy_val
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

def get_flight_units(product_oid, assembly_oid, default=1):
    """
    Find the number of units of the specified product in the specified
    assembly.

    Args:
        product_oid (str): the oid of the product
        assembly_oid (str): the oid of the assembly in which the product is a
            component

    Keyword Args:
        default (any): a value to be returned if the parameter is not found
    """
    if assembly_oid in componentz:
        for component in componentz[assembly_oid]:
            if component['oid'] == product_oid:
                return component['quantity']
    return default

def compute_margin(usage_oid, pid, default=0):
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
    variable, context = get_variable_and_context(pid)
    # log.debug('  using rqt_allocz: {}'.format(str(rqt_allocz)))
    # find requirements allocated to the specified usage and constraining the
    # specified variable
    allocated_rqt_oids = [rqt_oid for rqt_oid in rqt_allocz
                          if rqt_allocz[rqt_oid][0] == usage_oid
                          and rqt_allocz[rqt_oid][3] == variable]
    if not allocated_rqt_oids:
        # no requirement constraining the specified variable is allocated to
        # this usage
        # txt = 'usage "{}" has no reqt allocated to it constraining "{}".'
        # log.debug('  {}'.format(txt.format(usage_oid, variable)))
        return 'undefined'
    # for now, assume there is only one reqt that satisfies
    rqt_oid = allocated_rqt_oids[0]
    usage_oid, obj_oid, alloc_ref, pid, constraint = rqt_allocz[rqt_oid]
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

def compute_requirement_margin(rqt_oid, default=0):
    """
    Compute the "Margin" for the specified performance requirement. So far,
    "Margin" is only defined for performance requirements that specify a
    maximum or "Not To Exceed" value, and is computed as (NTE-CBE)/CBE, where
    CBE is the Current Best Estimate of the corresponding parameter of the
    system or component to which the requirement is currently allocated.

    Args:
        rqt_oid (str): the oid of the performance requirement for which margin
            is to be computed

    Keyword Args:
        context (str): the `id` of the context that defines the margin (for
            now, the only supported context is 'NTE', so context is ignored)
        default (any): a value to be returned if the parameter is not found

    Return:
        allocated_to_oid, parameter_id, margin (tuple)
    """
    # log.debug('* compute_requirement_margin()')
    if rqt_oid not in rqt_allocz:
        # TODO: notify user 
        msg = 'Requirement {} is not allocated.'.format(rqt_oid)
        return (None, None, None, None, msg)
    usage_oid, obj_oid, alloc_ref, pid, constraint = rqt_allocz[rqt_oid]
    if not pid:
        msg = 'Requirement {} is not a performance reqt.'.format(rqt_oid)
        return (None, None, None, None, msg)
    if constraint.constraint_type == 'maximum':
        try:
            nte = constraint.max
            nte_units = constraint.units
            # convert NTE value to base units, if necessary
            quan = nte * ureg.parse_expression(nte_units)
            quan_base = quan.to_base_units()
            converted_nte = quan_base.magnitude
        except:
            msg = 'Could not convert NTE units to base units'
            return (None, None, None, None, msg)
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

# the COMPUTES dict maps parameter id to applicable compute function
COMPUTES = {
    ('m[CBE]'):        compute_assembly_parameter,
    ('m[assembly]'):   compute_assembly_parameter,
    ('m[MEV]'):        compute_mev,
    ('m[Margin]'):     compute_margin,
    ('P[CBE]'):        compute_assembly_parameter,
    ('P[assembly]'):   compute_assembly_parameter,
    ('P[MEV]'):        compute_mev,
    ('P[Margin]'):     compute_margin,
    ('R_D[CBE]'):      compute_assembly_parameter,
    ('R_D[assembly]'): compute_assembly_parameter,
    ('R_D[MEV]'):      compute_mev,
    ('R_D[Margin]'):   compute_margin
    }

################################################
# DATA ELEMENT SECTION
################################################

# DATA ELEMENT CACHES ##################################################

# de_defz:  runtime cache of data element definitions
# purpose:  to enable fast lookup of data element metadata
# format:  {data element id: {data element properties}
#                             ...}}
# ... where data element definition properties are:
# -----------------------------------------------------------------------------
# name, label, description, range_datatype, mod_datetime
# -----------------------------------------------------------------------------
# NOTE:  although "label" (a formatted label to use as a column header) is not
# an attribute of DataElementDefinition, the label item can be set from a data
# element structure that is set in the application's "config" file, which
# create_de_defz() will use to update de_defz after populating it from the db
# DataElementDefinition objects.
de_defz = {}

def load_de_defz(dir_path):
    """
    Load the `de_defz` cache from a json file.
    """
    log.debug('* load_de_defz() ...')
    fpath = os.path.join(dir_path, 'de_defs.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            try:
                stored_de_defz = json.loads(f.read())
            except:
                log.debug('  - reading of "de_defs.json" failed.')
                return 'fail'
        de_defz.update(stored_de_defz)
        log.debug('  - de_defz cache loaded.')
        return 'success'
    else:
        log.debug('  - "de_defs.json" was not found.')
        return 'not found'

def save_de_defz(dir_path):
    """
    Save `de_defz` cache to a json file.
    """
    log.debug('* save_de_defz() ...')
    try:
        fpath = os.path.join(dir_path, 'de_defs.json')
        with open(fpath, 'w') as f:
            f.write(json.dumps(de_defz,
                               separators=(',', ':'),
                               indent=4, sort_keys=True))
        log.debug('  ... de_defs.json file written.')
    except:
        log.debug('  ... writing de_defs.json file failed!')

# data_elementz:  persistent** cache of assigned data element values
#              ** persisted in the file 'data_elements.json' in the
#              application home directory -- see the functions
#              `save_data_elementz` and `load_data_elementz`
#
# format:  {oid : {'data element id': value,
#                   ...}}
data_elementz = {}

def serialize_des(oid):
    """
    Args:
        oid (str):  the oid of the object whose data elements are to be
            serialized.

    Serialize the data elements associated with an object.
    """
    if oid in data_elementz and data_elementz[oid] is not None:
        return {deid: data_elementz[oid][deid]
                for deid in data_elementz[oid]}
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
        # log.debug('  object with oid "{}" has no data elements'.format(oid))
        return
    # ser_des is non-empty
    deids = list(ser_des)
    if ser_des[deids[0]] and isinstance(ser_des[deids[0]], dict):
        # if the value is a dict, format is old
        old_ser_des = deepcopy(ser_des)
        ser_des = {}
        for deid, dedict in old_ser_des.items():
            ser_des[deid] = dedict['value']
        log.debug('  - data elements converted from old format.')
    # this covers (1) oid not in data_elementz and (2) oid in data_elementz but
    # value is None
    if not data_elementz.get(oid):
        data_elementz[oid] = {}
    deids_to_delete = []
    for deid, value in ser_des.items():
        if deid in de_defz:
            data_elementz[oid][deid] = value
        else:
            # log_msg = 'unknown id found in data elements: "{}"'.format(deid)
            # log.debug('  - {}'.format(log_msg))
            # deid has no definition, so it should not be in data_elementz
            if deid in data_elementz[oid]:
                deids_to_delete.append(deid)
    # delete any undefined data elements
    for deid in deids_to_delete:
        if deid in data_elementz[oid]:
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

def load_data_elementz(dir_path):
    """
    Load `data_elementz` dict from json file.
    """
    log.debug('* load_data_elementz() ...')
    fpath = os.path.join(dir_path, 'data_elements.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            try:
                serialized_des = json.loads(f.read())
            except:
                log.debug('  - json decoding of "data_elements.json" failed.')
                return 'fail'
            # first check for old format and convert if necessary
            old_format = False
            oids = list(serialized_des)
            if oids:
                # find first non-empty data element dict
                n = 0
                while 1:
                    test_oid = oids[n]
                    test_dict = serialized_des[test_oid]
                    if test_dict:
                        # test_dict is non-empty
                        deids = list(test_dict)
                        if deids:
                            for deid, de_val in test_dict.items():
                                if de_val and isinstance(de_val, dict):
                                    # if the value is a dict, format is old
                                    old_format = True
                    if old_format:
                        break
                    else:
                        n += 1
                        if n == len(oids):
                            break
            if old_format:
                # convert to new format
                ser_des_old = deepcopy(serialized_des)
                serialized_des = {}
                for oid, old_de_dict in ser_des_old.items():
                    new_de_dict = {}
                    for deid in (old_de_dict or {}):
                        if old_de_dict[deid]:
                            new_de_dict[deid] = old_de_dict[deid]['value']
                        else:
                            dtype = (de_defz.get(deid, 'range_datatype', 'str')
                                     or 'str')
                            new_de_dict[deid] = NULL.get(dtype, '') or ''
                    serialized_des[oid] = new_de_dict
                log.debug('  - data_elementz cache converted from old format.')
        for oid, ser_des in serialized_des.items():
            deserialize_des(oid, ser_des)
        log.debug('  - data_elementz cache loaded.')
        return 'success'
    else:
        log.debug('  - "data_elements.json" was not found.')
        return 'not found'

def save_data_elementz(dir_path):
    """
    Save `data_elementz` dict to a json file.
    """
    log.debug('* save_data_elementz() ...')
    serialized_data_elementz = {}
    try:
        for oid, obj_des in data_elementz.items():
            # NOTE: serialize_des() uses deepcopy()
            serialized_data_elementz[oid] = serialize_des(oid)
        fpath = os.path.join(dir_path, 'data_elements.json')
        with open(fpath, 'w') as f:
            f.write(json.dumps(serialized_data_elementz,
                               separators=(',', ':'),
                               indent=4, sort_keys=True))
        log.debug('  ... data_elements.json file written.')
    except:
        log.debug('  ... writing data_elements.json file failed!')

def update_de_defz(de_def_obj):
    """
    Update the `de_defz` cache when a new DataElementDefinition is created or
    modified.

    Args:
        de_def_obj (DataElementDefinition):  DataElementDefinition object
    """
    de_defz[de_def_obj.id] = {
        'name': de_def_obj.name,
        'description': de_def_obj.description,
        'range_datatype': de_def_obj.range_datatype,
        'label': de_def_obj.label or '',
        'mod_datetime': str(dtstamp())}

def add_data_element(oid, deid, units=None):
    """
    Add a new data element to an object, which means adding a data element's data
    structure to the `p.node.parametrics.data_elementz` dictionary under that
    objects's oid, if it does not already exist for the specified paramter.

    Args:
        oid (str):  oid of the object that owns the data element
        deid (str):  the id of the data element
    """
    # oid could be a key in data_elementz but have a value of None -- if so, it
    # needs to be set as an empty dict ...
    if data_elementz.get(oid) is None:
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
        range_datatype = de_def.get('range_datatype', 'str')
        de_defaults = state.get('de_defaults') or {}
        if de_defaults.get(deid):
            # if a default value is configured for this deid, override null
            dtype = DATATYPES[range_datatype]
            value = dtype(de_defaults[deid])
        else:
            value = NULL.get(range_datatype, 0.0)
        # TODO:  add "dimensions" to data element definitions, so units can be
        # defined where applicable
        data_elementz[oid][deid] = value
        # log.debug('    data element "{}" added.'.format(deid))
        return True
    else:
        # log.debug('    data element "{}" was already there.'.format(deid))
        return True

def delete_data_element(oid, deid, local=True):
    """
    Delete a data element from an object.

    Args:
        oid (str):  oid of the object that owns the data element
        deid (str):  `id` attribute of the data element

    Keyword Args:
        local (bool):  if True, originated locally
    """
    # TODO: need to dispatch louie & pubsub messages!
    if deid in (data_elementz.get(oid) or {}):
        del data_elementz[oid][deid]
        if local:
            dispatcher.send(signal='de del', oid=oid, deid=deid)

def get_dval(oid, deid, units=''):
    """
    Return a cached data element value.

    Args:
        oid (str): the oid of the object that has the parameter
        deid (str): the data element 'id' value

    Keyword Args:
        units (str): the units in which the data element value is expressed;
            empty -> SI (mks) base units
    """
    # Too verbose -- only for extreme debugging ...
    # log.debug('* get_dval() ...')
    dedef = de_defz.get(deid)
    if not dedef:
        # log.debug('* get_dval: "{}" does not have a definition.'.format(deid))
        return '-'
    if not data_elementz.get(oid):
        data_elementz[oid] = {}
    return (data_elementz[oid].get(deid) or
            NULL.get(dedef.get('range_datatype', 'str') or 'str'))

def get_dval_as_str(oid, deid, units=''):
    """
    Return a cached data element value a string for display and editing in UI.
    (Used in the object editor, `p.node.gui.pgxnobject.PgxnObject`, the
    dashboard, and the DataGrid.)

    Args:
        oid (str): the oid of the object that has the parameter
        deid (str): the `id` of the data element

    Keyword Args:
        units (str): the units in which the data element value is expressed;
            empty -> SI (mks) base units
    """
    return str(get_dval(oid, deid))

def set_dval(oid, deid, value, units='', local=True):
    """
    Set the value of a data element instance for the specified object to the
    specified value.

    Args:
        oid (str): the oid of the Modelable that has the data element
        deid (str): the data element 'id'
        value (TBD): value should be of the datatype specified by
            the data element object's definition.range_datatype

    Keyword Args:
        units (str): the units in which `value` is expressed; empty implies
            SI (mks) base units
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
    if oid not in data_elementz:
        data_elementz[oid] = {}
    try:
        # cast value to range_datatype before setting
        dt_name = dedef['range_datatype']
        dtype = DATATYPES[dt_name]
        if value:
            value = dtype(value)
        else:
            value = NULL.get(dt_name, 0.0)
        data_elementz[oid][deid] = value
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

def set_dval_from_str(oid, deid, str_val, units='', local=True):
    """
    Set the value of a data element instance for the specified object from a
    string value.  (Mainly for use in saving input from the object editor,
    `p.node.gui.pgxnobject.PgxnObject`.)

    Args:
        oid (str): the oid of the Modelable that has the parameter
        pid (str): the parameter 'id'
        str_val (str): string value

    Keyword Args:
        units (str): the units in which `value` is expressed; empty implies
            SI (mks) base units
        local (bool):  if False, we were called as a result of a remote event
            -- i.e., someone else set the value [default: True]
    """
    # This log msg is only needed for extreme debugging -- `set_pval()` is
    # called at the end and will log essentially the same information ...
    # log.debug('* set_dval_from_str({}, {}, {})'.format(oid, deid,
                                                           # str(str_val)))
    try:
        de_def = de_defz.get(deid) or {}
        range_datatype = de_def.get('range_datatype', 'str')
        if range_datatype in ['int', 'float']:
            dtype = DATATYPES.get(range_datatype)
            num_fmt = prefs.get('numeric_format')
            if num_fmt == 'Thousands Commas' or not num_fmt:
                val = dtype(str_val.replace(',', ''))
            else:
                # this should work for both 'Scientific Notation' and
                # 'No Commas'
                val = dtype(str_val)
        else:
            val = str_val
        set_dval(oid, deid, val, local=local)
    except:
        # if unable to cast a value, do nothing (and log it)
        # TODO:  more form validation!
        # log.debug('  could not convert string "{}" ...'.format(str_val))
        pass

def add_default_data_elements(obj, des=None):
    """
    Assign any configured or preferred default data elements that are missing
    from an object.

    Args:
        obj (Identifiable):  the object to receive data elements

    Keyword Args:
        des (list):  list of data element id's to add
    """
    # log.debug('* adding default data elements to object "{}"'.format(
                                                                 # obj.id))
    deids = OrderedSet()
    cname = obj.__class__.__name__
    deids |= OrderedSet(DEFAULT_CLASS_DATA_ELEMENTS.get(cname) or [])
    # TODO: let user set default data elements in their prefs
    if not config.get('default_data_elements'):
        config['default_data_elements'] = ['TRL', 'Vendor',
                                           'reference_missions']
    if cname == 'HardwareProduct':
        # default for "default_data_elements":  Vendor
        # (state is read in p.node.gui.startup, and will be overridden by
        # prefs['default_data_elements'] if it is set
        deids |= OrderedSet(des or config['default_data_elements'])
        if obj.product_type:
            deids |= OrderedSet(DEFAULT_PRODUCT_TYPE_DATA_ELMTS.get(
                                obj.product_type.id) or [])
    # log.debug('  - adding data elements {} ...'.format(str(deids)))
    deids_to_add = deids - set(data_elementz.get(obj.oid) or [])
    if deids_to_add:
        # log.debug(f'  - adding default data elements {deids_to_add} ...')
        for deid in deids_to_add:
            add_data_element(obj.oid, deid)

################################################
# MODE SECTION
################################################

# MODE CACHES ##########################################################

# mode_defz:  persistent** cache of system power mode definitions, which
#             consist of a set of systems (ProjectSystemUsages) and subsystems
#             (Assembly Component Usages or Acus) and the applicable power
#             states of each (i.e. of their "system" or "component",
#             respectively) during a specified activity. The 'systems' sub-dict
#             contains all items that have been explicitly added to the mode
#             definitions.  If a 'system' has components, its components are
#             added to the 'components' sub-dict and its modes' power values
#             will be computed from the sum of its components power values for
#             each mode.  If a 'system' has no components, then its modes'
#             power values have to be explicitly defined rather than computed.
#
#             ** persisted in the file 'mode_defs.json' in the
#             application home directory -- see the functions
#             `save_mode_defz` and `load_mode_defz`
#
# format:  {project A oid:
#               'modes': {mode 1 act.oid: act.name,
#                         mode 2 act.oid: act.name,
#                         ...},
#               'systems':
#                  {psu 1 oid: {mode 1 act.oid: mode 1 modal_context**,
#                               mode 2 act.oid: mode 2 modal_context**,
#                                ...},
#                   acu 1 oid: {mode 3 act.oid: mode 3 modal_context**,
#                               mode 4 act.oid: mode 4 modal_context**,
#                                ...}
#                   ...},
#               'components':
#                  {psu 1 oid:
#                       {acu 3 oid: {mode 5 act.oid: mode 5 modal_context**,
#                                    mode 6 act.oid: mode 6 modal_context**,
#                                    ...},
#                        acu 4 oid: {mode 7 act.oid: mode 7 modal_context**,
#                                    mode 8 act.oid: mode 8 modal_context**,
#                                    ...}
#                        ...},
#                   psu 2 oid:
#                       {acu 5 oid ...},
#                   acu 1 oid:
#                       {acu 6 oid ...}
#                   ...},
#           project B oid:
#               {...}
#           }
# ... where
# * default context: to be used if None or empty dict is specified as context
# ** mode n modal_context: None (Off), "[computed]", or a ParameterContext id
mode_defz = {}

def load_mode_defz(dir_path):
    """
    Load the `mode_defz` dict from file in cache format.
    """
    log.debug('* load_mode_defz() ...')
    fpath = os.path.join(dir_path, 'mode_defs.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            try:
                stored_mode_defz = json.loads(f.read())
            except:
                log.debug('  - reading of "mode_defs.json" failed.')
                return 'fail'
        mode_defz.update(stored_mode_defz)
        log.debug('  - mode_defz cache loaded.')
        return 'success'
    else:
        log.debug('  - "mode_defs.json" was not found.')
        return 'not found'

def save_mode_defz(dir_path):
    """
    Save `mode_defz` dict to a file in cache format.
    """
    log.debug('* save_mode_defz() ...')
    try:
        fpath = os.path.join(dir_path, 'mode_defs.json')
        with open(fpath, 'w') as f:
            f.write(json.dumps(mode_defz, separators=(',', ':'),
                               indent=4))
        log.debug(f'  ... mode_defs.json file written to {dir_path}.')
    except:
        log.debug('  ... writing data_elements.json file failed!')

def get_modal_context(project_oid, usage_oid, mode_oid):
    """
    Get the value of the modal_context (i.e. power level corresponding to a
    mode) for the specified mode of the specified project and usage.

    Args:
        project_oid (str): the oid of the project within which the mode is
            defined
        usage_oid (str): the oid of the usage that has the mode
        mode_oid (str): the oid of the mode (activity)
    """
    if not project_oid in mode_defz:
        return ''
    sys_dict = mode_defz[project_oid].get('systems')
    if not sys_dict:
        return ''
    if usage_oid in sys_dict:
        if mode_oid in sys_dict[usage_oid]:
            return sys_dict[usage_oid][mode_oid]
        else:
            return ''
    else:
        comp_dict = mode_defz[project_oid].get('components')
        if comp_dict:
            comp_mode = ''
            for sys_oid in comp_dict:
                if usage_oid in list(comp_dict[sys_oid]):
                    comp_mode = comp_dict[sys_oid][usage_oid].get(mode_oid)
                    break
            return comp_mode or ''
        else:
            return ''

def set_comp_modal_context(project_oid, sys_usage_oid, usage_oid, mode_oid,
                           level):
    """
    Set the value of the modal_context (a.k.a. power level corresponding to a
    mode) for a component of the specified system usage in the specified
    project for the specified mode.

    Args:
        project_oid (str): the oid of the project within which the mode is
            defined
        sys_usage_oid (str): the oid of the usage of the system that contains
            the component that has the mode
        usage_oid (str): the oid of the usage that has the mode
        mode_oid (str): the oid of the mode (activity)
    """
    if not project_oid in mode_defz:
        mode_defz[project_oid] = dict(modes={}, systems={}, components={})
    sys_dict = mode_defz[project_oid]['systems']
    comp_dict = mode_defz[project_oid]['components']
    if sys_usage_oid not in sys_dict:
        sys_dict[sys_usage_oid] = {}
    sys_dict[sys_usage_oid][mode_oid] = '[computed]'
    if sys_usage_oid not in comp_dict:
        comp_dict[sys_usage_oid] = {}
    if usage_oid not in comp_dict[sys_usage_oid]:
        comp_dict[sys_usage_oid][usage_oid] = {}
    comp_dict[sys_usage_oid][usage_oid][mode_oid] = level

def get_modal_power(project_oid, sys_usage_oid, oid, mode, modal_context,
                    units=None):
    """
    Get the numeric value of the modal power in the specified units for either
    (1) if the modal_context is "computed", the computed modal power in the
    specified "mode" of the system with the specified oid which is in the
    "assembly" attribute of the usage with the specified sys_usage_oid, or
    (2) the spec value of the power for the product with the specified oid in
    the specified modal_context (as the modal_context is either a known spec
    power level or is mapped to a known spec power level).

    Args:
        project_oid (str): the oid of the project within which the mode is
            defined
        sys_usage_oid (str): the oid of the usage that has the mode
        oid (str): the oid of the product assembly containing the usage
        mode (str): the oid of the mode (activity)

    Keyword Args:
        units (str):  units in which the return value should be expressed
    """
    if modal_context == '[computed]':
        sys_dict = mode_defz[project_oid].get('systems') or {}
        comp_dict = mode_defz[project_oid].get('components') or {}
        # log.debug('* computing modal power value ...')
        cz = componentz.get(oid)
        if (sys_usage_oid in comp_dict) and cz:
            # log.debug(f'  - found {len(cz)} components ...')
            # dtype cast is used here in case some component didn't have this
            # parameter or didn't exist and we got a 0.0 value for it ...
            summation = 0.0
            for c in cz:
                if c.usage_oid in comp_dict[sys_usage_oid]:
                    context = (comp_dict[sys_usage_oid][c.usage_oid].get(mode)
                               or 'Off')
                elif c.usage_oid in sys_dict:
                    context = sys_dict[c.usage_oid].get(mode) or 'Off'
                else:
                    context = 'Off'
                if context == 'Nominal':
                    context = 'CBE'
                if context == 'Off':
                    val = 0.0
                else:
                    if context == '[computed]':
                        val = get_modal_power(project_oid, c.usage_oid, c.oid,
                                              mode, context, units=units)
                    else:
                        val = get_pval(c.oid, get_parameter_id('P', context),
                                       units=units)
                # log.debug(f'    + {val} (context: {context})')
                summation += (val or 0.0) * c.quantity
            # log.debug(f'  total: {summation}')
            return round_to(summation)
        else:
            # if the product has no known components, return its specified
            # value for the variable (note that the default here is 0.0)
            return get_pval(oid, get_parameter_id('P', modal_context),
                            units=units)
    elif modal_context == 'Off':
        return 0.0
    elif modal_context == 'Nominal':
        return get_pval(oid, 'P[CBE]', units=units)
    return get_pval(oid, get_parameter_id('P', modal_context), units=units)

def get_power_contexts(obj):
    """
    Return the contexts of all power (P) parameters for an object, adding an
    "Off" context.
    """
    pids = []
    if obj.oid in parameterz:
        pids = list(parameterz[obj.oid])
    if pids:
        ptups = [get_variable_and_context(pid) for pid in pids
                 if pid.split('[')[0] == 'P']
        contexts = [ptup[1] for ptup in ptups
                    if ptup[1] and ptup[1] not in ['MEV', 'Ctgcy']]
        contexts.insert(0, 'Off')
        return contexts
    return ['Off']

def get_usage_mode_val(project_oid, usage_oid, oid, mode, units='',
                       allow_nan=False):
    """
    Return the power mode value for a usage in base units or in the units
    specified.

    Args:
        project_oid (str): the oid of the project within which the mode is
            defined
        usage_oid (str): the oid of the usage that has the mode
        oid (str): the oid of the product in the usage (system or component)
        mode (str): the name of the mode

    Keyword Args:
        units (str):  units in which the return value should be expressed
    """
    # Too verbose -- only for extreme debugging ...
    # log.debug('* get_usage_mode_val() ...')
    if project_oid not in mode_defz:
        log.debug('* the specified project has no modes defined.')
        return 0.0
    modes = mode_defz[project_oid].get('modes') or {}
    if mode not in modes:
        log.debug(f'* mode "{mode}" is not defined for the specified project.')
        return 0.0
    sys_dict = mode_defz[project_oid].get('systems') or {}
    comp_dict = mode_defz[project_oid].get('components') or {}
    if not sys_dict:
        log.debug('* no systems in this project have modes defined.')
        return 0.0
    if usage_oid in sys_dict:
        context = sys_dict[usage_oid].get(mode)
        if context is None:
            context = "Off"
            sys_dict[usage_oid][mode] = context
        return get_modal_power(project_oid, usage_oid, oid, mode, context,
                               units=units)
    else:
        # not a system usage -- check if included as a component ...
        val = None
        for sys_usage_oid in comp_dict:
            if usage_oid in comp_dict[sys_usage_oid]:
                # get Power value specified for that context
                context = comp_dict[sys_usage_oid][usage_oid].get(mode)
                if context is None:
                    context = "Off"
                    comp_dict[sys_usage_oid][usage_oid][mode] = context
                val = get_modal_power(project_oid, usage_oid, oid, mode,
                                      context, units=units)
        if val == None:
            # not defined
            log.debug(f'* no modes defined for components of with oid "{oid}".')
            val = 0.0
        return val

def get_usage_mode_val_as_str(project_oid, usage_oid, oid, mode, units='',
                              allow_nan=False):
    """
    Return the power mode value for a usage in the specified units (or in base
    units if not specified) as a formatted string, for display in UI.  (Used in
    the dashboard.)

    Args:
        project_oid (str): the oid of the project within which the mode is
            defined
        usage_oid (str): the oid of the usage that has the mode
        oid (str): the oid of the product in the usage (system or component)
        mode (str): the name of the mode

    Keyword Args:
        units (str):  units in which the return value should be expressed
        allow_nan (bool):  allow numpy NaN as a return value
    """
    # Too verbose -- only for extreme debugging ...
    # log.debug('* get_usage_mode_val_as_str({}, {})'.format(oid, pid))
    try:
        val = get_usage_mode_val(project_oid, usage_oid, oid, mode,
                                 units=units)
        if val is None:
            return ''
        return str(val) or '-'
    except:
        # FOR EXTREME DEBUGGING ONLY:
        # this logs an ERROR for every unpopulated parameter
        # msg = '* get_usage_mode_val_as_str({}, {})'.format(oid, pid)
        # msg += '  encountered an error.'
        # log.debug(msg)
        # for production use, return '' if the value causes error
        return 'exception'

