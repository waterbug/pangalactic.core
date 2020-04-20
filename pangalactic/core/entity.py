# -*- coding: utf-8 -*-
"""
Pan Galactic Entity and DataMatrix classes.
"""
from copy            import deepcopy
from collections     import UserList
from collections.abc import MutableMapping
from itertools       import chain
from uuid            import uuid4

# pangalactic
from pangalactic.core.parametrics     import (de_defz, parm_defz,
                                              entz, ent_histz,
                                              data_elementz,
                                              parameterz,
                                              schemaz, dmz,
                                              get_dval, get_pval,
                                              set_dval, set_pval)
from pangalactic.core.utils.datetimes import dtstamp


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
        log.debug('* __getitem__()')
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
        sig = 'project_id="{}", schema_name="{}"'.format(
                                        project_id, schema_name or '[None]')
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
        return '-'.join([self.project.id, self.schema_name])

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

    def insert_new_row(self, i, child=False):
        """
        Inserts an empty Entity with a new oid, in the ith position, using
        'child' flag to compute the level.
        """
        e = Entity()
        self.insert(i, e)
        if child:
            # assembly level 1 higher than preceding row if a child
            level = (self.level_map.get(self[i-1].get('oid')) or 0) + 1
        else:
            # assembly level same as preceding row if a peer
            level = self.level_map.get(self[i-1].get('oid')) or 0
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

