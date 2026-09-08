# -*- coding: utf-8 -*-
"""
Tests for access.may_add_system() -- who may say what a project's systems
are.

Adding a system to a project modifies the project, so the rule is 'modify'
on the Project, which get_perms() branch [3] already decides.  These cover
each answer it can give, and pin the roles:  Administrator, lead_engineer
and systems_engineer in the project's context, plus a global admin.

The STEP import dialog offered the option to everybody, and checked, which
invited a user to ask for something they were not authorized to do.
"""
import unittest

# set the orb
import pangalactic.core.set_uberorb

from pangalactic.core             import orb, state
from pangalactic.core.access      import may_add_system
from pangalactic.core.serializers import deserialize
from pangalactic.core.test.utils  import (create_test_users,
                                          create_test_project)

HOME = 'access_test'
orb.start(home=HOME)
deserialize(orb, create_test_users() + create_test_project())

# The test data's only H2G2 Administrator is "steve", who is also a *global*
# admin -- so testing with him cannot tell the project-role branch from the
# global one.  This is somebody who is only the former.
PROJECT_ADMIN = 'test:localadmin'


def make_project_admin():
    from pangalactic.core.clone import clone
    if orb.get(PROJECT_ADMIN) is None:
        clone('Person', oid=PROJECT_ADMIN, id='localadmin',
              name='A Project Administrator', first_name='Local',
              last_name='Admin')
        clone('RoleAssignment', oid='test:RA.localadmin_h2g2',
              id='localadmin_h2g2',
              assigned_role=orb.get('pgefobjects:Role.Administrator'),
              assigned_to=orb.get(PROJECT_ADMIN),
              role_assignment_context=orb.get('H2G2'))
        orb.db.commit()


class MayAddSystemTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        make_project_admin()

    def setUp(self):
        self.was_user = state.get('local_user_oid')
        # every rule below is about entitlement;  is_writable_now() would
        # otherwise withhold 'modify' from a "disconnected client"
        self.was_client = state.get('client')
        state['client'] = False

    def tearDown(self):
        state['local_user_oid'] = self.was_user
        state['client'] = self.was_client

    def project(self):
        return orb.get('H2G2')

    def test_01_a_systems_engineer_may(self):
        """CASE: systems_engineer on the project."""
        self.assertTrue(may_add_system(self.project(),
                                       user=orb.get('test:zaphod')))

    def test_02_a_project_administrator_may(self):
        """
        CASE: Administrator on the project, and nothing else.

        This is the case the rule could not answer until 2026-09-07:  the
        role set spelled it 'administrator' where the Role's id is
        'Administrator', so it matched nothing.
        """
        self.assertTrue(may_add_system(self.project(),
                                       user=orb.get(PROJECT_ADMIN)))

    def test_03_a_lead_engineer_may(self):
        """CASE: lead_engineer on the project."""
        self.assertTrue(may_add_system(self.project(),
                                       user=orb.get('test:carefulwalker')))

    def test_04_a_global_admin_may(self):
        """CASE: a global admin, by the branch above the role check."""
        self.assertTrue(may_add_system(self.project(),
                                       user=orb.get('test:steve')))

    def test_05_a_discipline_engineer_may_not(self):
        """
        CASE: propulsion_engineer on the project.  They may add and remove
        components of the propulsion subsystem;  that is a different act
        from declaring what the project's systems are.
        """
        self.assertFalse(may_add_system(self.project(),
                                        user=orb.get('test:buckaroo')))

    def test_06_no_user_and_no_project_are_refused(self):
        """CASE: nothing to ask about."""
        state['local_user_oid'] = ''
        expected = [False, False]
        value = [may_add_system(self.project()),          # no local user
                 may_add_system(None, user=orb.get('test:zaphod'))]
        self.assertEqual(expected, value)

    def test_07_the_local_user_is_used_when_none_is_given(self):
        """
        CASE: called with no user, as the dialog calls it -- the local user
        is looked up, the same way get_perms() does.
        """
        state['local_user_oid'] = 'test:zaphod'
        was_se = may_add_system(self.project())
        state['local_user_oid'] = 'test:buckaroo'
        was_pe = may_add_system(self.project())
        self.assertEqual([True, False], [was_se, was_pe])

    def test_08_anyone_may_add_a_system_to_the_sandbox(self):
        """
        CASE: the SANDBOX, which get_perms() answers before it reaches any
        role check -- "anyone can 'modify' the SANDBOX (i.e. add systems to
        it)".  Deferring to get_perms() inherits that, which is the point.
        """
        self.assertTrue(may_add_system(orb.get('pgefobjects:SANDBOX'),
                                       user=orb.get('test:buckaroo')))

    def test_09_a_disconnected_client_is_told_no(self):
        """
        CASE: the same entitled user, offline.  A disconnected client may
        write to an object it created (is_writable_now rule [4]) or holds a
        claim on (rule [1]), and a Project is neither -- PrepareForOfflineDialog
        does not offer Projects for check-out.  So the option is not shown
        during an offline import.  Recorded because it is a consequence of
        deferring to get_perms(), not a decision made here.
        """
        state['client'] = True
        state['connected'] = False
        try:
            value = may_add_system(self.project(),
                                   user=orb.get('test:zaphod'))
        finally:
            state['connected'] = True
        self.assertFalse(value)


if __name__ == '__main__':
    unittest.main()
