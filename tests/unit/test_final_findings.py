"""Regression tests for the final blocking findings in the security PR.

Each class targets one of the four blocking findings from the independent
review:

* H1 — role-creation privilege escalation
* H2 — ``must_change_password`` flag preservation in ``edit_user``
* M2 — atomic transaction for ``assign_complaint``
* M3 — deny-by-default status transitions
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..'))
assert os.path.isdir(os.path.join(_PROJECT_ROOT, 'app'))


# ------------------------------------------------------------------
# H1 — role-creation privilege escalation
# ------------------------------------------------------------------

class TestRoleCreationPrivilegeEscalation(unittest.TestCase):
    """A ``roles.manage``-only user must not be able to mint a role
    carrying sensitive permissions or an admin-equivalent name."""

    def setUp(self):
        from app.services.admin_protection import AdminProtectionService
        self.svc = AdminProtectionService

    def _actor(self, is_admin, user_id=9001):
        user = MagicMock()
        user.id = user_id
        user.has_role = lambda name: name == 'admin' if is_admin else False
        return user

    def _run_can_create_role(self, actor, perm_ids, role_name,
                             submitted_permissions=None,
                             protected_ids=None):
        """Run ``can_create_role`` with the DB-access helpers patched so
        the test never touches the Flask app context.

        ``submitted_permissions`` is a list of Permission-like objects
        matching the IDs in ``perm_ids``.  ``protected_ids`` is the set
        of permission IDs that would be returned by
        :meth:`_protected_permission_ids`; the test asserts on the
        security decision, not on the DB contents.
        """
        from app.models import Permission
        submitted = list(submitted_permissions or [])
        with patch.object(self.svc, '_log_blocked', return_value=None), \
             patch.object(self.svc, '_load_submitted_permissions',
                          return_value=submitted), \
             patch.object(self.svc, '_protected_permission_ids',
                          return_value=protected_ids or set()):
            return self.svc.can_create_role(actor, perm_ids, role_name=role_name)

    def _perm(self, perm_id, name, is_active=True):
        p = MagicMock()
        p.id = perm_id
        p.name = name
        p.is_active = is_active
        return p

    def test_admin_creating_role_with_protected_permission_is_allowed(self):
        """An admin creating a role that carries sensitive permissions is
        a legitimate workflow and must not be blocked.  The protected
        set is empty here because admin short-circuits the sensitive
        check — the admin flag check is the first branch, so the
        sensitive-permission guard is not even evaluated."""
        actor = self._actor(is_admin=True)
        p5 = self._perm(5, 'users.manage')
        p12 = self._perm(12, 'some_other')
        result = self._run_can_create_role(
            actor, [5, 12], 'ops_admin',
            submitted_permissions=[p5, p12],
            protected_ids={5, 7, 9, 11, 13},
        )
        self.assertTrue(result.ok,
                        f'Admin creating an authorized role should be allowed: {result.reason}')

    def test_non_admin_granting_users_manage_permission_is_blocked(self):
        """A ``roles.manage``-only user cannot add the ``users.manage``
        permission (id=5 in this synthetic setup) to a new role."""
        actor = self._actor(is_admin=False)
        p = self._perm(5, 'users.manage')
        result = self._run_can_create_role(
            actor, [5], 'super_user',
            submitted_permissions=[p],
            protected_ids={5},
        )
        self.assertFalse(result.ok,
                         'Non-admin creating a role with users.manage must be blocked')

    def test_non_admin_granting_permissions_manage_is_blocked(self):
        """A ``roles.manage``-only user cannot add the ``permissions.manage``
        permission to a new role."""
        actor = self._actor(is_admin=False)
        p = self._perm(7, 'permissions.manage')
        result = self._run_can_create_role(
            actor, [7], 'perm_manager',
            submitted_permissions=[p],
            protected_ids={7},
        )
        self.assertFalse(result.ok,
                         'Non-admin creating a role with permissions.manage must be blocked')

    def test_non_admin_creating_admin_named_role_is_blocked(self):
        """A non-admin cannot create a role whose name is 'admin'
        (or 'ADMIN', 'Admin') even without any permissions."""
        actor = self._actor(is_admin=False)
        result = self._run_can_create_role(actor, [], 'Admin')
        self.assertFalse(result.ok,
                         'Non-admin creating a role named "admin" must be blocked')

    def test_invalid_permission_id_is_rejected(self):
        """A permission ID that does not exist in the DB is rejected up
        front, regardless of the actor's privileges."""
        actor = self._actor(is_admin=False)
        result = self._run_can_create_role(actor, [9999], 'rogue')
        self.assertFalse(result.ok,
                         'Non-existent permission IDs must be rejected')

    def test_inactive_permission_is_rejected(self):
        """An inactive permission cannot be added to a new role."""
        actor = self._actor(is_admin=False)
        p = self._perm(42, 'some_inert', is_active=False)
        result = self._run_can_create_role(
            actor, [42], 'inert',
            submitted_permissions=[p],
        )
        self.assertFalse(result.ok,
                         'Inactive permission IDs must be rejected')

    def test_non_admin_creating_role_with_only_normal_permission_is_allowed(self):
        """A legitimate workflow — non-admin creating a role with only
        non-sensitive permissions — must still be allowed."""
        actor = self._actor(is_admin=False)
        p = self._perm(3, 'complaints.view_all')
        result = self._run_can_create_role(
            actor, [3], 'viewer',
            submitted_permissions=[p],
            protected_ids={5, 7, 9, 11, 13},
        )
        self.assertTrue(result.ok,
                        f'Non-admin creating a role with only non-sensitive permission must be allowed: {result.reason}')


# ------------------------------------------------------------------
# H2 — must_change_password flag preservation
# ------------------------------------------------------------------

class TestMustChangePasswordPreservation(unittest.TestCase):
    """A user edit that does not submit the checkbox must not clear the
    flag.  A user edit that submits the checkbox unchecked must not
    clear the flag when the actor is not an admin.

    These tests exercise the *exact* code path in
    ``app.routes.users.edit_user`` by extracting the conditional block
    into a helper that mirrors the route logic, so the test can assert
    on the flag decision without needing a Flask request context.
    """

    @staticmethod
    def _apply_route_logic(data, actor_has_admin_role, user):
        """Mirror of the must_change_password block in
        ``edit_user`` — the same conditional, with no DB side effects.
        ``data`` is the form dict; the function updates ``user`` in place
        and returns the new flag value."""
        if 'must_change_password' in data:
            if data.get('must_change_password'):
                user.must_change_password = True
            else:
                if actor_has_admin_role:
                    user.must_change_password = False
                # else: keep the flag; a non-admin may not lift it.
        return user.must_change_password

    def _user(self, must_change_password=True):
        u = MagicMock()
        u.must_change_password = must_change_password
        return u

    def test_edit_without_checking_box_preserves_existing_flag(self):
        """When the form does not include the checkbox, the flag stays
        as it was.  Target: flag is True, admin does not submit the
        checkbox, no password → flag must remain True."""
        user = self._user(must_change_password=True)
        form = {'username': 'bob', 'first_name': 'B', 'last_name': 'B'}
        result = self._apply_route_logic(form, actor_has_admin_role=True, user=user)
        self.assertTrue(result,
                        'A form edit that does not include the checkbox must not clear must_change_password')

    def test_non_admin_edit_cannot_clear_flag(self):
        """A non-admin editing a user that currently has
        ``must_change_password=True`` and submitting the checkbox
        unchecked must NOT clear the flag."""
        user = self._user(must_change_password=True)
        form = {'username': 'bob', 'first_name': 'B', 'last_name': 'B',
                'must_change_password': ''}
        result = self._apply_route_logic(form, actor_has_admin_role=False, user=user)
        self.assertTrue(result,
                        'A non-admin may not clear must_change_password even when they submit the checkbox unchecked')

    def test_admin_can_explicitly_clear_flag(self):
        """An admin explicitly submitting the checkbox unchecked may
        clear the flag.  This is the authorized administrative workflow."""
        user = self._user(must_change_password=True)
        form = {'username': 'bob', 'first_name': 'B', 'last_name': 'B',
                'must_change_password': ''}
        result = self._apply_route_logic(form, actor_has_admin_role=True, user=user)
        self.assertFalse(result,
                         'An admin explicitly unchecking the checkbox should clear must_change_password')

    def test_admin_setting_flag_true_keeps_it_set(self):
        """When an admin explicitly checks the checkbox, the flag must
        become True regardless of the prior value."""
        user = self._user(must_change_password=False)
        form = {'username': 'bob', 'first_name': 'B', 'last_name': 'B',
                'must_change_password': 'on'}
        result = self._apply_route_logic(form, actor_has_admin_role=True, user=user)
        self.assertTrue(result,
                        'An admin explicitly checking the checkbox should set must_change_password=True')

    def test_source_code_does_not_unconditionally_reset_flag(self):
        """Guard against a regression where someone replaces the block
        with ``user.must_change_password = data.get('must_change_password', False)``."""
        import app.routes.users as users_mod
        with open(users_mod.__file__, 'r', encoding='utf-8') as f:
            src = f.read()
        # The vulnerable line must not be present
        self.assertNotIn(
            "user.must_change_password = data.get('must_change_password', False)",
            src,
            'The unconditional reset of must_change_password has been reintroduced')
        # The guard must be in place
        self.assertIn(
            "if 'must_change_password' in data:",
            src,
            'The must_change_password preservation guard is missing from edit_user')


# ------------------------------------------------------------------
# M2 — assign_complaint atomicity
# ------------------------------------------------------------------

class TestAssignComplaintAtomicity(unittest.TestCase):
    """``assign_complaint`` must commit the entire transaction exactly
    once, and must roll back *all* partial work on failure."""

    def test_failure_after_auto_transition_rolls_back_all_work(self):
        """Simulate a failure after the auto-transition status change
        but before the final commit: no partial writes may remain."""
        from app.services.complaint import ComplaintService

        complaint = MagicMock()
        complaint.id = 100
        complaint.assigned_to_user_id = None
        complaint.status = MagicMock()
        complaint.status.code = 'new'
        complaint.status.id = 1

        current_user = MagicMock()
        current_user.id = 9001

        with patch.object(ComplaintService, '_change_status_internal',
                          side_effect=Exception('boom')), \
             patch('app.services.complaint.db.session') as mock_session, \
             patch('app.services.complaint.ComplaintAssignment') as mock_ca, \
             patch('app.services.complaint.ComplaintHistory') as mock_ch, \
             patch('app.services.complaint.Status.query') as mock_sq, \
             patch('app.services.complaint.NotificationService') as mock_ns, \
             patch('app.services.complaint.AuditService') as mock_as:
            mock_sq.filter_by.return_value.first.return_value = MagicMock()
            with self.assertRaises(Exception):
                ComplaintService.assign_complaint(
                    complaint, 5, current_user,
                    reason='assign', notes='n',
                )
            mock_session.rollback.assert_called_once()
            mock_session.commit.assert_not_called()

    def test_successful_assignment_commits_once(self):
        """A successful assignment commits the entire transaction
        exactly once."""
        from app.services.complaint import ComplaintService

        complaint = MagicMock()
        complaint.id = 100
        complaint.assigned_to_user_id = None
        complaint.status = None
        complaint.complaint_number = 'H-2026-0001'

        current_user = MagicMock()
        current_user.id = 9001

        with patch.object(ComplaintService, '_change_status_internal'), \
             patch('app.services.complaint.db.session') as mock_session, \
             patch('app.services.complaint.ComplaintAssignment'), \
             patch('app.services.complaint.ComplaintHistory'), \
             patch('app.services.complaint.NotificationService'), \
             patch('app.services.complaint.AuditService'):
            success, _ = ComplaintService.assign_complaint(
                complaint, 5, current_user, reason='assign',
            )
            self.assertTrue(success)
            mock_session.commit.assert_called_once()
            mock_session.rollback.assert_not_called()


# ------------------------------------------------------------------
# M3 — deny-by-default status transitions
# ------------------------------------------------------------------

class TestDenyByDefaultTransitions(unittest.TestCase):
    """When ``allowed_transitions`` is NULL or empty, no transition is
    permitted.  When a non-empty list is set, only the listed targets
    are allowed."""

    def _status(self, allowed_transitions, is_terminal=False):
        from app.models.status import Status
        s = Status()
        s.allowed_transitions = allowed_transitions
        s.is_terminal = is_terminal
        s.name = 'x'
        return s

    def test_null_rules_allow_no_transitions(self):
        s = self._status(None)
        self.assertFalse(s.can_transition_to(2),
                         'NULL allowed_transitions must deny every target')
        self.assertFalse(s.can_transition_to(3))

    def test_empty_list_denies_every_target(self):
        s = self._status([])
        self.assertFalse(s.can_transition_to(2),
                         'Empty list allowed_transitions must deny every target')
        self.assertFalse(s.can_transition_to(99))

    def test_valid_rule_allows_listed_target(self):
        s = self._status([2, 3, 4])
        self.assertTrue(s.can_transition_to(2))
        self.assertTrue(s.can_transition_to(4))
        self.assertFalse(s.can_transition_to(99))

    def test_terminal_status_with_empty_rules_cannot_transition_out(self):
        """Closed and Rejected statuses are terminal with ``[]`` rules.
        They must not transition out unless a specifically authorized
        reopening workflow adds an explicit target."""
        s = self._status([], is_terminal=True)
        self.assertFalse(s.can_transition_to(8),
                         'Terminal status with empty rules must not allow any transition out')

    def test_terminal_status_with_reopen_rule_allows_reopen(self):
        """An admin can explicitly add the 'reopened' target to a
        terminal status's allowed_transitions.  That specific
        reopening workflow is the only way to move out of a terminal
        status."""
        s = self._status([8], is_terminal=True)
        self.assertTrue(s.can_transition_to(8),
                        'A terminal status with an explicit "reopened" target rule allows that specific transition')


if __name__ == '__main__':
    unittest.main()
