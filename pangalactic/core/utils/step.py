#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classes corresponding to STEP Entities
"""
import os, sys
from optparse import OptionParser
from typing import NamedTuple

from pangalactic.core.uberorb import orb
from pangalactic.core.utils.part21 import parse_p21_data


def get_step_file_path(model):
    """
    Find the path of a STEP file for a model.

    Args:
        model (Model):  the Model instance for which the STEP file is sought

    Returns:
        the path to the STEP file in the orb's "vault"
    """
    # orb.log.debug('* get_step_model_path(model with oid "{}")'.format(
                  # getattr(model, 'oid', 'None')))
    if (model.has_files and model.type_of_model.id == "MCAD"):
        for rep_file in model.has_files:
            if rep_file.user_file_name.endswith(
                            ('.stp', '.STP', '.step', '.STEP', '.p21', '.P21')):
                vault_fname = rep_file.oid + '_' + rep_file.user_file_name
                fpath = os.path.join(orb.vault, vault_fname)
                if os.path.exists(fpath):
                    return fpath
            else:
                continue
    else:
        return ''


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


step_entities = [
    "PRODUCT",
    "PRODUCT_DEFINITION_FORMATION",
    "PRODUCT_DEFINITION",
    "PRODUCT_DEFINITION_WITH_ASSOCIATED_DOCUMENTS",
    "PRODUCT_CONTEXT",
    "NEXT_ASSEMBLY_USAGE_OCCURRENCE"
    ]

step_classes = [
    Product,
    ProductDefinitionFormation,
    ProductDefinition,
    Pdwad,
    ProductContext,
    Nauo
    ]

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

def make_step_obj(name, n, contents, data, db):
    """
    Construct a STEP python object from the unparsed parameter content of an
    entity in a part 21 file. This recursively creates any objects that may be
    needed to populate object-valued fields (attributes) of the object being
    constructed.

    Args:
        name (str): type name of a STEP entity
        n (str): numeric identifier ("ENTITY_INSTANCE_NAME", w/o "#")
        contents (str): its unparsed parameter content
        data (dict): parsed content of the containing p21 file
        db (dict): collection of python objects created from the p21 file
    """
    if name in step_entities:
        cls = step_classes[step_entities.index(name)]
    else:
        return None
    # for now, SET() attrs don't matter -- leave them unparsed
    parsed = [x.strip(" \n\r#'") for x in contents.split(',')]
    t = []
    for i, field in enumerate(cls._fields):
        ftype = cls.__annotations__[field]
        # identify any object-valued fields
        if ftype in step_classes:
            inst_n = parsed[i]
            if db.get('by_nbr') and inst_n in db['by_nbr']:
                t.append(db['by_nbr'][inst_n])
            else:
                contents = data['contents'][inst_n]
                obj = make_step_obj(step_entities[step_classes.index(ftype)],
                                    inst_n, contents, data, db)
                t.append(obj)
        else:
            t.append(parsed[i])
    obj = cls(*t)
    db['by_nbr'][n] = obj
    if not db['by_type'].get(name):
        db['by_type'][name] = [obj]
    else:
        db['by_type'][name].append(obj)
    return obj

def make_step_db(fpath):
    """
    Return a set of linked python step objects created from the entities in a
    part 21 file.
    """
    data = get_p21_data(fpath)
    db = {}
    db['by_nbr'] = {}
    db['by_type'] = {}
    for entity_name in step_entities:
        if entity_name in data['typeinst']:
            for inst_nbr in data['typeinst'][entity_name]:
                contents = data['contents'][inst_nbr]
                make_step_obj(entity_name, inst_nbr, contents, data, db)
    return db

def get_assembly(fpath):
    """
    Extract assembly tree from a STEP file.

    @param fpath:  path of a STEP file
    @type  fpath:  str
    """
    db = make_step_db(fpath)
    # TODO: build the tree from the NAUOs ...
    return db['by_type']['NEXT_ASSEMBLY_USAGE_OCCURRENCE']


if __name__ == '__main__':
    usage = 'usage:  %prog [options] file.p21'
    opt = OptionParser(usage)
    (options, args) = opt.parse_args(args=sys.argv)
    # debugging:
    print(f"options:  {options}")
    print(f"args:     {args}")
    print(get_assembly(args[1]))

