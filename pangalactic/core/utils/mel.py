# -*- coding: utf-8 -*-
"""
Pan Galactic Master Equipment List (MEL) utility
"""
import os
import ruamel_yaml as yaml

# pangalactic
from pangalactic.core.parametrics import get_pval
from pangalactic.core.uberorb     import orb


mel_field_names = ['level', 'name', 'unit_mass', 'cold_units', 'hot_units',
    'fhw_units', 'fhw_spares', 'em_prototype', 'fhw_mass_cbe',
    'fhw_mass_contingency', 'fhw_mass_mev', 'fhw_unit_power_cbe',
    'fhw_total_power_cbe', 'fhw_power_contingency', 'fhw_power_mev',
    'fhw_peak_unit_power_cbe', 'fhw_peak_total_power_cbe',
    'fhw_peak_power_contingency', 'fhw_total_power_mev',
    'quiescent_total_power', 'quoted_price', 'composition',
    'additional_information', 'trl', 'vendor_maturity', 'location',
    'hver_temp', 'hver_pressure', 'hver_entry_load', 'hver_tid',
    'new_tech_or_ec', 'ownership', 'performance_change', 'heritage_design',
    'heritage_mfr', 'heritage_software', 'heritage_provider',
    'heritage_use', 'heritage_op_env', 'heritage_prior_use',
    'reference_missions', 'heritage_justification', 'cost_structure_mass',
    'cost_electronic_complexity', 'cost_structure_complexity',
    'cost_electronic_remaining_design', 'cost_structure_remaining_design',
    'cost_engineering_complexity_mod_level']

mel_fields = dict(
    level=dict(range='int', definition='Assembly Hierarchy'),
    name=dict(range='str', definition='System/Subsystem Name'),
    unit_mass=dict(range='float', definition='Mass of Unit'),
    cold_units=dict(range='int', definition='Unpowered Units'),
    hot_units=dict(range='int', definition='Powered Units'),
    fhw_units=dict(range='int', definition='Units to be Flown'),
    fhw_spares=dict(range='int', definition='Units not to be Flown'),
    em_prototype=dict(range='int', definition='Units Used in Prototype'),
    fhw_mass_cbe=dict(range='float', definition='CBE of Flight HW Mass'),
    fhw_mass_contingency=dict(range='float',
                             definition='Flight HW Mass Contingency'),
    fhw_mass_mev=dict(range='float', definition='Flight HW Mass MEV'),
    fhw_unit_power_cbe=dict(range='float', definition=''),
    fhw_total_power_cbe=dict(range='float', definition=''),
    fhw_power_contingency=dict(range='float', definition=''),
    fhw_power_mev=dict(range='float', definition=''),
    fhw_peak_unit_power_cbe=dict(range='float', definition=''),
    fhw_peak_total_power_cbe=dict(range='float', definition=''),
    fhw_peak_power_contingency=dict(range='float', definition=''),
    fhw_total_power_mev=dict(range='float', definition=''),
    quiescent_total_power=dict(range='float', definition=''),
    quoted_price=dict(range='float', definition=''),
    composition=dict(range='str', definition=''),
    additional_information=dict(range='str', definition=''),
    trl=dict(range='int', definition=''),
    vendor_maturity=dict(range='str', definition=''),
    location=dict(range='', definition=''),
    hver_temp=dict(range='', definition=''),
    hver_pressure=dict(range='', definition=''),
    hver_entry_load=dict(range='', definition=''),
    hver_tid=dict(range='', definition=''),
    new_tech_or_ec=dict(range='', definition=''),
    ownership=dict(range='', definition=''),
    performance_change=dict(range='', definition=''),
    heritage_design=dict(range='', definition=''),
    heritage_mfr=dict(range='', definition=''),
    heritage_software=dict(range='', definition=''),
    heritage_provider=dict(range='', definition=''),
    heritage_use=dict(range='', definition=''),
    heritage_op_env=dict(range='', definition=''),
    heritage_prior_use=dict(range='', definition=''),
    reference_missions=dict(range='', definition=''),
    heritage_justification=dict(range='', definition=''),
    cost_structure_mass=dict(range='', definition=''),
    cost_electronic_complexity=dict(range='', definition=''),
    cost_structure_complexity=dict(range='', definition=''),
    cost_electronic_remaining_design=dict(range='', definition=''),
    cost_structure_remaining_design=dict(range='', definition=''),
    cost_engineering_complexity_mod_level=dict(range='', definition='')
    )

mel_schema = dict(field_names=mel_field_names, fields=mel_fields)

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
    # Set position of title
    title_row = 0
    # Set relative positions of header rows
    hrow1 = title_row + 1
    hrow2 = hrow1 + 1
    hrow3 = hrow2 + 1
    # # HEADERS
    # # First row of headers (hrow1)
    # worksheet.write(hrow1, 0, 'LEVEL', fmts['ctr_pale_blue_bold_12'])
    # worksheet.write(hrow1, 1, 'NAME (Mission or Payload Name)',
                                        # fmts['ctr_pale_blue_bold_12'])
    # worksheet.write(hrow1, 2, 'UNIT\nMASS', fmts['ctr_pale_blue_bold_12'])
    # worksheet.merge_range(hrow1, 3, hrow1, 7, '# OF UNITS',
                          # fmts['ctr_pale_blue_bold_12'])
    # worksheet.merge_range(hrow1, 8, hrow1, 10, 'FLIGHT HARDWARE MASS',
                          # fmts['ctr_pale_blue_bold_12'])
    # worksheet.merge_range(hrow1, 11, hrow1, 14,
                          # 'NOMINAL FLIGHT HARDWARE POWER',
                          # fmts['ctr_pale_blue_bold_12'])
    # worksheet.merge_range(hrow1, 15, hrow1, 18,
                          # 'PEAK FLIGHT HARDWARE POWER',
                          # fmts['ctr_gray_bold_12'])
    # worksheet.write(hrow1, 19, 'QUIESCENT', fmts['ctr_gray_bold_12'])
    # worksheet.write(hrow1, 22, 'ADDITIONAL INFORMATION',
                    # fmts['ctr_pale_blue_bold_12'])
    # worksheet.merge_range(hrow1, 26, hrow1, 29,
                          # 'HERITAGE VS ENVIRONMENTAL REQUIREMENTS',
                          # fmts['ctr_turquoise_bold_12'])
    # worksheet.merge_range(hrow1, 33, hrow1, 39,
                          # 'HERITAGE SUMMARY',
                          # fmts['ctr_turquoise_bold_12'])
    # worksheet.merge_range(hrow1, 42, hrow1, 47,
                          # 'PRICE COST MODELING DATA',
                          # fmts['ctr_green_bold_12'])
    # # # Second row of headers (hrow2)
    # # # Set height to accomodate wrapped column heading text
    # worksheet.set_row(hrow2, 12*8)
    # worksheet.write(hrow2, 0, "", fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 1, "Subassembly/Component",
                    # fmts['left_pale_blue_12'])
    # worksheet.write(hrow2, 2, 'Unit Mass\n[kg]\n(CBE)',
                    # fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 3, 'Cold\nUnits', fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 4, 'Hot\nUnits', fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 5, 'Flight\nUnits', fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 6, 'Flight\nSpares', fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 7, 'EM\nPrototype', fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 8, 'Total Mass\n[kg] (CBE)',
                    # fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 9, 'Contingency\n[%]', fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 10, 'Total Mass\n[kg] with\nContingency\n(MEV)',
                    # fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 11, 'Unit\nPower [W]\n(CBE)',
                    # fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 12, 'Total\nPower [W]\n(CBE)',
                    # fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 13, 'Contingency\n(%)', fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 14, 'Total\nPower [W]\nwith\nContingency\n(MEV)',
                    # fmts['ctr_pale_blue_12'])
    # worksheet.write(hrow2, 15, 'Unit\nPower [W]\n(CBE)', fmts['ctr_gray_12'])
    # worksheet.write(hrow2, 16, 'Total\nPower [W]\n(CBE)', fmts['ctr_gray_12'])
    # worksheet.write(hrow2, 17, 'Contingency\n(%)', fmts['ctr_gray_12'])
    # worksheet.write(hrow2, 18, 'Total\nPower [W]\nwith\nContingency\n(MEV)',
                    # fmts['ctr_gray_12'])
    # worksheet.write(hrow2, 19, 'Total Power\n[W] (CBE)', fmts['ctr_gray_12'])
    # worksheet.merge_range(hrow1, 20, hrow2, 20, 'Quoted\nUnit\nPrice\n($K)',
                          # fmts['ctr_pale_blue_12'])
    # worksheet.merge_range(hrow1, 21, hrow2, 21, 'Composition',
                          # fmts['ctr_pale_blue_12'])
    # text = """(As applicable:
    # Vendor, make, model, part #,
    # volume, quote information,
    # notation of identical items,
    # instrument / component
    # characteristics, ETU approach...)"""
    # worksheet.write(hrow2, 22, text, fmts['ctr_pale_blue_12'])
    # trl_text = """TECHNOLOGY
    # READINESS
    # LEVEL
    # (TRL)
    # """
    # worksheet.merge_range(hrow1, 23, hrow2, 23, trl_text,
                       # fmts['ctr_periwinkle_bold_12'])
    # vendor_maturity_text = "VENDOR\nMATURITY\nDESCRIPTION"
    # worksheet.merge_range(hrow1, 24, hrow2, 24, vendor_maturity_text,
                                            # fmts['turquoise_bold_12_rotated'])
    # worksheet.merge_range(hrow1, 25, hrow2, 25, 'LOCATION',
                                            # fmts['ctr_turquoise_bold_12'])
    # worksheet.write(hrow2, 26, 'Temperature\n-X to Y',
                 # fmts['ctr_turquoise_12'])
    # worksheet.write(hrow2, 27, 'Pressure\nX to Y [mPa]',
                 # fmts['ctr_turquoise_12'])
    # worksheet.write(hrow2, 28, 'Entry Load\n< X [G]', fmts['ctr_turquoise_12'])
    # worksheet.write(hrow2, 29, 'Radiation\nTID\n< X [krad-Si]',
                 # fmts['ctr_turquoise_12'])
    # worksheet.merge_range(hrow1, 30, hrow2, 30,
                       # 'NEW TECHNOLOGY\nOR\nENGNRG CHANGE?',
                       # fmts['turquoise_bold_12_rotated'])
    # worksheet.merge_range(hrow1, 31, hrow2, 31, 'OWNERSHIP?',
                       # fmts['turquoise_bold_12_rotated'])
    # worksheet.merge_range(hrow1, 32, hrow2, 32, 'PERFORMANCE\nCHANGE?',
                       # fmts['turquoise_bold_12_rotated'])
    # worksheet.write(hrow2, 33, 'DESIGN', fmts['turquoise_bold_12_rotated'])
    # worksheet.write(hrow2, 34, 'MANUFACTURE',
                    # fmts['turquoise_bold_12_rotated'])
    # worksheet.write(hrow2, 35, 'SOFTWARE', fmts['turquoise_bold_12_rotated'])
    # worksheet.write(hrow2, 36, 'PROVIDER', fmts['turquoise_bold_12_rotated'])
    # worksheet.write(hrow2, 37, 'USE', fmts['turquoise_bold_12_rotated'])
    # worksheet.write(hrow2, 38, 'OPERATING\nENVIRONMENT',
                    # fmts['turquoise_bold_12_rotated'])
    # worksheet.write(hrow2, 39, 'PRIOR USE', fmts['turquoise_bold_12_rotated'])
    # worksheet.merge_range(hrow1, 40, hrow2, 40, 'REFERENCE\nMISSION(S)',
                          # fmts['turquoise_bold_12_rotated'])
    # worksheet.merge_range(hrow1, 41, hrow2, 41,
                   # 'HERITAGE JUSTIFICATION and ADDITIONAL INFORMATION',
                   # fmts['ctr_turquoise_bold_12'])
    # worksheet.write(hrow2, 42, 'Structure\nMass [kg]', fmts['ctr_green_12'])
    # worksheet.write(hrow2, 43, 'Electronic\nComplexity\nFactor',
                                                # fmts['ctr_green_12'])
    # worksheet.write(hrow2, 44, 'Structure\nComplexity\nFactor',
                                                # fmts['ctr_green_12'])
    # worksheet.write(hrow2, 45, 'Electronic\nRemaining\nDesign\n(1.00 = 100%)',
                                                # fmts['ctr_green_12'])
    # worksheet.write(hrow2, 46, 'Structure\nRemaining\nDesign\n(1.00 = 100%)',
                                                # fmts['ctr_green_12'])
    # worksheet.write(hrow2, 47,
                 # 'Engineering\nComplexity\nMod. Level\n(Simple,\nNew)',
                 # fmts['ctr_green_12'])
    # # # Third row of headers (hrow3)
    # worksheet.write(hrow3, 1, "TOTAL FLIGHT HARDWARE",
                    # fmts['left_pale_blue_bold_12'])
    # level_fmts = {1: fmts['ctr_black_bg_12'],
                  # 2: fmts['ctr_gray_bold_12'],
                  # 3: fmts['ctr_12']
                  # }
    # name_fmts = {1: fmts['left_black_bg_12'],
                 # 2: fmts['left_gray_bold_12'],
                 # 3: fmts['left_12']
                 # }
    # data_fmts = {1: fmts['right_black_bg_12'],
                 # 2: fmts['right_gray_bold_12'],
                 # 3: fmts['right_12']
                 # }
    # for fmt in data_fmts.values():
        # fmt.set_num_format('#,##0.00')

    # system level
    # (note that system.name overwrites the template "NAME..." placeholder)
    if is_project:
        # context is Project, so may include several systems
        project = context
        # HEADER
        # mel_label = 'MISSION: {}'.format(project.id)
        # worksheet.write(hrow1, 1, mel_label, fmts['left_pale_blue_bold_12'])
        start_row = hrow3
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
        get_components_parms(mel, 1, hrow3, system)

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

