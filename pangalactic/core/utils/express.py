"""
A generic (no dependencies on the rest of PanGalactic) reader for EXPRESS (ISO
10303-11) models formulated as instance data based on the MEXICO EXPRESS v2 XMI
metamodel.  This module reads an EXPRESS-XMI data file into a set of nested
Python dictionaries.
"""
# Python
import sys
from pprint import pprint
from StringIO import StringIO
# ElementTree
try:  # Python 2.5
    import xml.etree.ElementTree as ET
except:  # Python < 2.5 => install external ElementTree module
    import ElementTree as ET
# try:
#     from ElementTree import Element, SubElement, ElementTree
# except:
#     from elementtree.ElementTree import Element, SubElement, ElementTree
# PanGalactic
from pangalactic.core.names import namespaces
from pangalactic.core.names import register_ns


def read(f):
    """
    Read an EXPRESS-XMI file/stream and return a set of Python dictionaries.

    @param f:  A filename or file-like object containing EXPRESS-XMI data
    @type  f:  C{str} or C{file}

    @return:  a dictionary EXPRESS schema elements, mapped by their names.

             {name : {'type' : value
                      'attrs': [list of attr names] ...},
              ...}

    @rtype:   C{dict}
    """
    exp_schema = {}
    s = f
    if hasattr(f, 'read'):
        s = f.read()
    # register any namespaces specified in the source
    register_ns(StringIO(s))
    root = ET.parse(StringIO(s))
    content = root.find('XMI.content')
    # 'EXP2:Schema' element:
    schema = content.find(''.join(['{', namespaces['EXP2'], '}', 'Schema']))
    exp_schema['name'] = schema.get('name')
    # 'EXP2:schema-elements' element
    schema_elements = schema.find(''.join(['{', namespaces['EXP2'], '}',
                                           'schema-elements']))
    entities = {}
    defined_types = {}
    for e in schema_elements.getiterator():
        # general Schema element processing
        xmi_id = e.get('xmi.id')
        local_name = ''
        ne = e.find(''.join(['{', namespaces['EXP2'], '}', 'NamedElement.id']))
        if ne:
            scoped_id = ne.find(''.join(['{', namespaces['EXP2'], '}',
                                         'ScopedId']))
            if scoped_id:
                local_name = scoped_id.get('localName')
        if e.tag == ''.join(['{', namespaces['EXP2'], '}', 'EntityType']):
            # Entity-specific processing
            is_abstract = (e.get('isAbstract') == 'TRUE')
            if local_name:
                entities[local_name] = {}
                entities[local_name]['is_abstract'] = is_abstract
                entities[local_name]['xmi_id'] = xmi_id
                entities[local_name]['attributes'] = {}
                entity_attrs = e.find(''.join(['{', namespaces['EXP2'], '}',
                                      'EntityType.attributes']))
                if entity_attrs:
                    ea_idrefs = []
                    for ea in entity_attrs.getchildren():
                        ea_idrefs.append(ea.get('xmi.idref'))
                    # temporary thing for testing:
                    entities[local_name]['attributes']['idrefs'] = ea_idrefs
                entities[local_name]['subtype-of'] = {}
                entity_supertype = e.find(''.join(['{', namespaces['EXP2'], '}',
                                          'EntityType.subtype-of']))
                if entity_supertype:
                    es_idrefs = []
                    for es in entity_supertype.getchildren():
                        es_idrefs.append(es.get('xmi.idref'))
                    # temporary thing for testing:
                    entities[local_name]['subtype-of']['idrefs'] = es_idrefs
        if e.tag == ''.join(['{', namespaces['EXP2'], '}', 'SpecializedType']):
            # SpecializedType-specific processing (defined types)
            pass
    exp_schema['entities'] = entities
    exp_schema['defined_types'] = defined_types
    return exp_schema


if __name__ == '__main__':
    res = read(open(sys.argv[1]))
    pprint(res)

