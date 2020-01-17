# -*- coding: utf-8 -*-
"""
Pan Galactic Master Equipment List (MEL) utility
"""
import os
import ruamel_yaml as yaml
from collections import OrderedDict

# pangalactic
from pangalactic.core.parametrics import get_pval
from pangalactic.core.uberorb     import orb


mel_fields = OrderedDict(
    row=dict(range='int', name='Row in MEL Report'),
    level=dict(range='int', name='Level in Assembly Hierarchy'),
    name=dict(range='str', name='System/Subsystem Name'),
    unit_mass=dict(range='float', name='Unit Mass'),
    cold_units=dict(range='int', name='Cold (Unpowered) Units'),
    hot_units=dict(range='int', name='Hot (Powered) Units'),
    fhw_units=dict(range='int', name='Flight Units'),
    fhw_spares=dict(range='int', name='Flight Spares'),
    etu_qual_units=dict(range='int', name='ETU/Qual Units'),
    em_edu_prototype_units=dict(range='int',
                                name='Units Used in Prototype'),
    mass_cbe=dict(range='float', name='Mass CBE'),
    mass_ctgcy=dict(range='float', name='Mass Contingency'),
    mass_mev=dict(range='float', name='Mass MEV'),
    nom_unit_power_cbe=dict(range='float',
                            name='Nominal Unit Power CBE'),
    nom_power_cbe=dict(range='float',
                            name='Nominal Power CBE'),
    nom_power_ctgcy=dict(range='float',
                            name='Nominal Power Contingency'),
    nom_power_mev=dict(range='float',
                            name='Nominal Power MEV'),
    peak_unit_power_cbe=dict(range='float',
                            name='Peak Unit Power CBE'),
    peak_total_power_cbe=dict(range='float',
                            name='Peak Power CBE'),
    peak_power_ctgcy=dict(range='float',
                            name='Peak Power Contingency'),
    peak_power_mev=dict(range='float',
                            name='Peak Power MEV'),
    quiescent_total_power=dict(range='float',
                            name='Quiescent Power CBE'),
    quoted_unit_price=dict(range='float', name='Quoted Unit Price ($K)'),
    composition=dict(range='str', name='Composition'),
    additional_information=dict(range='str',
                            name='Additional Information'),
    trl=dict(range='int', name='Technology Readiness Level (TRL)'),
    similarity=dict(range='str', name='Similarity to Existing'),
    heritage_design=dict(range='str', name='Heritage Design'),
    heritage_mfr=dict(range='str', name='Heritage Manufacture'),
    heritage_software=dict(range='str', name='Heritage Software'),
    heritage_provider=dict(range='str', name='Heritage Provider'),
    heritage_use=dict(range='str', name='Heritage Use'),
    heritage_op_env=dict(range='str', name='Heritage Operating Environment'),
    heritage_prior_use=dict(range='str', name='Heritage Ref Prior Use'),
    reference_missions=dict(range='str', name='Reference Mission(s)'),
    heritage_justification=dict(range='str', name='Heritage Justification'),
    cost_structure_mass=dict(range='str', name='Structure Mass (kg)'),
    cost_electronic_complexity=dict(range='str',
                            name='Electronic Complexity Factor'),
    cost_structure_complexity=dict(range='str',
                            name='Structure Complexity Factor'),
    cost_electronic_remaining_design=dict(range='str',
                            name='Electronic Remaining Design'),
    cost_structure_remaining_design=dict(range='str',
                            name='Structure Remaining Design'),
    cost_engineering_complexity_mod_level=dict(range='str',
                            name='Engineering Complexity Mod. Level'),
    )

mel_schema = dict(field_names=list(mel_fields), fields=mel_fields)

def read_mel(orb, context_id):
    """
    Read a MEL that has been stored in a yaml file.

    Args:
        orb (Uberorb):  the imported orb instance
        context_id (str):  the 'id' of the project or system whose MEL is to be
            read
    """
    mel = {}
    mel_fname = context_id + '_mel.yaml'
    melpath = os.path.join(orb.home, 'vault', mel_fname)
    if os.path.exists(melpath):
        f = open(melpath)
        data = f.read()
        if data:
            mel.update(yaml.safe_load(data))
        f.close()
    return mel

def refresh_mel(mel, context, is_project=True):
    """
    Refresh the generated fields in a Master Equipment List (MEL)

    Args:
        mel (list of dict):  the MEL to be refreshed
        context (Project or Product):  the project or system
        is_project (bool):  True if context is a Project; False otherwise
    """
    start_row = 1
    if is_project:
        # context is Project, so may include several systems
        project = context
        # HEADER
        # mel_label = 'MISSION: {}'.format(project.id)
        # worksheet.write(hrow1, 1, mel_label, fmts['left_pale_blue_bold_12'])
        system_names = [psu.system.name.lower() for psu in project.systems]
        system_names.sort()
        systems_by_name = {psu.system.name.lower() : psu.system
                           for psu in project.systems}
        for system_name in system_names:
            last_row = get_components_parms(mel, 1, start_row,
                                            systems_by_name[system_name])
            start_row = last_row + 1
    else:
        # context is Product -> a single system MEL
        system = context
        # ANOTHER HEADER
        # worksheet.write(hrow1, 1, system.name, fmts['left_pale_blue_bold_12'])
        get_components_parms(mel, 1, start_row, system)

def get_components_parms(mel, level, row, component, qty=1):
    mcbe = get_pval(orb, component.oid, 'm[CBE]')
    ctgcy_m = str(100 * get_pval(orb, component.oid, 'm[Ctgcy]')) + ' %'
    mmev = get_pval(orb, component.oid, 'm[MEV]')
    pcbe = get_pval(orb, component.oid, 'P[CBE]')
    ctgcy_P = str(100 * get_pval(orb, component.oid, 'P[Ctgcy]')) + ' %'
    pmev = get_pval(orb, component.oid, 'P[MEV]')
    # columns:
    #   0: Level
    #   1: Name
    #   2: UNIT MASS CBE
    #   8: Mass CBE
    #   9: Mass Contingency (Margin)
    #  10: Mass MEV
    #  12: Power CBE
    #  13: Power Contingency (Margin)
    #  14: Power MEV
    row += 1
    print('writing {} in row {}'.format(component.name, row))
    # then write the "LEVEL" cell
    mel[row]['level'] = level
    # level-based indentation
    spaces = '  ' * level
    mel[row]['Name'] = spaces + component.name
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
            mel[row] = get_components_parms(mel, next_level, row,
                                            comps_by_name[comp_name],
                                            qty=qty_by_name[comp_name])
    return row

