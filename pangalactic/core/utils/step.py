#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classes corresponding to STEP Entities
"""
import sys
from optparse import OptionParser
from pprint import pprint
# from collections import namedtuple
from typing import NamedTuple

# from pangalactic.core.uberorb import orb
from pangalactic.core.utils.part21 import parse_p21_data


class Product(NamedTuple):
    """
    A product concept
    """
    id: str
    name: str
    description: str
    frame_of_reference: list


class ProductDefinitionFormation(NamedTuple):
    """
    A version of a product that is used in a model.
    """
    id: str
    description: str
    of_product: Product


class ProductDefinition(NamedTuple):
    """
    The representation of a product that is used in a model.
    """
    id: str
    description: str
    formation: ProductDefinitionFormation
    frame_of_reference: list


class Pdwad(NamedTuple):
    """
    [PRODUCT_DEFINITION_WITH_ASSOCIATED_DOCUMENTS] Subtype of
    product_definition with a list of references to associated documents
    (files).
    """
    id: str
    description: str
    formation: ProductDefinitionFormation
    frame_of_reference: list
    documentation_ids: list


class ProductContext(NamedTuple):
    """
    The context in which a product model is defined
    """
    name: str
    frame_of_reference: list
    discipline_type: str


class Nauo(NamedTuple):
    """
    [NEXT_ASSEMBLY_USAGE_OCCURRENCE] The relationship between an assembly and
    a component.
    """
    id: str
    name: str
    description: str
    relating_product_definition: ProductDefinition
    related_product_definition: ProductDefinition
    reference_designator: str


step_classes = {
    "PRODUCT": Product,
    "PRODUCT_DEFINITION": ProductDefinition,
    "PRODUCT_DEFINITION_WITH_ASSOCIATED_DOCUMENTS": Pdwad,
    "PRODUCT_DEFINITION_FORMATION":   ProductDefinitionFormation,
    "PRODUCT_CONTEXT":                ProductContext,
    "NEXT_ASSEMBLY_USAGE_OCCURRENCE": Nauo
    }

def get_p21_data(fpath):
    """
    Return a set of data structures by parsing a p21 file.

    @return:  a dict that contains 4 items:
        (1) 'header', the unparsed header section of the part 21 file;
        (2) 'contents', a dict that maps entity instance numbers to their
            unparsed content (production: 'ENTITY_INSTANCE_NAME');
        (3) 'insttype', a dict that maps entity instance numbers to their
            declared types (production: 'KEYWORD')
        (4) 'typeinst', a dict that maps declared types to a list of their
            entity instance numbers.
    """
    f = open(fpath)
    p21_data = f.read()
    f.close()
    data = parse_p21_data(p21_data)
    return data

def make_step_obj(name, contents):
    """
    Construct a STEP python object from the unparsed parameter content of an
    entity in a part 21 file.

    Args:
        name (str): type name of a STEP entity
        contents (str): its unparsed parameter content
    """
    cls = step_classes.get(name)
    if cls is None:
        return None
    t = [x.strip(" \n\r#'") for x in contents.split(',')]
    # for now, SET() attrs don't matter -- leave them unparsed
    return cls(*t)

def get_step_db(fpath):
    """
    Return a set of linked python step objects created from the entities in a
    part 21 file.
    """
    data = get_p21_data(fpath)
    objs_by_nbr = {}
    objs_by_type = {}
    for entity_name in data['typeinst']:
        if entity_name in step_classes:
            objs_by_type[entity_name] = []
            for inst_nbr in data['typeinst'][entity_name]:
                contents = data['contents'][inst_nbr]
                obj = make_step_obj(entity_name, contents)
                objs_by_nbr[inst_nbr] = obj
                objs_by_type[entity_name].append(obj)

def getAssemblies(fpath):
    """
    Extract assembly structures from a STEP file.

    @param fpath:  path of a STEP file
    @type  fpath:  str
    """
    data = get_p21_data(fpath)
    # projid = os.path.basename(f).split('.')[0].upper()
    # print(f' - project id: {projid}')
    # TODO:
    #   - this function could have a wizard:
    #     + pick a namespace (default to user's preferred ns)
    #     + ask if user wants to create a context related to this data
    #     + pick a project (default to current project if user has permission;
    #       otherwise, default to user's preferred project, if any)
    # project = orb.classes['Project'](_schema=orb.schemas['Project'],
                                     # id=projid,
                                     # id_ns='sandbox')
    # nauos maps p21 ids to extracted Nauo instances
    nauos = {}
    # id_ns = project.oid
    assemblies = set()
    components = set()
    if not data['typeinst'].get('NEXT_ASSEMBLY_USAGE_OCCURRENCE'):
        print('No assemblies found.')
        return
    for n in data['typeinst']['NEXT_ASSEMBLY_USAGE_OCCURRENCE']:
        assembly, component = [x.strip(" \n\r#'")
                         for x in data['contents'][n].split(',')[3:5]]
        nauos[n] = {'id'     : n,
                   'assembly' : assembly,  # relating_product_definition
                   'component' : component,  # related_product_definition
                   'reference_designator' : ''
                   }
        assemblies.add(assembly)
        components.add(component)
    # product_definition (and subtype) instances
    pdset = assemblies | components
    print(f'pdset = {pdset}')
    pd = {}
    for pdref in pdset:
        pdfref = data['contents'][pdref].split(',')[2].strip(" \n\r#'")
        version = data['contents'][pdfref].split(',')[0].strip(" \n\r#'")
        mpref = data['contents'][pdfref].split(',')[2].strip(" \n\r#'")
        # product name (or id if name attr is empty)
        pre_id = (data['contents'][mpref].split(',')[1].strip(" \n\r#'")
                  or data['contents'][mpref].split(',')[0].strip(" \n\r#'"))
        product_id = '-'.join([pre_id, pdref])
        product_name = ' '.join([pre_id, '( STEP file instance:', pdref, ')'])
        pd[pdref] = {'id'           : product_id,
                     'version'      : version,        # version from pdf
                     'name'         : product_name    # modeled product
                     }
    # acus = [orb.classes['Acu'](_schema=orb.schemas['Acu'], **nauos[n])
            # for n in nauos]
    # models = [orb.classes['Model'](_schema=orb.schemas['Model'], **pd[p])
              # for p in pd]
    # return project, acus, models
    print('-------------------------------------')
    print('Product Definitions:')
    print('-------------------------------------')
    pprint(pd)
    print('-------------------------------------')
    print('NAUOs:')
    print('-------------------------------------')
    pprint(nauos)
    print('-------------------------------------')

if __name__ == '__main__':
    import time
    usage = 'usage:  %prog [options] file.p21'
    opt = OptionParser(usage)
    opt.add_option("-p", "--perf", action='store_true',
                   dest="performance", default=False,
                   help="run the parser's unit tests")
    (options, args) = opt.parse_args(args=sys.argv)
    # debugging:
    print(f"options:  {options}")
    print(f"args:     {args}")
    if len(args) > 1:
        if options.performance:
            start = time.time()
        getAssemblies(args[1])
        if options.performance:
            end = time.time()
            print("\nTotal time: %6.2f sec" % (end - start))
    else:
        opt.print_help()

