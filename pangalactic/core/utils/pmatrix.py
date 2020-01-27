# -*- coding: utf-8 -*-
"""
Pan Galactic parameter matrix
"""
# pangalactic
from pangalactic.core.parametrics import get_pval
from pangalactic.core.uberorb     import orb


def refresh_pmatrix(pmatrix, context):
    """
    Refresh the generated fields in a parameter matrix. If no pmatrix is passed
    in, generate a new one.  A parameter matrix is a dict that maps oids to
    dicts of values ("records"), where the record structure is specified by the
    schema of the pmatrix.

    Args:
        pmatrix (dict of dicts):  the MEL to be refreshed
        context (Project or Product):  the project or system to which the
            parameters pertain
    """
    pmatrix = pmatrix or {}
    new = False
    if not pmatrix:
        new = True
        row = 1
    if new:
        if isinstance(context, orb.classes['Project']):
            # context is Project, so may include several systems
            project = context
            system_names = [psu.system.name.lower() for psu in project.systems]
            system_names.sort()
            systems_by_name = {psu.system.name.lower() : psu.system
                               for psu in project.systems}
            for system_name in system_names:
                system = systems_by_name[system_name]
                row = get_components_parms(pmatrix, 1, row, system)
        elif isinstance(context, orb.classes['Product']):
            # context is Product -> a single system MEL
            system = context
            row = get_components_parms(pmatrix, 1, row, system)
        else:
            # not a Project or Product -- yikes, punt!
            pmatrix = {}
    else:
        # [1] add/remove oids as necessary
        # [2] update existing oids
        pmatrix = {}
    return pmatrix

def get_components_parms(pmatrix, level, row, component, qty=1):
    oid = component.oid
    pmatrix['m_unit'] = get_pval(orb, oid, 'm[CBE]')
    pmatrix['m_cbe'] = qty * pmatrix['m_unit']
    pmatrix['m_ctgcy'] = get_pval(orb, oid, 'm[Ctgcy]')
    pmatrix['m_mev'] = qty * get_pval(orb, oid, 'm[MEV]')
    pmatrix['nom_p_unit_cbe'] = get_pval(orb, oid, 'P[CBE]')
    pmatrix['nom_p_cbe'] = qty * pmatrix['nom_p_unit_cbe']
    pmatrix['nom_p_ctgcy'] = get_pval(orb, oid, 'P[Ctgcy]')
    pmatrix['nom_p_mev'] = qty * get_pval(orb, oid, 'P[MEV]')
    # columns in spreadsheet MEL:
    #   0: Level
    #   1: Name
    #   2: Unit MASS CBE
    #   9: Mass CBE
    #  10: Mass Contingency (%)
    #  11: Mass MEV
    #  12: Unit Power CBE
    #  13: Power CBE
    #  14: Power Contingency (%)
    #  15: Power MEV
    row += 1
    print('writing {} in row {}'.format(component.name, row))
    # then write the "LEVEL" cell
    pmatrix[oid]['level'] = level
    pmatrix[oid]['name'] = component.name
    if component.components:
        next_level = level + 1
        comp_names = [acu.component.name.lower()
                      for acu in component.components]
        comp_names.sort()
        comps_by_name = {acu.component.name.lower() : acu.component
                         for acu in component.components}
        qty_by_name = {acu.component.name.lower() : acu.quantity or 1
                       for acu in component.components}
        for comp_name in comp_names:
            comp = comps_by_name[comp_name]
            qty = qty_by_name[comp_name]
            row = get_components_parms(pmatrix, next_level, row, comp, qty)
    return row

