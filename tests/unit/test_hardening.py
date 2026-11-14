"""Behavioral tests for the security hardening work.

These tests cover:

  * AdminProtectionService: cross-admin stripping, admin-role edit, and
    non-admin blocking.
  * User model: lockout with bounded ``locked_until`` and auto-unlock.
  * File validator: path-traversal rejection, MIME sniffing, and
    confidential download restrictions.
  * AuditService redaction of secret-shaped fields.
  * Complaint edit policy: reporter edits, privileged scope, terminal
    status lock.
  * Auth config: ProductionConfig fails fast on weak or missing
    SECRET_KEY.

Run with the project virtualenv::

    .venv/Scripts/python.exe -m unittest \
        tests.unit.test_hardening -v
"""
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _fake_user(is_active=True, id=1, **role_perms):
    user = MagicMock()
    user.is_active = is_active
    user.id = id
    user.has_role.return_value = role_perms.get('has_role', False)
    user.has_permission.side_effect = lambda p: p in (role_perms.get('permissions', set()))
    return user


class TestAdminProtection(unittest.TestCase):
    """Behavioral tests against the real AdminProtectionService.

    The database is mocked so the tests do not require a live MySQL;
    the real code paths are exercised via the public methods and their
    documented side-effects.
    """

    def _admin_role(self):
        role = MagicMock()
        role.name = 'admin'
        role.id = 1
        role.is_active = True
        return role

    def test_cross_admin_strip_blocked_for_non_admin_actor(self):
        """A non-admin with users.manage cannot strip admin from another admin."""
        from app.services.admin_protection import AdminProtectionService

        admin_role = self._admin_role()
        target_admin = MagicMock()
        target_admin.id = 2
        target_admin.has_role.return_value = True
        target_admin.has_role.side_effect = lambda name: name == 'admin'
        target_admin.username = 'target_admin'

        actor = _fake_user(id=3, has_role=False,
                           permissions={'users.manage'})

        # Mock out the two DB queries the method performs:
        #   _require_admin_role → admin_role
        #   _lock_active_admins(exclude_user_id=2) → [] (no other active admin)
        with self._patch_service(
                admin_role=admin_role,
                lock_active_admins=[],
        ) as ctx:
            check = AdminProtectionService.can_remove_admin_role_from(
                target_admin, [], actor,
            )

        self.assertFalse(check.ok,
                         'non-admin actor must not be able to strip admin '
                         'from another admin')
        self.assertIn('administrator role', check.reason.lower())

    def test_last_admin_strip_blocked_even_for_self_actor(self):
        """Self-removal of the last admin role is blocked."""
        from app.services.admin_protection import AdminProtectionService
        admin_role = self._admin_role()
        target = MagicMock()
        target.id = 1
        target.has_role.side_effect = lambda name: name == 'admin'
        actor = _fake_user(id=1, has_role=True,
                            permissions={'users.manage', 'roles.manage'})

        with self._patch_service(admin_role=admin_role,
                                 lock_active_admins=[]):
            check = AdminProtectionService.can_remove_admin_role_from(
                target, [], actor,
            )
        self.assertFalse(check.ok,
                         'self-removal of the last admin role must be blocked')

    def test_admin_can_strip_admin_from_other_admin_when_backup_exists(self):
        """Active admin actor may strip admin from another admin as long
        as at least one other active admin remains."""
        from app.services.admin_protection import AdminProtectionService
        admin_role = self._admin_role()
        target = MagicMock()
        target.id = 2
        target.has_role.side_effect = lambda name: name == 'admin'
        target.username = 'other_admin'
        actor = _fake_user(id=1, has_role=True,
                            permissions={'users.manage', 'roles.manage'})
        other_admin = MagicMock()
        other_admin.id = 3

        with self._patch_service(admin_role=admin_role,
                                 lock_active_admins=[other_admin]):
            check = AdminProtectionService.can_remove_admin_role_from(
                target, [], actor,
            )
        self.assertTrue(check.ok,
                        'admin may strip admin from another admin when '
                        'a backup admin remains')

    def test_admin_role_edit_blocked_for_non_admin(self):
        """Only active admins may edit the admin role's permission set."""
        from app.services.admin_protection import AdminProtectionService
        admin_role = self._admin_role()
        actor = _fake_user(id=2, has_role=False,
                           permissions={'roles.manage'})

        with self._patch_service(admin_role=admin_role,
                                 lock_active_admins=[MagicMock()]):
            check = AdminProtectionService.can_edit_admin_role(
                actor, [], original_permission_ids=[5, 6], role_id=1,
            )
        self.assertFalse(check.ok,
                         'non-admin must not edit the admin role')

    def test_admin_role_edit_allowed_for_active_admin(self):
        from app.services.admin_protection import AdminProtectionService
        admin_role = self._admin_role()
        actor = _fake_user(id=1, has_role=True)

        # Provide the protected permission rows the new guard requires.
        protected_perms = []
        for i, name in enumerate(
            ['users.manage', 'roles.manage', 'permissions.manage',
             'settings.manage', 'config.manage', 'audit.view'],
            start=100,
        ):
            p = MagicMock()
            p.name = name
            p.id = i
            protected_perms.append(p)

        with self._patch_service(admin_role=admin_role,
                                 lock_active_admins=[MagicMock()]), \
             unittest.mock.patch('app.services.admin_protection.Permission') as MockPerm:
            MockPerm.query.filter.return_value.all.return_value = protected_perms
            check = AdminProtectionService.can_edit_admin_role(
                actor,
                [100, 101, 102, 103, 104, 105],  # all protected perms
                original_permission_ids=[5, 6], role_id=1,
            )
        self.assertTrue(check.ok,
                        'active admin may edit the admin role when all '
                        'protected permissions are retained')

    # ------------------------------------------------------------------
    def _patch_service(self, admin_role, lock_active_admins):
        """Context manager that patches _require_admin_role and
        _lock_active_admins on AdminProtectionService."""
        from contextlib import contextmanager
        from app.services import admin_protection

        @contextmanager
        def _ctx():
            original_require = admin_protection.AdminProtectionService._require_admin_role
            original_lock = admin_protection.AdminProtectionService._lock_active_admins
            original_log = admin_protection.AdminProtectionService._log_blocked

            admin_protection.AdminProtectionService._require_admin_role = \
                classmethod(lambda cls: admin_role)
            admin_protection.AdminProtectionService._lock_active_admins = \
                classmethod(lambda cls, exclude_user_id=None: lock_active_admins)
            admin_protection.AdminProtectionService._log_blocked = \
                classmethod(lambda *a, **kw: None)
            try:
                yield
            finally:
                admin_protection.AdminProtectionService._require_admin_role = original_require
                admin_protection.AdminProtectionService._lock_active_admins = original_lock
                admin_protection.AdminProtectionService._log_blocked = original_log

        return _ctx()


class TestUserLockout(unittest.TestCase):
    """Lockout now has a bounded window (locked_until) and auto-unlocks."""

    def setUp(self):
        # record_failed_login calls db.session.add(self), which needs
        # an application context.  Build a minimal one with SQLite so
        # the test does not require MySQL.
        from app import create_app
        self._app = create_app('testing')
        self._ctx = self._app.app_context()
        self._ctx.push()

    def tearDown(self):
        self._ctx.pop()

    def test_failed_login_sets_bounded_locked_until(self):
        from app.models.user import User
        user = User()
        user.failed_login_attempts = 0
        user.is_locked = False
        user.record_failed_login(max_attempts=3, lockout_duration=300)
        self.assertEqual(user.failed_login_attempts, 1)
        self.assertFalse(user.is_locked)

        user.record_failed_login(max_attempts=3, lockout_duration=300)
        self.assertEqual(user.failed_login_attempts, 2)
        self.assertFalse(user.is_locked)

        user.record_failed_login(max_attempts=3, lockout_duration=300)
        self.assertEqual(user.failed_login_attempts, 3)
        self.assertTrue(user.is_locked)
        self.assertIsNotNone(user.locked_until)
        # Bounded: exactly lockout_duration seconds from now.
        delta = (user.locked_until - datetime.utcnow()).total_seconds()
        self.assertLessEqual(delta, 305)
        self.assertGreater(delta, 295)

    def test_auto_unlock_if_expired_releases_after_window(self):
        from app.models.user import User
        user = User()
        user.is_locked = True
        user.locked_until = datetime.utcnow() - timedelta(seconds=1)
        user.failed_login_attempts = 5
        user.auto_unlock_if_expired()
        self.assertFalse(user.is_locked)
        self.assertEqual(user.failed_login_attempts, 0)
        self.assertIsNone(user.locked_until)

    def test_auto_unlock_noop_when_not_locked(self):
        from app.models.user import User
        user = User()
        user.is_locked = False
        user.auto_unlock_if_expired()
        self.assertFalse(user.is_locked)


class TestFileValidatorPathTraversal(unittest.TestCase):
    """Upload validation rejects path-traversal payloads."""

    def _fake_file(self, filename, content=b'abc'):
        import io
        return io.BytesIO(content).__class__(filename), None

    def test_filename_with_dotdot_rejected(self):
        from app.validators.file import validate_file_upload
        from app import create_app
        from io import BytesIO

        # Simulate a malicious filename
        app = create_app('testing')
        with app.test_request_context():
            f = BytesIO(b'\x25\x50\x44\x46\x2d\x2d\x54\x65\x73\x74')
            f.filename = '../../etc/passwd.pdf'
            errors, info = validate_file_upload(f,
                                                allowed_extensions={'pdf'},
                                                max_size=1024)
            self.assertIn('file', errors)
            self.assertIn('path-traversal', errors['file'].lower())

    def test_normal_pdf_filename_accepted(self):
        from app.validators.file import validate_file_upload
        from app import create_app
        from io import BytesIO

        app = create_app('testing')
        with app.test_request_context():
            f = BytesIO(b'%PDF-1.4 a minimal test pdf')
            f.filename = 'report.pdf'
            errors, info = validate_file_upload(f,
                                                allowed_extensions={'pdf'},
                                                max_size=1024)
            self.assertNotIn('file', errors)
            self.assertEqual(info['mime_type'], 'application/pdf')
            self.assertEqual(info['extension'], 'pdf')

    def test_mime_mismatch_rejected(self):
        from app.validators.file import validate_file_upload
        from app import create_app
        from io import BytesIO

        app = create_app('testing')
        with app.test_request_context():
            f = BytesIO(b'%PDF-1.4 test pdf content')
            f.filename = 'report.png'  # .png but PDF content
            errors, info = validate_file_upload(f,
                                                allowed_extensions={'png', 'pdf'},
                                                max_size=1024)
            self.assertIn('file', errors)
            self.assertIn('does not match', errors['file'].lower())

    def test_empty_file_rejected(self):
        from app.validators.file import validate_file_upload
        from app import create_app
        from io import BytesIO

        app = create_app('testing')
        with app.test_request_context():
            f = BytesIO(b'')
            f.filename = 'empty.txt'
            errors, info = validate_file_upload(f,
                                                allowed_extensions={'txt'},
                                                max_size=1024)
            self.assertIn('file', errors)
            self.assertIn('empty', errors['file'].lower())


class TestAuditRedaction(unittest.TestCase):
    """AuditService redacts secret-shaped fields before writing rows."""

    def test_password_field_redacted(self):
        from app.services.audit import _redact_dict
        payload = {
            'username': 'alice',
            'password': 'hunter2',
            'old_password': 'oldpass',
            'session_token': 'abc123',
        }
        redacted = _redact_dict(payload)
        self.assertEqual(redacted['password'], '<redacted>')
        self.assertEqual(redacted['old_password'], '<redacted>')
        self.assertEqual(redacted['session_token'], '<redacted>')
        self.assertEqual(redacted['username'], 'alice')

    def test_bearer_token_pattern_redacted(self):
        from app.services.audit import _redact_dict
        redacted = _redact_dict({'note': 'Bearer eyJabc123.xyz789'})
        self.assertEqual(redacted['note'], '<redacted>')

    def test_nested_list_redaction(self):
        from app.services.audit import _redact_dict
        redacted = _redact_dict({'items': [{'token': 'x'}, {'name': 'ok'}]})
        self.assertEqual(redacted['items'][0]['token'], '<redacted>')
        self.assertEqual(redacted['items'][1]['name'], 'ok')


class TestComplaintEditPolicy(unittest.TestCase):
    """Reporter edits, privileged scope, and terminal-status locks."""

    def _complaint(self, code='new', status_id=1):
        complaint = MagicMock()
        complaint.id = 10
        complaint.status_id = status_id
        status = MagicMock()
        status.code = code
        complaint.status = status
        return complaint

    def test_reporter_can_edit_own_open_complaint(self):
        from app.permissions.policy import PermissionPolicy
        user = _fake_user(id=1, permissions=set())
        complaint = self._complaint('new')
        complaint.reported_by_user_id = 1
        self.assertTrue(PermissionPolicy.can_edit_complaint(user, complaint))

    def test_reporter_cannot_edit_terminal_complaint(self):
        from app.permissions.policy import PermissionPolicy
        user = _fake_user(id=1, permissions=set())
        complaint = self._complaint('closed')
        complaint.reported_by_user_id = 1
        # Terminal codes are closed/rejected/resolved.  The policy's
        # terminal check is case-sensitive; make sure the status's
        # ``code`` is exactly the terminal code string.
        self.assertEqual(complaint.status.code, 'closed')
        self.assertFalse(PermissionPolicy.can_edit_complaint(user, complaint))

    def test_privileged_user_with_view_all_can_edit_any_complaint(self):
        from app.permissions.policy import PermissionPolicy
        user = _fake_user(id=1,
                          permissions={'complaints.edit', 'complaints.view_all'})
        complaint = self._complaint('closed')
        complaint.reported_by_user_id = 2
        self.assertTrue(PermissionPolicy.can_edit_complaint(user, complaint))

    def test_unrelated_user_cannot_edit_complaint(self):
        from app.permissions.policy import PermissionPolicy
        user = _fake_user(id=9, permissions=set())
        complaint = self._complaint('new')
        complaint.reported_by_user_id = 1
        complaint.assigned_to_user_id = 2
        self.assertFalse(PermissionPolicy.can_edit_complaint(user, complaint))


class TestConfidentialDownload(unittest.TestCase):
    """Confidential attachments require complaint-scoped access."""

    def test_view_internal_alone_denied_for_confidential(self):
        from app.permissions.policy import PermissionPolicy
        user = _fake_user(id=3,
                          permissions={'comments.view_internal'})
        complaint = MagicMock()
        complaint.reported_by_user_id = 1
        complaint.assigned_to_user_id = 2
        attachment = MagicMock()
        attachment.user_id = 999
        attachment.complaint = complaint
        attachment.is_confidential = True
        with unittest.mock.patch.object(PermissionPolicy, 'can_view_complaint',
                                        return_value=False):
            self.assertFalse(PermissionPolicy.can_download_attachment(user, attachment))

    def test_uploader_can_download_confidential(self):
        from app.permissions.policy import PermissionPolicy
        user = _fake_user(id=3, permissions=set())
        complaint = MagicMock()
        complaint.reported_by_user_id = 1
        complaint.assigned_to_user_id = 2
        attachment = MagicMock()
        attachment.user_id = 3
        attachment.complaint = complaint
        attachment.is_confidential = True
        self.assertTrue(PermissionPolicy.can_download_attachment(user, attachment))

    def test_view_internal_granted_when_complaint_visible(self):
        from app.permissions.policy import PermissionPolicy
        user = _fake_user(id=3,
                          permissions={'comments.view_internal'})
        complaint = MagicMock()
        complaint.reported_by_user_id = 1
        complaint.assigned_to_user_id = 2
        attachment = MagicMock()
        attachment.user_id = 999
        attachment.complaint = complaint
        attachment.is_confidential = True
        with unittest.mock.patch.object(PermissionPolicy, 'can_view_complaint',
                                        return_value=True):
            self.assertTrue(PermissionPolicy.can_download_attachment(user, attachment))


class TestProductionConfigSecretValidation(unittest.TestCase):
    """ProductionConfig refuses weak or missing SECRET_KEY values.

    The check runs through :func:`app.config.validate_production_env`
    which is called by ``create_app`` when the config class is
    ``ProductionConfig``.  Here we test the function directly.
    """

    def _validate(self, config_instance):
        """Call the real production validator on a config object."""
        from app.config import validate_production_env
        validate_production_env(config_instance)

    def test_weak_secret_key_rejected(self):
        from app.config import ProductionConfig
        # Build a ProductionConfig instance with a weak secret and assert
        # the validator rejects it.
        cfg = ProductionConfig()
        cfg.SECRET_KEY = 'dev-secret-key-change-in-production'
        # The validator reads SECRET_KEY from the environment; patch it.
        with unittest.mock.patch.dict(os.environ, {'SECRET_KEY': 'dev-secret-key-change-in-production'}):
            with self.assertRaises(RuntimeError):
                self._validate(cfg)

    def test_empty_secret_key_rejected(self):
        from app.config import ProductionConfig
        cfg = ProductionConfig()
        with unittest.mock.patch.dict(os.environ, {'SECRET_KEY': ''}, clear=False):
            with self.assertRaises(RuntimeError):
                self._validate(cfg)

    def test_long_random_secret_key_accepted(self):
        from app.config import ProductionConfig
        cfg = ProductionConfig()
        # A 64-char hex value with no placeholder markers.
        with unittest.mock.patch.dict(os.environ, {'SECRET_KEY': 'a' * 64}, clear=False):
            self._validate(cfg)


class TestSafeNextRedirect(unittest.TestCase):
    """External redirects are rejected; relative paths are allowed."""

    def test_external_url_rejected(self):
        from app.routes.auth import _is_safe_next
        self.assertFalse(_is_safe_next('https://evil.com/'))

    def test_double_slash_host_rejected(self):
        from app.routes.auth import _is_safe_next
        self.assertFalse(_is_safe_next('//evil.com/'))

    def test_relative_path_allowed(self):
        from app.routes.auth import _is_safe_next
        self.assertTrue(_is_safe_next('/dashboard'))

    def test_javascript_uri_rejected(self):
        from app.routes.auth import _is_safe_next
        # javascript: URL has an empty netloc but the scheme is hostile.
        self.assertFalse(_is_safe_next('javascript:alert(1)'))


if __name__ == '__main__':
    unittest.main()
