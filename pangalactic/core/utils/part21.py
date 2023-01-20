#!/usr/bin/env python
"""
A generic (no dependencies on the rest of pangalactic) reader/writer for
Part 21 files (ISO 10303-21, STEP "Clear Text Encoding" serialization
format).
"""
import sys, string
from optparse import OptionParser
from pprint import pprint
from pyparsing import Word, Optional, Forward, ZeroOrMore
from pyparsing import delimitedList

# added by Paul McGuire (thanks, Paul!)
from pyparsing import Combine, sglQuotedString, Group, Suppress, removeQuotes
from pyparsing import Dict, OneOrMore, cppStyleComment

# import time
# time.clock()

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
PARAMETER_LIST << Group(delimitedList(PARAMETER, delim=','))
unparsed_record = KEYWORD + groupInParens('.*')
SIMPLE_RECORD = KEYWORD + groupInParens( Optional(PARAMETER_LIST) )
SIMPLE_RECORD_LIST = SIMPLE_RECORD + ZeroOrMore(SIMPLE_RECORD)
SUBSUPER_RECORD = groupInParens( SIMPLE_RECORD_LIST )
#~ COMPLEX_ENTITY_INSTANCE = ENTITY_INSTANCE_NAME + '=' + SUBSUPER_RECORD + ';'
#~ ENTITY_INSTANCE = (SIMPLE_ENTITY_INSTANCE ^ COMPLEX_ENTITY_INSTANCE)
ENTITY_INSTANCE = Group(ENTITY_INSTANCE_NAME + '=' + ( SIMPLE_RECORD | SUBSUPER_RECORD ) + ';')
ENTITY_INSTANCE_LIST = ZeroOrMore(ENTITY_INSTANCE)

DATA_SECTION = ('DATA' + Optional( groupInParens( PARAMETER_LIST ).setResultsName("PARAMETERS")) + ';' + Dict(ENTITY_INSTANCE_LIST) + 'ENDSEC;')

HEADER_ENTITY = KEYWORD + groupInParens( Optional(PARAMETER_LIST) ) + ";"
HEADER_ENTITY_LIST = HEADER_ENTITY + ZeroOrMore(HEADER_ENTITY)
HEADER_SECTION = ("HEADER;" + HEADER_ENTITY + HEADER_ENTITY + HEADER_ENTITY +
                  Optional(HEADER_ENTITY_LIST) + "ENDSEC;")
EXCHANGE_FILE = ("ISO-10303-21;" + HEADER_SECTION.setResultsName("HEADER") + 
                 OneOrMore(DATA_SECTION).setResultsName("DATA") + "END-ISO-10303-21;")
EXCHANGE_FILE.ignore(cppStyleComment)


if __name__ == '__main__':
    usage = 'usage:  %prog [options] file[.p21|.stp|.step]'
    optparser = OptionParser(usage)
    # optparser.add_option("-t", "--time", action='store_true',
                         # dest="show_time", default=False,
                         # help="show the time consumed")
    (options, args) = optparser.parse_args(args=sys.argv[1:] or ['-h'])
    if args[0] != '-h':
        data = open(args[0]).read()
        # if options.show_time:
            # startTime = time.clock()
        res = EXCHANGE_FILE.parseString(data)
        # if options.show_time:
            # endTime = time.clock()
            # totalTime = endTime - startTime
            # print("\nTotal parse time: %6.2f sec" % totalTime)
            # print(len(data.split("\n"))," lines\n")
        print('res.HEADER:')
        print('==============================================================')
        print(res.HEADER)
        print('==============================================================')
        print('res.DATA:')
        print('==============================================================')
        print(res.DATA)
        print('==============================================================')
        print('res.asList():')
        print('==============================================================')
        pprint( res.asList() )
        print('==============================================================')
        # keylist = list(res.DATA.keys())
        # print('\nitem IDs are:', keylist)
        # print('\nfirst 10 items are:')
        # for k in range(10):
            # print(keylist[k], res.DATA[keylist[k]][1], res.DATA[keylist[k]][2])
        # print('\nlast 10 items are:')
        # for k in range(11)[1:]:
            # print(keylist[(-1)*k], res.DATA[keylist[(-1)*k]][1], res.DATA[keylist[(-1)*k]][2])

