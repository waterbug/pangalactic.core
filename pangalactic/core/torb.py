# -*- coding: utf-8 -*-
"""
The fast Object Request Broker (ORB):
Pan Galactic speedy hub for object metadata and storage operations.

NOTE:  Only the `orb` instance created in this module should be imported (it is
intended to be a singleton).
"""
import json, os, shutil, sys, traceback
# import pprint
from copy      import deepcopy
from functools import reduce
from pathlib   import Path
from uuid      import uuid4

# ruamel_yaml
import ruamel_yaml as yaml

# PanGalactic
# core
from pangalactic.core             import __version__
from pangalactic.core             import diagramz
from pangalactic.core             import read_config
from pangalactic.core             import prefs, read_prefs
from pangalactic.core             import state, read_state, write_state
from pangalactic.core             import trash, read_trash
from pangalactic.core             import refdata
from pangalactic.core.mapping     import schema_maps, schema_version
from pangalactic.core.meta        import TEXT_PROPERTIES
from pangalactic.core.parametrics import (add_default_parameters,
                                          add_default_data_elements,
                                          add_parameter,
                                          componentz, systemz,
                                          data_elementz, de_defz,
                                          get_parameter_id,
                                          get_parameter_name,
                                          get_parameter_description,
                                          get_dval_as_str,
                                          get_pval_as_str,
                                          load_allocz, load_compz,
                                          load_rqt_allocz, load_data_elementz,
                                          load_parmz, load_de_defz,
                                          load_parmz_by_dimz,
                                          load_systemz, parameterz, parm_defz,
                                          save_allocz, save_compz,
                                          save_systemz, save_rqt_allocz,
                                          save_data_elementz, save_parmz,
                                          save_de_defz,
                                          save_parmz_by_dimz)
from pangalactic.core.smerializers import serialize, deserialize
from pangalactic.core.tachistry    import Tachistry, matrix, schemas
from pangalactic.core.test         import data as test_data_mod
from pangalactic.core.test         import vault as test_vault_mod
from pangalactic.core.test.utils   import gen_test_dvals, gen_test_pvals
from pangalactic.core.units        import in_si
from pangalactic.core.utils.datetimes import (dtstamp, file_dts,
                                              file_date_stamp, dt2local_tz_str)
from pangalactic.core.log          import get_loggers
from pangalactic.core.validation   import get_assembly


NULL_VALUE = {'str' : '',
              'unicode' : '',
              'datetime' : '0',
              'time' : '0',
              'int' : 0,
              'float' : 0.0,
              'bool' : False,
              'bytes' : b'',
              'set' : set([])}


# 'inverses' is a cached mapping of all one-to-many inverse attributes to their
# values, which has the format:
#
#   {oid: {inverse_attr : [oids]}}
#
# ... where:
#   "oid" is the oid of the object that owns the inverse attribute 
#   "inverse_attr" is the name of the inverse attribute 
#   "oids" is a list of the oids of the objects that are the value of the
#          inverse attribute 
#
# Its purpose is to avoid the very expensive process of checking every object
# in the "database" for the matching (non-inverse) attribute

inverses = {}


def matrix_setattr(self, a, val):
    schema = schemas[self.__class__.__name__]
    if a in ['oid', '_cname']:
        object.__setattr__(self, a, val)
    elif a in schema['field_names']:
        if schema['fields'][a]['field_type'] == 'object':
            # 'a' is an object-valued attribute
            if schema['fields'][a]['range'] in schemas:
                if schema['fields'][a]['functional']:
                    # if an object value is specified, replace with its oid
                    allowed_types = orb.get_subclass_names(
                                                schema['fields'][a]['range'])
                    if (getattr(val, '_cname', None)
                        and val._cname in allowed_types):
                        matrix[self.oid][a] = getattr(val, 'oid', None)
                    elif val is None:
                        # if None is assigned, set to empty string
                        matrix[self.oid][a] = ''
                    elif isinstance(val, str):
                        # not object, must be an oid (str); if not, ignore
                        matrix[self.oid][a] = val
        else:
            # a is a datatype attribute, coerce correct datatype
            if val is None:
                val = NULL_VALUE.get(schema['fields'][a]['range'])
            try:
                if schema['fields'][a]['range'] in ['datetime', 'time']:
                    matrix[self.oid][a] = str(val)
                else:
                    matrix[self.oid][a] = schema['fields'][
                                                    a]['field_type'](val)
            except:
                pass


def matrix_getattr(self, a):
    cname = self.__class__.__name__
    if ((a not in ('oid', '_cname')) and
        a in schemas[cname]['field_names']):
        if schemas[cname]['fields'][a]['range'] in schemas:
            # ObjectProperty
            if matrix.get(self.oid) is None:
                return None
            elif schemas[cname]['fields'][a]['functional']:
                return orb.get(matrix[self.oid].get(a))
            else:
                # return orb.get(oids=inverses.get[self.oid][a])
                inverse = schemas[cname]['fields'][a]['inverse_of']
                return [o for o in db.values()
                        if getattr(o, inverse, None) is self]
        else:
            if matrix.get(self.oid) is None:
                return NULL_VALUE.get(schemas[cname]['fields'][a]['range'])
            return (matrix[self.oid].get(a) or
                    NULL_VALUE.get(schemas[cname]['fields'][a]['range']))


def thing_init(self, **kw):
    oid = kw.get('oid')
    if not oid:
        oid = str(uuid4())
        kw['oid'] = oid
    # IMPORTANT: check if there is already a matrix entry for that oid; if so,
    # don't replace it, just update it
    if not matrix.get(oid):
        matrix[oid] = dict(oid=oid)
        matrix[oid]['_cname'] = self._cname
    self.oid = oid
    for a in kw:
        if a in self.schema['field_names']:
            setattr(self, a, kw[a])


class metathing(type):
    def __new__(cls, cname, bases,  namespace):
        namespace['_cname'] = cname
        namespace['schema'] = schemas[cname]
        namespace['__init__'] = thing_init
        namespace['__slots__'] = ['oid']
        namespace['__setattr__'] = matrix_setattr
        namespace['__getattr__'] = matrix_getattr
        return super().__new__(cls, cname, bases, namespace)


# db:  a runtime cache used by the orb that maps oids to Thing instances
db = {}


class TachyOrb(object):
    """
    The Tachy Object Request Broker (Torb) is intended to be a vastly speedier
    and more flexible replacement for the UberORB.  Like the UberORB, the
    TachyOrb mediates all communications with local objects and the local
    metadata registry.

    The principal difference between the TachyOrb and the UberORB is that the
    classes that the UberORB manages are created using SqlAlchemy and always
    exist in a database session, connected to a relational database backend,
    whereas the classes that the TachyOrb manages are subclasses of the class
    Thing (named in homage to the root class of the OWL [Web Ontology Language]
    ontological universe).  Subclasses of Thing do not have a relational
    database backend but share a global dictionary that holds their attributes.
    Their persistence mechanism is a YAML-based serialization.

    IMPORTANT:  The TachyOrb, like the UberORB, is intended to be a singleton.
    The TachyOrb class should *not* be imported; instead, import 'orb', the
    module-level instance created at the end of this module.

    NOTE:  the TachyOrb eschews the use of an __init__() method in order to
    avoid side-effects of importing the module-level instance that is created
    -- its start() method must be explicitly called to initialize it.

    Attributes:
        classes (dict):  a mapping of `meta_id`s to runtime app classes.
        data (dict):  in-memory cache of DataMatrix instances
        data_store (str):  path to directory in which tsv-serialized instances
            of DataMatrix are stored
        error_log (Logger):  instance of pgorb_error_logger
        home (str):  full path to the application home directory -- populated
            by orb.start()
        log (Logger):  instance of pgorb_logger
        new_oids (list of str):  oids of objects that have been created but not
            saved
        registry (Tachistry):  instance of Tachistry
        role_product_types (dict): cache that maps Role ids to corresponding
            ProductType ids (used by the 'access' module, which determines user
            permissions relative to domain objects)
        role_oids_to_ids (dict): cache that maps Role oids to their ids (mainly
            for use by the 'access' module
        user_raz (list): cache of serialized RoleAssignment objects for roles
            assigned to the local user
    """
    is_torb = True
    started = False
    new_oids = []
    classes = {}
    # parmz_status and data_elementz_status are used to determine whether saved
    # parameter and data_element data have been loaded successfully from the
    # "parameters.json" and "data_elements.json" files
    data_elementz_status = 'unknown'
    parmz_status = 'unknown'

    def save_matrix(self, dir_path):
        """
        Save 'matrix' dict to a json file.
        """
        self.log.debug(f'* saving matrix ({len(matrix)} objects) ...')
        fpath = os.path.join(dir_path, 'matrix.json')
        with open(fpath, 'w') as f:
            f.write(json.dumps(matrix, separators=(',', ':'),
                               indent=4))
        self.log.debug('  matrix saved.')

    def load_matrix(self, dir_path):
        """
        Load the 'matrix' dict from a json file.
        """
        self.log.debug('* loading matrix ...')
        fpath = os.path.join(dir_path, 'matrix.json')
        if os.path.exists(fpath):
            with open(fpath) as f:
                try:
                    matrix.update(json.loads(f.read()))
                    self.log.debug(f'  {len(matrix)} objects loaded.')
                except:
                    return 'fail'
            return 'success'
        else:
            return 'not found'

    def start(self, home=None, console=False, debug=False, log_msgs=None,
              **kw):
        """
        Initialization logic.

        Args:
            home (str):  home directory (full path)
            console (bool):  (default: False)
                if True: send output to console
                if False: redirect stdout/stderr to log file
            debug (bool):  (default: False) log in debug mode
            log_msgs (list of str):  initial log message(s)
        """
        if self.started:
            return
        self.log_msgs = log_msgs or []
        # initialize user_raz
        self.user_raz = []
        # initialize role_oids_to_ids
        self.role_oids_to_ids = {}
        # set home directory -- in order of precedence (A, B, C):
        # [A] 'home' kw arg (this should be set by the application, if any)
        if home:
            marv_home = home
        # [B] from 'PANGALACTIC_HOME' env var
        elif 'PANGALACTIC_HOME' in os.environ:
            marv_home = os.environ['PANGALACTIC_HOME']
        # [C] create a 'marvin_home' directory in the user's home dir
        else:
            if sys.platform == 'win32':
                default_home = os.path.join(os.environ.get('USERPROFILE'))
                if os.path.exists(default_home):
                    marv_home = os.path.join(default_home, 'marvin_home')
            else:
                user_home = os.environ.get('HOME')
                if user_home:
                    marv_home = os.path.join(user_home, 'marvin_home')
                else:
                    # TODO:  a first-time dialog/wizard to set marv_home ...
                    # current fallback is just to use the current directory
                    marv_home = os.path.join(os.getcwd(), 'marvin_home')
        if not os.path.exists(marv_home):
            os.makedirs(marv_home, mode=0o755)
        marv_home = os.path.abspath(marv_home)
        # --------------------------------------------------------------------
        # ### NOTE:  user-set config overrides app config
        # --------------------------------------------------------------------
        # If values in the "config" file have been edited, they will take
        # precedence over any config set by app defaults:  'read_config()' does
        # config.update() from the "config" file contents.
        read_config(os.path.join(marv_home, 'config'))
        # --------------------------------------------------------------------
        # ### NOTE:  saved "state" file represents most recently saved state
        # ###        of the app -- so in case any new items have been added to
        # ###        state at the app level (which would be in the current,
        # ###        in-memory state dict), copy that to "app_state" and update
        # ###        the saved state with it as necessary ... in particular,
        # ###        check for any new dashboards.
        app_state = deepcopy(state)
        read_state(os.path.join(marv_home, 'state'))
        # --------------------------------------------------------------------
        # Saved prefs and trash are read here; will be overridden by
        # any new prefs and trash set at runtime.
        read_prefs(os.path.join(marv_home, 'prefs'))
        read_trash(os.path.join(marv_home, 'trash'))
        # create "file vault"
        self.vault = os.path.join(marv_home, 'vault')
        if not os.path.exists(self.vault):
            os.makedirs(self.vault, mode=0o755)
        self.logging_initialized = False
        self.start_logging(home=marv_home, console=console, debug=debug)
        # self.log.debug('* config read ...')
        self.log.debug('* state read ...')
        self.log.debug('  checking for updates to state ...')
        # check for new app dashboards in state
        new_dashes = []
        app_dashes = {}
        if app_state and app_state.get('app_dashboards'):
            app_dashes = app_state['app_dashboards']
        for dash_name in app_dashes:
            if dash_name not in state['app_dashboards']:
                state['app_dashboards'][dash_name] = app_dashes[dash_name]
                new_dashes.append(dash_name)
        if new_dashes:
            dashes = str(new_dashes)
            self.log.debug(f'  new dashboards found, added: {dashes}')
        # check for new default parameters, data elements in state
        app_parms = []
        if app_state and app_state.get('default_parms'):
            app_parms = app_state['default_parms']
        if not state.get('default_parms'):
            state['default_parms'] = []
        for pid in app_parms:
            if pid not in state['default_parms']:
                state['default_parms'].append(pid)
        app_data_elements = []
        if app_state and app_state.get('default_data_elements'):
            app_data_elements = app_state['default_data_elements']
        if not state.get('default_data_elements'):
            state['default_data_elements'] = []
        for deid in app_data_elements:
            if deid not in state['default_data_elements']:
                state['default_data_elements'].append(deid)
        # check for default_schema_name
        app_schema_name = 'MEL'
        if app_state and app_state.get('default_schema_name'):
            app_schema_name = app_state['default_schema_name']
        if not state.get('default_schema_name'):
            state['default_schema_name'] = app_schema_name
        # check for p_defaults (default parameter values)
        app_p_defaults = {}
        if app_state and app_state.get('p_defaults'):
            app_p_defaults = app_state['p_defaults']
        if not state.get('p_defaults'):
            state['p_defaults'] = app_p_defaults
        # self.log.debug('  state: {}'.format(str(state)))
        # self.log.debug('* prefs read ...')
        # self.log.debug('  prefs: {}'.format(str(prefs)))
        self.log.debug('* trash read ({} objects).'.format(len(trash)))
        if 'units' not in prefs:
            prefs['units'] = {}
        self.cache_path = os.path.join(marv_home, 'cache')
        home_schema_version = state.get('schema_version')
        if (home_schema_version is None or
            home_schema_version == schema_version):
            # home_schema_version is None or matches the app schema_version,
            # just initialize the registry.
            # NOTE:  registry 'debug' is set to False regardless of the
            # client's log level because its debug logging is INSANELY verbose
            # ...  if the registry needs debugging, just hack this and set
            # debug=True.
            self.log.debug(f'* schema version {schema_version} matches ...')
            self.log.debug('  initializing registry ...')
            self.init_registry(marv_home, version=schema_version, log=self.log,
                               debug=False, console=console)
            self.log.debug('  registry initialized.')
            self.classes = {cname : metathing(cname, (), {})
                            for cname in schemas}
        else:
            # NOT the latest schema -> rebuild everything ...
            self.log.debug('* schema versions do not match:')
            self.log.debug(f'    app schema version =  {schema_version}')
            self.log.debug(f'    home schema version = {home_schema_version}')
            # if the state 'schema_version' does not match the current
            # package's schema_version:
            dump_path = os.path.join(marv_home, 'db.yaml')
            # [1] remove .json caches and "cache" directory:
            self.log.debug('  [1] removing caches ...')
            for prefix in ['data_elements', 'diagrams', 'parameters',
                           'schemas']:
                fpath = os.path.join(marv_home, prefix + '.json')
                if os.path.exists(fpath):
                    os.remove(fpath)
            self.log.debug('      + json caches removed.')
            if os.path.exists(self.cache_path):
                shutil.rmtree(self.cache_path, ignore_errors=True)
            self.log.debug('      + class/property caches removed.')
            # [2] initialize registry with "force_new_core" to create the new
            #     classes and db:
            self.log.debug('  [2] initializing registry ...')
            self.init_registry(marv_home, force_new_core=True,
                               version=schema_version, debug=False,
                               console=console)
            self.classes = {cname : metathing(cname, (), {})
                            for cname in schemas}
            # [3] load reference data (needed before deserializing the db dump)
            self.log.debug('  [3] calling load_reference_data() ...')
            self.load_reference_data()
            # [4] transform and import data that was dumped previously:
            self.log.debug('  [4] reloading dumped data ...')
            serialized_data = self.load_and_transform_data(dump_path)
            if serialized_data:
                deserialize(self, serialized_data, include_refdata=True)
            state['schema_version'] = schema_version
            write_state(os.path.join(marv_home, 'state'))
            # check for private key in old key path
            self.log.debug('  [5] checking for old private keys ...')
            self.log.debug('      (for transition from 1.4.x versions)')
            old_key_path = os.path.join(marv_home, '.creds', 'private.key')
            if os.path.exists(old_key_path):
                self.log.debug('      found old "private.key" ...')
                # if found, copy key to user home dir and remove '.creds' dir
                p = Path(marv_home)
                absp = p.resolve()
                user_home = absp.parent
                new_key_path = os.path.join(str(user_home), 'cattens.key')
                # only copy key to new_key_path if there is no key there ...
                # i.e. if user has not used a new dev version
                if os.path.exists(new_key_path):
                    self.log.debug('      found "cattens.key", not replacing.')
                    self.log.debug('      may need to submit public key.')
                else:
                    shutil.copyfile(old_key_path, new_key_path)
                    self.log.debug('      copying old key to new location ...')
                    self.log.debug('      should be able to log in now.')
                # in any case, remove the old key, since it's not used now
                shutil.rmtree(os.path.join(marv_home, '.creds'),
                              ignore_errors=True)
                self.log.debug('      done with keys.')
        #############################################
        # POST registry-initialization operations ...
        #############################################
        # * copy test data files from 'p.test.data' module to test_data_dir
        self.test_data_dir = os.path.join(marv_home, 'test_data')
        current_test_files = set()
        self.log.debug('* checking for test data in [marv_home]/test_data...')
        if not os.path.exists(self.test_data_dir):
            os.makedirs(self.test_data_dir)
        else:
            current_test_files = set(os.listdir(self.test_data_dir))
        # self.log.debug('  - found {} data files'.format(
                       # len(current_test_files)))
        test_data_mod_path = test_data_mod.__path__[0]
        test_data_files = set([s for s in os.listdir(test_data_mod_path)
                               if (not s.startswith('__init__')
                               and not s.startswith('__pycache__'))
                               ])
        test_data_to_copy = test_data_files - current_test_files
        # self.log.debug('  - {} data files to be installed: '.format(
                       # len(test_data_to_copy)))
        if test_data_to_copy:
            # self.log.debug('  - copying data files into test_data dir...')
            test_data_cpd = []
            for p in test_data_to_copy:
                shutil.copy(os.path.join(test_data_mod_path, p),
                            self.test_data_dir)
                test_data_cpd.append(p)
            # self.log.debug('  - new test data files installed: %s'
                          # % str(test_data_cpd))
        # else:
            # self.log.debug('  - all test data files already installed.')
        # * copy files from 'p.test.vault' module to vault_dir
        # self.log.debug('* checking for files in [marv_home]/vault ...')
        current_vault_files = set(os.listdir(self.vault))
        # self.log.debug('  - found {} vault files:'.format(
                       # len(current_vault_files)))
        # if current_vault_files:
            # for fpath in current_vault_files:
                # self.log.debug('    {}'.format(fpath))
        vault_mod_path = test_vault_mod.__path__[0]
        test_vault_files = set([s for s in os.listdir(vault_mod_path)
                               if (not s.startswith('__init__')
                               and not s.startswith('__pycache__'))
                               ])
        vault_files_to_copy = test_vault_files - current_vault_files
        # self.log.debug('  - new test vault files to be installed: {}'.format(
                       # len(vault_files_to_copy)))
        if vault_files_to_copy:
            # self.log.debug('  - copying test vault files into vault dir...')
            vault_files_copied = []
            for p in vault_files_to_copy:
                shutil.copy(os.path.join(vault_mod_path, p), self.vault)
                vault_files_copied.append(p)
            # self.log.debug('  - new test vault files installed: {}'.format(
                           # str(vault_files_copied)))
        # else:
            # self.log.debug('  - all test vault files already installed.')
        # basically, versionables == {Product and all its subclasses}
        self.versionables = [cname for cname in schemas if 'version' in
                             schemas[cname]['field_names']]
        # load the "matrix" and initialize the db
        self.matrix_status = self.load_matrix(self.home)
        if self.matrix_status == 'success':
            self.log.debug(f'* matrix loaded with {len(matrix)} entries.')
            # initialize db objects ...
            self.log.debug('  initializing "db" (object cache) ...')
            for oid in matrix:
                cname = matrix[oid]['_cname']
                # self.create_or_update_thing(matrix[oid]['_cname'], oid=oid)
                cls = self.classes[cname]
                db[oid] = cls(oid=oid)
            self.log.debug(f'  - initialized with {len(db)} objects.')
        # load (and update) ref data ... note that this must be done AFTER
        # config and state have been created and updated (except in the case
        # that the schema version doesn't match and we have to load data from a
        # dump)
        self.load_user_raz(self.home)
        self.load_reference_data()
        # load "componentz" and allocation-related caches
        self.load_assembly_cache_data()
        # load the cached block diagrams
        self._load_diagramz()
        # populate 'role_oids_to_ids' cache
        self.role_oids_to_ids.update({role.oid : role.id
                                      for role in self.get_by_type('Role')})
        # create 'role_product_types' cache
        self.role_product_types = {}
        # discipline_subsystems maps Discipline ids to ProductType ids
        discipline_subsystems = {}
        for dpt in self.get_by_type('DisciplineProductType'):
            did = getattr(dpt.used_in_discipline, 'id', '')
            ptid = getattr(dpt.relevant_product_type, 'id', '')
            if did in discipline_subsystems:
                if did and ptid:
                    discipline_subsystems[did].append(ptid)
            elif did and ptid:
                discipline_subsystems[did] = [ptid]
        # role_disciplines maps Role ids to related Discipline ids
        role_disciplines = {}
        for dr in self.get_by_type('DisciplineRole'):
            rtdid = getattr(dr.related_to_discipline, 'id', '')
            rrid = getattr(dr.related_role, 'id', '')
            if rrid in role_disciplines:
                if rrid and rtdid:
                    role_disciplines[rrid].append(rtdid)
            elif rrid and rtdid:
                role_disciplines[rrid] = [rtdid]
        for role_id, discipline_ids in role_disciplines.items():
            for discipline_id in discipline_ids:
                if discipline_id in discipline_subsystems:
                    if role_id in self.role_product_types:
                        self.role_product_types[role_id] |= set(
                            discipline_subsystems.get(discipline_id))
                    else:
                        self.role_product_types[role_id] = set(
                            discipline_subsystems.get(discipline_id))
        self.started = True
        # TODO:  clean up boilerplate ...
        save_data_elementz(self.home)
        save_parmz(self.home)
        self.save_matrix(self.home)
        self.log.debug('* orb startup completed.')
        return self.home

    def init_registry(self, home, force_new_core=False, version='', log=None,
                      debug=False, console=False):
        self.registry = Tachistry(home=home, cache_path=self.cache_path,
                                  version=version, log=log, debug=debug,
                                  console=console,
                                  force_new_core=force_new_core)
        self.home = self.registry.home
        self.schemas = schemas
        # NOTE: self.classes is constructed in the start() method
        self.mbo = self.registry.metaobject_build_order()

    def dump_db(self, fpath=None, dir_path=None):
        """
        Serialize the database objects to `db-dump-[dts].yaml` (or '.json', if
        specified) in the specified directory.

        Keyword Args:
            fpath (str):  file path to save to (overrides dir_path)
            dir_path (str):  directory path to save to
        """
        self.log.info('* dump_db()')
        dts = file_dts()
        if fpath:
            dir_path, fname = os.path.split(fpath)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        else:
            if not dir_path:
                # if neither fpath nor dir_path specified, assume backup
                dir_path = os.path.join(self.home, 'backup')
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            fname = 'db-dump-' + dts + '.yaml'
        self.log.info('  dumping matrix to yaml ...')
        serialized_objs = serialize(self, db.values())
        f = open(os.path.join(dir_path, fname), 'w')
        f.write(yaml.safe_dump(serialized_objs, default_flow_style=False))
        f.close()
        self.log.info('  dump to yaml completed.')
        self.log.debug('  {} objects written.'.format(len(serialized_objs)))

    def save_caches(self, dir_path=None):
        """
        Serialize all caches (matrix, data_elementz and parameterz) to files
        and:

            1. if no directory is specified, save the files in the home
               directory and save copies to a backup directory named with the
               date stamp.

            2. if a directory is specified, save the files in the home
               directory and save copies in the specified directory.

        Note that only one backup for any given day will be preserved, because
        the backup directory name is the date so the last backup on a given day
        will overwrite any previous backups for that day.
        """
        self.log.info('* save_caches()')
        self.cache_dump_complete = False
        backup = False
        # [1] save all caches to home
        save_data_elementz(self.home)
        save_parmz(self.home)
        self.save_matrix(self.home)
        self.save_user_raz(self.home)
        save_allocz(self.home)
        save_de_defz(self.home)
        save_parmz_by_dimz(self.home)
        save_compz(self.home)
        save_systemz(self.home)
        save_rqt_allocz(self.home)
        self.log.info('  cache saves completed ...')
        # [2] save all caches to backup dir
        if not dir_path:
            # if no dir_path specified, backup
            backup = True
            backup_path = os.path.join(self.home, 'backup')
            dts = file_date_stamp()
            dir_path = os.path.join(backup_path, dts)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        save_data_elementz(dir_path)
        save_parmz(dir_path)
        self.save_matrix(dir_path)
        self.save_user_raz(dir_path)
        save_allocz(dir_path)
        save_de_defz(dir_path)
        save_parmz_by_dimz(dir_path)
        save_compz(dir_path)
        save_systemz(dir_path)
        save_rqt_allocz(dir_path)
        self.cache_dump_complete = True
        if backup:
            self.log.info('  cache backup completed.')
        else:
            self.log.info('  cache dump completed.')

    def dump_all(self, dir_path=None):
        self.save_caches(dir_path=dir_path)
        # self.dump_db(dir_path=dir_path)

    def _load_diagramz(self):
        """
        Load `diagramz` cache from diagrams.json file.
        """
        json_path = os.path.join(self.home, 'diagrams.json')
        if os.path.exists(json_path):
            with open(json_path) as f:
                diagramz.update(json.loads(f.read()))
            # self.log.debug('* diagramz cache read from diagrams.json')
        else:
            # self.log.debug('* no diagrams.json file found.')
            pass

    def _save_diagramz(self):
        """
        Save `diagramz` cache to diagrams.json file.
        """
        # self.log.debug('* _save_diagramz() ...')
        json_path = os.path.join(self.home, 'diagrams.json')
        with open(json_path, 'w') as f:
            f.write(json.dumps(diagramz, separators=(',', ':'),
                               indent=4, sort_keys=True))
        # self.log.debug('  ... diagrams.json file written.')

    def create_or_update_thing(self, cname, **kw):
        """
        Create an instance of Thing with the specified attributes.
        NOTE: if an oid is specified and an object with that oid exists, the
        existing object will be returned and the matrix will be updated with
        the other keyword args if the 'mod_datetime' is later than the one
        currently in the matrix.

        Args:
            cname (str): name of the associated domain class

        Keyword Args:
            kw (dict): can contain the 'oid' and any number of other attributes
                in the schema of the associated domain class
        """
        if cname not in list(schemas):
            self.log.debug('  invalid class name')
            return None
        oid = kw.get('oid')
        schema = schemas[cname]
        # filter kw for valid attrs
        valid_kw = {a : kw[a] for a in kw if a in schema['field_names']}
        if oid and oid in db:
            # self.log.debug(f'+ oid {oid} found in db')
            thing = db[oid]
            kw_dt = valid_kw.get('mod_datetime')
            # make sure kw mod_datetime is "stringified", e.g. if it is a
            # datetime object
            if kw_dt and (str(kw_dt) > thing.mod_datetime):
                # the created class will update the matrix ...
                self.log.debug(f'  kw mod_dt: {kw_dt}')
                self.log.debug(f'  thing mod_dt: {thing.mod_datetime}')
                self.log.debug('  mod_dt is later, thing will be updated ...')
                self.log.debug(f'  oid: "{thing.oid}"')
                self.log.debug(f'  id: "{thing.id}"')
                self.log.debug(f'  valid kw: "{valid_kw}"')
                valid_kw['mod_datetime'] = str(kw_dt)
                matrix[oid].update(valid_kw)
            return thing
        # NOTE: unnecessary to generate an oid here -- __init__ will do that
        # else:
            # valid_kw[oid] = str(uuid4())
        # class instantiation will update the matrix
        thing = self.classes[cname](**valid_kw)
        db[thing.oid] = thing
        return thing

    def assign_test_parameters(self, objs, parms=None, des=None):
        """
        Assign a set of test parameters and data elements with
        randomly-generated values to an iterable of objects.

        Args:
            objs (iterable of Modelable):  objects the test parameters and data
                elements will be assigned to
        """
        self.log.debug('* assign_test_parameters()')
        for o in objs:
            add_default_data_elements(o, des=des)
            gen_test_dvals(data_elementz[o.oid])
            add_default_parameters(o, parms=parms)
            gen_test_pvals(parameterz[o.oid])
        self.log.debug('  ... done.')

    def start_logging(self, home=None, console=False, debug=False):
        """
        Create an orb log and begin writing to it.

        Keyword Args:
            home (str):  full path to app home directory (log files will be
                written into a 'log' subdirectory)
            console (bool):  (default: False)
                if True: send output to console
                if False: redirect stdout/stderr to log files
            debug (bool):  if True, set log level to 'debug'
        """
        if not self.logging_initialized:
            if not home:
                home = os.getcwd()
            self.log, self.error_log = get_loggers(home, 'orb', console=console,
                                                   debug=debug)
            self.log.propagate = False
            self.error_log.propagate = False
            self.log.info('* orb logging initialized ...')
            self.logging_initialized = True
            # log any initial 'log_msg' passed in at start()
            if self.log_msgs:
                for log_msg in self.log_msgs:
                    self.log.info(log_msg)

    def load_and_transform_data(self, data_path):
        """
        Load and transform all dumped serialized data to the new schema.
        Called when restarting after an upgrade that includes a schema change.

        Args:
            data_path (str):  path to yaml file containing dumped db data
        """
        self.log.info('* transforming all data to new schema ...')
        sdata = ''
        if os.path.exists(data_path):
            try:
                f = open(data_path)
                sdata = yaml.safe_load(f.read())
                if __version__ in schema_maps:
                    map_fn = schema_maps[__version__]
                    sdata = map_fn(sdata)
                    self.log.debug('  - data loaded and transformed.')
                else:
                    self.log.debug('  - data loaded (transformation unnec.).')
            except:
                self.log.debug('  - an error ocurred (see error log).')
                self.error_log.info('* error in load_and_transform_data():')
                self.error_log.info(traceback.format_exc())
        else:
            self.log.debug(f'  - file "{data_path}" not found.')
        return sdata

    def save_user_raz(self, dir_path):
        """
        Save the `user_raz` cache to user_roles.json file.
        """
        self.log.debug('* save_user_raz() ...')
        fpath = os.path.join(dir_path, 'user_roles.json')
        with open(fpath, 'w') as f:
            f.write(json.dumps(self.user_raz, separators=(',', ':'),
                               indent=4, sort_keys=True))
        self.log.debug(f'  ... user_roles.json file written to {dir_path}.')


    def load_user_raz(self, dir_path):
        """
        Load the `user_raz` cache from user_roles.json file.
        """
        self.log.debug('* load_user_raz() ...')
        fpath = os.path.join(dir_path, 'user_roles.json')
        if os.path.exists(fpath):
            with open(fpath) as f:
                self.user_raz += json.loads(f.read())
            self.log.debug('  - user_raz cache loaded.')
            return 'success'
        else:
            self.log.debug('  - "user_roles.json" was not found.')
            return 'not found'

    def load_reference_data(self):
        """
        Create reference data objects.  Performed at orb start up, since new
        objects created at runtime refer to some of the reference objects.
        """
        self.log.info('* checking reference data ...')
        # first get the oids of everything in the db ...
        db_oids = list(db)
        # [0] load initial reference data (Orgs, Persons, Roles,
        # RoleAssignments)
        missing_i = [so for so in refdata.initial if so['oid'] not in db_oids]
        if missing_i:
            self.log.debug('  + missing some initial reference data:')
            self.log.debug('  {}'.format([so['oid'] for so in missing_i]))
            i_objs = deserialize(self, [so for so in missing_i],
                                 include_refdata=True,
                                 force_no_recompute=True)
            self.save(i_objs)
        admin = self.get('pgefobjects:admin')
        pgana = self.get('pgefobjects:PGANA')
        self.log.info('  + initial reference data loaded.')
        # [1] load any parameter definitions and contexts that may be missing
        #     from the current db (in a first-time installation, this will of
        #     course be *all* parameter definitions and contexts)
        # ---------------------------------------------------------------------
        # NOTE: THIS STEP IS UNNECESSARY IN THE TORB SINCE 'parm_defz' is
        # recreated from refdata at runtime.
        # ---------------------------------------------------------------------
        # missing_p = [so for so in refdata.pdc if so['oid'] not in db_oids]
        # if missing_p:
            # self.log.debug('  + missing some reference parameters/contexts:')
            # self.log.debug('  {}'.format([so['oid'] for so in missing_p]))
            # p_objs = deserialize(self, [so for so in missing_p],
                                 # include_refdata=True,
                                 # force_no_recompute=True)
            # self.save(p_objs)
        # [1.1] load any data element definitions that may be missing
        #     from the current db (in a first-time installation, this will of
        #     course be *all* data element definitions)
        missing_d = [so for so in refdata.deds if so['oid'] not in db_oids]
        if missing_d:
            self.log.debug('  + missing some reference data elements:')
            self.log.debug('  {}'.format([so['oid'] for so in missing_d]))
            d_objs = deserialize(self, [so for so in missing_d],
                                 include_refdata=True,
                                 force_no_recompute=True)
            self.save(d_objs)
        # [2] XXX IMPORTANT!  Load the parameter definitions caches
        # ('parm_defz', 'parmz_by_dimz' 'de_defz') before loading parameters
        # from 'parameters.json' -- the deserializer uses these caches.
        self.create_parm_defz()
        load_de_defz(self.home)
        load_parmz_by_dimz(self.home)
        # *** NOTE ***********************************************************
        # [3] run _load_parmz() and _load_data_elementz() before checking for
        # updates to data element definitions and parameter definitions and
        # contexts, since updated ref data may update data element and
        # parameter data that was loaded from the parameters cache
        # (parameters.json) -- e.g., some ref data objects might have updated
        # parameters
        # ********************************************************************
        self.data_elementz_status = load_data_elementz(self.home)
        self.parmz_status = load_parmz(self.home)
        # self.log.debug('  dmz: {}'.format(str(dmz)))
        # [4] check for updates to parameter definitions and contexts
        # self.log.debug('  + checking for updates to parameter definitions ...')
        all_pds = refdata.pdc
        all_pd_oids = [so['oid'] for so in all_pds]
        # get mod_datetimes of all current ref data objects
        pd_mod_dts = self.get_mod_dts(oids=all_pd_oids)
        # compare them to all newly imported refdata objects
        updated_pds = [so for so in all_pds
                       if (so.get('mod_datetime') and
                           pd_mod_dts.get(so['oid']) and
                           (so.get('mod_datetime') >
                            pd_mod_dts.get(so['oid'])))] 
        if updated_pds:
            # self.log.debug('    {} updates found ...'.format(len(updated_pds)))
            deserialize(self, updated_pds, include_refdata=True)
            # self.log.debug('    parameter definition updates completed.')
        # else:
            # self.log.debug('    no updates found.')
        # [5] load balance of any reference data missing from db
        missing_c = [so for so in refdata.core if so['oid'] not in db_oids]
        objs = []
        if missing_c:
            self.log.debug('  + missing some core reference data:')
            self.log.debug('  {}'.format([so['oid'] for so in missing_c]))
            objs = deserialize(self, [so for so in missing_c],
                               include_refdata=True,
                               force_no_recompute=True)
        for o in objs:
            if hasattr(o, 'owner'):
                o.owner = pgana
                o.creator = o.modifier = admin
        # [6] check for updates to reference data other than parameter defs
        # self.log.debug('  + checking for updates to reference data ...')
        all_ref = refdata.initial + refdata.core + refdata.deds
        all_ref_oids = [so['oid'] for so in all_ref]
        # get mod_datetimes of all current ref data objects
        mod_dts = self.get_mod_dts(oids=all_ref_oids)
        # compare them to all newly imported refdata objects
        updated_r = [so for so in all_ref
                     if (so.get('mod_datetime') and
                         mod_dts.get(so['oid']) and
                         (so.get('mod_datetime') >
                          mod_dts.get(so['oid'])))] 
        if updated_r:
            # self.log.debug('    {} updates found ...'.format(len(updated_r)))
            deserialize(self, updated_r, include_refdata=True)
            # self.log.debug('    updates completed.')
        # else:
            # self.log.debug('    no updates found.')
        # [7] delete deprecated reference data
        #     **********************************************************
        #     NOTE:  DON'T DO THIS STEP UNTIL ALL DATA RELATED TO THE
        #     DEPRECATED DATA HAS BEEN REMOVED FROM THE CURRENT DATABASE
        #     **********************************************************
        db_oids = list(db)
        deprecated = [oid for oid in refdata.deprecated if oid in db_oids]
        if deprecated:
            self.log.debug('  + deleting deprecated reference data:')
            self.log.debug('  {}'.format([oid for oid in deprecated]))
            for oid in deprecated:
                self.delete([self.get(oid) for oid in deprecated])
        ####################################################################
        self.log.info('  + all reference data loaded.')

    def load_assembly_cache_data(self):
        """
        Load caches of assembly structures ("componentz") and requirement
        allocations.
        """
        load_compz(self.home)
        load_systemz(self.home)
        load_allocz(self.home)
        load_rqt_allocz(self.home)

    #########################################################################
    # PARAMETER AND DATA ELEMENT STUFF
    # Note:  ParameterDefinition and DataElementDefinition may eventually
    # be removed from the db and become independent of the orb, and move back
    # to the parametrics module ...
    #########################################################################

    def create_parm_defz(self):
        """
        Create the `parm_defz` cache of ParameterDefinitions from refdata, in
        the format:

            {parameter_id : {name, variable, context, context_type, description,
                             dimensions, range_datatype, computed, mod_datetime},
             data_element_id : {name, description, range_datatype, mod_datetime},
             ...}
        """
        # --------------------------------------------------------------------
        # NOTE: all parameters containing '_operational', '_survival',
        # '_throughput' are deprecated -- these have now been implemented as
        # ParameterContexts [2022-01-16 SCW]
        # --------------------------------------------------------------------
        # self.log.debug('* create_parm_defz')
        pds = [so for so in refdata.pdc
               if so['_cname'] == 'ParameterDefinition']
        # first, the "variable" parameters ...
        pd_dict = {pd['id'] :
                   {'name': pd['name'],
                    'variable': pd['id'],
                    'context': None,
                    'context_type': None,
                    'description': pd['description'],
                    'dimensions': pd['dimensions'],
                    'range_datatype': pd['range_datatype'],
                    'computed': False,
                    'mod_datetime':
                        str(pd.get('mod_datetime', '') or dtstamp())
                    } for pd in pds}
        parm_defz.update(pd_dict)
        # var_ids = sorted(list(pd_dict), key=str.lower)
        # self.log.debug('      bases created: {}'.format(
                                                # str(list(pd_dict.keys()))))
        # add PDs for the descriptive contexts (CBE, Contingency, MEV) for the
        # variables (Mass, Power, Datarate) for which functions have been defined
        # to compute the CBE and MEV values
        all_contexts = [so for so in refdata.pdc
                        if so['_cname'] == 'ParameterContext']
        # self.log.debug('      adding context parms for: {}'.format(
                                        # str([c.id for c in all_contexts])))
        for pd in pds:
            for c in all_contexts:
                parm_defz[get_parameter_id(pd['id'], c['id'])] = {
                    'name': get_parameter_name(pd['name'],
                                               c['abbreviation'] or c['id']),
                    'variable': pd['id'],
                    'context': c['id'],
                    'context_type': c['context_type'],
                    'description': get_parameter_description(
                                        pd['description'], c['description']),
                    'dimensions': c.get('context_dimensions') or pd[
                                                            'dimensions'],
                    'range_datatype': c.get('context_datatype') or pd[
                                                            'range_datatype'],
                    'computed': c['computed'],
                    'mod_datetime': str(dtstamp())}

    def create_parmz_by_dimz(self):
        """
        Create the `parmz_by_dimz` cache, where the cache has the form

            {dimension : [ids of ParameterDefinitions having that dimension]}
        """
        self.log.debug('* create_parmz_by_dimz')

    ##########################################################################
    # DB FUNCTIONS
    ##########################################################################

    def save(self, objs, recompute=True):
        """
        Save the specified objects.  (CAVEAT: this will update the object if it
        already exists in db.)

        NOTE:  alteration of the 'mod_datetime' of objects is *NOT* a
        side-effect of the orb save() function, because the orb.save() is used
        for both local objects and objects received from remote (network)
        sources, whose 'mod_datetime' must be preserved when saving locally.
        Therefore, locally created or modified objects must be time-stamped
        *before* they are passed to orb.save().

        Args:
            objs (iterable of objects):  the objects to be saved
        """
        for obj in objs:
            cname = obj.__class__.__name__
            oid = getattr(obj, 'oid', None)
            new = bool(oid in self.new_oids)
            if new:
                log_txt = 'orb.save: {} is a new {}, saving it ...'.format(
                           getattr(obj, 'id', '[unknown]'), cname)
                self.log.debug('* {}'.format(log_txt))
                if obj.oid in self.new_oids:
                    self.new_oids.remove(obj.oid)
            else:
                # updating an existing object
                log_txt = 'orb.save: "{}" is existing {}, updating ...'.format(
                           getattr(obj, 'id', '[unknown]'), cname)
                self.log.debug('* {}'.format(log_txt))
                # NOTE:  in new paradigm, obj is versioned iff
                # [1] it has a 'version' attr and
                # [2] a non-null version has been assigned to it (i.e. neither
                # None nor an empty string)
                if self.is_versionable(obj):
                    # if obj is versionable, bump its iteration #
                    # NOTE:  TODO (maybe) yes, this means iterations are not
                    # tracked in the db ... that's a separate issue
                    if isinstance(obj.iteration, int):
                        obj.iteration += 1
                    else:
                        obj.iteration = 1
            if hasattr(obj, 'owner') and not obj.owner:
                # ensure 'owner' is always populated if present!
                if obj.creator and getattr(obj.creator, 'org', None):
                    # first fallback:  owner is creator's org ...
                    obj.owner = obj.creator.org
                else:
                    # ultimate fallback:  owner is PGANA
                    obj.owner = self.get('pgefobjects:PGANA')
            elif cname == 'HardwareProduct':
                # make sure HW Products have mass, power, data rate parms
                if obj.oid not in parameterz:
                    parameterz[obj.oid] = {}
                for pid in ['m', 'P', 'R_D']:
                    if not parameterz[obj.oid].get(pid):
                         add_parameter(obj.oid, pid)
            elif cname == 'Role':
                self.role_oids_to_ids[obj.oid] = obj.id
        return True

    def obj_view_to_dict(self, obj, view):
        d = {}
        schema = schemas.get(obj.__class__.__name__)
        if not schema:
            # this will only be the case for a NullObject, which is only used for
            # ObjectSelectionDialog as a "None" choice, so the only fields needed
            # are id, name, description
            return {'id': 'None',
                    'name': '',
                    'description': ''}
        for a in view:
            if a in schema['field_names']:
                if a == 'id':
                    d[a] = obj.id
                elif a in TEXT_PROPERTIES:
                    d[a] = (getattr(obj, a) or ' ').replace('\n', ' ')
                elif schema['fields'][a]['range'] == 'datetime':
                    d[a] = dt2local_tz_str(getattr(obj, a))
                elif schema['fields'][a]['field_type'] == 'object':
                    rel_obj = getattr(obj, a)
                    if rel_obj.__class__.__name__ == 'ProductType':
                        d[a] = rel_obj.abbreviation or ''
                    elif rel_obj.__class__.__name__ in ['HardwareProduct',
                                                        'Organization',
                                                        'Person', 'Project']:
                        d[a] = rel_obj.id or rel_obj.name or '[unnamed]'
                    else:
                        if rel_obj is None:
                            d[a] = '[None]'
                        else:
                            d[a] = (getattr(rel_obj, 'id', None) or
                                    '[unidentified]')
                else:
                    d[a] = str(getattr(obj, a))
            elif a in parm_defz:
                pd = parm_defz.get(a)
                units = prefs['units'].get(pd['dimensions'], '') or in_si.get(
                                                        pd['dimensions'], '')
                d[a] = get_pval_as_str(obj.oid, a, units=units)
            elif a in de_defz:
                d[a] = get_dval_as_str(obj.oid, a)
        return d

    def get(self, *args, **kw):
        """
        Get an object or objects from the db:

          [1] if a positional argument is given, its oid
          [2] if 'oids' is a keyword argument, by a list of oids

        Args:
            args (tuple):  if populated, its first element is interpreted as
                the oid of an object in the db

        Keyword Args:
            kw (dict):  if 'oids' is a key, its value is interpreted as a list
                of oids of objects in the db

        Returns:
            one or more PGEF domain objects or an empty list or None
        """
        if args:
            # self.log.debug('* get(%s)' % oid[0])
            return db.get(args[0])
        elif kw:
            oids = kw.get('oids')
            # self.log.debug('* get(oids=%s)' % str(oids))
            # self.log.debug('* get(oids=({} oids))'.format(len(oids)))
            if oids:
                return [db.get(oid) for oid in oids]
            else:
                return []
        else:
            # self.log.debug('* get() [no arguments provided]')
            return None

    def get_count(self, cname):
        """
        Get a count of the objects of a given class in local db.
        NB:  this count includes all instances of SUBTYPES of the class.

        Args:
            cname (str):  the class name of the objects to be counted

        Returns:
            count (int)
        """
        # TODO: add a filter
        # self.log.debug('* get_count(%s)' % cname)
        return len([o for o in db.values() if o.__class__.__name__ == cname])

    def get_by_type(self, cname):
        """
        Get objects from the local db by class name.

        Args:
            cname (str):  the class name of the objects to be retrieved 

        Returns:
            an iterator of objects of the specified class (may be empty)
        """
        # self.log.debug('* get_by_type(%s)' % cname)
        return [o for o in db.values() if o.__class__.__name__ == cname]

    def get_subclass_names(self, cname):
        """
        Get subclass names of the specified class.

        Args:
            cname (str):  the class name to be referenced

        Returns:
            list of names of subclasses (may be empty)
        """
        e = self.registry.ces.get(cname)
        return self.registry.all_your_sub(e)

    def is_a(self, obj, cname):
        """
        Determine if an object is an instance of an orb domain class -- used in
        place of 'isinstance()' for instances of orb classes, since instances
        of the "thing" class are inheritance-unaware.

        Args:
            cname (str):  the supertype class name

        Returns:
            bool:  True if a subtype.
        """
        try:
            subclasses = tuple(set([self.classes[name] for name in
                                    self.get_subclass_names(cname)]))
            return isinstance(obj, subclasses)
        except:
            return False

    def get_all_subtypes(self, cname):
        """
        Get objects from the local db by class name, including all subtypes
        of the specified class.

        Args:
            cname (str):  the class name to be referenced

        Returns:
            list of objects of the specified class or a subclass (may be empty)
        """
        # self.log.debug('* get_all_subtypes(%s)' % cname)
        subnames = self.get_subclass_names(cname)
        return [o for o in db.values() if o.__class__.__name__ in subnames]

    def get_oids(self, cname=None):
        """
        Get all oids from the local db -- used for checking whether a given
        object is in the db or not.  Returns:

          [1] with no arguments:  all oids in the db
          [2] with 'cname':  all oids for objects of the specified class

        Keyword Args:
            cname (str):  class name of the objects to be used
        """
        return list(db)

    def get_ids(self, cname=None):
        """
        Get all ids from the local db -- used for validating ids.  Returns:

          [1] with no arguments:  all ids in the db
          [2] with 'cname':  all ids for objects of the specified class

        Keyword Args:
            cname (str):  class name of the objects to be used
        """
        if cname:
            objs = [o for o in db.values() if o.__class__.__name__ == cname]
        else:
            objs = db.values()
        return [o.id for o in objs]

    def gen_product_id(self, obj):
        """
        Create a unique 'id' attribute for a new HardwareProduct or Template.

        Args:
            obj (HardwareProduct or Template):  obj for which to generate an
                'id'
        """
        # self.log.debug('* gen_product_id')
        HW = self.classes['HardwareProduct']
        Template = self.classes['Template']
        if not isinstance(obj, (HW, Template)):
            return ''
        all_ids = self.get_ids(cname='HardwareProduct')
        all_ids += self.get_ids(cname='Template')
        # self.log.debug('  all_ids:')
        # self.log.debug('  {}'.format(str(all_ids)))
        id_suffixes = [(i or '').split('-')[-1] for i in all_ids]
        # self.log.debug('  id_suffixes:')
        # self.log.debug('  {}'.format(str(id_suffixes)))
        current_id_parts = (obj.id or '').split('-')
        # self.log.debug('  current_id_parts: {}'.format(
                                                # str(current_id_parts)))
        if current_id_parts[-1] in id_suffixes:
            id_suffixes.remove(current_id_parts[-1])
        owner_id = getattr(obj.owner, 'id', 'Owner-unspecified')
        # self.log.debug('  owner_id: {}'.format(owner_id))
        pt_abbr = getattr(obj.product_type, 'abbreviation', 'TBD') or 'TBD'
        # self.log.debug('  pt_abbr: {}'.format(pt_abbr))
        # test whether current id already conforms -- i.e., first part is
        # [owner.id or "Vendor"] + '-' + [product_type.abbrev.] + '-'
        # and last part (suffix) is unique
        if (len(current_id_parts) >= 3 and
            ((obj.id or '').startswith(owner_id + '-' + pt_abbr + '-')) and
            # suffix is unique (has been removed from id_suffixes once)
            current_id_parts[-1] not in id_suffixes):
            return obj.id
        hw_id_ints = [0]
        for i in id_suffixes:
            try:
                hw_id_ints.append(int(i))
            except:
                continue
        next_sufx = str(max(hw_id_ints)).zfill(7)
        while 1:
            if next_sufx not in id_suffixes:
                break
            else:
                next_int = max(hw_id_ints) + 1
                next_sufx = str(next_int).zfill(7)
        owner_id = owner_id or 'Vendor'
        abbrev = getattr(obj.product_type, 'abbreviation', 'TBD') or 'TBD'
        if obj.__class__.__name__ == 'Template':
            abbrev += '-Template'
        return '-'.join([owner_id, abbrev, next_sufx])

    def get_idvs(self, cname=None):
        """
        Return a list of (id, version) tuples:

          [1] with no arguments:  for all objects in the db
          [2] with 'cname':  for all objects of the specified class

        Keyword Args:
            cname (str):  class name of the objects to be used
        """
        if cname in self.versionables:
            return [(o.id, o.version) for o in self.get_by_type(cname)]
        else:
            return [(o.id, o.version) for o in db.values()]

    def get_mod_dts(self, cnames=None, oids=None, datetimes=False):
        """
        Get a dict that maps oids of objects to their 'mod_datetime' stamps as
        strings:

          [1] with no arguments:  for all objects in the db for which
              'mod_datetime' is not None.
          [2] with 'cname':  for all objects of the specified class
          [3] with 'oids':   for all objects whose oids are in the 'oids' list

        Keyword Args:
            cnames (list):  class names search parameter
            oids (list):  oids search parameter
            datetimes (bool):  if True, use datetime objects for
                datetime-stamp values; if False (default) convert them to
                strings

        Returns:
            dict:  mapping of oids to 'mod_datetime' strings.
        """
        objs = []
        if not cnames and not oids:
            objs = db.values()
        elif cnames:
            for cname in cnames:
                objs += self.get_by_type(cname)
        elif oids:
            objs = self.get(oids=oids)
        if datetimes:
            return {o.oid: o.mod_datetime for o in objs
                    if o.mod_datetime is not None}
        else:
            return {o.oid: str(o.mod_datetime) for o in objs
                    if o.mod_datetime is not None}

    def get_oid_cnames(self, oids=None, cname=None):
        """
        For a list of oids, get a dict that maps the oids to their class names.

        Keyword Args:
            oids (list):  oids of objects

        Returns:
            dict:  mapping of oids to class names.
        """
        if oids:
            objs = self.get(oids=oids)
        elif cname:
            objs = self.get_by_type(cname)
        else:
            return {}
        return {o.oid : o.__class__.__name__ for o in objs}

    def select(self, cname, **kw):
        """
        Get a single object from the local db by its class name and a set of
        criteria that is intended to identify a unique instance.  (NOTE: if the
        query results in multiple items, select returns the first item.)

        Args:
            cname (str):  class name of the object to be retrieved 

        Returns:
            obj (Identifiable or subtype) or None
        """
        self.log.debug(f'* select({cname}, **kw)')
        objs = self.get_by_type(cname)
        if objs:
            obj_ids = []
            for obj in objs:
                obj_id = getattr(obj, 'id', 'no id') or 'unknown'
                obj_ids.append(obj_id)
            # self.log.debug(f'  objects being searched: {obj_ids}')
        else:
            # self.log.debug(f'  no objects of class {cname} found.')
            return None
        schema = schemas[cname]
        # filter kw for valid attrs
        valid_kw = {a : kw[a] for a in kw if a in schema['field_names']}
        obj_kw = {a : kw[a] for a in valid_kw
                  if schema['fields'][a]['range'] in schemas}
        # if obj_kw:
            # self.log.debug('  object-valued criteria:')
            # for a, val in obj_kw.items():
                # if val is None:
                    # val_id = 'None'
                # else:
                    # val_id = val.id
                # self.log.debug(f'    {a} : {val_id}')
        # else:
            # self.log.debug('  no object-valued criteria')
        data_kw = {a : kw[a] for a in valid_kw
                   if a not in obj_kw}
        # if data_kw:
            # self.log.debug('  data-valued criteria:')
            # for a, val in data_kw.items():
                # self.log.debug(f'    {a} : {val}')
        # else:
            # self.log.debug('  no data-valued criteria')
        # matching = {}
        for o in objs:
            data_res = True
            obj_res = True
            # obj_oid = getattr(o, 'oid', 'no oid') or 'unknown'
            # matching[obj_oid] = []
            if data_kw:
                data_res = all([getattr(o, k) == data_kw[k] for k in data_kw])
            if obj_kw:
                obj_res = False
                res = []
                for k in obj_kw:
                    if obj_kw[k] is None and getattr(o, k, '') is None:
                        res.append(True)
                        # matching[obj_oid].append(
                                    # f'  {k}: None is None')
                    else:
                        o_oid = getattr(getattr(o, k, None),
                                        'oid', 'this') or 'this'
                        k_oid = getattr(obj_kw[k], 'oid', 'that') or 'that'
                        if k_oid == o_oid:
                            res.append(True)
                            # matching[obj_oid].append(
                                    # f'  {k}: "{o_oid}" == "{k_oid}"')
                        else:
                            res.append(False)
                obj_res = all(res)
            if data_res and obj_res:
                # self.log.debug(f'  object "{o.id}" matched:')
                # for x in matching[obj_oid]:
                    # self.log.debug(f'  {x}')
                return o
        # self.log.debug('  no object found.')
        return None

    def search_exact(self, **kw):
        """
        Search for instances that exactly match a set of attribute values.  The
        result will include all matching instances of any classes that contain
        all the requested attributes.

        A special keyword 'cname' can be used to specify that the search should
        be restricted to the named class specified by 'cname'.

        Keyword Args:
            kw (dict of kw args):  special key 'cname' specifies a class name

        Returns:
            list:  a list of objects
        """
        self.log.debug(f'* search_exact(**({str(kw)}))')
        cname = kw.pop('cname', None)
        if cname:
            if cname in schemas:
                # self.log.debug(f'* cname "{cname}" in schemas ...')
                schema = schemas[cname]
                attrs = [a for a in kw if a in schema['field_names']]
            else:
                # cname is not valid
                return []
        else:
            attrs = [a for a in kw if a in self.registry.pes]
        # self.log.debug(f'* attrs: {attrs}')
        if attrs:
            domains = [self.registry.pes[a]['domain'] for a in attrs]
            idx = max([self.mbo.index(d) for d in domains])
            domain = self.mbo[idx]
            # self.log.debug(f'  - domain: {domain}')
            ok_kw = {a : kw[a] for a in attrs}
            if cname:
                # if cname is supplied, check that it contains all attrs
                extr = self.registry.ces.get(cname)
                if extr:
                    bases = self.registry.all_your_base(extr) | set([cname])
                    # self.log.debug(f'  - bases of cname: {bases}')
                    if not domain in bases:
                        # class does not have all attrs: return empty list
                        return []
                else:
                    # cname is not a valid class: return empty list
                    return []
            elif not cname:
                # no cname specified -- find the most general class that
                # contains all specified parameters
                cname = domain
                self.log.debug(f'  - no cname kw, using: {cname}')
            # self.log.debug(f'  - ok_kw: {ok_kw}')
            schema = schemas[cname]
            objs = self.get_all_subtypes(cname)
            obj_kw = {a : kw[a] for a in ok_kw
                      if schema['fields'][a]['range'] in schemas}
            data_kw = {a : kw[a] for a in ok_kw if a not in obj_kw}
            result = []
            matching = {}
            for o in objs:
                data_res = True
                obj_res = True
                obj_oid = getattr(o, 'oid', 'no oid') or 'unknown'
                matching[obj_oid] = []
                if data_kw:
                    data_res = all([getattr(o, k) == data_kw[k] for k in data_kw])
                if obj_kw:
                    obj_res = False
                    res = []
                    for k in obj_kw:
                        if obj_kw[k] is None and getattr(o, k, '') is None:
                            res.append(True)
                            matching[obj_oid].append(f'  {k}: None is None')
                        else:
                            o_oid = getattr(getattr(o, k, None),
                                            'oid', 'this') or 'this'
                            k_oid = getattr(obj_kw[k], 'oid', 'that') or 'that'
                            if k_oid == o_oid:
                                res.append(True)
                                matching[obj_oid].append(
                                        f'  {k}: "{o_oid}" == "{k_oid}"')
                            else:
                                res.append(False)
                    obj_res = all(res)
                if data_res and obj_res:
                    # self.log.debug(f'  object "{o.id}" (oid {o.oid}) matched')
                    # for x in matching[obj_oid]:
                        # self.log.debug(f'  {x}')
                    result.append(o)
            self.log.debug(f'  result: {len(result)} objects:')
            for o in result:
                self.log.debug(f'  - "{o.id}" (oid {o.oid})')
            return result
        else:
            return []

    def get_internal_flows_of(self, managed_object):
        """
        Get all flows of which the specified ManagedObject is the
        'flow_context'.

        Args:
            managed_object (ManagedObject):  the specified object
        """
        # handle exception in case we get something that's not a Product
        # self.log.debug('* get_internal_flows_of()')
        try:
            flows = self.get_by_type('Flow')
            relevant_flows = [f for f in flows
                              if f.flow_context is managed_object]
            return relevant_flows
        except:
            return []

    def get_all_usage_flows(self, usage):
        """
        For an assembly component usage (Acu) or a ProjectSystemUsage, get all
        flows defined to or from its component/system object in the context of
        its assembly/project object.

        Args:
            usage (Acu or ProjectSystemUsage):  the specified usage
        """
        self.log.debug('* get_all_usage_flows()')
        if usage:
            oid = getattr(usage, 'oid', None)
            if oid:
                self.log.debug(f'  for usage <{oid}>')
            else:
                self.log.debug('  object provided had no "oid" -> no flows.')
                return []
        else:
            self.log.debug('  no usage provided -> no flows.')
            return []
        if usage.__class__.__name__ == 'ProjectSystemUsage':
            self.log.debug('  - no flows (Project context cannot have flows).')
            return []
        if usage.__class__.__name__ == 'Acu':
            assembly = usage.assembly
            component = usage.component
        else:
            self.log.debug('  usage was not an Acu -> no flows.')
            return []
        # in case we're dealing with a corrupted "usage" ...
        if not component or not component.ports:
            self.log.debug('  usage had no components/ports -> no flows.')
            return []
        self.log.debug(f'  - assembly id: "{assembly.id}"')
        self.log.debug(f'  - component id: "{component.id}"')
        flows = self.get_by_type('Flow')
        context_flows = [f for f in flows if f.flow_context is assembly]
        self.log.debug(f'  - # of context flows: {len(context_flows)}')
        ports = component.ports
        np = len(ports)
        port_ids = [p.id for p in component.ports]
        self.log.debug(f'  - {np} component ports: {port_ids}')
        flows = [flow for flow in context_flows
                 if flow.start_port in ports or flow.end_port in ports]
        if flows:
            flow_ids = [flow.id for flow in flows]
            nf = len(flow_ids)
            self.log.debug(f'  - {nf} associated flows: {flow_ids}')
        else:
            self.log.debug('  - no associated flows found.')
        return flows

    def gazoutas(self, port):
        """
        Get start_ports of all flows connecting to a port.

        Args:
            port (Port):  the specified Port
        """
        flows = self.get_by_type('Flow')
        flowzintas = [f for f in flows if f.end_port is port]
        return [flow.start_port for flow in flowzintas]

    def gazintas(self, port):
        """
        Get end_ports of all flows connecting to a port.

        Args:
            port (Port):  the specified Port
        """
        flows = self.get_by_type('Flow')
        flowzoutas = [f for f in flows if f.start_port is port]
        return [flow.end_port for flow in flowzoutas]

    def get_all_port_flows(self, port):
        """
        For a Port instance, get all flows defined to or from it (gazintas and
        gazoutas).

        Args:
            port (Port):  the specified Port
        """
        self.log.debug('* get_all_port_flows()')
        flows = self.get_by_type('Flow')
        flowzoutas = [f for f in flows if f.start_port is port]
        flowzintas = [f for f in flows if f.end_port is port]
        return flowzoutas + flowzintas

    def get_objects_for_project(self, project):
        """
        Get all objects relevant to the specified project, including [1] the
        project object, [2] all objects for which the project is the `owner`,
        [3] all objects to which the project has a `ProjectSystemUsage`
        relationship, and [4] all related objects (assemblies and related
        components, ports, flows, etc.).

        Args:
            project (Project):  the specified project
        """
        self.log.debug('* get_objects_for_project({})'.format(
                                        getattr(project, 'id', '[None]')))
        if not project:
            self.log.debug('  - no project provided -- returning empty list.')
            return []
        if project.__class__.__name__ != 'Project':
            self.log.debug('  - object provided is not a Project.')
            return []
        mos = self.get_by_type('ManagedObject')
        objs = [obj for obj in mos if obj.owner is project]
        psus = self.get_project_psus(project)
        if psus:
            objs += psus
            systems = [psu.system for psu in psus]
            objs += systems
            # get all assemblies
            # TODO: possibly have a "lazy" option (only top-level assemblies)
            assemblies = []
            # check for cycles
            for system in systems:
                cycles = self.check_for_cycles(system)
                if cycles:
                    self.log.info('  - cycles found:')
                    self.log.info(f'    {cycles}')
                    self.log.info('    returning intermediate result ...')
                    res = [o for o in set(objs) if o]
                    return res
            for system in systems:
                # NOTE:  get_assembly is recursive, gets *all* sub-assemblies
                assemblies += get_assembly(system)
            if assemblies:
                self.log.debug('  - {} assemblies found'.format(
                               len(assemblies)))
            objs += assemblies
            # get Missions and Activities related to project systems
            activities = []
            for system in systems:
                if system.activities:
                    activities += system.activities
            if activities:
                self.log.debug('  - {} Mission(s)/Activities found'.format(
                               len(activities)))
            objs += activities
        else:
            self.log.debug('  - no project-level systems found')
        objs.append(project)
        models = []
        for o in objs:
            o_models = list(getattr(o, 'has_models', []))
            if o_models:
                models += o_models
        representations = []
        if models:
            # get Representations of Models (if any)
            for m in models:
                m_reps = list(m.has_representations)
                if m_reps:
                    representations += m_reps
        if representations:
            objs += representations
            # get RepresentationFiles of Representations (if any)
            rep_files = []
            for r in representations:
                r_files = list(r.has_files)
                if r_files:
                    rep_files += r_files
            if rep_files:
                objs += rep_files
        rqts = self.get_rqts_for_project(project)
        if rqts:
            # include all Relations that are 'computable_form' of a rqt
            # and their ParameterRelations (rel.correlates_parameters)
            for rqt in rqts:
                if rqt.computable_form:
                    objs.append(rqt.computable_form)
                    prs = rqt.computable_form.correlates_parameters
                    if prs:
                        objs += prs
        # include all ports and flows relevant to products
        for obj in objs:
            if obj.__class__.__name__ in ['Product', 'HardwareProduct',
                                          'Software']:
                objs += obj.ports
                objs += self.get_internal_flows_of(obj)
        # TODO:  get the files too (fpath = rep_file.url)
        # use set() to eliminate dups
        res = [o for o in set(objs) if o]
        self.log.debug(f'  - total project objects found: {len(res)}')
        return res

    def get_rqts_for_project(self, project):
        """
        Get all requirements whose owner is the specified project.

        Args:
            project (Project):  the specified project
        """
        self.log.debug('* get_rqts_for_project({})'.format(
                                        getattr(project, 'id', '[None]')))
        if not project:
            self.log.debug('  no project provided -- returning empty list.')
            return []
        all_rqts = self.get_by_type('Requirement')
        rqts = [r for r in all_rqts if r.owner is project]
        self.log.debug('  - rqt(s) found: {}'.format(len(rqts)))
        return rqts

    def count_rqts_for_project(self, project):
        """
        Get a count of the requirements whose owner is the specified project.

        Args:
            project (Project):  the specified project
        """
        self.log.debug('* count_rqts_for_project({})'.format(
                                        getattr(project, 'id', '[None]')))
        if not project:
            self.log.debug('  - no project provided -- returning 0.')
            return 0
        rqts = [o for o in self.get_by_type('Requirement')
                 if o.owner == project]
        n = len(rqts)
        self.log.debug('  - rqts count: {n}')
        return n

    def delete(self, oids):
        """
        Delete the specified objects from the local db.

        First, note that in the "TachyOrb", there are no "local deletions" --
        all deletions are performed on the server and the client only deletes
        local objects when it receives messages from the server to that effect.

        Args:
            oids (Iterable of strings): oids of objects in the local db
        """
        self.log.debug('* orb.delete() called ...')
        # TODO: make sure appropriate relationships in which these objects
        # are the parent or child are also deleted
        for oid in oids:
            obj = orb.get(oid)
            if obj:
                del obj
            if oid in db:
                del db[oid]
            if oid in matrix:
                del matrix[oid]
            else:
                self.log.debug(f'  - oid "{oid}" not found,')

    def is_versionable(self, obj):
        """
        Determine if a object is versionable: having a "version"
        attribute is sufficient.
        """
        return (hasattr(obj, 'version') and hasattr(obj, 'iteration'))

    # =============================================================================
    # new section from "p.marv.perms" ...

    def get_user_orgs(self):
        """
        Get all orgs in which the local user has a role.

        Returns:
            list of orgs
        """
        ra_context_oids = set([ra['role_assignment_context']
                               for ra in self.user_raz])
        return [orb.get(oid) for oid in ra_context_oids]

    def am_global_admin(self):
        """
        Return True if the local user is a global admin; otherwise False.

        Returns:
            boolean
        """
        global_admin = [ra for ra in self.user_raz
                    if (ra.get('assigned_role') == 'pgefobjects:Role.Administrator'
                        and ra.get('role_assignment_context', None) is None)]
        return bool(global_admin)

    # =============================================================================

    def get_project_psus(self, project):
        """
        Return the ProjectSystemUsages for the specified project.  Note that
        this function is specific to the TachyOrb and is not needed in the
        Uberorb, which uses the inverse attribute "systems" of Project.
        """
        maybe_psus = [self.get(system.usage_oid)
                      for system in (systemz.get(project.oid) or [])]
        return [psu for psu in maybe_psus if psu is not None]

    def check_for_cycles(self, product):
        """
        Check for cyclical data structures among all [known] components used at
        up to 5 levels of assembly of the specified product.

        Args:
            product (Product): the Product in which to look for cycles
        """
        if product and getattr(product, 'oid', None) in componentz:
            comps = [self.get(comp.oid) for comp in componentz[product.oid]]
            # acus_by_comp_oid = {acu.component.oid : acu
                                # for acu in product.components}
            if product.oid in [getattr(c, 'oid', None) for c in comps]:
                txt = 'is a component of itself.'
                msg = 'product oid "{}" (id: "{}" {}'.format(
                          product.oid, product.id or 'no id', txt)
                self.log.debug(msg)
                return msg
            # else:
                # self.log.debug('  - level 1 components ok.')
            comps1 = []
            acus1_by_comp_oid = {}
            for comp in comps:
                if comp:
                    comps1 += [self.get(c.oid)
                               for c in (componentz.get(comp.oid) or [])]
                    acus1_by_comp_oid.update(
                     {c.oid : self.get(c.usage_oid)
                      for c in (componentz.get(comp.oid) or [])})
            if comps1:
                comps += comps1
            else:
                # self.log.debug('  - no more levels.')
                return
            if product.oid in [getattr(c, 'oid', None) for c in comps1]:
                txt = 'is a 2nd-level component of itself.'
                msgs = []
                msg = ' *** product {} (id: "{}" {}'.format(
                          product.oid, product.id or 'no id', txt)
                msgs.append(msg)
                self.log.debug(msg)
                acu1 = acus1_by_comp_oid[product.oid]
                msg1 = ' *** offending Acu is:'
                msgs.append(msg1)
                self.log.debug(msg1)
                msg2 = '     id: {}'.format(str(acu1.id))
                msgs.append(msg2)
                self.log.debug(msg2)
                msg3 = '     creator: {}'.format(acu1.creator.id)
                msgs.append(msg3)
                self.log.debug(msg3)
                assy1 = acu1.assembly
                msg4 = '     assembly: {}'.format(str(assy1.id))
                msgs.append(msg4)
                self.log.debug(msg4)
                msg5 = '     assembly oid: {}'.format(str(assy1.oid))
                msgs.append(msg5)
                self.log.debug(msg5)
                # acu = acus_by_comp_oid[assy1.oid]
                return '<br>'.join(msgs)
            # else:
                # self.log.debug('  - level 2 components ok.')
            comps2 = []
            for comp in comps1:
                comps2 += [self.get(getattr(c, 'oid', None))
                           for c in (
                           componentz.get(getattr(comp, 'oid', None)) or [])]
            if comps2:
                comps += comps2
            else:
                # self.log.debug('  - no more levels.')
                return
            if product.oid in [getattr(c, 'oid', None) for c in comps2]:
                txt = 'is a 3nd-level component of itself.'
                msg = 'product {} (id: "{}" {}'.format(
                          product.oid, product.id or 'no id', txt)
                self.log.debug(msg)
                return msg
            # else:
                # self.log.debug('  - level 3 components ok.')
            comps3 = []
            for comp in comps2:
                comps3 += [self.get(getattr(c, 'oid', None))
                           for c in (
                           componentz.get(getattr(comp, 'oid', None)) or [])]
            if comps3:
                comps += comps3
            else:
                # self.log.debug('  - no more levels.')
                return
            if product.oid in [getattr(c, 'oid', None) for c in comps3]:
                txt = 'is a 4th-level component of itself.'
                msg = 'product {} (id: "{}" {}'.format(
                          product.oid, product.id or 'no id', txt)
                self.log.debug(msg)
                return msg
            else:
                # self.log.debug('no cycles')
                return
        # self.log.debug('no cycles')

    def get_bom_from_compz(self, product):
        """
        Return a list of all known components at every level of assembly in the
        specified product.

        Args:
            product (Product) the subject product
        """
        try:
            # NOTE: this will explode if assembly contains cycles!
            if product:
                comps = [self.get(comp.oid)
                         for comp in (componentz.get(product.oid) or [])]
                if comps:
                    comps = reduce(lambda x,y: x+y,
                                   [self.get_bom_from_compz(c)
                                    for c in comps],
                                   comps)
                return comps
            return []
        except:
            # self.log.debug('bom exploded -- probably contained a cycle.')
            return []

    def get_assembly_from_compz(self, product):
        """
        Return the product's assembly structure, including all Acu instances plus
        all (known) components used at every level of assembly of the specified
        product.
        """
        if product:
            comps = self.get_bom_from_compz(product)
            base_acus = [self.get(c.usage_oid)
                         for c in (componentz.get(product.oid) or [])]
            acus = reduce(lambda x,y: x + y,
                          [[self.get(comp.usage_oid) for comp in
                            (componentz.get(c.oid) or [])]
                           for c in comps],
                          base_acus)
            return comps + acus
        return []

    def get_bom_oids(self, product):
        return set([getattr(p, 'oid', '') or ''
                    for p in self.get_bom_from_compz(product)
                    if hasattr(p, 'oid')])


# A node has only one instance of TachyOrb, called 'orb', which is intended to
# be imported by all application components.
orb = TachyOrb()

