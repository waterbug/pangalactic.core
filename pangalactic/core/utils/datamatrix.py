# -*- coding: utf-8 -*-
"""
Pan Galactic Entity and DataMatrix classes.
"""
import os
from copy            import deepcopy
from collections     import UserList
from collections.abc import MutableMapping
from itertools       import chain
from uuid            import uuid4

# pangalactic
from pangalactic.core                 import config
from pangalactic.core.parametrics     import (de_defz, parm_defz,
                                              entz, ent_histz,
                                              data_elementz,
                                              parameterz,
                                              schemaz, dmz,
                                              get_dval, get_pval,
                                              set_dval, set_pval)
from pangalactic.core.uberorb         import orb
from pangalactic.core.utils.datetimes import dtstamp
# from pangalactic.core.utils.meta       import uncookers


class Entity(MutableMapping):
    """
    An interface to access a set of Data Elements and Parameters in the
    `data_elementz` and `parameterz` caches, respectively.  The concept behind
    Entity is essentially synonymous with "record" as in database records,
    "row" as in tables or matrices, anonymous Class instances in an ontology,
    or "Item" in a PyQt QAbstractItemModel.  Its metadata (owner, creator,
    modifier, create_datetime, and mod_datetime) are maintained in the 'entz'
    cache.  Attributes other than its 'oid' are accessed from caches: its
    metadata are stored in the 'entz' cache; all other attributes are accessed
    via the `data_elementz` and `parameterz` caches; therefore, an Entity does
    not store any data locally other than its 'oid', which is used as a key
    when interfacing to the caches.

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
        orb.log.debug('* Entity()')
        super(Entity, self).__init__(*args, **kw)
        if not oid:
            oid = str(uuid4())
        self.oid = oid
        # TODO:  also check if oid is that of an object
        if oid not in entz:
            dt = str(dtstamp())
            creator = 'pgefobjects:admin'
            modifier = 'pgefobjects:admin'
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
        # orb.log.debug('* __getitem__()')
        if k in ('oid', 'owner', 'creator', 'modifier', 'create_datetime',
                 'mod_datetime'):
            # metadata
            return entz[self.oid].get(k)
        elif k in parm_defz:
            return get_pval(orb, self.oid, k)
        else:
            return get_dval(orb, self.oid, k)

    def get(self, k, *default):
        """
        Get the value of an entity key, returning [0] for a metadata key, a
        metadata value, [1] for a data element, a simple value, [2] for a
        parameter, a value in base units, [3] if none of those are present,
        None or whatever is provided in the 'default' arg.
        """
        # orb.log.debug('* get()')
        if k in ('oid', 'owner', 'creator', 'modifier', 'create_datetime',
                 'mod_datetime'):
            # metadata
            # orb.log.debug('  - got metadata.')
            return entz[self.oid].get(k)
        elif k in parm_defz:
            # orb.log.debug('  - got parameter.')
            return get_pval(orb, self.oid, k)
        elif k in de_defz:
            # orb.log.debug('  - got data element.')
            return get_dval(orb, self.oid, k)
        elif default:
            # orb.log.debug('  - got default: {}.'.format(str(default)))
            return default[0]
        else:
            # orb.log.debug('  - got nothin.')
            return get_dval(orb, self.oid, k)

    def __setitem__(self, k, v):
        """
        Set the value of an entity key, which may be a metadata key, a data
        element, or a parameter.  Note that this will add the key if it is not
        already present.
        """
        orb.log.debug('* __getitem__()')
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
                success = set_pval(orb, self.oid, k, v)
            else:
                success = set_dval(orb, self.oid, k, v)
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
            parms = ', '.join(['{}: {}'.format(k, get_pval(orb, self.oid, k))
                               for k in parameterz.get(self.oid, {})])
        des = None
        if data_elementz.get(self.oid, {}).items():
            des = ', '.join(['{}: {}'.format(k, get_dval(orb, self.oid, k))
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
        data (iterable):  an iterable of entity oids
        level_map (dict):  maps entity oids to assembly levels
        project (Project): associated project (owner of the DataMatrix)
        schema_name (str): name of a schema for lookup in the `schemaz` cache
            -- if found, the 'schema' arg will be ignored
        schema (list): list of data element ids and parameter ids
    """
    def __init__(self, *data, project=None, schema_name=None, schema=None,
                 owner=None, creator=None, modifier=None, create_datetime=None,
                 mod_datetime=None):
        """
        Initialize.

        Args:
            data (iterable):  (optional) an iterable of Entity oids

        Keyword Args:
            project (Project): associated project (owner of the DataMatrix)
            schema_name (str): name of a schema for lookup in
                config['dm_schemas'] -- if found, 'schema' arg will be ignored
            schema (list): list of data element ids (column "names")
            owner (str):  oid of an Organization
            creator (str):  oid of the entity's creator
            modifier (str):  oid of the entity's last modifier
            create_datetime (str):  iso-format string of creation datetime
            mod_datetime (str):  iso-format string of last mod datetime
        """
        super(DataMatrix, self).__init__(*data)
        sig = 'project="{}", schema_name="{}", schema={}'.format(
                                        getattr(project, 'id', '') or '[None]',
                                        schema_name or '[None]',
                                        str(schema or '[None]'))
        orb.log.debug('* DataMatrix({})'.format(sig))
        self.level_map = {}
        if not isinstance(project, orb.classes['Project']):
            project = orb.get('pgefobjects:SANDBOX')
        self.project = project
        orb.log.debug('  - project: {}'.format(project.id))
        self.schema_name = schema_name or 'generic'
        orb.log.debug('  - schema_name set to: "{}"'.format(schema_name))
        orb.log.debug('  - looking up schema ...')
        config_deds = config.get('deds', {})
        self.schema = schemaz.get(schema_name, [])
        if self.schema:
            self.column_labels = [
                (de_defz.get(col_id, {}).get('label', '')
                 or config_deds.get(col_id, {}).get('label', '')
                 or parm_defz.get(col_id, {}).get('label', '')
                 or de_defz.get(col_id, {}).get('name', '')
                 or config_deds.get(col_id, {}).get('name', '')
                 or parm_defz.get(col_id, {}).get('name', '')
                 or col_id)
                for col_id in self.schema]
        else:
            # if schema lookup is unsuccessful, use the supplied schema, if
            # any, or a generic schema of last resort ...
            self.schema = schema or ['name', 'desc']
            self.column_labels = schema or ['Name', 'Description']
        # add myself to the dmz cache
        dmz[self.oid] = self

    @property
    def oid(self):
        return '-'.join([self.project.id, self.schema_name])

    def row(self, i):
        """
        Return the i-th row from the dm.
        """
        if i >= len(self):
            return
        return self[i]

    def append_new_row(self, child=False):
        """
        Appends an empty Entity with a new oid, using 'child' flag to compute
        the level.
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

# class DataMatrixOld(dict):
    # """
    # A dict that contains "entities" (dicts), a.k.a. rows, as its values.  The
    # DataMatrix maps the unique identifier ("oid") of each entity to the entity.
    # The DataMatrix has an attribute "schema" that is a list of data element
    # identifiers that reference DataElementDefinitions (which are cached in the
    # "de_defz" dict for quick access). Each entity maps data element ids to
    # values.

    # A DataMatrix is cached in the orb's data store (`orb.data`) and can be
    # saved to a .tsv file whose name is formed using the unique identifier (oid)
    # of the DataMatrix, which is composed from the 'id' of its owner Project and
    # the name of its schema.

    # When a DataMatrix is instantiated, its initialization will first look for
    # an appropriately named file in the orb's persistent data store (the `data`
    # directory in app home); if that is not found, it will use the schema
    # provided in the `schema` argument or, if that is not provided, a default
    # schema that can be configured by the app, and create an empty instance with
    # that schema.

    # Attributes:
        # project (Project): associated project (owner of the DataMatrix)
        # schema_name (str): name of a schema for lookup in `schemaz` cache
            # -- if found, 'schema' arg will be ignored
        # schema (list): list of data element or parameter ids (column "names")
        # oids (list): list of Entity oids
    # """
    # def __init__(self, *args, project=None, schema_name=None, schema=None,
                 # **kw):
        # """
        # Initialize.

        # Keyword Args:
            # project (Project): associated project (owner of the DataMatrix)
            # schema_name (str): name of a schema for lookup in
                # config['dm_schemas'] -- if found, 'schema' arg will be ignored
            # schema (list): list of data element ids (column "names")
        # """
        # super(DataMatrix, self).__init__(*args, **kw)
        # self.oids = []
        # sig = 'project="{}", schema_name="{}", schema={}'.format(
                                        # getattr(project, 'id', '') or '[None]',
                                        # schema_name or '[None]',
                                        # str(schema or '[None]'))
        # orb.log.debug('* DataMatrix({})'.format(sig))
        # if not isinstance(project, orb.classes['Project']):
            # project = orb.get('pgefobjects:SANDBOX')
        # self.project = project
        # orb.log.debug('  - project: {}'.format(project.id))
        # self.schema_name = schema_name or config.get('default_schema_name',
                                                     # 'generic')
        # orb.log.debug('  - schema_name set to: "{}"'.format(schema_name))
        # got_data = False
        # config_deds = config.get('deds', {})
        # if self.schema_name:
            # fname = self.oid + '.tsv'
            # try:
                # self.load(fname)
                # self.schema_name = self.oid[len(self.project.id)+1:]
                # # if load is successful, it will set self.schema from the file
                # # column headings -- the following checks to see if any column
                # # labels can be found based on self.schema; if a label is not
                # # found, the column heading from the file will be used
                # self.column_labels = [
                    # (de_defz.get(deid, {}).get('label', '')
                     # or config_deds.get(deid, {}).get('label', '')
                     # or de_defz.get(deid, {}).get('name', '')
                     # or config_deds.get(deid, {}).get('name', '')
                     # or deid)
                    # for deid in self.schema]
                # got_data = True
            # except:
                # orb.log.debug('  - unable to load "{}".'.format(fname))
                # orb.log.debug('    empty DataMatrix will be created ...')
        # if not got_data:
            # orb.log.debug('  - no data; looking up schema ...')
            # # if self.dm has a 'schema_name' set, precedence is given to a schema
            # # lookup in config["dm_schemas"] by 'schema_name' over a 'schema'
            # # that has been assigned to the dm.
            # std_schema = config.get('dm_schemas', {}).get(schema_name, [])
            # if std_schema:
                # msg = 'std schema "{}" found, setting col labels ...'.format(
                                                                 # schema_name)
                # orb.log.debug('  - {}'.format(msg))
                # self.schema = std_schema[:]
                # self.column_labels = [
                    # (de_defz.get(deid, {}).get('label', '')
                     # or config_deds.get(deid, {}).get('label', '')
                     # or de_defz.get(deid, {}).get('name', '')
                     # or config_deds.get(deid, {}).get('name', '')
                     # or deid)
                    # for deid in std_schema]
            # else:
                # self.schema = schema or ['name', 'desc']
                # self.column_labels = schema or ['Name', 'Description']
        # # add myself to the orb.data in-memory cache
        # orb.data[self.oid] = self

    # @property
    # def oid(self):
        # return '-'.join([self.project.id, self.schema_name])

    # def row(self, i):
        # """
        # Return the i-th row from the dm.
        # """
        # if i >= len(self.oids):
            # return
        # return self[self.oids[i]]

    # def append_new_row(self):
        # """
        # Appends an empty Entity with a new oid.
        # """
        # e = Entity()
        # self[e.oid] = e
        # self.oids.append(e.oid)
        # return e

    # def insert_new_row(self, i):
        # """
        # Inserts an empty Entity with a new oid, in the ith position.
        # """
        # e = Entity()
        # self[e.oid] = e
        # self.oids.insert(i, e.oid)
        # return e

    # def remove_row(self, i):
        # """
        # Remove the ith row.
        # """
        # if i >= len(self.oids):
            # return False
        # oid = self.oids[i]
        # del self[oid]
        # self.oids.pop(i)
        # return True

    # def remove_oid(self, oid):
        # """
        # Remove the row with the specified oid.
        # """
        # if oid not in self.oids:
            # return False
        # self.oids.remove(oid)
        # del self[oid]
        # return True

    # ---------------------------------------------------------------------
    # NOTE:  the "load" method is unnecessary in the Entity paradigm:  the
    # Entity's data is all in the caches and is accessed from there.
    # ---------------------------------------------------------------------
    # def load(self, fname):
        # """
        # Load data from a datamatrix .tsv file.

        # Args:
            # fname (str): name of a DataMatrix .tsv file
        # """
        # # TODO: add exception handling:  empty file, etc.
        # orb.log.debug('* dm.load({})'.format(fname))
        # fpath = os.path.join(orb.data_store, fname)
        # if not os.path.exists(fpath):
            # orb.log.debug('  - path "{}" does not exist)'.format(fpath))
            # return
        # with open(fpath) as f:
            # first = f.readline()
            # schema = first[:-1].split('\t')
            # orb.log.debug('  - serialized schema: "{}"'.format(str(schema)))
            # for line in f:
                # data = line[:-1].split('\t')
                # if len(data) == 1:
                    # # this would be a final empty line
                    # break
                # data_row_dict = {}
                # for i, de in enumerate(schema):
                    # data_row_dict[de] = data[i]
                # if 'oid' in data_row_dict:
                    # oid = data_row_dict['oid']
                    # del data_row_dict['oid']
                # else:
                    # oid = str(uuid4())
                # self[oid] = deepcopy(data_row_dict)
                # self.oids.append(oid)
                # orb.log.debug('  - read row "{}": {}'.format(
                                                # oid, str(self[oid])))
            # schema.remove('oid')
            # orb.log.debug('  - schema: "{}"'.format(str(schema)))
            # orb.log.debug('    + read {} row(s) of data:'.format(len(self)))
            # self.schema = schema
            # orb.log.debug('    + schema: {}'.format(str(schema)))
            # for row_oid, row_dict in self.items():
                # # type cast data element values in each row
                # for de in row_dict:
                    # row_dict[de] = uncookers[(schema[de]['range_datatype'],
                                              # True)](row_dict[de])
                # orb.log.debug('      {}: {}'.format(row_oid, str(row_dict)))

    def save(self, fmt='tsv'):
        """
        Persist my data.

        Keyword args:
            fmt (str):  persistence format: one of [tsv|json|yaml]
        """
        if fmt == 'tsv':
            self.to_tsv()
            return True
        # TODO:  json and yaml
        return False

    def to_tsv(self, fpath=None):
        """
        Write my data into a .tsv file in the specified path (default: the
        orb's "data store" (i.e., 'app_home/data').
        """
        orb.log.debug('  - dm.save()')
        orb.log.debug('    data rows: {}'.format(len(self)))
        orb.log.debug('    row oids: {}'.format(str(self.oids)))
        fname = self.oid + '.tsv'
        orb.log.debug('    output file name: {}'.format(fname))
        if not fpath:
            fpath = orb.data_store
        f = open(os.path.join(fpath, fname), 'w')
        # header line
        ser_schema = ['oid']
        ser_schema += self.schema[:]
        data_out = '\t'.join(ser_schema) + '\n'
        orb.log.debug('  - output schema: {}'.format(ser_schema))
        for oid in self.oids:
            if not oid:
                continue
            orb.log.debug('  - row with oid: {}'.format(oid))
            orb.log.debug('    {}'.format(str(self[oid])))
            ser_row = [oid]
            for deid in self.schema:
                ser_row.append(str(self[oid].get(deid) or ''))
            orb.log.debug('    serialized row: {}'.format(str(ser_row)))
            data_out += '\t'.join(ser_row) + '\n'
        orb.log.debug('    + writing data:')
        orb.log.debug('      {}'.format(data_out))
        f.write(data_out)
        f.close()

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
            if isinstance(context, orb.classes['Project']):
                # context is Project, so may include several systems
                project = context
                system_names = [psu.system.name.lower() for psu in project.systems]
                system_names.sort()
                systems_by_name = {psu.system.name.lower() : psu.system
                                   for psu in project.systems}
                for system_name in system_names:
                    system = systems_by_name[system_name]
                    row = self.get_components_parms(self.data, 1, row, system)
            elif isinstance(context, orb.classes['Product']):
                # context is Product -> a single system MEL
                system = context
                row = self.get_components_parms(self.data, 1, row, system)
            else:
                # not a Project or Product
                pass
        else:
            # [1] add/remove oids as necessary
            # [2] update existing oids
            pass

    def get_components_parms(self, level, row, component, qty=1):
        oid = component.oid
        self.data['m_unit'] = get_pval(orb, oid, 'm[CBE]')
        self.data['m_cbe'] = qty * self.data['m_unit']
        self.data['m_ctgcy'] = get_pval(orb, oid, 'm[Ctgcy]')
        self.data['m_mev'] = qty * get_pval(orb, oid, 'm[MEV]')
        self.data['nom_p_unit_cbe'] = get_pval(orb, oid, 'P[CBE]')
        self.data['nom_p_cbe'] = qty * self.data['nom_p_unit_cbe']
        self.data['nom_p_ctgcy'] = get_pval(orb, oid, 'P[Ctgcy]')
        self.data['nom_p_mev'] = qty * get_pval(orb, oid, 'P[MEV]')
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

