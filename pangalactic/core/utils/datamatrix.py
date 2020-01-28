# -*- coding: utf-8 -*-
"""
Pan Galactic data matrix
"""
from collections import UserDict
from uuid import uuid4

# pangalactic
from pangalactic.core.parametrics import get_pval
from pangalactic.core.uberorb     import orb


class DataMatrix(UserDict):
    """
    A dictionary containing "rows", each of which is dictionary that maps
    columns ids to the corresponding values.  It has an attribute "schema" that
    is a dictionary of "column" definitions.
    """
    def __init__(self, oid=None, id='', owner_oid=None, schema=None,
                 data=None):
        super(DataMatrix, self).__init__(data)
        self.oid = oid or str(uuid4())
        self.id = id
        self.owner_oid = owner_oid
        self.schema = schema

    def load(self, data):
        """
        Reads a stored set of data (.tsv) and schema (.yaml) files.
        """
        pass

    def dump(self):
        """
        Writes `data` into an [id].tsv file and `schema` into an [id].yaml
        file.
        """
        # yaml.safe_dump(self.schema, orb.datamatrix_store)
        pass

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

