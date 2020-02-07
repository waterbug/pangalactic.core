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
from pangalactic.core.parametrics      import get_pval
from pangalactic.core.uberorb          import orb
from pangalactic.core.utils.datetimes  import dtstamp


class DataMatrix(OrderedDict):
    """
    An OrderedDict that has dicts (rows) as values, and maps a unique 'oid'
    value to each row.  It has an attribute "schema", which is a list of data
    element identifiers that reference DataElementDefinitions cached in the
    "dedz" dict. Each row dict maps data element ids in the schema to values.

    The intent is that a DataMatrix will be created using a DataSet instance
    and/or a schema.  Providing a DataSet implies that the DataMatrix has been
    saved and that its .tsv file is referenced by the file name in
    DataSet.has_representations[0].has_files[0].url, which it will attempt to
    load from the orb.data_store.  If no file by that name is found in the
    data_store, it will look for 'schema' and create an empty instance with
    that schema, or with a default schema if none is provided.

    Keyword Args:
        dataset (DataSet): an associated DataSet instance (only exists if the
            DataMatrix has been saved)
        schema (list): list of data element ids (column "names")
        project (Project): associated project (becomes the owner of the DataSet
            that is created when the DataMatrix is saved)
    """
    def __init__(self, *args, project=None, dataset=None, schema_name=None,
                 schema=None, **kw):
        super(DataMatrix, self).__init__(*args, **kw)
        sig = 'project={}, dataset={}, schema_name={}, schema={}'.format(
                                            getattr(project, 'id', 'None'),
                                            getattr(dataset, 'id', 'None'),
                                            str(schema_name),
                                            str(schema))
        orb.log.debug('* DataMatrix({})'.format(sig))
        self.schema = schema or []
        if not isinstance(project, orb.classes['Project']):
            project = orb.get('pgefobjects:SANDBOX')
        self.project = project
        got_data = False
        if isinstance(dataset, orb.classes['DataSet']):
            # we received a DataSet instance -- look for a corresponding file
            # in the data_store and load its data into the datamatrix ...
            try:
                fname = dataset.has_representations[0].has_files[0].url
            except:
                orb.log.debug('  - dataset did not reference a url;')
                orb.log.debug('    an empty instance will be created ...')
                fname = None
            if fname is not None:
                try:
                    self.load(fname)
                    self.dataset = dataset
                    if dataset.id.startswith(self.project.id):
                        self.schema_name = dataset.id[len(self.project.id):]
                    else:
                        self.schema_name = dataset.id
                    got_data = True
                except:
                    orb.log.debug('  - unable to load "{}".'.format(fname))
                    orb.log.debug('    empty DataMatrix will be created ...')
                finally:
                    if not got_data:
                        # DataSet was invalid -- delete it and its refs ...
                        to_delete = [dataset]
                        if dataset.has_representations:
                            reps = dataset.has_representations
                            to_delete += reps
                            for rep in reps:
                                if rep.has_files:
                                    to_delete += rep.has_files
                        orb.delete(to_delete)
        if not got_data:
            # look up schema if valid, or use "MEL" schema as default, for now
            if not config['dm_schemas'].get(schema_name):
                # if provided schema_name is not found, use 'MEL'
                schema_name = 'MEL'
            self.schema_name = schema_name
            self.schema = config['dm_schemas'][self.schema_name]
            # look for a saved DataMatrix with that project and schema_name:
            fname = project.id + '-' + schema_name + '.tsv'
            rep_file = orb.select('RepresentationFile', url=fname)
            if rep_file:
                dataset = getattr(getattr(rep_file, 'of_representation', None),
                                  'of_object', None)
                if dataset:
                    try:
                        self.load(fname)
                    except:
                        orb.log.debug('  - could not load saved datamatrix.')
        # add myself to the orb.data in-memory cache
        orb.data[self.oid] = self

    @property
    def oid(self):
        return self.project.id + '-' + self.schema_name

    def load(self, fname):
        """
        Load data from a datamatrix .tsv file.

        Args:
            fname (str): name of a DataMatrix .tsv file
        """
        # TODO: add exception handling:  empty file, etc.
        orb.log.debug('* dm.load({})'.format(fname))
        with open(os.path.join(orb.data_store, fname)) as f:
            first = f.readline()
            serialization_schema = first[:-1].split('\t')
            row_oids = True
            if serialization_schema[0] != 'oid':
                row_oids = False
                self.schema = serialization_schema[:]
            else:
                self.schema = serialization_schema[1:]
            orb.log.debug('  - schema: {}'.format(str(self.schema)))
            for line in f:
                data = line[:-1].split('\t')
                if len(data) == 1:
                    # this would be a final empty line
                    break
                row_dict = {}
                for i, de in enumerate(serialization_schema):
                    row_dict[de] = data[i]
                if row_oids:
                    oid = row_dict['oid']
                else:
                    oid = str(uuid4())
                    row_dict['oid'] = oid
                self[oid] = row_dict
            orb.log.debug('  - read {} row(s) of data.'.format(len(self) - 1))

    def save(self):
        """
        Write my data into a .tsv file.
        """
        orb.log.debug('* dm.save()')
        orb.log.debug('  full dm:')
        orb.log.debug('  {}'.format(str(deepcopy(self))))
        fname = self.oid + '.tsv'
        serialization_schema = self.schema[:]
        serialization_schema.insert(0, 'oid')
        with open(os.path.join(orb.data_store, fname), 'w') as f:
            # header line
            schema_out = '\t'.join(serialization_schema) + '\n'
            orb.log.debug('  - writing schema: {}'.format(schema_out))
            f.write(schema_out)
            # data
            data_out = '\n'.join(['\t'.join(
                         [str(self[r_oid].get(de, ''))
                          for de in serialization_schema])
                         for r_oid, r in self.items()])
            orb.log.debug('  - writing data: {}'.format(data_out))
            f.writelines(data_out)
            # I like a final line-ending char :)
            f.write('\n')
        # look for an existing dataset
        dataset = None
        rep_file = orb.select('RepresentationFile', url=fname)
        if rep_file:
            rep = rep_file.of_representation
            if rep:
                dataset = rep.of_object
        if not dataset:
            # create the associated DataSet, etc., to reference the file
            NOW = dtstamp()
            ADMIN = orb.get('pgefobjects:admin')
            DataSet = orb.classes['DataSet']
            ds_id = self.project.id + '-' + self.schema_name
            ds_oid = str(uuid4())
            self.dataset = DataSet(oid=ds_oid, id=ds_id, owner=self.project,
                                   creator=ADMIN, modifier=ADMIN,
                                   create_datetime=NOW, mod_datetime=NOW)
            Representation = orb.classes['Representation']
            rep_oid = str(uuid4())
            rep = Representation(oid=rep_oid, id=ds_id+'-representation',
                                 of_object=self.dataset,
                                 creator=ADMIN, modifier=ADMIN,
                                 create_datetime=NOW, mod_datetime=NOW)
            RepresentationFile = orb.classes['RepresentationFile']
            rep_file_oid = str(uuid4())
            rep_file = RepresentationFile(
                                oid=rep_file_oid,
                                id=ds_id+'-representation_file',
                                of_representation=rep, url=fname,
                                creator=ADMIN, modifier=ADMIN,
                                create_datetime=NOW, mod_datetime=NOW)
            orb.save([self.dataset, rep, rep_file])

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

