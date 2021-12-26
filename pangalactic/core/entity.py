# -*- coding: utf-8 -*-
"""
Pan Galactic Entity and DataMatrix classes.
"""
import json, os
from copy            import deepcopy
from itertools       import chain
from uuid            import uuid4

# pangalactic
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


class DummyAcu:
    def __init__(self):
        self.assembly = None
        self.component = None
        self.quantity = None
        self.reference_designator = None

# -----------------------------------------------------------------------
# ENTITY-RELATED CACHES
# -----------------------------------------------------------------------
# ent_histz:  persistent** cache of previous versions of entities,
#             saved as named tuples ...
#              ** persisted in the file 'ent_hists.json' in the
#              application home directory -- see
#              `save_ent_histz` and `load_ent_histz`
# format:  {entity['oid'] : [list of previous versions of entity]}
ent_histz = {}

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

    By design, an Entity is always created within the context of a DataMatrix
    (a list of Entities) and can only exist within its containing DataMatrix
    because some or all of its data may only be meaningful within that context.

    The concept behind Entity is similar to "record" as in database records,
    "row" as in tables or matrices, anonymous Class instances in an ontology,
    or "Item" in a PyQt QAbstractItemModel.  Its metadata are maintained in the
    'dmz' (DataMatrix) cache along with its containing DataMatrix.  Attributes
    other than its metadata are accessed via the `data_elementz` and
    `parameterz` caches; therefore, an Entity does not store any data locally
    and its 'oid' is used as a key when interfacing to the caches.

    Attributes:
        oid (str):  a unique identifier
        dm_oid (str):  oid of the entity's containing DataMatrix
        parent_oid (str):  oid of the entity's "parent" entity
        system_oid (str):  [optional] oid of a system (Project or Product)
            to which the entity is mapped
        assembly_level (int):  [computed] level of assembly at which the Entity
            occurs in its DataMatrix (if no DataMatrix, it is 1).
        system_name (str):  derived from the library product name and
            reference_designator within its assembly
    """
    metadata = ['oid', 'dm_oid', 'parent_oid', 'system_oid', 'system_name',
                'owner', 'creator', 'modifier', 'create_datetime',
                'mod_datetime']

    def __init__(self, *args, oid=None, dm_oid=None, parent_oid=None,
                 system_oid=None, system_name=None, owner=None, creator=None,
                 modifier=None, create_datetime=None, mod_datetime=None, **kw):
        """
        Initialize.

        Args:
            args (tuple):  optional positional argument (0 or 1).  If a
                positional arg is present, it must be either a mapping or an
                iterable in which each element is an iterable containing 2
                elements (e.g. a list of 2-tuples).

        Keyword Args:
            oid (str):  a unique identifier
            dm_oid (str):  oid of the entity's containing DataMatrix
            parent_oid (str):  oid of the entity's "parent" entity
            system_oid (str):  [optional] oid of a system (Project or Product)
                to which the entity is mapped
            system_name (str):  derived from the library product name and
                reference_designator within its assembly
            owner (str):  oid of an Organization
            creator (str):  oid of the entity's creator
            modifier (str):  oid of the entity's last modifier
            create_datetime (str):  iso-format string of creation datetime
            mod_datetime (str):  iso-format string of last mod datetime
            kw (dict):  keyword args, passed to superclass (dict)
                initialization
        """
        log.debug(f'* Entity(oid={oid}, dm_oid={dm_oid},')
        log.debug(f'         parent_oid={parent_oid},')
        log.debug(f'         system_oid={system_oid},')
        log.debug(f'         system_name={system_name}, ...)')
        super().__init__(*args)
        self.mapped = False
        # TODO:  check for oid collisions
        if not oid:
            oid = str(uuid4())
        self.oid = oid
        self.dm_oid = dm_oid
        self.parent_oid = parent_oid
        self.system_oid = system_oid
        self.system_name = system_name
        self.owner = owner or 'pgefobjects:PGANA'
        self.creator = creator or 'pgefobjects:admin'
        self.modifier = modifier or 'pgefobjects:admin'
        dt = str(dtstamp())
        self.create_datetime = create_datetime or dt
        self.mod_datetime = mod_datetime or dt

    @property
    def assembly_level(self):
        dm = dmz.get(self.dm_oid)
        if dm:
            entities = {e.oid : e for e in dm}
            if self.parent_oid in entities:
                return entities[self.parent_oid].assembly_level + 1
        return 1

    def __getitem__(self, k):
        """
        Get the value of an entity key, returning [1] for a data element, a
        simple value, [2] for a parameter, a value in base units, [3] if none
        of those are present, None or whatever is provided in the 'default'
        arg.
        """
        # log.debug(f'* Entity.__getitem__({k})')
        # print(f'* Entity.__getitem__({k})')
        # NOTE: for special attrs 'oid', 'assembly_level' and 'system_name',
        # they are both object attributes and dict keys
        if k in ['oid', 'assembly_level', 'system_name']:
            return getattr(self, k)
        elif k in parm_defz:
            # k is a parameter
            # print('  - got parameter.')
            return get_pval(self.oid, k)
        else:
            # k is a data element or undefined
            # print('  - got data element or undefined.')
            return get_dval(self.oid, k)

    def get(self, k, *default):
        """
        Get the value of an entity key, returning [1] for a data element, a
        simple value, [2] for a parameter, a value in base units, [3] if none
        of those are present, None or whatever is provided in the 'default'
        arg.
        """
        # NOTE: for special attrs 'oid', 'assembly_level' and 'system_name',
        # they are both object attributes and dict keys
        if k in ['oid', 'assembly_level', 'system_name']:
            return getattr(self, k)
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
        success = False
        previous_self = deepcopy(self)
        if k in ['oid', 'system_name']:
            object.__setattr__(self, k, v)
            success = True
        else:
            if k in parm_defz:
                success = set_pval(self.oid, k, v)
            elif k in de_defz:
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
        s = '<Entity "' + self.oid + '">: '
        for a in self.metadata:
            s += '\n' + ': '.join([a, getattr(self, a) or ''])
        s += '\n{' + '\n'.join([parms, des]) + '}'
        return s

    def undo(self):
        if self.oid in ent_histz and ent_histz[self.oid]:
            self = ent_histz[self.oid].pop()

    def serialize_meta(self):
        """
        Serialize only the metadata for the Entity.  (Used when saving the
        entity as part of a serialized DataMatrix.)
        """
        d = {a : getattr(self, a, '') for a in self.metadata}
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

    def delete(self):
        """
        Remove all references to the Entity from ent_histz, parameterz,
        data_elementz, and dmz.
        """
        if self.oid in ent_histz:
            del ent_histz[self.oid]
        if self.oid in parameterz:
            del parameterz[self.oid]
        if self.oid in data_elementz:
            del data_elementz[self.oid]
        dm = dmz.get(self.dm_oid)
        if dm and self in dm:
            dm.remove(self)

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
                              Entity(**se) for se in sdm['ents']],
                              project_oid=sdm['project_oid'],
                              entity_class=sdm['entity_class'],
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
    ser_dms = {oid: dict(project_oid=dm.project_oid,
                         entity_class=dm.entity_class,
                         ents=[e.serialize_meta() for e in dm],
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


class DataMatrix(list):
    """
    A list subclass that contains instances of Entity as its items.  A
    DataMatrix has an attribute `schema` that is a list of identifiers that
    reference DataElementDefinitions or ParameterDefinitions, which are cached
    in the `de_defz` dict and `parm_defz` dict, respectively.

    All DataMatrix instances are cached in the `dmz` dict cache, in which the
    key is the DataMatrix instance `oid`, a property composed from its
    `project_oid` (the `oid` of its owner Project) and its `entity_class`
    (which is also the key used to look up its `schema` in the `schemaz`
    cache).

    Attributes:
        data (iterable):  an iterable of entities
        project_oid (str): oid of a project (owner of the DataMatrix)
        schema (list): list of data element ids and parameter ids
        mapped_ents (list): used when recomputing a MEL DataMatrix to keep
            track of which entities have been mapped from the assembly
            structure(s)
    """
    def __init__(self, *data, project_oid=None, entity_class='HardwareProduct',
                 schema_name=None, schema=None, creator=None, modifier=None,
                 create_datetime=None, mod_datetime=None):
        """
        Initialize.

        Args:
            data (iterable):  (optional) an iterable of entities

        Keyword Args:
            project_oid (str): oid of a project (owner of the DataMatrix)
            entity_class (str):  name of the class of the contained entities
                (e.g. "HardwareProduct", "Activity", "Requirement")
            schema_name (str): name of a schema to be looked up in the
                'schemaz' cache
            schema (list): list of data element ids and parameter ids
            creator (str):  oid of the entity's creator
            modifier (str):  oid of the entity's last modifier
            create_datetime (str):  iso-format string of creation datetime
            mod_datetime (str):  iso-format string of last mod datetime
        """
        super().__init__(*data)
        sig = f'project_oid="{project_oid}", entity_class="{entity_class}"'
        log.debug('* DataMatrix({})'.format(sig))
        dt = str(dtstamp())
        self.entity_class = entity_class
        self.creator = creator or 'pgefobjects:admin'
        self.modifier = modifier or 'pgefobjects:admin'
        self.create_datetime = create_datetime or dt
        self.mod_datetime = mod_datetime or dt
        # NOTE:  self.project_oid and self.entity_class MUST be set before
        # accessing self.oid, which is computed from them ...
        self.project_oid = project_oid or 'pgefobjects:SANDBOX'
        log.debug(f'  - project_oid set to: {self.project_oid}')
        # check for a cached DataMatrix instance with our computed oid ...
        log.debug(f'  checking `dmz` cache for oid "{self.oid}" ...')
        log.debug('  dmz cache is: {}'.format(str(dmz)))
        if self.oid in dmz:
            log.debug('  - found in cache ...')
            del dmz[self.oid]
            log.debug('    removed.')
        self.schema = schema
        if not schema:
            if schemaz.get(schema_name):
                log.debug(f'    found "{schema_name}" in schemaz cache ...')
                self.schema = schemaz[schema_name]
            else:
                log.debug(f'    "{schema_name}" schema not found ...')
                if entity_class == 'HardwareProduct':
                    self.schema_name = 'MEL'
                    self.schema = schemaz.get('MEL') or ['system_name']
                    log.debug('    using "MEL".')
                else:
                    # TODO: set default schemas for Activity and Requirement
                    self.schema_name = 'Default'
                    self.schema = ['system_name']
        # look for pre-defined column labels, or use names/ids as defaults
        if self.schema:
            log.debug('    setting column labels ...')
            self.column_labels = [
                (de_defz.get(col_id, {}).get('label', '')
                 or parm_defz.get(col_id, {}).get('label', '')
                 or de_defz.get(col_id, {}).get('name', '')
                 or parm_defz.get(col_id, {}).get('name', '')
                 or col_id)
                for col_id in self.schema]
        self.add_to_cache()

    @property
    def oid(self):
        return '-'.join([self.project_oid, self.entity_class, 'DataMatrix'])

    def __str__(self):
        s = 'DataMatrix: '
        if self:
            s = '['
            s += ', '.join([e.oid for e in self])
            s += ']'
        else:
            s += '[]'
        return s

    def etuples(self):
        """
        Return a list containing the unique tuple of

            (system_oid, parent_oid)

        for each entity in the DataMatrix, where "system_oid" is the oid of the
        product that maps to the entity and "parent_oid" is the oid of the
        entity's parent entity.

        The purpose of these tuples is to maintain the mapping of assembly
        items to entities in the Master Equipment List (MEL) as much as
        possible when a subassembly name, reference designator, or other
        attributes change, so that the information maintained in the MEL for an
        assembly item is not lost.

        NOTE: since the MEL is a *flattened* representation of the system
        assembly model -- i.e., all usages of a given product within a given
        subsystem are represented by a single line item in the MEL, even if the
        the usages may be distinguished by unique reference designators and
        positions in the system assembly model (e.g., RF wheel, LF wheel, RR
        wheel, LR wheel in a car chassis, all populated by the same "wheel"
        product) -- information in the MEL can only be associated with a single
        line item that represents all usages of a given product within a
        subsystem.
        """
        return [(entity.system_oid,
                 entity.parent_oid) for entity in self]

    def add_to_cache(self):
        """
        Add myself to the 'dmz' cache.
        """
        dmz[self.oid] = self

    def row(self, i):
        """
        Return the i-th entity from the dm.
        """
        if i >= len(self):
            return
        return self[i]

    def append_new_row(self, child=False):
        """
        Appends an "empty" Entity with a new oid.
        """
        e = Entity(dm_oid=self.oid)
        self.append(e)
        return e

    def insert_new_row(self, pos=None, child_of=None):
        """
        Inserts an empty Entity with a new oid, in the ith position.  To
        support GridTreeItem.insertChildren(), use child_of=True.

        Keyword Args:
            pos (int):  position at which to insert
            child_of (Entity):  the parent Entity (or None if same level as
                preceding row)
        """
        if child_of is not None:
            e = Entity(dm_oid=self.oid, parent_oid=child_of.oid)
        else:
            e = Entity(dm_oid=self.oid)
        if pos and pos < len(self):
            self.insert(pos, e)
        else:
            self.append(e)
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
            i = oids.index(oid)
        else:
            return False
        self.pop(i)
        return True

    def recompute(self, context):
        """
        Recompute parameters / data elements for the DataMatrix.

        Args:
            context (Project or Product):  the project or system to which the
                MEL parameters pertain
        """
        if self.entity_class == 'HardwareProduct':
            self.recompute_mel(context)
        elif self.entity_class == 'Activity':
            self.map_activities(context)
        elif self.entity_class == 'Requirement':
            self.map_requirements(context)

    def map_activities(self, context):
        """
        Compute parameters / data elements for a project's Activity model
        (ConOps).

        Args:
            context (Project or Product):  the project or system to which the
                parameters pertain
        """
        pass

    def map_requirements(self, context):
        """
        Compute parameters / data elements for a project's Requirements.

        Args:
            context (Project or Product):  the project or system to which the
                parameters pertain
        """
        pass

    def recompute_mel(self, context):
        """
        Compute parameters / data elements for a MEL (Master Equipment List) in
        a 'context' (Project or Product).

        Args:
            context (Project or Product):  the project or system to which the
                MEL parameters pertain
        """
        log.debug('* recompute_mel()')
        row = 0
        # re-mapping, so set all entities as not mapped
        for e in self:
            e.mapped = False
        if not context:
            return
        if context.__class__.__name__ == 'Project':
            log.debug(f'  recomputing MEL for Project "{context.id}" ...')
            # context is Project, so may include several systems
            project = context
            for psu in project.systems:
                name = f'{psu.system_role} [{psu.system.id}]'
                end = self.compute_mel_parms(row, name, psu.system)
                row += end + 1
        elif context.__class__.__name__ == 'HardwareProduct':
            # context is Product -> a single system MEL
            log.debug(f'  recomputing MEL for System "{context.id}" ...')
            name = f'{context.name} [{context.id}]'
            self.compute_mel_parms(0, name, context)
        else:
            # not a Project or HardwareProduct
            log.debug('  context specified is neither Project nor System.')
            return
        # after a recompute, remove and delete any unmapped entities ...
        log.debug('  checking for unmapped entities ...')
        unmapped = 0
        for entity in self:
            if not entity.mapped:
                log.debug(f'  removing unmapped entity "{entity.oid}"')
                self.remove_row_by_oid(entity.oid)
                entity.delete()
                unmapped += 1
        if unmapped:
            log.debug(f'  {unmapped} unmapped entities removed.')
        else:
            log.debug('  no unmapped entities found.')

    def compute_mel_parms(self, row, name, component, qty=1,
                          parent_oid=None):
        """
        Compute parameter and data element values for the components in a
        Master Equipment List (MEL) based on their positions in the system
        assembly.

        If there are multiple occurrences of a given product in the assembly of
        a system or subsystem, they will be collapsed into a single line item
        in the MEL.

        Args:
            row (int):  the (0-based) row index within the parent DataMatrix
            name (str):  the structured name:
                '{acu.reference_designator} {component.name}'
            component (Product):  the system Product instance

        Keyword Args:
            qty (int):  quantity of this item in its parent assembly
            parent_oid (str):  oid of this item's parent entity (NOT the oid of
                the component's parent assembly!)
        """
        log.debug(f'* compute_mel_parms({row}, {name}, qty={qty},')
        log.debug(f'                    parent_oid={parent_oid}')
        system_oid = component.oid
        etuple = (system_oid, parent_oid)
        log.debug(f'  for (system "{component.name}": {system_oid},')
        log.debug(f'       parent entity oid: {parent_oid})')
        # get the current set of entity "tuples" (which may change during
        # updating of the MEL DataMatrix)
        etups = self.etuples()
        # [1] check whether there is an entity anywhere in the DataMatrix that
        # corresponds to the current assembly item
        if etuple in etups:
            if row < len(etups) and etuple == etups[row]:
                log.debug('  etuple maps to the entity in this row.')
                entity = self[row]
            else:
                log.debug('  etuple maps to an entity in another row ...')
                entity = self.pop(etups.index(etuple))
                if row < len(self):
                    # row index is "inside" the DataMatrix, insert the entity there
                    self.insert(row, entity)
                else:
                    # otherwise, append it
                    self.append(entity)
        # [2] there is no corresponding entity in the current DataMatrix;
        # create a new entity (with an auto-generated oid)
        else:
            log.debug('  etuple not yet mapped to an entity, creating ...')
            entity = Entity(dm_oid=self.oid,
                            parent_oid=parent_oid,
                            system_oid=component.oid, 
                            system_name=name, 
                            owner=component.owner.oid,
                            creator=component.creator.oid,
                            create_datetime=str(component.create_datetime),
                            modifier=component.modifier.oid,
                            mod_datetime=str(component.mod_datetime))
            if row < len(self):
                # row index is "inside" the DataMatrix, insert the entity there
                self.insert(row, entity)
            else:
                # otherwise, append it
                self.append(entity)
        entity.mapped = True
        # map data element values to parameter values where appropriate ...
        # NOTE: not using set_dval() because these values are computed from the
        # model (they are still stored in data_elementz, so the values will
        # still be returned by get_dval())
        log.debug('  entity["system_name"] = {}'.format(entity['system_name']))
        # TODO:  define these Data Elements as "computed"
        entity['m_unit'] = get_pval(system_oid, 'm[CBE]') or 0
        entity['hot_units'] = qty
        entity['flight_units'] = qty
        log.debug('  entity["m_unit"] = {}'.format(entity['m_unit']))
        entity['m_cbe'] = qty * entity['m_unit']
        entity['m_ctgcy'] = (round_to(100 * get_pval(system_oid, 'm[Ctgcy]'),
                                      n=3) or 0)
        entity['m_mev'] = qty * (get_pval(system_oid, 'm[MEV]') or 0)
        entity['nom_p_unit_cbe'] = get_pval(system_oid, 'P[CBE]') or 0
        entity['nom_p_cbe'] = qty * (entity['nom_p_unit_cbe'] or 0)
        entity['nom_p_ctgcy'] = (round_to(100 * get_pval(system_oid,
                                                         'P[Ctgcy]')) or 0)
        entity['nom_p_mev'] = (round_to(qty * (get_pval(system_oid, 'P[MEV]')))
                               or 0)
        # columns in spreadsheet MEL computed from the model:
        #   0: Name
        #   1: Level
        #   2: Unit MASS CBE
        #   4: Hot Units
        #   5: Flight Units
        #   9: Mass CBE
        #  10: Mass Contingency (%)
        #  11: Mass MEV
        #  12: Unit Power CBE
        #  13: Power CBE
        #  14: Power Contingency (%)
        #  15: Power MEV
        log.debug(f' + writing {name} in row {row}')
        if component.components:
            log.debug('   - it has components ...')
            # ignore None and "TBD" components
            acus = [acu for acu in component.components
                    if (acu.component and
                        getattr(acu.component, 'oid', None) and
                        acu.component.oid != 'pgefobjects:TBD')]
            # consolidate acus if there are multiple usages of the same product
            consolidated_acus = acus
            acu_comp_oids = [acu.component.oid for acu in acus]
            if len(acu_comp_oids) > len(set(acu_comp_oids)):
                log.debug('     some collapsing is needed ...')
                # -> there are multiple usages of at least one product --
                #    collapse each such set of acus into a "dummy_acu"
                consolidated_acus = []
                comp_oid_to_acus = {}
                for acu in acus:
                    if comp_oid_to_acus.get(acu.component.oid):
                        comp_oid_to_acus[acu.component.oid].append(acu)
                    else:
                        comp_oid_to_acus[acu.component.oid] = [acu]
                for comp_oid, comp_acus in comp_oid_to_acus.items():
                    n = len(comp_acus)
                    if n > 1:
                        log.debug(f'     collapsing {n} components')
                        log.debug(f'     of "{acu.assembly.name}" ...')
                        dummy_acu = DummyAcu()
                        dummy_acu.assembly = comp_acus[0].assembly
                        dummy_acu.component = comp_acus[0].component
                        dummy_acu.quantity = sum([acu.quantity or 1
                                                  for acu in comp_acus])
                        dummy_acu.reference_designator = getattr(
                                            dummy_acu.component.product_type,
                                            'abbreviation')
                        consolidated_acus.append(dummy_acu)
                    else:
                        consolidated_acus.append(comp_acus[0])
            else:
                log.debug('     no collapsing needed.')
            # sort consolidated acus by reference designator
            # iterate over sorted acus
            for acu in consolidated_acus:
                row += 1
                component = acu.component
                qty = acu.quantity or 1
                name = f'{acu.reference_designator} [{component.name}]'
                row = self.compute_mel_parms(row, name, component, qty=qty,
                                             parent_oid=entity.oid)
        else:
            log.debug('   - no components found.')
        return row

