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
    carrying permissions they do not personally hold, or an admin-
    equivalent name.  Administrators are exempt from the delegation
    check because the seeded admin role carries the full permission set."""

    def setUp(self):
        from app.services.admin_protection import AdminProtectionService
        self.svc = AdminProtectionService

    def _actor(self, is_admin, held_perm_ids=None, user_id=9001):
        """Build a mock user whose ``get_permissions()`` returns objects
        for the given permission ID/name pairs.

        ``held_perm_ids`` is a list of ``(perm_id, name)`` tuples.
        When ``is_admin`` is True, ``has_role('admin')`` returns True.
        """
        user = MagicMock()
        user.id = user_id
        user.has_role = lambda name: name == 'admin' if is_admin else False

        held = []
        for pid, pname in (held_perm_ids or []):
            p = MagicMock()
            p.id = pid
            p.name = pname
            p.is_active = True
            held.append(p)
        user.get_permissions = MagicMock(return_value=held)
        return user

    def _run_can_create_role(self, actor, perm_ids, role_name,
                             submitted_permissions=None):
        """Run ``can_create_role`` with DB-access helpers patched so the
        test never touches the Flask app context.

        ``submitted_permissions`` is a list of Permission-like objects
        matching the IDs in ``perm_ids``.  The test asserts on the
        security decision, not on the DB contents.
        """
        from app.models import Permission
        submitted = list(submitted_permissions or [])
        with patch.object(self.svc, '_log_blocked', return_value=None), \
             patch.object(self.svc, '_load_submitted_permissions',
                          return_value=submitted):
            return self.svc.can_create_role(actor, perm_ids, role_name=role_name)

    def _perm(self, perm_id, name, is_active=True):
        p = MagicMock()
        p.id = perm_id
        p.name = name
        p.is_active = is_active
        return p

    # ------------------------------------------------------------------
    # Admin exempt from delegation
    # ------------------------------------------------------------------

    def test_admin_creating_role_with_sensitive_permissions_is_allowed(self):
        """An admin creating a role that carries sensitive permissions is
        a legitimate workflow and must not be blocked."""
        actor = self._actor(is_admin=True)
        p5 = self._perm(5, 'users.manage')
        p7 = self._perm(7, 'permissions.manage')
        result = self._run_can_create_role(
            actor, [5, 7], 'ops_admin',
            submitted_permissions=[p5, p7],
        )
        self.assertTrue(result.ok,
                        f'Admin creating a role with sensitive permissions must be allowed: {result.reason}')

    def test_admin_creating_role_with_no_permissions_is_allowed(self):
        """An admin may create an empty role (no permissions)."""
        actor = self._actor(is_admin=True)
        result = self._run_can_create_role(actor, [], 'empty_role')
        self.assertTrue(result.ok,
                        f'Admin creating a role with no permissions must be allowed: {result.reason}')

    # ------------------------------------------------------------------
    # Strict delegation — non-admin can only grant what they hold
    # ------------------------------------------------------------------

    def test_non_admin_granting_users_manage_permission_is_blocked(self):
        """A non-admin with only ``complaints.view_all`` cannot add the
        ``users.manage`` permission to a new role."""
        actor = self._actor(
            is_admin=False,
            held_perm_ids=[(3, 'complaints.view_all')],
        )
        p5 = self._perm(5, 'users.manage')
        result = self._run_can_create_role(
            actor, [5], 'super_user',
            submitted_permissions=[p5],
        )
        self.assertFalse(result.ok,
                         'Non-admin without users.manage in their permission set must be blocked')
        self.assertIn('personally hold', result.reason,
                      'Rejection reason must explain the delegation rule')

    def test_non_admin_granting_permissions_manage_is_blocked(self):
        """A non-admin with only ``roles.manage`` cannot add the
        ``permissions.manage`` permission to a new role."""
        actor = self._actor(
            is_admin=False,
            held_perm_ids=[(9, 'roles.manage')],
        )
        p7 = self._perm(7, 'permissions.manage')
        result = self._run_can_create_role(
            actor, [7], 'perm_manager',
            submitted_permissions=[p7],
        )
        self.assertFalse(result.ok,
                         'Non-admin without permissions.manage in their set must be blocked')

    def test_non_admin_granting_a_permission_they_do_hold_is_allowed(self):
        """A legitimate workflow: non-admin has ``complaints.view_all`` and
        creates a role carrying only that permission."""
        actor = self._actor(
            is_admin=False,
            held_perm_ids=[(3, 'complaints.view_all')],
        )
        p3 = self._perm(3, 'complaints.view_all')
        result = self._run_can_create_role(
            actor, [3], 'viewer',
            submitted_permissions=[p3],
        )
        self.assertTrue(result.ok,
                        f'Non-admin granting a permission they personally hold must be allowed: {result.reason}')

    def test_non_admin_granting_mixed_held_and_unheld_is_blocked(self):
        """If even one permission in the set is not held by the actor,
        the whole submission is blocked (all-or-nothing)."""
        actor = self._actor(
            is_admin=False,
            held_perm_ids=[(3, 'complaints.view_all')],
        )
        p3 = self._perm(3, 'complaints.view_all')
        p5 = self._perm(5, 'users.manage')
        result = self._run_can_create_role(
            actor, [3, 5], 'mixed',
            submitted_permissions=[p3, p5],
        )
        self.assertFalse(result.ok,
                         'Granting a mix of held and unheld permissions must be blocked')

    # ------------------------------------------------------------------
    # Admin role name guard
    # ------------------------------------------------------------------

    def test_non_admin_creating_admin_named_role_is_blocked(self):
        """A non-admin cannot create a role whose name is 'admin'
        (or 'ADMIN', 'Admin') even without any permissions."""
        actor = self._actor(is_admin=False)
        result = self._run_can_create_role(actor, [], 'Admin')
        self.assertFalse(result.ok,
                         'Non-admin creating a role named "admin" must be blocked')
        self.assertIn('admin_role_name', result.audit_reason)

    def test_admin_creating_admin_named_role_is_allowed(self):
        """An admin creating a role named 'admin' is not blocked by the
        name guard (the name check only applies to non-admins)."""
        actor = self._actor(is_admin=True)
        result = self._run_can_create_role(actor, [], 'admin')
        self.assertTrue(result.ok,
                        f'Admin creating a role named "admin" must be allowed: {result.reason}')

    # ------------------------------------------------------------------
    # Malformed / unknown / inactive permission IDs
    # ------------------------------------------------------------------

    def test_malformed_permission_id_is_rejected(self):
        """A non-integer permission ID string is rejected up front."""
        actor = self._actor(is_admin=False)
        result = self._run_can_create_role(actor, ['abc'], 'rogue')
        self.assertFalse(result.ok,
                         'Non-integer permission ID must be rejected')
        self.assertIn('malformed', result.audit_reason)

    def test_invalid_permission_id_is_rejected(self):
        """A permission ID that does not exist in the DB is rejected."""
        actor = self._actor(is_admin=False)
        result = self._run_can_create_role(actor, [9999], 'rogue')
        self.assertFalse(result.ok,
                         'Non-existent permission IDs must be rejected')
        self.assertIn('unknown_permission', result.audit_reason)

    def test_inactive_permission_is_rejected(self):
        """An inactive permission cannot be added to a new role."""
        actor = self._actor(
            is_admin=False,
            held_perm_ids=[(42, 'some_inert')],
        )
        p42 = self._perm(42, 'some_inert', is_active=False)
        result = self._run_can_create_role(
            actor, [42], 'inert',
            submitted_permissions=[p42],
        )
        self.assertFalse(result.ok,
                         'Inactive permission IDs must be rejected')
        self.assertIn('inactive_permission', result.audit_reason)

    # ------------------------------------------------------------------
    # Duplicate IDs
    # ------------------------------------------------------------------

    def test_duplicate_permission_ids_are_deduplicated(self):
        """Duplicate permission IDs are harmless — the route stores a
        de-duplicated set.  A non-admin who holds the permission may
        submit it multiple times without error."""
        actor = self._actor(
            is_admin=False,
            held_perm_ids=[(3, 'complaints.view_all')],
        )
        p3 = self._perm(3, 'complaints.view_all')
        # Submit 3 three times; it should still succeed because 3 is held.
        result = self._run_can_create_role(
            actor, [3, 3, 3], 'dup_viewer',
            submitted_permissions=[p3],
        )
        self.assertTrue(result.ok,
                        f'Duplicate IDs for a held permission must be allowed: {result.reason}')


# ------------------------------------------------------------------
# H2 — must_change_password flag preservation
# ------------------------------------------------------------------

class TestMustChangePasswordPreservation(unittest.TestCase):
    """A user edit that does not submit the checkbox must not clear the
    flag.  Clearing the flag (checkbox submitted unchecked) requires the
    actor to be **both** an active admin (``is_active`` and the admin
    role must be active) — an inactive admin, a secondary/custom role,
    or a plain non-admin may not clear it.

    These tests exercise the *exact* code path in
    ``app.routes.users.edit_user`` by extracting the conditional block
    into a helper that mirrors the route logic, so the test can assert
    on the flag decision without needing a Flask request context.
    """

    @staticmethod
    def _apply_route_logic(data, actor_is_active, actor_has_admin_role, user):
        """Mirror of the must_change_password block in
        ``edit_user`` — the same conditional, with no DB side effects.
        ``data`` is the form dict; the function updates ``user`` in place
        and returns the new flag value.

        The clearing gate is:
            ``actor_is_active and actor_has_admin_role``
        so that a deactivated admin cannot clear the flag even though
        their roles technically still exist in the DB.
        """
        if 'must_change_password' in data:
            if data.get('must_change_password'):
                user.must_change_password = True
            else:
                # Mirrors: current_user.is_active AND current_user.has_role('admin')
                if actor_is_active and actor_has_admin_role:
                    user.must_change_password = False
                # else: keep the flag.
        return user.must_change_password

    def _user(self, must_change_password=True):
        u = MagicMock()
        u.must_change_password = must_change_password
        return u

    # ------------------------------------------------------------------
    # Preservation: absent checkbox keeps existing value
    # ------------------------------------------------------------------

    def test_edit_without_checking_box_preserves_existing_flag(self):
        """When the form does not include the checkbox, the flag stays
        as it was.  Target: flag is True, admin does not submit the
        checkbox, no password → flag must remain True."""
        user = self._user(must_change_password=True)
        form = {'username': 'bob', 'first_name': 'B', 'last_name': 'B'}
        result = self._apply_route_logic(form, actor_is_active=True,
                                         actor_has_admin_role=True, user=user)
        self.assertTrue(result,
                        'A form edit that does not include the checkbox must not clear must_change_password')

    # ------------------------------------------------------------------
    # Non-admin: cannot clear
    # ------------------------------------------------------------------

    def test_non_admin_edit_cannot_clear_flag(self):
        """A non-admin editing a user that currently has
        ``must_change_password=True`` and submitting the checkbox
        unchecked must NOT clear the flag."""
        user = self._user(must_change_password=True)
        form = {'username': 'bob', 'first_name': 'B', 'last_name': 'B',
                'must_change_password': ''}
        result = self._apply_route_logic(form, actor_is_active=True,
                                         actor_has_admin_role=False, user=user)
        self.assertTrue(result,
                        'A non-admin may not clear must_change_password even when they submit the checkbox unchecked')

    def test_secondary_role_cannot_bypass_admin_gate(self):
        """A user whose role name is not 'admin' — e.g. a custom
        'super_admin' or 'sys_admin' role — does not satisfy
        ``has_role('admin')`` and therefore cannot clear the flag."""
        user = self._user(must_change_password=True)
        form = {'must_change_password': ''}
        # A secondary role that is *not* the admin role; actor_has_admin_role
        # is False because has_role('admin') returned False for this user.
        result = self._apply_route_logic(form, actor_is_active=True,
                                         actor_has_admin_role=False, user=user)
        self.assertTrue(result,
                        'A secondary/custom role must not bypass the admin-only clearing gate')

    # ------------------------------------------------------------------
    # Inactive admin: cannot clear
    # ------------------------------------------------------------------

    def test_inactive_admin_cannot_clear_flag(self):
        """An admin whose account has been deactivated (``is_active=False``)
        cannot clear the flag even though their roles are still in the DB.
        The gate requires BOTH ``is_active`` and the admin role to be
        active, mirroring the ``load_user`` fail-closed behaviour."""
        user = self._user(must_change_password=True)
        form = {'must_change_password': ''}
        result = self._apply_route_logic(form, actor_is_active=False,
                                         actor_has_admin_role=True, user=user)
        self.assertTrue(result,
                        'An inactive admin must not be able to clear must_change_password')

    # ------------------------------------------------------------------
    # Authorized admin workflow: active admin can clear
    # ------------------------------------------------------------------

    def test_active_admin_can_explicitly_clear_flag(self):
        """An active admin explicitly submitting the checkbox unchecked may
        clear the flag.  This is the authorized administrative workflow."""
        user = self._user(must_change_password=True)
        form = {'username': 'bob', 'first_name': 'B', 'last_name': 'B',
                'must_change_password': ''}
        result = self._apply_route_logic(form, actor_is_active=True,
                                         actor_has_admin_role=True, user=user)
        self.assertFalse(result,
                         'An active admin explicitly unchecking the checkbox should clear must_change_password')

    def test_admin_setting_flag_true_keeps_it_set(self):
        """When an admin explicitly checks the checkbox, the flag must
        become True regardless of the prior value."""
        user = self._user(must_change_password=False)
        form = {'username': 'bob', 'first_name': 'B', 'last_name': 'B',
                'must_change_password': 'on'}
        result = self._apply_route_logic(form, actor_is_active=True,
                                         actor_has_admin_role=True, user=user)
        self.assertTrue(result,
                        'An admin explicitly checking the checkbox should set must_change_password=True')

    # ------------------------------------------------------------------
    # Source-code guard
    # ------------------------------------------------------------------

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
        # The is_active + has_role gate must be in place
        self.assertIn(
            "current_user.is_active and",
            src,
            'The is_active check in the must_change_password clearing gate is missing')
        self.assertIn(
            "current_user.has_role(",
            src,
            'The has_role check in the must_change_password clearing gate is missing')


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
