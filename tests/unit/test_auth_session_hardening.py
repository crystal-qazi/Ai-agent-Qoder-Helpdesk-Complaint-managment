"""Regression tests for persistent authentication hardening."""
import unittest

from app import create_app
from app.extensions import db
from app.models import User


class AuthenticationHardeningTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.ctx = self.app.app_context()
        self.ctx.push()
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
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self):
        response = self.client.post('/auth/login', data={
            'username': 'security_test',
            'password': 'StrongTest#123',
        })
        self.assertIn(response.status_code, (200, 302))

    def test_login_session_contains_persistent_credential_version(self):
        self._login()
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session.get('_auth_version'), 1)

    def test_password_version_change_invalidates_existing_session(self):
        self._login()
        with db.session.begin():
            user = db.session.get(User, self.user_id)
            user.session_version += 1

        response = self.client.get('/auth/profile')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.headers['Location'])

    def test_must_change_password_blocks_other_authenticated_pages(self):
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
