# -*- coding: utf-8 -*-
"""
Pan Galactic hub for object metadata and storage operations.

NOTE:  Only the `orb` instance created in this module should be imported (it is
intended to be a singleton).
"""
from builtins import object
import json, os, shutil, sys, traceback

# ruamel_yaml
import ruamel_yaml as yaml

# SQLAlchemy
from sqlalchemy     import sql
from sqlalchemy.orm import sessionmaker, with_polymorphic

# PanGalactic
from pangalactic.core             import __version__
from pangalactic.core             import diagramz
from pangalactic.core             import config, read_config
from pangalactic.core             import prefs, read_prefs
from pangalactic.core             import state, read_state
from pangalactic.core             import trash, read_trash
from pangalactic.core.registry    import PanGalacticRegistry
from pangalactic.core.utils.meta  import uncook_datetime
from pangalactic.core.mapping     import schema_maps, schema_version
from pangalactic.core.parametrics import (add_default_parameters,
                                          _compute_pval, componentz,
                                          create_parm_defz,
                                          create_parmz_by_dimz,
                                          parm_defz, parameterz,
                                          refresh_componentz,
                                          update_parm_defz,
                                          update_parmz_by_dimz)
from pangalactic.core.serializers import (deserialize, deserialize_parms,
                                          serialize, serialize_parms)
from pangalactic.core             import refdata
from pangalactic.core.test        import data as test_data_mod
from pangalactic.core.test        import vault as test_vault_mod
from pangalactic.core.test.utils  import gen_test_pvals
from pangalactic.core.log         import get_loggers
from pangalactic.core.validation  import get_assembly
from functools import reduce


class UberORB(object):
    """
    The UberORB mediates all communications with local objects, local storage,
    the local metadata registry, and remote repositories and services.

    IMPORTANT:  The UberORB is intended to be a singleton.  The UberORB class
    should not be imported; instead, the module-level instance created at the
    end of this module should be imported.

    NOTE:  the orb does not have an __init__() in order to avoid side-effects
    of importing the module-level instance that is created -- its start()
    method must be called to initialize it.

    Attributes:
        [Instance (orb) attributes defined here]
        registry (PanGalacticRegistry):  instance of PanGalacticRegistry
        log (Logger):  instance of pgorb_logger
        error_log (Logger):  instance of pgorb_error_logger
        db (Session):  interface to the local db
        new_oids (list of str):  oids of objects that have been created but not
            saved
        remote (TBD) interface to remote services [TO BE IMPLEMENTED]
        home (str):  full path to the application home directory -- populated
            by orb.start()

        [referenced from PanGalacticRegistry]
        db_engine (SQLAlchemy orm):  result of registry `create_engine`
        schemas (dict):  see definition in
            p.meta.registry._update_schemas_from_extracts
        classes (dict):  a mapping of `meta_id`s to runtime app classes.
        parms (dict):  the parameter cache, which maps tuples of
            (object oid, parameter id) to parameter value
    """
    started = False
    startup_msg = '* orb starting up ...'
    new_oids = []
    parms = {}

    def start(self, home=None, db_url=None, console=False, debug=False, **kw):
        """
        Initialization logic.

        Args:
            home (str):  home directory (full path)
            db_url (str):  url for registry to use in sqlalchemy create_engine
                (if None, the registry creates a local sqlite db)
            console (bool):  (default: False)
                if True: send output to console
                if False: redirect stdout/stderr to log file
            debug (bool):  (default: False) log in debug mode
        """
        if self.started:
            return
        # set home directory -- in order of precedence:
        # [1] 'home' kw arg (this should be set by the application, if any)
        if home:
            pgx_home = home
        # [2] from 'PANGALACTIC_HOME' env var
        elif os.environ.get('PANGALACTIC_HOME'):
            pgx_home = os.environ['PANGALACTIC_HOME']
        # [3] create a 'pangalaxian' directory in the user's home dir
        else:
            if sys.platform == 'win32':
                default_home = os.path.join(os.environ.get('HOMEPATH'))
                if os.path.exists(default_home):
                    pgx_home = os.path.join(default_home, 'pangalaxian')
            else:
                user_home = os.environ.get('HOME')
                if user_home:
                    pgx_home = os.path.join(user_home, 'pangalaxian')
                else:
                    # TODO:  a first-time dialog/wizard to set pgx_home ...
                    # current fallback is just to use the current directory
                    pgx_home = os.path.join(os.getcwd(), 'pangalaxian')
        if not os.path.exists(pgx_home):
            os.makedirs(pgx_home, mode=0o755)
        pgx_home = os.path.abspath(pgx_home)
        # If config values have been edited, they will take precedence over any
        # config set by app start-up defaults.
        app_config = {}
        # config file is read here -- it is initially created with app
        # defaults, and later may be edited by the user
        read_config(os.path.join(pgx_home, 'config'))
        if config:
            app_config.update(config)
        config.update(app_config)
        # Saved prefs, state, and trash are read here; will be overwritten by
        # any new prefs, state, and trash set at runtime.
        read_prefs(os.path.join(pgx_home, 'prefs'))
        read_state(os.path.join(pgx_home, 'state'))
        read_trash(os.path.join(pgx_home, 'trash'))
        # create "file vault"
        self.vault = os.path.join(pgx_home, 'vault')
        if not os.path.exists(self.vault):
            os.makedirs(self.vault, mode=0o755)
        self.start_logging(home=pgx_home, console=console, debug=debug)
        self.log.info('* prefs read: {}'.format(str(prefs)))
        self.log.info('* state read: {}'.format(str(state)))
        self.log.info('* trash read ({} objects).'.format(len(trash)))
        if not prefs.get('units'):
            prefs['units'] = {}
        # * copy test data files from 'p.test.data' module to test_data_dir
        self.test_data_dir = os.path.join(pgx_home, 'test_data')
        current_test_files = set()
        self.log.debug('* checking for test data in [pgx_home]/test_data...')
        if not os.path.exists(self.test_data_dir):
            os.makedirs(self.test_data_dir)
        else:
            current_test_files = set(os.listdir(self.test_data_dir))
        self.log.debug('  - found %i data files' % len(current_test_files))
        test_data_mod_path = test_data_mod.__path__[0]
        test_data_files = set([s for s in os.listdir(test_data_mod_path)
                               if (not s.startswith('__init__')
                               and not s.startswith('__pycache__'))
                               ])
        test_data_to_copy = test_data_files - current_test_files
        self.log.debug('  - data files to be installed: %i'
                       % len(test_data_to_copy))
        if test_data_to_copy:
            self.log.debug('  - copying data files into test_data dir...')
            test_data_cpd = []
            for p in test_data_to_copy:
                shutil.copy(os.path.join(test_data_mod_path, p),
                            self.test_data_dir)
                test_data_cpd.append(p)
            self.log.info('  - new test data files installed: %s'
                          % str(test_data_cpd))
        else:
            self.log.info('  - all test data files already installed.')
        # * copy files from 'p.test.vault' module to vault_dir
        self.log.debug('* checking for files in [pgx_home]/vault ...')
        current_vault_files = set(os.listdir(self.vault))
        self.log.debug('  - found %i vault files:' % len(current_vault_files))
        if current_vault_files:
            for fpath in current_vault_files:
                self.log.debug('    {}'.format(fpath))
        vault_mod_path = test_vault_mod.__path__[0]
        test_vault_files = set([s for s in os.listdir(vault_mod_path)
                               if (not s.startswith('__init__')
                               and not s.startswith('__pycache__'))
                               ])
        vault_files_to_copy = test_vault_files - current_vault_files
        self.log.debug('  - new test vault files to be installed: %i'
                       % len(vault_files_to_copy))
        if vault_files_to_copy:
            self.log.debug('  - copying test vault files into vault dir...')
            vault_files_copied = []
            for p in vault_files_to_copy:
                shutil.copy(os.path.join(vault_mod_path, p), self.vault)
                vault_files_copied.append(p)
            self.log.info('  - new test vault files installed: %s'
                          % str(vault_files_copied))
        else:
            self.log.info('  - all test vault files already installed.')
        self.cache_path = os.path.join(pgx_home, 'cache')
        if not db_url:
            # if no db_url is specified, create a local sqlite db
            local_db_path = os.path.join(pgx_home, 'local.db')
            db_url = 'sqlite:///{}'.format(local_db_path)
        state['db_url'] = db_url
        state['schema_version'] = schema_version
        # if __version__ != schema_version:
            # if the state 'schema_version' does not match the current
            # package's schema_version:
            # [1] drop and create database
            # self.drop_and_create_db(pgx_home)
            # [2] initialize registry with "force_new_core" to create the new
            #     classes and db tables
            # self.init_registry(pgx_home, db_url, force_new_core=True,
                               # version=schema_version, debug=False,
                               # console=console)
            # [3] transform and import data that was dumped previously
            # serialized_data = self.load_and_transform_data()
            # if serialized_data:
                # deserialize(self, serialized_data, include_refdata=True)
            # state['schema_version'] = schema_version
        # else:
            # if there were no schema mods, just initialize the registry with
            # the current schema
        # NOTE:  registry 'debug' is set to False regardless of the client's
        # log level because its debug logging is INSANELY verbose ...  if the
        # registry needs debugging, just hack this.
        self.init_registry(pgx_home, db_url, version=schema_version,
                           log=self.log, debug=False, console=console)
        self.versionables = [cname for cname in self.classes if 'version' in
                             self.schemas[cname]['field_names']]
        self.load_reference_data()
        # reload or create the parameter definitions cache ('parm_defz')
        self._load_parm_defz()
        # build the 'componentz' runtime cache ...
        self._build_componentz_cache()
        self._load_parmz()
        self._load_diagramz()
        # populate the 'parmz_by_dimz' runtime cache ...
        create_parmz_by_dimz(self)
        # get the hdf5 store or create a new one ...
        # self.store_path = os.path.join(self.home, 'datasets.h5')
        # self.data_store = pandas.io.pytables.HDFStore(self.store_path)
        self.data_store = {}
        self.started = True
        return self.home

    def init_registry(self, home, db_url, force_new_core=False, version='',
                      log=None, debug=False, console=False):
        self.registry = PanGalacticRegistry(home=home, db_url=db_url,
                                            cache_path=self.cache_path,
                                            version=version, log=log,
                                            debug=debug, console=console,
                                            force_new_core=force_new_core)
        self.home = self.registry.home
        self.db_engine = self.registry.db_engine
        self.schemas = self.registry.schemas
        self.classes = self.registry.classes
        self.mbo = self.registry.metaobject_build_order()
        # init db
        self.init_db()

    def init_db(self):
        """
        Initialize the local database.
        """
        msg = '* init_db():  initializing local db session ...'
        self.log.info(msg)
        self.startup_msg = msg
        if not getattr(self, 'db', None):
            Session = sessionmaker(bind=self.db_engine)
            self.db = Session()
            # NOTE:  DO NOT *EVER* USE 'expire_on_commit = False' here!!!
            #        -> it causes VERY weird behavior ...

    def dump_db(self, fmt='yaml'):
        """
        Serialize the entire db and dump to `vault/db.yaml`.
        """
        self.log.info('* dump_db()')
        if fmt == 'json':
            f = open(os.path.join(self.vault, 'db.json'), 'w')
            f.write(json.dumps(serialize(
                    self, self.get_all_subtypes('Identifiable')),
                    separators=(',', ':'),
                    indent=4, sort_keys=True))
            f.close()
        elif fmt == 'yaml':
            self.log.info('  dumping database to yaml file ...')
            f = open(os.path.join(self.vault, 'db.yaml'), 'w')
            f.write(yaml.safe_dump(serialize(
                    self, self.get_all_subtypes('Identifiable'))))
            f.close()
        self.log.info('  dump to {} completed.'.format(fmt))

    # def drop_and_create_db(self, home):
        # """
        # Drop the database and create a new one -- used when the schema has
        # changed.

        # Args:
            # home (str):  home directory (full path)
        # """
        # self.log.info('* drop_and_create_db() ...')
        # db_url = state.get('db_url')
        # if db_url and db_url.startswith('postgresql:'):
            # # pyscopg2 (only used here, when schema changes)
            # import psycopg2
            # db_name = 'pgerdb'
            # try:
                # with psycopg2.connect(database='postgres') as conn:
                    # conn.autocommit = True
                    # with conn.cursor() as cur:
                        # cur.execute('DROP DATABASE {};'.format(db_name))
                        # self.log.info('  database "{}" dropped.'.format(
                                                                 # db_name))
                        # cur.execute('CREATE DATABASE {};'.format(db_name))
                # self.log.info('  database "{}" created.'.format(db_name))
            # except:
                # self.log.info('  problem encountered -- see error log.')
                # self.error_log.info('* error in drop_and_create_db():')
                # self.error_log.info(traceback.format_exc())
        # elif db_url and db_url.startswith('sqlite:'):
            # # if the db is sqlite, simply remove its file; the registry will
            # # create a new one when it starts up
            # try:
                # db_path = os.path.join(home, 'local.db')
                # if os.path.exists(db_path):
                    # os.remove(db_path)
                    # self.log.info('  db file removed.')
                # else:
                    # self.log.info('  file "local.db" not found.')
            # except:
                # self.log.info('  error encounterd in removing db file.')
                # self.error_log.info('* error in drop_and_create_db():')
                # self.error_log.info(traceback.format_exc())

    def _load_diagramz(self):
        """
        Load `diagramz` cache from diagrams.json file.
        """
        json_path = os.path.join(self.home, 'diagrams.json')
        if os.path.exists(json_path):
            with open(json_path) as f:
                diagramz.update(json.loads(f.read()))
            self.log.info('[orb] diagramz cache read from diagrams.json')
        else:
            self.log.info('[orb] no diagrams.json file found.')

    def _save_diagramz(self):
        """
        Save `diagramz` cache to diagrams.json file.
        """
        self.log.info('* [orb] _save_diagramz() ...')
        diagz_path = os.path.join(self.home, 'diagrams.json')
        with open(diagz_path, 'w') as f:
            f.write(json.dumps(diagramz, separators=(',', ':'),
                               indent=4, sort_keys=True))
        self.log.info('        ... diagrams.json file written.')

    def _load_parm_defz(self):
        """
        Load the parameter definitions cache (`parm_defz` dict) from a saved
        parameter_defs.json file; if the file is not found, create the cache
        from the ParameterDefinition, State, and Context objects in the
        database.
        """
        self.log.info('* [orb] _load_parm_defz() ...')
        json_path = os.path.join(self.home, 'parameter_defs.json')
        if os.path.exists(json_path):
            with open(json_path) as f:
                saved_parm_defs = json.loads(f.read())
                parm_defz.update(saved_parm_defs)
            self.log.info('        parm_defz cache is loaded.')
        else:
            self.log.info('        "parameter_defs.json" was not found.')
            self.log.info('        creating "parm_defz" cache ...')
            create_parm_defz(self)
            self._save_parm_defz()

    def _save_parm_defz(self):
        """
        Save the parameter definitions cache (`parm_defz` dict) to
        parameter_defs.json.
        """
        self.log.info('* [orb] _save_parm_defz() ...')
        json_path = os.path.join(self.home, 'parameter_defs.json')
        with open(json_path, 'w') as f:
            f.write(json.dumps(parm_defz, separators=(',', ':'),
                               indent=4, sort_keys=True))
        self.log.info('        ... parameter_defs.json written.')

    def _load_parmz(self):
        """
        Load `parameterz` dict from json file.
        """
        self.log.info('* [orb] _load_parmz() ...')
        json_path = os.path.join(self.home, 'parameters.json')
        if os.path.exists(json_path):
            with open(json_path) as f:
                serialized_parms = json.loads(f.read())
            for oid, ser_parms in serialized_parms.items():
                deserialize_parms(oid, ser_parms)
            self.recompute_parmz()
            self.log.info('        parameterz cache loaded and recomputed.')
        else:
            self.log.info('        "parameters.json" was not found.')

    def _save_parmz(self):
        """
        Save `parameterz` dict to a json file.
        """
        self.log.info('* [orb] _save_parmz() ...')
        parms_path = os.path.join(self.home, 'parameters.json')
        serialized_parameterz = {}
        for oid, obj_parms in parameterz.items():
            # NOTE: serialize_parms() uses deepcopy()
            serialized_parameterz[oid] = serialize_parms(obj_parms)
        with open(parms_path, 'w') as f:
            f.write(json.dumps(serialized_parameterz, separators=(',', ':'),
                               indent=4, sort_keys=True))
        self.log.info('        ... parameters.json file written.')

    def recompute_parmz(self):
        """
        Recompute any computed parameters for the configured variables and
        contexts.  This is required at startup or when a parameter is created,
        modified, or deleted.
        """
        self.log.info('* [orb] recompute_parmz()')
        # TODO:  preferred contexts should override defaults
        # default descriptive contexts:  CBE, MEV
        d_contexts = config.get('descriptive_contexts', ['CBE', 'MEV']) or []
        variables = config.get('variables', ['m', 'P', 'R_D']) or []
        # TODO:  make this more efficient by iterating over only the "top
        # level" assembly oids, since _compute_pval is recursive and will
        # recompute all lower-level component/subassembly values in each pass
        for context in d_contexts:
            for variable in variables:
                for oid in parameterz:
                    _compute_pval(self, oid, variable, context)
        # prescriptive contexts (performance requirements)
        # for now, only 'Margin' (for nodes that have an NTE value)
        p_contexts = ['Margin']
        for context in p_contexts:
            for variable in ['m', 'P', 'R_D']:
                for oid in parameterz:
                    if parameterz[oid].get(variable + '[NTE]'):
                        _compute_pval(self, oid, variable, context)
        self._save_parmz()

    def assign_test_parameters(self, objs):
        """
        Assign a set of test parameters with randomly-generated values to an
        iterable of objects.

        Args:
            objs (iterable of Modelable):  objects the test parameters will be
                assigned to
        """
        self.log.info('* [orb] assign_test_parameters()')
        try:
            for o in objs:
                add_default_parameters(self, o)
                gen_test_pvals(parameterz[o.oid])
            self.recompute_parmz()
            self.log.info('        ... done.')
        except:
            self.log.info('        ... failed.')

    def _build_componentz_cache(self):
        """
        Build the `componentz` cache (which maps Product oids to the oids of
        their components) at startup.
        """
        self.log.info('* [orb] _build_componentz_cache()')
        for product in self.get_all_subtypes('Product'):
            if product.components:
                refresh_componentz(self, product)
        self.log.info('  componentz cache ready.')

    def start_logging(self, home=None, console=False, debug=False):
        """
        Create a pangalaxian orb (`pgorb`) log and begin writing to it.

        Keyword Args:
            home (str):  full path to app home directory (log files will be
                written into a 'log' subdirectory)
            console (bool):  (default: False)
                if True: send output to console
                if False: redirect stdout/stderr to log files
            debug (bool):  if True, set log level to 'debug'
        """
        if not home:
            home = os.getcwd()
        self.log, self.error_log = get_loggers(home, 'orb', console=console,
                                               debug=debug)
        self.log.info('* orb logging initialized ...')

    def load_and_transform_data(self):
        """
        Load and transform all dumped serialized data to the new schema.
        Called when restarting after an upgrade that includes a schema change.
        """
        self.log.info('* [orb] transforming all data to new schema ...')
        sdata = ''
        data_path = os.path.join(self.vault, 'db.yaml')
        if os.path.exists(data_path):
            try:
                f = open(data_path)
                sdata = yaml.safe_load(f.read())
                if __version__ in schema_maps:
                    map_fn = schema_maps[__version__]
                    sdata = map_fn(sdata)
                    self.log.info('        data loaded and transformed.')
                else:
                    self.log.info('        data loaded (no transformation).')
            except:
                self.log.info('        an error ocurred (see error log).')
                self.error_log.info('* error in load_and_transform_data():')
                self.error_log.info(traceback.format_exc())
        else:
            self.log.info('        file "db.yaml" not found.')
        return sdata

    def load_reference_data(self):
        """
        Create reference data objects.  Performed at orb start up, since new
        objects created at runtime refer to some of the reference objects.
        """
        self.log.info('* checking reference data ...')
        oids = self.get_oids()
        # 0:  load initial reference data
        missing_i = [so for so in refdata.initial if so['oid'] not in oids]
        if missing_i:
            self.log.info('  + missing some initial reference data:')
            self.log.info('  {}'.format([so['oid'] for so in missing_i]))
            i_objs = deserialize(self, [so for so in missing_i],
                                 include_refdata=True,
                                 force_no_recompute=True)
            for o in i_objs:
                self.db.add(o)
        admin = self.get('pgefobjects:admin')
        pgana = self.get('pgefobjects:PGANA')
        self.log.info('  + initial reference data loaded.')
        # 1:  load balance of reference data
        missing_c = [so for so in refdata.core if so['oid'] not in oids]
        objs = []
        if missing_c:
            self.log.info('  + missing some core reference data:')
            self.log.info('  {}'.format([so['oid'] for so in missing_c]))
            objs = deserialize(self, [so for so in missing_c],
                               include_refdata=True,
                               force_no_recompute=True)
        for o in objs:
            if hasattr(o, 'owner'):
                o.owner = pgana
                o.creator = o.modifier = admin
            self.db.add(o)
        # 2:  check for updates to reference data
        self.log.info('  + checking for updates to reference data ...')
        all_ref = refdata.initial + refdata.core
        all_ref_oids = [so['oid'] for so in all_ref]
        # get mod_datetimes of all current ref data objects
        mod_dts = self.get_mod_dts(oids=all_ref_oids)
        # compare them to all newly imported refdata objects
        updated_r = [so for so in all_ref
                     if (uncook_datetime(so.get('mod_datetime')) and
                         uncook_datetime(mod_dts.get(so['oid'])) and
                         (uncook_datetime(so.get('mod_datetime')) >
                         uncook_datetime(mod_dts.get(so['oid']))))] 
        if updated_r:
            self.log.info('    updates found ...')
            deserialize(self, updated_r, force_no_recompute=True)
            self.log.info('    updates completed.')
        else:
            self.log.info('    no updates found.')
        # 3:  delete deprecated reference data
        # NOTE:  don't do this step until the deprecated data has been removed
        # from the current database
        # oids = self.get_oids()
        # deprecated = [oid for oid in refdata.deprecated if oid in oids]
        # if deprecated:
            # self.log.info('  + deleting deprecated reference data:')
            # self.log.info('  {}'.format([oid for oid in deprecated]))
            # for oid in deprecated:
                # self.delete([self.get(oid) for oid in deprecated])
        self.log.info('  + all reference data loaded.')

    # begin db operations

    def save(self, objs):
        """
        Save the specified objects to the local db.  (CAVEAT: this will
        update ["merge"] any object that already exists in the db.)

        Args:
            objs (iterable of objects):  the objects to be saved
        """
        for obj in objs:
            cname = obj.__class__.__name__
            oid = getattr(obj, 'oid', None)
            self.log.info('* orb.save')
            new = bool(oid in self.new_oids) or not self.get(oid)
            if new:
                self.log.info('  orb.save: %s is a new %s, saving it ...' % (
                                                        oid, cname))
                self.db.add(obj)
                self.log.info('  orb.save: adding object with oid "%s" ...' % (
                                                                obj.oid))
                if obj.oid in self.new_oids:
                    self.new_oids.remove(obj.oid)
            else:
                # updating an existing object
                self.log.info(
                    '  orb.save: oid "%s" is existing %s, updating ...' % (
                                                        oid, cname))
                # NOTE:  in new paradigm, obj is versioned iff
                # [1] it has a 'version' attr and
                # [2] a non-null version has been assigned to it (i.e. neither
                # None nor an empty string)
                if self.is_versioned(obj):
                    # if obj is being versioned, bump its iteration #
                    # NOTE:  TODO (maybe) yes, this means iterations are not
                    # tracked in the db ... that's a separate issue
                    if obj.iteration is None:
                        obj.iteration = 0
                    obj.iteration += 1
                self.db.merge(obj)
            if cname == 'Acu':
                refresh_componentz(self, obj.assembly)
            elif cname == 'ParameterDefinition':
                # NOTE:  all Parameter Definitions are public
                obj.public = True
                update_parmz_by_dimz(self, obj)
                pd_context = getattr(obj, 'context', None)
                if pd_context:
                    update_parm_defz(self, obj, pd_context)
                self._save_parm_defz()
        self.log.info('  orb.save:  committing db session.')
        self.db.commit()
        self.recompute_parmz()
        return True

    def get(self, *oid, **kw):
        """
        Get an object or objects from the db:

          [1] if 'oid' argument is given, by its oid -- fully polymorphic
              return value thanks to SqlAlchemy's 'with_polymorphic'.
          [2] if 'oids' kw arg is used, by a list of oids

        Args:
            oid (str):  the oid of an object in the db

        Keyword Args:
            oids (list):  a list of oids of objects in the db

        Returns:
            obj (Identifiable or subtype) or None
        """
        entity = with_polymorphic(self.classes['Identifiable'], '*')
        if oid:
            self.log.debug('* get(%s)' % oid[0])
            return self.db.query(entity).filter_by(oid=oid[0]).first()
        elif kw:
            oids = kw.get('oids')
            self.log.debug('* get(oids=%s)' % str(oids))
            if oids:
                return self.db.query(entity).filter(
                                        entity.oid.in_(oids)).all()
            else:
                return []
        else:
            self.log.debug('* get() [nothing]')
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
        self.log.debug('* get_count(%s)' % cname)
        return self.db.query(self.classes[cname]).count()

    def get_by_type(self, cname):
        """
        Get objects from the local db by class name.

        Args:
            cname (str):  the class name of the objects to be retrieved 

        Returns:
            an iterator of objects of the specified class (may be empty)
        """
        self.log.debug('* get_by_type(%s)' % cname)
        cls = self.classes.get(cname)
        if not cls:
            return []
        return list(self.db.query(cls).filter(cls.pgef_type == cname))

    def get_all_subtypes(self, cname):
        """
        Get objects from the local db by class name, including all subtypes
        of the specified class.

        Args:
            cname (str):  the class name to be referenced

        Returns:
            list of objects of the specified class or a subclass (may be empty)
        """
        self.log.debug('* get_all_subtypes(%s)' % cname)
        return self.db.query(self.classes[cname]).all()

    def get_oids(self, cname=None):
        """
        Get all oids from the local db -- used for checking whether a given
        object is in the db or not.  Returns:

          [1] with no arguments:  all oids in the db
          [2] with 'cname':  all oids for objects of the specified class

        Keyword Args:
            cname (str):  class name of the objects to be used
        """
        Identifiable = self.classes['Identifiable']
        query = self.db.query(Identifiable.oid)
        if cname:
            query = query.filter(Identifiable.pgef_type == cname)
        return [row[0] for row in query.all()]

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
            ident = self.classes['Identifiable'].__table__
            if not cname:
                s = sql.select([ident])
            elif cname:
                s = sql.select([ident]).where(ident.c.pgef_type == cname)
            return [(row['id'], '') for row in self.db.execute(s)]

    def get_mod_dts(self, cname=None, oids=None):
        """
        Get a dict that maps oids of objects to their 'mod_datetime' stamps as
        strings:

          [1] with no arguments:  for all objects in the db for which
              'mod_datetime' is not None.
          [2] with 'cname':  for all objects of the specified class
          [3] with 'oids':   for all objects whose oids are in the 'oids' list

        Keyword Args:
            cname (str):  class name of the objects to be used
            oids (list):  oids of objects to be used

        Returns:
            dict:  mapping of oids to 'mod_datetime' strings.
        """
        ident = self.classes['Identifiable'].__table__
        if not cname and not oids:
            s = sql.select([ident]).where(ident.c.mod_datetime != None)
        elif cname:
            s = sql.select([ident]).where(sql.and_(
                                        ident.c.mod_datetime != None,
                                        ident.c.pgef_type == cname
                                        ))
        elif oids:
            s = sql.select([ident]).where(sql.and_(
                                        ident.c.mod_datetime != None,
                                        ident.c.oid.in_(oids)
                                        ))
        return {row['oid'] : str(row['mod_datetime'])
                for row in self.db.execute(s)}

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
        self.log.debug('* select(%s, **(%s))' % (cname, str(kw)))
        kw['pgef_type'] = cname
        return self.db.query(self.classes[cname]).filter_by(**kw).first()

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
        self.log.debug('* search_exact(**(%s))' % (str(kw)))
        # only allow search parameters that occur in schemas
        cname = kw.get('cname')
        attrs = [a for a in kw if a in self.registry.pes]
        if attrs:
            domains = [self.registry.pes[a]['domain'] for a in attrs]
            idx = max([self.mbo.index(d) for d in domains])
            domain = self.mbo[idx]
            ok_kw = {a : kw[a] for a in attrs}
            if cname:
                # if cname is supplied, check that it contains all attrs
                extr = self.registry.ces.get(cname)
                if extr:
                    bases = self.registry.all_your_base(extr) | set([cname])
                    self.log.debug('  - bases of cname: {}'.format(str(bases)))
                    if not domain in bases:
                        # class does not have all attrs: return empty list
                        return []
                else:
                    # cname is not a valid class: return empty list
                    return []
            else:
                # no cname specified -- use the most general class that
                # contains all specified parameters
                cname = domain
                self.log.debug('  - no cname kw, using: {}'.format(cname))
            # self.log.debug('  - ok_kw: {}'.format(str(ok_kw)))
            return list(self.db.query(self.classes[cname]).filter_by(**ok_kw))
        else:
            return []

    def get_internal_flows_of(self, product):
        """
        Get all flows between the ports of the components of the specified
        product, including internal flows between component ports and the ports
        of the product itself.

        Args:
            product (Product):  the specified product
        """
        # handle exception in case we get something that's not a Product
        try:
            objs = [product] + [acu.component for acu in product.components]
            port_oids = [p.oid for p in
                         reduce(lambda x, y: x+y, [o.ports for o in objs])]
            Port = orb.classes['Port']
            Flow = orb.classes['Flow']
            flows = orb.db.query(Flow).join(Flow.start_port).filter(
                        Port.oid.in_(port_oids)).join(Flow.end_port).filter(
                        Port.oid.in_(port_oids)).all()
            return flows
        except:
            return []

    def get_objects_for_project(self, project):
        """
        Get all the objects relevant to the specified project, including
        objects for which the project is the `owner` or `user` (i.e., to which
        the project has a `ProjectSystemUsage` relationship), plus all related
        objects (their assemblies and related components, etc.).

        Args:
            project (Project):  the specified project
        """
        self.log.info('* [orb] get_objects_for_project({})'.format(
                                        getattr(project, 'id', '[None]')))
        if not project:
            self.log.info('  no project provided -- returning empty list.')
            return []
        objs = self.search_exact(owner=project)
        psus = self.search_exact(cname='ProjectSystemUsage',
                                 project=project)
        if psus:
            objs += psus
            systems = [psu.system for psu in psus]
            objs += systems
            # get all assemblies
            # TODO: possibly have a "lazy" option (only top-level assemblies)
            assemblies = []
            for system in systems:
                # NOTE:  get_assembly is recursive, gets *all* sub-assemblies
                assemblies += get_assembly(system)
            if assemblies:
                self.log.debug('  {} assemblies found'.format(len(assemblies)))
            objs += assemblies
        else:
            self.log.debug('  no ProjectSystemUsages found')
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
        # TODO:  get the files too (fpath = rep_file.url)
        # use set() to eliminate dups
        res = [o for o in set(objs) if o]
        self.log.info('  returning {} object(s).'.format(len(res)))
        if res:
            for o in res:
                self.log.debug('  - {}: {}'.format(o.__class__.__name__, o.id))
        return res

    def get_reqts_for_project(self, project):
        """
        Get all requirements whose owner is the specified project.

        Args:
            project (Project):  the specified project
        """
        self.log.info('* [orb] get_reqts_for_project({})'.format(
                                        getattr(project, 'id', '[None]')))
        if not project:
            self.log.info('  no project provided -- returning empty list.')
            return []
        reqts = self.search_exact(cname='Requirement', owner=project)
        return reqts

    def count_reqts_for_project(self, project):
        """
        Get a count of the requirements whose owner is the specified project.

        Args:
            project (Project):  the specified project
        """
        self.log.info('* [orb] count_reqts_for_project({})'.format(
                                        getattr(project, 'id', '[None]')))
        if not project:
            self.log.info('  no project provided -- returning 0.')
            return 0
        # return self.db.query(self.classes['Requirement']).count()
        return self.db.query(self.classes['Requirement']).filter_by(
                                                        owner=project).count()

    def get_next_ref_des(self, assembly, component, prefix=None):
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
        """
        # TODO:  use a product type abbreviation for 'prefix' (or some other
        # semantic ref designator algorithm)
        prefix = 'Generic'
        if component.product_type:
            prefix = component.product_type.name
        acus = self.search_exact(cname='Acu', assembly=assembly)
        if acus:
            rds = [acu.reference_designator for acu in acus]
            # allow product_type to contain '-' (but it shouldn't)
            all_prefixes = [(' '.join(rd.split(' ')[:-1])) for rd in rds if rd]
            these_prefixes = [p for p in all_prefixes if p == prefix]
            new_nbr = len(these_prefixes) + 1
            return prefix + ' ' + str(new_nbr)
        else:
            return prefix + ' 1'

    def delete(self, objs):
        """
        Delete the specified objects from the local db.

        Args:
            objs (Iterable of Identifiable or subtype): objects in the local db
        """
        self.log.info('* bulk_delete() called ...')
        # TODO: make sure appropriate relationships in which these objects
        # are the parent or child are also deleted
        info = []
        refresh_parameterz = False
        refresh_assemblies = []
        local_user = self.get(state.get('local_user_oid', 'me'))
        for obj in objs:
            if not obj:
                info.append('   None (ignored)')
                continue
            info.append('   id: {}, name: {} (oid {})'.format(obj.id, obj.name,
                                                              obj.oid))
            if isinstance(obj, self.classes['Product']):
                psus = obj.projects_using_system
                for psu in psus:
                    info.append('   id: {}, name: {} (oid {})'.format(psu.id,
                                                                   psu.name,
                                                                   psu.oid))
                    self.db.delete(psu)
                child_acus = obj.components
                if child_acus:
                    for acu in child_acus:
                        info.append('   id: {}, name: {} (oid {})'.format(
                                                                    acu.id,
                                                                    acu.name,
                                                                    acu.oid))
                        self.db.delete(acu)
                    if obj.oid in componentz:
                        del componentz[obj.oid]
                parent_acus = obj.where_used
                if parent_acus:
                    for acu in parent_acus:
                        info.append('   id: {}, name: {} (oid {})'.format(
                                                                    acu.id,
                                                                    acu.name,
                                                                    acu.oid))
                        assembly = acu.assembly
                        self.db.delete(acu)
                        if assembly.oid in componentz:
                            refresh_assemblies.append(assembly)
            if parameterz.get(obj.oid):
                # NOTE: very important:  remove oid from parameterz
                del parameterz[obj.oid]
                refresh_parameterz = True
            elif isinstance(obj, self.classes['Acu']):
                if getattr(obj.assembly, 'oid') in componentz:
                    refresh_assemblies.append(obj.assembly)
                refresh_parameterz = True
            creator = getattr(obj, 'creator', None)
            if creator == local_user:
                # if local_user created obj, add it to trash
                trash[obj.oid] = serialize(self, [obj])
            self.db.delete(obj)
        self.db.commit()
        self.log.info(' - objs deleted:')
        for text in info:
            self.log.info(text)
        if refresh_assemblies:
            for assembly in refresh_assemblies:
                refresh_componentz(self, assembly)
        if refresh_parameterz:
            self.recompute_parmz()

    def is_versioned(self, obj):
        """
        Determine if a object is being versioned:  (1) it has a 'version'
        attribute and (2) its 'version' attribute has been assigned a non-null
        version (i.e. a non-empty string)
        """
        if obj.__class__.__name__ in self.versionables and obj.version:
            return True
        return False

# A node has only one instance of UberORB, the 'orb', which is intended to be
# imported by all application components.
orb = UberORB()

