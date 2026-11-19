"""Regression tests for the active database configuration.

The application deliberately ignores a generic ``DATABASE_URL`` / ``DB_NAME``
and builds its connection from ``DB_HOST`` / ``DB_PORT`` / ``DB_USER`` /
``DB_PASSWORD`` plus a fixed database name per environment.  Several scripts
and integration tests still mentioned the old variables; these tests pin the
behaviour that matters and guard the cleanup.

No test here connects to a real server or prints a credential.
"""
import os
import sys
import unittest
from unittest.mock import patch

_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, _PROJECT_ROOT)

# Values that must never be used as the application target.
_BOGUS = {
    'DATABASE_URL': 'mysql+pymysql://legacy:legacy@legacy-host:3306/legacy_db',
    'DB_NAME': 'legacy_db',
}


class TestApplicationIgnoresLegacyVariables(unittest.TestCase):
    def test_database_url_is_built_from_db_star_settings(self):
        from sqlalchemy.engine import make_url
        from app.config import Config

        env = {
            'DB_HOST': 'db.example.internal',
            'DB_PORT': '3307',
            'DB_USER': 'helpdesk_app',
            'DB_PASSWORD': 'p@ss:word/with@chars',
            **_BOGUS,
        }
        with patch.dict(os.environ, env, clear=False):
            url = make_url(Config._database_url('helpdesk_qoder_dev'))

        self.assertEqual(url.host, 'db.example.internal')
        self.assertEqual(url.port, 3307)
        self.assertEqual(url.username, 'helpdesk_app')
        # Special characters must survive URL construction untouched.
        self.assertEqual(url.password, 'p@ss:word/with@chars')

    def test_environment_database_name_is_ignored(self):
        from sqlalchemy.engine import make_url
        from app.config import Config

        with patch.dict(os.environ, _BOGUS, clear=False):
            url = make_url(Config._database_url('helpdesk_qoder_dev'))

        self.assertEqual(url.database, 'helpdesk_qoder_dev')

    def test_fixed_targets_per_environment(self):
        from sqlalchemy.engine import make_url
        from app.config import DevelopmentConfig, ProductionConfig

        self.assertEqual(
            make_url(DevelopmentConfig.SQLALCHEMY_DATABASE_URI).database,
            'helpdesk_qoder_dev')
        self.assertEqual(
            make_url(ProductionConfig.SQLALCHEMY_DATABASE_URI).database,
            'Helpdesk_qoder_prod')

    def test_development_app_ignores_database_url_override_in_env(self):
        from sqlalchemy.engine import make_url
        from app import create_app

        with patch.dict(os.environ, _BOGUS, clear=False):
            app = create_app('development')

        self.assertEqual(
            make_url(app.config['SQLALCHEMY_DATABASE_URI']).database,
            'helpdesk_qoder_dev')


class TestResetAndSeedTargetsTestDatabase(unittest.TestCase):
    """The destructive rebuild must derive its target from the DB_* vars."""

    def setUp(self):
        from scripts import reset_and_seed
        self.module = reset_and_seed

    def test_build_database_url_uses_db_star_settings(self):
        from sqlalchemy.engine import make_url

        env = {
            'DB_HOST': '127.0.0.1',
            'DB_PORT': '3307',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password',
        }
        with patch.dict(os.environ, env, clear=False):
            url = make_url(self.module._build_database_url('helpdesk_qoder_test'))

        self.assertEqual(url.database, 'helpdesk_qoder_test')
        self.assertEqual(url.host, '127.0.0.1')
        self.assertEqual(url.port, 3307)
        self.assertEqual(url.username, 'test_user')

    def test_rejects_non_test_database_names(self):
        for name in ('helpdesk_qoder_dev', 'Helpdesk_qoder_prod', 'other_db'):
            with patch.dict(os.environ, {'TEST_DB_NAME': name}, clear=False):
                with self.assertRaises(SystemExit):
                    self.module._target_database()

    def test_accepts_test_database_names(self):
        with patch.dict(os.environ, {'TEST_DB_NAME': 'helpdesk_ci_test'}, clear=False):
            self.assertEqual(self.module._target_database(), 'helpdesk_ci_test')


class TestStaleVariableCleanup(unittest.TestCase):
    """Source-level guards for the scripts/tests that referenced the old vars."""

    def _read(self, relative_path):
        with open(os.path.join(_PROJECT_ROOT, relative_path), encoding='utf-8') as handle:
            return handle.read()

    def test_reset_and_seed_no_longer_sets_database_url(self):
        source = self._read('scripts/reset_and_seed.py')
        self.assertNotIn("os.environ['DATABASE_URL']", source)
        self.assertIn('config_overrides', source.lower().replace(
            'SQLALCHEMY_DATABASE_URI', 'config_overrides'))

    def test_seed_dev_db_no_longer_sets_database_url(self):
        source = self._read('scripts/seed_dev_db.py')
        self.assertNotIn("setdefault('DATABASE_URL'", source)
        self.assertNotIn("os.environ['DATABASE_URL']", source)

    def test_repair_role_activation_no_longer_reads_database_url(self):
        source = self._read('scripts/repair_role_activation.py')
        self.assertNotIn("os.environ['DATABASE_URL']", source)
        self.assertNotIn("os.environ.get('DATABASE_URL'", source)

    def test_rbac_integration_has_no_dead_application_url(self):
        source = self._read('tests/integration/test_rbac_integration.py')
        self.assertNotIn('_APPLICATION_DATABASE_URL', source)

    def test_no_script_prints_a_password_value(self):
        """Guard against formatting the password value into operator output.

        Matching the *word* ``DB_PASSWORD`` in a warning message is fine;
        interpolating the value itself into a print is not.
        """
        import re
        interpolation = re.compile(
            r'\{[^}]*\b(password|db_password|_password)\b[^}]*\}'
            r'|\.format\([^)]*\b(password|db_password)\b'
            r'|%\s*\(?[^)]*\b(password|db_password)\b',
            re.IGNORECASE,
        )
        offenders = []
        for relative_path in (
            'scripts/cleanup_old_permissions.py',
            'scripts/repair_role_activation.py',
            'scripts/seed_mysql.py',
            'scripts/reset_and_seed.py',
        ):
            for line_no, line in enumerate(self._read(relative_path).splitlines(), 1):
                if 'print' not in line:
                    continue
                if interpolation.search(line):
                    offenders.append(f'{relative_path}:{line_no}')
        self.assertEqual(offenders, [],
                         'do not print password values: ' + ', '.join(offenders))


if __name__ == '__main__':
    unittest.main()
