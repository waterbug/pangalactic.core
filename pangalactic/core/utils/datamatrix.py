# -*- coding: utf-8 -*-
"""
Pan Galactic data matrix
"""
import os
from collections import OrderedDict
from uuid        import uuid4

# pangalactic
from pangalactic.core.parametrics import get_pval
from pangalactic.core.uberorb     import orb


class DataMatrix(OrderedDict):
    """
    An OrderedDict that has dicts (rows) as values, and maps an 'oid' value to
    each row.  It has an attribute "schema", which is a list of data element
    identifiers which reference DataElementDefinitions cached in the "dedz"
    dict. Each dict maps data element ids in the schema to values.

    Keyword Args:
        schema (list): list of data element ids (column "names")
        dataset (DataSet): an associated DataSet instance
    """
    def __init__(self, *args, schema=None, dataset=None, **kw):
        super(DataMatrix, self).__init__(*args, **kw)
        self.dataset = dataset
        self.schema = schema or []

    @property
    def oid(self):
        return getattr(self.dataset, 'id', 'unknown-datamatrix')

    def load(self, f):
        """
        Load data from a datamatrix .tsv file.

        Args:
            f (file): file object for a .tsv file
        """
        first = f.readline()
        schema = first[:-1].split('\t')
        row_oids = True
        if schema[0] != 'oid':
            row_oids = False
        for line in f:
            data = line[:-1].split('\t')
            row_dict = {}
            for i, de in enumerate(schema):
                row_dict[de] = data[i]
            if not row_oids:
                oid = str(uuid4())
                row_dict['oid'] = oid
            self[oid] = row_dict

    def save(self):
        """
        Write my data into a .tsv file.
        """
        fname = self.dataset.id + '.tsv'
        serialization_schema = self.schema[:]
        serialization_schema.insert(0, 'oid')
        with open(os.path.join(orb.data_store, fname), 'w') as f:
            # header line
            f.write('\t'.join(serialization_schema) + '\n')
            # data
            f.writelines('\n'.join(['\t'.join(
                         [str(self[r_oid].get(de, ''))
                          for de in serialization_schema])
                         for r_oid, r in self.items()]))
            # I like a final line-ending char :)
            f.write('\n')

    # NOTE: this code is just a copy of the code in reports.py for MEL
    # generation -- needs to be adapted/generalized ...
    def refresh(self, context):
        """
        Refresh generated parameters related to a 'context' (Project or
        Product) from which the generated values are obtained.

        Args:
            context (Project or Product):  the project or system to which the
                generated parameters pertain
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

