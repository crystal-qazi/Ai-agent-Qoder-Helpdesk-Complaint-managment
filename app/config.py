import os
import re
from datetime import timedelta


def _as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _validate_secret_key(value, context):
    """Fail fast on missing or weak secret keys.

    The base (dev/test) context tolerates a short placeholder only when the
    key is explicitly marked as development.  The production context
    requires a long, non-default secret.  Any caller that receives a
    placeholder in production is a deployment bug and must crash at
    startup so the misconfiguration is visible.
    """
    if not value or not str(value).strip():
        raise RuntimeError(
            f'SECRET_KEY is empty in {context}. Set a random value (>= 32 '
            'chars, e.g. ``python -c "import secrets;print(secrets.token_urlsafe(48))"``).'
        )
    lowered = str(value).lower()
    weak_markers = ('dev-secret', 'change-in-production', 'change-this',
                    'your-super-secret', 'supersecret', 'insecure',
                    'placeholder')
    is_weak = any(marker in lowered for marker in weak_markers)
    is_too_short = len(str(value)) < 32
    if is_weak or is_too_short:
        raise RuntimeError(
            f'SECRET_KEY in {context} is weak or too short. Set a '
            f'long, random value (>= 32 chars, no placeholder words).'
        )


class Config:
    """Base configuration class.

    Dev/test environments only: this class still carries a placeholder
    fallback so a fresh clone boots without a .env.  ProductionConfig
    overrides this behaviour with fail-fast validation.
    """

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://dev_user:dev_password@localhost:3306/hospital_complaints',
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }

    # Session
    SESSION_COOKIE_SECURE = _as_bool(os.environ.get('SESSION_COOKIE_SECURE'), False)
    SESSION_COOKIE_HTTPONLY = _as_bool(os.environ.get('SESSION_COOKIE_HTTPONLY'), True)
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', '3600')))
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = SESSION_COOKIE_HTTPONLY
    REMEMBER_COOKIE_DURATION = int(
        os.environ.get('REMEMBER_COOKIE_DURATION', 604800))

    # Security
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', 12))
    LOGIN_MAX_ATTEMPTS = int(os.environ.get('LOGIN_MAX_ATTEMPTS', 5))
    LOGIN_LOCKOUT_DURATION = int(os.environ.get('LOGIN_LOCKOUT_DURATION', 900))
    # Trusted-proxy configuration.  When empty, the application does not
    # honour X-Forwarded-For and trusts REMOTE_ADDR only.  This is the
    # safe default for a directly-reachable Flask app.
    TRUSTED_PROXIES = tuple(
        x.strip() for x in os.environ.get('TRUSTED_PROXIES', '').split(',')
        if x.strip()
    )

    # File Upload
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))
    ALLOWED_EXTENSIONS = set(
        e.strip() for e in os.environ.get(
            'ALLOWED_EXTENSIONS',
            'pdf,png,jpg,jpeg,gif,txt,doc,docx,xls,xlsx',
        ).split(',') if e.strip()
    )

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '25'))
    MAIL_USE_TLS = _as_bool(os.environ.get('MAIL_USE_TLS'), False)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')

    # Application
    APP_NAME = os.environ.get('APP_NAME', 'IT Software Complain System')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production configuration.

    Fail-fast validation runs against SECRET_KEY and database credentials
    when :func:`validate_production_env` is called by the application
    start-up.  Deployers who set FLASK_ENV=production must call
    ``validate_production_env(app.config)`` from their WSGI entrypoint
    (see ``wsgi.py``) so that misconfiguration aborts the boot.
    """
    DEBUG = False
    SQLALCHEMY_ECHO = False

    # Secure cookies.  ``SESSION_COOKIE_SECURE=True`` means the session
    # cookie is only sent over HTTPS.  Deployments running on plain HTTP
    # (e.g. a reverse proxy that terminates TLS) must set this to false
    # through the environment, but the default is secure.
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    # The SECRET_KEY in the env is the source of truth; if it is unset,
    # the class-level value is the placeholder that the caller must
    # detect at start-up.
    SECRET_KEY = os.environ.get('SECRET_KEY') or Config.SECRET_KEY

    # The database URI; the caller validates the credentials when the
    # app boots under FLASK_ENV=production.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://app_user:change-me@localhost:3306/hospital_complaints',
    )

    # Optional TRUSTED_PROXIES.  Operators on a public reverse-proxy must
    # set TRUSTED_PROXIES to the CIDR(s) of the proxy hops; X-Forwarded-For
    # is honoured only for those hops.  Leave empty in non-proxied
    # deployments so the app never trusts spoofable headers.
    TRUSTED_PROXIES = tuple(
        x.strip() for x in os.environ.get('TRUSTED_PROXIES', '').split(',')
        if x.strip()
    )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False
    BCRYPT_LOG_ROUNDS = 4  # Faster for testing
    # SQLite uses StaticPool; the MySQL pool_size / max_overflow keys
    # are not accepted by create_engine() for this driver.
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def validate_production_env(config_instance):
    """Validate production settings and raise on misconfiguration.

    Callers in WSGI entrypoints (wsgi.py, serve.py) invoke this when
    ``FLASK_ENV == 'production'``.  The method is idempotent and may be
    called more than once; the checks are pure so there is no state.

    Raises
    ------
    RuntimeError
        On any of the fatal misconfigurations below:

        * ``SECRET_KEY`` is missing, short, or a placeholder.
        * The database URL uses the ``root`` account.
        * The database URL has no password.
    """
    if not isinstance(config_instance, ProductionConfig):
        # Dev/test configurations keep the placeholder; nothing to check.
        return

    # 1. SECRET_KEY must come from the environment and be strong.
    secret_from_env = os.environ.get('SECRET_KEY')
    if not secret_from_env:
        raise RuntimeError(
            'ProductionConfig: SECRET_KEY environment variable is not set. '
            'Provide a strong, random value (>= 32 chars), e.g. '
            '``export SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(48))")``.'
        )
    _validate_secret_key(secret_from_env, 'production')

    # 2. Database URL must not use root or a blank password.
    from sqlalchemy.engine import make_url
    db_uri = getattr(config_instance, 'SQLALCHEMY_DATABASE_URI', None)
    if db_uri:
        url = make_url(db_uri)
        if url.username == 'root':
            raise RuntimeError(
                'ProductionConfig: the database URL uses the "root" '
                'database account. Never deploy the application under '
                'root; create a least-privilege application account.'
            )
        if not url.password:
            raise RuntimeError(
                'ProductionConfig: the database URL has no password. '
                'Set a strong application-database password.'
            )
