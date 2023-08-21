# -*- coding: utf-8 -*-
"""
The Pan Galactic Tach Registry
"""
# Python
import glob, os, pkgutil, shutil

# PanGalactic
from pangalactic.core.datastructures import OrderedSet
from pangalactic.core.kb             import PanGalacticKnowledgeBase as KB
from pangalactic.core.kb             import get_ontology_prefix
from pangalactic.core.meta           import (dump_metadata, load_metadata,
                                             MAX_LENGTH, PGEF_PROPS_ORDER,
                                             READONLY)
from pangalactic.core.names          import namespaces


class FakeLog(object):
    """
    Fake logger to print log messages if we are run without a logger.
    """
    def info(self, s):
        print(s)
    def debug(self, s):
        print(s)


class AntiLog(object):
    """
    Fake logger to NOT print log messages if we are run without a logger.
    """
    def info(self, s):
        pass
    def debug(self, s):
        pass


datatypes = {
    # (is_datatype, range, functional) : field datatype (schema: 'field_type')
    (True, 'bool', True)      : bool,
    (True, 'bool', False)     : set,
    (True, 'int', True)       : int,
    (True, 'int', False)      : set,
    (True, 'float', True)     : float,
    (True, 'float', False)    : set,
    (True, 'unicode', True)   : str, # narrative -> text (multi-line)
    (True, 'unicode', False)  : set,
    (True, 'bytes', True)     : bytes,
    (True, 'str', True)       : str,
    (True, 'str', False)      : set,
    (True, 'date', True)      : str,
    (True, 'date', False)     : set,
    (True, 'time', True)      : str,
    (True, 'time', False)     : set,
    (True, 'datetime', True)  : str,
    (True, 'datetime', False) : set,
    (False, None, True)       : str,
    (False, None, False)      : set
    }


def property_to_field(name, pe):
    """
    Create a field dict from a property extract.  The field dict has the
    following form (terminology adopted from django-metaservice api):

     'id'            : (str) the name of the field
     'id_ns'         : (str) namespace in which name of the field exists
     'field_type'    : the field type, either a python datatype or "object"
     'local'         : (bool)  True -> locally defined; False -> inherited
     'related_cname' : (str) for fk fields, name of the related class
     'functional'    : (bool)  True -> single-valued
     'range'         : python datatype name or, if object, related class name
     'inverse_functional' : (bool)  True -> one-to-one
     'is_inverse'    : (bool)  True -> property is an inverse ("backref")
     'inverse_of'    : (str) name of property of which this one is an inverse
     'max_length'    : (int) maximum length of a string field
     'null'          : (bool) whether the field can be null
     'editable'      : (bool) opposite of read-only
     'unique'        : (bool) same as the sql concept
     'external_name' : (str) name displayed in user interfaces
     'definition'    : (str) definition of the field

    The 'fields' key in a schema dict will consist of a dict that maps
    field names to field dicts of this form.
    """
    field = {}
    field['id'] = pe['id']
    field['id_ns'] = pe['id_ns']
    field['definition'] = pe['definition']
    field['functional'] = pe['functional']
    field['range'] = pe['range']
    field['editable'] = not name in READONLY
    field['external_name'] = ' '.join(pe['id'].split('_'))
    if pe['is_datatype']:
        field['field_type'] = datatypes[(pe['is_datatype'],
                                         pe['range'],
                                         pe['functional'])]
        field['is_inverse'] = False
        field['inverse_of'] = ''
        field['max_length'] = MAX_LENGTH.get(pe['id'], 80)
    else:
        field['field_type'] = 'object'
        field['related_cname'] = pe['range']
        field['is_inverse'] = pe['is_inverse']
        field['inverse_of'] = pe['inverse_of']
    return field


# schemas:  a module-level dictionary containing all class schemas.
# It is recreated at startup from the ontology, so unnecessary to cache it.
#
# Its structure is:
#
#      {oid: schema}
#
# where "schema" is in the format specified in
# _update_schemas_from_extracts():
#
#   {'field_names'    : [field names in the order defined in the model],
#    'base_names'     : [names of immediate superclasses for the schema],
#    'definition'     : [ontological class definition],
#    'pk_name'        : [name of the primary key field for this model],
#    'fields' : {
#       field-1-name  : { [field-1-attrs] },
#       field-2-name  : { [field-2-attrs] },
#       ...           
#       field-n-name  : { [field-n-attrs] }
#       }
#   }
#
# ... and the field (property) schemas are in the format specified in
# property_to_field() (see below)

schemas = {}


# matrix:  a module-level dictionary containing all class instances
# and their attributes, accessed by Thing instances.  Its structure is:
#
#      {oid: object structure}
#
# where "object structure" is a dict in the format of a serialized object but
# without the "parameters" and "data_elements" sub-dictionaries. It is
# persisted in the file 'matrix.json' in the application home directory -- see
# the functions 'save_matrix' and 'load_matrix'.

matrix = {}


class Tachistry:
    """
    The Tachistry maintains dictionaries of the schemas used to specify
    the PGEF classes.

    Attributes:
        home (str):  application home directory.  [default: `pangalactic_home`]
        cache_path (str):  directory in which serialized schemas will be cached
        onto_path (str):  directory containing app ontology OWL files
            [default: `apps` -- other values are used only for testing]
        apps (list of str):  list of loaded apps (app ontology prefixes)
        kb (p.meta.kb.KB):  An RDF graph containing the app ontology
        ces (dict):  A mapping of `meta_id`s to `Class` extracts
        pes (dict):  A mapping of `meta_id`s to `Property` extracts
        nses (dict):  A mapping of namespace prefixes to namespace extracts
    """
    def __init__(self, home=None, cache_path='cache', onto_path='onto',
                 apps=None, log=None, version='', debug=False, console=False,
                 force_new_core=False):
        """
        Initialize the tachistry.

        Keyword Args:
            home (None or str):  if not `None`, indicates the registry should
                use this path as its home directory.
            cache_path (str):  directory containing serialized schemas
                [default: `cache` -- other values are used only for testing]
            onto_path (str):  directory containing the ontology OWL files
                [default: `onto` -- other values are used only for testing]
            log (logger):  logger instance passed in by orb (or None)
            version (str):  [optional] current version tag
            debug (bool):  if True, set logging to `debug` level
            console (bool):  if True, send log msgs to stdout
            force_new_core (bool):  if `True`, the registry will rebuild the
                pgef core schemas from the pgef.owl file at start-up, even if
                cached schemas exist.  (The source pgef OWL file, `pgef.owl` is
                in p.meta.ontology and at initial registry startup will be
                written to the pangalactic home directory for use by app
                ontology developers)
        """
        # NOTE:  uncomment these if more primitive debugging is required ...
        # print 'Smegistry initializing with:'
        # print '  home           =', str(home)
        # print '  cache_path     =', str(cache_path)
        # print '  onto_path      =', str(onto_path)
        # print '  apps           =', str(apps)
        # print '  debug          =', str(debug)
        # print '  console        =', str(console)
        # print '  force_new_core =', str(force_new_core)
        # assume we got caches until proven otherwise
        self.version = version
        self.got_cache = True
        self.got_pgef_cache = True
        if log:
            self.log = log
        else:
            # log messages neither logged nor printed
            self.log = AntiLog()
        # create home directory and subdirs
        if home is not None:
            self.home = os.path.abspath(home)
        else:
            self.home = os.environ.get('PANGALACTIC_HOME',
                                       os.path.abspath('pangalactic_home'))
        if not os.path.exists(self.home):
            os.mkdir(self.home)
        self.log.info('* [registry] home directory: {}'.format(self.home))
        self.cache_path = os.path.join(self.home, cache_path)
        if not os.path.exists(self.cache_path):
            self.got_cache = False
            os.makedirs(self.cache_path)
        self.pgef_cache_path = os.path.join(self.home, cache_path, 'pgef')
        if not os.path.exists(self.pgef_cache_path):
            self.got_pgef_cache = False
            os.makedirs(self.pgef_cache_path)
        # copy canonical pgef OWL file to onto dir (this file is only used to
        # create the KB instance -- once that is done, pgef.owl is left there
        # as a reference for the interested user, who might, for example, want
        # to create an app ontology based on it.
        # TODO:  put a README in the home dir that explains what the files are
        self.onto_path = os.path.join(self.home, onto_path)
        if not os.path.exists(self.onto_path): 
            os.makedirs(self.onto_path)
        pgef_owl_path = str(os.path.join(self.onto_path, 'pgef.owl'))
        f = open(pgef_owl_path, 'w')
        f.write(str(pkgutil.get_data('pangalactic.core.ontology',
                                     'pgef.owl').decode('utf-8')))
        f.close()
        # self.log.debug('* not installed; using pgef.owl in home dir.')
        self.apps_dict = {}   # not currently used
        self.apps = []
        self.ces = {}
        self.pes = {}
        self.nses = {}
        # create the KB (knowledgebase) and initialize the registry's schemas,
        # which will be used in generating the database and app classes
        # self.log.debug('* [registry] creating KB from pgef.owl source ...')
        # self.log.debug('             (pgef.owl path: "{}")'.format(
                                                            # pgef_owl_path))
        self.kb = KB(pgef_owl_path)
        self._create_pgef_core_meta_objects(use_cache=(not force_new_core))
        # check for app ontologies -- if any are found, load them
        app_onto_files = [n for n in os.listdir(self.onto_path)
                          if n != 'pgef.owl']
        if app_onto_files:
            for fname in app_onto_files:
                if fname.endswith('.owl'):
                    self.build_schemas_from_ontology(
                                    os.path.join(self.onto_path, fname))

    def _create_pgef_core_meta_objects(self, use_cache=True):
        """
        Build schemas and classes based on the pgef ontology.

        @param use_cache:  if True, check for cached pgef core models; if any
            exist, the registry will rebuild the pgef core meta objects from
            the cached models; otherwise, it will rebuild them using pgef.owl.
        @type  use_cache:  `bool`
        """
        # self.log.debug('* creating pgef core meta objects')
        # [1] create extracts or get them from cache
        if use_cache:
            if self.got_pgef_cache:
                # self.log.debug('  - restoring meta objects from cache.')
                self._get_extracts_from_cache()
            else:
                # self.log.debug('  - pgef cache needs rebuilding.')
                # TODO:  display a "processing" message to user with "Building
                # application classes from ontology"
                # create extracts of pgef core meta objects from owl source files
                self._create_extracts_from_source()
        else:
            # TODO:  make sure cache is cleared (remove files)
            self._create_extracts_from_source()
        # [2] create schemas from the extracts
        self._update_schemas_from_extracts()
        # [3] create pgef core metaobjects in order from the schemas
        # self._update_classes_from_schemas()

    def _create_extracts_from_source(self, source=None):
        """
        Create {Class|Property|Namespace} extracts corresponding to the
        principal namespace or model in the source.  This function rebuilds or
        adds to the "extract caches":  `self.nses` (namespace extracts),
        `self.pes` (property extracts), and `self.ces` (class extracts).

        Keyword Args:
            source (str):  if None, create extracts for the 'pgef' namespace
                from its source files; otherwise, source must be the path to an
                OWL file.
        """
        # self.log.debug('* creating extracts from source')
        if source == None:
            # self.log.debug('   + source:  pgef.owl')
            nsprefix = 'pgef'
        else:
            # self.log.debug('   + source:  %s' % str(source))
            nsprefix = get_ontology_prefix(source)
            if hasattr(source, 'read'):
                # if source is file-like, must reset to beginning
                source.seek(0)
            self.kb.parse(source)
        # self.log.debug('   + nsprefix = %s' % str(nsprefix))
        new_pes = {}
        new_ces = {}
        pnames = self.kb.get_property_names(nsprefix)
        # self.log.debug('   + pnames:  %s' % pnames)
        for pname in pnames:
            attrs = self.kb.get_attrs_of_property(nsprefix, pname)
            e = {}
            e['oid'] = ':'.join([attrs['id_ns'], attrs['id']])
            e['_meta_id'] = 'Property'
            e.update(attrs)
            # add 'oid' and 'uri', which need to be generated from 'id' and
            # 'id_ns' (and we don't want them as properties of the OWL
            # properties anyway)
            new_pes[pname] = e
        cnames = self.kb.get_class_names(nsprefix)
        # self.log.debug('   + cnames:  %s' % cnames)
        for cname in cnames:
            attrs = self.kb.get_attrs_of_class(nsprefix, cname)
            e = {}
            e['oid'] = ':'.join([attrs['id_ns'], attrs['id']])
            e['_meta_id'] = 'Class'
            e['bases'] = self.kb.get_base_names(nsprefix, cname)
            e.update(attrs)
            new_ces[cname] = e
        # create Namespace extracts for all known namespaces (the current ns
        # has already been registered while reading the source -- by
        # kb.get_ontology_prefix(source) -- so it is already in the
        # 'namespaces' dictionary)
        # TODO:  support app ontology "versions"? ... possibly giving them
        # different prefixes, or else naming the extract files differently
        # (e.g. using the version).
        new_nses = dict([(n.prefix, n.extract())
                          for n in namespaces.values() if n.prefix])
        # serialize the property and class extracts to the cache
        cache_path = os.path.join(self.cache_path, nsprefix)
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        ns_cache_path = os.path.join(cache_path, 'namespaces')
        if not os.path.exists(ns_cache_path):
            os.makedirs(ns_cache_path)
        property_cache_path = os.path.join(cache_path, 'properties')
        if not os.path.exists(property_cache_path):
            os.makedirs(property_cache_path)
        class_cache_path = os.path.join(cache_path, 'classes')
        if not os.path.exists(class_cache_path):
            os.makedirs(class_cache_path)
        for meta_id, ne in new_nses.items():
            dump_metadata(ne, os.path.join(
                                ns_cache_path, meta_id + '.json'))
        for meta_id, pe in new_pes.items():
            dump_metadata(pe, os.path.join(
                                property_cache_path, meta_id + '.json'))
        for meta_id, ce in new_ces.items():
            dump_metadata(ce, os.path.join(
                                class_cache_path, meta_id + '.json'))
        # NOTE (CAVEAT!):  if there are any name collisions, new names will
        # clobber existing ones
        self.nses.update(new_nses)
        self.pes.update(new_pes)
        self.ces.update(new_ces)

    def _get_extracts_from_cache(self):
        """
        Recreate the extract dictionaries (`nses`, `ces`, and `pes`) from their
        cached json serializations.
        """
        # TODO:  register the namespaces in kb after getting their extracts
        for ns_prefix in os.listdir(self.cache_path):
            prefix_cache = os.path.join(self.cache_path, ns_prefix)
            nss_dir = os.path.join(prefix_cache, 'namespaces')
            properties_dir = os.path.join(prefix_cache, 'properties')
            classes_dir = os.path.join(prefix_cache, 'classes')
            if os.path.exists(nss_dir):
                for file_path in os.listdir(nss_dir):
                    e = load_metadata(os.path.join(nss_dir, file_path))
                    self.nses[e['prefix']] = e
            if os.path.exists(properties_dir):
                for file_path in os.listdir(properties_dir):
                    pe = load_metadata(os.path.join(properties_dir, file_path))
                    self.pes[pe['id']] = pe
            if os.path.exists(classes_dir):
                for file_path in os.listdir(classes_dir):
                    ce = load_metadata(os.path.join(classes_dir, file_path))
                    self.ces[ce['id']] = ce

    def _update_schemas_from_extracts(self):
        """
        Update the application class schemas (`schemas`) from any
        registered ontology class extracts (`self.ces`) for which schemas are
        not registered.  Schemas take the following form (similar to the
        django-metaservice api):

        {'field_names'    : [field names in the order defined in the model],
         'base_names'     : [names of immediate superclasses for the schema],
         'definition'     : [ontological class definition],
         'pk_name'        : [name of the primary key field for this model],
         'fields' : {
            field-1-name  : { [field-1-attrs] },
            field-2-name  : { [field-2-attrs] },
            ...           
            field-n-name  : { [field-n-attrs] }
            }
        }

        ... where the structure of the field dicts (`field-n-attrs`) is
        documented in `pangalactic.core.meta.property_to_field()`.
        """
        # self.log.debug('* updating schemas from extracts')
        to_build = [meta_id for meta_id in self.metaobject_build_order()
                    if meta_id not in schemas]
        for meta_id in to_build:
            # self.log.debug('  - constructing schema for %s' % meta_id)
            e = self.ces[meta_id]
            schema = {}
            schema['pk_name'] = 'oid'
            # self.log.debug('    bases ... %s' % str(e['bases']))
            schema['base_names'] = e['bases']
            schema['definition'] = e['definition']
            # OrderedSet doesn't have a 'union' method, so use set here ...
            # this section basically implements 'inheritance' for fields.
            base_schemas = [schemas[n] for n in e['bases']]
            if base_schemas:
                base_attrs = set.union(*[set(s['fields'])
                                         for s in base_schemas])
                attr_set = OrderedSet(base_attrs)
            else:
                attr_set = OrderedSet()
            # add local attributes last:
            local_props = [p for p in self.pes
                           if self.pes[p]['domain'] == meta_id]
            attr_set |= OrderedSet(local_props)
            # use default order for pgef iface properties:
            pgef_props = OrderedSet(PGEF_PROPS_ORDER)
            attr_order = (attr_set & pgef_props) | (attr_set - pgef_props)
            schema['field_names'] = list(attr_order)
            schema['fields'] = {a : property_to_field(a, self.pes[a])
                                for a in schema['field_names']}
            for field_name in schema['fields']:
                if field_name in local_props:
                    schema['fields'][field_name]['local'] = True
                else:
                    schema['fields'][field_name]['local'] = False
            # self.log.debug('    field_names:  %s' % str(list(attr_order)))
            # "register" the schema ...
            schemas[meta_id] = schema

    def metaobject_build_order(self):
        """
        Return a list containing the ids of all currently registered Class
        extracts (C{self.ces}) in order such that none occurs in the list
        before any of its bases.

        @return:  a list of ids in build order
        @rtype:   a `list` of `str`s
        """
        # self.log.debug('* metaobject_build_order()')
        build_order = []
        nextids = set(list(self.ces))
        # self.log.debug('   begin assembling build_order')
        while 1:
            for e in [self.ces[eid] for eid in nextids]:
                # append e['id'] to the build_order if the intersection of
                # all e's bases (C{set(self._extract_basewalk(e))}) with
                # the current build_order is equal to the set of all e's
                # bases.
                if (self.all_your_base(e)).issubset(set(build_order)):
                    build_order.append(e['id'])
                    # VERY verbose -- only use for extreme debugging
                    # self.log.debug('   ... "%s" inserted.' % e['id'])
                    # self.log.debug('   build_order = %s' % build_order)
            nextids -= set(build_order)
            if not nextids:
                break
        return build_order

    def all_your_base(self, e):
        """
        Given an extract, return the set of all its base class names.

        Args:
            e (dict):  an extract
        """
        # self.log.debug('* all_your_base')
        return set(self._extract_basewalk(e)) - set([e['id']])

    def _extract_basewalk(self, e):
        """
        Given an extract, return a generator that will yield the `id`s of
        all bases specified by it and its ancestors (note that duplicate `id`s
        may be yielded if the bases are not a DAG).

        Args:
            e (dict):  an extract
        """
        yield e['id']
        for b in e['bases']:
            for x in self._extract_basewalk(self.ces[b]):
                yield x

    def all_your_sub(self, e):
        """
        Given an extract, return the set of all its base class names.

        Args:
            e (dict):  an extract
        """
        # self.log.debug('* all_your_sub')
        return set(self._extract_subwalk(e))

    def _extract_subwalk(self, e):
        """
        Given an extract, return a generator that will yield the `id`s of all
        subclasses specified by it and its children.

        Args:
            e_id (str):  an extract id
        """
        yield e['id']
        for c in self.ces.values():
            if e['id'] in c['bases']:
                for x in self._extract_subwalk(c):
                    yield x

    def find_app_ontologies(self):
        """
        Find all app ontology source files in `self.onto_path` and populate
        the self.apps_dict dictionary that maps nsprefixes to source file paths.
        """
        # TODO:  check the cache, too, and give user the option of restoring
        # what's in cache or re-building the cache from the source OWL files --
        # also, detect whether the OWL files have changed since the cached
        # version was built.
        self.apps_dict = {} # clear it, in case it needs refreshing
        # self.log.debug('* looking for app ontologies')
        app_owl_file_paths = glob.glob(os.path.join(self.onto_path, '*.owl'))
        if 'pgef.owl' in app_owl_file_paths:
            app_owl_file_paths.remove('pgef.owl')
        if app_owl_file_paths:
            # NOTE:  if OWL file(s) other than 'pgef.owl' are found in the
            # ontologies directory, the domain schemas will always be rebuilt.
            # (TODO:  make this user-selectable.)
            for owl_file in app_owl_file_paths:
                nsprefix = get_ontology_prefix(owl_file)
                self.apps_dict[nsprefix] = owl_file
                # self.log.debug('   + found:  %s in %s' % (nsprefix, owl_file))
        else:
            # self.log.debug('   + no application OWL files found.')
            pass

    def build_schemas_from_ontology(self, source, use_cache=True):
        """
        Build a dictionary of application schemas and classes based on an
        application ontology.

        Args:
            source (str):  name ('prefix') of the ontology or path to an OWL
                file.  (If a 'prefix' is given, the ontology must be contained
                in an OWL file named '[prefix].owl' and located in
                `self.onto_path`.)

        Keyword Args:
            use_cache (bool):  if True, check for cached schemas
        """
        # TODO:  Currently, all application ontologies are imported into one big
        # namespace.  If a name in an application name collides with a pgef
        # name, it clobbers it.  This may or may not be desirable -- at any
        # rate, it should be consciously evaluated as a strategy, and possibly
        # should be made into a configurable option.  Namespace-qualified class
        # and property definitions might be confusing to users.  Note that
        # having all names in one big namespace doesn't mean that we can't
        # trace the *origin* of names and have an application "context" based
        # on an application ontology -- that's quite doable even with one big
        # namespace, because all the metaobjects can have an 'origin_ns'
        # attribute, or some such.  That's a separate issue -- this issue is
        # just about global name uniqueness, collisions, and "qualified names".
        # self.log.debug('* building app classes from ontology')
        if os.sep in source or '.' in source:
            app_prefix = os.path.basename(source).split('.')[0]
        else:
            app_prefix = source
            source = os.path.join(self.onto_path, (app_prefix+'.owl'))
        # self.log.debug('  app_prefix = "%s"' % app_prefix)
        app_cache_path = os.path.join(self.cache_path, app_prefix)
        got_cache = os.path.exists(app_cache_path)
        # [1] create extracts or get them from cache
        if use_cache:
            if got_cache:
                # self.log.debug('  - using cache.')
                self._get_extracts_from_cache()
            else:
                # self.log.debug('  - cache needs rebuilding.')
                # TODO:  display a "processing" message to user with "Building
                # application classes from ontology"
                # create extracts of pgef core meta objects from owl source files
                self._create_extracts_from_source(source)
        else:
            # TODO:  make sure cache is cleared (remove files)
            if got_cache:
                shutil.rmtree(app_cache_path)
            self._create_extracts_from_source(source)
        # [2] create schemas from the extracts
        self._update_schemas_from_extracts()
        self.apps += app_prefix

    def report(self, meta_ids=None):
        """
        Generate a plain text report on the registry's contents (ontology).
        """
        output = '\n===========================\n'
        output += 'PanGalactic Ontology Report\n===========================\n'
        if self.version:
            output += 'version: {}\n'.format(self.version)
        output += '--------------------------------------------------\n'
        if meta_ids:
            if type(meta_ids) is str:
                meta_ids = [meta_ids]
        else:
            meta_ids = self.metaobject_build_order()
        for name in meta_ids:
            schema = schemas[name]
            if schema['base_names']:
                base_names = ', '.join(schema['base_names'])
            else:
                base_names = '[none]'
            output += '\nClass .................... %s\n' % (name)
            output += '  Base Class(es) ......... %s\n' % base_names
            output += '  Definition:\n'
            try:
                output += schema['definition']
            except:
                output += '[none]'
            output += '\n\n  Properties:'
            for field_name in schema['field_names']:
                output += '\n      * %s\n' % schema['fields'][field_name]['id']
                output += '\n        Definition:  %s\n' % (
                            schema['fields'][field_name]['definition'],)
            output += '\n--------------------------------------------------\n'
        return output

    def report_html(self):
        """
        Generate an HTML report on the registry's contents (derived from the
        pgef.owl ontology).
        """
        output = '<html>'
        output += '<head>'
        output += '<title>Pan Galactic Ontology Report</title>'
        output += '</head>'
        output += '<body>'
        output += '<h1>Pan Galactic Ontology Report</h1>'
        if self.version:
            output += '<h3>version: <font color="red">'
            output += '{}</font></h3>'.format(self.version)
        output += '<hr>'
        cnames = list(schemas.keys())[:]
        cnames.sort()
        output += '<h3>Classes:</h3>'
        # index (arrange in 7 columns)
        output += '<table>\n'
        i = 0
        while 1:
            output += '<tr>'
            for j in range(7):
                output += '<td><a href="#{}"><b>{}</b></a></td>'.format(
                                                    cnames[i], cnames[i])
                i += 1
                if i >= len(cnames):
                    break
            output += '</tr>\n'
            if i >= len(cnames):
                break
        output += '</table>\n'
        output += '<hr>'
        output += '<ul>'
        for name in self.metaobject_build_order():
            schema = schemas[name]
            field_names = schema['field_names']
            field_names.sort()
            if schema['base_names']:
                base_names = ', '.join(schema['base_names'])
            else:
                base_names = '[none]'
            output += '<li>'
            output += '<a name="{}"></a>'.format(name)
            output += '<b>Class:</b> '
            output += '<b><i><font color="red">%s</font></b></i><br>' % name
            output += '<b>Base Class(es):</b> <i>%s</i><br>' % str(base_names)
            output += '<dl><dt><b>Definition:</b></dt>'
            output += '<dd>'
            output += schema.get('definition', '[none]')
            output += '</dd></dl>'
            local_properties = [p for p in field_names
                                if schema['fields'][p]['local']]
            inherited_properties = [p for p in field_names
                                    if not schema['fields'][p]['local']]
            if local_properties:
                output += '<b>Local Properties:</b>'
                output += '<ul>'
                for p in local_properties:
                    inv = ''
                    if schema['fields'][p]['is_inverse']:
                        inv = ''.join(
                                    [' <font color="red">[inverse of</font> ',
                                     schema['fields'][p]['inverse_of'],
                                     '<font color="red">]</font>'])
                    output += ''.join(['<li><i><b>',
                                     schema['fields'][p]['id'],
                                     ' <font color="blue">(',
                                     schema['fields'][p]['range'],
                                     ')</font>',
                                     inv,
                                     '</b></i>: ',
                                     schema['fields'][p]['definition'],
                                     '</li>'
                                     ])
                output += '</ul>'
            if inherited_properties:
                output += '<b>Inherited Properties:</b>'
                output += '<ul>'
                for p in inherited_properties:
                    inv = ''
                    if schema['fields'][p]['is_inverse']:
                        inv = ''.join(
                                    [' <font color="red">[inverse of</font> ',
                                     schema['fields'][p]['inverse_of'],
                                     '<font color="red">]</font>'])
                    output += ''.join(['<li><i><b>',
                                     schema['fields'][p]['id'],
                                     ' <font color="blue">(',
                                     schema['fields'][p]['range'],
                                     ')</font>',
                                     inv,
                                     '</b></i>: ',
                                     schema['fields'][p]['definition'],
                                     '</li>'
                                     ])
                output += '</ul>'
            output += '<hr>'
        output += '</ul>'
        output += '</body>'
        output += '</html>'
        return output


# FUNCTIONS USED IN Tachistry:

# function                            where called
# --------                            ------------
# _create_pgef_core_meta_objects       __init__
# build_schemas_from_ontology      __init__
# _create_extracts_from_source         _create_pgef_core_meta_objects
# _update_schemas_from_extracts        _create_extracts_from_source
# _get_extracts_from_cache             _create_pgef_core_meta_objects
# _create_extracts_from_source         build_schemas_from_ontology
# _get_extracts_from_cache             build_schemas_from_ontology
# metaobject_build_order               _update_schemas_from_extracts
# all_your_base                        metaobject_build_order
# _extract_basewalk                    all_your_base
# report                               [end-user]
# reportHtml                           [end-user]

