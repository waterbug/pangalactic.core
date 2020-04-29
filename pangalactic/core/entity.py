# -*- coding: utf-8 -*-
"""
Pan Galactic Entity and DataMatrix classes.
"""
import json, os
from copy            import deepcopy
from collections     import UserList
from collections.abc import MutableMapping
from itertools       import chain
from uuid            import uuid4

# pangalactic
from pangalactic.core.parametrics     import (de_defz, parm_defz,
                                              data_elementz,
                                              parameterz,
                                              get_dval, get_pval,
                                              set_dval, set_pval,
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
#              application home directory -- see the orb functions
#              `save_entz` and `load_entz`
# format:  {oid : {'owner': 'x', 'creator': 'y', 'modifier': 'z', ...},
#           ...}
# ... where required data elements for the entity are:
# -------------------------------------------------------
# owner, creator, modifier, create_datetime, mod_datetime
# -------------------------------------------------------
entz = {}

# EXPERIMENTAL:  support for searching of entities by data element and
#                parameter values (in base units)
# ent_lookupz    runtime cache for reverse lookup of entities
#              maps tuples of values to entity oids
# format:  {de_values, p_values) : oid,
#           ...}
ent_lookupz = {}

# ent_histz:  persistent** cache of previous versions of entities,
#             saved as named tuples ...
#              ** persisted in the file 'ent_hists.json' in the
#              application home directory -- see
#              `save_ent_histz` and `load_ent_histz`
# format:  {entity['oid'] : [list of previous versions of entity]}
ent_histz = {}

def load_entz(json_path):
    """
    Load the `entz` dict from json file.
    """
    log.debug('* load_entz() ...')
    if os.path.exists(json_path):
        with open(json_path) as f:
            data = f.read()
            if data:
                entz.update(json.loads(data))
        log.debug('  - entz cache loaded.')
    else:
        log.debug('  - "ents.json" was not found.')

def save_entz(json_path):
    """
    Save `entz` dict to json file.
    """
    log.debug('* save_entz() ...')
    try:
        with open(json_path, 'w') as f:
            if entz:
                f.write(json.dumps(entz, separators=(',', ':'),
                                   indent=4, sort_keys=True))
            else:
                log.debug('  ... entz was empty.')
        log.debug('  ... ents.json file written.')
    except:
        log.debug('  ... exception encountered.')

# ent_lookupz  runtime cache for reverse lookup of Entity instances
#              maps tuples of values to entity oids
#              (EXPERIMENTAL) support for searching of Entity instance data by
#              data element and parameter values (in base units)
# format:  {(oid, de_value1, ..., p_value1, ...) : oid,
#           ...}
#          where 'oid' is inserted for uniqueness.
ent_lookupz = {}

# ent_histz:  persistent** cache of previous versions of Entity states,
#             saved as named tuples ...
#              ** persisted in the file 'ent_hists.json' in the
#              application home directory
# format:  {entity['oid'] : [list of serialized previous versions of entity]}
ent_histz = {}

def load_ent_histz(json_path):
    """
    Load the `ent_histz` dict from json file.
    """
    log.debug('* load_ent_histz() ...')
    if os.path.exists(json_path):
        with open(json_path) as f:
            data = f.read()
            if data:
                ent_histz.update(json.loads(data))
        log.debug('  - ent_histz cache loaded.')
    else:
        log.debug('  - "ent_hists.json" was not found.')
        pass

def save_ent_histz(json_path):
    """
    Save `ent_histz` dict to json file.
    """
    log.debug('* save_ent_histz() ...')
    try:
        with open(json_path, 'w') as f:
            if ent_histz:
                f.write(json.dumps(ent_histz, separators=(',', ':'),
                                   indent=4, sort_keys=True))
            else:
                log.debug('  ... ent_histz was empty.')
        log.debug('  ... ent_hists.json file written.')
    except:
        log.debug('  ... unable to write to path "{}".'.format(
                                                        json_path))
        pass


class Entity(MutableMapping):
    """
    An interface to access a set of Data Elements and Parameters in the
    `data_elementz` and `parameterz` caches, respectively.  The concept behind
    Entity is essentially synonymous with "record" as in database records,
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
        owner (str):  oid of an Organization
        creator (str):  oid of the entity's creator
        modifier (str):  oid of the entity's last modifier
        create_datetime (str):  iso-format string of creation datetime
        mod_datetime (str):  iso-format string of last mod datetime
    """
    def __init__(self, *args, oid=None, owner=None, creator=None,
                 modifier=None, create_datetime=None, mod_datetime=None,
                 **kw):
        """
        Initialize.

        Args:
            args (tuple):  optional positional arguments (0 or 1).  If a
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
            kw (dict):  keyword args, passed to superclass (dict)
                initialization
        """
        # log.debug('* Entity()')
        super(Entity, self).__init__(*args, **kw)
        if not oid:
            oid = str(uuid4())
        self.oid = oid
        # TODO:  also check if oid is that of an object
        if oid not in entz:
            dt = str(dtstamp())
            creator = creator or 'pgefobjects:admin'
            modifier = modifier or 'pgefobjects:admin'
            create_datetime = create_datetime or dt
            mod_datetime = mod_datetime or dt
            owner = owner or 'pgefobjects:PGANA'
            entz[oid] = dict(oid=oid, owner=owner, creator=creator,
                             modifier=modifier, create_datetime=create_datetime,
                             mod_datetime=mod_datetime)

    def __getitem__(self, k):
        """
        Get the value of an entity key, returning [0] for a metadata key, a
        metadata value, [1] for a data element, a simple value, [2] for a
        parameter, a value in base units, [3] if none of those are present,
        None or whatever is provided in the 'default' arg.
        """
        # log.debug('* __getitem__()')
        if k in ('oid', 'owner', 'creator', 'modifier', 'create_datetime',
                 'mod_datetime'):
            # metadata
            return entz[self.oid].get(k)
        elif k in parm_defz:
            return get_pval(self.oid, k)
        else:
            return get_dval(self.oid, k)

    def get(self, k, *default):
        """
        Get the value of an entity key, returning [0] for a metadata key, a
        metadata value, [1] for a data element, a simple value, [2] for a
        parameter, a value in base units, [3] if none of those are present,
        None or whatever is provided in the 'default' arg.
        """
        # log.debug('* get()')
        if k in ('oid', 'owner', 'creator', 'modifier', 'create_datetime',
                 'mod_datetime'):
            # metadata
            # log.debug('  - got metadata.')
            return entz[self.oid].get(k)
        elif k in parm_defz:
            # log.debug('  - got parameter.')
            return get_pval(self.oid, k)
        elif k in de_defz:
            # log.debug('  - got data element.')
            return get_dval(self.oid, k)
        elif default:
            # log.debug('  - got default: {}.'.format(str(default)))
            return default[0]
        else:
            # log.debug('  - got nothin.')
            return get_dval(self.oid, k)

    def __setitem__(self, k, v):
        """
        Set the value of an entity key, which may be a metadata key, a data
        element, or a parameter.  Note that this will add the key if it is not
        already present.
        """
        # log.debug('* __getitem__()')
        if k == 'oid':
            object.__setattr__(self, 'oid', v)
        elif k in ('oid', 'owner', 'creator', 'modifier',
                          'create_datetime', 'mod_datetime'):
            # metadata
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
        return len(parameterz.get(self.oid, {})) + len(data_elementz.get(
                                                            self.oid, {}))

    def __str__(self):
        parms = None
        if parameterz.get(self.oid, {}).items():
            parms = ', '.join(['{}: {}'.format(k, get_pval(self.oid, k))
                               for k in parameterz.get(self.oid, {})])
        des = None
        if data_elementz.get(self.oid, {}).items():
            des = ', '.join(['{}: {}'.format(k, get_dval(self.oid, k))
                             for k in data_elementz.get(self.oid, {})])
        if parms and des:
            return '{' + ', '.join([parms, des]) + '}'
        elif parms:
            return '{' + parms + '}'
        elif des:
            return '{' + des + '}'
        else:
            return '{}'

    def undo(self):
        if self.oid in ent_histz and ent_histz[self.oid]:
            self = ent_histz[self.oid].pop()

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v

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
# format:  {schema_name : [colname1, colname2, ...],
#           ...}
# -------------------------------------------------------
schemaz = {'generic': ['system_name', 'assembly_level',
                       'additional_information']}

def load_schemaz(json_path):
    """
    Load the `schemaz` dict from json file.  (Restores all DataMatrix
    instances.)

    Args:
        schemaz_path (str):  location of file to read
    """
    log.debug('* load_schemaz() ...')
    if os.path.exists(json_path):
        with open(json_path) as f:
            data = f.read()
            if data:
                schemaz.update(json.loads(data))
        nsch = len(schemaz)
        log.debug(f'  - {nsch} schemas loaded into schemaz cache.')
    else:
        log.debug('  - "schemas.json" was not found.')
        pass

def save_schemaz(json_path):
    """
    Save `schemaz` dict (all DataMatrix instances) to json file.

    Args:
        schemaz_path (str):  location of file to write
    """
    log.debug('* save_schemaz() ...')
    nsch = len(schemaz)
    with open(json_path, 'w') as f:
        f.write(json.dumps(schemaz, separators=(',', ':'),
                           indent=4, sort_keys=True))
    log.debug(f'  ... {nsch} schema(s) saved to schemas.json.')

def load_dmz(json_path):
    """
    Load the `dmz` dict from json file.  (Restores all DataMatrix
    instances.)

    Args:
        dmz_path (str):  location of file to read
    """
    log.debug('* load_dmz() ...')
    if os.path.exists(json_path):
        with open(json_path) as f:
            ser_dms = json.loads(f.read()) or {}
        try:
            deser_dms = {oid: DataMatrix([
                              Entity(oid=oid) for oid in sdm.get('ents', [])],
                              project_id=sdm['project_id'],
                              schema_name=sdm['schema_name'],
                              level_map=sdm['level_map'],
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

def save_dmz(json_path):
    """
    Save `dmz` dict (all DataMatrix instances) to json file.

    Args:
        dmz_path (str):  location of file to write
    """
    log.debug('* save_dmz() ...')
    ser_dms = {oid: dict(project_id=dm.project_id,
                         schema_name=dm.schema_name,
                         ents=[e.oid for e in dm],
                         level_map=dm.level_map,
                         creator=dm.creator,
                         modifier=dm.modifier,
                         create_datetime=dm.create_datetime,
                         mod_datetime=dm.mod_datetime)
               for oid, dm in dmz.items()}
    ndms = len(ser_dms)
    with open(json_path, 'w') as f:
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
    composed from the 'id' of its owner Project and its `schema_name` (which is
    the key used to look up its schema in the `schemaz' cache).

    When a DataMatrix is instantiated, its initialization will first check the
    `dmz` to see if it already exists; if not, it will create a new metadata
    record for itself there.

    Attributes:
        data (iterable):  an iterable of entities
        level_map (dict):  maps entity oids to assembly levels (ints > 0)
        project_id (str): id a project (owner of the DataMatrix)
        schema (list): list of data element ids and parameter ids
        schema_name (str): name of a schema for lookup in 'schemaz' cache
    """
    def __init__(self, *data, project_id='', schema_name=None, level_map=None,
                 creator=None, modifier=None, create_datetime=None,
                 mod_datetime=None):
        """
        Initialize.

        Args:
            data (iterable):  (optional) an iterable of entities

        Keyword Args:
            project_id (str): id of a project (owner of the DataMatrix)
            schema_name (str): name of a schema for lookup in 'schemaz' cache
            level_map (dict):  maps entity oids to assembly levels (ints > 0)
            creator (str):  oid of the entity's creator
            modifier (str):  oid of the entity's last modifier
            create_datetime (str):  iso-format string of creation datetime
            mod_datetime (str):  iso-format string of last mod datetime
        """
        super(DataMatrix, self).__init__(*data)
        # sig = 'project_id="{}", schema_name="{}"'.format(
                                        # project_id, schema_name or '[None]')
        # log.debug('* DataMatrix({})'.format(sig))
        # metadata
        dt = str(dtstamp())
        self.creator = creator or 'pgefobjects:admin'
        self.modifier = modifier or 'pgefobjects:admin'
        self.create_datetime = create_datetime or dt
        self.mod_datetime = mod_datetime or dt
        self.project_id = project_id or 'SANDBOX'
        self.level_map = level_map or {}
        # log.debug('  - project id: {}'.format(project_id))
        self.schema_name = schema_name or 'generic'
        # log.debug('  - schema_name set to: "{}"'.format(schema_name))
        # log.debug('  - looking up schema ...')
        self.schema = schemaz.get(schema_name, [])
        if self.schema:
            self.column_labels = [
                (de_defz.get(col_id, {}).get('label', '')
                 or parm_defz.get(col_id, {}).get('label', '')
                 or de_defz.get(col_id, {}).get('name', '')
                 or parm_defz.get(col_id, {}).get('name', '')
                 or col_id)
                for col_id in self.schema]
        else:
            # if schema lookup is unsuccessful, use the supplied schema, if
            # any, or a generic schema of last resort ...
            self.schema = ['name', 'desc']
            self.column_labels = ['Name', 'Description']
        # add myself to the dmz cache
        dmz[self.oid] = self

    @property
    def oid(self):
        return '-'.join([self.project_id, self.schema_name])

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
        i = len(self)
        self.append(e)
        if child:
            # assembly level 1 higher than preceding row if a child
            level = (self.level_map.get(self[i-1].get('oid')) or 0) + 1
        else:
            # assembly level same as preceding row if a peer
            level = self.level_map.get(self[i-1].get('oid')) or 0
        self.level_map[e.oid] = level
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
        if child_of is False:
            # assembly level same as preceding row if a peer
            level = self.level_map.get(self[i-1].get('oid')) or 0
        else:
            # assembly level 1 higher than the specified "child_of"
            level = (self.level_map.get(self[i-1].get('oid')) or 0) + 1
        self.level_map[e.oid] = level
        return e

    def remove_row(self, i):
        """
        Remove the ith row.
        """
        if i >= len(self):
            return False
        if getattr(self[i], 'oid') in self.level_map:
            del self.level_map[getattr(self[i], 'oid')]
        del self[i]
        return True

    def remove_row_by_oid(self, oid):
        """
        Remove the row with the specified oid.
        """
        oids = [e.oid for e in self]
        if oid not in oids:
            return False
        del self[oids.index(oid)]
        return True

    # NOTE: this code is just a copy of the code in reports.py for MEL
    # generation -- needs to be adapted/generalized ...
    def refresh_mel_data(self, context):
        """
        Refresh generated MEL (Master Equipment List) parameters related to a
        'context' (Project or Product) from which the generated values are
        obtained.

        Args:
            context (Project or Product):  the project or system to which the
                generated MEL parameters pertain
        """
        new = False
        if not self.data:
            new = True
            row = 1
        if new:
            if context.__class__.__name__ == 'Project':
                # context is Project, so may include several systems
                project = context
                system_names = [psu.system.name.lower() for psu in project.systems]
                system_names.sort()
                systems_by_name = {psu.system.name.lower() : psu.system
                                   for psu in project.systems}
                for system_name in system_names:
                    system = systems_by_name[system_name]
                    row = self.get_components_parms(self.data, 1, row, system)
            elif context.__class__.__name__ == 'HardwareProduct':
                # context is Product -> a single system MEL
                system = context
                row = self.get_components_parms(self.data, 1, row, system)
            else:
                # not a Project or HardwareProduct
                pass
        else:
            # [1] add/remove oids as necessary
            # [2] update existing oids
            pass

    def get_components_parms(self, level, row, component, qty=1):
        oid = component.oid
        self.data['m_unit'] = get_pval(oid, 'm[CBE]')
        self.data['m_cbe'] = qty * self.data['m_unit']
        self.data['m_ctgcy'] = get_pval(oid, 'm[Ctgcy]')
        self.data['m_mev'] = qty * get_pval(oid, 'm[MEV]')
        self.data['nom_p_unit_cbe'] = get_pval(oid, 'P[CBE]')
        self.data['nom_p_cbe'] = qty * self.data['nom_p_unit_cbe']
        self.data['nom_p_ctgcy'] = get_pval(oid, 'P[Ctgcy]')
        self.data['nom_p_mev'] = qty * get_pval(oid, 'P[MEV]')
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
        row += 1
        print('writing {} in row {}'.format(component.name, row))
        # then write the "LEVEL" cell
        self.data[oid]['level'] = level
        self.data[oid]['name'] = component.name
        if component.components:
            next_level = level + 1
            comp_names = [acu.component.name.lower()
                          for acu in component.components]
            comp_names.sort()
            comps_by_name = {acu.component.name.lower() : acu.component
                             for acu in component.components}
            qty_by_name = {acu.component.name.lower() : acu.quantity or 1
                           for acu in component.components}
            for comp_name in comp_names:
                comp = comps_by_name[comp_name]
                qty = qty_by_name[comp_name]
                row = self.get_components_parms(self.data, next_level, row,
                                                comp, qty)
        return row

