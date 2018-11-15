"""
OWL import/export module.

This module imports and exports OWL graphs to and from PanGalactic.

OWL graphs are composed of sets of Classes (sets with a defining
characteristic), Properties (descriptive "attributes" of Classes, which may
either have a datatype value or an object value -- i.e., be a relationship
between instances of the Class and instances of another Class), and
constraints.
"""
# Python modules
import os
import re
from collections import OrderedDict

# ElementTree
import xml.etree.ElementTree as ET

# RDFLib
from rdflib import Graph, Namespace, RDF

# PanGalactic
from pangalactic.core                import xsd_datatypes
from pangalactic.core.datastructures import OrderedSet
from pangalactic.core.names          import namespaces, register_namespaces
from pangalactic.core.names          import u2q, q2u, get_uri, get_prefix
from pangalactic.core.utils.meta     import asciify


def fix_funky_uris(s):
    """
    Replace stupid "file:/x..." and "file://x..." URIs with correct
    "file:///x...".
    """
    funkyre = re.compile('file://?([^/])')
    def fixit(matchobj):
        return 'file:///' + matchobj.group(1)
    return re.sub(funkyre, fixit, s)


OWL_NS = Namespace(u'http://www.w3.org/2002/07/owl#')


def get_ontology_prefix(source):
    """
    Get the uri of the principal Ontology node of a source dataset.

    There should be one and only one Ontology element per source, and that
    ontology element's 'about' attribute can either be an empty string
    (meaning the ontology is defined in the local namespace) or must contain
    the full uri of the ontology.

    Args:
        source (str):  a path or string buffer containing RDF/XML encoded OWL
            data

    Returns:
        str:  the uri of the Ontology defined in the source
    """
    root = ET.parse(source)
    onode = root.find('{http://www.w3.org/2002/07/owl#}Ontology')
    oref = onode.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
    if hasattr(source, 'read'):
        # if source is file-like, must reset to beginning ...
        source.seek(0)
    register_namespaces(source)
    return get_prefix(oref)


def find_nodes_by_type(graph, typeqn):
    """
    Find nodes in a graph which have the value of C{typeqn} as their type.

    Args:
        graph (Graph):  the subject graph
        typeqn (str):  qname of the type of nodes to be sought

    Returns:
        OrderedDict:  dict mapping type qnames to matching nodes
    """
    nodes = OrderedDict()
    for node in graph.subjects(RDF.type, q2u(typeqn)):
        for ns in list(namespaces.values()):
            # 'if ns.uri' eliminates blank Class nodes (if it doesn't
            # have an ID, we're nagonna use it)
            if ns.uri and ns.uri in node:
                nodes[u2q(node)] = node
    return nodes


class PanGalacticKnowledgeBase(Graph):
    """
    Represents a KnowledgeBase -- a container for graphs of statements.
    Typically imported as `KB`. ;)

    Graphs can be added to a `KB` instance from RDF/XML files.  The `graphs`
    attribute of a `KB` instance is a dictionary of the graphs it contains.

    KB implements the `ISchemaSource` interface, the PGEF interface to data
    structures that define application domain schemas.

    @ivar store:  an in-memory storage of all triples (a.k.a. statements)
        known to this KB instance.
    @type store:  L{rdflib.ConjunctiveGraph}

    @ivar graphs:  a dictionary of named graphs (instances of the RDFLib "Graph"
        class), each typically read in from an RDF/XML file.  All triples in a
        Graph instance are also added to KB.store when the instance is read in
        from an RDF/XML file using the KB.readGraphFromRdfXmlData() method.
    @type graphs:  dict

    @ivar class_nodes_by_type:  a dictionary that maps the qname of each Class
        node type ('rdfs:Class' or 'owl:Class') to a dictionary that maps the
        qnames of nodes of that type to their nodes.
    @type class_nodes_by_type:  dict

    @ivar property_nodes_by_type:  a dictionary that maps the qname of each
        Property node type ('rdf:Property', 'owl:DatatypeProperty',
        'owl:ObjectProperty') to a dictionary that maps the qnames of nodes
        of that type to their nodes.
    @type property_nodes_by_type:  dict

    @ivar class_node_names:  the set of qnames of all Class nodes.  (Implemented
        as a property that is derived from class_nodes_by_type.)
    @type class_node_names:  L{set} of L{str}

    @ivar property_node_names:  the set of qnames of all Property nodes.
        (Implemented as a property that is derived from property_nodes_by_type.)
    @type property_node_names:  L{set} of L{str}

    @ivar node_names:  the set of qnames of all Class and Property nodes in the
        knowledgebase.
    @type node_names:  L{set} of L{str}
    """

    def __init__(self, pgef_path):
        """
        Create a KB instance using `pgef.owl` as the initial ontology.

        If a path or a data stream is specified, an initial ontology will be
        extracted from the files or data (which currently must be in RDF and/or
        OWL format -- other formats, such as N3, may be supported later).  The
        initial ontology can be extended, and instances added to the store, by
        calling `self.parse` with additional sources.

        Args:
            pgef_path (str):  path to an OWL file.
        """
        Graph.__init__(self)
        if pgef_path and not os.path.exists(pgef_path):
            raise ValueError('pgef.owl path given does not exist.')
        self.import_ontology(pgef_path)

    def import_ontology(self, kbpath):
        """
        Read an ontology from a .owl file.

        Args:
            kbpath (str):  path to an OWL file
        """
        if kbpath.endswith('.owl'):
            print('* KB: registering namespaces from owl file ...')
            register_namespaces(kbpath)
            print('* KB: beginning parse of owl ...')
            self.parse(kbpath)

    def _get_class_nodes_by_type(self):
        """
        Construct a dictionary that maps the qnames of the types of Class
        nodes to a dictionary that maps the node qname to the node for
        nodes of that type in a graph.
        """
        nodesbytype = OrderedDict()
        for typeqn in ['rdfs:Class', 'owl:Class']:
            nodesbytype[typeqn] = find_nodes_by_type(self, typeqn)
        return nodesbytype

    # property:  class_nodes_by_type

    class_nodes_by_type = property(fget=_get_class_nodes_by_type)

    def _get_property_node_names_by_type(self):
        """
        Construct a dictionary of the Property nodes for a graph.
        """
        nodesbytype = OrderedDict()
        for typeqn in [
            'rdf:Property',
            'owl:DatatypeProperty',
            'owl:FunctionalProperty',
            'owl:InverseFunctionalProperty',
            'owl:ObjectProperty',
            'owl:SymmetricProperty',
            'owl:TransitiveProperty'
            ]:
            nodesbytype[typeqn] = find_nodes_by_type(self, typeqn)
        return nodesbytype

    # property:  property_nodes_by_type

    property_nodes_by_type = property(fget=_get_property_node_names_by_type)

    # property:  'class_node_names'

    def get_class_node_names(self):
        return OrderedSet([qname
                           for node_dict in list(self.class_nodes_by_type.values())
                           for qname in node_dict])

    def set_class_node_names(self, val):
        raise TypeError('class_node_names attribute is read-only')

    def del_class_node_names(self):
        raise TypeError('class_node_names attribute cannot be removed')

    class_node_names = property(get_class_node_names,
                                set_class_node_names,
                                del_class_node_names,
                                'class_node_names')

    # property:  'property_node_names'

    def get_property_node_names(self):
        return OrderedSet([qname
                        for node_dict in list(self.property_nodes_by_type.values())
                        for qname in node_dict])

    def set_property_node_names(self, val):
        raise TypeError('property_node_names attribute is read-only')

    def del_property_node_names(self):
        raise TypeError('property_node_names attribute cannot be removed')

    property_node_names = property(get_property_node_names,
                                   set_property_node_names,
                                   del_property_node_names,
                                   'property_node_names')

    # property:  'node_names'

    def get_node_names(self):
        return OrderedSet([qname
                    for node_dict in (list(self.class_nodes_by_type.values()) +
                                      list(self.property_nodes_by_type.values()))
                    for qname in node_dict])

    def set_node_names(self, val):
        raise TypeError('node_names attribute is read-only')

    def del_node_names(self):
        raise TypeError('node_names attribute cannot be removed')

    node_names = property(get_node_names, set_node_names, del_node_names,
                          'node_names')

    def get_triple_objects(self, subjqn, predqn):
        """
        Get the object nodes of triples that have the specified subject and
        predicate.

        @param subjqn:  Qname of the subject node
        @type  subjqn:  C{str}

        @param predqn:  Qname of the predicate node
        @type  predqn:  C{str}
        """
        objects = []
        for s, p, o in self.triples((get_uri(subjqn), get_uri(predqn), None)):
            objects.append(o)
        return objects

    def get_class_names(self, nsprefix):
        """
        Return the local names of all Classes defined within the specified
        namespace in KB.  Names will be forced to L{str} type for use as Python
        identifiers (names).

        @param nsprefix:  the name (a.k.a. "prefix") of a namespace
        @type  nsprefix:  C{unicode} or C{str}

        @param unicode:  if True, return names as C{unicode} instances;
            otherwise, return them as C{str}s
        @type  unicode:  C{bool}

        @return:  set of Class names
        @rtype:   L{set} of L{str}
        """
        cnames = OrderedSet([asciify(n.split(':')[1])
                             for n in self.class_node_names
                             if nsprefix+':' in n])
        return cnames

    def get_base_names(self, nsprefix, name, scope=None):
        """
        Within the specified namespace, get the names of all Classes to which
        the named Class has a `subClassOf` relationship, excluding 'owl'
        Classes (such as "Thing").  If a scope is specified, only get base names
        within the namespaces in scope.

        @param nsprefix:  the name (a.k.a. "prefix") of a namespace
        @type  nsprefix:  C{str}

        @param name:  the local name of a Class in the specified namespace
        @type  name:  C{str}

        @param scope:  if not None, only get base names within the namespaces
            specified
        @type  scope:  C{list} (of C{str} or C{unicode})

        @param unicode:  if True, return names as C{unicode} instances;
            otherwise, return them as C{str}s
        @type  unicode:  C{bool}

        @return:  the set of base names of the specified Class
        @rtype:   C{str}
        """
        subclassof = self.get_triple_objects(nsprefix+':'+name, 'rdfs:subClassOf')
        bases = []
        if subclassof:
            bases = [asciify(u2q(sc)) for sc in subclassof]
        if scope:
            bases = [asciify(n.split(':')[1])
                     for n in bases if n.split(':')[0] in scope]
        else:
            bases = [asciify(n.split(':')[1])
                     for n in bases if n.split(':')[0] != 'owl']
        return list(OrderedSet(bases))

    def get_property_names(self, nsprefix):
        """
        Get the local names of all C{Property} instances in the specified
        namespace.  Names will be forced to L{str} type for use as Python
        identifiers (names).

        @param nsprefix:  the name (a.k.a. "prefix") of a namespace
        @type  nsprefix:  C{str}

        @return:  the set of local names of all Properties in the knowledgebase
        @rtype:   L{set} of L{str}
        """
        ns_pnames = []
        for p_qname in self.property_node_names:
            if nsprefix + ':' in p_qname:
                ns_pnames.append(p_qname)
        pnames = OrderedSet([asciify(p.split(':')[1]) for p in ns_pnames])
        return pnames

    def get_attrs_of_property(self, nsprefix, pname):
        """
        Get all attributes of a Property known to the KnowledgeBase and
        return a dictionary that maps them to their values.

        @param nsprefix:  the name (a.k.a. "prefix") of a namespace
        @type  nsprefix:  C{str}

        @param pname:  the local name of a Property
        @type  pname:  C{str}

        @param unicode:  if True, return names as C{unicode} instances;
            otherwise, return them as C{str}s
        @type  unicode:  C{bool}

        @return:  a dictionary of Property node attribute names to their
            values
        @rtype:   C{dict}
        """
        # TODO:  make an 'abbreviation' using the first letter + capital
        # letters in the id and check the pgef abbreviation namespace to make
        # sure it is unique (and if not ... holler or something).
        # TODO:  figure out how to process 'xsd:maxLength', which is supported
        # by Protege as part of the Manchester OWL syntax.  Example in xsd:
        # http://www.w3.org/TR/xmlschema-2/#rf-maxLength
        # <restriction base='string'>
        #   <maxLength value='50'/>
        # </restriction>
        propattrs = OrderedDict()
        pnode_qn = nsprefix + ':' + pname
        pnodeuri = get_uri(pnode_qn)
        propattrs['id_ns'], propattrs['id'] = [asciify(val)
                                       for val in pnode_qn.split(':')]
        labels = self.get_triple_objects(pnode_qn, 'rdfs:label')
        if labels:
            propattrs['name'] = asciify(labels[0])
        else:
            propattrs['name'] = asciify(propattrs['id'])
        abbrevs = self.get_triple_objects(pnode_qn, 'pgef:abbreviation')
        if abbrevs:
            propattrs['abbreviation'] = asciify(abbrevs[0])
        else:
            propattrs['abbreviation'] = '' # TODO:  algorithm to generate
                                       # unique abbreviation
        domains = self.get_triple_objects(pnode_qn, 'rdfs:domain')
        if domains:
            propattrs['domain'] = asciify(u2q(domains[0]).split(':')[1])
        else:
            propattrs['domain'] = 'Thing'
        if pnodeuri in self.subjects(RDF.type, OWL_NS.ObjectProperty):
            propattrs['is_datatype'] = False
        else:
            propattrs['is_datatype'] = True
        ranges = self.get_triple_objects(pnode_qn, 'rdfs:range')
        # hard-code Property range of "ids" to be str ...
        if propattrs['id'] in ['id', 'id_ns', 'oid', 'uri', 'version',
                           'domain', 'range']:
            propattrs['range'] = 'str'
        elif ranges:
            # if propattrs['is_datatype']:
            if pnodeuri in self.subjects(RDF.type, OWL_NS.ObjectProperty):
                propattrs['range'] = asciify(u2q(ranges[0]).split(':')[1])
            else:
                propattrs['range'] = asciify(xsd_datatypes[ranges[0]][0])
        else:
            propattrs['range'] = 'str'
        if pnodeuri in self.subjects(RDF.type, OWL_NS.FunctionalProperty):
            propattrs['functional'] = True
        else:
            propattrs['functional'] = False
        if pnodeuri in self.subjects(RDF.type,
                                     OWL_NS.InverseFunctionalProperty):
            propattrs['inverse_functional'] = True
        else:
            propattrs['inverse_functional'] = False
        # not being used atm
        # subpropertyof = self.get_triple_objects(pnode_qn,
        #                                         'rdfs:subPropertyOf')
        # if subpropertyof:
            # base = str(subpropertyof[0])  # this should not be necessary
        # else:
            # base = ''
        # owl:inverseOf identifies defined inverses of Object Properties
        inverse_of = self.get_triple_objects(pnode_qn, 'owl:inverseOf')
        if inverse_of:
            propattrs['is_inverse'] = True
            propattrs['inverse_of'] = asciify(u2q(inverse_of[0]).split(':')[1])
        else:
            propattrs['is_inverse'] = False
            propattrs['inverse_of'] = ''
        # rdfs:comment maps to pgef:definition
        definitions = self.get_triple_objects(pnode_qn, 'rdfs:comment')
        if definitions:
            propattrs['definition'] = asciify(definitions[0])
        else:
            propattrs['definition'] = ''
        comments = self.get_triple_objects(pnode_qn, 'pgef:comment')
        if comments:
            propattrs['comment'] = asciify(comments[0])
        else:
            propattrs['comment'] = ''
        return propattrs

    def get_attrs_of_class(self, nsprefix, name):
        """
        Return a dictionary mapping the names of all attribute of an ontological
        Class (C{rdfs:Class} or C{owl:Class}) to their values.  (Note:  since we
        are treating C{rdfs:Class} and C{owl:Class} the same, we are effectively
        operating in an "OWL Full" context.)

        @param nsprefix:  the name (a.k.a. "prefix") of a namespace
        @type  nsprefix:  C{str}

        @param name:  the local name of a Class node in KB
        @type  name:  C{str}

        @param unicode:  if True, return names as C{unicode} instances;
            otherwise, return them as C{str}s
        @type  unicode:  C{bool}

        @return:  a dictionary mapping names of attributes to their types
        @rtype:   L{dict}
        """
        # TODO:  make an 'abbreviation' using the first letter + capital
        # letters in the id and check the pgef abbreviation namespace to
        # make sure it is unique (and if not ... holler or something).
        cdict = OrderedDict()
        cnode_qn = nsprefix + ':' + name
        if not cnode_qn in self.node_names:
            return None
        cdict['id_ns'], cdict['id'] = cnode_qn.split(':')
        labels = self.get_triple_objects(cnode_qn, 'rdfs:label')        
        if labels:
            cdict['name'] = labels[0]
        else:
            # cdict['name'] = str(cdict['id'])  # python 2: force identifiers
            # to be python 2 str (i.e. bytes)
            cdict['name'] = cdict['id']
        abbrevs = self.get_triple_objects(cnode_qn, 'pgef:abbreviation')
        if abbrevs:
            cdict['abbreviation'] = abbrevs[0]
        else:
            cdict['abbreviation'] = u'' # TODO:  algorithm to generate
                                        # unique abbreviations
        # rdfs:comment maps to pgef:definition
        definitions = self.get_triple_objects(cnode_qn, 'rdfs:comment')
        if definitions:
            # definitions[0] is rdflib.Literal object (has no decode() method)
            # cdict['definition'] = definitions[0].decode()
            cdict['definition'] = definitions[0]
        else:
            cdict['definition'] = u''
        comments = self.get_triple_objects(cnode_qn, 'pgef:comment')
        if comments:
            # comments[0] is rdflib.Literal object (has no decode() method)
            # cdict['comment'] = comments[0].decode()
            cdict['comment'] = comments[0]
        else:
            cdict['comment'] = u''
        return cdict

    def report(self, include_ns=False):
        """
        Return a report on stuff I contain.
        """
        output = ''
        if include_ns:
            output += '=========='
            output += '\nNamespaces'
            output += '\n=========='
            for ns in list(namespaces.values()):
                output += '\n- %s:  %s' % (ns.prefix, ns.uri)
                if ns:
                    for name in ns.names:
                        output += '\n  - ' + name
                else:
                    output += '\n    [empty]'
                output += '\n' + '-'*40
            # TODO:  sort namespaces and output Classes and Properties by
            # namespace in a sorted list
        output += '\n======='
        output += '\nClasses'
        output += '\n======='
        if not self.class_node_names:
            output += '\n  - None'
            output += '\n' + '-'*40
        else:
            output += '\n%s Class nodes found:' % len(self.class_node_names)
            for node_qn in self.class_node_names:
                output += '\n  - ' + node_qn
            output += '\n' + '-'*40
        output += '\n=========='
        output += '\nProperties'
        output += '\n=========='
        if not self.property_node_names:
            output += '\n  - None\n'
            output += '\n' + '-'*40
        else:
            output += '\n%s Property nodes found:' % len(
                                                    self.property_node_names)
            for node_qn in self.property_node_names:
                output += '\n  - ' + node_qn
            output += '\n' + '-'*40
        output += '\n- end -'
        output += '\n' + '='*65
        return output

