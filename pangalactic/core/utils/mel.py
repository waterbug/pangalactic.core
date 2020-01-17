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
    m_unit=dict(range='float', name='Unit Mass'),
    cold_units=dict(range='int', name='Cold (Unpowered) Units'),
    hot_units=dict(range='int', name='Hot (Powered) Units'),
    flight_units=dict(range='int', name='Flight Units'),  # cold + hot
    flight_spares=dict(range='int', name='Flight Spares'),
    etu_qual_units=dict(range='int', name='ETU/Qual Units'),
    em_edu_prototype_units=dict(range='int', name='Units Used in Prototype'),
    m_cbe=dict(range='float', name='Mass CBE'),
    m_ctgcy=dict(range='float', name='Mass Contingency'),
    m_mev=dict(range='float', name='Mass MEV'),
    nom_p_unit_cbe=dict(range='float', name='Nominal Unit Power CBE'),
    nom_p_cbe=dict(range='float', name='Nominal Power CBE'),
    nom_p_ctgcy=dict(range='float', name='Nominal Power Contingency'),
    nom_p_mev=dict(range='float', name='Nominal Power MEV'),
    peak_p_unit_cbe=dict(range='float', name='Peak Unit Power CBE'),
    peak_p_cbe=dict(range='float', name='Peak Power CBE'),
    peak_p_ctgcy=dict(range='float', name='Peak Power Contingency'),
    peak_p_mev=dict(range='float', name='Peak Power MEV'),
    quiescent_p_cbe=dict(range='float', name='Quiescent Power CBE'),
    quoted_unit_price=dict(range='float', name='Quoted Unit Price ($K)'),
    composition=dict(range='str', name='Composition'),
    additional_information=dict(range='str', name='Additional Information'),
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

# 'field_names' will have same ordering as schema, which is an ordered dict --
# the 'field_names' list is needed to maintain the field ordering when
# serialized/deserialized, since ordinary dicts do not maintain ordering when
# deserialized but lists do.
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

def refresh_mel(mel, context):
    """
    Refresh the generated fields in a Master Equipment List (MEL), or if no MEL
    is passed in, generate a new one.  The MEL object is a dict that maps oids
    to MEL "records", where the record structure is specified by the mel
    schema.

        mel[oid] = [row, level, name, unit_mass, ...]

    Args:
        mel (dict of dicts):  the MEL to be refreshed
        context (Project or Product):  the project or system
    """
    mel = mel or {}
    new = False
    if not mel:
        # TODO:  use read_mel() to look for existing MEL related to 'context'
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
                row = get_components_parms(mel, 1, row, system)
        elif isinstance(context, orb.classes['Product']):
            # context is Product -> a single system MEL
            system = context
            row = get_components_parms(mel, 1, row, system)
        else:
            # not a Project or Product -- yikes, punt!
            mel = {}
    else:
        # existing MEL:
        #     [1] add/remove oids as necessary
        #     [2] update existing oids
        mel = {}
    return mel

def get_components_parms(mel, level, row, component, qty=1):
    oid = component.oid
    mel['m_unit'] = get_pval(orb, oid, 'm[CBE]')
    mel['m_cbe'] = qty * mel['m_unit']
    mel['m_ctgcy'] = get_pval(orb, oid, 'm[Ctgcy]')
    mel['m_mev'] = qty * get_pval(orb, oid, 'm[MEV]')
    mel['nom_p_unit_cbe'] = get_pval(orb, oid, 'P[CBE]')
    mel['nom_p_cbe'] = qty * mel['nom_p_unit_cbe']
    mel['nom_p_ctgcy'] = get_pval(orb, oid, 'P[Ctgcy]')
    mel['nom_p_mev'] = qty * get_pval(orb, oid, 'P[MEV]')
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
    mel[oid]['level'] = level
    mel[oid]['name'] = component.name
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
            row = get_components_parms(mel, next_level, row, comp, qty)
    return row

