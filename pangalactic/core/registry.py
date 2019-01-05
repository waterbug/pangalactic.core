# -*- coding: utf-8 -*-
"""
The Pan Galactic Meta Object Registry
"""
# TODO:
# [ ] create a KB db backend (all data about ontologies -- this corresponds to
    # application meta-meta-data -- i.e., data about the objects from which
    # application classes/objects are created):
    # + Ontology
    # + Property
    # + Class
# [DONE] create sa Tables and app classes from cached meta-meta-data
# [DONE] generate registry schemas from kb classes + properties

# Python
from __future__ import print_function
try:
    # Python 2
    from __builtin__ import str as builtin_str
except ImportError:
    # Python 3
    from builtins import str as builtin_str
from builtins import range
from builtins import object
import glob, os, pkgutil, shutil
from collections import OrderedDict

# SqlAlchemy
from sqlalchemy                 import Column, create_engine
from sqlalchemy                 import ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm             import relationship

# PanGalactic
from pangalactic.core                import config
from pangalactic.core.datastructures import OrderedSet
from pangalactic.core.meta           import PGEF_PROPS_ORDER
from pangalactic.core.kb             import PanGalacticKnowledgeBase as KB
from pangalactic.core.kb             import get_ontology_prefix
from pangalactic.core.names          import namespaces
from pangalactic.core.utils.meta     import dump_metadata, load_metadata
from pangalactic.core.utils.meta     import property_to_field
from pangalactic.core.utils.meta     import to_table_name
from pangalactic.core.log            import get_loggers


# create SqlAlchemy declarative 'Base' class for MetaObject classes
Base = declarative_base()

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


class PanGalacticRegistry(object):
    """
    The `PanGalacticRegistry` maintains dictionaries of the schemas used to
    specify an application's domain classes and database structures.

    Attributes:
        home (str):  application home directory.  [default: `pangalactic_home`]
        schemas (dict):  see definition in _update_schemas_from_extracts
        cache_path (str):  directory in which serialized schemas will be cached
        onto_path (str):  directory containing app ontology OWL files
            [default: `apps` -- other values are used only for testing]
        apps (list of str):  list of loaded apps (app ontology prefixes)
        classes (dict):  A mapping of `meta_id`s to runtime app classes.
        persistables (set):  The names of schemas for which there are db tables
        kb (p.meta.kb.KB):  An RDF graph containing the app ontology
        ces (dict):  A mapping of `meta_id`s to `Class` extracts
        pes (dict):  A mapping of `meta_id`s to `Property` extracts
        nses (dict):  A mapping of namespace prefixes to namespace extracts
    """
    def __init__(self, home=None, db_url=None, cache_path='cache',
                 onto_path='onto', apps=None, log=None, version='',
                 debug=False, console=False, force_new_core=False):
        """
        Initialize the registry.

        Keyword Args:
            home (None or str):  if not `None`, indicates the registry should
                use this path as its home directory.
            db_url (str):  url to use in sqlalchemy create_engine
                [default (None): `sqlite:///[home]/local.db`]
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
        # print 'Registry initializing with:'
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
        elif console:
            # print log messages
            self.log = FakeLog()
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
        if not os.path.exists(pgef_owl_path):
            f = open(pgef_owl_path, 'w')
            f.write(str(pkgutil.get_data('pangalactic.core.ontology',
                                         'pgef.owl').decode('utf-8')))
            f.close()
        self.log.info('* not installed; using pgef.owl in home dir.')
        self.apps_dict = {}   # not currently used
        self.apps = []
        self.schemas = {}
        self.classes = {}
        self.ces = {}
        self.pes = {}
        self.nses = {}
        if db_url:
            self.log.info('* initializing db at "{}"'.format(db_url))
            self.db_engine = create_engine(db_url)
        else:
            # if no db_url is specified, set up a local (sqlite) db in home
            self.log.info('* initializing local sqlite db.')
            local_db_path = os.path.join(self.home, 'local.db')
            self.db_engine = create_engine('sqlite:///%s' % local_db_path)
        # create the KB (knowledgebase) and initialize the registry's schemas,
        # which will be used in generating the database and app classes
        self.log.info('* [registry] creating KB from pgef.owl source ...')
        self.log.info('             (pgef.owl path: "{}")'.format(
                                                            pgef_owl_path))
        self.kb = KB(pgef_owl_path)
        self._create_pgef_core_meta_objects(use_cache=(not force_new_core))
        # check for app ontologies -- if any are found, load them
        app_onto_files = [n for n in os.listdir(self.onto_path)
                          if n != 'pgef.owl']
        if app_onto_files:
            for fname in app_onto_files:
                if fname.endswith('.owl'):
                    self.build_app_classes_from_ontology(
                                    os.path.join(self.onto_path, fname))

    def start_logging(self, console=False, debug=False):
        """
        Create a registry (`pgreg`) log and begin writing to it.

        Keyword Args:
            console (bool):  if True, sends log messages to stdout
            debug (bool):  if True, sets level to debug
        """
        if config.get('test_mode') and console:
            console = True
        else:
            console = False
        self.log, self.error_log = get_loggers(self.home, 'registry',
                                               console=console, debug=debug)
        self.log.info('* registry logging initialized ...')

    def _create_pgef_core_meta_objects(self, use_cache=True):
        """
        Build schemas and classes based on the pgef ontology.

        @param use_cache:  if True, check for cached pgef core models; if any
            exist, the registry will rebuild the pgef core meta objects from
            the cached models; otherwise, it will rebuild them using pgef.owl.
        @type  use_cache:  `bool`
        """
        self.log.info('* creating pgef core meta objects')
        # [1] create extracts or get them from cache
        if use_cache:
            if self.got_pgef_cache:
                self.log.info('  - restoring meta objects from cache.')
                self._get_extracts_from_cache()
            else:
                self.log.info('  - pgef cache needs rebuilding.')
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
        self._update_classes_from_schemas()

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
        self.log.info('* creating extracts from source')
        if source == None:
            self.log.info('   + source:  pgef.owl')
            nsprefix = 'pgef'
        else:
            self.log.info('   + source:  %s' % str(source))
            nsprefix = get_ontology_prefix(source)
            if hasattr(source, 'read'):
                # if source is file-like, must reset to beginning
                source.seek(0)
            self.kb.parse(source)
        self.log.debug('   + nsprefix = %s' % str(nsprefix))
        new_pes = {}
        new_ces = {}
        pnames = self.kb.get_property_names(nsprefix)
        self.log.debug('   + pnames:  %s' % pnames)
        for pname in pnames:
            attrs = self.kb.get_attrs_of_property(nsprefix, pname)
            e = OrderedDict()
            e['oid'] = ':'.join([attrs['id_ns'], attrs['id']])
            e['_meta_id'] = 'Property'
            e.update(attrs)
            # add 'oid' and 'uri', which need to be generated from 'id' and
            # 'id_ns' (and we don't want them as properties of the OWL
            # properties anyway)
            new_pes[pname] = e
        cnames = self.kb.get_class_names(nsprefix)
        self.log.debug('   + cnames:  %s' % cnames)
        for cname in cnames:
            attrs = self.kb.get_attrs_of_class(nsprefix, cname)
            e = OrderedDict()
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
        Update the application class schemas (`self.schemas`) from any
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
        documented in `pangalactic.meta.utils.property_to_field`.
        """
        self.log.info('* updating schemas from extracts')
        to_build = [meta_id for meta_id in self.metaobject_build_order()
                    if meta_id not in self.schemas]
        for meta_id in to_build:
            self.log.debug('  - constructing schema for %s' % meta_id)
            e = self.ces[meta_id]
            schema = {}
            schema['pk_name'] = 'oid'
            self.log.debug('    bases ... %s' % str(e['bases']))
            schema['base_names'] = e['bases']
            schema['definition'] = e['definition']
            # OrderedSet doesn't have a 'union' method, so use set here ...
            # this section basically implements 'inheritance' for fields.
            base_schemas = [self.schemas[n] for n in e['bases']]
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
            self.log.debug('    field_names:  %s' % str(list(attr_order)))
            # "register" the schema ...
            self.schemas[meta_id] = schema

    def metaobject_build_order(self):
        """
        Return a list containing the ids of all currently registered Class
        extracts (C{self.ces}) in order such that none occurs in the list
        before any of its bases.

        @return:  a list of ids in build order
        @rtype:   a `list` of `str`s
        """
        self.log.debug('* metaobject_build_order()')
        build_order = []
        nextids = set(list(self.ces))
        self.log.debug('   begin assembling build_order')
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
        Given an 'extract', return the set of all its base classes.

        Args:
            e (dict):  an extract
        """
        # self.log.debug('* all_your_base')
        return set(self._extract_basewalk(e)) - set([e['id']])

    def _extract_basewalk(self, e):
        """
        Given an 'extract', return a generator that will yield the `id`s of
        all bases specified by it and its ancestors (note that duplicate `id`s
        may be yielded if the bases are not a DAG).

        Args:
            e (dict):  an extract
        """
        yield e['id']
        for b in e['bases']:
            for x in self._extract_basewalk(self.ces[b]):
                yield x

    def _update_classes_from_schemas(self):
        """
        Create class objects for any newly registered ontology Classes and
        update the `classes` member of the registry (a mapping of names to
        class objects).
        NOTE:  this function is currently only called by
        `_create_pgef_core_meta_objects` (at start-up), but in theory could do
        a "partial update" as part of a schema migration process.
        """
        # NOTE:  due to a limitation of sqlalchemy's joined table inheritance
        # model, a class can't have an object property (-> fk field) that
        # refers to its immediate superclass (because sqlalchemy will get
        # confused between that fk and the superclass 'oid' fk relationship).
        # [There may be a way to resolve this using relationship's
        # 'primaryjoin' kw arg or somehow specifying the 'onclause' of the
        # joins, but I haven't figured out how to do either yet.]
        self.log.info('  - updating classes from schemas')
        self.log.debug('    [using get_nearest_persistable_base()]')
        new_meta = [meta_id for meta_id in self.metaobject_build_order()
                    if (meta_id in self.persistables and
                    meta_id not in self.classes)]

        for cname in new_meta:
            self.log.debug('   + creating class for schema %s' % cname)
            schema = self.schemas[cname]
            # TODO:  more metadata about class, e.g.:
            #        - some kind of origin (onto)
            #        - origin (ontology, standard, or other metamodel)
            fields = schema['fields']
            class_dict = {}
            table_name = to_table_name(cname)
            class_dict['__tablename__'] = table_name
            self.log.debug('  - tablename: %s' % table_name)
            # special case:  Identifiable defines "discriminator" column
            if cname == 'Identifiable':
                class_dict['oid'] = Column(String, primary_key=True)
                pgef_type = Column(String)
                class_dict['pgef_type'] = pgef_type
                base_id = 'Base'
                base_class = Base
                mapper_dict = {'polymorphic_identity': 'Identifiable',
                               'polymorphic_on': pgef_type}
                class_dict['__mapper_args__'] = mapper_dict
            else:
                base_id = self.get_nearest_persistable_base(cname)
                base_class = self.classes[base_id]
                # for subclasses, 'oid' is primary key *AND* also fk to
                # its base_class's 'oid'
                base_cls_oid = to_table_name(base_id) + '.oid'
                class_dict['oid'] = Column(String,
                                           ForeignKey(base_cls_oid),
                                           primary_key=True)
                class_dict['__mapper_args__'] = {'polymorphic_identity': cname}
            # identify locally-defined non-inverse property fields
            local_field_names = [n for n in schema['field_names']
                                 if n != 'oid'
                                 and not schema['fields'][n]['is_inverse']
                                 and schema['fields'][n]['local']]
            # identify locally-defined inverse property fields
            local_inverse_names = [n for n in schema['field_names']
                                   if n != 'oid'
                                   and schema['fields'][n]['is_inverse']
                                   and schema['fields'][n]['local']]
            # do non-inverse fields first -- some inverse fields need to
            # reference the fk columns that are created here
            for field_name in local_field_names:
                field = fields[field_name]
                related_cname = field.get('related_cname')
                if related_cname:
                    # -> object property
                    self.log.debug('  - non-inverse field "%s"' % field_name)
                    related_oid = to_table_name(related_cname) + '.oid'
                    fk_field_name = field_name + '_oid'
                    fk_col = Column(ForeignKey(related_oid))
                    class_dict[fk_field_name] = fk_col
                    # check whether it *has* an inverse property
                    self.log.debug('     checking for inverse of %s' %
                                  field_name)
                    rel_schema = self.schemas[related_cname]
                    has_inverse = [name for name, f
                                   in rel_schema['fields'].items()
                                   if f['inverse_of'] == field_name]
                    if has_inverse:
                        # if so, add the 'back_populates'
                        self.log.debug('     inverse found: %s' %
                                      has_inverse[0])
                        if related_cname == cname:
                            # self-referential -> need a 'remote_side' arg
                            rel = relationship(related_cname,
                                               foreign_keys=[fk_col],
                                               remote_side=[class_dict['oid']],
                                               back_populates=has_inverse[0])
                        else:
                            rel = relationship(related_cname,
                                               foreign_keys=[fk_col],
                                               back_populates=has_inverse[0])
                    else:
                        self.log.debug('     no inverse found.')
                        if related_cname == cname:
                            # self-referential -> need a 'remote_side' arg
                            rel = relationship(related_cname,
                                               remote_side=[class_dict['oid']],
                                               foreign_keys=[fk_col])
                        else:
                            rel = relationship(related_cname,
                                               foreign_keys=[fk_col])
                    class_dict[field_name] = rel
                # TODO:  deal with non-functional properties (collections) --
                # possibly by manufacturing fk's for them
                elif field['functional']:
                    # -> datatype fields
                    class_dict[field_name] = Column(field['field_type'])
            for field_name in local_inverse_names:
                # inverse property -> no ForeignKey column, just a relationship
                field = fields[field_name]
                orig_field = field['inverse_of']
                self.log.debug('     "%s", inverse of "%s"' % (field_name,
                                                              orig_field))
                related_cname = field['related_cname']
                fk_col = related_cname + '.' + orig_field + '_oid'
                if related_cname == cname:
                    # self-referential -> need a 'remote_side' arg
                    rel = relationship(
                                   related_cname,
                                   foreign_keys=fk_col,
                                   remote_side=[class_dict[orig_field+'_oid']])
                                   # back_populates=orig_field)
                else:
                    # not self-referential
                    rel = relationship(related_cname,
                                       foreign_keys=fk_col)
                                       # back_populates=orig_field)
                class_dict[field_name] = rel
            self.log.debug('    ->  base class: %s' % str(base_id))
            self.log.debug('    ->  class_dict: %s' % str(class_dict))
            # create class
            self.classes[cname] = type(builtin_str(cname), (base_class,),
                                       class_dict)
        # generate all tables ...
        Base.metadata.create_all(self.db_engine)

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
        self.log.info('* looking for app ontologies')
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
                self.log.info('   + found:  %s in %s' % (nsprefix, owl_file))
        else:
            self.log.info('   + no application OWL files found.')

    def build_app_classes_from_ontology(self, source, use_cache=True):
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
        self.log.info('* building app classes from ontology')
        if os.sep in source or '.' in source:
            app_prefix = os.path.basename(source).split('.')[0]
        else:
            app_prefix = source
            source = os.path.join(self.onto_path, (app_prefix+'.owl'))
        self.log.info('  app_prefix = "%s"' % app_prefix)
        app_cache_path = os.path.join(self.cache_path, app_prefix)
        got_cache = os.path.exists(app_cache_path)
        # [1] create extracts or get them from cache
        if use_cache:
            if got_cache:
                self.log.info('  - using cache.')
                self._get_extracts_from_cache()
            else:
                self.log.info('  - cache needs rebuilding.')
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
        # [3] create pgef core metaobjects in order from the schemas
        self._update_classes_from_schemas()
        self.apps += app_prefix

    #######################################################################
    #  property:  'persistables'
    #
    #  The main use of persistables is in chronosynclastic, to determine
    #  which schemas have database tables.
    #######################################################################

    @property
    def persistables(self):
        """
        Get a list of the names of all registered schemas for which tables
        will be created in PGER.
        """
        meta_ids = [x for x in self.schemas
                    if x not in [
                    'Class',          # NOTE: may become persistable later
                    'Property',       #  "
                    'Namespace',      #  "
                    'Schema',         #  "
                    'Interface',      #  "
                    'PanGalacticFu',  #  "
                    'MetaObject',
                    'Discoverable',
                    'Representable',
                    'Securable',
                    'Manageable',
                    'MemberOf',
                    ]]
        return set(meta_ids)

    def get_nearest_persistable_base(self, meta_id):
        """
        For a given meta_id, find the meta_id of the nearest ancestor within the
        inheritance tree of persistable classes rooted in `Identifiable`.

        @param meta_id:  the meta_id whose nearest persistable ancestor's
            meta_id is to be found
        @type  meta_id:  `str`

        @return:  `meta_id` of nearest persistable base
        @rtype:   `str`
        """
        self.log.debug('* get_nearest_persistable_base(%s)' % meta_id)
        bases = [b for b in self.ces[meta_id]['bases']
                 if b in self.persistables]
        if bases:
            base = bases.pop()
        else:
            base = None
        self.log.debug('  - base: %s' % base)
        return base

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
            schema = self.schemas[name]
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
        cnames = list(self.classes.keys())[:]
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
            schema = self.schemas[name]
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


# FUNCTIONS USED IN REGISTRY:

# function                            where called
# --------                            ------------
# _create_pgef_core_meta_objects       __init__
# build_app_classes_from_ontology      __init__
# _create_extracts_from_source         _create_pgef_core_meta_objects
# _update_schemas_from_extracts        _create_extracts_from_source
# _get_extracts_from_cache             _create_pgef_core_meta_objects
# _update_classes_from_schemas         _create_pgef_core_meta_objects
# _create_extracts_from_source         build_app_classes_from_ontology
# _get_extracts_from_cache             build_app_classes_from_ontology
# metaobject_build_order               _update_schemas_from_extracts
# all_your_base                        metaobject_build_order
# _extract_basewalk                    all_your_base
# persistables                         _update_classes_from_schemas
# get_nearest_persistable_base         _update_classes_from_schemas
# report                               [end-user]
# reportHtml                           [end-user]


    ###### NOTE:  the below are currently not used ... may be revamped

# class Ontology(MetaObjectBase):
    # """
    # An OWL Ontology [owl:Ontology].
    # """
    # __tablename__ = 'ontologies'

    # prefix = Column(String, primary_key=True)
    # uri = Column(String)
    # description = Column(String)

    # def __repr__(self):
        # return '<Ontology "%s" [%s]>' % (self.prefix, self.uri)


# class Class(MetaObjectBase):
    # """
    # An OWL Class [owl:Class].
    # """
    # __tablename__ = 'classes'

    # id = Column(String, primary_key=True)
    # # TODO:  possibly make id+id_ns a compound foreign key, which would permit
    # # the same Class name to be used in multiple Ontologies (realistic, albeit
    # # also potentially confusing)
    # id_ns = Column(String, ForeignKey('ontologies.prefix'))
    # # 'name' is actually unicode (sa 'String' supports unicode); 'id' is
    # # asciified 'name'
    # name = Column(String)
    # # TODO: rdfs:subClassOf -- the list of bases
    # # figure out how to do this (either FK rel. or list of strings / ENUM)
    # # for now, just use registry.ces (class extracts
    # abbreviation = Column(String)
    # definition = Column(String)
    # ontology = relationship("Ontology", backref=backref('ontologies',
                            # order_by="classes.c.prefix"))

    # def __repr__(self):
        # return '<Class %s:%s>' % (self.id_ns, self.id)


# class Property(MetaObjectBase):
    # """
    # An OWL Property [owl:ObjectProperty or owl:DatatypeProperty].
    # """
    # __tablename__ = 'properties'

    # id = Column(String, primary_key=True)
    # # TODO:  possibly make id+id_ns a compound foreign key, which would permit
    # # the same Property name to be used in multiple Classes
    # id_ns = Column(String, ForeignKey('classes.id'))
    # # 'name' is actually unicode (sa 'String' supports unicode); 'id' is
    # # asciified 'name'
    # name = Column(String)
    # type = Column(String)
    # abbreviation = Column(String)
    # definition = Column(String)
    # functional = Column(Boolean)
    # domain = relationship("Class",
                          # backref=backref('classes', order_by='properties.c.id'))

    # __mapper_args__ = {
        # 'polymorphic_identity' : 'property',
        # 'polymorphic_on' : 'type'
        # }


# class ObjectProperty(Property):
    # """
    # An OWL ObjectProperty [owl:ObjectProperty].
    # """
    # __tablename__ = 'object_properties'
    # id = Column(String, ForeignKey('properties.id'), primary_key=True)
    # range = Column(String, ForeignKey('classes.id'))

    # __mapper_args__ = {
        # 'polymorphic_identity' : 'object_property'
        # }


# class DatatypeProperty(Property):
    # """
    # An OWL DatatypeProperty [owl:DatatypeProperty].
    # """
    # __tablename__ = 'datatype_properties'
    # id = Column(String, ForeignKey('properties.id'), primary_key=True)
    # range = Column(String)    # Python type names ('int', 'str', etc.)
                              # # and custom datatypes (e.g. value with units)

    # __mapper_args__ = {
        # 'polymorphic_identity' : 'datatype_property'
        # }


    # def create_metaobjects_from_src(self, source,
                                    # module='pangalactic.meta.names',
                                    # use_cache=False,
                                    # nsprefix='pgef'):
        # """
        # Build a dictionary of schemas (Zope Schemas -- which are `Interface`
        # instances) and classes based on them from an application source model.

        # @param source:  path to an OWL file or RDF/XML encoded OWL data in a
            # string buffer
        # @type  source:  `str` or `file`

        # @param module:  a name to be used as the `__module__` attribute for the
            # `Schema` instances that will be created
        # @type  module:  `str`

        # @param use_cache:  if `True` and there is a cached pgef core model, the
                          # registry will rebuild the pgef core meta objects from
                          # the cached model; otherwise, it will rebuild them
                          # using pgef.owl.
        # @type  use_cache:  `bool`
        # """
        # self.log.info('* create_metaobjects_from_src()')
        # # (1) get extracts of app meta objects from cache or source files
        # if use_cache:
            # # use the cache, Luke! no, really ... implement something
            # pass
        # else:
            # # read app metadata from the default application source directory
            # # TODO:  keep a state variable of sources read, to avoid reading
            # # them again unless requested to do so
            # self._create_extracts_from_source(source)
        # (2) create metaobjects from the extracts
        #     (metaobjects can be modified to create new apps)
        # FIXME (what was here was broken and has been gutted ... use
        # techniques from _create_pgef_core_meta_objects
        # ** OLD CODE for caching metaobjects -- to be replaced by meta_db
        # if not use_cache:
            # # (3) serialize the source meta objects to the app cache
            # appcache_path = os.path.join(self.cache_path, nsprefix)
            # if not os.path.exists(appcache_path):
                # os.makedirs(appcache_path)
            # self.property_cache_path = os.path.join(appcache_path,
            #                                         'properties')
            # if not os.path.exists(self.property_cache_path):
                # os.mkdir(self.property_cache_path)
            # for meta_id, pe in self.pes.items():
                # dump_metadata(pe, os.path.join(self.property_cache_path,
                #                       meta_id + '.json'))
            # self.class_cache_path = os.path.join(appcache_path, 'classes')
            # if not os.path.exists(self.class_cache_path):
                # os.mkdir(self.class_cache_path)
            # for meta_id, cse in self.ces.items():
                # dump_metadata(cse, os.path.join(self.class_cache_path,
                #                        meta_id + '.json'))
        # ** OLD CODE for caching metaobjects -- to be replaced by meta_db

    # def create_report_on_source(self, source=None):
        # """
        # Create {Class|Property|Namespace} extracts corresponding to the
        # principal namespace or model in the source.

        # @param source:  if None, create extracts for the 'pgef' namespace from
            # its source files; otherwise, source must be a string (buffer) that
            # contains an OWL dataset.
        # @type  source:  `str`
        # """
        # self.log.info('* create_report_on_source()')
        # if source == None:
            # self.log.debug(' '.join(['   + no source specified; getting "pgef"',
                                    # 'from its source OWL files ...']))
            # nsprefix = 'pgef'
        # else:
            # self.log.debug('   + source = %s' % str(source))
            # nsprefix = get_ontology_prefix(source)
            # self.kb.parse(source)
        # self.log.info('   + nsprefix = %s' % str(nsprefix))
        # pnames = self.kb.get_property_names(nsprefix)
        # for pname in pnames:
            # e = self.kb.get_attrs_of_property(nsprefix, pname)
            # e['_meta_id'] = 'Property'
            # # add 'oid' and 'uri', which need to be generated from 'id' and
            # # 'id_ns' (and we don't want them as properties of the OWL
            # # properties anyway)
            # e['oid'] = ':'.join([e['id_ns'], e['id']])
            # self.pes[pname] = e
        # cnames = self.kb.get_class_names(nsprefix)
        # self.log.debug('   + cnames:  %s' % cnames)
        # for cname in cnames:
            # e = self.kb.get_attrs_of_class(nsprefix, cname)
            # e['bases'] = self.kb.get_base_names(nsprefix, cname)
            # e['_meta_id'] = 'Class'
            # e['oid'] = ':'.join([e['id_ns'], e['id']])
            # self.ces[cname] = e
        # # create a Namespace extract for the specified namespace (ns has
        # # already been registered while reading the source -- e.g., by
        # # readRdfGraphFromRdfXmlData(source) -- so it is already in the
        # # 'namespaces' dictionary)
        # ns = namespaces[nsprefix]

