# -*- coding: utf-8 -*-
"""
Pan Galactic DataMatrix object, based on OrderedDict.
"""
import os
from collections import OrderedDict
from copy        import deepcopy
from uuid        import uuid4

# pangalactic
from pangalactic.core                  import config
from pangalactic.core.parametrics      import de_defz, get_pval
from pangalactic.core.uberorb          import orb
from pangalactic.core.utils.datetimes  import dtstamp
from pangalactic.core.utils.meta       import cookers, uncookers


class DataMatrix(OrderedDict):
    """
    An OrderedDict that has dicts (rows) as values, and maps a unique 'oid'
    value to each row.  It has an attribute "schema", which is a list of data
    element identifiers that reference DataElementDefinitions cached in the
    "de_defz" dict. Each row dict maps data element ids in the schema to
    values.

    The intent is that a DataMatrix can be created from a data structure that
    has keys/schema corresponding to data elements that are defined in
    "de_defz".

    A DataMatrix is cached in the orb's data store (`orb.data`) and can be
    saved to a .tsv file whose name is formed using the 'id' of its owner
    Project and the name of its schema.

    When DataMatrix is instantiated, its initialization will first look for an
    appropriately named file in the orb's persistent data store (the `data`
    directory in app home); if that is not found, it will use the schema
    provided in the `schema` argument or, if that is not provided, a default
    schema that can be configured by the app, and create an empty instance with
    that schema.

    Attributes:
        project (Project): associated project (becomes the owner of the DataSet
            that is created when the DataMatrix is saved)
        schema_name (str): name of a schema for lookup in config['dm_schemas']
            -- if found, 'schema' arg will be ignored
        schema (list): list of data element ids (column "names")
    """
    def __init__(self, *args, project=None, schema_name=None, schema=None,
                 **kw):
        """
        Initialize.

        Keyword Args:
            project (Project): associated project (becomes the owner of the DataSet
                that is created when the DataMatrix is saved)
            schema_name (str): name of a schema for lookup in
                config['dm_schemas'] -- if found, 'schema' arg will be ignored
            schema (list): list of data element ids (column "names")
        """
        super(DataMatrix, self).__init__(*args, **kw)
        sig = 'project="{}", schema_name="{}", schema={}'.format(
                                        getattr(project, 'id', '') or '[None]',
                                        schema_name or '[None]',
                                        str(schema or '[None]'))
        orb.log.debug('* DataMatrix({})'.format(sig))
        if not isinstance(project, orb.classes['Project']):
            project = orb.get('pgefobjects:SANDBOX')
        self.project = project
        orb.log.debug('  - project: {}'.format(project.id))
        self.schema_name = schema_name or config.get('default_schema_name',
                                                     'generic')
        orb.log.debug('  - schema_name set to: "{}"'.format(schema_name))
        got_data = False
        config_deds = config.get('deds', {})
        if self.schema_name:
            fname = self.oid + '.tsv'
            try:
                self.load(fname)
                self.schema_name = self.oid[len(self.project.id)+1:]
                # if load is successful, it will set self.schema from the file
                # column headings -- the following checks to see if any column
                # labels can be found based on self.schema; if a label is not
                # found, the column heading from the file will be used
                self.column_labels = [
                    (de_defz.get(deid, {}).get('label', '')
                     or config_deds.get(deid, {}).get('label', '')
                     or de_defz.get(deid, {}).get('name', '')
                     or config_deds.get(deid, {}).get('name', '')
                     or deid)
                    for deid in self.schema]
                got_data = True
            except:
                orb.log.debug('  - unable to load "{}".'.format(fname))
                orb.log.debug('    empty DataMatrix will be created ...')
        if not got_data:
            orb.log.debug('  - no data; looking up schema ...')
            # if self.dm has a 'schema_name' set, precedence is given to a schema
            # lookup in config["dm_schemas"] by 'schema_name' over a 'schema'
            # that has been assigned to the dm.
            std_schema = config.get('dm_schemas', {}).get(schema_name, [])
            if std_schema:
                msg = 'std schema "{}" found, setting col labels ...'.format(
                                                                 schema_name)
                orb.log.debug('  - {}'.format(msg))
                self.schema = std_schema[:]
                self.column_labels = [
                    (de_defz.get(deid, {}).get('label', '')
                     or config_deds.get(deid, {}).get('label', '')
                     or de_defz.get(deid, {}).get('name', '')
                     or config_deds.get(deid, {}).get('name', '')
                     or deid)
                    for deid in std_schema]
            else:
                self.schema = schema or ['name', 'desc']
                self.column_labels = schema or ['Name', 'Description']
        # add myself to the orb.data in-memory cache
        orb.data[self.oid] = self

    @property
    def oid(self):
        return '-'.join([self.project.id, self.schema_name])

    def row(self, i):
        """
        Return the i-th value from the dm.
        """
        if i >= len(self):
            return {}
        idxs = list(self.keys())
        return self[idxs[i]]

    def append_new_row(self):
        """
        Appends an empty row, with a new oid.
        """
        row_dict = {}
        oid = str(uuid4())
        self[oid] = row_dict
        return row_dict

    def load(self, fname):
        """
        Load data from a datamatrix .tsv file.

        Args:
            fname (str): name of a DataMatrix .tsv file
        """
        # TODO: add exception handling:  empty file, etc.
        orb.log.debug('* dm.load({})'.format(fname))
        fpath = os.path.join(orb.data_store, fname)
        if not os.path.exists(fpath):
            orb.log.debug('  - path "{}" does not exist)'.format(fpath))
            return
        with open(fpath) as f:
            first = f.readline()
            schema = first[:-1].split('\t')
            for line in f:
                data = line[:-1].split('\t')
                if len(data) == 1:
                    # this would be a final empty line
                    break
                data_row_dict = {}
                for i, de in enumerate(schema):
                    data_row_dict[de] = data[i]
                if 'oid' in data_row_dict:
                    oid = data_row_dict['oid']
                    del data_row_dict['oid']
                    schema.remove('oid')
                else:
                    oid = str(uuid4())
                self[oid] = deepcopy(data_row_dict)
            orb.log.debug('    + read {} row(s) of data:'.format(len(self)))
            self.schema = schema
            orb.log.debug('    + schema: {}'.format(str(schema)))
            for row_oid, row_dict in self.items():
                # type cast data element values in each row
                for de in row_dict:
                    row_dict[de] = uncookers[(schema[de]['range_datatype'],
                                              True)](row_dict[de])
                orb.log.debug('      {}: {}'.format(row_oid, str(row_dict)))

    def save(self):
        """
        Serialize my data into a .tsv file.
        """
        orb.log.debug('  - dm.save()')
        orb.log.debug('    + full dm:')
        orb.log.debug('      {}'.format(str(deepcopy(self))))
        fname = self.oid + '.tsv'
        with open(os.path.join(orb.data_store, fname), 'w') as f:
            # header line
            ser_schema = ['oid']
            ser_schema += self.schema
            schema_out = '\t'.join(ser_schema) + '\n'
            orb.log.debug('  - writing schema: {}'.format(schema_out))
            f.write(schema_out)
            # add 'oid' column to data
            serialized_data = deepcopy(self)
            for oid, row in serialized_data.items():
                for de, val in self.schema:
                    row[de] = cookers[(de_defz[de]['range_datatype'],
                                       True)](row[de])
                row['oid'] = oid
            # data
            data_out = '\n'.join(['\t'.join([row[de] for de in ser_schema])
                                   for row in serialized_data])
            orb.log.debug('    + writing data: {}'.format(data_out))
            f.writelines(data_out)
            # I like a final line-ending char :)
            f.write('\n')

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

