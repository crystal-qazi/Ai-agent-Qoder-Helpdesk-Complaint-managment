"""Regression tests for the password-recovery implementation.

These tests document what the code actually does, so the documented
"security-hardening scope" can be compared against reality:

  * reset tokens are HMAC-SHA256 signed, bound to the issuing browser
    session, single-use, and TTL-limited;
  * the whole feature is hard-disabled in production configuration;
  * token material never reaches the audit log.

They deliberately do not assert that the feature is production-ready.
"""
import os
import sys
import unittest
from datetime import datetime, timedelta

_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, _PROJECT_ROOT)


def _make_app(**overrides):
    from app import create_app
    from app.extensions import db
    from app.models import User

    app = create_app('testing', dict(overrides) or None)
    with app.app_context():
        db.create_all()
        user = User(username='reset_user', first_name='Reset', last_name='User',
                    is_active=True, must_change_password=False)
        user.set_password('Original#123')
        db.session.add(user)
        db.session.commit()
    return app


def _issue_token(client):
    """Drive /forgot-password and return (random_hex, digest) from session."""
    response = client.post('/auth/forgot-password', data={'username': 'reset_user'})
    assert response.status_code == 302, response.get_data(as_text=True)
    with client.session_transaction() as browser_session:
        return (browser_session['_reset_token_random_hex'],
                browser_session['_reset_token_digest'])


class TestProductionGate(unittest.TestCase):
    def test_production_config_disables_password_reset(self):
        from app.config import Config, ProductionConfig
        self.assertFalse(ProductionConfig.PASSWORD_RESET_ENABLED)
        # Dev/test keeps the legacy flow available for development.
        self.assertTrue(Config.PASSWORD_RESET_ENABLED)

    def test_routes_are_hidden_when_disabled(self):
        app = _make_app(PASSWORD_RESET_ENABLED=False)
        client = app.test_client()
        self.assertEqual(client.get('/auth/forgot-password').status_code, 404)
        self.assertEqual(client.get('/auth/reset-password/abc.def').status_code, 404)
        self.assertEqual(
            client.post('/auth/forgot-password',
                        data={'username': 'reset_user'}).status_code,
            404,
        )


class TestSessionBinding(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_reset_requires_the_issuing_session(self):
        """A token without the issuing session cookie is rejected."""
        other = self.app.test_client()
        response = other.post('/auth/reset-password/anything.anything',
                              data={'new_password': 'Attacker#123'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.headers['Location'])

        with self.app.app_context():
            from app.extensions import db
            from app.models import User
            user = User.query.filter_by(username='reset_user').first()
            self.assertTrue(user.check_password('Original#123'),
                            'a session-less token must not change the password')


class TestTokenLifecycle(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def _password_is(self, candidate):
        with self.app.app_context():
            from app.extensions import db
            from app.models import User
            user = User.query.filter_by(username='reset_user').first()
            return user.check_password(candidate)

    def test_successful_reset_changes_password_once(self):
        random_hex, digest = _issue_token(self.client)
        token = f'{random_hex}.{digest}'

        response = self.client.post(f'/auth/reset-password/{token}',
                                    data={'new_password': 'BrandNew#456'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.headers['Location'])
        self.assertTrue(self._password_is('BrandNew#456'))
        self.assertFalse(self._password_is('Original#123'))

    def test_token_is_single_use(self):
        random_hex, digest = _issue_token(self.client)
        token = f'{random_hex}.{digest}'

        first = self.client.post(f'/auth/reset-password/{token}',
                                 data={'new_password': 'BrandNew#456'})
        self.assertEqual(first.status_code, 302)
        self.assertTrue(self._password_is('BrandNew#456'))

        second = self.client.post(f'/auth/reset-password/{token}',
                                  data={'new_password': 'SecondAttempt#789'})
        self.assertEqual(second.status_code, 302)
        self.assertTrue(self._password_is('BrandNew#456'),
                        'a redeemed token must not be usable again')
        self.assertFalse(self._password_is('SecondAttempt#789'))

    def test_expired_token_is_rejected(self):
        random_hex, digest = _issue_token(self.client)
        with self.client.session_transaction() as browser_session:
            browser_session['_reset_token_issued_at'] = (
                datetime.utcnow() - timedelta(hours=2)).isoformat()

        response = self.client.post(f'/auth/reset-password/{random_hex}.{digest}',
                                    data={'new_password': 'TooLate#789'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/forgot-password', response.headers['Location'])
        self.assertTrue(self._password_is('Original#123'))

    def test_wrong_digest_is_rejected(self):
        random_hex, _digest = _issue_token(self.client)
        response = self.client.post(
            f'/auth/reset-password/{random_hex}.{"0" * 64}',
            data={'new_password': 'Tampered#789'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/forgot-password', response.headers['Location'])
        self.assertTrue(self._password_is('Original#123'))

    def test_token_material_never_reaches_the_audit_log(self):
        random_hex, digest = _issue_token(self.client)
        self.client.post(f'/auth/reset-password/{random_hex}.{digest}',
                         data={'new_password': 'BrandNew#456'})

        with self.app.app_context():
            from app.models import AuditLog
            for row in AuditLog.query.all():
                blob = ' '.join(str(value) for value in (
                    row.action, row.entity_type, row.entity_repr,
                    row.old_values, row.new_values, row.changed_fields,
                    row.error_message,
                ) if value is not None)
                self.assertNotIn(digest, blob,
                                 'reset token digest must not be audited')
                self.assertNotIn(random_hex, blob,
                                 'reset token nonce must not be audited')


if __name__ == '__main__':
    unittest.main()
