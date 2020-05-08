"""
Utility functions to support validation checks.
"""
import re
from collections import OrderedDict
from functools import reduce
from string import ascii_letters, digits
from pangalactic.core.meta import PGXN_REQD


ID_ALLOWED_CHARS = set(ascii_letters + digits + '_' + '.' + '-' + '/' )
PD_ID_PATTERN = r'[A-Za-z0-9][A-Za-z0-9]*(_[A-Za-z0-9][A-Za-z0-9]*)?'
NAME_DISALLOWED_CHARS = set('<>')
PID_FMT = """letters and numbers separated by a single underscore "_"
 ... Examples: "X_y", "Angle_32", "XXX_Range"."""


def check_for_cycles(product):
    """
    Check for cyclical data structures among all [known] components used at
    every level of assembly of the specified product.

    Args:
        product (Product): the Product in which to look for cycles
    """
    if product:
        comps = [acu.component for acu in product.components]
        if product.oid in [c.oid for c in comps]:
            txt = 'is a component of itself.'
            return 'product {} (id: "{}" {}'.format(
                                            product.oid, product.id, txt)
        if comps:
            try:
                comps = reduce(lambda x,y: x+y, [get_bom(c) for c in comps],
                               comps)
            except RecursionError:
                txt = 'occurs in a lower level of its own assembly.'
                return 'product {} (id: "{}" {}'.format(
                                            product.oid, product.id, txt)
        return ''
    return ''


def get_bom(product):
    """
    Return a list (a.k.a. "Bill of Materials") of all [known] components used
    at every level of assembly of the specified product.

    Args:
        product (Product): the Product whose bom is to be computed
    """
    # NOTE: this will explode if assembly is circular!!
    if product:
        comps = [acu.component for acu in product.components]
        if comps:
            comps = reduce(lambda x,y: x+y, [get_bom(c) for c in comps], comps)
        return comps
    return []


def get_bom_oids(product):
    return set([getattr(p, 'oid', '') for p in get_bom(product)
                if hasattr(p, 'oid')])


def get_assembly(product):
    """
    Return the product's assembly structure, including all Acu instances plus
    all [known] components used at every level of assembly of the specified
    product.

    Args:
        product (Product): the Product whose assembly is to be returned
    """
    if product:
        comps = get_bom(product)
        base_acus = list(product.components)
        acus = reduce(lambda x,y: x+y,
                      [getattr(c, 'components', []) for c in comps],
                      base_acus)
        return comps + acus
    return []


def validate_all(fields_dict, cname, schema, view, required=None, idvs=None,
                 ids=None, html=False):
    """
    Check a dict of form fields for minimum required fields and valid data.

    Args:
        fields_dict (dict):  dict mapping form field names to values
        cname (str):  class name of a pangalactic domain object
        schema (dict):  schema of the class
        view (list of str):  view used by the form being validated

    Keyword Args:
        required (list of str):  fields required to have non-null values (if
            None, the required fields specified for the object's class in
            PGXN_REQD are used) -- NOTE that a field in 'required' will not be
            validated if it is not also in 'view'
        idvs (list of tuples):  list of current (`id`, `version`) values to be
            avoided
        html (bool):  output msgs in a format suitable for embedding in html
            (e.g., "rich text" in a Qt text widget)
    """
    msg_dict = OrderedDict()
    # field_names has the correct order -- use it for ordering output
    id_value = fields_dict.get('id')
    idvs = idvs or [('', '')]
    if id_value:
        invalid = list(set(id_value) - ID_ALLOWED_CHARS)
        if 'version' in fields_dict:
            idv = (fields_dict.get('id'), fields_dict.get('version'))
            if idv in idvs:
                msg = '{} with id + version '.format(cname)
                msg += '"{}.v.{}" exists.'.format(idv[0], idv[1])
                msg_dict['Duplicate id + version'] = msg
        else:
            ids = set([idv[0] for idv in idvs])
            if id_value in ids:
                msg_dict['Duplicate id'] = '{} with id "{}" exists.'.format(
                                                            cname, id_value)
        if cname == 'ParameterDefinition':
            # special format required for ParameterDefinition id
            try:
                m = re.match(PD_ID_PATTERN, id_value)
                if not m.group(0) == id_value:
                    msg_dict['Parameter ID'] = PID_FMT
            except:
                msg_dict['Parameter ID'] = PID_FMT
        if invalid:
            if html:
                if '<' in invalid:
                    invalid[invalid.index('<')] = '&lt;'
                if '>' in invalid:
                    invalid[invalid.index('>')] = '&gt;'
            if ' ' in id_value:
                msg_dict['id'] = 'cannot contain spaces.'
            elif len(invalid) == 1:
                msg_dict['id'] = 'contains evil "{}" character'.format(
                                                            str(invalid[0]))
            else:
                msg_dict['id'] = 'contains evil characters: {}'.format(
                                  ', '.join(['"'+s+'"' for s in invalid]))
    name_value = fields_dict.get('name')
    if name_value:
        invalid = list(set(name_value) & NAME_DISALLOWED_CHARS)
        if invalid:
            if html:
                if '<' in invalid:
                    invalid[invalid.index('<')] = '&lt;'
                if '>' in invalid:
                    invalid[invalid.index('>')] = '&gt;'
            if len(invalid) == 1:
                msg_dict['name'] = 'contains evil "{}" character'.format(
                                                            str(invalid[0]))
            else:
                msg_dict['name'] = 'contains evil characters: {}'.format(
                                   ', '.join(['"'+s+'"' for s in invalid]))
    fields = schema['field_names']
    to_be_validated = [n for n in fields if n in view] or fields
    required = required or PGXN_REQD.get(cname) or []
    # 'version' and 'url' may always be blank
    required = [f for f in required if f not in ('version', 'url')]
    for fname in to_be_validated:
        if (fname in required) and not fields_dict.get(fname):
            msg_dict[fname] = 'is required.'
    return msg_dict

