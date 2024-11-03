#!/usr/bin/env python
"""
A generic (no dependencies on the rest of PanGalactic) reader/writer for
"Part 21 files" (ISO 10303-21, STEP "Clear Text Encoding", a serialization
format).
"""

import re, sys, string, time
from optparse import OptionParser
from pprint import pprint
from pyparsing import Word, Optional, Forward, ZeroOrMore
from pyparsing import delimitedList

# added by Paul McGuire (thanks, Paul!)
from pyparsing import Combine, sglQuotedString,Group, Suppress, removeQuotes
from pyparsing import Dict, OneOrMore, cppStyleComment


def groupInParens(expr):
    return Group(Suppress("(") + expr + Suppress(")"))
    
pre = '0123'
HEX = string.hexdigits
BINARY = Word(pre, HEX)

DIGIT = string.digits
LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase + '_'
SPECIAL = '!"*$%&.#+,-()?/:;<=>@[]{|}^`~'
REVERSE_SOLIDUS = '\\'
APOSTROPHE = "'"
SIGN = Word('+-', max=1)
CHARACTER = Word((' ' + DIGIT + LOWER + UPPER + SPECIAL + REVERSE_SOLIDUS +
                  APOSTROPHE), max=1)
NON_Q_CHAR = Word((' ' + DIGIT + LOWER + UPPER + SPECIAL), max=1)
STRING = sglQuotedString.setParseAction(removeQuotes)
ENUMERATION = Combine('.' + Word(UPPER, UPPER + DIGIT) + '.')
ENTITY_INSTANCE_NAME = Word('#',DIGIT)

REAL = Combine(Optional(SIGN) + Word(DIGIT) + "." + Optional(Word(DIGIT)) + 
        Optional('E' + Optional(SIGN) + Word(DIGIT)))
INTEGER = Word('+-'+DIGIT,DIGIT)
STANDARD_KEYWORD = Word(UPPER, UPPER + DIGIT)
USER_DEFINED_KEYWORD = Combine('!' + STANDARD_KEYWORD)
KEYWORD = USER_DEFINED_KEYWORD | STANDARD_KEYWORD

OMITTED_PARAMETER = '*'
LIST = Forward()
UNTYPED_PARAMETER = Forward()
PARAMETER = Forward()
TYPED_PARAMETER = Forward()
PARAMETER_LIST = Forward()
LIST << groupInParens( Optional(PARAMETER_LIST) )

# replacing '^' with '|' in the next two expressions accounted for most of the
# performance speedup
UNTYPED_PARAMETER << ("$" | REAL | INTEGER | STRING | ENTITY_INSTANCE_NAME
                      | ENUMERATION | BINARY | LIST)
PARAMETER << (TYPED_PARAMETER | UNTYPED_PARAMETER | OMITTED_PARAMETER)
TYPED_PARAMETER << (KEYWORD + groupInParens( PARAMETER ))
PARAMETER_LIST << delimitedList(PARAMETER, delim=',')
unparsed_record = KEYWORD + groupInParens('.*')
SIMPLE_RECORD = KEYWORD + groupInParens( Optional(PARAMETER_LIST) )
SIMPLE_RECORD_LIST = SIMPLE_RECORD + ZeroOrMore(SIMPLE_RECORD)
SUBSUPER_RECORD = groupInParens( SIMPLE_RECORD_LIST )
#~ COMPLEX_ENTITY_INSTANCE = ENTITY_INSTANCE_NAME + '=' + SUBSUPER_RECORD + ';'
#~ ENTITY_INSTANCE = (SIMPLE_ENTITY_INSTANCE ^ COMPLEX_ENTITY_INSTANCE)
ENTITY_INSTANCE = Group(ENTITY_INSTANCE_NAME + Suppress('=') +
                        ( SIMPLE_RECORD | SUBSUPER_RECORD ) + Suppress(';'))
ENTITY_INSTANCE_LIST = ZeroOrMore(ENTITY_INSTANCE)

DATA_SECTION = ('DATA' +
                Optional( groupInParens( PARAMETER_LIST ).setResultsName(
                                                            "PARAMETERS")) +
                ';' +
                Dict(ENTITY_INSTANCE_LIST, asdict=True).setResultsName(
                                                            "ENTITIES") +
                'ENDSEC;')

HEADER_ENTITY = KEYWORD + groupInParens( Optional(PARAMETER_LIST) ) + ";"
HEADER_ENTITY_LIST = HEADER_ENTITY + ZeroOrMore(HEADER_ENTITY)
HEADER_SECTION = ("HEADER;" + HEADER_ENTITY + HEADER_ENTITY + HEADER_ENTITY +
                  Optional(HEADER_ENTITY_LIST) + "ENDSEC;")
EXCHANGE_FILE = ("ISO-10303-21;" + HEADER_SECTION.setResultsName("HEADER") + 
                 OneOrMore(DATA_SECTION).setResultsName("DATA") +
                 "END-ISO-10303-21;")
EXCHANGE_FILE.ignore(cppStyleComment)

generic_opening = """
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('STEP conformance test data for PDMnet, Round 2','AP203 instantiation - bill of material UoF'),'2;1');
FILE_NAME('b_o_m6.p21','1993-07-29 T11:23:12',
('M. Green','J. Black'),
('New Ventures, Inc.',
'P.O. Box 2222',
'Middleton',
'Michigan',
'50800'),'NIST Data Probe, Release March 1993','conformance test suite','K. H. White');
FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));
ENDSEC;
DATA;
"""


def preparse(data):
    top = generic_opening
    bottom = "\nENDSEC;\nEND-ISO-10303-21;"
    nauo_pat = r'#[0-9][0-9]*[ ]*=[ ]*NEXT_ASSEMBLY_USAGE_OCCURRENCE[ ]*\([^;]*\)[ ]*;'
    nauo = re.compile(nauo_pat, re.DOTALL)
    matches = nauo.findall(data)
    print(f'Contains {len(matches)} assemblies')
    nauos = '\n'.join(matches)
    nauos_p21 = top + nauos + bottom
    return nauos_p21


if __name__ == '__main__':
    usage = 'usage:  %prog [options] file.p21'
    optparser = OptionParser(usage)
    optparser.add_option("-t", "--time", action='store_true',
                         dest="show_time", default=False,
                         help="show the time consumed")
    (options, args) = optparser.parse_args(args=sys.argv[1:] or ['-h'])
    if args[0] != '-h':
        data = open(args[0]).read()
        if options.show_time:
            startTime = time.time()
        newdata = preparse(data)
        # print(newdata)
        res = EXCHANGE_FILE.parseString(newdata)
        if options.show_time:
            endTime = time.time()
            totalTime = endTime - startTime
            print("\nTotal parse time: %6.2f sec" % totalTime)
            print(len(data.split("\n"))," lines\n")
        # pprint( res.asList() )
        print('---------------')
        print('HEADER section:')
        print('---------------')
        print(res.HEADER)
        print()
        entities = res.ENTITIES[0]
        keylist = list(entities.keys())
        # print('\nENTITY IDs are:', keylist)
        # print('\nENTITIES are:')
        pprint(entities)
        # print('-------------------------')
        # print(f'Number of entities: {len(entities)}')
        # print(' - first 10 entities are:')
        # print('-------------------------')
        # for k in range(10):
            # print(entities[keylist[k]])
        # print('\nlast 10 items are:')

