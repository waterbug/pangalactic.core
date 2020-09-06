# -*- coding: utf-8 -*-
"""
Pan Galactic hub for object metadata and storage operations.

NOTE:  Only the `orb` instance created in this module should be imported (it is
intended to be a singleton).
"""
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
from pangalactic.core             import refdata
from pangalactic.core.entity      import (dmz, load_dmz, save_dmz,
                                          entz, load_entz, save_entz,
                                          ## NOTE: deactivating PartsList stuff
                                          # load_plz, save_plz,
                                          # pliz, load_pliz, save_pliz,
                                          schemaz, load_schemaz, save_schemaz,
                                          load_ent_histz, save_ent_histz)
from pangalactic.core.registry    import PanGalacticRegistry
from pangalactic.core.utils.meta  import uncook_datetime
from pangalactic.core.mapping     import schema_maps, schema_version
from pangalactic.core.parametrics import (add_context_parm_def,
                                          add_default_parameters,
                                          add_default_data_elements,
                                          add_parameter,
                                          componentz,
                                          _compute_pval,
                                          compute_requirement_margin,
                                          data_elementz, de_defz,
                                          get_dval, get_parameter_id,
                                          load_data_elementz,
                                          save_data_elementz,
                                          load_parmz, save_parmz,
                                          parameterz, parm_defz,
                                          parmz_by_dimz,
                                          refresh_componentz,
                                          refresh_req_allocz, req_allocz,
                                          update_de_defz,
                                          update_parm_defz,
                                          update_parmz_by_dimz)
from pangalactic.core.serializers import serialize, deserialize
from pangalactic.core.test        import data as test_data_mod
from pangalactic.core.test        import vault as test_vault_mod
from pangalactic.core.test.utils  import gen_test_dvals, gen_test_pvals
from pangalactic.core.utils.datetimes import dtstamp, file_dts
from pangalactic.core.log         import get_loggers
from pangalactic.core.validation  import get_assembly
from functools import reduce


class UberORB(object):
    """
    The UberORB mediates all communications with local objects, local storage,
    the local metadata registry, and remote repositories and services.

    IMPORTANT:  The UberORB is intended to be a singleton.  The UberORB class
    should not be imported; instead, import 'orb', the module-level instance
    created at the end of this module.

    NOTE:  the orb does not have an __init__() in order to avoid side-effects
    of importing the module-level instance that is created -- its start()
    method must be called to initialize it.

    Attributes:
        classes (dict):  a mapping of `meta_id`s to runtime app classes.
        data (dict):  in-memory cache of DataMatrix instances
        data_store (str):  path to directory in which tsv-serialized instances
            of DataMatrix are stored
        db (Session):  interface to the local db
        db_engine (SQLAlchemy orm):  result of registry `create_engine`
        error_log (Logger):  instance of pgorb_error_logger
        home (str):  full path to the application home directory -- populated
            by orb.start()
        log (Logger):  instance of pgorb_logger
        new_oids (list of str):  oids of objects that have been created but not
            saved
        registry (PanGalacticRegistry):  instance of PanGalacticRegistry
        remote (TBD) interface to remote services [TO BE IMPLEMENTED]
        role_product_types: cache that maps Role ids to corresponding
            ProductType ids (used by the 'access' module, which determines user
            permissions relative to domain objects
        schemas (dict):  see definition in
            p.meta.registry._update_schemas_from_extracts
    """
    started = False
    startup_msg = '* orb starting up ...'
    new_oids = []

    def start(self, home=None, db_url=None, console=False, debug=False,
              log_msgs=None, **kw):
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
            log_msgs (list of str):  initial log message(s)
        """
        if self.started:
            return
        self.log_msgs = log_msgs or []
        # set home directory -- in order of precedence:
        # [1] 'home' kw arg (this should be set by the application, if any)
        if home:
            pgx_home = home
        # [2] from 'PANGALACTIC_HOME' env var
        elif 'PANGALACTIC_HOME' in os.environ:
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
        # --------------------------------------------------------------------
        # ### NOTE:  user-set config overrides app config
        # --------------------------------------------------------------------
        # If values in the "config" file have been edited, they will take
        # precedence over any config set by app defaults:  'read_config()' does
        # config.update() from the "config" file contents.
        read_config(os.path.join(pgx_home, 'config'))
        # --------------------------------------------------------------------
        # ### NOTE:  saved "state" file represents most recent state of app
        read_state(os.path.join(pgx_home, 'state'))
        # --------------------------------------------------------------------
        # Saved prefs and trash are read here; will be overwritten by
        # any new prefs and trash set at runtime.
        read_prefs(os.path.join(pgx_home, 'prefs'))
        read_trash(os.path.join(pgx_home, 'trash'))
        # create "file vault"
        self.vault = os.path.join(pgx_home, 'vault')
        if not os.path.exists(self.vault):
            os.makedirs(self.vault, mode=0o755)
        self.logging_initialized = False
        self.start_logging(home=pgx_home, console=console, debug=debug)
        self.log.debug('* config read ...')
        self.log.debug('* state read ...')
        # self.log.debug('  state: {}'.format(str(state)))
        self.log.debug('* prefs read ...')
        # self.log.debug('  prefs: {}'.format(str(prefs)))
        self.log.debug('* trash read ({} objects).'.format(len(trash)))
        if 'units' not in prefs:
            prefs['units'] = {}
        # create in-memory cache for DataMatrix instances
        self.data = {}
        # create storage area for serialized DataMatrix instances (.tsv files)
        self.data_store = os.path.join(pgx_home, 'data')
        if not os.path.exists(self.data_store):
            os.makedirs(self.data_store, mode=0o755)
        # * copy test data files from 'p.test.data' module to test_data_dir
        self.test_data_dir = os.path.join(pgx_home, 'test_data')
        current_test_files = set()
        # self.log.debug('* checking for test data in [pgx_home]/test_data...')
        if not os.path.exists(self.test_data_dir):
            os.makedirs(self.test_data_dir)
        else:
            current_test_files = set(os.listdir(self.test_data_dir))
        self.log.debug('  - found {} data files'.format(
                       len(current_test_files)))
        test_data_mod_path = test_data_mod.__path__[0]
        test_data_files = set([s for s in os.listdir(test_data_mod_path)
                               if (not s.startswith('__init__')
                               and not s.startswith('__pycache__'))
                               ])
        test_data_to_copy = test_data_files - current_test_files
        self.log.debug('  - data files to be installed: '.format(
                       len(test_data_to_copy)))
        if test_data_to_copy:
            self.log.debug('  - copying data files into test_data dir...')
            test_data_cpd = []
            for p in test_data_to_copy:
                shutil.copy(os.path.join(test_data_mod_path, p),
                            self.test_data_dir)
                test_data_cpd.append(p)
            # self.log.debug('  - new test data files installed: %s'
                          # % str(test_data_cpd))
        else:
            self.log.debug('  - all test data files already installed.')
        # * copy files from 'p.test.vault' module to vault_dir
        self.log.debug('* checking for files in [pgx_home]/vault ...')
        current_vault_files = set(os.listdir(self.vault))
        self.log.debug('  - found {} vault files:'.format(
                       len(current_vault_files)))
        # if current_vault_files:
            # for fpath in current_vault_files:
                # self.log.debug('    {}'.format(fpath))
        vault_mod_path = test_vault_mod.__path__[0]
        test_vault_files = set([s for s in os.listdir(vault_mod_path)
                               if (not s.startswith('__init__')
                               and not s.startswith('__pycache__'))
                               ])
        vault_files_to_copy = test_vault_files - current_vault_files
        self.log.debug('  - new test vault files to be installed: {}'.format(
                       len(vault_files_to_copy)))
        if vault_files_to_copy:
            self.log.debug('  - copying test vault files into vault dir...')
            vault_files_copied = []
            for p in vault_files_to_copy:
                shutil.copy(os.path.join(vault_mod_path, p), self.vault)
                vault_files_copied.append(p)
            # self.log.debug('  - new test vault files installed: {}'.format(
                           # str(vault_files_copied)))
        else:
            self.log.debug('  - all test vault files already installed.')
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
            # [a] drop and create database:
            #     self.drop_and_create_db(pgx_home)
            # [b] initialize registry with "force_new_core" to create the new
            #     classes and db tables:
            # self.init_registry(pgx_home, db_url, force_new_core=True,
                               # version=schema_version, debug=False,
                               # console=console)
            # [c] transform and import data that was dumped previously:
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
        # basically, versionables == {Product and all its subclasses}
        self.versionables = [cname for cname in self.classes if 'version' in
                             self.schemas[cname]['field_names']]
        # [3] load (and update) ref data ... note that this must be done AFTER
        #     config and state have been created and updated
        self.load_reference_data()
        # ---------------------------------------------------------------------
        # ### NOTE:  user or app configured schemas can override reference data
        # -- if there are any pre-configured schemas, they are updated here ...
        if config.get('schemaz'):
            schemaz.update(config['schemaz'])
        # ---------------------------------------------------------------------
        self._load_diagramz()
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
        save_entz(self.home)
        save_ent_histz(self.home)
        # save_pliz(self.home)
        # save_plz(self.home)
        save_schemaz(self.home)
        save_dmz(self.home)
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
        self.log.debug(msg)
        self.startup_msg = msg
        if not getattr(self, 'db', None):
            Session = sessionmaker(bind=self.db_engine)
            self.db = Session()
            # NOTE:  DO NOT *EVER* USE 'expire_on_commit = False' here!!!
            #        -> it causes VERY weird behavior ...

    def dump_db(self, fmt='yaml', dir_path='backup'):
        """
        Serialize all db objects, along with all their parameters and data
        elements, and write to `db.yaml` in the specified directory.
        """
        self.log.info('* dump_db()')
        self.db_dump_complete = False
        dts = file_dts()
        if not dir_path:
            # if no dir_path specified, assume backup
            dir_path = os.path.join(self.home, 'backup')
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        json_fname = 'db-dump-' + dts + '.json'
        yaml_fname = 'db-dump-' + dts + '.yaml'
        if fmt == 'json':
            f = open(os.path.join(dir_path, json_fname), 'w')
            f.write(json.dumps(serialize(
                    self, self.get_all_subtypes('Identifiable'),
                    include_refdata=True),
                    separators=(',', ':'),
                    indent=4, sort_keys=True))
            f.close()
        elif fmt == 'yaml':
            self.log.info('  dumping database to yaml file ...')
            f = open(os.path.join(dir_path, yaml_fname), 'w')
            f.write(yaml.safe_dump(serialize(
                    self, self.get_all_subtypes('Identifiable'),
                    include_refdata=True)))
            f.close()
        self.log.info('  dump to {} completed.'.format(fmt))
        self.db_dump_complete = True

    def save_caches(self, dir_path=None):
        """
        Serialize all caches (data_elementz, parameterz, entz, ent_histz,
        schemaz, and dmz) to files in the specified directory.
        """
        self.log.info('* save_caches()')
        self.cache_dump_complete = False
        dts = file_dts()
        if not dir_path:
            # if no dir_path specified, assume backup
            backup_path = os.path.join(self.home, 'backup')
            dir_path = os.path.join(backup_path, 'caches-' + dts)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        save_data_elementz(dir_path)
        save_parmz(dir_path)
        save_entz(dir_path)
        save_ent_histz(dir_path)
        # save_pliz(dir_path)
        # save_plz(dir_path)
        save_schemaz(dir_path)
        save_dmz(dir_path)
        self.cache_dump_complete = True
        self.log.info('  cache dump completed.')

    def dump_all(self, dir_path=None):
        self.save_caches(dir_path=dir_path)
        self.dump_db(dir_path=dir_path)

    # def drop_and_create_db(self, home):
        # """
        # Drop the database and create a new one -- used when the schema has
        # changed.

        # Args:
            # home (str):  home directory (full path)
        # """
        # self.log.debug('* drop_and_create_db() ...')
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
                        # self.log.debug('  database "{}" dropped.'.format(
                                                                 # db_name))
                        # cur.execute('CREATE DATABASE {};'.format(db_name))
                # self.log.debug('  database "{}" created.'.format(db_name))
            # except:
                # self.log.debug('  problem encountered -- see error log.')
                # self.error_log.info('* error in drop_and_create_db():')
                # self.error_log.info(traceback.format_exc())
        # elif db_url and db_url.startswith('sqlite:'):
            # # if the db is sqlite, simply remove its file; the registry will
            # # create a new one when it starts up
            # try:
                # db_path = os.path.join(home, 'local.db')
                # if os.path.exists(db_path):
                    # os.remove(db_path)
                    # self.log.debug('  db file removed.')
                # else:
                    # self.log.debug('  file "local.db" not found.')
            # except:
                # self.log.debug('  error encounterd in removing db file.')
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
            # self.log.debug('* diagramz cache read from diagrams.json')
        else:
            # self.log.debug('* no diagrams.json file found.')
            pass

    def _save_diagramz(self):
        """
        Save `diagramz` cache to diagrams.json file.
        """
        self.log.debug('* _save_diagramz() ...')
        json_path = os.path.join(self.home, 'diagrams.json')
        with open(json_path, 'w') as f:
            f.write(json.dumps(diagramz, separators=(',', ':'),
                               indent=4, sort_keys=True))
        self.log.debug('  ... diagrams.json file written.')

    def recompute_parmz(self):
        """
        Recompute any computed parameters for the configured variables and
        contexts.  This is required at startup or when a parameter is created,
        modified, or deleted.
        """
        # self.log.debug('* recompute_parmz()')
        # TODO:  preferred contexts should override defaults
        # default descriptive contexts:  CBE, MEV
        d_contexts = config.get('descriptive_contexts', ['CBE', 'MEV']) or []
        variables = config.get('variables', ['m', 'P', 'R_D']) or []
        # NOTE: this iterates only over assembly oids (i.e., keys in the
        # 'componentz' cache), because _compute_pval() is recursive and will
        # recompute all lower-level component/subassembly values in each call
        # NOTE: a further implication is that non-products (e.g. Port,
        # PortTemplate, etc.) DO NOT HAVE COMPUTED PARAMETERS ...
        for context in d_contexts:
            for variable in variables:
                # slightly kludgy, but ALL HW (and ONLY HW) should have ALL
                # these variables and context parameters, period!
                for oid in self.get_oids(cname='HardwareProduct'):
                    pid = get_parameter_id(variable, context)
                    val = _compute_pval(oid, variable, context)
                    if oid not in parameterz:
                        parameterz[oid] = {}
                    if pid not in parameterz[oid]:
                        add_parameter(oid, pid)
                    parameterz[oid][pid]['value'] = val
        # Recompute Margins for all performance requirements
        # [0] Remove any previously computed performance requirements (NTEs and
        #     Margins) in case any requirements have been deleted or
        #     re-allocated
        pid_deletions = []
        oid_deletions = []
        for oid in parameterz:
            for pid in parameterz[oid]:
                if 'Margin' in pid or 'NTE' in pid:
                    pid_deletions.append((oid, pid))
        for oid, pid in pid_deletions:
            del parameterz[oid][pid]
            if not parameterz[oid]:
                oid_deletions.append(oid)
        for oid in oid_deletions:
            del parameterz[oid]
        # [1] iterate over current set of performance requirements, which
        # should already have been identified by running refresh_req_allocz()
        for req_oid in req_allocz:
            # compute_requirement_margin() returns a tuple:
            # 0: oid of Acu or PSU to which reqt is allocated
            # 1: id of performance parameter
            # 2: nte value (max) of performance parameter
            # 3: units of nte value
            # 4: margin [result] (expressed as a %)
            oid, pid, nte, nte_units, result = compute_requirement_margin(
                                                                    req_oid)
            if oid:
                margin_pid = get_parameter_id(pid, 'Margin')
                nte_pid = get_parameter_id(pid, 'NTE')
                # self.log.debug('  - {} at {}: {}'.format(pid, oid,
                                                               # result))
                if oid not in parameterz:
                    parameterz[oid] = {}
                if isinstance(result, (int, float)):
                    # if result is int or float, set it as margin; otherwise,
                    # it is a message indicating that margin could not be
                    # computed
                    parameterz[oid][margin_pid] = dict(value=result, units='%',
                                                   mod_datetime=str(dtstamp()))
                parameterz[oid][nte_pid] = dict(value=nte,
                                                units=nte_units,
                                                mod_datetime=str(dtstamp()))
            else:
                # if oid is empty, reason for failure will be in "result"
                # self.log.debug(' - margin comp. failed for req with oid:')
                # self.log.debug('   "{}"'.format(req_oid))
                # self.log.debug('   computation result: {}'.format(result))
                pass

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
            gen_test_dvals(data_elementz.get(o.oid))
            add_default_parameters(o, parms=parms)
            gen_test_pvals(parameterz[o.oid])
        self.recompute_parmz()
        self.log.debug('  ... done.')

    def _build_componentz_cache(self):
        """
        Build the `componentz` cache (which maps Product oids to the oids of
        their components) at startup.
        """
        # self.log.debug('* _build_componentz_cache()')
        for product in self.get_all_subtypes('Product'):
            if product.components:
                refresh_componentz(product)
        # self.log.debug('  componentz cache ready.')

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

    def load_and_transform_data(self):
        """
        Load and transform all dumped serialized data to the new schema.
        Called when restarting after an upgrade that includes a schema change.
        """
        self.log.info('* transforming all data to new schema ...')
        sdata = ''
        data_path = os.path.join(self.vault, 'db.yaml')
        if os.path.exists(data_path):
            try:
                f = open(data_path)
                sdata = yaml.safe_load(f.read())
                if __version__ in schema_maps:
                    map_fn = schema_maps[__version__]
                    sdata = map_fn(sdata)
                    self.log.debug('  - data loaded and transformed.')
                else:
                    self.log.debug('  - data loaded (no transformation).')
            except:
                self.log.debug('  - an error ocurred (see error log).')
                self.error_log.info('* error in load_and_transform_data():')
                self.error_log.info(traceback.format_exc())
        else:
            self.log.debug('  - file "db.yaml" not found.')
        return sdata

    def load_reference_data(self):
        """
        Create reference data objects.  Performed at orb start up, since new
        objects created at runtime refer to some of the reference objects.
        """
        self.log.info('* checking reference data ...')
        # first get the oids of everything in the db ...
        db_oids = self.get_oids()
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
            # for o in i_objs:
                # self.db.add(o)
            # self.db.commit()
        admin = self.get('pgefobjects:admin')
        pgana = self.get('pgefobjects:PGANA')
        self.log.info('  + initial reference data loaded.')
        # [1] load any parameter definitions and contexts that may be missing
        #     from the current db (in a first-time installation, this will of
        #     course be *all* parameter definitions and contexts)
        missing_p = [so for so in refdata.pdc if so['oid'] not in db_oids]
        if missing_p:
            self.log.debug('  + missing some reference parameters/contexts:')
            self.log.debug('  {}'.format([so['oid'] for so in missing_p]))
            p_objs = deserialize(self, [so for so in missing_p],
                                 include_refdata=True,
                                 force_no_recompute=True)
            self.save(p_objs)
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
        # [2] XXX IMPORTANT!  Create the parameter definitions caches
        # ('parm_defz' and 'parmz_by_dimz') before loading parameters from
        # 'parameters.json' -- the deserializer uses these caches.  Note that
        # create_de_defz will first populate 'de_defz' from
        # DataElementDefinitions found in the database (some are initially
        # created from refdata and additional ones may be created at runtime
        # and saved in the db) and then will check for data element definitions
        # in config['de_defz'], which may be part of the app config or a
        # user-edited config -- if any are found, it will create
        # DataElementDefinitions from them, add them to the database, and then
        # add them to 'de_defz'.
        self.create_de_defz()
        self.create_parm_defz()
        self.create_parmz_by_dimz()
        # *** NOTE ***********************************************************
        # [3] run _load_parmz() and _load_data_elementz() before checking for
        # updates to data element definitions and parameter definitions and
        # contexts, since updated ref data may update data element and
        # parameter data that was loaded from the parameters cache
        # (parameters.json) -- e.g., some ref data objects might have updated
        # parameters
        # ********************************************************************
        load_data_elementz(self.home)
        load_parmz(self.home)
        self.log.debug('* loading entz ...')
        load_entz(self.home)
        self.log.debug('  entz: {}'.format(str(entz)))
        # self.log.debug('* loading pliz ...')
        # load_pliz(self.home)
        # self.log.debug('  pliz: {}'.format(str(pliz)))
        # self.log.debug('* loading plz ...')
        # load_plz(self.home)
        # self.log.debug('  plz: {}'.format(str(pliz)))
        self.log.debug('* loading ent_histz ...')
        load_ent_histz(self.home)
        self.log.debug('* loading schemaz ...')
        load_schemaz(self.home)
        self.log.debug('* loading dmz ...')
        load_dmz(self.home)
        self.log.debug('  dmz: {}'.format(str(dmz)))
        self.recompute_parmz()
        # [4] check for updates to parameter definitions and contexts
        self.log.debug('  + checking for updates to parameter definitions ...')
        all_pds = refdata.pdc
        all_pd_oids = [so['oid'] for so in all_pds]
        # get mod_datetimes of all current ref data objects
        pd_mod_dts = self.get_mod_dts(oids=all_pd_oids)
        # compare them to all newly imported refdata objects
        updated_pds = [so for so in all_pds
                       if (uncook_datetime(so.get('mod_datetime')) and
                           uncook_datetime(pd_mod_dts.get(so['oid'])) and
                           (uncook_datetime(so.get('mod_datetime')) >
                           uncook_datetime(pd_mod_dts.get(so['oid']))))] 
        if updated_pds:
            self.log.debug('    {} updates found ...'.format(len(updated_pds)))
            deserialize(self, updated_pds, include_refdata=True)
            self.log.debug('    parameter definition updates completed.')
        else:
            self.log.debug('    no updates found.')
        # [5] load balance of any reference data missiong from db
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
            self.db.add(o)
        # [6] check for updates to reference data other than parameter defs
        self.log.debug('  + checking for updates to reference data ...')
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
            self.log.debug('    {} updates found ...'.format(len(updated_r)))
            deserialize(self, updated_r, include_refdata=True)
            self.log.debug('    updates completed.')
        else:
            self.log.debug('    no updates found.')
        # [7] delete deprecated reference data
        #     **********************************************************
        #     NOTE:  DON'T DO THIS STEP UNTIL ALL DATA RELATED TO THE
        #     DEPRECATED DATA HAS BEEN REMOVED FROM THE CURRENT DATABASE
        #     **********************************************************
        # db_oids = self.get_oids()
        # deprecated = [oid for oid in refdata.deprecated if oid in db_oids]
        # if deprecated:
            # self.log.debug('  + deleting deprecated reference data:')
            # self.log.debug('  {}'.format([oid for oid in deprecated]))
            # for oid in deprecated:
                # self.delete([self.get(oid) for oid in deprecated])
        # build the 'componentz' runtime cache, which is used in recomputing
        # parameters ...
        self._build_componentz_cache()
        # update the req_allocz runtime cache (used in computing margins)
        for req in self.get_by_type('Requirement'):
            refresh_req_allocz(req)
        self.recompute_parmz()
        self.log.info('  + all reference data loaded.')

    #########################################################################
    # PARAMETER AND DATA ELEMENT STUFF
    # Note:  ParameterDefinition and DataElementDefinition may eventually
    # be removed from the db and become independent of the orb, and move back
    # to the parametrics module ...
    #########################################################################

    def create_parm_defz(self):
        """
        Create the `parm_defz` cache of ParameterDefinitions, in the format:

            {parameter_id : {name, variable, context, context_type, description,
                             dimensions, range_datatype, computed, mod_datetime},
             data_element_id : {name, description, range_datatype, mod_datetime},
             ...}
        """
        self.log.debug('* create_parm_defz')
        pds = self.get_by_type('ParameterDefinition')
        # first, the "simple variable" parameters ...
        pd_dict = {pd.id :
                   {'name': pd.name,
                    'variable': pd.id,
                    'context': None,
                    'context_type': None,
                    'description': pd.description,
                    'dimensions': pd.dimensions,
                    'range_datatype': pd.range_datatype,
                    'computed': False,
                    'mod_datetime':
                        str(getattr(pd, 'mod_datetime', '') or dtstamp())
                    } for pd in pds}
        parm_defz.update(pd_dict)
        self.log.debug('      bases created: {}'.format(
                                                str(list(pd_dict.keys()))))
        # add PDs for the descriptive contexts (CBE, Contingency, MEV) for the
        # variables (Mass, Power, Datarate) for which functions have been defined
        # to compute the CBE and MEV values
        all_contexts = self.get_by_type('ParameterContext')
        self.log.debug('      adding context parms for: {}'.format(
                                        str([c.id for c in all_contexts])))
        for pid in ['m', 'P', 'R_D']:
            pd = self.select('ParameterDefinition', id=pid)
            for c in all_contexts:
                add_context_parm_def(pd, c)
        # all float-valued parameters should have associated Contingency parms
        float_pds = [pd for pd in pds if pd.range_datatype == 'float']
        contingency = self.select('ParameterContext', name='Contingency')
        self.log.debug('      adding Ctgcy parms for float types: {}'.format(
                                        str([pd.id for pd in float_pds])))
        for float_pd in float_pds:
            contingency_pid = get_parameter_id(float_pd.id, contingency.id)
            if contingency_pid not in parm_defz:
                add_context_parm_def(float_pd, contingency)

    def create_parmz_by_dimz(self):
        """
        Create the `parmz_by_dimz` cache, where the cache has the form

            {dimension : [ids of ParameterDefinitions having that dimension]}
        """
        self.log.debug('* create_parmz_by_dimz')
        pds = self.get_by_type('ParameterDefinition')
        dimz = set([pd.dimensions for pd in pds])
        parmz_by_dimz.update({dim : [pd.id for pd in pds if pd.dimensions == dim]
                              for dim in dimz})

    def create_de_defz(self):
        """
        Create the `de_defz` cache of DataElementDefinitions, in the format:

            {data_element_id : {name, description, range_datatype, mod_datetime},
             ...}
        """
        self.log.debug('* create_de_defz')
        # check for localized data element definition structures in
        # config['de_defz'] -- these can be introduced by an app
        new_dedef_objs = []
        self.log.debug('  - checking for de defs in config["de_defz"] ...')
        new_config_dedef_ids = []
        # NEW: check for labels even if the dedef objects are not new, so that
        # labels can be updated by new app config at startup ...
        config_dedef_labels = {}
        if config.get('de_defz'):
            ded_ids = self.get_ids('DataElementDefinition')
            new_config_dedef_ids = [deid for deid in config['de_defz']
                                    if deid not in ded_ids]
            config_dedef_labels.update({deid: de_def.get('label')
                                for deid, de_def in config['de_defz'].items()
                                if de_def.get('label')})
            if new_config_dedef_ids:
                # if any are found, create DataElementDefinitions from them,
                # making sure to save their 'label' fields separately since
                # they are not yet supported by DataElementDefinition ...
                dt = dtstamp()
                admin = orb.get('pgefobjects:admin')
                DataElementDefinition = self.classes.get(
                                                    'DataElementDefinition')
                for deid in new_config_dedef_ids:
                    ded = config['de_defz'][deid]
                    ded_oid = 'pgef:DataElementDefinition.' + deid
                    dt = uncook_datetime(ded.get('mod_datetime')) or dt
                    descr = ded.get('description') or ded.get('name', deid)
                    name = ded.get('name', deid)
                    ded_obj = DataElementDefinition(oid=ded_oid, id=deid,
                                                name=name,
                                                label=ded.get('label', name),
                                                range_datatype=ded[
                                                            'range_datatype'],
                                                creator=admin, modifier=admin,
                                                description=descr,
                                                create_datetime=dt,
                                                mod_datetime=dt)
                    new_dedef_objs.append(ded_obj)
            if new_dedef_objs:
                self.save(new_dedef_objs)
        de_def_objs = self.get_by_type('DataElementDefinition')
        de_defz.update(
            {de_def_obj.id :
             {'name': de_def_obj.name,
              'label': de_def_obj.label,
              'description': de_def_obj.description,
              'range_datatype': de_def_obj.range_datatype,
              'mod_datetime':
                  str(getattr(de_def_obj, 'mod_datetime', '') or dtstamp())
              } for de_def_obj in de_def_objs}
              )
        # update config_dedz with labels, if they have any
        # TODO:  add labels as "external names" in p.core.meta
        # if new_config_dedef_ids:
            # for deid in new_config_dedef_ids:
                # ded = config['de_defz'][deid]
                # if de_defz.get(deid) and ded.get('label'):
                    # de_defz[deid]['label'] = ded['label']
        # if config_dedef_labels:
            # for deid in config_dedef_labels:
                # de_defz[deid]['label'] = config_dedef_labels[deid]
        self.log.debug('  - data element defs created: {}'.format(
                                                str(list(de_defz.keys()))))

    ##########################################################################
    # DB FUNCTIONS
    ##########################################################################

    def save(self, objs, recompute=True):
        """
        Save the specified objects to the local db.  (CAVEAT: this will
        update ["merge"] any object that already exists in the db.)

        NOTE:  alteration of the 'mod_datetime' of objects is *NOT* a
        side-effect of the orb save() function, because the orb.save() is used
        for both local objects and objects received from remote (network)
        sources, whose 'mod_datetime' must be preserved when saving locally.
        Therefore, locally created or modified objects must be time-stamped
        *before* they are passed to orb.save().

        Args:
            objs (iterable of objects):  the objects to be saved
        """
        recompute_required = False
        for obj in objs:
            cname = obj.__class__.__name__
            oid = getattr(obj, 'oid', None)
            # if the object is used in any assemblies, recompute parameters
            # TODO:  target the recompute to the specific assemblies ...
            if getattr(obj, 'where_used', []):
                recompute_required = True
            # self.log.debug('* orb.save')
            new = bool(oid in self.new_oids) or not self.get(oid)
            if new:
                log_txt = 'orb.save: {} is a new {}, saving it ...'.format(
                           getattr(obj, 'id', '[unknown]'), cname)
                self.log.debug('* {}'.format(log_txt))
                self.db.add(obj)
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
                if self.is_versioned(obj):
                    # if obj is being versioned, bump its iteration #
                    # NOTE:  TODO (maybe) yes, this means iterations are not
                    # tracked in the db ... that's a separate issue
                    if obj.iteration is None:
                        obj.iteration = 0
                    obj.iteration += 1
                self.db.merge(obj)
            if hasattr(obj, 'owner') and not obj.owner:
                # ensure 'owner' is always populated if present!
                if obj.creator and getattr(obj.creator, 'org', None):
                    # first fallback:  owner is creator's org ...
                    obj.owner = obj.creator.org
                else:
                    # ultimate fallback:  owner is PGANA
                    obj.owner = self.get('pgefobjects:PGANA')
            if cname == 'Acu':
                refresh_componentz(obj.assembly)
                if not new:
                    # find all allocations to this Acu and refresh them ...
                    alloc_reqs = [req_oid for req_oid in req_allocz
                                  if req_allocz[req_oid][0] == obj.oid]
                    if alloc_reqs:
                        for req_oid in alloc_reqs:
                            req = self.get(req_oid)
                            if req:
                                refresh_req_allocz(req)
                            else:
                                # if requirement not there, remove alloc
                                del alloc_reqs[req_oid]
                recompute_required = True
            elif cname == 'HardwareProduct':
                # make sure HW Products have mass, power, data rate parms
                if obj.oid not in parameterz:
                    parameterz[obj.oid] = {}
                for pid in ['m', 'P', 'R_D']:
                    if not parameterz[obj.oid].get(pid):
                         add_parameter(obj.oid, pid)
                recompute_required = True
            elif cname == 'ProjectSystemUsage':
                if not new:
                    # find all allocations to this PSU and refresh them ...
                    alloc_reqs = [req_oid for req_oid in req_allocz
                                  if req_allocz[req_oid][0] == obj.oid]
                    if alloc_reqs:
                        for req_oid in alloc_reqs:
                            req = self.get(req_oid)
                            if req:
                                refresh_req_allocz(req)
                            else:
                                # if requirement not there, remove alloc
                                del alloc_reqs[req_oid]
                # TODO: is recompute required here???
                # recompute_required = True
            elif cname == 'Requirement' and obj.req_type == 'performance':
                refresh_req_allocz(obj)
                recompute_required = True
            elif cname == 'DataElementDefinition':
                # NOTE:  all DataElementDefinitions are public
                obj.public = True
                update_de_defz(obj)
            elif cname == 'ParameterDefinition':
                # NOTE:  all ParameterDefinitions are public
                obj.public = True
                update_parm_defz(obj)
                update_parmz_by_dimz(obj)
        # self.log.debug('  orb.save:  committing db session.')
        self.db.commit()
        if recompute_required and recompute:
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
            # self.log.debug('* get(%s)' % oid[0])
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
            self.log.debug('* get() [no arguments provided]')
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
        return self.db.query(self.classes[cname]).count()

    def get_by_type(self, cname):
        """
        Get objects from the local db by class name.

        Args:
            cname (str):  the class name of the objects to be retrieved 

        Returns:
            an iterator of objects of the specified class (may be empty)
        """
        # self.log.debug('* get_by_type(%s)' % cname)
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
        # self.log.debug('* get_all_subtypes(%s)' % cname)
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

    def get_ids(self, cname=None):
        """
        Get all ids from the local db -- used for validating ids.  Returns:

          [1] with no arguments:  all ids in the db
          [2] with 'cname':  all ids for objects of the specified class

        Keyword Args:
            cname (str):  class name of the objects to be used
        """
        Identifiable = self.classes['Identifiable']
        query = self.db.query(Identifiable.id)
        if cname:
            query = query.filter(Identifiable.pgef_type == cname)
        return [row[0] for row in query.all()]

    def gen_product_id(self, obj):
        """
        Create a unique 'id' attribute for a new HardwareProduct or Template.

        Args:
            obj (HardwareProduct or Template):  obj for which to generate an
                'id'
        """
        self.log.debug('* gen_product_id')
        if not isinstance(obj, (self.classes['HardwareProduct'],
                                self.classes['Template'])):
            return ''
        all_ids = self.get_ids(cname='HardwareProduct')
        all_ids += self.get_ids(cname='Template')
        self.log.debug('  all_ids:')
        self.log.debug('  {}'.format(str(all_ids)))
        id_suffixes = [(i or '').split('-')[-1] for i in all_ids]
        self.log.debug('  id_suffixes:')
        self.log.debug('  {}'.format(str(id_suffixes)))
        current_id_parts = (obj.id or '').split('-')
        self.log.debug('  current_id_parts: {}'.format(str(current_id_parts)))
        if current_id_parts[-1] in id_suffixes:
            id_suffixes.remove(current_id_parts[-1])
        # if the 'Vendor' data element has a non-blank value, the owner id is
        # set to 'Vendor'
        if get_dval(obj.oid, 'Vendor'):
            owner_id = 'Vendor'
        else:
            owner_id = getattr(obj.owner, 'id', 'Owner-Unknown')
        self.log.debug('  owner_id: {}'.format(owner_id))
        pt_abbr = getattr(obj.product_type, 'abbreviation', 'TBD') or 'TBD'
        self.log.debug('  pt_abbr: {}'.format(pt_abbr))
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
        if not isinstance(obj.product_type, self.classes['ProductType']):
            # no product_type assigned yet
            abbrev = 'TBD'
        if isinstance(obj, self.classes['Template']):
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

    def get_oid_cnames(self, oids=None, cname=None):
        """
        For a list of oids, get a dict that maps the oids to their class names.

        Keyword Args:
            oids (list):  oids of objects

        Returns:
            dict:  mapping of oids to class names.
        """
        ident = self.classes['Identifiable'].__table__
        if oids:
            s = sql.select([ident]).where(ident.c.oid.in_(oids))
        elif cname:
            s = sql.select([ident]).where(sql.and_(
                                        ident.c.oid.in_(oids),
                                        ident.c.pgef_type == cname
                                        ))
        else:
            return {}
        return {row['oid'] : str(row['pgef_type'])
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
        # self.log.debug('* select(%s, **(%s))' % (cname, str(kw)))
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
        # self.log.debug('* search_exact(**(%s))' % (str(kw)))
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
                    # self.log.debug('  - bases of cname: {}'.format(
                                   # str(bases)))
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
                # self.log.debug('  - no cname kw, using: {}'.format(cname))
            # self.log.debug('  - ok_kw: {}'.format(str(ok_kw)))
            return list(self.db.query(self.classes[cname]).filter_by(**ok_kw))
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
        try:
            flows = self.search_exact(cname='Flow',
                                      flow_context=managed_object)
            return flows
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
        if isinstance(usage, self.classes['Acu']):
            assembly = usage.assembly
            component = usage.component
            other_objs = [usage.assembly]
            other_objs += [acu.component for acu in usage.assembly.components
                           if acu is not usage]
        elif isinstance(usage, self.classes['ProjectSystemUsage']):
            assembly = usage.project
            component = usage.system
            other_objs = [psu.system for psu in usage.project.systems
                          if psu is not usage]
        else:
            return []
        other_port_oids = [p.oid for p in reduce(lambda x, y: x+y,
                                        [o.ports for o in other_objs], [])]
        comp_port_oids = [p.oid for p in component.ports]
        Port = self.classes['Port']
        Flow = self.classes['Flow']
        flows_from = self.db.query(Flow).filter_by(
                        flow_context=assembly).join(Flow.start_port).filter(
                        Port.oid.in_(comp_port_oids)).join(
                        Flow.end_port).filter(Port.oid.in_(
                        other_port_oids)).all()
        flows_to = self.db.query(Flow).filter_by(
                        flow_context=assembly).join(Flow.start_port).filter(
                        Port.oid.in_(other_port_oids)).join(
                        Flow.end_port).filter(Port.oid.in_(
                        comp_port_oids)).all()
        return flows_from + flows_to

    def get_all_port_flows(self, port):
        """
        For a Port instance, get all flows defined to or from it (gazintas and
        gazoutas).

        Args:
            port (Port):  the specified Port
        """
        gazoutas = orb.search_exact(cname='Flow', start_port=port)
        gazintas = orb.search_exact(cname='Flow', end_port=port)
        return gazoutas + gazintas

    def get_objects_for_project(self, project):
        """
        Get all the objects relevant to the specified project, including
        [1] the project object, [2] objects for which the project is the
        `owner` or `user` (i.e., to which the project has a
        `ProjectSystemUsage` relationship), and [3] all related objects
        (assemblies and related components, etc.).

        Args:
            project (Project):  the specified project
        """
        self.log.debug('* get_objects_for_project({})'.format(
                                        getattr(project, 'id', '[None]')))
        if not project:
            self.log.debug('  - no project provided -- returning empty list.')
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
            # TODO: check for cycles
            # for system in systems:
                # cycles = check_for_cycles(system)
                # if cycles:
                    # self.log.info(f'  - {cycles}')
            for system in systems:
                # NOTE:  get_assembly is recursive, gets *all* sub-assemblies
                assemblies += get_assembly(system)
            if assemblies:
                self.log.debug('  - {} assemblies found'.format(
                               len(assemblies)))
            objs += assemblies
        else:
            self.log.debug('  - no ProjectSystemUsages found')
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
        reqts = self.search_exact(cname='Requirement', owner=project)
        if reqts:
            # include all Relations that are 'computable_form' of a reqt
            # and their ParameterRelations (rel.correlates_parameters)
            for reqt in reqts:
                if reqt.computable_form:
                    objs.append(reqt.computable_form)
                    prs = reqt.computable_form.correlates_parameters
                    if prs:
                        objs += prs
        # also get Mission, if any, and its components (Acus) -- Activities
        # within the project are already included, since their "owner" is the
        # project ...
        mission = self.select('Mission', owner=project)
        if mission:
            objs.append(mission)
            objs += mission.components  # Acus
        # TODO:  get the files too (fpath = rep_file.url)
        # use set() to eliminate dups
        res = [o for o in set(objs) if o]
        self.log.debug('  - returning {} object(s).'.format(len(res)))
        # if res:
            # for o in res:
                # self.log.debug('  - {}: {}'.format(
                               # o.__class__.__name__, o.id))
        return res

    def get_reqts_for_project(self, project):
        """
        Get all requirements whose owner is the specified project.

        Args:
            project (Project):  the specified project
        """
        self.log.debug('* get_reqts_for_project({})'.format(
                                        getattr(project, 'id', '[None]')))
        if not project:
            self.log.debug('  no project provided -- returning empty list.')
            return []
        reqts = self.search_exact(cname='Requirement', owner=project)
        self.log.debug('  - returning {} reqt(s).'.format(len(reqts)))
        return reqts

    def count_reqts_for_project(self, project):
        """
        Get a count of the requirements whose owner is the specified project.

        Args:
            project (Project):  the specified project
        """
        self.log.debug('* count_reqts_for_project({})'.format(
                                        getattr(project, 'id', '[None]')))
        if not project:
            self.log.debug('  - no project provided -- returning 0.')
            return 0
        # return self.db.query(self.classes['Requirement']).count()
        return self.db.query(self.classes['Requirement']).filter_by(
                                                        owner=project).count()

    def delete(self, objs):
        """
        Delete the specified objects from the local db.  Note that the orb does
        not check permissions here -- the assumption is that permissions were
        checked before orb.delete() was called and that every done here is
        authorized.  Also note that in deleting some types of objects, it may
        be required to delete many related objects, some of which may have been
        created by other users.

        Args:
            objs (Iterable of Identifiable or subtype): objects in the local db
        """
        self.log.debug('* delete() called ...')
        # TODO: make sure appropriate relationships in which these objects
        # are the parent or child are also deleted
        info = []
        recompute_required = False
        refresh_assemblies = []
        local_user = self.get(state.get('local_user_oid', 'me'))
        for obj in objs:
            if not obj:
                info.append('   None (ignored)')
                continue
            if isinstance(obj, self.classes['Project']):
                # delete all related role assignments:
                ras = self.search_exact(cname='RoleAssignment',
                                        role_assignment_context=obj)
                if ras:
                    txt = 'attempting to delete role assignments for'
                    info.append('   - {} "{}" ...'.format(txt, obj.id))
                    for ra in ras:
                        info.append('     id: {}, name: {})'.format(ra.id,
                                                                    ra.name))
                        self.db.delete(ra)
                        try:
                            self.db.commit()
                            info.append('     ... deleted.')
                        except:
                            self.db.rollback()
                            info.append('     ... delete failed, rolled back.')
                # delete any related system usages:
                psus = self.search_exact(cname='ProjectSystemUsage',
                                         project=obj)
                if psus:
                    txt = 'deleted system usages for'
                    info.append('   - {} "{}" ...'.format(txt, obj.id))
                    for psu in psus:
                        info.append('     id: {}, name: {}'.format(psu.id,
                                                                   psu.name))
                        self.db.delete(psu)
                        try:
                            self.db.commit()
                            info.append('     ... deleted.')
                        except:
                            self.db.rollback()
                            info.append('     ... delete failed, rolled back.')
                # delete any flows that have this as their 'flow_context':
                flows = self.search_exact(cname='Flow', flow_context=obj)
                if flows:
                    for flow in flows:
                        self.db.delete(flow)
                        try:
                            self.db.commit()
                            info.append('     ... deleted.')
                        except:
                            self.db.rollback()
                            info.append('     ... delete failed, rolled back.')
            if isinstance(obj, self.classes['Organization']):
                # if an Organization (which includes projects) owns any
                # objects, change their ownership to either its
                # 'parent_organization', or if none, to PGANA (if PGANA they
                # will be editable only by Global Admins until/unless their
                # ownership is reassigned to another Organization ... these
                # mods will be committed when the db session is committed
                if obj.owned_objects:
                    pgana = self.get('pgefobjects:PGANA')
                    new_owner = obj.parent_organization or pgana
                    for owned_obj in obj.owned_objects:
                        owned_obj.owner = new_owner
            if isinstance(obj, (self.classes['Acu'],
                                self.classes['ProjectSystemUsage'])):
                # delete any related flows to/from its component/system in
                # the context of its assembly/project
                flows = self.get_all_usage_flows(obj)
                for flow in flows:
                    info.append('   id: {}, name: {} (oid {})'.format(
                                                                    flow.id,
                                                                    flow.name,
                                                                    flow.oid))
                    self.db.delete(flow)
                    try:
                        self.db.commit()
                        info.append('     ... deleted.')
                    except:
                        self.db.rollback()
                        info.append('     ... delete failed, rolled back.')
            if isinstance(obj, self.classes['Product']):
                # for Products, first delete related Flows, Ports, Acus, and
                # ProjectSystemUsages
                # NOTE: for flows, only need to worry about internal flows --
                # if the deletion is allowed, all of the Product's usages in
                # assemblies or projects have been already deleted, so there
                # are no external flows
                flows = self.get_internal_flows_of(obj)
                if flows:
                    for flow in flows:
                        info.append('   id: {}, name: {} (oid {})'.format(
                                                                    flow.id,
                                                                    flow.name,
                                                                    flow.oid))
                        self.db.delete(flow)
                        try:
                            self.db.commit()
                            info.append('     ... deleted.')
                        except:
                            self.db.rollback()
                            info.append('     ... delete failed, rolled back.')
                ports = obj.ports
                if ports:
                    for port in ports:
                        info.append('   id: {}, name: {} (oid {})'.format(
                                                                    port.id,
                                                                    port.name,
                                                                    port.oid))
                        self.db.delete(port)
                        try:
                            self.db.commit()
                            info.append('     ... deleted.')
                        except:
                            self.db.rollback()
                            info.append('     ... delete failed, rolled back.')
                psus = obj.projects_using_system
                for psu in psus:
                    info.append('   id: {}, name: {} (oid {})'.format(psu.id,
                                                                   psu.name,
                                                                   psu.oid))
                    self.db.delete(psu)
                    try:
                        self.db.commit()
                        info.append('     ... deleted.')
                    except:
                        self.db.rollback()
                        info.append('     ... delete failed, rolled back.')
                child_acus = obj.components
                if child_acus:
                    for acu in child_acus:
                        info.append('   id: {}, name: {} (oid {})'.format(
                                                                    acu.id,
                                                                    acu.name,
                                                                    acu.oid))
                        self.db.delete(acu)
                        try:
                            self.db.commit()
                            info.append('     ... deleted.')
                        except:
                            self.db.rollback()
                            info.append('     ... delete failed, rolled back.')
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
                        try:
                            self.db.commit()
                            info.append('     ... deleted.')
                        except:
                            self.db.rollback()
                            info.append('     ... delete failed, rolled back.')
                        if assembly.oid in componentz:
                            refresh_assemblies.append(assembly)
            if isinstance(obj, self.classes['Port']):
                # for Ports, first delete all related Flows, both outgoing and
                # incoming (in which it is the start or end)
                skip_port = False
                flows = self.get_all_port_flows(obj)
                if flows:
                    for flow in flows:
                        info.append('   id: {}, name: {} (oid {})'.format(
                                                                    flow.id,
                                                                    flow.name,
                                                                    flow.oid))
                        try:
                            self.db.delete(flow)
                            self.db.commit()
                            info.append('     ... deleted.')
                        except:
                            self.db.rollback()
                            info.append('     ... flow delete failed,')
                            info.append('     port will not be deleted.')
                            skip_port = True
                if skip_port:
                    continue
            if isinstance(obj, self.classes['Requirement']):
                # delete any related Relation and ParameterRelation objects
                rel = obj.computable_form
                if rel:
                    prs = rel.correlates_parameters
                    if prs:
                        for pr in prs:
                            self.db.delete(pr)
                            try:
                                self.db.commit()
                            except:
                                self.db.rollback()
                                info.append('     ... ParameterRelation')
                                info.append('         delete failed,')
                                info.append('         rolled back.')
                    obj.computable_form = None
                    self.db.delete(rel)
                    try:
                        self.db.commit()
                        info.append('     ... deleted.')
                    except:
                        self.db.rollback()
                        info.append('     ... Relation')
                        info.append('         delete failed, rolled back.')
                    # computable_form -> require recompute
                    recompute_required = True
                # if its oid is in req_allocz, remove it
                if obj.oid in req_allocz:
                    del req_allocz[obj.oid]
            if obj.oid in parameterz:
                # NOTE: VERY IMPORTANT! remove oid from parameterz
                del parameterz[obj.oid]
                recompute_required = True
            elif isinstance(obj, self.classes['Acu']):
                if getattr(obj.assembly, 'oid') in componentz:
                    refresh_assemblies.append(obj.assembly)
                recompute_required = True
            creator = getattr(obj, 'creator', None)
            if creator == local_user:
                # if local_user created obj, add it to trash
                # TODO:  use trash to enable undo of delete ...
                trash[obj.oid] = serialize(self, [obj])
            info.append('   obj id: {}, name: {} (oid "{}")'.format(
                                        getattr(obj, 'id', 'no id'),
                                        getattr(obj, 'name', 'no name'),
                                        obj.oid))
            info.append('   attempting to delete ...')
            self.db.delete(obj)
            try:
                self.db.commit()
                info.append('     ... object deleted.')
            except:
                self.db.rollback()
                info.append('     ... delete failed, rolled back.')
        self.log.debug(' - objs deleted:')
        for text in info:
            self.log.debug(text)
        if refresh_assemblies:
            for assembly in refresh_assemblies:
                refresh_componentz(assembly)
        if recompute_required:
            self.recompute_parmz()

    def is_versioned(self, obj):
        """
        Determine if a object is being versioned: for now, being an instance of
        "Product" means it is versioned (i.e., it has "version" and "iteration"
        attributes).  This function permits the criteria for deciding whether
        an object is versioned to change in the future.
        """
        return isinstance(obj, self.classes['Product'])

# A node has only one instance of UberORB, the 'orb', which is intended to be
# imported by all application components.
orb = UberORB()

