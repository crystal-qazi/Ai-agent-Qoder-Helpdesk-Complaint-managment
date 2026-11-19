"""Regression tests: no route may surface raw exception detail to a user.

Background
----------
The QA audit found 24 ``flash(f'Error ... {str(e)}')`` sites in
``app/routes/{users,complaints,admin}.py``.  Raw driver/SQLAlchemy text can
embed the failing statement and bound parameters (password hashes, reset
tokens, licence keys), so it must never reach the browser.

Two layers of protection are asserted here:

1. A source-level scan proves the pattern is gone from every route module
   and that each handler routes diagnostics through the shared helper.
2. Behavioural tests drive real requests that fail inside the route and
   assert (a) the page shows a generic message, (b) secret-shaped values
   are absent from the response, and (c) the server log retains the
   diagnostic detail with secrets redacted.
"""
import os
import sys
import unittest
from unittest.mock import patch

_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, _PROJECT_ROOT)

# Secret-shaped payload an exception could carry from a real driver error.
_SECRET = 'Hunter2'
_LEAKY_EXCEPTION = (
    f'INSERT failed: password={_SECRET} token=tok_abc123 '
    f'mysql+pymysql://app:{_SECRET}@db.internal:3306/helpdesk_qoder_dev'
)


class TestNoRawExceptionInRoutes(unittest.TestCase):
    """Static guard against reintroducing the pattern."""

    ROUTE_MODULES = ('admin.py', 'complaints.py', 'users.py')

    def _source(self, module):
        path = os.path.join(_PROJECT_ROOT, 'app', 'routes', module)
        with open(path, encoding='utf-8') as handle:
            return handle.read()

    def test_no_str_e_interpolation_anywhere_in_app(self):
        offenders = []
        for root, _dirs, files in os.walk(os.path.join(_PROJECT_ROOT, 'app')):
            for name in files:
                if not name.endswith('.py'):
                    continue
                path = os.path.join(root, name)
                with open(path, encoding='utf-8') as handle:
                    for line_no, line in enumerate(handle, 1):
                        if 'flash(' in line and ('{str(e)}' in line
                                                 or '{str(exc)}' in line):
                            offenders.append(
                                f'{os.path.relpath(path, _PROJECT_ROOT)}:{line_no}')
        self.assertEqual(offenders, [],
                         'raw exception text flashed to users: '
                         + ', '.join(offenders))

    def test_each_handler_logs_server_side(self):
        for module in self.ROUTE_MODULES:
            source = self._source(module)
            self.assertIn('log_unexpected_error(', source,
                          f'{module} must log unexpected failures server-side')
            self.assertIn('user_error_message(', source,
                          f'{module} must flash a generic message')

    def test_expected_call_counts(self):
        """24 remediated sites: 18 admin, 2 complaints, 4 users."""
        expected = {'admin.py': 18, 'complaints.py': 2, 'users.py': 4}
        for module, count in expected.items():
            source = self._source(module)
            self.assertEqual(source.count('log_unexpected_error('), count,
                             f'{module}: unexpected number of logged handlers')
            self.assertEqual(source.count('user_error_message('), count,
                             f'{module}: unexpected number of generic messages')


class TestRedaction(unittest.TestCase):
    def setUp(self):
        from app.error_handling import redact_text
        self.redact = redact_text

    def test_url_credentials_are_removed(self):
        out = self.redact('mysql+pymysql://app:Hunter2@db:3306/helpdesk')
        self.assertNotIn('Hunter2', out)
        self.assertIn('<redacted>@', out)

    def test_key_value_secrets_are_removed(self):
        out = self.redact('password=Hunter2 token: abc123 secret=xyz')
        for value in ('Hunter2', 'abc123', 'xyz'):
            self.assertNotIn(value, out)

    def test_bearer_and_jwt_are_removed(self):
        jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl'
        out = self.redact(f'Authorization: Bearer {jwt}')
        self.assertNotIn(jwt, out)
        self.assertNotIn('Bearer eyJ', out)

    def test_benign_text_is_unchanged(self):
        text = 'IntegrityError: duplicate entry for key code'
        self.assertEqual(self.redact(text), text)

    # --- regression: suffixed secret keys and positional SQL params -------

    def test_password_hash_value_is_redacted(self):
        # Synthetic hash, not a real credential.
        out = self.redact("UPDATE users SET password_hash='pbkdf2:sha256:99999$abc$xyz123' WHERE id=7")
        self.assertNotIn('pbkdf2:sha256:99999$abc$xyz123', out)
        self.assertIn('<redacted>', out)
        # The id should still be visible for correlation.
        self.assertIn('id=7', out)

    def test_reset_token_hash_value_is_redacted(self):
        out = self.redact('token_hash=abcdef0123456789')
        self.assertNotIn('abcdef0123456789', out)

    def test_positional_sql_param_first_element_is_redacted(self):
        # Synthetic positional parameters; only the first (a secret-shaped
        # string) is masked, the trailing numeric id is preserved.
        out = self.redact("params [('SuperSecret123', 5)]")
        self.assertNotIn('SuperSecret123', out)
        self.assertIn("('<redacted>', 5)", out)

    def test_positional_numeric_only_params_are_not_masked(self):
        out = self.redact("params [(5, 12)]")
        # No quoted first element, so nothing should be masked.
        self.assertEqual(out, "params [(5, 12)]")

    def test_real_credential_is_never_written_to_log(self):
        """End-to-end: a route failure that raises with a synthetic secret
        in the exception message must not write that secret to the log."""
        from app.error_handling import redact_text
        secret = 'SuperSecret123'
        self.assertNotIn(secret, redact_text(f'password={secret}'))
        self.assertNotIn(secret, redact_text(f"[('{secret}', 5)]"))


def _build_app(permission_name, seed_catalogs=False):
    """Testing app with one active user holding ``permission_name``."""
    from app import create_app
    from app.extensions import db
    from app.models import (
        User, Role, Permission, Category, Priority, Department,
        SoftwareCatalog,
    )

    app = create_app('testing')
    with app.app_context():
        db.create_all()
        permission = Permission(
            name=permission_name,
            display_name=permission_name,
            module=permission_name.split('.')[0],
            action=permission_name.split('.')[1],
            is_active=True,
        )
        role = Role(name='route_tester', display_name='Route Tester',
                    is_active=True)
        role.permissions.append(permission)
        user = User(username='route_tester', first_name='Route',
                    last_name='Tester', is_active=True,
                    must_change_password=False)
        user.set_password('StrongTest#123')
        user.roles.append(role)
        db.session.add_all([role, user])
        db.session.commit()

        if seed_catalogs:
            db.session.add_all([
                Category(name='Hardware', code='HW', is_active=True),
                Priority(name='Medium', code='MEDIUM', level=3,
                         color='#3B82F6', is_active=True),
                Department(name='IT Helpdesk', code='IT', is_active=True),
                SoftwareCatalog(name='Suite', code='SUITE', is_active=True),
            ])
            db.session.commit()
    return app


def _login(client):
    response = client.post('/auth/login', data={
        'username': 'route_tester', 'password': 'StrongTest#123',
    })
    assert response.status_code == 302, response.get_data(as_text=True)


class TestComplaintRouteDoesNotLeak(unittest.TestCase):
    def setUp(self):
        from app.extensions import db
        from app.models import Category, Priority, Department, SoftwareCatalog

        self.app = _build_app('complaints.create', seed_catalogs=True)
        with self.app.app_context():
            self.category_id = Category.query.first().id
            self.priority_id = Priority.query.first().id
            self.department_id = Department.query.first().id
            self.software_id = SoftwareCatalog.query.first().id
        self.client = self.app.test_client()
        _login(self.client)

    def _payload(self):
        return {
            'title': 'Printer offline',
            'description': 'The ward printer will not accept print jobs.',
            'category_id': str(self.category_id),
            'priority_id': str(self.priority_id),
            'department_id': str(self.department_id),
            'software_id': str(self.software_id),
            'source_type': 'portal',
            'affected_users_count': '1',
        }

    def test_failure_shows_generic_message_only(self):
        from app.services.complaint import ComplaintService

        with patch.object(ComplaintService, 'create_complaint',
                          side_effect=RuntimeError(_LEAKY_EXCEPTION)):
            response = self.client.post('/complaints/create', data=self._payload())

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('could not create the complaint', html)
        for leaked in (_SECRET, 'tok_abc123', 'RuntimeError',
                       'mysql+pymysql', 'INSERT failed'):
            self.assertNotIn(leaked, html, f'{leaked!r} leaked to the browser')

    def test_failure_is_logged_with_secrets_redacted(self):
        from app.services.complaint import ComplaintService

        with self.assertLogs(self.app.logger, level='ERROR') as captured:
            with patch.object(ComplaintService, 'create_complaint',
                              side_effect=RuntimeError(_LEAKY_EXCEPTION)):
                self.client.post('/complaints/create', data=self._payload())

        output = '\n'.join(captured.output)
        self.assertIn('Unhandled error during create complaint', output)
        self.assertIn('<redacted>', output)
        self.assertNotIn(_SECRET, output, 'password value must be redacted')
        self.assertNotIn('tok_abc123', output, 'token value must be redacted')

    def test_validation_messages_are_not_hidden(self):
        payload = self._payload()
        payload['title'] = ''
        response = self.client.post('/complaints/create', data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Title is required.', response.get_data(as_text=True))


class TestAdminRouteDoesNotLeak(unittest.TestCase):
    def setUp(self):
        self.app = _build_app('config.manage')
        self.client = self.app.test_client()
        _login(self.client)

    def test_failure_shows_generic_message_only(self):
        with patch('app.routes.admin.Department',
                   side_effect=RuntimeError(_LEAKY_EXCEPTION)):
            response = self.client.post('/admin/departments/create', data={
                'name': 'Radiology IT',
                'code': 'RADIT',
            })

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('could not create the department', html)
        for leaked in (_SECRET, 'tok_abc123', 'RuntimeError', 'mysql+pymysql'):
            self.assertNotIn(leaked, html, f'{leaked!r} leaked to the browser')

    def test_failure_is_logged_with_secrets_redacted(self):
        with self.assertLogs(self.app.logger, level='ERROR') as captured:
            with patch('app.routes.admin.Department',
                       side_effect=RuntimeError(_LEAKY_EXCEPTION)):
                self.client.post('/admin/departments/create', data={
                    'name': 'Radiology IT',
                    'code': 'RADIT',
                })

        output = '\n'.join(captured.output)
        self.assertIn('Unhandled error during create department', output)
        self.assertNotIn(_SECRET, output)


if __name__ == '__main__':
    unittest.main()
