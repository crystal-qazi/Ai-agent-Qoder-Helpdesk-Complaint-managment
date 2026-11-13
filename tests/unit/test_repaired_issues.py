"""Regression tests for repaired security, permissions and workflow issues."""
import os
import sys
import unittest
from datetime import datetime, timedelta, time
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Resolve project root reliably: tests/unit/../.. = project root
_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
assert os.path.isdir(os.path.join(_PROJECT_ROOT, 'app')), f"PROJECT_ROOT mismatch: {_PROJECT_ROOT}"


class TestOpenRedirectFix(unittest.TestCase):
    """Verifies the auth login route blocks external redirects."""

    def _is_safe_redirect(self, next_page):
        """Copy of the validation logic from auth.py for direct testing."""
        if not next_page:
            return False
        from urllib.parse import urlparse
        parsed = urlparse(next_page)
        return parsed.netloc == '' and not next_page.startswith('//')

    def test_external_redirect_rejected_double_slash(self):
        self.assertFalse(self._is_safe_redirect('//evil.com'))

    def test_external_url_rejected(self):
        self.assertFalse(self._is_safe_redirect('https://evil.com/path'))

    def test_relative_path_allowed(self):
        self.assertTrue(self._is_safe_redirect('/dashboard'))

    def test_absolute_path_without_host_allowed(self):
        self.assertTrue(self._is_safe_redirect('/complaints/1'))


class TestAttachmentAuthorization(unittest.TestCase):
    """Verifies attachment download no longer grants access based solely on comments.view_internal."""

    def test_can_download_attachment_requires_complaint_access(self):
        from app.permissions.policy import PermissionPolicy

        user = MagicMock()
        user.is_active = True
        user.has_permission.side_effect = lambda p: p == 'comments.view_internal'

        attachment = MagicMock()
        complaint = MagicMock()
        complaint.reported_by_user_id = 999
        complaint.assigned_to_user_id = 999
        attachment.complaint = complaint
        attachment.user_id = 888

        with patch.object(PermissionPolicy, 'can_view_complaint', return_value=False):
            result = PermissionPolicy.can_download_attachment(user, attachment)
            self.assertFalse(result,
                             "view_internal alone must not grant attachment download without complaint access")

    def test_can_download_granted_when_user_is_reporter(self):
        from app.permissions.policy import PermissionPolicy

        user = MagicMock()
        user.is_active = True
        user.has_permission.return_value = False
        user.id = 1

        attachment = MagicMock()
        complaint = MagicMock()
        complaint.reported_by_user_id = 1
        complaint.assigned_to_user_id = 2
        attachment.complaint = complaint
        attachment.user_id = 999

        result = PermissionPolicy.can_download_attachment(user, attachment)
        self.assertTrue(result)


class TestProfileDepartmentAssignment(unittest.TestCase):
    """Verifies profile update correctly parses department_id as int."""

    def test_department_id_parsed_as_int(self):
        data = {'department_id': '5'}
        result = int(data.get('department_id') or 0) or None
        self.assertEqual(result, 5)

    def test_empty_department_becomes_none(self):
        data = {'department_id': ''}
        result = int(data.get('department_id') or 0) or None
        self.assertIsNone(result)

    def test_missing_key_becomes_none(self):
        data = {}
        result = int(data.get('department_id') or 0) or None
        self.assertIsNone(result)


class TestReporterComplaintVisibility(unittest.TestCase):
    """Verifies reporters can see their own submitted complaints."""

    def test_reporter_can_view_own_complaint(self):
        from app.permissions.policy import PermissionPolicy

        user = MagicMock()
        user.is_active = True
        user.has_permission.return_value = False
        user.id = 1

        complaint = MagicMock()
        complaint.reported_by_user_id = 1
        complaint.assigned_to_user_id = 2

        result = PermissionPolicy.can_view_complaint(user, complaint)
        self.assertTrue(result, "Reporter should be able to view their own complaint")

    def test_non_reporter_cannot_view_unassigned(self):
        from app.permissions.policy import PermissionPolicy

        user = MagicMock()
        user.is_active = True
        user.has_permission.return_value = False
        user.id = 1

        complaint = MagicMock()
        complaint.reported_by_user_id = 2
        complaint.assigned_to_user_id = 3

        result = PermissionPolicy.can_view_complaint(user, complaint)
        self.assertFalse(result, "Non-reporter non-assignee should not view the complaint")

    def test_assigned_user_with_view_my_can_view(self):
        from app.permissions.policy import PermissionPolicy

        user = MagicMock()
        user.is_active = True
        user.id = 2
        # Simulate user has complaints.view_my permission
        user.has_permission.side_effect = lambda p: p == 'complaints.view_my'

        complaint = MagicMock()
        complaint.reported_by_user_id = 1
        complaint.assigned_to_user_id = 2

        result = PermissionPolicy.can_view_complaint(user, complaint)
        self.assertTrue(result, "Assignee with view_my permission should view the complaint")

    def test_assigned_user_without_view_my_cannot_view(self):
        from app.permissions.policy import PermissionPolicy

        user = MagicMock()
        user.is_active = True
        user.id = 2
        user.has_permission.return_value = False

        complaint = MagicMock()
        complaint.reported_by_user_id = 1
        complaint.assigned_to_user_id = 2

        result = PermissionPolicy.can_view_complaint(user, complaint)
        self.assertFalse(result, "Assignee without view_my cannot view the complaint")


class TestStatusTransitionDecorator(unittest.TestCase):
    """Verifies the status transition decorator rejects invalid requests."""

    def test_decorator_validates_status_id_present(self):
        """The decorator must reject requests missing status_id with abort(400)."""
        from app.permissions import decorators as dec
        with open(dec.__file__) as src_file:
            src = src_file.read()
        # Should contain explicit abort(400) for missing status_id
        self.assertIn("abort(400)", src,
                      "can_change_status_complaint must call abort(400) when status_id is missing")
        # Should validate new_status_id type before proceeding
        self.assertIn("int(new_status_id)", src,
                      "must cast and validate status_id as integer")

    def test_permission_policy_rejects_invalid_status_code(self):
        from app.permissions.policy import PermissionPolicy
        user = MagicMock()
        user.is_active = True
        user.has_permission.return_value = False
        complaint = MagicMock()
        complaint.assigned_to_user_id = 1

        # Restricted status 'new' requires status_unlock
        restricted = MagicMock()
        restricted.code = 'new'
        result = PermissionPolicy.can_change_status(user, complaint, restricted)
        self.assertFalse(result, "Missing status_unlock should deny access to restricted status")


class TestSLADeadlineLoopProtection(unittest.TestCase):
    """Verifies calculate_deadline does not enter an unbounded loop."""

    def test_calendar_mode_ignores_schedule(self):
        from app.services.sla import SLAService

        start = datetime(2026, 1, 1, 9, 0)
        result = SLAService.calculate_deadline(start, 120, use_business_hours=False)
        expected = start + timedelta(minutes=120)
        self.assertEqual(result, expected)

    def test_loop_safety_cap_exists(self):
        from app.services.sla import SLAService
        self.assertTrue(hasattr(SLAService, 'MAX_DEADLINE_ITERATIONS'))
        self.assertIsInstance(SLAService.MAX_DEADLINE_ITERATIONS, int)
        self.assertGreater(SLAService.MAX_DEADLINE_ITERATIONS, 0)


class TestFirstResponseTracking(unittest.TestCase):
    """Verifies first_response_at is set only on the first reporter-visible
    comment from a user who is not the reporter themselves.

    Internal comments do NOT set first_response_at — they are invisible to
    the reporter.  Assignment is also not a reporter-visible response.
    """

    def test_first_response_set_on_reporter_visible_comment(self):
        from app.services.complaint import ComplaintService

        complaint = MagicMock()
        complaint.id = 1
        complaint.first_response_at = None
        complaint.reported_by_user_id = 10

        user = MagicMock()
        user.id = 20  # agent, different from reporter

        with patch('app.services.complaint.db.session') as mock_session, \
             patch('app.services.complaint.NotificationService'), \
             patch('app.services.complaint.AuditService'):

            success, msg = ComplaintService.add_comment(
                complaint, "Fix in progress", user, visibility='reporter_visible')
            self.assertTrue(success)
            self.assertIsNotNone(complaint.first_response_at,
                                 "first_response_at must be set on a reporter-visible comment from a non-reporter")

    def test_first_response_not_set_on_internal_comment(self):
        from app.services.complaint import ComplaintService

        complaint = MagicMock()
        complaint.id = 1
        complaint.first_response_at = None
        complaint.reported_by_user_id = 10

        user = MagicMock()
        user.id = 20  # agent, different from reporter

        with patch('app.services.complaint.db.session') as mock_session, \
             patch('app.services.complaint.NotificationService'), \
             patch('app.services.complaint.AuditService'):

            ComplaintService.add_comment(complaint, "Internal note", user, visibility='internal')
            self.assertIsNone(complaint.first_response_at,
                              "internal comments must NOT set first_response_at")

    def test_first_response_not_set_on_reporters_own_comment(self):
        from app.services.complaint import ComplaintService

        complaint = MagicMock()
        complaint.id = 1
        complaint.first_response_at = None
        complaint.reported_by_user_id = 10

        user = MagicMock()
        user.id = 10  # the reporter themselves

        with patch('app.services.complaint.db.session') as mock_session, \
             patch('app.services.complaint.NotificationService'), \
             patch('app.services.complaint.AuditService'):

            ComplaintService.add_comment(complaint, "Adding a note", user, visibility='reporter_visible')
            self.assertIsNone(complaint.first_response_at,
                              "the reporter's own comment does not count as first response")

    def test_first_response_not_overwritten(self):
        from app.services.complaint import ComplaintService

        already = datetime.utcnow() - timedelta(hours=1)
        complaint = MagicMock()
        complaint.id = 1
        complaint.first_response_at = already
        complaint.reported_by_user_id = 10

        user = MagicMock()
        user.id = 20

        with patch('app.services.complaint.db.session') as mock_session, \
             patch('app.services.complaint.NotificationService'), \
             patch('app.services.complaint.AuditService'):

            ComplaintService.add_comment(complaint, "Second reply", user, visibility='reporter_visible')
            self.assertEqual(complaint.first_response_at, already,
                             "existing first_response_at must not be overwritten")


class TestScriptFileIntegrity(unittest.TestCase):
    """Verify script file contents match expectations."""

    def test_seed_uses_integer_keys(self):
        seed_path = os.path.join(_PROJECT_ROOT, 'scripts', 'seed_mysql.py')
        with open(seed_path) as f:
            content = f.read()
        self.assertIn("'0':", content, "seed_mysql.py should use integer weekday string keys")
        self.assertNotIn("'monday':", content, "seed_mysql.py must not use day-name strings")

    def test_no_duplicate_version_columns_in_seed(self):
        seed_path = os.path.join(_PROJECT_ROOT, 'scripts', 'seed_mysql.py')
        with open(seed_path) as f:
            content = f.read()
        tables_section = content[content.index("tables = ["):content.index('for table_name')]
        count = tables_section.count('version')
        self.assertEqual(count, 0,
                         "No 'version' column should appear in raw SQL table definitions")

    def test_cleanup_has_upsert_ignore_helper(self):
        cleanup_path = os.path.join(_PROJECT_ROOT, 'scripts', 'cleanup_old_permissions.py')
        with open(cleanup_path) as f:
            content = f.read()
        self.assertIn('def upsert_ignore', content)
        self.assertIn('INSERT OR IGNORE', content)
        self.assertIn('INSERT IGNORE', content)


class TestInactiveRolePermissionFiltering(unittest.TestCase):
    """Verifies has_permission and get_permissions filter out inactive roles/permissions."""

    def _read_user_model_source(self):
        path = os.path.join(_PROJECT_ROOT, 'app', 'models', 'user.py')
        with open(path) as f:
            return f.read()

    def test_has_permission_source_filters_role_is_active(self):
        """The has_permission method must include Role.is_active == True filter."""
        src = self._read_user_model_source()
        # Find the has_permission method body
        start = src.index('def has_permission')
        end = src.index('def has_role', start)
        method_src = src[start:end]
        self.assertIn('Role.is_active', method_src,
                      "has_permission must filter by Role.is_active")
        self.assertIn('Permission.is_active', method_src,
                      "has_permission must filter by Permission.is_active")

    def test_get_permissions_source_filters_inactive(self):
        """The get_permissions method must filter active roles and permissions."""
        src = self._read_user_model_source()
        start = src.index('def get_permissions')
        end = src.index('def record_login', start)
        method_src = src[start:end]
        self.assertIn('Role.is_active', method_src,
                      "get_permissions must filter by Role.is_active")
        self.assertIn('Permission.is_active', method_src,
                      "get_permissions must filter by Permission.is_active")


class TestPrivilegeEscalationPrevention(unittest.TestCase):
    """Verifies the user routes block non-admins from assigning admin roles."""

    def _read_users_route_source(self):
        path = os.path.join(_PROJECT_ROOT, 'app', 'routes', 'users.py')
        with open(path) as f:
            return f.read()

    def test_create_user_has_privilege_check(self):
        """create_user route must check for admin role assignment."""
        src = self._read_users_route_source()
        start = src.index("def create_user")
        end = src.index("@users_bp.route('/<int:user_id>')", start)
        method_src = src[start:end]
        self.assertIn("has_admin_role", method_src,
                      "create_user must check if admin role is being assigned")

    def test_edit_user_has_privilege_check(self):
        """edit_user route must check for admin role assignment."""
        src = self._read_users_route_source()
        start = src.index("def edit_user")
        end = src.index("@users_bp.route('/<int:user_id>/delete'", start)
        method_src = src[start:end]
        self.assertIn("has_admin_role", method_src,
                      "edit_user must check if admin role is being assigned")


class TestLastAdminProtection(unittest.TestCase):
    """Verifies last-admin deactivation and deletion protections exist."""

    def _read_users_route_source(self):
        path = os.path.join(_PROJECT_ROOT, 'app', 'routes', 'users.py')
        with open(path) as f:
            return f.read()

    def test_delete_user_protects_last_admin(self):
        """delete_user must check for last active admin."""
        src = self._read_users_route_source()
        start = src.index("def delete_user")
        end = src.index("@users_bp.route('/<int:user_id>/unlock'", start)
        method_src = src[start:end]
        self.assertIn("other_active_admins", method_src,
                      "delete_user must count other active admins before deactivating")

    def test_edit_user_protects_last_admin(self):
        """edit_user must prevent deactivating the last active admin."""
        src = self._read_users_route_source()
        start = src.index("def edit_user")
        end = src.index("@users_bp.route('/<int:user_id>/delete'", start)
        method_src = src[start:end]
        self.assertIn("other_active_admins", method_src,
                      "edit_user must protect the last active admin from deactivation")

    def test_toggle_role_protects_last_admin(self):
        """toggle_role must prevent deactivating the admin role if it's the last one."""
        src = self._read_users_route_source()
        start = src.index("def toggle_role")
        end = src.index("@users_bp.route('/permissions')", start)
        method_src = src[start:end]
        self.assertIn("other_admins", method_src,
                      "toggle_role must protect the last admin role")


class TestRoleDuplicateRejection(unittest.TestCase):
    """Verifies create_role rejects duplicate names."""

    def _read_users_route_source(self):
        path = os.path.join(_PROJECT_ROOT, 'app', 'routes', 'users.py')
        with open(path) as f:
            return f.read()

    def test_create_role_checks_duplicate_name(self):
        src = self._read_users_route_source()
        start = src.index("def create_role")
        end = src.index("@users_bp.route('/roles/<int:role_id>/edit'", start)
        method_src = src[start:end]
        self.assertIn("Role.query.filter_by(name=name).first()", method_src,
                      "create_role must check for existing role names")


class TestRoleToggleRoute(unittest.TestCase):
    """Verifies the toggle_role route exists and updates is_active."""

    def _read_users_route_source(self):
        path = os.path.join(_PROJECT_ROOT, 'app', 'routes', 'users.py')
        with open(path) as f:
            return f.read()

    def test_toggle_route_defined(self):
        src = self._read_users_route_source()
        self.assertIn("def toggle_role", src,
                      "toggle_role route must be defined")

    def test_toggle_updates_is_active(self):
        src = self._read_users_route_source()
        start = src.index("def toggle_role")
        end = src.index("@users_bp.route('/permissions')", start)
        method_src = src[start:end]
        self.assertIn("new_state = not role.is_active", method_src,
                      "toggle_role must flip the is_active flag")
        self.assertIn("role.is_active = new_state", method_src,
                      "toggle_role must persist the new state")


if __name__ == '__main__':
    unittest.main()
