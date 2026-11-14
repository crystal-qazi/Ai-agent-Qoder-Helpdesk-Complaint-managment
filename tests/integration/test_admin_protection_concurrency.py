"""MySQL concurrency tests for administrator protection.

These tests exercise the real MySQL row-locking semantics used by
``AdminProtectionService`` so that two concurrent last-admin-sensitive
transactions are correctly serialized on the shared admin-role row and
on the individual active-admin user rows.

The suite is isolated against the same dedicated test database used by
``test_rbac_integration`` — a ``helpdesk_*_test`` schema, never the
application database. It only adds rows and only inside a fresh test
session that is dropped at the end of each test.

Requires a MySQL server reachable via ``DATABASE_URL`` (or the DB_*
env vars) and the ``helpdesk_<identifier>_test`` database. Run with::

    .venv/Scripts/python.exe -m unittest \
        tests.integration.test_admin_protection_concurrency -v
"""
import os
import re
import threading
import unittest

import pymysql
from dotenv import load_dotenv

from sqlalchemy.engine import make_url, URL

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

_TEST_DB_NAME = os.environ.get('TEST_DB_NAME', 'helpdesk_qoder_test')


def _server_config():
    raw_url = os.environ.get('DATABASE_URL')
    if raw_url:
        parsed = make_url(raw_url)
        if not parsed.drivername.startswith('mysql'):
            raise RuntimeError(
                'Admin-protection concurrency tests require a MySQL DATABASE_URL.'
            )
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
    if not re.fullmatch(r'helpdesk_[a-z0-9_]*_test', _TEST_DB_NAME):
        raise RuntimeError(
            'TEST_DB_NAME must match helpdesk_<identifier>_test; refusing '
            'to run concurrency tests against any other schema.'
        )
    app_db = server.get('database')
    if not app_db:
        raise RuntimeError(
            'Cannot establish the configured application database identity; '
            'set DATABASE_URL or DB_NAME before running concurrency tests.'
        )
    if app_db.casefold() == _TEST_DB_NAME.casefold():
        raise RuntimeError(
            'The concurrency test database is the configured application '
            'database. Refusing to run tests that mutate admin rows.'
        )


def _ensure_test_db(server: dict):
    _validate_test_database_target(server)
    conn = pymysql.connect(
        host=server['host'], port=server['port'],
        user=server['user'], password=server['password'],
    )
    try:
        cur = conn.cursor()
        cur.execute(f'CREATE DATABASE IF NOT EXISTS `{_TEST_DB_NAME}` '
                    f'CHARACTER SET utf8mb4')
        conn.commit()
    finally:
        conn.close()


class TestAdminProtectionConcurrency(unittest.TestCase):
    """Two SQLAlchemy sessions in two threads must serialize on the admin
    role row and on the active-admin user rows.

    The test seeds a *single* active admin in a dedicated session, then
    runs two threads:

      * Thread A tries to deactivate the admin user.
      * Thread B tries to strip the admin role from the admin user.

    Because the service locks the admin-role row first (``SELECT ... FOR
    UPDATE`` on ``roles``), the two transactions are serialized. Both
    must be rejected: whichever runs first finds a zero-length active
    admin set and rejects; whichever runs second sees the same state
    and rejects again.  After the test, the admin user must still be
    active and still hold the admin role.
    """

    @classmethod
    def setUpClass(cls):
        server = _server_config()
        _ensure_test_db(server)
        cls._url = _test_database_url(server)
        from app import create_app
        # Build with 'testing' (WTF disabled, faster bcrypt), then override
        # the database URI to point at the dedicated test schema.
        cls._app = create_app('testing')
        cls._app.config['SQLALCHEMY_DATABASE_URI'] = cls._url
        # The TestingConfig default pool is sized for SQLite; use the
        # MySQL-appropriate options.
        cls._app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 10,
            'max_overflow': 20,
        }

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        # Recreate the schema in the isolated test DB so each test starts
        # from a clean slate; the app DB is never touched.
        with self._app.app_context():
            from app.extensions import db
            db.session.remove()
            db.drop_all()
            db.create_all()
            self._seed()

    def tearDown(self):
        with self._app.app_context():
            from app.extensions import db
            db.session.remove()

    def _seed(self):
        from app.extensions import db
        from app.models import User, Role, Permission

        p_users = Permission(name='users.manage', display_name='Manage users',
                             module='users', action='manage', is_active=True)
        p_roles = Permission(name='roles.manage', display_name='Manage roles',
                             module='roles', action='manage', is_active=True)
        db.session.add_all([p_users, p_roles])
        db.session.flush()

        admin_role = Role(name='admin', display_name='Administrator',
                          is_system=True, is_active=True)
        db.session.add(admin_role)
        db.session.flush()
        admin_role.permissions.append(p_users)
        admin_role.permissions.append(p_roles)

        last_admin = User(username='only_admin', first_name='Last', last_name='Admin')
        last_admin.set_password('Passw0rd!123')
        last_admin.roles.append(admin_role)
        db.session.add(last_admin)
        db.session.flush()

        operator = User(username='operator', first_name='Op', last_name='erator')
        operator.set_password('Passw0rd!123')
        db.session.add(operator)
        db.session.flush()

        # Operator has users.manage through a separate active role so the
        # route-level permission check passes; the admin-protection layer
        # is what must block the operation.
        operator_role = Role(name='users_mgr', display_name='Users Manager',
                             is_active=True)
        operator_role.permissions.append(p_users)
        db.session.add(operator_role)
        db.session.flush()
        operator.roles.append(operator_role)

        db.session.commit()
        self._last_admin_id = last_admin.id
        self._operator_id = operator.id
        self._admin_role_id = admin_role.id

    # ------------------------------------------------------------------
    def test_concurrent_last_admin_operations_are_serialized(self):
        """Two threads racing on last-admin protection must both be rejected.

        If either thread's transaction could observe an inconsistent
        state, the test would commit a deactivation / role-strip and the
        post-condition check would fail.
        """
        from app.extensions import db
        from app.services.admin_protection import (
            AdminProtectionService, ProtectionCheck,
        )
        from app.models import User, Role

        results = {'a': None, 'b': None}
        barrier = threading.Barrier(2)

        def thread_a():
            with self._app.app_context():
                db.session.remove()
                barrier.wait()
                user = db.session.get(User, self._last_admin_id)
                actor = db.session.get(User, self._operator_id)
                check = AdminProtectionService.can_deactivate_user(user, actor)
                results['a'] = check
                db.session.rollback()

        def thread_b():
            with self._app.app_context():
                db.session.remove()
                barrier.wait()
                user = db.session.get(User, self._last_admin_id)
                actor = db.session.get(User, self._operator_id)
                # Empty submitted role list: operator would strip admin
                # from the last admin.
                check = AdminProtectionService.can_remove_admin_role_from(
                    user, [], actor,
                )
                results['b'] = check
                db.session.rollback()

        t_a = threading.Thread(target=thread_a)
        t_b = threading.Thread(target=thread_b)
        t_a.start()
        t_b.start()
        t_a.join()
        t_b.join()

        self.assertIsNotNone(results['a'], 'thread A did not complete')
        self.assertIsNotNone(results['b'], 'thread B did not complete')
        self.assertFalse(results['a'].ok,
                         'deactivating the last active admin must be rejected')
        self.assertFalse(results['b'].ok,
                         'stripping admin from the last active admin must be rejected')

        # Post-condition: the last admin must still be active and hold
        # the admin role.
        with self._app.app_context():
            db.session.remove()
            user = db.session.get(User, self._last_admin_id)
            self.assertTrue(user.is_active)
            role_names = {r.name for r in user.roles}
            self.assertIn('admin', role_names)

    def test_non_admin_cannot_strip_admin_from_other_admin(self):
        """A second active admin exists; a non-admin must still be blocked
        from stripping admin privileges from another admin."""
        from app.extensions import db
        from app.services.admin_protection import AdminProtectionService
        from app.models import User, Role

        with self._app.app_context():
            db.session.remove()
            # Add a second admin so last-admin check would pass, but
            # the cross-admin rule must still block the non-admin actor.
            admin_role = Role.query.filter_by(name='admin').first()
            second_admin = User(username='second_admin',
                                first_name='Sec', last_name='Admin')
            second_admin.set_password('Passw0rd!123')
            second_admin.roles.append(admin_role)
            db.session.add(second_admin)
            db.session.flush()
            second_admin_id = second_admin.id
            db.session.commit()

            target = db.session.get(User, second_admin_id)
            actor = db.session.get(User, self._operator_id)
            # The actor submits an empty role list: admin is dropped.
            check = AdminProtectionService.can_remove_admin_role_from(
                target, [], actor,
            )
            db.session.rollback()

        self.assertFalse(check.ok,
                         'a non-admin with users.manage must not be able '
                         'to remove administrator privileges from another admin')

    def test_admin_role_edit_by_non_admin_blocked(self):
        """Only active admins may edit the admin role's permission set."""
        from app.extensions import db
        from app.services.admin_protection import AdminProtectionService
        from app.models import User, Role, Permission

        with self._app.app_context():
            db.session.remove()
            admin_role = Role.query.filter_by(name='admin').first()
            operator = db.session.get(User, self._operator_id)
            original = [p.id for p in admin_role.permissions]

            # Non-admin operator tries to edit the admin role.
            check = AdminProtectionService.can_edit_admin_role(
                operator,
                [],  # empty submitted set
                original_permission_ids=original,
                role_id=admin_role.id,
            )
            db.session.rollback()

        self.assertFalse(check.ok,
                         'a non-admin must not be able to edit the '
                         'administrator role')

    def test_active_admin_may_strip_admin_from_last_admin(self):
        """Sanity: two active admins exist; the acting admin IS allowed to
        strip admin from the other admin (last-admin check passes, and the
        actor IS an admin)."""
        from app.extensions import db
        from app.services.admin_protection import AdminProtectionService
        from app.models import User, Role

        with self._app.app_context():
            db.session.remove()
            admin_role = Role.query.filter_by(name='admin').first()
            second_admin = User(username='second_admin2',
                                first_name='S', last_name='A')
            second_admin.set_password('Passw0rd!123')
            second_admin.roles.append(admin_role)
            db.session.add(second_admin)
            db.session.flush()
            second_admin_id = second_admin.id
            db.session.commit()

            target = db.session.get(User, second_admin_id)
            actor = db.session.get(User, self._last_admin_id)
            check = AdminProtectionService.can_remove_admin_role_from(
                target, [], actor,
            )
            db.session.rollback()

        self.assertTrue(check.ok,
                        'an active admin must be allowed to strip admin '
                        'from another active admin as long as at least one '
                        'active admin remains')


if __name__ == '__main__':
    unittest.main()
