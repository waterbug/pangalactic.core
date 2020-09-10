# -*- coding: utf-8 -*-
"""
Pan Galactic Entity and DataMatrix classes.
"""
import json, os
from copy            import deepcopy
from collections     import UserList
from itertools       import chain
from uuid            import uuid4

# pangalactic
from pangalactic.core                 import config
from pangalactic.core.parametrics     import (data_elementz, de_defz,
                                              parameterz, parm_defz,
                                              get_dval, get_pval,
                                              set_dval, set_pval,
                                              round_to,
                                              serialize_des,
                                              serialize_parms)
from pangalactic.core.utils.datetimes import dtstamp

# dispatcher (Louie)
from louie import dispatcher


class logger:
    def info(self, s):
        dispatcher.send(signal='log info msg', msg=s)
    def debug(self, s):
        dispatcher.send(signal='log debug msg', msg=s)

log = logger()


# -----------------------------------------------------------------------
# ENTITY-RELATED CACHES
# -----------------------------------------------------------------------
# entz:        persistent** cache of entity metadata
#              ** persisted in the file 'ents.json' in the
#              application home directory -- see the functions
#              `save_entz` and `load_entz`
# format:  {oid : {'owner': 'x', 'creator': 'y', 'modifier': 'z', ...},
#           ...}
# ... where required data elements for the entity are:
# -------------------------------------------------------
# owner, creator, modifier, create_datetime, mod_datetime
# -------------------------------------------------------
entz = {}

# ent_histz:  persistent** cache of previous versions of entities,
#             saved as named tuples ...
#              ** persisted in the file 'ent_hists.json' in the
#              application home directory -- see
#              `save_ent_histz` and `load_ent_histz`
# format:  {entity['oid'] : [list of previous versions of entity]}
ent_histz = {}

def load_entz(dir_path):
    """
    Load the `entz` cache from json file.
    """
    log.debug('* load_entz() ...')
    fpath = os.path.join(dir_path, 'ents.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            data = f.read()
            if data:
                entz.update(json.loads(data))
        log.debug('  - entz cache loaded.')
    else:
        log.debug('  - "ents.json" was not found.')
        pass

def save_entz(dir_path):
    """
    Save `entz` dict to json file.
    """
    log.debug('* save_entz() ...')
    try:
        fpath = os.path.join(dir_path, 'ents.json')
        with open(fpath, 'w') as f:
            if entz:
                f.write(json.dumps(entz, separators=(',', ':'),
                                   indent=4, sort_keys=True))
            else:
                log.debug('  ... entz was empty.')
                pass
        log.debug('  ... ents.json file written.')
    except:
        log.debug('  ... exception encountered.')
        pass

def load_ent_histz(dir_path):
    """
    Load the `ent_histz` cache from json file.
    """
    log.debug('* load_ent_histz() ...')
    fpath = os.path.join(dir_path, 'ent_hists.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            data = f.read()
            if data:
                ent_histz.update(json.loads(data))
        log.debug('  - ent_histz cache loaded.')
    else:
        log.debug('  - "ent_hists.json" was not found.')
        pass

def save_ent_histz(dir_path):
    """
    Save `ent_histz` dict to json file.
    """
    log.debug('* save_ent_histz() ...')
    try:
        fpath = os.path.join(dir_path, 'ent_hists.json')
        with open(fpath, 'w') as f:
            if ent_histz:
                f.write(json.dumps(ent_histz, separators=(',', ':'),
                                   indent=4, sort_keys=True))
            else:
                log.debug('  ... ent_histz was empty.')
                pass
        log.debug('  ... ent_hists.json file written.')
    except:
        log.debug('  ... unable to write to path "{}".'.format(dir_path))
        pass


class Entity(dict):
    """
    An interface to access a set of Data Elements and Parameters in the
    `data_elementz` and `parameterz` caches, respectively.  An Entity can
    represent a component in an assembly, a model in a collection of models, a
    line item in a parts list, etc.

    The concept behind Entity is similar to "record" as in database records,
    "row" as in tables or matrices, anonymous Class instances in an ontology,
    or "Item" in a PyQt QAbstractItemModel.  Its metadata (owner, creator,
    modifier, create_datetime, and mod_datetime) are maintained in the 'entz'
    cache.  Attributes other than its 'oid' and metadata are accessed via the
    `data_elementz` and `parameterz` caches; therefore, an Entity does not
    store any data locally other than its 'oid', which is used as a key when
    interfacing to the caches.

    Note that no serializer or deserializer is needed for Entity because all of
    its data are maintained in the entz, data_elementz, and parameterz caches,
    which are all persisted -- all known Entities can be recreated by calling
    Entity(oid=oid) with each of the oids in the 'entz' cache.

    Attributes:
        oid (str):  a unique identifier
    """
    metadata = ['owner', 'creator', 'modifier', 'create_datetime',
                'mod_datetime', 'assembly_level', 'parent_oid', 'system_oid',
                'system_name']

    def __init__(self, *args, oid=None, owner=None, creator=None,
                 modifier=None, create_datetime=None, mod_datetime=None,
                 assembly_level=1, parent_oid=None, system_oid=None,
                 system_name=None, **kw):
        """
        Initialize.

        Args:
            args (tuple):  optional positional argument (0 or 1).  If a
                positional arg is present, it must be either a mapping or an
                iterable in which each element is an iterable containing 2
                elements (e.g. a list of 2-tuples).

        Keyword Args:
            oid (str):  a unique identifier
            owner (str):  oid of an Organization
            creator (str):  oid of the entity's creator
            modifier (str):  oid of the entity's last modifier
            create_datetime (str):  iso-format string of creation datetime
            mod_datetime (str):  iso-format string of last mod datetime
            parent_oid (str):  oid of the entity's "parent" entity within the
                context of its DataMatrix
            system_oid (str):  [optional] oid of a system (Project or Product)
                to which the entity is mapped
            system_name (str):  derived from the library product name and
                reference_designator within its assembly
            kw (dict):  keyword args, passed to superclass (dict)
                initialization
        """
        log.debug('* Entity()')
        super().__init__(*args)
        # TODO:  check if oid is that of an object
        if not oid:
            oid = str(uuid4())
        self.oid = oid
        d = locals()
        meta = {a: d.get(a) for a in self.metadata}
        if self.oid in entz:
            log.debug(f'  entity oid "{oid}" was in "entz", using ...')
        else:
            log.debug(f'  entity oid "{oid}" was NOT in "entz", creating ...')
            dt = str(dtstamp())
            entz[self.oid] = dict(
                creator=meta.get('creator') or 'pgefobjects:admin',
                modifier=meta.get('modifier') or 'pgefobjects:admin',
                create_datetime=meta.get('create_datetime') or dt,
                mod_datetime=meta.get('mod_datetime') or dt,
                owner=meta.get('owner') or 'pgefobjects:PGANA',
                assembly_level=meta.get('assembly_level') or 1,
                parent_oid=meta.get('parent_oid'),
                system_oid=meta.get('system_oid'),
                system_name=meta.get('system_name'))

    def __getitem__(self, k):
        """
        Get the value of an entity key, returning [0] for a metadata key, a
        metadata value, [1] for a data element, a simple value, [2] for a
        parameter, a value in base units, [3] if none of those are present,
        None or whatever is provided in the 'default' arg.
        """
        # log.debug(f'* Entity.__getitem__({k})')
        # print(f'* Entity.__getitem__({k})')
        if k == 'oid':
            return self.oid
        elif k in self.metadata:
            # print('  - got metadata.')
            return entz[self.oid].get(k)
        elif k in parm_defz:
            # k is a parameter
            # print('  - got parameter.')
            return get_pval(self.oid, k)
        else:
            # k is a data element
            # print('  - got data element.')
            return get_dval(self.oid, k)

    def get(self, k, *default):
        """
        Get the value of an entity key, returning [0] for a metadata key, a
        metadata value, [1] for a data element, a simple value, [2] for a
        parameter, a value in base units, [3] if none of those are present,
        None or whatever is provided in the 'default' arg.
        """
        if k == 'oid':
            return self.oid
        elif k in self.metadata:
            # log.debug('  - got metadata.')
            # print('  - got metadata.')
            return entz[self.oid].get(k)
        elif k in parm_defz:
            # log.debug('  - got parameter.')
            # print('  - got parameter.')
            return get_pval(self.oid, k)
        elif k in de_defz:
            # log.debug('  - got data element.')
            # print('  - got data element.')
            return get_dval(self.oid, k)
        elif default:
            # log.debug('  - got default: {}.'.format(str(default)))
            # print('  - got default: {}.'.format(str(default)))
            return default[0]
        else:
            # log.debug('  - got nothin.')
            # print('  - got nothin.')
            return get_dval(self.oid, k)

    def __setitem__(self, k, v):
        """
        Set the value of an entity key, which may be a metadata key, a data
        element, or a parameter.  Note that this will add the key if it is not
        already present.
        """
        # log.debug(f'* Entity.__setitem__({k}, {v})')
        # print(f'* Entity.__setitem__({k}, {v})')
        # NOTE: for 'oid', it is both an object attribute and a dict key
        if k == 'oid':
            object.__setattr__(self, 'oid', v)
        elif k in self.metadata:
            if not self.oid in entz:
                entz[self.oid] = {}
            entz[self.oid][k] = v
        else:
            previous_self = deepcopy(self)
            if k in parm_defz:
                success = set_pval(self.oid, k, v)
            else:
                success = set_dval(self.oid, k, v)
            if success:
                # add previous self to history ...
                if not self.oid in ent_histz:
                    ent_histz[self.oid] = [deepcopy(previous_self)]
                else:
                    ent_histz[self.oid].append(deepcopy(previous_self))

    def __delitem__(self, k):
        if k in parameterz.get(self.oid, {}):
            del parameterz[self.oid][k]
        elif k in data_elementz.get(self.oid, {}):
            del data_elementz[self.oid][k]

    def __iter__(self):
        return chain(parameterz.get(self.oid, {}),
                     data_elementz.get(self.oid, {}))

    def __len__(self):
        return (len(parameterz.get(self.oid, {}))
                + len(data_elementz.get(self.oid, {})))

    def __str__(self):
        parms = 'PARAMETERS: '
        if parameterz.get(self.oid, {}).items():
            parms += ', '.join(['{}: {}'.format(k, get_pval(self.oid, k))
                               for k in parameterz.get(self.oid, {})])
        else:
            parms += 'None'
        des = 'DATA ELEMENTS: '
        if data_elementz.get(self.oid, {}).items():
            des += ', '.join(['{}: {}'.format(k, get_dval(self.oid, k))
                             for k in data_elementz.get(self.oid, {})])
        else:
            des += 'None'
        return '{<Entity "' + self.oid + '">: ' + ', '.join([parms, des]) + '}'

    def undo(self):
        if self.oid in ent_histz and ent_histz[self.oid]:
            self = ent_histz[self.oid].pop()

    def serialize_meta(self):
        """
        Serialize only the metadata for the Entity.  (Used when saving the
        'entz' cache.)
        """
        d = dict(oid=self.oid, owner=self.get('owner', ''),
                 creator=self.get('creator', ''),
                 modifier=self.get('modifier', ''),
                 create_datetime=self.get('create_datetime', ''),
                 mod_datetime=self.get('mod_datetime', ''))
        return d

    def serialize(self):
        """
        Serialize the complete "contents" of the Entity.  (Used when exchanging
        complete entities, such as in messages between the client and server.)
        """
        d = self.serialize_meta()
        d.update(serialize_des(self.oid))
        d.update(serialize_parms(self.oid))
        return d


# -----------------------------------------------------------------------
# DATAMATRIX-RELATED CACHES #############################################
# -----------------------------------------------------------------------

# dmz:         persistent** cache of DataMatrix instances
#              ** persisted in the file 'dms.json' in the
#              application home directory
# format:  {oid : DataMatrix},
#           ...}
dmz = {}

# schemaz:     persistent** cache of schemas (column views)
#              ** persisted in the file 'schemas.json' in the
#              application home directory
# format:  {name1 : [colname1, colname2, ...],
#           name2 : [colname3, colname4, ...],
#           ...}
# -------------------------------------------------------
schemaz = {'generic': ['system_name', 'assembly_level',
                       'additional_information']}

def load_schemaz(dir_path):
    """
    Load the `schemaz` cache from json file.

    Args:
        schemaz_path (str):  location of file to read
    """
    log.debug('* load_schemaz() ...')
    fpath = os.path.join(dir_path, 'schemas.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            data = f.read()
            if data:
                schemaz.update(json.loads(data))
        nsch = len(schemaz)
        log.debug(f'  - {nsch} schemas loaded into schemaz cache.')
    else:
        log.debug('  - "schemas.json" was not found.')
        pass

def save_schemaz(dir_path):
    """
    Save `schemaz` dict to json file.

    Args:
        schemaz_path (str):  location of file to write
    """
    log.debug('* save_schemaz() ...')
    nsch = len(schemaz)
    fpath = os.path.join(dir_path, 'schemas.json')
    with open(fpath, 'w') as f:
        f.write(json.dumps(schemaz, separators=(',', ':'),
                           indent=4, sort_keys=True))
    log.debug(f'  ... {nsch} schema(s) saved to schemas.json.')

def load_dmz(dir_path):
    """
    Load the `dmz` cache from json file.  (Restores all DataMatrix
    instances.)

    Args:
        dmz_path (str):  location of file to read
    """
    log.debug('* load_dmz() ...')
    fpath = os.path.join(dir_path, 'dms.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            ser_dms = json.loads(f.read()) or {}
        try:
            deser_dms = {oid: DataMatrix([
                              Entity(oid=oid) for oid in sdm['ents']],
                              project_id=sdm['project_id'],
                              name=sdm['name'],
                              creator=sdm['creator'],
                              modifier=sdm['modifier'],
                              create_datetime=sdm['create_datetime'],
                              mod_datetime=sdm['mod_datetime'])
                         for oid, sdm in ser_dms.items()}
        except:
            log.debug('  - Parsing of dms.json failed.')
            return
        dmz.update(deser_dms)
        ndmz = len(dmz)
        log.debug(f'  - {ndmz} DataMatrix instance(s) loaded into dmz cache.')
    else:
        log.debug('  - "dms.json" was not found.')
        pass

def save_dmz(dir_path):
    """
    Save `dmz` dict (all DataMatrix instances) to json file.

    Args:
        dmz_path (str):  location of file to write
    """
    log.debug('* save_dmz() ...')
    ser_dms = {oid: dict(project_id=dm.project_id,
                         name=dm.name,
                         ents=[e.oid for e in dm],
                         creator=dm.creator,
                         modifier=dm.modifier,
                         create_datetime=dm.create_datetime,
                         mod_datetime=dm.mod_datetime)
               for oid, dm in dmz.items()}
    ndms = len(ser_dms)
    fpath = os.path.join(dir_path, 'dms.json')
    with open(fpath, 'w') as f:
        f.write(json.dumps(ser_dms, separators=(',', ':'),
                           indent=4, sort_keys=True))
    log.debug(f'  ... {ndms} DataMatrix instance(s) saved to dms.json.')


class DataMatrix(UserList):
    """
    A UserList subclass that contains instances of Entity as its items.  The
    DataMatrix has an attribute "schema" that is a list of identifiers that
    reference DataElementDefinitions or ParameterDefinitions (which are cached
    in the "de_defz" dict and "parm_defz" dict, respectively).

    A DataMatrix's list ('data') contents and its metadata are cached in the
    `dmz` cache in which its key is its unique identifier ('oid'), which is
    composed from the 'id' of its owner Project and its `name` (which is
    the key used to look up its schema in the `schemaz' cache).

    When a DataMatrix is instantiated, its initialization will first check the
    `dmz` to see if it already exists; if not, it will create a new metadata
    record for itself there.

    Attributes:
        data (iterable):  an iterable of entities
        name (str): name (which may or may not exist in the 'schemaz' cache)
        project_id (str): id a project (owner of the DataMatrix)
        schema (list): list of data element ids and parameter ids
    """
    def __init__(self, *data, project_id='', name=None,
                 schema=None, creator=None, modifier=None,
                 create_datetime=None, mod_datetime=None):
        """
        Initialize.

        Args:
            data (iterable):  (optional) an iterable of entities

        Keyword Args:
            project_id (str): id of a project (owner of the DataMatrix)
            name (str): name (which may or may not exist in 'schemaz')
            schema (list): list of data element ids and parameter ids
            creator (str):  oid of the entity's creator
            modifier (str):  oid of the entity's last modifier
            create_datetime (str):  iso-format string of creation datetime
            mod_datetime (str):  iso-format string of last mod datetime
        """
        super().__init__(*data)
        sig = 'project_id="{}", name="{}"'.format(
                                        project_id, name or '[None]')
        log.debug('* DataMatrix({})'.format(sig))
        # NOTE:  self.project_id and self.name MUST be set before accessing
        # self.oid, which is computed from them ...
        self.project_id = project_id or 'SANDBOX'
        log.debug('  - project id: {}'.format(project_id))
        self.name = name or 'custom'
        log.debug('  - name set to: "{}"'.format(name))
        dt = str(dtstamp())
        self.creator = creator or 'pgefobjects:admin'
        self.modifier = modifier or 'pgefobjects:admin'
        self.create_datetime = create_datetime or dt
        self.mod_datetime = mod_datetime or dt
        log.debug('    checking for schema with that name ...')
        if schema:
            # if a schema is passed in, use it and register it in schemaz ...
            self.schema = schema
            schemaz[self.oid] = schema
        elif schemaz.get(name):
            # else check 'schemaz' for a schema by the name
            self.schema = schemaz[name]
        elif config.get('schemas', {}).get(name):
            # else check config["schemas"] for that name ...
            self.schema = config['schemas'][name]
        else:
            # if schema lookup in 'schemaz' and 'prefs["schemas"]' is
            # unsuccessful, use 'generic' schema of last resort ...
            self.name = 'generic'
            self.schema = schemaz.get(self.name) or ['system_name']
        # look for pre-defined column labels, or use names/ids as defaults
        if self.schema:
            self.column_labels = [
                (de_defz.get(col_id, {}).get('label', '')
                 or parm_defz.get(col_id, {}).get('label', '')
                 or de_defz.get(col_id, {}).get('name', '')
                 or parm_defz.get(col_id, {}).get('name', '')
                 or col_id)
                for col_id in self.schema]
        self.cache_meta()

    def __str__(self):
        s = 'DataMatrix: '
        if self:
            s += '['
            for e in self:
                s += '{}, '.format(e.oid)
            s += ']'
        else:
            s += '[]'
        return s

    def cache_meta(self):
        """
        Add myself to the 'dmz' cache -- this method should be overridden in
        subclasses to use the cache relevant to the subclass.
        """
        dmz[self.oid] = self

    @property
    def oid(self):
        return '-'.join([self.project_id, self.name])

    def row(self, i):
        """
        Return the i-th entity from the dm.
        """
        if i >= len(self):
            return
        return self[i]

    def append_new_row(self, child=False):
        """
        Appends an "empty" Entity with a new oid, using 'child' flag to
        indicate what the level should be.
        """
        e = Entity()
        self.append(e)
        return e

    def insert_new_row(self, i, child_of=False):
        """
        Inserts an empty Entity with a new oid, in the ith position, using
        'child' flag to compute the level.  To support
        GridTreeItem.insertChildren(), use child=True.

        Keyword Args:
            child_of (Entity):  the parent Entity (or None if same level as
                preceding row)
        """
        e = Entity()
        self.insert(i, e)
        return e

    def remove_row(self, i):
        """
        Remove the ith row.
        """
        if i >= len(self):
            return False
        self.pop(i)
        return True

    def remove_row_by_oid(self, oid):
        """
        Remove the row with the specified oid.
        """
        oids = [e.oid for e in self]
        if oid in oids:
            i = self.index(oid)
        else:
            return False
        self.pop(i)
        return True

    def recompute_mel(self, context):
        """
        Compute parameters / data elements for a MEL (Master Equipment List) in
        a 'context' (Project or Product).

        Args:
            context (Project or Product):  the project or system to which the
                MEL parameters pertain
        """
        log.debug(f'* recompute_mel({context.id})')
        row = 0
        if context.__class__.__name__ == 'Project':
            # context is Project, so may include several systems
            project = context
            for psu in project.systems:
                name = f'{psu.system_role} [{psu.system.id}]'
                end_row = self.compute_mel_parms(1, row, name, psu.system)
                row += end_row
        elif context.__class__.__name__ == 'HardwareProduct':
            # context is Product -> a single system MEL
            name = f'{context.name} [{context.id}]'
            self.compute_mel_parms(1, 0, name, context)
        else:
            # not a Project or HardwareProduct
            pass

    def compute_mel_parms(self, level, row, name, component, qty=1,
                          parent_oid=None):
        """
        Compute parameter and data element values for the components in a
        Master Equipment List (MEL) based on their positions in the system
        assembly.
        """
        log.debug(f'* compute_mel_parms({level}, {row}, {name}, qty={qty},')
        log.debug(f'                    parent_oid={parent_oid}')
        oid = component.oid
        if (row < len(self) and self[row].get('system_oid') == oid
            and self[row].get('parent_oid') == parent_oid
            and self[row].get('system_name') == name):
            # this row is an entity that corresponds to its index
            entity = self[row]
        else:
            # create a new entity (with an auto-generated oid)
            entity = Entity(parent_oid=parent_oid,
                            assembly_level=level,
                            system_oid=component.oid, 
                            system_name=name, 
                            owner=component.owner.oid,
                            creator=component.creator.oid,
                            create_datetime=str(component.create_datetime),
                            modifier=component.modifier.oid,
                            mod_datetime=str(component.mod_datetime))
        if row < len(self):
            self[row] = entity
        else:
            self.append(entity)
        # map data element values to parameter values where appropriate ...
        entity['m_unit'] = get_pval(oid, 'm[CBE]') or 0
        log.debug('  entity["m_unit"] = {}'.format(entity['m_unit']))
        entity['m_cbe'] = qty * entity['m_unit']
        entity['m_ctgcy'] = round_to(100 * get_pval(oid, 'm[Ctgcy]'), n=3) or 0
        entity['m_mev'] = qty * (get_pval(oid, 'm[MEV]') or 0)
        entity['nom_p_unit_cbe'] = get_pval(oid, 'P[CBE]') or 0
        entity['nom_p_cbe'] = qty * (entity['nom_p_unit_cbe'] or 0)
        entity['nom_p_ctgcy'] = round_to(100 * get_pval(oid, 'P[Ctgcy]')) or 0
        entity['nom_p_mev'] = qty * (get_pval(oid, 'P[MEV]') or 0)
        # columns in spreadsheet MEL:
        #   0: Level
        #   1: Name
        #   2: Unit MASS CBE
        #   9: Mass CBE
        #  10: Mass Contingency (%)
        #  11: Mass MEV
        #  12: Unit Power CBE
        #  13: Power CBE
        #  14: Power Contingency (%)
        #  15: Power MEV
        log.debug(f' + writing {name} in row {row}')
        if component.components:
            next_level = level + 1
            for acu in component.components:
                if acu.component.oid == 'pgefobjects:TBD':
                    continue
                row += 1
                component = acu.component
                qty = acu.quantity or 1
                name = f'{acu.reference_designator} [{component.name}]'
                row = self.compute_mel_parms(next_level, row, name, component,
                                             qty=qty, parent_oid=entity.oid)
        return row


