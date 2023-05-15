#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A generic (no dependencies on the rest of PanGalactic) reader/writer for
"Part 21 files" (ISO 10303-21, STEP "Clear Text Encoding", a serialization
format).  This module reads a STEP Part 21 data file into a set of
Python dictionaries.
"""
import sys, time
from optparse import OptionParser
from pprint import pprint
from simpleparse.common import numbers, strings, comments
from simpleparse.parser import Parser
from simpleparse import dispatchprocessor as dp

# Part 21 File syntax specification (informal)

# Productions whose names are all caps are formally named and specified in ISO
# 10303-21:2002(E).  Productions with lower-case names are either "convenience"
# productions invented for this parser, or are specified in ISO 10303-21:2002(E)
# somewhere other than the formal file syntax specification.

# NOTES:
# (1)  simplification:  "USER_DEFINED_KEYWORD" will be ignored for now (should
# essentially never occur in a STEP file produced from a COTS CAX tool), so
# "KEYWORD" == "STANDARD_KEYWORD" for our purposes here.
# (2)  some definitions:
# simple_instance ->   an unparsed simple entity instance
# complex_instance ->  an unparsed complex entity instance

p21_syntax = r'''
ENTITY_INSTANCE_NAME  := '#', [0-9]+
KEYWORD               := [A-Z_], [A-Z0-9_]*
<eol>                 := '\r'?, '\n'
<record_terminator>   := ')', ts, ';', eol
parameter_list        := -record_terminator, -record_terminator*
simple_instance       := ts, ENTITY_INSTANCE_NAME, ts, '=', ts, KEYWORD,
                         ts, eol?, '(', parameter_list?, record_terminator
instance_list         := KEYWORD, ts, eol?, '(', parameter_list?, ')', ts,
                         eol?, (KEYWORD, '(', parameter_list?, ')', ts, eol?)*
complex_instance      := ts, ENTITY_INSTANCE_NAME, ts, '=', ts, '(',
                         parameter_list?, record_terminator
<ts>                  := [ \t]*
<comma>               := ',', ts, eol?, ts
<nullline>            := ts, eol
<ignorable_stuff>     := (ts, c_comment)/nullline
<header_tag>          := 'HEADER;', eol?
<end_tag>             := 'ENDSEC;', eol
HEADER_SECTION        := header_tag, -end_tag*, end_tag
EXCHANGE_FILE         := 'ISO-10303-21;', eol?, ignorable_stuff*,
                         HEADER_SECTION, ignorable_stuff*,
                         ('DATA;',
                         (simple_instance/complex_instance/ignorable_stuff)*,
                         ts, 'ENDSEC;', eol),
                         (ignorable_stuff*,
                         ('DATA;',
                         (simple_instance/complex_instance/ignorable_stuff)*,
                         ts, 'ENDSEC;', eol))*,
                         ignorable_stuff*, 'END-ISO-10303-21;', nullline*
'''


class Part21Preparser(Parser):
    """
    Preparser for Part 21 files.
    """
    def __init__(self, *arg, verbose=False):
        Parser.__init__(self, *arg)
        self.res = {}
        self.verbose = verbose

    def buildProcessor(self):
        return Part21Processor(self.res, verbose=self.verbose)


class Part21Processor(dp.DispatchProcessor):
    """
    Processing object for postprocessing the Part 21 grammar definitions into a
    new generator.
    """
    def __init__(self, res, verbose=False):
        self.res = res
        self.verbose = verbose
        # contents:  maps entity inst nbr (n) to unparsed content
        # insttype:  maps entity inst nbr (n) to KEYWORD (i.e. type)
        # typeinst:  maps KEYWORD (i.e. type) (n) to entity inst numbers list
        self.res['contents'] = {}
        self.res['insttype'] = {}
        self.res['typeinst'] = {}

    def ENTITY_INSTANCE_NAME(self, tag_stuff, buffer):
        """
        Process C{ENTITY_INSTANCE_NAME} production.
        """
        return dp.getString(tag_stuff, buffer)[1:]

    def KEYWORD(self, tag_stuff, buffer):
        """
        Process C{KEYWORD} production.
        """
        return dp.getString(tag_stuff, buffer)

    def parameter_list(self, tag_stuff, buffer):
        """
        Process C{parameter_list} production.
        """
        return dp.getString(tag_stuff, buffer)

    def instance_list(self, tag_stuff, buffer):
        """
        Process C{instance_list} production.

        @return:  a 2-tuple of (keywords, parameter lists), where keywords is
            the list of KEYWORD occurrences and parameter lists is a list of
            strings (each of which is an unparsed parameter list).
        """
        inst = dp.multiMap(tag_stuff, buffer)
        return inst.get('KEYWORD'), inst.get('parameter_list')

    def simple_instance(self, tag_stuff, buffer):
        """
        Process C{simple_instance} production.
        """
        tag, start, stop, subtags = tag_stuff
        inst = dp.singleMap(subtags, self, buffer)
        self.res['contents'][
            inst.get('ENTITY_INSTANCE_NAME')] = inst.get('parameter_list')
        self.res['insttype'][
            inst.get('ENTITY_INSTANCE_NAME')] = inst.get('KEYWORD')
        if self.verbose:
            name = inst.get('ENTITY_INSTANCE_NAME')
            keyword = inst.get('KEYWORD')
            print(f'{name}: {keyword}')
        if inst.get('KEYWORD') in self.res['typeinst']:
            self.res['typeinst'][
                inst.get('KEYWORD')].append(inst.get('ENTITY_INSTANCE_NAME'))
        else:
            self.res['typeinst'][
                inst.get('KEYWORD')] = [inst.get('ENTITY_INSTANCE_NAME')]

    def complex_instance(self, tag_stuff, buffer):
        """
        Process C{complex_instance} production.
        """
        tag, start, stop, subtags = tag_stuff
        inst = dp.singleMap(subtags, self, buffer)
        self.res['contents'][
            inst.get('ENTITY_INSTANCE_NAME')] = inst.get('parameter_list')
        self.res['insttype'][
            inst.get('ENTITY_INSTANCE_NAME')] = 'complex_type'
        if self.verbose:
            name = inst.get('ENTITY_INSTANCE_NAME')
            keyword = 'complex_type'
            print(f'{name}: {keyword}')
        if inst.get('KEYWORD') in self.res['typeinst']:
            self.res['typeinst'][
                inst.get('KEYWORD')].append(inst.get('ENTITY_INSTANCE_NAME'))
        else:
            self.res['typeinst'][
                inst.get('KEYWORD')] = [inst.get('ENTITY_INSTANCE_NAME')]

    def HEADER_SECTION(self, tag_stuff, buffer):
        """
        Process C{HEADER_SECTION} production.
        """
        # tag_stuff = (tag, start, stop, subtags)
        self.res['header'] = dp.getString(tag_stuff, buffer)


def parse_p21_data(data, perf=False, verbose=False, test=False):
    """
    Read a STEP Part 21 file/stream and return a set of Python dictionaries.

    @param data:  STEP instance data in Part 21 format
    @type  data:  str

    @param null:  a value to use for nulls in the data, which are
        represented by '$' in Part 21.  Attributes with null values will not
        be included in the instance dictionaries unless a value is supplied
        for null, in which case they will be included with that value
    @type  null:  str

    @return:  a dict that contains 4 items:
        (1) 'header', the unparsed header section of the part 21 file;
        (2) 'contents', a dict that maps entity instance numbers to their
            unparsed content (production: 'ENTITY_INSTANCE_NAME');
        (3) 'insttype', a dict that maps entity instance numbers to their
            declared types (production: 'KEYWORD')
        (4) 'typeinst', a dict that maps declared types to a list of their
            entity instance numbers.
    @rtype:   dict
    """
    p = Part21Preparser(p21_syntax, verbose=verbose)
    if verbose:
        print('* p21 parser created.')
    if data:
        if perf:
            start = time.time()
        success, result, nextchar = p.parse(data, production='EXCHANGE_FILE')
        if perf:
            end = time.time()
            print("\nTotal parse time: %6.2f sec" % (end - start))
            print(len(list(p.res.get('contents', [])))," instances\n")
        if test:
            print('---------------')
            print('Sample of Data:')
            print('---------------')
            sample = data[:100]
            print(sample)
            print('\n------------')
            print('Result Tree:')
            print('------------')
            pprint(p.res)
        return p.res
    elif test:
        # run all tests on p21_syntax
        from pangalactic.test import test_part21_preparse as tpp
        for production, test_data in tpp.tests.items():
            if verbose:
                print('* production:', production)
            for data in test_data:
                success, children, nextcharacter = p.parse(data,
                                                production=production)
                assert success and nextcharacter==len(data), ''.join([
                    "Wasn't able to parse %s as a %s " % (
                        repr(data), production),
                    "(%s chars parsed of %s), returned value was %s" % (
                        nextcharacter, len(data),
                        (success, children, nextcharacter))
                        ])
                if verbose:
                    print('  * data:', data)
                    print('  * output:')
                    pprint(p.parse(data, production=production))
                    print
                elif success:
                    print('  * passed: ', production)
    else:
        print('No data specified.')


def write(dataset, schema='pgef', fpath='out.p21', description='',
          null='$', wrap='element'):
    """
    Write a dataset out to a Part 21 file/stream.

    @param dataset:  a dictionary of dictionaries of the form:

             {id-1 : {attr:value, ...},
              id-2 : {attr:value, ...},
              ...}

        ... where each C{id-n} attribute is of the form '#'+str(int) and
        must be unique within the dataset.

    @type  dataset:  C{dict}

    @param schema:  name of the schema governing the data
    @type  schema:  C{str}

    @param fpath:  the path of the file to write to
    @type  fpath:  C{str}

    @param description:  some text describing the data
    @type  description:  C{str}

    @param null:  a value to use for nulls in the data, which are
        represented by '$' in Part 21.  Attributes with null values will not be
        included in the instance dictionaries unless a value is supplied for
        null, in which case they will be included with that value
    @type  null:  C{str}

    @param wrap:  type of wrapping to use for output:

        'element' :  wrap elements
        'pprint'  :  wrap elements and attributes
        otherwise :  no wrap (any other value of 'wrap')

    @type  wrap:  C{str}
    """
    f = open(fpath, 'w')
    f.write('Part 21 File\n')
    f.close()


if __name__ == '__main__':
    usage = 'usage:  %prog [options] file.p21'
    optparser = OptionParser(usage)
    optparser.add_option("-p", "--perf", action='store_true',
                         dest="performance", default=False,
                         help="run the parser's unit tests")
    optparser.add_option("-t", "--test", action='store_true',
                         dest="test", default=False,
                         help="run the parser's unit tests")
    optparser.add_option("-v", "--verbose", action='store_true',
                         dest="verbose", default=False,
                         help="verbose output from test (no effect on normal function)")
    (options, args) = optparser.parse_args(args=sys.argv)
    # debugging:
    # print("options:  %s" % str(options))
    # print("args:     %s" % str(args))
    if len(args) > 1:
        f = open(args[1])
        p21_data = f.read()
        f.close()
        parse_p21_data(p21_data,
                       perf=options.performance,
                       verbose=options.verbose,
                       test=options.test)
    elif options.test:
        parse_p21_data(None,
                       test=True,
                       perf=options.performance,
                       verbose=options.verbose)
    else:
        optparser.print_help()

