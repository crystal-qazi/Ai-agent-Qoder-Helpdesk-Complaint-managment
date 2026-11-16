"""Regression tests for persistent authentication hardening.

Each client request gets its own Flask application/request context, matching
production behavior. Keeping one app context pushed across requests would
incorrectly cache Flask-Login's current_user on the same g object.
"""
import unittest

from app import create_app
from app.extensions import db
from app.models import User


class AuthenticationHardeningTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        with self.app.app_context():
            db.create_all()
            user = User(
                username='security_test',
                first_name='Security',
                last_name='Tester',
                is_active=True,
                must_change_password=False,
            )
            user.set_password('StrongTest#123')
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.session.remove()

    def _login(self):
        response = self.client.post('/auth/login', data={
            'username': 'security_test',
            'password': 'StrongTest#123',
        })
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True))

    def test_login_session_contains_persistent_credential_version(self):
        self._login()
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session.get('_auth_version'), 1)
            self.assertEqual(browser_session.get('_user_id'), f'{self.user_id}:1')

    def test_password_version_change_invalidates_existing_session(self):
        self._login()
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            user.session_version += 1
            db.session.commit()

        response = self.client.get('/auth/profile')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.headers['Location'])

    def test_successful_password_change_keeps_current_session_and_rotates_identity(self):
        self._login()
        response = self.client.post('/auth/change-password', data={
            'current_password': 'StrongTest#123',
            'new_password': 'NewStrong#456',
            'confirm_password': 'NewStrong#456',
        })
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True))
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session.get('_user_id'), f'{self.user_id}:3')
            self.assertEqual(browser_session.get('_auth_version'), 3)
        profile = self.client.get('/auth/profile')
        self.assertEqual(profile.status_code, 200)

    def test_must_change_password_blocks_other_authenticated_pages(self):
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            user.must_change_password = True
            db.session.commit()

        self._login()
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/change-password', response.headers['Location'])

        allowed = self.client.get('/auth/change-password')
        self.assertEqual(allowed.status_code, 200)


if __name__ == '__main__':
    unittest.main()
