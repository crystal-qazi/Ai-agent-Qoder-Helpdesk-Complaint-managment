"""Integration tests for dynamic RBAC (role visibility, validation, admin
protection) against a real database.

The suite runs against a DEDICATED test database (``helpdesk_qoder_test``),
created if absent and schema-reset only inside the validated test database. It is fully isolated from the
production database — the production schema and records are never touched.

Each test:
  * builds the real Flask app factory pointed at the test database,
  * authenticates through the real login route with a real session cookie,
  * and drives real test-client requests through the user / role routes,
    supplying a fresh CSRF token on every POST (matching how the browser
    submits the forms).

Run with the project virtualenv so all dependencies are present::

    .venv/Scripts/python.exe -m unittest tests.integration.test_rbac_integration -v

The test database name may be overridden with the ``TEST_DB_NAME`` env var.
"""
import os
import re
import unittest
import re

from sqlalchemy.engine import make_url, URL

import pymysql
from dotenv import load_dotenv

# Load .env the same way run.py does, so DB host/port/credentials are known.
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
_APPLICATION_DATABASE_URL = os.environ.get('DATABASE_URL')

_TEST_DB_NAME = os.environ.get('TEST_DB_NAME', 'helpdesk_qoder_test')


def _server_config():
    """Parse the configured application DB URL without lossy string splitting."""
    raw_url = _APPLICATION_DATABASE_URL
    if raw_url:
        parsed = make_url(raw_url)
        if not parsed.drivername.startswith('mysql'):
            raise RuntimeError('MySQL integration tests require a MySQL DATABASE_URL.')
        return {
            'host': parsed.host or 'localhost',
            'port': parsed.port or 3306,
            'user': parsed.username,
            'password': parsed.password or '',
            'database': parsed.database,
        }
    return {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', '3306')),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'database': os.environ.get('DB_NAME'),
    }


def _test_database_url(server: dict) -> str:
    return URL.create(
        drivername='mysql+pymysql',
        username=server['user'],
        password=server['password'],
        host=server['host'],
        port=server['port'],
        database=_TEST_DB_NAME,
    ).render_as_string(hide_password=False)


def _validate_test_database_target(server: dict):
    """Fail closed unless this is a distinct, explicitly test-named schema."""
    if not re.fullmatch(r'helpdesk_[a-z0-9_]*_test', _TEST_DB_NAME):
        raise RuntimeError(
            'TEST_DB_NAME must match helpdesk_<identifier>_test; refusing '
            'to run destructive or schema-changing integration setup.'
        )
    app_db = server.get('database')
    if not app_db:
        raise RuntimeError(
            'Cannot establish the configured application database identity; '
            'set DATABASE_URL or DB_NAME before running integration tests.'
        )
    if app_db.casefold() == _TEST_DB_NAME.casefold():
        raise RuntimeError(
            'The test database is the configured application database. '
            'Refusing to run integration tests.'
        )


def _ensure_test_db(server: dict):
    """Create a new dedicated schema; never drop or overwrite an existing DB."""
    _validate_test_database_target(server)
    conn = pymysql.connect(
        host=server['host'], port=server['port'],
        user=server['user'], password=server['password'],
    )
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
            "WHERE SCHEMA_NAME = %s", (_TEST_DB_NAME,)
        )
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{_TEST_DB_NAME}` CHARACTER SET utf8mb4"
        )
        conn.commit()
    finally:
        conn.close()


def _csrf_token(html: str):
    """Extract the CSRF token embedded in a rendered form page."""
    m = (re.search(r'name="csrf_token" value="([^"]+)"', html)
         or re.search(r'name="csrf-token" content="([^"]+)"', html))
    return m.group(1) if m else None


class RBACIntegrationTestBase(unittest.TestCase):
    """Flask app + test client pointed at the isolated test DB.

    The app and client are built lazily in ``setUpClass`` (once per class),
    but each individual test re-creates the test database and re-seeds it so
    that no state leaks between tests. This makes the suite safe to run on
    its own or alongside other test modules in a single process.
    """

    _app = None
    _client = None
    _db_uri = None
    _ctx = None

    @classmethod
    def _build_app_once(cls):
        server = _server_config()
        cls._db_uri = _test_database_url(server)
        os.environ['DATABASE_URL'] = cls._db_uri
        from app import create_app
        cls._app = create_app('development')
        cls._app.config['SERVER_NAME'] = 'localhost'
        cls._client = cls._app.test_client()

    @classmethod
    def setUpClass(cls):
        server = _server_config()
        _validate_test_database_target(server)
        _ensure_test_db(server)
        if cls._app is None:
            cls._build_app_once()
        with cls._app.app_context():
            from app.extensions import db
            # Destructive schema reset is permitted only after the dedicated
            # test-schema identity checks above; never targets the app DB.
            db.drop_all()
            db.create_all()
        cls._ctx = cls._seed()

    @classmethod
    def tearDownClass(cls):
        # Deliberately retain the isolated test schema. Automatic teardown
        # must never issue DROP DATABASE, even for a test-named database.
        if cls._app is not None:
            with cls._app.app_context():
                from app.extensions import db
                db.session.remove()

    @classmethod
    def _seed(cls):
        """Create the minimal roles / permissions / users the tests need."""
        with cls._app.app_context():
            from app.extensions import db
            from app.models import User, Role, Permission, UserProfile

            p_users = Permission(name='users.manage', display_name='Manage users',
                                 module='users', action='manage', is_active=True)
            p_roles = Permission(name='roles.manage', display_name='Manage roles',
                                 module='roles', action='manage', is_active=True)
            db.session.add_all([p_users, p_roles])
            db.session.flush()

            admin = Role(name='admin', display_name='Administrator',
                         is_system=True, is_active=True)
            db.session.add(admin)
            db.session.flush()
            admin.permissions.append(p_users)
            admin.permissions.append(p_roles)

            helpdesk = Role(name='helpdesk_agent', display_name='Helpdesk Agent',
                            is_active=True)
            custom = Role(name='it_support', display_name='IT Support', is_active=True)
            inactive_role = Role(name='legacy', display_name='Legacy', is_active=False)
            db.session.add_all([helpdesk, custom, inactive_role])

            admin_user = User(username='admin', first_name='Ada', last_name='Admin')
            admin_user.set_password('Admin#Pass123')
            admin_user.roles.append(admin)
            db.session.add(admin_user)
            db.session.flush()
            db.session.add(UserProfile(user_id=admin_user.id))

            agent = User(username='helper', first_name='Hilary', last_name='Helper')
            agent.set_password('Helper#Pass123')
            agent.roles.append(helpdesk)
            agent.roles.append(custom)
            db.session.add(agent)
            db.session.flush()
            db.session.add(UserProfile(user_id=agent.id))

            db.session.commit()
            return {
                'admin_role_id': admin.id,
                'helpdesk_role_id': helpdesk.id,
                'custom_role_id': custom.id,
                'inactive_role_id': inactive_role.id,
                'admin_user_id': admin_user.id,
                'agent_user_id': agent.id,
            }

    # ------------------------------------------------------------------
    # test-client helpers
    # ------------------------------------------------------------------
    def _login_admin(self):
        # Clear any session left by a previous test so the admin login is
        # deterministic regardless of test order.
        with self._client.session_transaction() as sess:
            sess.clear()
        self._client.get('/auth/login')
        page = self._client.get('/auth/login').get_data(as_text=True)
        self._client.post('/auth/login', data={
            'username': 'admin', 'password': 'Admin#Pass123',
            'csrf_token': _csrf_token(page),
        })

    def _post(self, url, data=None, fetch_from=None):
        """POST with a freshly-fetched CSRF token.

        ``fetch_from`` overrides the page used to source the token — needed
        for POST-only routes (e.g. delete) whose URL cannot be GET.
        """
        page = self._client.get(fetch_from or url).get_data(as_text=True)
        payload = dict(data or {})
        payload['csrf_token'] = _csrf_token(page)
        return self._client.post(url, data=payload)

    def _get(self, url):
        return self._client.get(url)

    def _flash_text(self, resp):
        """Collect flash messages from the response HTML (the alert block)."""
        parts = []
        html = resp.get_data(as_text=True)
        # The base template renders flashes inside the top-right alert block.
        for block in re.findall(r'fixed top-20.*?</div>', html, re.S):
            for msg in re.findall(r'<p class="text-sm text-gray-700">(.*?)</p>', block, re.S):
                parts.append(re.sub(r'<[^>]+>', '', msg).strip())
        return parts

    def _assert_flash_contains(self, resp, needle):
        parts = self._flash_text(resp)
        self.assertTrue(
            any(needle.lower() in p.lower() for p in parts),
            f"expected flash containing {needle!r}, got {parts}",
        )

    def _user_exists(self, username):
        with self._app.app_context():
            from app.models import User
            return User.query.filter_by(username=username).first() is not None


class TestRoleVisibility(RBACIntegrationTestBase):
    def test_create_form_lists_all_active_roles(self):
        self._login_admin()
        resp = self._get('/users/create')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        for rid in (self._ctx['helpdesk_role_id'], self._ctx['custom_role_id']):
            self.assertIn(f'name="role_ids" value="{rid}"', html)
        self.assertNotIn(
            f'name="role_ids" value="{self._ctx["inactive_role_id"]}"', html)

    def test_newly_created_role_appears_on_next_load(self):
        """A role created at runtime shows up with no code changes."""
        self._login_admin()
        with self._app.app_context():
            from app.extensions import db
            from app.models import Role
            new_role = Role(name='billing', display_name='Billing', is_active=True)
            db.session.add(new_role)
            db.session.commit()
            new_id = new_role.id
        html = self._get('/users/create').get_data(as_text=True)
        self.assertIn(f'name="role_ids" value="{new_id}"', html)


class TestRoleAssignmentValidation(RBACIntegrationTestBase):
    def _create_user_payload(self, role_ids, username):
        return {
            'username': username,
            'first_name': 'New',
            'last_name': 'User',
            'email': f'{username}@example.com',
            'password': 'Passw0rd!123',
            'is_active': 'on',
            'must_change_password': 'on',
            'role_ids': [str(r) for r in role_ids],
        }

    def test_valid_roles_create_user(self):
        self._login_admin()
        resp = self._post('/users/create',
                          self._create_user_payload([self._ctx['helpdesk_role_id']], 'alice'))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self._user_exists('alice'))
        with self._app.app_context():
            from app.models import User
            u = User.query.filter_by(username='alice').first()
            self.assertEqual([r.name for r in u.roles], ['helpdesk_agent'])

    def test_malformed_role_id_rejected(self):
        self._login_admin()
        resp = self._post('/users/create',
                          self._create_user_payload(['notanumber'], 'bob'))
        self.assertEqual(resp.status_code, 200)  # re-rendered, not committed
        self._assert_flash_contains(resp, 'not a valid role ID')
        self.assertFalse(self._user_exists('bob'))

    def test_unknown_role_id_rejected(self):
        self._login_admin()
        resp = self._post('/users/create',
                          self._create_user_payload([999999], 'carol'))
        self.assertEqual(resp.status_code, 200)
        self._assert_flash_contains(resp, 'do not exist')
        self.assertFalse(self._user_exists('carol'))

    def test_inactive_role_rejected(self):
        self._login_admin()
        resp = self._post('/users/create',
                          self._create_user_payload([self._ctx['inactive_role_id']], 'dave'))
        self.assertEqual(resp.status_code, 200)
        self._assert_flash_contains(resp, 'Cannot assign inactive')
        self.assertFalse(self._user_exists('dave'))

    def test_non_admin_cannot_reach_user_management(self):
        """A user without 'users.manage' is forbidden from the create form."""
        # Clear any session left over from a previous test (the admin
        # credentials would otherwise still be in effect).
        with self._client.session_transaction() as sess:
            sess.clear()
        self._client.get('/auth/login')
        page = self._client.get('/auth/login').get_data(as_text=True)
        self._client.post('/auth/login', data={
            'username': 'helper', 'password': 'Helper#Pass123',
            'csrf_token': _csrf_token(page)})
        resp = self._client.get('/users/create')
        # The permission check calls abort(403); the 403 handler renders the
        # "403 - Access Denied" page.
        self.assertEqual(resp.status_code, 403)


class TestLastAdminProtection(RBACIntegrationTestBase):
    def test_cannot_deactivate_last_admin(self):
        self._login_admin()
        # /users/<id>/delete is POST-only; source the token from the user view.
        resp = self._post(
            f'/users/{self._ctx["admin_user_id"]}/delete',
            fetch_from=f'/users/{self._ctx["admin_user_id"]}',
        )
        with self._app.app_context():
            from app.extensions import db
            from app.models import User
            u = db.session.get(User, self._ctx['admin_user_id'])
            self.assertTrue(u.is_active,
                            "last active admin must remain active")

    def test_deactivating_admin_role_blocked_while_in_use(self):
        self._login_admin()
        resp = self._post(
            f'/users/roles/{self._ctx["admin_role_id"]}/toggle',
            fetch_from='/users/roles',
        )
        with self._app.app_context():
            from app.extensions import db
            from app.models import Role
            role = db.session.get(Role, self._ctx['admin_role_id'])
            self.assertTrue(role.is_active,
                            "admin role must remain active while admins rely on it")

    def test_toggle_still_works_for_non_admin_role(self):
        self._login_admin()
        resp = self._post(
            f'/users/roles/{self._ctx["inactive_role_id"]}/toggle',
            fetch_from='/users/roles',
        )
        self.assertEqual(resp.status_code, 302)
        with self._app.app_context():
            from app.extensions import db
            from app.models import Role
            role = db.session.get(Role, self._ctx['inactive_role_id'])
            self.assertTrue(role.is_active,
                            "toggle should activate a non-admin inactive role")


class TestInactiveRoleGrantsNoPermissions(RBACIntegrationTestBase):
    def test_inactive_role_grants_no_permissions(self):
        with self._app.app_context():
            from app.extensions import db
            from app.models import Role, Permission, User, UserProfile

            legacy = db.session.get(Role, self._ctx['inactive_role_id'])
            p = Permission.query.filter_by(name='users.manage').first()
            legacy.permissions.append(p)
            db.session.flush()

            user = User(username='legacyuser', first_name='Le', last_name='Gacy')
            user.set_password('Legacy#Pass123')
            user.roles.append(legacy)
            db.session.add(user)
            db.session.flush()
            db.session.add(UserProfile(user_id=user.id))
            db.session.commit()

            self.assertFalse(user.has_permission('users.manage'),
                             "inactive role must not grant its permission")
            self.assertFalse(user.has_role('legacy'),
                             "an inactive role must not be reported as held")


if __name__ == '__main__':
    unittest.main()
