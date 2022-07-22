"""
PGEF units:  reference data for numeric values with units.
"""
# cross reference from dimension names to SI units, in which the values can be
# used to find the corresponding astropy Unit object by:
#   from astropy import units as u
#   unit = getattr(u, in_si['current'])
# [e.g.]
#   unit = getattr(u, 'A')    # the "Amperes" object)

from collections import OrderedDict
import pint

ureg = pint.UnitRegistry()

# in_si maps "dimensions" to their associated base SI units
in_si = OrderedDict([
    ('', ''),
    (None, ''),
    ('None', ''),
    ('dimensionless', ''),
    ('acceleration', 'm/s^2'),              # meter / second^2
    ('angle', 'radian'),                    # degree
    ('angular acceleration', 'degree/s^2'), # degree / second^2
    ('angular momentum', 'N*m*s'),          # Newton-meter-second, etc.
    ('angular velocity', 'degree/s'),       # degree / second
    ('area', 'm^2'),                        # square meter
    ('bitrate', 'bit/s'),                   # bit / second
    ('capacitance', 'F'),                   # farad
    ('charge', 'C'),                        # coulomb
    ('data', 'bit'),                        # bit
    ('decibels-isotropic', 'dBi'),          # dBi (decibels-isotropic)
    ('decibels', 'dB'),                     # dB (decibels)
    ('electrical current', 'A'),            # ampere
    ('electrical potential', 'V'),          # volt
    ('electrical resistance', 'Ohm'),       # ohm
    ('energy', 'J'),                        # joule
    ('force', 'N'),                         # newton
    ('frequency', 'Hz'),                    # hertz (== s^-1)
    ('inductance', 'H'),                    # henry
    ('length', 'm'),                        # meter
    ('luminosity', 'cd'),                   # candela, cd, candle (old)
    ('mass', 'kg'),                         # kilogram
    ('moment of inertia', 'kg*m^2'),        # kg * meter^2
    ('momentum', 'kg*m/s'),                 # kg * meter / second
    ('money', '$'),                         # dollar
    ('percent', '%'),                       # .01 * value
    ('power', 'W'),                         # watt
    ('pressure', 'Pa'),                     # pascal
    ('radiation', 'rads'),                  # rads -- not 'rad' (== 'radian')
    ('substance', 'mol'),                   # moles
    ('temperature', 'K'),                   # Kelvin
    ('time', 's'),                          # second
    ('torque', 'N*m'),                      # newton-meter
    ('volume', 'm^3'),                      # cubic meter
    ('velocity', 'm/s')                     # meter / second
    ])

# alt_units maps "dimensions" to lists of their most commonly used units
alt_units = OrderedDict([
    ('', ['', 'radian', 'degree', 'arcminute', 'arcsecond', 'steradian']),
    ('angle', ['radian', 'degree', 'arcminute', 'arcsecond', 'steradian']),
    ('area', ['m^2', 'cm^2', 'mm^2']),
    ('bitrate', ['bit/s', 'kbit/s', 'Mbit/s', 'Gbit/s', 'Tbit/s', 'Tbit/day',
                 'Tbit/week', 'Tbit/fortnight', 'Tbit/month', 'Tbit/year',
                 'kB/s', 'MB/s', 'GB/s', 'TB/s']),
    ('capacitance', ['F', 'mF', 'uF', 'nF', 'pF']),
    ('charge', ['C', 'mC', 'uC', 'nC', 'pC']),
    ('data', ['bit', 'kbit', 'Mbit', 'Gbit', 'Tbit', 'kB', 'MB', 'GB', 'TB',
              'PB', 'EB']),
    ('decibels-isotropic', ['dBi']),   # antenna gain
    ('decibels', ['dB']),              # amplifier gain
    ('electrical current', ['A', 'mA', 'uA', 'kA']),
    ('electrical potential', ['V', 'kV', 'mV', 'uV']),
    ('electrical resistance', ['Ohm', 'kOhm', 'MOhm', 'GOhm', 'mOhm', 'uOhm']),
    ('energy', ['J', 'kJ', 'MJ', 'GJ', 'TJ', 'mJ', 'uJ', 'nJ', 'pJ',
                'watthour', 'erg', 'eV', 'keV', 'MeV', 'GeV', 'TeV']),
    ('force', ['N', 'kN', 'dyne']),
    ('frequency', ['Hz', 'kHz', 'MHz', 'GHz', 'THz', 'rpm']),
    ('inductance', ['H', 'mH', 'uH']),
    ('length', ['m', 'km', 'cm', 'mm', 'nm', 'angstrom', 'ly', 'au', 'parsec',
                'foot', 'inch', 'furlong']),
    ('luminosity', ['mcd', 'cd']),
    ('mass', ['kg', 'g', 'mg', 'ug', 'lb']),
    ('moment of inertia', ['kg*m^2']),        # kg * meter^2
    ('momentum', ['kg*m/s']),                 # kg * meter / second
    ('money', ['$']),                         # dollar
    ('substance', ['mol', 'nmol', 'mmol']),
    ('power', ['W', 'kW', 'MW', 'GW', 'TW', 'mW', 'uW', 'nW', 'pW']),
    ('pressure', ['Pa', 'kPa', 'mPa', 'uPa', 'atm', 'psi']),
    ('radiation', ['rads', 'krads', 'Mrads', 'mrads', 'gray']),
    ('temperature', ['K', 'degC', 'degF']),
    ('time', ['s', 'ms', 'us', 'ns', 'hr', 'day', 'week', 'fortnight', 'month',
              'year']),
    ('volume', ['m^3', 'liter', 'cc']),
    ('velocity', ['m/s', 'kph', 'mph', 'mile/s', 'c', 'furlong/fortnight'])
    ])

# prefixes maps SI decimal and binary prefixes to their definitions
prefixes = dict(
    # decimal prefixes
    y='yocto (1e-24)',
    z='zepto (1e-21)',
    a='atto (1e-18)',
    f='femto (1e-15)',
    p='pico (1e-12)',
    n='nano (1e-9)',
    u='micro (1e-6)',
    m='milli (1e-3)',
    c='centi (1e-2)',
    d='deci (1e-1)',
    da='deca (1e+1)',
    h='hecto (1e2)',
    k='kilo (1e3)',
    M='mega (1e6)',
    G='giga (1e9)',
    T='tera (1e12)',
    P='peta (1e15)',
    E='exa (1e18)',
    Z='zetta (1e21)',
    Y='yotta (1e24)',
    # binary_prefixes
    Ki='kibi (2**10)',
    Mi='mebi (2**20)',
    Gi='gibi (2**30)',
    Ti='tebi (2**40)',
    Pi='pebi (2**50)',
    Ei='exbi (2**60)',
    Zi='zebi (2**70)',
    Yi='yobi (2**80)'
    )

