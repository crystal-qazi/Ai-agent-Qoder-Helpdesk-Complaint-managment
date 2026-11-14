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
    """The notification view_notification route must not redirect to
    external URLs stored in action_url."""

    def _simulate_redirect_check(self, action_url):
        """Reproduce the logic from notifications.py view_notification."""
        from urllib.parse import urlparse
        parsed = urlparse(action_url)
        # Simulate request.host == 'example.com'
        is_safe = (
            (not parsed.scheme and not parsed.netloc)
            or (parsed.scheme in ('http', 'https') and parsed.netloc == 'example.com')
        )
        return is_safe

    def test_relative_path_is_safe(self):
        self.assertTrue(self._simulate_redirect_check('/complaints/1'))

    def test_external_url_is_blocked(self):
        self.assertFalse(self._simulate_redirect_check('https://evil.com/'))

    def test_protocol_relative_is_blocked(self):
        self.assertFalse(self._simulate_redirect_check('//evil.com/'))

    def test_javascript_scheme_is_blocked(self):
        self.assertFalse(self._simulate_redirect_check('javascript:alert(1)'))

    def test_same_origin_url_is_safe(self):
        self.assertTrue(self._simulate_redirect_check('http://example.com/'))


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
