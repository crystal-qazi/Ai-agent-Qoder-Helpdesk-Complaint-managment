"""Regression tests for fixes applied in the security hardening follow-up.

Covers:
  * Open redirect in notification action_url
  * SLA policy reference in working schedule deletion
  * Missing comma in reset_and_seed.py
  * Uploader download access for confidential attachments
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, _PROJECT_ROOT)


class TestNotificationOpenRedirect(unittest.TestCase):
    """Exercise the exact validator used by the notification route."""

    def setUp(self):
        from app.routes.notifications import _safe_internal_redirect_target
        self.validate = _safe_internal_redirect_target

    def test_absolute_internal_path_is_safe(self):
        self.assertEqual(self.validate('/complaints/1', 'example.com'), '/complaints/1')

    def test_external_and_protocol_relative_urls_are_blocked(self):
        self.assertIsNone(self.validate('https://evil.test/', 'example.com'))
        self.assertIsNone(self.validate('//evil.test/', 'example.com'))

    def test_unsafe_schemes_are_blocked(self):
        self.assertIsNone(self.validate('javascript:alert(1)', 'example.com'))
        self.assertIsNone(self.validate('data:text/html,bad', 'example.com'))

    def test_same_origin_absolute_url_is_safe(self):
        self.assertEqual(
            self.validate('https://example.com/complaints/1', 'example.com'),
            'https://example.com/complaints/1',
        )

    def test_host_suffix_and_userinfo_attacks_are_blocked(self):
        self.assertIsNone(self.validate('https://example.com.evil.test/', 'example.com'))
        self.assertIsNone(self.validate('https://example.com@evil.test/', 'example.com'))

    def test_backslash_and_encoded_backslash_are_blocked(self):
        self.assertIsNone(self.validate('\\\\evil.test/path', 'example.com'))
        self.assertIsNone(self.validate('/%5c%5cevil.test/path', 'example.com'))

    def test_relative_reference_without_leading_slash_is_blocked(self):
        self.assertIsNone(self.validate('complaints/1', 'example.com'))

    def test_whitespace_and_control_characters_are_blocked(self):
        self.assertIsNone(self.validate(' /complaints/1', 'example.com'))
        self.assertIsNone(self.validate('/complaints/1\r\nLocation:https://evil.test', 'example.com'))


class TestWorkingScheduleDeleteSLAReference(unittest.TestCase):
    """delete_working_schedule must use a direct SLAPolicy query, not a
    nonexistent backref relationship."""

    def test_no_backref_reference_in_source(self):
        path = os.path.join(_PROJECT_ROOT, 'app', 'routes', 'admin.py')
        with open(path) as f:
            src = f.read()
        # The bug: schedule.sla_policies.count() would crash
        self.assertNotIn('schedule.sla_policies.count()', src,
                         'must not use nonexistent backref relationship')
        # The fix: direct query on SLAPolicy
        self.assertIn('SLAPolicy.query.filter_by(working_schedule_id=schedule.id', src,
                      'must use direct SLAPolicy query')


class TestResetAndSeedSyntax(unittest.TestCase):
    """reset_and_seed.py must compile without SyntaxWarning."""

    def test_no_missing_comma_in_permissions(self):
        import py_compile
        import warnings
        path = os.path.join(_PROJECT_ROOT, 'scripts', 'reset_and_seed.py')
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            py_compile.compile(path, doraise=True)


class TestConfidentialUploaderDownload(unittest.TestCase):
    """Uploader must always be able to download their own confidential
    attachment, even if they lack complaint view permissions."""

    def test_uploader_can_download_confidential_even_without_complaint_view(self):
        from app.permissions.policy import PermissionPolicy

        user = MagicMock()
        user.is_active = True
        user.id = 3
        user.has_permission.return_value = False

        complaint = MagicMock()
        complaint.reported_by_user_id = 1
        complaint.assigned_to_user_id = 2
        complaint.is_confidential = True

        attachment = MagicMock()
        attachment.user_id = 3  # uploader
        attachment.complaint = complaint
        attachment.is_confidential = True

        # Uploader check runs first, so can_view_complaint is never reached
        result = PermissionPolicy.can_download_attachment(user, attachment)
        self.assertTrue(result,
                        'uploader must always be able to download their own files')


if __name__ == '__main__':
    unittest.main()
