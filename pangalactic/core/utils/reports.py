# -*- coding: utf-8 -*-
"""
Pan Galactic Report Writer
"""
import xlsxwriter

from pangalactic.core.parametrics import get_pval
from pangalactic.core.uberorb import orb
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
        print('col_widths = {}'.format(str(col_widths)))
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

def write_mel_xlsx(context, is_project=True,
                   file_path='mel_writer_output.xlsx'):
    """
    Output a Master Equipment List (MEL)

    Args:
        context (Project or Product):  the project or system of which this is
            the MEL
        is_project (bool):  flag indicating whether context is a Product or
            Project
        file_path (str):  path to report file
    """
    book = xlsxwriter.Workbook(file_path)
    worksheet = book.add_worksheet()
    # xlsxwriter specifies widths in "characters" (as does Excel)
    col_widths = 48 * [8]
    col_widths[0]  = 10
    col_widths[1] = 40
    col_widths[2] = 8     # UNIT MASS
    col_widths[3] = 6     # Cold Units
    col_widths[4] = 6
    col_widths[5] = 6
    col_widths[6] = 8     # Flight Spares
    col_widths[7] = 10    # EM Prototype
    col_widths[8] = 9     # Total Mass [kg] (CBE)
    col_widths[9] = 12    # Contingency [%]
    col_widths[10] = 12   # Total Mass w/ Contingency (MEV)
    col_widths[11] = 8
    col_widths[12] = 8
    col_widths[13] = 12   # Contingency [%]
    col_widths[14] = 12   # Total Power w/ Contingency (MEV)
    col_widths[15] = 8
    col_widths[16] = 8
    col_widths[17] = 12   # Contingency [%]
    col_widths[18] = 12   # Total Power w/ Contingency (MEV)
    col_widths[19] = 13   # QUIESCENT Total Power [W] (CBE)
    col_widths[20] = 10   # Quoted Unit Price ($K)
    col_widths[21] = 15   # Composition
    col_widths[22] = 40   # ADDITIONAL INFORMATION
    col_widths[23] = 16   # TRL
    col_widths[24] = 8
    col_widths[25] = 15   # LOCATION
    col_widths[26] = 14   # Temperature
    col_widths[27] = 12
    col_widths[28] = 12
    col_widths[29] = 15   # Radiation
    col_widths[30] = 10
    col_widths[31] = 10
    col_widths[32] = 10
    col_widths[33] = 5
    col_widths[34] = 5
    col_widths[35] = 5
    col_widths[36] = 5
    col_widths[37] = 5
    col_widths[38] = 5
    col_widths[39] = 5
    col_widths[40] = 10
    col_widths[41] = 60
    col_widths[42] = 12
    col_widths[43] = 12
    col_widths[44] = 12
    col_widths[45] = 12
    col_widths[46] = 12
    col_widths[47] = 12

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
                          '  MASTER EQUIPMENT LIST',
                          fmts['black_bg_18'])

    # First row of headers (hrow1)
    # worksheet.row(hrow1).height_mismatch = True
    worksheet.set_row(hrow1, 12*3)
    worksheet.write(hrow1, 0, 'LEVEL', fmts['ctr_pale_blue_bold_12'])
    worksheet.write(hrow1, 1, 'NAME (Mission or Payload Name)',
                                        fmts['ctr_pale_blue_bold_12'])
    worksheet.write(hrow1, 2, 'UNIT\nMASS', fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 3, hrow1, 7, '# OF UNITS',
                          fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 8, hrow1, 10, 'FLIGHT HARDWARE MASS',
                          fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 11, hrow1, 14,
                          'NOMINAL FLIGHT HARDWARE POWER',
                          fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 15, hrow1, 18,
                          'PEAK FLIGHT HARDWARE POWER',
                          fmts['ctr_gray_bold_12'])
    worksheet.write(hrow1, 19, 'QUIESCENT', fmts['ctr_gray_bold_12'])
    worksheet.write(hrow1, 22, 'ADDITIONAL INFORMATION',
                    fmts['ctr_pale_blue_bold_12'])
    worksheet.merge_range(hrow1, 26, hrow1, 29,
                          'HERITAGE VS ENVIRONMENTAL REQUIREMENTS',
                          fmts['ctr_turquoise_bold_12'])
    worksheet.merge_range(hrow1, 33, hrow1, 39,
                          'HERITAGE SUMMARY',
                          fmts['ctr_turquoise_bold_12'])
    worksheet.merge_range(hrow1, 42, hrow1, 47,
                          'PRICE COST MODELING DATA',
                          fmts['ctr_green_bold_12'])

    # # Second row of headers (hrow2)
    # # Set height to accomodate wrapped column heading text
    worksheet.set_row(hrow2, 12*8)
    worksheet.write(hrow2, 0, "", fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 1, "Subassembly/Component",
                    fmts['left_pale_blue_12'])
    worksheet.write(hrow2, 2, 'Unit Mass\n[kg]\n(CBE)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 3, 'Cold\nUnits', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 4, 'Hot\nUnits', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 5, 'Flight\nUnits', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 6, 'Flight\nSpares', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 7, 'EM\nPrototype', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 8, 'Total Mass\n[kg] (CBE)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 9, 'Contingency\n[%]', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 10, 'Total Mass\n[kg] with\nContingency\n(MEV)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 11, 'Unit\nPower [W]\n(CBE)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 12, 'Total\nPower [W]\n(CBE)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 13, 'Contingency\n(%)', fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 14, 'Total\nPower [W]\nwith\nContingency\n(MEV)',
                    fmts['ctr_pale_blue_12'])
    worksheet.write(hrow2, 15, 'Unit\nPower [W]\n(CBE)', fmts['ctr_gray_12'])
    worksheet.write(hrow2, 16, 'Total\nPower [W]\n(CBE)', fmts['ctr_gray_12'])
    worksheet.write(hrow2, 17, 'Contingency\n(%)', fmts['ctr_gray_12'])
    worksheet.write(hrow2, 18, 'Total\nPower [W]\nwith\nContingency\n(MEV)',
                    fmts['ctr_gray_12'])
    worksheet.write(hrow2, 19, 'Total Power\n[W] (CBE)', fmts['ctr_gray_12'])
    worksheet.merge_range(hrow1, 20, hrow2, 20, 'Quoted\nUnit\nPrice\n($K)',
                          fmts['ctr_pale_blue_12'])
    worksheet.merge_range(hrow1, 21, hrow2, 21, 'Composition',
                          fmts['ctr_pale_blue_12'])
    text = """(As applicable:
    Vendor, make, model, part #,
    volume, quote information,
    notation of identical items,
    instrument / component
    characteristics, ETU approach...)"""
    worksheet.write(hrow2, 22, text, fmts['ctr_pale_blue_12'])
    trl_text = """TECHNOLOGY
    READINESS
    LEVEL
    (TRL)
    """
    worksheet.merge_range(hrow1, 23, hrow2, 23, trl_text,
                       fmts['ctr_periwinkle_bold_12'])
    vendor_maturity_text = "VENDOR\nMATURITY\nDESCRIPTION"
    worksheet.merge_range(hrow1, 24, hrow2, 24, vendor_maturity_text,
                                            fmts['turquoise_bold_12_rotated'])
    worksheet.merge_range(hrow1, 25, hrow2, 25, 'LOCATION',
                                            fmts['ctr_turquoise_bold_12'])
    worksheet.write(hrow2, 26, 'Temperature\n-X to Y',
                 fmts['ctr_turquoise_12'])
    worksheet.write(hrow2, 27, 'Pressure\nX to Y [mPa]',
                 fmts['ctr_turquoise_12'])
    worksheet.write(hrow2, 28, 'Entry Load\n< X [G]', fmts['ctr_turquoise_12'])
    worksheet.write(hrow2, 29, 'Radiation\nTID\n< X [krad-Si]',
                 fmts['ctr_turquoise_12'])
    worksheet.merge_range(hrow1, 30, hrow2, 30,
                       'NEW TECHNOLOGY\nOR\nENGNRG CHANGE?',
                       fmts['turquoise_bold_12_rotated'])
    worksheet.merge_range(hrow1, 31, hrow2, 31, 'OWNERSHIP?',
                       fmts['turquoise_bold_12_rotated'])
    worksheet.merge_range(hrow1, 32, hrow2, 32, 'PERFORMANCE\nCHANGE?',
                       fmts['turquoise_bold_12_rotated'])
    worksheet.write(hrow2, 33, 'DESIGN', fmts['turquoise_bold_12_rotated'])
    worksheet.write(hrow2, 34, 'MANUFACTURE',
                    fmts['turquoise_bold_12_rotated'])
    worksheet.write(hrow2, 35, 'SOFTWARE', fmts['turquoise_bold_12_rotated'])
    worksheet.write(hrow2, 36, 'PROVIDER', fmts['turquoise_bold_12_rotated'])
    worksheet.write(hrow2, 37, 'USE', fmts['turquoise_bold_12_rotated'])
    worksheet.write(hrow2, 38, 'OPERATING\nENVIRONMENT',
                    fmts['turquoise_bold_12_rotated'])
    worksheet.write(hrow2, 39, 'PRIOR USE', fmts['turquoise_bold_12_rotated'])
    worksheet.merge_range(hrow1, 40, hrow2, 40, 'REFERENCE\nMISSION(S)',
                          fmts['turquoise_bold_12_rotated'])
    worksheet.merge_range(hrow1, 41, hrow2, 41,
                   'HERITAGE JUSTIFICATION and ADDITIONAL INFORMATION',
                   fmts['ctr_turquoise_bold_12'])
    worksheet.write(hrow2, 42, 'Structure\nMass [kg]', fmts['ctr_green_12'])
    worksheet.write(hrow2, 43, 'Electronic\nComplexity\nFactor',
                                                fmts['ctr_green_12'])
    worksheet.write(hrow2, 44, 'Structure\nComplexity\nFactor',
                                                fmts['ctr_green_12'])
    worksheet.write(hrow2, 45, 'Electronic\nRemaining\nDesign\n(1.00 = 100%)',
                                                fmts['ctr_green_12'])
    worksheet.write(hrow2, 46, 'Structure\nRemaining\nDesign\n(1.00 = 100%)',
                                                fmts['ctr_green_12'])
    worksheet.write(hrow2, 47,
                 'Engineering\nComplexity\nMod. Level\n(Simple,\nNew)',
                 fmts['ctr_green_12'])
    # # Third row of headers (hrow3)
    worksheet.write(hrow3, 1, "TOTAL FLIGHT HARDWARE",
                    fmts['left_pale_blue_bold_12'])

    level_fmts = {1: fmts['ctr_black_bg_12'],
                  2: fmts['ctr_gray_bold_12'],
                  3: fmts['ctr_12']
                  }
    name_fmts = {1: fmts['left_black_bg_12'],
                 2: fmts['left_gray_bold_12'],
                 3: fmts['left_12']
                 }
    data_fmts = {1: fmts['right_black_bg_12'],
                 2: fmts['right_gray_bold_12'],
                 3: fmts['right_12']
                 }
    for fmt in data_fmts.values():
        fmt.set_num_format('#,##0.00')
    # system level
    # (note that system.name overwrites the template "NAME..." placeholder)
    if is_project:
        # context is Project, so may include several systems
        project = context
        mel_label = 'MISSION: {}'.format(project.id)
        worksheet.write(hrow1, 1, mel_label, fmts['left_pale_blue_bold_12'])
        start_row = hrow3
        system_names = [psu.system.name.lower() for psu in project.systems]
        system_names.sort()
        systems_by_name = {psu.system.name.lower() : psu.system
                           for psu in project.systems}
        for system_name in system_names:
            last_row = write_component_rows_xlsx(worksheet, level_fmts,
                                                 name_fmts, data_fmts, 1,
                                                 start_row,
                                                 systems_by_name[system_name])
            start_row = last_row + 1
    else:
        # context is Product -> a single system MEL
        system = context
        worksheet.write(hrow1, 1, system.name, fmts['left_pale_blue_bold_12'])
        write_component_rows_xlsx(worksheet, level_fmts, name_fmts, data_fmts,
                                  1, hrow3, system)
    book.close()

def write_component_rows_xlsx(sheet, level_fmts, name_fmts, data_fmts, level,
                              row, component, qty=1):
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
    # first write the formatting to the whole row to set the bg color
    sheet.write_row(row, 0, [' ']*48, level_fmts.get(level, level_fmts[3]))
    # then write the "LEVEL" cell
    sheet.write(row, 0, level, level_fmts.get(level, level_fmts[3]))
    # level-based indentation
    spaces = '   ' * level
    sheet.write(row, 1, spaces + component.name, name_fmts.get(level, name_fmts[3]))
    data_fmt = data_fmts.get(level, data_fmts[3])
    sheet.write(row, 2, mcbe, data_fmt)        # Unit Mass
    sheet.write(row, 5, int(qty), data_fmt)    # Flight Units
    sheet.write(row, 8, mcbe * qty, data_fmt)  # Total Mass
    sheet.write(row, 9, ctgcy_m, data_fmt)
    sheet.write(row, 10, mmev * qty, data_fmt) # Mass MEV
    sheet.write(row, 11, pcbe, data_fmt)       # Unit Power
    sheet.write(row, 12, pcbe * qty, data_fmt) # Total Power
    sheet.write(row, 13, ctgcy_P, data_fmt)
    sheet.write(row, 14, pmev * qty, data_fmt) # Power MEV
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
            row = write_component_rows_xlsx(sheet, level_fmts, name_fmts,
                                            data_fmts, next_level, row,
                                            comps_by_name[comp_name],
                                            qty=qty_by_name[comp_name])
    return row

