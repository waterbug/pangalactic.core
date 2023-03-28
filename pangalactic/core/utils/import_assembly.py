#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from optparse import OptionParser
from pprint import pprint
# from pangalactic.core.uberorb import orb
from pangalactic.core.utils.part21 import parse_p21_data

# nauo attrs:
#     - id                   (identifier) [product_definition_relationship]
#     - name                 (label)      [product_definition_relationship]
#     - description [OPTIONAL](text)      [product_definition_relationship]
#     - relating_product_def (product_definition) [product_definition_relationship]
#     - related_product_def  (product_definition) [product_definition_relationship]
#     - reference_designator [OPTIONAL](identifier) [acu]

# product_definition attrs:
#     - id                 : identifier
#     - description        : text
#     - formation          : product_definition_formation
#     - frame_of_reference : product_definition_context

# product_definition_formation attrs:
#     - id                 : identifier
#     - description        : text
#     - of_product         : product

# product attrs:
#     - id                 : identifier
#     - name               : label
#     - description        : text
#     - frame_of_reference : SET [1:?] OF product_context

# product_context attrs:
#     - name               : label                [application_context]
#     - frame_of_reference : application_context  [application_context]
#     - discipline_type    : label


# TODO:  rewrite to use part21.py
def getAssemblies(fpath):
    """
    Extract assembly structures from a STEP file.

    @param fpath:  path of a STEP file
    @type  fpath:  str
    """
    f = open(fpath)
    p21_data = f.read()
    f.close()
    data = parse_p21_data(p21_data)
    # projid = os.path.basename(f).split('.')[0].upper()
    # print(f' - project id: {projid}')
    # TODO:
    #   - this function really needs a wizard
    #     + pick a namespace (default to user's preferred ns)
    #     + ask if user wants to create a context related to this data
    #     + pick a project (default to current project if user has permission;
    #       otherwise, default to user's preferred project, if any)
    # project = orb.classes['Project'](_schema=orb.schemas['Project'],
                                     # id=projid,
                                     # id_ns='sandbox')
    nauo = {}
    # id_ns = project.oid
    parents = set()
    children = set()
    if not data['typeinst'].get('NEXT_ASSEMBLY_USAGE_OCCURRENCE'):
        print('No assemblies found.')
        return
    for n in data['typeinst']['NEXT_ASSEMBLY_USAGE_OCCURRENCE']:
        parent, child = [x.strip(" \n\r#'")
                         for x in data['contents'][n].split(',')[3:5]]
        nauo[n] = {'id'     : n,
                   # 'id_ns'  : id_ns,
                   # relating_product_definition (4th attr)
                   ### DEPRECATED:
                   ### 'parent' : ':'.join([id_ns, parent]),
                   'assembly' : parent,
                   # related_product_definition (5th attr)
                   ### DEPRECATED:
                   ### 'child'  : ':'.join([id_ns, child]),
                   'component' : child,
                   'reference_designator' : '' # test data doesn't have
                   }
        parents.add(parent)
        children.add(child)
    # product_definitions
    pdset = parents | children
    print(f'pdset = {pdset}')
    pd = {}
    for pdref in pdset:
        pdfref = data['contents'][pdref].split(',')[2].strip(" \n\r#'")
        version = data['contents'][pdfref].split(',')[0].strip(" \n\r#'")
        mpref = data['contents'][pdfref].split(',')[2].strip(" \n\r#'")
        # product name (or id if no name)
        pre_id = (data['contents'][mpref].split(',')[1].strip(" \n\r#'")
                  or data['contents'][mpref].split(',')[0].strip(" \n\r#'"))
        product_id = '-'.join([pre_id, pdref])
        product_name = ' '.join([pre_id, '( STEP file instance:', pdref, ')'])
        pd[pdref] = {'id'           : product_id,
                     # 'id_ns'        : id_ns,
                     # 'cm_authority' : project.oid,
                     # version from pdf
                     'version'      : version,
                     # modeled product
                     'name'         : product_name
                     }
    # acus = [orb.classes['Acu'](_schema=orb.schemas['Acu'], **nauo[n])
            # for n in nauo]
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
    pprint(nauo)
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

