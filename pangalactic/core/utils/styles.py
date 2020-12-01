# -*- coding: utf-8 -*-
"""
Styles, mainly for use with xlsxwriter in reports module
"""
# fonts
Helvetica = "Helvetica"
HelveticaBold = "Helvetica-Bold"
HelveticaBoldObl = "Helvetica-BoldOblique"
CourierBold = "Courier-Bold"
Courier = "Courier"
FontSize = 10
TinyFont = HelveticaBold
TinyFontSize = 7

xlsx_styles = dict(
    black_bg_18=dict(font_name='Arial', bold=True, font_size=18,
                     font_color='white', pattern=1, fg_color=0,
                     align='left', valign='vcenter', text_wrap=True),
    left_12=dict(font_name='Arial', font_size=12, font_color='black', border=1,
                 pattern=1, fg_color='white', align='left', valign='vcenter',
                 text_wrap=True),
    float_right_12=dict(font_name='Arial', font_size=12, font_color='black',
                  border=1, pattern=1, fg_color='white', align='right',
                  valign='vcenter', num_format='#,##0.00', text_wrap=True),
    int_right_12=dict(font_name='Arial', font_size=12, font_color='black',
                  border=1, pattern=1, fg_color='white', align='right',
                  valign='vcenter', num_format='#,##0', text_wrap=True),
    ctr_12=dict(font_name='Arial', font_size=12, font_color='black', border=1,
                pattern=1, fg_color='white', align='center', valign='vcenter',
                text_wrap=True),
    ctr_black_bg_12=dict(font_name='Arial', bold=True, font_size=12,
                         font_color='white', border=1, pattern=1, fg_color=0,
                         align='center', valign='vcenter', text_wrap=True),
    ctr_gray_12=dict(font_name='Arial', font_size=12, border=1, pattern=1,
                     align='center', valign='vcenter', fg_color='#DCDCDC',
                     text_wrap=True),
    ctr_gray_bold_12=dict(font_name='Arial', font_size=12, bold=True, border=1,
                          pattern=1, align='center', valign='vcenter',
                          fg_color='#DCDCDC', text_wrap=True),
    ctr_green_bold_12=dict(font_name='Arial', font_size=12, bold=True,
                           border=1, pattern=1, align='center',
                           valign='vcenter', fg_color='#CCFFCC', text_wrap=True),
    ctr_green_12=dict(font_name='Arial', font_size=12, border=1, pattern=1,
                      align='center', valign='vcenter',
                      fg_color='#CCFFCC', text_wrap=True),
    ctr_turquoise_12=dict(font_name='Arial', font_size=12, border=1, pattern=1,
                          align='center', valign='vcenter',
                          fg_color='#CCFFFF', text_wrap=True),
    ctr_turquoise_bold_12=dict(font_name='Arial', font_size=12, bold=True,
                               border=1, pattern=1, align='center',
                               valign='vcenter', fg_color='#CCFFFF',
                               text_wrap=True),
    ctr_light_steel_blue_12=dict(font_name='Arial', font_size=12, border=1,
                            pattern=1, align='center', valign='vcenter',
                            fg_color='#AFDBF5', text_wrap=True),
    ctr_light_steel_blue_bold_12=dict(font_name='Arial', font_size=12,
                            bold=True, border=1, pattern=1, align='center',
                            valign='vcenter', fg_color='#AFDBF5',
                            text_wrap=True),
    ctr_periwinkle_bold_12=dict(font_name='Arial', font_size=12, bold=True,
                                border=1, pattern=1, align='center',
                                valign='vcenter', fg_color='#99CCFF',
                                text_wrap=True),
    ctr_pale_blue_12=dict(font_name='Arial', font_size=12, border=1, pattern=1,
                          align='center', valign='vcenter',
                          fg_color='#99CCFF', text_wrap=True),
    ctr_pale_blue_bold_12=dict(font_name='Arial', font_size=12, bold=True,
                               border=1, pattern=1, align='center',
                               valign='vcenter', fg_color='#99CCFF',
                               text_wrap=True),
    left_black_bg_12=dict(font_name='Arial', font_size=12, border=1, pattern=1,
                          font_color='white', fg_color=0, align='left',
                          valign='vcenter', text_wrap=True),
    left_gray_bold_12=dict(font_name='Arial', font_size=12, bold=True,
                           border=1, pattern=1, align='left',
                           valign='vcenter', fg_color='#DCDCDC',
                           text_wrap=True),
    left_pale_blue_12=dict(font_name='Arial', font_size=12, border=1,
                           pattern=1, align='left', valign='vcenter',
                           fg_color='#99CCFF', text_wrap=True),
    left_pale_blue_bold_12=dict(font_name='Arial', font_size=12, bold=True,
                                border=1, pattern=1, align='left',
                                valign='vcenter', fg_color='#99CCFF',
                                text_wrap=True),
    float_right_black_bg_12=dict(font_name='Arial', font_size=12,
                                 font_color='white', border=1, pattern=1,
                                 align='right', valign='vcenter', fg_color=0,
                                 num_format='#,##0.00', text_wrap=True),
    int_right_black_bg_12=dict(font_name='Arial', font_size=12,
                               font_color='white', border=1, pattern=1,
                               align='right', valign='vcenter', fg_color=0,
                               num_format='#,##0', text_wrap=True),
    float_right_gray_bold_12=dict(font_name='Arial', font_size=12, bold=True,
                            border=1, pattern=1, align='right',
                            valign='vcenter', fg_color='#DCDCDC',
                            num_format='#,##0.00', text_wrap=True),
    int_right_gray_bold_12=dict(font_name='Arial', font_size=12, bold=True,
                            border=1, pattern=1, align='right',
                            valign='vcenter', fg_color='#DCDCDC',
                            num_format='#,##0', text_wrap=True),
    turquoise_bold_12_rotated=dict(font_name='Arial', font_size=12, bold=True,
                                   border=1, pattern=1, align='center',
                                   valign='vcenter', rotation=90,
                                   fg_color='#CCFFFF', text_wrap=True),
    turquoise_bold_10_rotated=dict(font_name='Arial', font_size=10, bold=True,
                                   border=1, pattern=1, align='center',
                                   valign='vcenter', rotation=90,
                                   fg_color='#CCFFFF', text_wrap=True),
    light_steel_blue_bold_12_rotated=dict(font_name='Arial', font_size=12,
                            bold=True, border=1, pattern=1, align='center',
                            valign='vcenter', rotation=90,
                            fg_color='#AFDBF5', text_wrap=True),
    light_steel_blue_bold_10_rotated=dict(font_name='Arial', font_size=10,
                            bold=True, border=1, pattern=1, align='center',
                            valign='vcenter', rotation=90, fg_color='#AFDBF5',
                            text_wrap=True)
    )


# DEPRECATED:  xlwt styles

# import xlwt

# # Styles can be combined if more than one needs to be applied
# # Borders are applied to all styles
# wrap_style = xlwt.easyxf(
    # 'align:wrap 1;  borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# # allows text to wrap instead of disappear off the edge, grid applied
# # (in all styles)
# bold_style = xlwt.easyxf(
    # 'font: bold 1;  borders: top 0x01, bottom 0x01, '
    # 'left 0x01, right 0x01;')
# bold_italic = xlwt.easyxf(
    # 'font:bold 1; font: italic 1;  borders: top 0x01, bottom 0x01, '
    # 'left 0x01, right 0x01;')
# italic_style = xlwt.easyxf(
    # 'font: italic 1;borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# # red text
# red_style = xlwt.easyxf(
    # 'font: bold 1, color red;  borders: top 0x01, bottom 0x01, '
    # 'left 0x01, right 0x01;')
# black_bg = xlwt.easyxf(
    # 'font: bold 1, color white; pattern: pattern solid, fore_color 0;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# black_bg_18 = xlwt.easyxf(
    # 'font: bold 1, height 360, color white; pattern: pattern solid, '
    # 'fore_color 0; borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# black_bg_12 = xlwt.easyxf(
    # 'font: bold 1, height 240, color white; pattern: pattern solid, '
    # 'fore_color 0; borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_black_bg_12 = xlwt.easyxf(
    # 'font: bold 1, height 240, color white; pattern: pattern solid, '
    # 'fore_color 0; align:vert center, horiz center; '
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# left_black_bg_12 = xlwt.easyxf(
    # 'font: bold 1, height 240, color white; pattern: pattern solid, '
    # 'fore_color 0; align:vert center, horiz left; '
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# right_black_bg_12 = xlwt.easyxf(
    # 'font: bold 1, height 240, color white; pattern: pattern solid, '
    # 'fore_color 0; align:vert center, horiz right; '
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# turquoise_bold_12_rotated = xlwt.easyxf(
    # 'font: bold 1, height 240; pattern: pattern solid, '
    # 'fore_color light_turquoise;'
    # 'align: vert center, horiz center, rotation 90;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_turquoise_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; pattern: pattern solid, '
    # 'fore_color light_turquoise; align:vert center, horiz center;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_turquoise_12 = xlwt.easyxf(
    # 'font: height 240; pattern: pattern solid, '
    # 'fore_color light_turquoise; align:vert center, horiz center;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_periwinkle_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; pattern: pattern solid, '
    # 'fore_color gray25; align:vert center, horiz center;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_green_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; pattern: pattern solid, '
    # 'fore_color light_green; align:vert center, horiz center;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_green_12 = xlwt.easyxf(
    # 'font: height 240; pattern: pattern solid, '
    # 'fore_color light_green; align:vert center, horiz center;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_12 = xlwt.easyxf(
    # 'font: height 240; '
    # 'align:vert center, horiz center;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# left_12 = xlwt.easyxf(
    # 'font: height 240; '
    # 'align:vert center, horiz left;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# right_12 = xlwt.easyxf(
    # 'font: height 240; '
    # 'align:vert center, horiz right;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; '
    # 'align:vert center, horiz center;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# left_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; '
    # 'align:vert center, horiz left;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# right_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; '
    # 'align:vert center, horiz right;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_pale_blue_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; pattern: pattern solid, fore_color pale_blue; '
    # 'align:vert center, horiz center;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# left_pale_blue_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; pattern: pattern solid, fore_color pale_blue; '
    # 'align:vert center, horiz left;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# right_pale_blue_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; pattern: pattern solid, fore_color pale_blue; '
    # 'align:vert center, horiz right;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# ctr_pale_blue_12 = xlwt.easyxf(
    # 'font: height 240; pattern: pattern solid, fore_color pale_blue; '
    # 'align:vert center, horiz center;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# left_pale_blue_12 = xlwt.easyxf(
    # 'font: height 240; pattern: pattern solid, fore_color pale_blue; '
    # 'align:vert center, horiz left;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# wrap_bold = xlwt.easyxf(
    # 'font: bold 1; align: wrap 1;  borders: top 0x01, '
    # 'bottom 0x01, left 0x01, right 0x01;')
# ctr_style = xlwt.easyxf(
    # 'align:vert center, horiz center;borders: top 0x01, bottom 0x01, '
    # 'left 0x01, right 0x01;')
# ctr_bold = xlwt.easyxf(
    # 'font: bold 1; align:vert center, horiz center;borders: top 0x01, '
    # 'bottom 0x01, left 0x01, right 0x01;')
# wrap_ctr_bold = xlwt.easyxf(
    # 'font: bold 1; align: wrap 1;align:vert center, horiz center;  borders: '
    # 'top 0x01, bottom 0x01, left 0x01, right 0x01;')
# gray_bg = xlwt.easyxf (
    # 'pattern: pattern solid, fore_color 22;borders: top 0x01, bottom 0x01, '
    # 'left 0x01, right 0x01;')
# gray_bold = xlwt.easyxf(
    # 'font: bold 1; pattern: pattern solid, fore_color 22;borders: top 0x01, '
    # 'bottom 0x01, left 0x01, right 0x01;')
# ctr_gray_bold = xlwt.easyxf(
    # 'align:vert center, horiz center; font: bold 1; pattern: pattern solid, '
    # 'fore_color 22; borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# wrap_ctr_gray_bold = xlwt.easyxf(
    # 'align:vert center, horiz center; align:wrap 1; font: bold 1;'
    # 'pattern: pattern solid, fore_color 22;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# ctr_gray_12 = xlwt.easyxf(
    # 'font: height 240; align:vert center, horiz center;'
    # 'pattern: pattern solid, fore_color 22;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# left_gray_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; align:vert center, horiz left;'
    # 'pattern: pattern solid, fore_color 22;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# right_gray_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; align:vert center, horiz right;'
    # 'pattern: pattern solid, fore_color 22;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# ctr_gray_bold_12 = xlwt.easyxf(
    # 'font: bold 1, height 240; align:vert center, horiz center;'
    # 'pattern: pattern solid, fore_color 22;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# wrap_ctr_gray = xlwt.easyxf(
    # 'align:wrap 1; align:vert center, horiz center; pattern: pattern solid, '
    # 'fore_color 22;borders: top 0x01, bottom 0x01, left 0x01, right 0x01' )
# ctr_gray = xlwt.easyxf(
    # 'align:vert center, horiz center; pattern: pattern solid, fore_color 22;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# wrap_gray = xlwt.easyxf(
    # 'align:wrap 1; pattern:pattern solid, fore_color 22; '
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# bold_italic_blue = xlwt.easyxf(
    # 'font:bold 1; font: italic 1; pattern: pattern solid, fore_color 40;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# blue_bg = xlwt.easyxf(
    # 'pattern:pattern solid, fore_color 40;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# yellow_bg = xlwt.easyxf(
    # 'pattern:pattern solid, fore_color 43;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# wrap_bright_yellow =xlwt.easyxf(
    # 'pattern:pattern solid, fore_color 5;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01; align: wrap 1')
# # bg yellow, text red
# red_yellow = xlwt.easyxf(
    # 'font: bold 1, color red; pattern: pattern solid, fore_color 43;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# # cell with thin borders on the top, bottom, and sides
# borders_style = xlwt.easyxf(
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;')
# # borders and wrapped text
# wrap_with_borders =xlwt.easyxf(
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;align: wrap 1')
# tall_font = xlwt.easyxf(
    # 'font:height 1500;borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# green_font = xlwt.easyxf(
    # 'font: color green;borders: top 0x01, bottom 0x01, left 0x01, right 0x01')
# # green wrapped text with borders
# green_borders = xlwt.easyxf(
    # 'align: wrap 1;borders:top 0x01, bottom 0x01, left 0x01, right 0x01; font: bold 1, color green;' )
# align_right = xlwt.easyxf(
    # 'align:horiz right; borders:top 0x01, bottom 0x01, left 0x01, right 0x01')
# # green text, yellow bg
# green_yellow = xlwt.easyxf(
    # 'font: color green; pattern:pattern solid, fore_color 5;'
    # 'borders: top 0x01, bottom 0x01, left 0x01, right 0x01;align: wrap 1')
# # sets the number format to percent
# style_percent = xlwt.easyxf(num_format_str='0.00%')

