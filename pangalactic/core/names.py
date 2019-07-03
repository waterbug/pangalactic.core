# -*- coding: utf-8 -*-
"""
Objects and services for handling identifiers, addresses, and namespaces.
"""
from collections import OrderedDict
from unidecode import unidecode
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from rdflib.term import URIRef

from pangalactic.core.datastructures import OrderedSet


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


def transliterate_unicode(s):
    """
    Transliterate a unicode string into a Python lexical name.
    """
    try:
        s = unidecode(s)
        if s.istitle():
            return unicode(''.join(s.split(' ')))
        else:
            return unicode('_'.join(s.split(' ')))
    except:
        # Python 3: str IS unicode
        s = unidecode(s)
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
    print('* names: calling iterparse() ...')
    for event, elem in ET.iterparse(rdfdataset, events):
        if event == 'start-ns':
            if elem[0] == '':
                localnsuri = elem[1]
            else:
                # map the (transliterated) prefix to its uri
                rdfdataset_nsdict[transliterate_unicode(elem[0])] = elem[1]
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
                # add the (transliterated) local name minus the local ns uri
                localnames.add(transliterate_unicode(about[len(localnsuri):]))
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

