# -*- coding: utf-8 -*-
"""
Pan Galactic Report Writer
"""
import xlsxwriter

from pangalactic.core              import orb, prefs
from pangalactic.core.meta         import MAIN_VIEWS
from pangalactic.core.names        import (get_mel_item_name, pname_to_header,
                                           STD_VIEWS)
from pangalactic.core.parametrics  import (componentz, systemz,
                                           get_modal_context,
                                           get_modal_power,
                                           get_pval, get_dval, de_defz,
                                           parm_defz, round_to)
from pangalactic.core.units        import in_si
from pangalactic.core.utils.styles import xlsx_styles


def product_type_report(output=None):
    """
    Report on the current Product Types in the database and which Disciplnes
    they are related to.

    Keyword args:
        output (str):  format of output
            default: None
            valid choices: 'tsv', 'xlsx'
    """
    # product_types = orb.get_by_type('ProductType')
    disciplines = orb.get_by_type('Discipline')
    d_by_name = {d.name : d for d in disciplines}
    d_names = list(d_by_name.keys())
    d_names.sort()
    headers = ['Discipline', 'Product Type', 'Abbrev', 'Description']
    records = []
    for d_name in d_names:
        discipline = d_by_name[d_name]
        dpts = discipline.relevant_product_types
        if dpts:
            records.append([discipline.name, '', '', ''])
            for dpt in dpts:
                pt = dpt.relevant_product_type
                records.append(['', pt.name,
                                pt.abbreviation or '',
                                pt.description or ''])
    if output == 'tsv':
        f = open('product_types.tsv', 'w')
        f.writelines(['\t'.join([cell for cell in line])
                     for line in (headers + records)])
    elif output == 'xlsx':
        workbook = xlsxwriter.Workbook('product_types.xlsx')
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})
        cell_widths = []
        for col in range(len(headers)):
            cell_widths.append([len(rec[col]) for rec in headers + records])
        col_widths = [max(widths) for widths in cell_widths]
        # print('col_widths = {}'.format(str(col_widths)))
        for i, width in enumerate(col_widths):
            worksheet.set_column(i, i, width)
        worksheet.write('A1', 'Discipline', bold)
        worksheet.write('B1', 'Product Type', bold)
        worksheet.write('C1', 'Abbrev', bold)
        worksheet.write('D1', 'Description', bold)
        row = 1
        for i, rec in enumerate(records):
            for j, val in enumerate(rec):
                worksheet.write(row + i, j, val)
        workbook.close()
    return headers + records


def fix_ctgcy(ctgcy):
    # string form of contingency may "explode"; if so, truncate
    if len(str(ctgcy)) > 3:
        ctgcy = ctgcy[0:4]
    # Excel doesn't like space between the number and "%"
    return ctgcy + '%'


def write_mel_xlsx_from_model(context, is_project=True,
                              file_path='mel_writer_output.xlsx'):
    """
    Output a Master Equipment List (MEL) in "summary" format directly from a
    system model.

    Args:
        context (Project or Product):  the project or system of which this is
            the MEL

    Keyword Args:
        is_project (bool):  flag indicating whether context is a Product or
            Project
        file_path (str):  path to report file
    """
    orb.log.info('* write_mel_xlsx_from_model()')
    orb.log.info(f'  - creating Excel workbook file "{file_path}" ...')
    book = xlsxwriter.Workbook(file_path)
    worksheet = book.add_worksheet()
    # xlsxwriter specifies widths in "characters" (as does Excel)
    col_widths = 42 * [8]
    col_widths[0] = 10    # Level
    col_widths[1] = 60    # System/Subsystem Name
    col_widths[2] = 8     # UNIT MASS
    col_widths[3] = 6     # Cold Units       [# of Units]
    col_widths[4] = 6     # Hot Units        [# of Units]
    col_widths[5] = 6     # Flight Units     [# of Units]
    col_widths[6] = 6     # Flight Spares    [# of Units]
    col_widths[7] = 6     # ETU/Qual Units   [# of Units]
    col_widths[8] = 9     # EM/EDU Prototype [# of Units]
    col_widths[9] = 9     # Total Mass [kg] (CBE)
    col_widths[10] = 14   # Mass Contingency [%]
    col_widths[11] = 14   # Total Mass w/ Contingency (MEV)
    col_widths[12] = 12   # Nominal Unit Power (W)
    col_widths[13] = 12   # Nominal Total Power (W)
    col_widths[14] = 14   # Nominal Power Contingency [%]
    col_widths[15] = 14   # Nominal Total Power w/ Contingency (MEV)
    col_widths[16] = 12   # Peak Unit Power (W)
    col_widths[17] = 12   # Peak Total Power (W)
    col_widths[18] = 14   # Peak Power Contingency [%]
    col_widths[19] = 14   # Peak Total Power w/ Contingency (MEV)
    col_widths[20] = 16   # QUIESCENT Total Power [W] (CBE)
    col_widths[21] = 12   # Quoted Unit Price ($)
    col_widths[22] = 24   # Composition
    col_widths[23] = 40   # ADDITIONAL INFORMATION
    col_widths[24] = 18   # TRL
    col_widths[25] = 20   # Similarity to Existing
    col_widths[26] = 20   # Design        [Heritage Summary]
    col_widths[27] = 20   # Manufacture   [Heritage Summary]
    col_widths[28] = 20   # Software      [Heritage Summary]
    col_widths[29] = 20   # Provider      [Heritage Summary]
    col_widths[30] = 20   # Use           [Heritage Summary]
    col_widths[31] = 20   # Operating Env [Heritage Summary]
    col_widths[32] = 20   # Ref Prior Use [Heritage Summary]
    col_widths[33] = 20   # Reference Mission(s)
    col_widths[34] = 120  # Heritage Justification and Additional Information
    col_widths[35] = 20   # Structure Mass (kg)               [COST MODELING DATA]
    col_widths[36] = 20   # Electronic Complexity Factor      [COST MODELING DATA]
    col_widths[37] = 20   # Structure Complexity Factor       [COST MODELING DATA]
    col_widths[38] = 20   # Electronic Remaining Design       [COST MODELING DATA]
    col_widths[39] = 20   # Structure Remaining Design        [COST MODELING DATA]
    col_widths[40] = 20   # Engineering Complexity Mod. Level [COST MODELING DATA]
    col_widths[41] = 10   # [Add columns to the right if needed]

    orb.log.info('  - writing formatted column headers ...')
    for i, width in enumerate(col_widths):
        worksheet.set_column(i, i, width)

    fmts = {name : book.add_format(style)
            for name, style in xlsx_styles.items()}

    # Set position of title
    title_row = 0
    # Set relative positions of header rows
    hrow1 = title_row + 1
    hrow2 = hrow1 + 1
    hrow3 = hrow2 + 1

    # Title (row 0)
    # set title row height to 12*2
    worksheet.set_row(title_row, 12*2)
    worksheet.merge_range(title_row, 0, title_row, 47,
                          '  MASTER EQUIPMENT LIST (MEL)',
                          fmts['black_bg_18'])

    # First row of headers (hrow1)
    # worksheet.row(hrow1).height_mismatch = True
    worksheet.set_row(hrow1, 12*3)
    worksheet.write(hrow1, 0, 'LEVEL', fmts['ctr_pale_blue_bold_12'])
    worksheet.write(hrow1, 1, 'NAME (Mission or Payload Name)',
                                        fmts['ctr_pale_blue_bold_12'])
    worksheet.write(hrow1, 2, 'UNIT\nMASS', fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 3, hrow1, 8, '# OF UNITS',
                          fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 9, hrow1, 11, 'FLIGHT HARDWARE MASS',
                          fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 12, hrow1, 15,
                          'NOMINAL FLIGHT HARDWARE POWER',
                          fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 16, hrow1, 19,
                          'PEAK FLIGHT HARDWARE POWER',
                          fmts['ctr_gray_bold_12'])
    worksheet.write(hrow1, 20, 'QUIESCENT', fmts['ctr_gray_bold_12'])
    worksheet.write(hrow1, 23, 'ADDITIONAL INFORMATION',
                    fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 26, hrow1, 32,
                          'HERITAGE SUMMARY',
                          fmts['ctr_light_steel_blue_bold_12'])
    worksheet.merge_range(hrow1, 35, hrow1, 40,
                          'PRICE COST MODELING DATA',
                          fmts['ctr_green_bold_12'])

    # Second row of headers (hrow2)
    # Set height to accomodate wrapped column heading text
    worksheet.set_row(hrow2, 12*8)
    worksheet.write(hrow2, 0, "", fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 1, "Subassembly / Component",
                    fmts['left_pale_blue_12'])
    worksheet.write(hrow2, 2, 'Unit Mass\n[kg]\n(CBE)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 3, 'Cold\nUnits', fmts['ctr_gray_12'])
    worksheet.write(hrow2, 4, 'Hot\nUnits', fmts['ctr_gray_12'])
    worksheet.write(hrow2, 5, 'Flight\nUnits', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 6, 'Flight\nSpares', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 7, 'ETU /\nQual\nUnit', fmts['ctr_gray_12'])
    worksheet.write(hrow2, 8, 'EM /\nEDU /\nProto-\ntype',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 9, 'Total Mass\n[kg] (CBE)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 10, 'Contingency\n[%]', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 11, 'Total Mass\n[kg] with\nContingency\n(MEV)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 12, 'Unit\nPower [W]\n(CBE)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 13, 'Total\nPower [W]\n(CBE)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 14, 'Contingency\n(%)', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 15, 'Total\nPower [W]\nwith\nContingency\n(MEV)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 16, 'Unit\nPower [W]\n(CBE)', fmts['ctr_gray_12'])
    worksheet.write(hrow2, 17, 'Total\nPower [W]\n(CBE)', fmts['ctr_gray_12'])
    worksheet.write(hrow2, 18, 'Contingency\n(%)', fmts['ctr_gray_12'])
    worksheet.write(hrow2, 19, 'Total\nPower [W]\nwith\nContingency\n(MEV)',
                    fmts['ctr_gray_12'])
    worksheet.write(hrow2, 20, 'Total Power\n[W] (CBE)', fmts['ctr_gray_12'])
    worksheet.merge_range(hrow1, 21, hrow2, 21, 'Quoted\nUnit\nPrice\n($)',
                          fmts['ctr_pale_blue_12'])
    worksheet.merge_range(hrow1, 22, hrow2, 22, 'Composition',
                          fmts['ctr_pale_blue_12'])
    text = """(As applicable:
    Vendor, make, model, part #,
    volume, quote information,
    notation of identical items,
    instrument / component
    characteristics, ETU approach...)"""
    worksheet.write(hrow2, 23, text, fmts['ctr_pale_blue_12'])
    trl_text = """TECHNOLOGY
    READINESS
    LEVEL

    TRL
    """
    worksheet.merge_range(hrow1, 24, hrow2, 24, trl_text,
                       fmts['ctr_periwinkle_bold_12'])
    similarity_text = "SIMILARITY TO\nEXISTING"
    worksheet.merge_range(hrow1, 25, hrow2, 25, similarity_text,
                                            fmts['light_steel_blue_bold_12_rotated'])
    worksheet.write(hrow2, 26, 'DESIGN', fmts['light_steel_blue_bold_10_rotated'])
    worksheet.write(hrow2, 27, 'MANUFACTURE',
                    fmts['light_steel_blue_bold_10_rotated'])
    worksheet.write(hrow2, 28, 'SOFTWARE', fmts['light_steel_blue_bold_10_rotated'])
    worksheet.write(hrow2, 29, 'PROVIDER', fmts['light_steel_blue_bold_10_rotated'])
    worksheet.write(hrow2, 30, 'USE', fmts['light_steel_blue_bold_10_rotated'])
    worksheet.write(hrow2, 31, 'OPERATING ENV',
                    fmts['light_steel_blue_bold_10_rotated'])
    worksheet.write(hrow2, 32, 'REF PRIOR USE',
                    fmts['light_steel_blue_bold_10_rotated'])
    worksheet.merge_range(hrow1, 33, hrow2, 33, 'REFERENCE\nMISSION(S)',
                          fmts['light_steel_blue_bold_12_rotated'])
    worksheet.merge_range(hrow1, 34, hrow2, 34,
                   'HERITAGE JUSTIFICATION and ADDITIONAL INFORMATION',
                   fmts['ctr_light_steel_blue_bold_12'])
    worksheet.write(hrow2, 35, 'Structure\nMass (kg)', fmts['ctr_green_12'])
    worksheet.write(hrow2, 36, 'Electronic\nComplexity\nFactor',
                                                fmts['ctr_green_12'])
    worksheet.write(hrow2, 37, 'Structure\nComplexity\nFactor',
                                                fmts['ctr_green_12'])
    worksheet.write(hrow2, 38, 'Electronic\nRemaining\nDesign\n(1.00 = 100%)',
                                                fmts['ctr_green_12'])
    worksheet.write(hrow2, 39, 'Structure\nRemaining\nDesign\n(1.00 = 100%)',
                                                fmts['ctr_green_12'])
    worksheet.write(hrow2, 40,
                 'Engineering\nComplexity\nMod. Level\n(Simple,\nNew)',
                 fmts['ctr_green_12'])

    # Third row of headers (hrow3)
    worksheet.write(hrow3, 1, "TOTAL FLIGHT HARDWARE",
                    fmts['left_pale_blue_bold_12'])
    worksheet.write(hrow3, 35, "WS",
                    fmts['ctr_green_bold_12'])
    worksheet.write(hrow3, 36, "MCPLXE",
                    fmts['ctr_green_bold_12'])
    worksheet.write(hrow3, 37, "MCPLXS",
                    fmts['ctr_green_bold_12'])
    worksheet.write(hrow3, 38, "NEWST",
                    fmts['ctr_green_bold_12'])
    worksheet.write(hrow3, 39, "NEWST",
                    fmts['ctr_green_bold_12'])
    worksheet.write(hrow3, 40, "ECMPLX",
                    fmts['ctr_green_bold_12'])

    level_fmts = {1: fmts['ctr_black_bg_12'],
                  2: fmts['ctr_gray_bold_12'],
                  3: fmts['ctr_12']
                  }
    name_fmts = {1: fmts['left_black_bg_12'],
                 2: fmts['left_gray_bold_12'],
                 3: fmts['left_12']
                 }
    data_fmts = {1: fmts['float_right_black_bg_12'],
                 2: fmts['float_right_gray_bold_12'],
                 3: fmts['float_right_12']
                 }
    int_fmts = {1: fmts['int_right_black_bg_12'],
                2: fmts['int_right_gray_bold_12'],
                3: fmts['int_right_12']
                }
    txt_fmts = {1: fmts['txt_left_black_bg_12'],
                2: fmts['txt_left_gray_bold_12'],
                3: fmts['txt_left_12']
                }
    # system level
    # (note that system.name overwrites the template "NAME..." placeholder)
    if is_project:
        # context is Project, so may include several systems
        project = context
        mel_label = 'MISSION: {}'.format(project.id)
        worksheet.write(hrow1, 1, mel_label, fmts['left_pale_blue_bold_12'])
        start_row = hrow3
        psus = [orb.get(s.usage_oid) for s in systemz.get(project.oid, [])]
        system_names = [psu.system.name.lower() for psu in psus]
        system_names.sort()
        system_by_name = {psu.system.name.lower() : psu.system
                          for psu in psus}
        for system_name in system_names:
            last_row = write_component_rows_xlsx(worksheet, level_fmts,
                                                 name_fmts, data_fmts,
                                                 int_fmts, txt_fmts, 1,
                                                 start_row,
                                                 system_by_name[system_name])
            start_row = last_row + 1
    else:
        # context is Product -> a single system MEL
        system = context
        worksheet.write(hrow1, 1, system.name, fmts['left_pale_blue_bold_12'])
        write_component_rows_xlsx(worksheet, level_fmts, name_fmts, data_fmts,
                                  int_fmts, txt_fmts, 1, hrow3, system)
    book.close()


def write_component_rows_xlsx(sheet, level_fmts, name_fmts, data_fmts,
                              int_fmts, txt_fmts, level, row, component,
                              qty=1):
    """
    Write a row in the MEL for a component in the system model.

    Args:
        sheet (xlsx worksheet):  current worksheet instance
        level_fmts (dict):  formats for each level
        name_fmts (dict):  formats for cells in the "name" column
        data_fmts (dict):  formats for cells with float values
        int_fmts (dict):  formats for cells with integer values
        txt_fmts (dict):  formats for cells with str or text values
        level (int):  level of the current component
        row (int):  current row to write into the worksheet
        component (Product):  the product mapped to the current row

    Keyword Args:
        qty (int):  the number of instances of the component (Product instance)
            in the assembly
    """
    mcbe = get_pval(component.oid, 'm[CBE]')
    ctgcy_m = fix_ctgcy(str(100 * get_pval(component.oid, 'm[Ctgcy]')))
    # print(f' * ctgcy_m: {ctgcy_m}')
    mmev = get_pval(component.oid, 'm[MEV]')
    pcbe = get_pval(component.oid, 'P[CBE]')
    # Excel doesn't like space between the number and "%"
    ctgcy_P = fix_ctgcy(str(100 * get_pval(component.oid, 'P[Ctgcy]')))
    pmev = get_pval(component.oid, 'P[MEV]')
    cost = get_pval(component.oid, 'Cost')  # Quoted Unit Price
    vendor = get_dval(component.oid, 'Vendor')  # Vendor (-> Addl. Info.)
    # -------------------------------------------
    # columns
    # -------------------------------------------
    #  0: 'assembly_level'
    #  1: 'system_name'
    #  2: 'm_unit'
    #  3: 'cold_units'
    #  4: 'hot_units'
    #  5: 'flight_units'
    #  6: 'flight_spares'
    #  7: 'etu_qual_units'
    #  8: 'em_edu_prototype_units'
    #  9: 'm_cbe'
    # 10: 'm_ctgcy'
    # 11: 'm_mev'
    # 12: 'nom_p_unit_cbe'
    # 13: 'nom_p_cbe'
    # 14: 'nom_p_ctgcy'
    # 15: 'nom_p_mev'
    # 16: 'peak_p_unit_cbe'
    # 17: 'peak_p_cbe'
    # 18: 'peak_p_ctgcy'
    # 19: 'peak_p_mev'
    # 20: 'quiescent_p_cbe'
    # 21: 'quoted_unit_price'
    # 22: 'composition'
    # 23: 'additional_information'
    # 24: 'TRL'
    # 25: 'similarity'
    # 26: 'heritage_design'
    # 27: 'heritage_mfr'
    # 28: 'heritage_software'
    # 29: 'heritage_provider'
    # 30: 'heritage_use'
    # 31: 'heritage_op_env'
    # 32: 'heritage_prior_use'
    # 33: 'reference_missions'
    # 34: 'heritage_justification'
    # 35: 'cost_structure_mass'
    # 36: 'cost_electronic_complexity'
    # 37: 'cost_structure_complexity'
    # 38: 'cost_electronic_remaining_design'
    # 39: 'cost_structure_remaining_design'
    # 40: 'cost_engineering_complexity_mod_level'
    # -------------------------------------------
    mel_columns = [
        'assembly_level',
        'system_name',
        'm_unit',
        'cold_units',
        'hot_units',
        'flight_units',
        'flight_spares',
        'etu_qual_units',
        'em_edu_prototype_units',
        'm_cbe',
        'm_ctgcy',
        'm_mev',
        'nom_p_unit_cbe',
        'nom_p_cbe',
        'nom_p_ctgcy',
        'nom_p_mev',
        'peak_p_unit_cbe',
        'peak_p_cbe',
        'peak_p_ctgcy',
        'peak_p_mev',
        'quiescent_p_cbe',
        'quoted_unit_price',
        'composition',
        'additional_information',
        'TRL',
        'similarity',
        'heritage_design',
        'heritage_mfr',
        'heritage_software',
        'heritage_provider',
        'heritage_use',
        'heritage_op_env',
        'heritage_prior_use',
        'reference_missions',
        'heritage_justification',
        'cost_structure_mass',
        'cost_electronic_complexity',
        'cost_structure_complexity',
        'cost_electronic_remaining_design',
        'cost_structure_remaining_design',
        'cost_engineering_complexity_mod_level'
        ]
    row += 1
    # print('writing {} in row {}'.format(component.name, row))
    # first write the formatting to the whole row to set the bg color
    sheet.write_row(row, 0, [' ']*48, level_fmts.get(level, level_fmts[3]))
    # then write the "LEVEL" cell
    sheet.write(row, 0, level, level_fmts.get(level, level_fmts[3]))
    # level-based indentation
    spaces = '   ' * level
    sheet.write(row, 1, spaces + component.name,
                name_fmts.get(level, name_fmts[3]))
    data_fmt = data_fmts.get(level, data_fmts[3])
    int_fmt = int_fmts.get(level, int_fmts[3])
    txt_fmt = txt_fmts.get(level, txt_fmts[3])
    txt_fmt.set_text_wrap()
    sheet.write(row, 2, mcbe, data_fmt)        # Unit Mass
    sheet.write(row, 5, qty, int_fmt)          # Flight Units
    sheet.write(row, 9, mcbe * qty, data_fmt)  # Total Mass
    sheet.write(row, 10, ctgcy_m, data_fmt)
    sheet.write(row, 11, mmev * qty, data_fmt) # Mass MEV
    sheet.write(row, 12, pcbe, data_fmt)       # Unit Power
    sheet.write(row, 13, pcbe * qty, data_fmt) # Total Power
    sheet.write(row, 14, ctgcy_P, data_fmt)
    sheet.write(row, 15, pmev * qty, data_fmt) # Power MEV
    sheet.write(row, 21, cost, data_fmt)       # Quoted Unit Price
    sheet.write(row, 23, vendor, txt_fmt)        # Vendor (Addl. Info)
    predefined_cols = [1,2,5,9,10,11,12,13,14,15,21,23]
    dt_map = {'float': data_fmt,
              'int': int_fmt,
              'str': txt_fmt,
              'text': txt_fmt}
    for i, col_id in enumerate(mel_columns):
        val = get_dval(component.oid, col_id)
        if val and i not in predefined_cols:
            dtype = (de_defz.get(col_id) or {}).get('range_datatype')
            sheet.write(row, i, val, dt_map.get(dtype, txt_fmt))
    real_comps = []
    component_acus = [orb.get(comp.usage_oid)
                      for comp in componentz.get(component.oid, [])
                      if orb.get(comp.usage_oid) is not None]
    if component_acus:
        real_comps = [acu for acu in component_acus
                      if hasattr(acu.component, 'oid') and
                      acu.component.oid != 'pgefobjects:TBD']
    if real_comps:
        next_level = level + 1
        product_oids = set([acu.component.oid for acu in real_comps])
        if len(product_oids) < len(real_comps):
            # this means a product is a component in more than one acu, so we
            # need to iterate over unique product instances, and quantities
            # must be computed
            products = orb.get(oids=product_oids)
            comp_names = [product.name.lower() for product in products]
            comp_names.sort()
            comps_by_name = {product.name.lower() : product
                             for product in products}
            qty_by_name = {}
            for acu in real_comps:
                if qty_by_name.get(acu.component.name.lower()):
                    qty_by_name[acu.component.name.lower()] += (
                                                            acu.quantity or 1)
                else:
                    qty_by_name[acu.component.name.lower()] = (
                                                            acu.quantity or 1)
        else:
            comp_names = [acu.component.name.lower()
                          for acu in real_comps]
            comp_names.sort()
            comps_by_name = {acu.component.name.lower() : acu.component
                             for acu in real_comps}
            qty_by_name = {acu.component.name.lower() : acu.quantity or 1
                           for acu in real_comps}
        for comp_name in comp_names:
            row = write_component_rows_xlsx(sheet, level_fmts, name_fmts,
                                            data_fmts, int_fmts, txt_fmts,
                                            next_level, row,
                                            comps_by_name[comp_name],
                                            qty=qty_by_name[comp_name])
    return row


def get_mel_data(root, schema=None, summary=False):
    """
    Generate a customized Master Equipment List (MEL) as a list of dicts.

    Args:
        root (Project or Product):  the project or system of which this is
            the MEL

    Keyword Args:
        schema (list of str):  ids of the parameters and data elements to be
            included
        summary (bool):  if True, combine all instances of a product in a given
            asssembly into one line item with a computed quantity; otherwise,
            tag each usage with its reference designator
    """
    root_id = getattr(root, 'id', None) or '[unknown id]'
    orb.log.debug(f'* getting Mini MEL data for {root_id} ...')
    data = []
    cols = []
    std_headers = ['system_name', 'ID', 'level', 'qty']
    if schema and isinstance(schema, list):
        cols = std_headers + schema
    else:
        cols = std_headers
        schema = []
    if isinstance(root, orb.classes['Project']):
        # root is Project, so may include several systems
        project = root
        item_names = [get_mel_item_name(psu) for psu in project.systems]
        item_names.sort()
        iname_to_psu = {get_mel_item_name(psu) : psu for psu in project.systems}
        for item_name in item_names:
            data += get_item_data(iname_to_psu[item_name], cols, schema, 1,
                                  summary=summary)
    elif isinstance(root, orb.classes['HardwareProduct']):
        # root is Product -> single system MEL
        system = root
        data += get_item_data(system, cols, schema, 1, summary=summary)
    else:
        orb.log.info('  - root is neither a Project nor Product ...')
        orb.log.info('    could not write MEL, quitting.')
        return []
    return data


def get_item_data(item, cols, schema, level, summary=False, qty=1):
    """
    Recursively return a lists of dicts containing the parameter and data
    element data for MEL items of an assembly.

    Args:
        item (Acu, ProjectSystemUsage, or HardwareProduct): item is an Acu
            or a ProjectSystemUsage unless it is the "root" of the MEL, in
            which case it is a HardwareProduct
        cols (list of str):  columns in the MEL (of which schema is a subset)
        schema (list of str):  ids of the parameters and data elements to be
            included
        level (int): assembly level of item

    Keyword Args:
        summary (bool):  if True, combine all instances of a product in a given
            asssembly into one line item with a computed quantity; otherwise,
            show a line item for each usage, tagged with its reference
            designator
        qty (int):  quantity of the item (used for summary)
    """
    # orb.log.debug('* get_item_data()')
    # item_id = getattr(item, 'id', 'unknown') or 'no id'
    # item_oid = getattr(item, 'oid', 'unknown') or 'no oid'
    # orb.log.debug(f'  - item: {item_id} ({item_oid})')
    # NB:  levels are 1-based
    if not item:
        return []
    if isinstance(item, orb.classes['HardwareProduct']):
        # orb.log.debug('  - item is a HardwareProduct')
        if not summary:
            # if not summary, the item being a Product instance implies that
            # it's the "root" item, so level and qty are 1
            level = 1
            qty = 1
        component = item
        comp_name = (getattr(item, 'name', '') or 'Unknown').replace(
                                                        '\n', ' ').strip()
        comp_name = (level - 1) * '  ' + comp_name
    else:
        # Acu or ProjectSystemUsage
        if hasattr(item, 'component'):
            # Acu
            # orb.log.debug('  - item is an Acu')
            component = item.component
            qty = item.quantity or 1
        else:
            # ProjectSystemUsage
            # orb.log.debug('  - item is a PSU')
            component = item.system
            qty = 1
        comp_name = (level - 1) * '  ' + get_mel_item_name(item)
    # orb.log.debug(f'  - "component" is {component}')
    data = []
    vals = []
    for col_id in schema:
        # TODO: predetermine whether each schema element is a pid or deid
        # Excel doesn't like space between the number and "%" --
        # hence, fix_ctgcy() ...
        if col_id in parm_defz:
            # it's a parameter ...
            if 'Ctgcy' in col_id:
                pval = fix_ctgcy(str(100 * get_pval(component.oid, col_id)))
            else:
                # get all values in user's preferred units
                pd = parm_defz.get(col_id)
                units = prefs['units'].get(pd['dimensions'], '') or in_si.get(
                                                        pd['dimensions'], '')
                pval = str(round_to(get_pval(
                                        component.oid, col_id, units=units)))
            vals.append(pval)
        elif col_id in de_defz:
            # it's a data_element ...
            dval = str(get_dval(component.oid, col_id))
            vals.append(dval)
        else:
            # neither a parameter nor data element
            vals.append('-')
    comp_id = component.id
    data.append(dict(zip(cols, [comp_name, comp_id, str(level), str(qty)]
                                + vals)))
    # orb.log.debug(f'getting "{comp_name}" at level {str(level)}')
    if component.oid in componentz:
        next_level = level + 1
        if summary:
            products_by_oid = {comp.oid : orb.get(comp.oid)
                               for comp in componentz[component.oid]
                               if comp.oid != 'pgefobjects:TBD'}
            qty_by_oid = {}
            acus = [orb.get(c.usage_oid) for c in componentz[component.oid]
                    if orb.get(c.usage_oid) is not None]
            for acu in acus:
                oid = acu.component.oid
                if qty_by_oid.get(oid):
                    qty_by_oid[oid] += acu.quantity or 1
                else:
                    qty_by_oid[oid] = acu.quantity or 1
            for oid in products_by_oid:
                data += get_item_data(products_by_oid[oid], cols,
                                      schema, next_level, qty=qty_by_oid[oid],
                                      summary=True)
        else:
            acus = [orb.get(c.usage_oid) for c in componentz[component.oid]]
            item_names = [get_mel_item_name(acu)
                          for acu in acus]
            item_names.sort()
            acus_by_item_name = {get_mel_item_name(acu) : acu
                                 for acu in acus}
            for item_name in item_names:
                data += get_item_data(acus_by_item_name[item_name], cols,
                                      schema, next_level)
    return data


def get_contextual_mel_data(context, root, schema=None, summary=False):
    """
    Generate a Master Equipment List (MEL) that contains "contextual" data that
    includes "prescriptive" parametric data such as parametric constraints from
    performance requirements, which are only meaningful in the context of a
    "usage" -- i.e. either an assembly or a project.

    Args:
        context (ProjectSystemUsage or Acu):  the "usage" that provides the
            conntext for any prescriptive parameters that may be included
        root (Project or Product):  the project or system of which this is
            the MEL

    Keyword Args:
        schema (list of str):  ids of the parameters and data elements to be
            included
        summary (bool):  if True, combine all instances of a product in a given
            asssembly into one line item with a computed quantity; otherwise,
            tag each usage with its reference designator
    """
    context_id = getattr(context, 'id', None) or '[unknown id]'
    root_id = getattr(root, 'id', None) or '[unknown id]'
    orb.log.debug(f'* Mini MEL data in the context of {context_id}')
    orb.log.debug(f'  for the root item {root_id} ...')
    data = []
    cols = []
    std_headers = ['system_name', 'ID', 'level', 'qty']
    if schema and isinstance(schema, list):
        cols = std_headers + schema
    else:
        cols = std_headers
        schema = []
    if isinstance(context, orb.classes['ProjectSystemUsage']):
        # context is ProjectSystemUsage
        project = context
        item_names = [get_mel_item_name(psu) for psu in project.systems]
        item_names.sort()
        iname_to_psu = {get_mel_item_name(psu) : psu for psu in project.systems}
        for item_name in item_names:
            data += get_contextual_item_data(iname_to_psu[item_name], cols,
                                             schema, 1, summary=summary)
    elif isinstance(context, orb.classes['Acu']):
        # context is Acu
        system = context
        data += get_contextual_item_data(system, cols, schema, 1,
                                         summary=summary)
    else:
        orb.log.info('  - context is neither a ProjectSystemUsage nor Acu ...')
        orb.log.info('    could not write MEL, quitting.')
        return []
    return data


def get_contextual_item_data(item, cols, schema, level, summary=False, qty=1):
    """
    Recursively return a lists of dicts containing the parameter and data
    element data for MEL items of an assembly.

    Args:
        item (Acu, ProjectSystemUsage, or HardwareProduct): item is an Acu
            or a ProjectSystemUsage unless it is the "root" of the MEL, in
            which case it is a HardwareProduct
        cols (list of str):  columns in the MEL (of which schema is a subset)
        schema (list of str):  ids of the parameters and data elements to be
            included
        level (int): assembly level of item

    Keyword Args:
        summary (bool):  if True, combine all instances of a product in a given
            asssembly into one line item with a computed quantity; otherwise,
            show a line item for each usage, tagged with its reference
            designator
        qty (int):  quantity of the item (used for summary)
    """
    # NB:  levels are 1-based
    if isinstance(item, orb.classes['Product']):
        if not summary:
            # if not summary, the item being a Product instance implies that
            # it's the "root" item, so level and qty are 1
            level = 1
            qty = 1
        component = item
        comp_name = (getattr(item, 'name', '') or 'Unknown').replace(
                                                        '\n', ' ').strip()
        comp_name = (level - 1) * '  ' + comp_name
    else:
        # Acu or ProjectSystemUsage
        if hasattr(item, 'component'):
            # Acu
            component = item.component
            qty = item.quantity or 1
        else:
            # ProjectSystemUsage
            component = item.system
            qty = 1
        comp_name = (level - 1) * '  ' + get_mel_item_name(item)
    data = []
    vals = []
    for col_id in schema:
        # TODO: predetermine whether each schema element is a pid or deid
        # Excel doesn't like space between the number and "%" --
        # hence, fix_ctgcy() ...
        if col_id in parm_defz:
            # it's a parameter ...
            if 'Ctgcy' in col_id:
                pval = fix_ctgcy(str(100 * get_pval(component.oid, col_id)))
            else:
                # get all values in user's preferred units
                pd = parm_defz.get(col_id)
                units = prefs['units'].get(pd['dimensions'], '') or in_si.get(
                                                        pd['dimensions'], '')
                pval = str(round_to(get_pval(
                                        component.oid, col_id, units=units)))
            vals.append(pval)
        elif col_id in de_defz:
            # it's a data_element ...
            dval = str(get_dval(component.oid, col_id))
            vals.append(dval)
        else:
            # neither a parameter nor data element
            vals.append('-')
    comp_id = component.id
    data.append(dict(zip(cols, [comp_name, comp_id, str(level), str(qty)]
                                + vals)))
    # orb.log.debug(f'getting "{comp_name}" at level {str(level)}')
    if component.components:
        next_level = level + 1
        if summary:
            products_by_oid = {acu.component.oid : acu.component
                               for acu in component.components
                               if acu.component.oid != 'pgefobjects:TBD'}
            qty_by_oid = {}
            for acu in component.components:
                oid = acu.component.oid
                if qty_by_oid.get(oid):
                    qty_by_oid[oid] += acu.quantity or 1
                else:
                    qty_by_oid[oid] = acu.quantity or 1
            for oid in products_by_oid:
                data += get_contextual_item_data(products_by_oid[oid], cols,
                                                 schema, next_level,
                                                 qty=qty_by_oid[oid],
                                                 summary=True)
        else:
            item_names = [get_mel_item_name(acu)
                          for acu in component.components]
            item_names.sort()
            acus_by_item_name = {get_mel_item_name(acu) : acu
                                 for acu in component.components}
            for item_name in item_names:
                data += get_contextual_item_data(acus_by_item_name[item_name],
                                                 cols, schema, next_level)
    return data


def write_mel_to_xlsx(context, schema=None, pref_units=False, summary=False,
                      file_path='dash_data.xlsx'):
    """
    Output a customized Master Equipment List (MEL) report to Excel .xlsx
    format, including system / subsystem / component names and assembly levels,
    with the specified schema (set of parameters, and data elements).

    Args:
        context (Project or Product):  the project or system of which this is
            the MEL

    Keyword Args:
        schema (list of str):  ids of the parameters and data elements to be
            included
        pref_units (bool):  express values in the user's preferred units;
            default is False (use mks units); if True, units will be specified
            in headers
        summary (bool):  if True, combine all instances of a product in a given
            asssembly into one line item with a computed quantity; otherwise,
            tag each usage with its reference designator
        file_path (str):  path to data file
    """
    context_id = getattr(context, 'id', None) or '[unknown id]'
    orb.log.debug(f'* writing Mini MEL data for {context_id} to xlsx ...')
    headers = []
    std_headers = ['System Name', 'ID', 'Level', 'Qty']
    if schema and isinstance(schema, list):
        schema_with_units = []
        for col_id in schema:
            if col_id in parm_defz:
                # it's a parameter ...
                if 'Ctgcy' in col_id:
                    schema_with_units.append(col_id + ' (%)')
                else:
                    pd = parm_defz.get(col_id)
                    if pref_units:
                        units = prefs['units'].get(pd['dimensions'], '')
                        units = units or in_si.get(pd['dimensions'], '')
                    else:
                        units = in_si.get(pd['dimensions'], '')
                    schema_with_units.append(col_id + f' ({units})')
            else:
                schema_with_units.append(col_id)
        headers = std_headers + schema_with_units
    else:
        headers = std_headers
        schema = []
    data = get_mel_data(context, schema, summary=summary)
    book = xlsxwriter.Workbook(file_path)
    worksheet = book.add_worksheet()
    # xlsxwriter specifies widths in "characters" (as does Excel)
    # TODO: set widths more appropriately (look up cols) ...
    col_widths = [80, 30, 7, 5] + (len(headers)-4) * [15]
    for i, width in enumerate(col_widths):
        worksheet.set_column(i, i, width)
    for i, h in enumerate(headers):
        worksheet.write(0, i, h)  # maybe use formatting (4 position)
    for r, d in enumerate(data):
        factor = int(d['level'])
        prefix = '    ' * (factor - 1)
        d['system_name'] = prefix + d['system_name']
        for col, val in enumerate(d.values()):
            worksheet.write(r+1, col, val)
    book.close()


def write_objects_to_xlsx(objs, file_path, view=None, cname='',
                          use_level=False):
    """
    Write a list of objects to .xlsx format.

    Args:
        objs (list of objects):  the objects to be included
        file_path (str): path of file to be written

    Keyword Args:
        view (list of str):  set of attributes, parameters, and data elements
            to write
        cname (str):  class name
        use_level (bool):  whether to use "level" attr to format output
    """
    book = xlsxwriter.Workbook(file_path)
    sheet = book.add_worksheet()
    fmts = {name : book.add_format(style)
            for name, style in xlsx_styles.items()}
    # TODO: figure out how to apply levels to requirements ... for now, ignore
    # if use_level:
        # # first write the formatting to the whole row to set the bg color
        # sheet.write_row(row, 0, [' ']*48, level_fmts.get(level, level_fmts[3]))
        # # then write the "LEVEL" cell
        # sheet.write(row, 0, level, level_fmts.get(level, level_fmts[3]))
        # # level-based indentation
        # spaces = '   ' * level
        # sheet.write(row, 1, spaces + reqt.name,
                    # name_fmts.get(level, name_fmts[3]))
        # data_fmt = data_fmts.get(level, data_fmts[3])
        # int_fmt = int_fmts.get(level, int_fmts[3])
        # txt_fmt = txt_fmts.get(level, txt_fmts[3])
    if objs:
        cname = objs[0].__class__.__name__
    else:
        objs = []
    if not view:
        view = MAIN_VIEWS.get(cname, ['id', 'name', 'description'])
    col_widths = STD_VIEWS.get(cname, {})
    for j, a in enumerate(view):
        sheet.set_column(j, j, col_widths.get(a) or 20)
        header = pname_to_header(a, cname)
        sheet.write(0, j, header, fmts['ctr_black_bg_12'])
    cell_format = book.add_format()
    cell_format.set_text_wrap()
    for i, obj in enumerate(objs):
        # d is a dict with string representations of all values, including
        # values that are objects
        d = orb.obj_view_to_dict(obj, view)
        for j, a in enumerate(view):
            val = d.get(a, '') or ''
            sheet.write(i+1, j, val, cell_format)
    book.close()


def write_data_to_tsv(data, file_path='data.tsv'):
    """
    Output data in "list of dicts" format to a .tsv file.

    Args:
        data (list of dicts):  the data to write to tsv

    Keyword Args:
        file_path (str):  path to data file
    """
    rows = ['\t'.join(data[0].keys())]
    for row in data:
        rows.append('\t'.join(row.values()))
    output = '\n'.join(rows)
    with open(file_path, 'w') as f:
        f.write(output)


def write_mel_to_tsv(context, schema=None, pref_units=False, summary=False,
                     file_path='dash_data.tsv'):
    """
    Output a customized Master Equipment List (MEL) report including system /
    subsystem / component names and assembly levels, with the specified schema
    (set of parameters, and data elements), to a .tsv file.

    Args:
        context (Project or Product):  the project or system of which this is
            the MEL

    Keyword Args:
        schema (list of str):  ids of the parameters and data elements to be
            included
        pref_units (bool):  express values in the user's preferred units;
            default is False (use mks units); if True, units will be specified
            in headers
        summary (bool):  if True, combine all instances of a product in a given
            asssembly into one line item with a computed quantity; otherwise,
            tag each usage with its reference designator
        file_path (str):  path to data file
    """
    context_id = getattr(context, 'id', None) or '[unknown id]'
    orb.log.debug(f'* writing Mini MEL data for {context_id} to tsv ...')
    data = ''
    std_headers = ['System Name', 'ID', 'Level', 'Qty']
    if schema and isinstance(schema, list):
        schema_with_units = []
        for col_id in schema:
            if col_id in parm_defz:
                # it's a parameter ...
                if 'Ctgcy' in col_id:
                    schema_with_units.append(col_id + ' (%)')
                else:
                    pd = parm_defz.get(col_id)
                    if pref_units:
                        units = prefs['units'].get(pd['dimensions'], '')
                        units = units or in_si.get(pd['dimensions'], '')
                    else:
                        units = in_si.get(pd['dimensions'], '')
                    schema_with_units.append(col_id + f' ({units})')
            else:
                schema_with_units.append(col_id)
        data = '\t'.join(std_headers + schema_with_units) + '\n'
    else:
        data = '\t'.join(std_headers) + '\n'
        schema = []
    if isinstance(context, orb.classes['Project']):
        # context is Project, so may include several systems
        project = context
        item_names = [get_mel_item_name(psu) for psu in project.systems]
        item_names.sort()
        iname_to_psu = {get_mel_item_name(psu) : psu for psu in project.systems}
        for item_name in item_names:
            data += get_item_data_tsv(iname_to_psu[item_name], schema, 1,
                                      summary=summary)
    elif isinstance(context, orb.classes['HardwareProduct']):
        # context is Product -> single system MEL
        system = context
        data += get_item_data_tsv(system, schema, 1, summary=summary)
    else:
        orb.info('  - context is neither a Project nor Product ...')
        orb.info('    could not write MEL, quitting.')
        return
    with open(file_path, 'w') as f:
        f.write(data)


def get_item_data_tsv(item, schema, level, pref_units=False, summary=False,
                      qty=1):
    """
    Return a tsv string for an assembly of components with parameters / data
    elements.

    Args:
        component (HardwareProduct): component object
        schema (list of str):  ids of the parameters and data elements to be
            included
        level (int): assembly level of component

    Keyword Args:
        summary (bool):  if True, combine all instances of a product in a given
            asssembly into one line item with a computed quantity; otherwise,
            show a line item for each usage, tagged with its reference
            designator
        qty (int):  quantity of the item (used for summary)
    """
    # NB:  levels are 1-based
    if isinstance(item, orb.classes['HardwareProduct']):
        # this implies "root" item, so level and qty are 1
        component = item
        comp_name = (getattr(item, 'name', '') or 'Unknown').replace(
                                                            '\n', ' ').strip()
        comp_name = (level - 1) * '  ' + comp_name
        if not summary:
            # if not summary, the item being a Product instance implies that
            # it's the "root" item, so level and qty are 1
            level = 1
            qty = 1
    else:
        # Acu or ProjectSystemUsage
        if hasattr(item, 'component'):
            # Acu
            component = item.component
            qty = item.quantity or 1
        else:
            # ProjectSystemUsage
            component = item.system
            qty = 1
        comp_name = (level - 1) * '  ' + get_mel_item_name(item)
    data = ''
    vals = []
    for col_id in schema:
        # TODO: predetermine whether each schema item is a pid or deid
        # Excel doesn't like space between the number and "%" --
        # hence, fix_ctgcy() ...
        if col_id in parm_defz:
            # it's a parameter ...
            if 'Ctgcy' in col_id:
                pval = fix_ctgcy(str(100 * get_pval(component.oid, col_id)))
            else:
                if pref_units:
                    # get all values in user's preferred units
                    pd = parm_defz.get(col_id)
                    units = prefs['units'].get(pd['dimensions'], '')
                    units = units or in_si.get(pd['dimensions'], '')
                    pval = str(round_to(get_pval(
                                            component.oid, col_id, units=units)))
                else:
                    # get all values in SI units
                    pval = str(round_to(get_pval(component.oid, col_id)))
            vals.append(pval)
        elif col_id in de_defz:
            # it's a data_element ...
            dval = str(get_dval(component.oid, col_id))
            vals.append(dval)
        else:
            # neither a parameter nor data element
            vals.append('unknown')
    comp_id = component.id
    data += '\t'.join([comp_name, comp_id, str(level), str(qty)] + vals) + '\n'
    if component.components:
        next_level = level + 1
        if summary:
            products_by_oid = {acu.component.oid : acu.component
                               for acu in component.components
                               if acu.component.oid != 'pgefobjects:TBD'}
            qty_by_oid = {}
            for acu in component.components:
                oid = acu.component.oid
                if qty_by_oid.get(oid):
                    qty_by_oid[oid] += acu.quantity or 1
                else:
                    qty_by_oid[oid] = acu.quantity or 1
            for oid in products_by_oid:
                data += get_item_data_tsv(products_by_oid[oid],
                                          schema, next_level,
                                          qty=qty_by_oid[oid],
                                          summary=True)
        else:
            item_names = [get_mel_item_name(acu)
                          for acu in component.components]
            item_names.sort()
            acus_by_item_name = {get_mel_item_name(acu) : acu
                                 for acu in component.components}
            for item_name in item_names:
                data += get_item_data_tsv(acus_by_item_name[item_name], schema,
                                          next_level)
    return data


def write_power_modes_to_xlsx(act, usage, pref_units=False,
                              file_path='power_modes.xlsx'):
    """
    Output a System Power Modes report to Excel .xlsx format, including system
    / subsystem / component names and assembly levels.  The output consists of
    2 sheets:

        1)  Similar to the "Modes Table" format previously used in MDL,
            consisting of a column for each Activity (Power Mode), each
            containing a set of 3 sub-columns:  Power (CBE), Congtingency, and
            Power (MEV), with a row for each instrument and subsystem.

        2)  A table showing the underlying mode definitions in terms of the
            associated power levels at the system and component level,
            summarizing the content of the ConOps "Mode Definition Dashboard".

    Args:
        act (Mission or Activity):  parent activity containing the
            activities/modes being characterized
        usage (Project, ProjectSystemUsage, or Acu):  the top-level system
            usage of the assembly whose power modes are being described

    Keyword Args:
        pref_units (bool):  express values in the user's preferred units;
            default is False (use mks units)
        file_path (str):  path to output file
    """
    system_id = getattr(usage, 'id', None) or '[unknown id]'
    orb.log.debug('* write_power_modes_to xlsx()')
    orb.log.debug(f'  - subject: {act.id}')
    orb.log.debug(f'  - system: {system_id}')
    project = act.owner
    if not project:
        orb.log.debug('* Project not found, aborting.')
    mission = orb.select('Mission', owner=project)
    if not mission:
        orb.log.debug('* Mission not found for project, aborting.')
        return
    if act.oid == mission.oid:
        subject_label = mission.name
    else:
        subject_label = f'{mission.id}\n{act.name}'
    headers = [subject_label]
    subj_acts = []
    subj_act_oids = []
    for act in mission.sub_activities:
        subj_acts.append(act)
        subj_act_oids.append(act.oid)
    headers += [act.name for act in subj_acts]
    cycles = []
    for act in subj_acts:
        if act.activity_type.name == 'Cycle':
            # for cycles, only show their sub_activities ...
            # info about the cycle (Avg & Max Power) can be in a note
            subj_acts.remove(act)
            headers.remove(act.name)
            subj_act_oids.remove(act.oid)
            cycles.append(act)
            sub_acts = act.sub_activities
            for sub_act in sub_acts:
                subj_acts.append(sub_act)
                subj_act_oids.append(sub_act.oid)
                sub_act_label = f'{act.name}\n{sub_act.name}'
                headers.append(sub_act_label)
    book = xlsxwriter.Workbook(file_path)
    worksheet = book.add_worksheet()
    # xlsxwriter specifies widths in "characters" (as does Excel)
    col_widths = [10] * ((len(headers) - 1)*3 + 1)
    col_widths[0] = 80    # Mission/System/Subsystem Name
    orb.log.info('  - writing formatted column headers ...')
    for i, width in enumerate(col_widths):
        worksheet.set_column(i, i, width)

    fmts = {name : book.add_format(style)
            for name, style in xlsx_styles.items()}

    # Set position of title
    title_row = 0
    # Set relative positions of header rows
    hrow1 = title_row + 1
    hrow2 = hrow1 + 1

    # Title (row 0)
    # set row 0 height to 12*2
    worksheet.set_row(title_row, 12*2)
    # set hrow2 height taller (activity sub-headers with units)
    worksheet.set_row(hrow2, 42)
    worksheet.merge_range(title_row, 0, title_row, len(col_widths)-1,
                          f'  {mission.name} Power Modes',
                          fmts['black_bg_18'])
    header_style_names = [
                          'ctr_turquoise_bold_12',
                          'ctr_gray_bold_12',
                          'ctr_lime_bold_12',
                          'ctr_light_steel_blue_bold_12',
                          'ctr_yellow_bold_12',
                          'ctr_periwinkle_bold_12',
                          'ctr_green_bold_12',
                          'ctr_pale_blue_bold_12'
                          ]
    usages = [usage]
    if isinstance(usage, orb.classes['ProjectSystemUsage']):
        usages += list(usage.system.components)
    elif isinstance(usage, orb.classes['Acu']):
        usages += list(usage.component.components)
    data = get_power_modes_data(project, subj_acts, usages)
    p_cbe_header = 'Power\n(CBE)\nWatts'
    ctgcy_header = 'Contin-\ngency\n   %'
    p_mev_header = 'Power\n(MEV)\nWatts'
    orb.log.debug(f'  - len(headers) = {len(headers)}')
    orb.log.debug(f'  - len(subj_act_oids) = {len(subj_act_oids)}')
    for i, h in enumerate(headers):
        orb.log.debug(f'    + i = {i}')
        orb.log.debug(f'      header = {h}')
        if i == 0:
            # subject name header uses only 1 column but spans rows 1 & 2
            worksheet.merge_range(hrow1, 0, hrow2, 0, h,
                                  fmts['ctr_pale_blue_bold_12'])
            for j, usage in enumerate(usages):
                if hasattr(usage, 'system'):
                    comp = usage.system
                    ref = usage.system_role
                else:
                    comp = usage.component
                    ref = usage.reference_designator
                if j == 0:
                    name = f'{comp.name}'
                else:
                    name = f' -- {ref} {comp.name}'
                worksheet.write(hrow2 + j + 1, 0, name, fmts['left_bold_12'])
        else:
            fmt = fmts[header_style_names[i % len(header_style_names)]]
            # each activity header spans 3 columns
            worksheet.merge_range(hrow1, i*3 - 2, hrow1, i*3, h, fmt)
            # 2nd level headers (activity/mode sub-headers)
            worksheet.write(hrow2, i*3 - 2, p_cbe_header, fmt)
            for j, usage in enumerate(usages):
                p_cbe = data[usage.oid][subj_act_oids[i-1]]['p_cbe']
                worksheet.write(hrow2 + j + 1, i*3 - 2, p_cbe, fmt)
            worksheet.write(hrow2, i*3 - 1, ctgcy_header, fmt)
            for j, usage in enumerate(usages):
                ctgcy = data[usage.oid][subj_act_oids[i-1]]['ctgcy']
                ctgcy = ctgcy * 100
                worksheet.write(hrow2 + j + 1, i*3 - 1, ctgcy, fmt)
            worksheet.write(hrow2, i*3, p_mev_header, fmt)
            for j, usage in enumerate(usages):
                p_mev = data[usage.oid][subj_act_oids[i-1]]['p_mev']
                worksheet.write(hrow2 + j + 1, i*3, p_mev, fmt)
    book.close()


def get_power_modes_data(project, acts, usages):
    """
    Get power modes data for the specified activities and usages.
    """
    data = {}
    for usage in usages:
        usage_data = {}
        if hasattr(usage, 'system'):
            comp = usage.system
        else:
            comp = usage.component
        for act in acts:
            act_data = {}
            modal_context = get_modal_context(project.oid, usage.oid, act.oid)
            p_cbe_val = get_modal_power(project.oid, usage.oid, comp.oid,
                                        act.oid, modal_context)
            act_data['p_cbe'] = p_cbe_val
            ctgcy = get_pval(comp.oid, 'P[Ctgcy]')
            act_data['ctgcy'] = ctgcy
            factor = 1.0 + ctgcy
            p_mev_val = round_to(p_cbe_val * factor)
            act_data['p_mev'] = p_mev_val
            usage_data[act.oid] = act_data
        data[usage.oid] = usage_data
    return data

