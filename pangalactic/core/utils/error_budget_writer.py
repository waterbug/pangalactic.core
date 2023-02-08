# -*- coding: utf-8 -*-
"""
Error Budget Writer
"""
import os, sys, xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell

from pangalactic.core.uberorb import orb


def gen_error_budget(instrument, file_path='Error_Budget.xlsx'):
    """
    Generate an Error Budget for an optical instrument.

    Args:
        instrument (Product):  the instrument of which this is the Error
            Budget

    Keyword args:
        file_path (str):  path to write the error budget file
    """
    book = xlsxwriter.Workbook(file_path)
    worksheet = book.add_worksheet('Top Down')

    # number and font formatting
    bold = book.add_format({'bold': True})
    rounded = book.add_format({'num_format': '0.0'})

    # cell_widths = []
    # for col in range(len(headers)):
        # cell_widths.append([len(rec[col]) for rec in headers + records])
    # col_widths = [max(widths) for widths in cell_widths]
    # # print('col_widths = {}'.format(str(col_widths)))
    # for i, width in enumerate(col_widths):
        # worksheet.set_column(i, i, width)

    error_list = [
        'Error Values', 
        'System WFE',
        'System Reserve', 
        'System AI&T',
        'Ground to Orbit',
        'Gravity Release',
        'Cooldown',
        'Moisture Desorption/Dryout',
        'On-orbit Stability',
        'Thermal Stability',
        'Jitter',
        'Material Stability',
        'Optical System',
        'Optical Reserve',
    ]

    level_two_errors = ['System Reserve', 'System AI&T', 'Ground to Orbit',
                        'On-orbit Stability', 'Optical System']
    level_three_errors = ['Gravity Release', 'Cooldown',
                          'Moisture Desorption/Dryout', 'Thermal Stability', 
                          'Jitter', 'Material Stability', 'Optical Reserve']
    level_four_errors = ['Instrument Reserve']
    level_five_errors = ['Fabrication', 'Alignment', 'Gravity', 'Thermal',
                         'EOL']

    # the inputs need to be >1 otherwise things might not work
    # for i, instrument in enumerate(instruments):
    # (initially, just 1 instrument ...)
    error_list.append(instrument.name)
    level_three_errors.append(instrument.name)
    error_list.extend([level_four_errors[0]])
    components = [acu.component for acu in instrument.components]
    num_components = len(components)
    if num_components == 0:
        # error budget cannot be generated
        return
    for j, comp in enumerate(components):
        error_list.append(comp.name)
        level_four_errors.append(comp.name)
        error_list.extend(level_five_errors)        

    def rctc(r,c):
        # Converts excel row-column format to cell format. Ex: (1,1) -> B2
        return xl_rowcol_to_cell(r,c) 

    SWFE = 100
    # SWFE = int(input("Enter a value for the System Wavefront Error: "))
    worksheet.write('G3', SWFE)
    worksheet.write('G2', "Error Values", bold)

    # if the formula is changed, rows will update automatically but columns
    # will need to be updated manually at the moment, you'll need to update the
    # excel formula if it's generating more than 1000 rows
    for row in range(len(error_list)):
        if error_list[row] == 'System WFE':
            worksheet.write(row+1, 1, error_list[row], bold)
        elif error_list[row] in level_two_errors:
            worksheet.write(row+1, 2, error_list[row], bold)
            worksheet.write_formula(rctc(row+1,7), '=G3/sqrt(counta(C1:C100))',
                                    rounded) 
        elif error_list[row] in level_three_errors:
            worksheet.write(row+1, 3, error_list[row], bold)
            if error_list[row] in ['Gravity Release', 'Cooldown',
                                   'Moisture Desorption/Dryout']:
                worksheet.write_formula(rctc(row+1,8),
                                        '=H6/sqrt(counta(D15:D1000))', rounded)
            elif error_list[row] in ['Thermal Stability', 'Jitter',
                                     'Material Stability']:
                worksheet.write_formula(rctc(row+1,8),
                                        '=H10/sqrt(counta(D15:D1000))',
                                        rounded)
            elif error_list[row] in level_three_errors[-1:-num_components-2:-1]:
                worksheet.write_formula(rctc(row+1,8),
                                        '=H14/sqrt(counta(D15:D1000))',
                                        rounded)                                
        elif error_list[row] in level_four_errors:
            worksheet.write(row+1, 4, error_list[row], bold)
            worksheet.write_formula(rctc(row+1,9),
                                    '=I16/sqrt(counta(E17:E20))', rounded)
        elif error_list[row] in level_five_errors:
            worksheet.write(row+1, 5, error_list[row], bold)
            worksheet.write_formula(rctc(row+1,10), '=J18/sqrt(5)', rounded)

    # code for the bottom up error budget page -- just copy and pasted the code
    # for top down sheet but more efficient to reference the first sheet
    # directly
    worksheet2 = book.add_worksheet('Bottom Up')

    # static values
    worksheet2.write('G3', SWFE)
    worksheet2.write('G2', "Error Values", bold)
    worksheet2.write('L2', "Error Values (CBE)", bold)
    
    # if the formula is changed, rows will update automatically but columns
    # will need to be updated manually at the moment, you'll need to update the
    # excel formula if it's generating more than 1000 rows
    for row in range(len(error_list)):
        if error_list[row] == 'System WFE':
            worksheet2.write(row+1, 1, error_list[row], bold)
            worksheet2.write_formula(row+1, 11, '=sqrt(sumsq(H1:H20))',
                                     rounded)
        elif error_list[row] in level_two_errors:
            worksheet2.write(row+1, 2, error_list[row], bold)
            worksheet2.write_formula(rctc(row+1,7),
                                     '=G3/sqrt(counta(C1:C100))', rounded) 
            if error_list[row] == 'System Reserve':
                worksheet2.write_formula(rctc(row+1,11),
                                         '=sqrt(G3^2-sumsq(H5:H25))', rounded)
            elif error_list[row] == 'Ground to Orbit':
                worksheet2.write_formula(rctc(row+1,11), '=sqrt(sumsq(I7:I9))',
                                         rounded)
            elif error_list[row] == 'On-orbit Stability':
                worksheet2.write_formula(rctc(row+1,11),
                                         '=sqrt(sumsq(I11:I13))', rounded)
            elif error_list[row] == 'Optical System': #
                worksheet2.write_formula(rctc(row+1,11),
                                         '=sqrt(sumsq(I15:I1000))', rounded)
        elif error_list[row] in level_three_errors:
            worksheet2.write(row+1, 3, error_list[row], bold)
            if error_list[row] in ['Gravity Release', 'Cooldown',
                                   'Moisture Desorption/Dryout']:
                worksheet2.write_formula(rctc(row+1,8),
                                         '=H6/sqrt(counta(D15:D1000))',
                                         rounded)
            elif error_list[row] in ['Thermal Stability', 'Jitter',
                                     'Material Stability']:
                worksheet2.write_formula(rctc(row+1,8),
                                         '=H10/sqrt(counta(D15:D1000))',
                                         rounded)
            elif error_list[row] in level_three_errors[-1:-num_components-2:-1]:
                worksheet2.write_formula(rctc(row+1,8),
                                         '=H14/sqrt(counta(D15:D1000))',
                                         rounded)
                worksheet2.write_formula(rctc(row+1,11),
                                         '=sqrt(H14^2-sumsq(I16:I1000))',
                                         rounded)
        elif error_list[row] in level_four_errors:
            worksheet2.write(row+1, 4, error_list[row], bold)
            worksheet2.write_formula(rctc(row+1,9),
                                     '=I16/sqrt(counta(E17:E20))', rounded)
            if error_list[row] == 'Instrument Reserve': #
                worksheet2.write_formula(rctc(row+1,11),
                                         '=sqrt(I16^2-sumsq(J18:J24))',
                                         rounded)
            else:
                worksheet2.write_formula(rctc(row+1,11),
                                         '=sqrt(sumsq(K19:K23))', rounded)
        elif error_list[row] in level_five_errors:
            worksheet2.write(row+1, 5, error_list[row], bold)
            worksheet2.write_formula(rctc(row+1,10), '=J18/sqrt(5)', rounded)

    book.close()
    if sys.platform == 'win32':
        try:
            os.system(f'start excel.exe "{file_path}"')
        except:
            orb.log.debug('  could not start Excel')
    elif sys.platform == 'darwin':
        try:
            cmd = f'open -a "Microsoft Excel.app" "{file_path}"'
            os.system(cmd)
        except:
            orb.log.debug('  unable to start Excel')


# if __name__ == '__main__':
    # gen_error_budget(None)

