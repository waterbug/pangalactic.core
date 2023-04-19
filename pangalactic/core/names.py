# -*- coding: utf-8 -*-
"""
Objects and services for handling identifiers, addresses, and namespaces.
"""
import inflect
import re
import xml.etree.ElementTree as ET

from collections import OrderedDict
from textwrap import wrap
from urllib.parse import urlparse

# rdflib
from rdflib.term import URIRef

from pangalactic.core                import prefs
from pangalactic.core.datastructures import OrderedSet
from pangalactic.core.meta           import (asciify, PLURALS, ATTR_EXT_NAMES,
                                             EXT_NAMES, EXT_NAMES_PLURAL)
from pangalactic.core.parametrics    import de_defz, mode_defz, parm_defz
from pangalactic.core.units          import in_si

_inf = inflect.engine()


class NS(OrderedSet):
    """
    A set of names with an id (prefix) and an address (uri).  To add a
    name n to the NS instance ns:  ns.add(n).  Note that a local namespace
    object (prefix == '') can be created, but if it is passed to
    C{register_ns}, it will be ignored (it cannot be registered, since there
    can be any number of local namespaces, one for each source dataset).

    @ivar prefix:  namespace's identifier.  By convention, the short identifier
        for a namespace is called a `prefix` because it is used in the
        `prefix:name` syntax.  If a `prefix` is not supplied, the final segment
        of its `uri` is used as the `prefix`.
    @type prefix:  C{str}

    @ivar uri:  address of the namespace.  This may be a real URI or it may
        be a faux URI (such as those permitted in RDF/OWL), but it must at
        least have the C{[scheme]://[authority][path]} structure specified
        in IETF RFC 2396.
    @type uri:  string

    @ivar version:  the namespace's version
    @type version:  C{set}

    @ivar iteration:  the namespace's iteration
    @type iteration:  C{set}

    @ivar meta_level:  the meta level of the namespace -- an integer corresponding to
        the n in the "Mn" meta levels specified for the OMG's Meta Object
        Facility.  A meta level of 10 is used to indicate that a namespace can
        apply at any meta level > 0.
    @type meta_level:  C{int}
    """
    # TODO:  decide whether an exception should be raised for attempts to
    # add a name that a Namespace already has

    def __init__(self, prefix, uri='', names=None, complete=False,
                 iteration=0, version='0', meta_level=0):
        """
        Initialize.

        @param prefix:  namespace's identifier
        @type  prefix:  C{str}

        @param uri:  the URI of the namespace
        @type  uri:  C{str}

        @param complete:  flag indicating whether the list of names is complete
        @type  complete:  C{bool}

        @param version:  the namespace's version
        @type  version:  C{set}

        @param iteration:  the namespace's iteration
        @type  iteration:  C{set}

        @param meta_level:  (see definition in ivars, above.)
        @type  meta_level:  C{int}
        """
        OrderedSet.__init__(self, iterable=names)
        if not prefix and not uri:
            raise NameError('At least one of prefix and uri must be non-empty.')
        self.uri = uri
        if prefix:
            self.prefix  = prefix
        else:
            # first try using the ultimate or penultimate path segment of uri
            try:
                self.prefix = (urlparse(uri)[2].split('/')[-1] or
                               urlparse(uri)[2].split('/')[-2])
            # if that fails, use the uri as the prefix
            except:
                self.prefix = urlparse(uri)[1]
        # if penultimate path segment is empty, use network location
        if not self.prefix:
            self.prefix = urlparse(uri)[1]
        self.complete = complete
        self.meta_level = meta_level
        self.iteration = iteration
        self.version = version

    @property
    def names(self):
        return OrderedSet(self)

    def extract(self):
        e = OrderedDict()
        e['_meta_id'] = 'Namespace'
        e.update([(a, getattr(self, a)) for a in
                  ['prefix', 'uri', 'complete', 'meta_level',
                   'iteration', 'version']])
        e['names'] = list(self)
        return e


# namespaces is the authoritative PGEF dictionary of registered namespaces,
# which maps namespace prefixes and uris to NS objects, and which the
# registry will use and continue to populate as new namespaces may be added at
# runtime.
namespaces = OrderedDict()


def register_ns(ns):
    """
    Add a `NS` to the registry's `namespaces` dictionary.

    The if clause logic says:

        - anonymous namespaces (C{namespace.prefix == ''}) are ignored.  (When a 
          L{NS} is created with an empty prefix, the uri will be used
          as the prefix, or if there is no prefix and no uri, a C{NameError} will be
          raised, so the only way to get an anonymous namespace instance is to
          somehow blank its prefix after it is created -- probably by mistake.)

        - currently registered namespaces (which have their C{prefix} in
          C{namespaces} and their instance in C{namespaces.values()}) are not
          overwritten unless the namespace being registered is "complete" (the
          assumption being that whoever is registering it is asserting that it
          is the current "complete" version, even if the one currently
          registered may also be tagged as "complete").

    @param ns:  a namespace
    @type  ns:  C{NS}
    """
    # TODO:  include local ns?  (prefix = '')
    if ns.prefix:
        namespaces[ns.prefix] = ns
    else:
        namespaces[ns.uri] = ns


def namify(s):
    """
    Transliterate a unicode string into a Python lexical name.
    """
    try:
        s = asciify(s)
        if s.istitle():
            return ''.join(s.split(' '))
        else:
            return '_'.join(s.split(' '))
    except:
        # Python 3: str IS unicode
        s = asciify(s)
        if s.istitle():
            return ''.join(s.split(' '))
        else:
            return '_'.join(s.split(' '))
    else:
        # if it's not unicode, just return it as a str
        # (python2 str=bytes or python3 unicode)
        return str(s)


def register_namespaces(rdfdataset):
    """
    Parse the namespace declarations out of an RDF dataset and create and
    register L{NS} objects for all the non-empty nsprefixes that are not
    in p.n.namespaces.  If there is a local namespace uri defined (prefix ==
    ''), check if there is also a non-empty prefix defined for that uri and if
    so, create a namespace object for it, register it, and return it as the
    local namespace; if not, create a namespace with an empty prefix and return
    that, but don't register it.  (Also make sure all names defined within the
    local namespace are added to its NS object.)

    @param rdfdataset:  the RDF dataset to be parsed, which can be either a
        file-like object (anything with a read() method) or the path to a file,
        which iterparse will open.
    @type  rdfdataset:  C{file} or C{str}

    @return:  a C{NS} instance representing the rdfdataset's local
        namespace
    """
    events = "start", "start-ns", "end-ns"
    localns = None
    localnsuri = None
    localnames = set()
    root = None
    rdfdataset_nsdict = {}
    # print('* names: calling iterparse() ...')
    for event, elem in ET.iterparse(rdfdataset, events):
        if event == 'start-ns':
            if elem[0] == '':
                localnsuri = elem[1]
            else:
                # map the prefix to its uri
                rdfdataset_nsdict[namify(elem[0])] = elem[1]
        elif event == "start":
            # check if this is a local name; if so, add it to 'localnames'
            if root is None:
                root = elem
            # note that rdf:nodeID can be used in place of rdf:about
            about = (elem.attrib.get(
                     '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
                     or elem.attrib.get(
                     '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}nodeID'))
            if (about and localnsuri is not None
                and about.startswith(localnsuri)):
                # add the local name minus the local ns uri
                localnames.add(namify(about[len(localnsuri):]))
    for prefix, uri in list(rdfdataset_nsdict.items()):
        ns = NS(prefix, uri)
        register_ns(ns)
    if localnsuri and not localns:
        localns = NS('', localnsuri, names=localnames)
        register_ns(localns)

# Define and register some reference namespaces ...

# XML Schema namespace (not available anywhere in RDF that I could find).
register_ns(NS(prefix='xsd',
               uri='http://www.w3.org/2001/XMLSchema#',
               meta_level=10,
               names=set([
               'string', 'normalizedString', 'boolean', 'decimal', 'float',
               'double', 'integer', 'nonNegativeInteger', 'positiveInteger',
               'nonPositiveInteger', 'negativeInteger', 'long', 'int', 'short',
               'byte', 'unsignedLong', 'unsignedInt', 'unsignedShort',
               'unsignedByte', 'hexBinary', 'base64Binary', 'dateTime', 'time',
               'date', 'gYearMonth', 'gYear', 'gMonthDay', 'gDay', 'gMonth',
               'anyURI', 'token', 'language', 'NMTOKEN', 'Name', 'NCName'])))

# RDF namespace
register_ns(NS(prefix='rdf',
               meta_level=10,
               uri='http://www.w3.org/1999/02/22-rdf-syntax-ns#'))

# RDFS namespace
register_ns(NS(prefix='rdfs',
               meta_level=10,
               uri='http://www.w3.org/2000/01/rdf-schema#'))

# OWL namespace
register_ns(NS(prefix='owl',
               meta_level=10,
               uri='http://www.w3.org/2002/07/owl#'))

# Dublin Core namespace
# TODO:  get the Dublin Core names ...
register_ns(NS(prefix='dc',
               meta_level=0,
               uri='http://purl.org/dc/elements/1.1/'))

# Protege (the ontology tool) namespace
# TODO:  get the Protege names ...
register_ns(NS(prefix='protege',
               meta_level=10,
               uri='http://protege.stanford.edu/plugins/owl/protege#'))

# 'test' namespace
# PGEF permanent test object namespace.  This namespace is intended to include
# only the names (`id`s) of test objects.
# FIXME:
# currently created by SQL scripts called from the script
# PanGalactic/src/sql/populate_pgerdb.sh.  NOTE:  insertion of other names into
# this namespace may cause some unit tests to fail.
register_ns(NS(prefix='test',
               meta_level=0,
               uri='http://pangalactic.us/test/'))

# 'sandbox' namespace
# PGEF permanent sandbox (demo) namespace.  This namespace is intended to
# include the `id`s of demo objects included in the initial set up of
# PGER -- currently created by SQL scripts called from the script
# PanGalactic/src/sql/populate_pgerdb.sh.  NOTE:  insertion of other names into
# this namespace should be okay (if not, it's a bug ;).
register_ns(NS(prefix='sandbox',
               meta_level=0,
               uri='http://pangalactic.us/sandbox/'))

# 'testtmp' namespace
# PGEF temporary test object namespace (for objects created during test runs).
# NOTE:  insertion of other names into this namespace may cause some unit tests
# to fail.
register_ns(NS(prefix='testtmp',
               meta_level=0,
               uri='http://pangalactic.us/test/tmp/'))

# 'pgefobjects' namespace
# NS for PGEF reference objects (e.g., the 'admin' Person object).
register_ns(NS(prefix='pgefobjects',
               meta_level=0,
               uri='http://pangalactic.us/objects/'))

# 'pgefnamespaces' namespace
# NS for namespace prefixes that don't have a namespace ... :)
register_ns(NS(prefix='pgefns',
               meta_level=10,
               uri='http://pangalactic.us/namespaces/'))

# 'world' namespace
# A completely generic namespace for use when no specific namespace seems
# appropriate -- should be used with the awareness that it may get "crowded"
# eventually ... ;)
register_ns(NS(prefix='world',
               meta_level=0,
               uri='http://earth.milkyway.universe/'))

# 'mime' namespace
# MIME media-types
register_ns(NS(prefix='mime',
               meta_level=0,
               uri='http://www.iana.org/assignments/media-types/'))


def u2q(uri):
    """
    Get the qname for a URI.

    @param uri:  a URI
    @type  uri:  C{str}
    """
    slash = uri.rfind('/')
    hash_ = uri.rfind('#')
    if slash == -1 and hash_ == -1:
        qname = uri
    else:
        if slash > hash_:
            ns_uri = uri[:slash+1]
            name = uri[slash+1:]
        else:
            ns_uri = uri[:hash_+1]
            name = uri[hash_+1:]
        # TODO:  create 'reversible mapping' class to use for 'namespaces'
        prefix_by_uri = {ns.uri : ns.prefix for ns in list(namespaces.values())}
        # if prefix not found, use '' (local ns)
        prefix = prefix_by_uri.get(ns_uri, '')
        qname = ':'.join([prefix, name])
    return qname


def get_prefix(uri):
    return u2q(uri).split(':')[0]


def q2u(qname):
    """
    Get the URI for a qname.

    @param qname:  a string of the form C{'[prefix:]localname'}
    @type  qname:  C{str}
    """
    if ':' not in qname:
        if not '#' in qname:
            uri = '#' + qname
        else:
            raise ValueError('invalid qname')
    else:
        prefix, name = qname.split(':')
        if prefix in namespaces:
            ns = namespaces[prefix]
            if ns.uri.endswith('/') or ns.uri.endswith('#'):
                uri = ''.join([ns.uri, name])
            else:
                uri = ''.join([ns.uri, '#', name])
        else:
            raise ValueError('unknown prefix: {}'.format(prefix))
    return URIRef(uri)


def q2eturi(qname):
    """
    Get the ElementTree-style URI for a qname -- i.e., using {}.

    @param qname:  a string of the form C{'[prefix:]localname'}
    @type  qname:  C{str}
    """
    if ':' not in qname:
        if not '#' in qname:
            uri = '#' + qname
        else:
            raise ValueError('invalid qname')
    else:
        prefix, name = qname.split(':')
        if prefix in namespaces:
            ns = namespaces[prefix]
            uri = ''.join(['{', ns.uri, '}', name])
        else:
            raise ValueError('unknown prefix: {}'.format(prefix))
    return uri


def get_uri(identifier):
    """
    Get the address (a.k.a. URI) corresponding to an identifier.  If the
    identifier contains '://', it is taken to be a URI; else, if it
    contains ':', it is taken to be a qname; otherwise, it is taken to be a
    local name.

    @param identifier:  can be a local name (aka 'lname' -- a simple string), a
        qname ('prefix:lname'), or a URI string.
    @type  identifier:  string
    """
    if '://' in identifier or identifier.startswith('#'):
        # identifier is a URI
        uri = identifier
    else:
        # identifier is either a qname or a local name
        uri = q2u(identifier)
    return URIRef(uri)

def get_external_name(cname):
    return EXT_NAMES.get(cname, to_external_name(cname))

def get_external_name_plural(cname):
    return EXT_NAMES_PLURAL.get(cname,
                                to_external_name(cname)+'s')

def get_attr_ext_name(cname, aname):
    return ATTR_EXT_NAMES.get(cname, {}).get(aname, ' '.join(aname.split('_')))

def to_external_name(cname):
    """
    Convert a standard metaobject (class, interface, or schema) camelcase name
    into a user-interface-friendly name.

    @param cname: a camelcase metaobject name
    @type  cname: L{str}

    @return: an "external name"
    @rtype:  L{str}
    """
    patt = re.compile('([A-Z])')
    l = re.split(patt, cname)
    parts = l[1:]
    if 0 < len(parts) < 3:
        vname = parts[0] + parts[1]
    elif len(parts) > 2:
        vname = parts[0] + parts[1]
        i = 2
        while i < len(parts):
            if i % 2 == 0:
                vname += ' '
            vname += parts[i]
            i += 1
    return vname

def to_table_name(cname):
    """
    Convert a standard (camelcase) class name into an underscore-delimited,
    lowercase table name.

    @param cname: a camelcase class name
    @type  cname: L{str}

    @return: a table name
    @rtype:  L{str}
    """
    patt = re.compile('([A-Z])')
    l = re.split(patt, cname)
    parts = l[1:]
    if 0 < len(parts) < 3:
        tname = (parts[0] + parts[1]).lower()
    elif len(parts) > 2:
        tname = parts[0] + parts[1]
        i = 2
        while i < len(parts):
            if i % 2 == 0:
                tname += '_'
            tname += parts[i]
            i += 1
        tname = tname.lower()
    return tname +  '_'

def pname_to_header_label(pname, headers_are_ids=False, project_oid=None):
    """
    Convert a property name, data element id, or parameter id into a
    header-friendly name.

    Args:
        pname: (str): a property name, data element id, or parameter id

    Keyword Args:
        project_oid (str):  oid of the current project
        headers_are_ids (bool):  use ids instead of names

    returns: external name (str)
    """
    pd = parm_defz.get(pname)
    de_def = de_defz.get(pname, '')
    if pd:
        units = prefs.get('units', {}).get(pd['dimensions'], '') or in_si.get(
                                                         pd['dimensions'], '')
        if units:
            units = '(' + units + ')'
        if headers_are_ids:
            return '  \n  '.join([pname, units])
        else:
            return '  \n  '.join(wrap(pd['name'], width=7,
                                 break_long_words=False) + [units])
    elif de_def:
        if headers_are_ids:
            return pname
        else:
            return '  \n  '.join(wrap(de_def['name'], width=7,
                                 break_long_words=False))
    elif project_oid:
        modes = (mode_defz.get(project_oid) or {}).get('modes')
        if modes and pname in modes:
            units = prefs.get('units', {}).get('power') or 'W'
            if units:
                units = '(' + units + ')'
            return '  \n  '.join(wrap(pname, width=7,
                                 break_long_words=False) + [units])
    parts = ' '.join(pname.split('_'))
    return ' \n '.join(wrap(parts, width=7, break_long_words=False))

def to_media_name(cname):
    """
    Convert a standard (camelcase) class name into a media name (primarily for
    use with pyqt drag and drop data).

    @param cname: a camelcase class name
    @type  cname: L{str}

    @return: a media name
    @rtype:  L{str}
    """
    patt = re.compile('([A-Z])')
    l = re.split(patt, cname)
    parts = l[1:]
    if 0 < len(parts) < 3:
        tname = (parts[0] + parts[1]).lower()
    elif len(parts) > 2:
        tname = parts[0] + parts[1]
        i = 2
        while i < len(parts):
            if i % 2 == 0:
                tname += '-'
            tname += parts[i]
            i += 1
        tname = tname.lower()
    return "application/x-pgef-" + tname

def to_collection_name(cname):
    """
    Convert a standard metaobject (class, interface, or schema) camelcase name
    into the name of an attribute that refers to a collection of that kind of
    object -- e.g.: 'Class' -> 'classes', 'Person' -> 'people', etc.

    @param cname: a camelcase metaobject name
    @type  cname: L{str}

    @return: a table name
    @rtype:  L{str}
    """
    return str(to_table_name(PLURALS.get(
               cname, _inf.plural(cname)))[:-1])

def to_class_name(table_name):
    """
    Convert an underscore-delimited, lowercase table name into a
    metaobject (class, interface, or schema) camelcase name.

    @param table_name: table name
    @type  table_name: L{str}

    @return: C{Interface} name
    @rtype:  L{str}
    """
    tn = table_name[:-1] # drop trailing '_'
    parts = tn.split('_')
    i = 0
    metaobject_name = ''
    while i < len(parts):
        metaobject_name += parts[i].capitalize()
        i += 1
    return str(metaobject_name)

def classnamify(base, tablename, table):
    """
    Specifically for use as the value of SqlAlchemy AutomapBase argument
    `classname_for_table`.  Clearly, it is simply a wrapper for
    `to_class_name`, converting a table name (with trailing underscore) to
    the corresponding class name.
    """
    return to_class_name(tablename)

def get_data_element_definition_oid(deid):
    """
    Return the oid of the DataElementDefinition for the specified data element
    id.

    Args:
        deid (str): the 'id' defined in the DataElementDefinition
    """
    return 'pgef:DataElementDefinition.' + deid

def get_parameter_definition_oid(variable):
    """
    Return the oid of the ParameterDefinition for the specified variable.

    Args:
        variable (str): the variable defined by the ParameterDefinition
    """
    return 'pgef:ParameterDefinition.' + variable

def get_parameter_context_oid(pcid):
    """
    Return the oid of the ParameterContext with the specified 'id'.

    Args:
        pcid (str): the ParameterContext 'id'
    """
    return 'pgef:ParameterContext.' + pcid

def get_state_oid(sid):
    """
    Return the oid of the State with the specified 'id'.

    Args:
        sid (str): the State 'id'
    """
    return 'pgef:State.' + sid

def get_ra_id(ra_context_id, role_id, fname, mi, lname):
    """
    Create an 'id' for a new RoleAssignment.

    Args:
        ra_context_id: 'id' of the role_assignment_context (Org)
        role_id:  the 'id' of the Role
        fname:  first name of the Person
        mi:  middle name or initial of the Person
        lname:  last name of the Person
    """
    if ra_context_id:
        return '-'.join([ra_context_id, role_id,
                         '_'.join([lname, fname, mi])])
    else:
        return '-'.join([role_id, '_'.join([lname, fname, mi])])

def get_next_ref_des(assembly, component, prefix=None, product_type=None):
    """
    Get the next reference designator for the specified assembly and component.

    This function assumes that reference designators are strings of the form
    'prefix-n', where 'n' can be cast to an integer.

    Args:
        assembly (Product): the product containing the component
        component (Product): the constituent product

    Keyword Args:
        prefix (str): a string to be used as the prefix of the reference
            designator
        product_type (ProductType): a product type to use if component is None
            or does not have a product_type
    """
    prefix = ''
    if getattr(component, 'product_type', None):
        prefix = (component.product_type.abbreviation or
                  component.product_type.name)
    if not prefix and product_type:
        prefix = product_type.abbreviation or product_type.name
    if not prefix:
        prefix = 'Generic'
    acus = assembly.components
    if acus:
        rds = [acu.reference_designator for acu in acus]
        # product_type abbreviation should not contain '-', but it can
        all_prefixes = [(''.join(rd.split('-')[:-1])) for rd in rds if rd]
        these_prefixes = [p for p in all_prefixes if p == prefix]
        new_nbr = len(these_prefixes) + 1
        refdes = prefix + '-' + str(new_nbr)
        while 1:
            if refdes not in rds:
                break
            else:
                new_nbr += 1
                refdes = prefix + '-' + str(new_nbr)
        return refdes
    else:
        return prefix + '-1'

def get_ra_name(ra_context_id, role_id, fname, mi, lname):
    """
    Create a 'name' for a new RoleAssignment.

    Args:
        ra_context_id:  the id of the ra 'context' (Org or Project)
        role_id:  the id of the assigned Role
        fname:  first name of the assignee
        mi:  middle initial of the assignee
        lname:  last name of the assignee
    """
    if ra_context_id:
        return ': '.join([ra_context_id, role_id,
                         ' '.join([lname, fname, mi])])
    else:
        return ': '.join([role_id, ' '.join([lname, fname, mi])])

def get_acu_id(assembly_id, ref_des):
    """
    Create an 'id' for a new Acu.

    Args:
        assembly_id:  the 'id' of the assembly (Product)
        ref_des:  the reference_designator of the Acu, created using
            get_next_ref_des()
    """
    return assembly_id + '-' + '-'.join(ref_des.split(' '))

def get_acu_name(assembly_name, ref_des):
    """
    Create a 'name' for a new Acu.

    Args:
        assembly_name:  the 'name' of the assembly (Product)
        ref_des:  the reference_designator of the Acu, created using
            get_next_ref_des()
    """
    return assembly_name + ' : ' + ref_des

def get_link_name(link):
    """
    Get a canonical name for a "link" (an Acu or ProjectSystemUsage).
    Used in generating the Modes Table (system power modes).
    """
    cname = link.__class__.__name__
    if cname == 'ProjectSystemUsage':
        # link is a psu
        sys_role = getattr(link, 'system_role', 'no role') or 'no role'
        sys_name = getattr(link.system, 'name', 'no name') or 'no name'
        return '[' + sys_role + '] ' + sys_name
    if cname == 'Acu':
        # link is an acu
        return '[' + link.reference_designator + '] ' + link.component.name
    else:
        return '[unknown]'

def get_link_object(link):
    """
    Get the "child" object for a "link" (an Acu or ProjectSystemUsage).
    Used in generating the Modes Table (system power modes).
    """
    if hasattr(link, 'system'):
        # link is a psu
        return link.system
    elif hasattr(link, 'component'):
        # link is an acu
        return link.component
    else:
        return None

def get_mel_item_name(item):
    """
    Create a unique name for a line item in a MEL (Master Equipment List).

    Args:
        item (Product, Acu, or ProjectSystemUsage):  the MEL line item
    """
    # newlines *should* not occur in a product name but have been known to --
    # hence the '\n' replacements ...
    if hasattr(item, 'component'):
        # item is an Acu
        name = (getattr(item.component, 'name', '') or 'unknown').replace(
                                                        '\n', ' ').strip()
        if item.reference_designator:
            return '[' + item.reference_designator + '] ' + name
        else:
            return name
    elif hasattr(item, 'system'):
        # item is an ProjectSystemUsage
        name = (getattr(item.system, 'name', '') or 'unknown').replace(
                                                        '\n', ' ').strip()
        if item.system_role:
            return '[' + item.system_role + '] ' + name
        else:
            return name
    else:
        # item is a Product
        name = (getattr(item, 'name', '') or 'unknown').replace(
                                                        '\n', ' ').strip()
        return name

def get_rel_id(context_id, role_id):
    """
    Create an 'id' for a new Relation.

    Args:
        context_id (str):  the 'id' of related context (a Requirement, e.g.)
        role_id (str):  the role of the Relation in the specified context
    """
    return context_id + '-' + role_id + '-relation'

def get_rel_name(context_name, role_name):
    """
    Create a name for a new Relation.

    Args:
        context_name (str):  the name of related context (a Requirement, e.g.)
        role_name (str):  its role name in the specified context
    """
    return context_name + ' ' + role_name + ' Relation'

def get_parm_rel_id(rel_id, pid):
    """
    Create an 'id' for a new ParameterRelation.

    Args:
        rel_id (str):  the 'id' of related Relation
        pid (str):  the parameter id of the related ParameterDefinition
    """
    return rel_id + '-' + pid + '-parm-rel'

def get_parm_rel_name(rel_name, pname):
    """
    Create a name for a new ParameterRelation.

    Args:
        rel_name (str):  the name of related Relation
        pname (str):  the parameter name of the related ParameterDefinition
    """
    return rel_name + ' ' + pname + ' Parameter Relation'

def get_next_port_seq(obj, port_type):
    """
    Get the next sequence number for an object and a type of port.

    Args:
        obj (Modelable):  object that may have ports
        port_type (PortType):  the PortType to be considered
    """
    if not getattr(obj, 'ports', None):
        return 0
    try:
        seq_ints = [int(port.id.split('-')[-1]) for port in obj.ports
                    if port.type_of_port is port_type]
        if seq_ints:
            return max(seq_ints) + 1
        else:
            return 0
    except:
        return 0

def get_port_id(of_product_id, port_type_id, seq):
    """
    Create an id for a new Port.

    Args:
        of_product_id (str):  the id of the port's "of_product" (Product)
        port_type_id (str):  the id of the port's type_of_port (PortType)
        seq (int):  the sequence number assigned to the port
    """
    return '-'.join([of_product_id, port_type_id, str(seq)])

def get_port_name(of_product_name, port_type_name, seq):
    """
    Create a name for a new Port.

    Args:
        of_product_name (str):  the name of the port's "of_product" (Product)
        port_type_name (str):  the name of the port's type_of_port (PortType)
        seq (int):  the sequence number assigned to the port
    """
    return ' '.join([of_product_name, port_type_name, str(seq)])

def get_port_abbr(port_type_abbr, seq):
    """
    Create an abbreviation for a new Port.

    Args:
        port_type_abbr (str):  the abbreviation of the port's type_of_port
            (PortType)
        seq (int):  the sequence number assigned to the port
    """
    return '-'.join([port_type_abbr, str(seq)])

def get_flow_id(start_context_id, start_port_id, end_context_id, end_port_id):
    """
    Create a unique id for a new Flow.

    Args:
        start_context_id:  the id of the start_port_context
        start_port_id:  the id of the start_port
        end_context_id:  the id of the end_port_context
        end_port_id:  the id of the end_port
    """
    return '-'.join(['flow', start_context_id, start_port_id, end_context_id,
                     end_port_id])

def get_flow_name(start_context_name, start_port_name, end_context_name,
                  end_port_name):
    """
    Create a name for a new Flow.

    Args:
        start_context_name:  the name of the start_port_context
        start_port_name:  the name of the start_port
        end_context_name:  the name of the end_port_context
        end_port_name:  the name of the end_port
    """
    return ' '.join(['Flow:', start_context_name, start_port_name, 'to',
                     end_context_name, end_port_name])

def display_id(obj):
    """
    Return a string to display as 'id' that will include, if `obj` is an
    instance of Product, its 'version' string if it is not null.

    Args:
        obj (Identifiable):  object whose id is to be displayed
    """
    version = getattr(obj, 'version', None)
    obj_id = getattr(obj, 'id', None) or 'unknown'
    if version:
        return obj_id + '.v.' + version
    else:
        return obj_id

def get_display_name(obj):
    """
    Return a string to display as 'name' that will include, if `obj` is an
    instance of Product, its 'version' string if it is not null.

    Args:
        obj (Identifiable):  object whose name is to be displayed
    """
    version = getattr(obj, 'version', None)
    name = getattr(obj, 'name', None) or 'Unidentified'
    if version:
        return ' v. '.join([name, version])
    else:
        return name

def get_block_model_id(obj):
    """
    Get canonical 'id' for a pgx block model.

    Args:
        obj (Modelable):  the object that is the subject of the model
    """
    return '_'.join([display_id(obj), 'pgx_ibd'])

def get_block_model_name(obj):
    """
    Get canonical 'name' for a pgx block model.

    Args:
        obj (Modelable):  the object that is the subject of the model
    """
    return ' '.join([get_display_name(obj), 'Pgx IBD'])

def get_block_model_file_name(obj):
    """
    Get canonical file name for a pgx block model.

    Args:
        obj (Modelable):  the object that is the subject of the model
    """
    return get_block_model_id(obj) + '.json'

