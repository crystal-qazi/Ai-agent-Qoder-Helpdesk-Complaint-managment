from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask import session
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
import os


# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def init_extensions(app):
    """Initialize all Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        # The ID includes the credential version, so both ordinary
        # sessions and Flask-Login remember cookies are invalidated after
        # password changes. Legacy IDs intentionally fail closed.
        try:
            raw_id, raw_version = str(user_id).rsplit(':', 1)
            user_id_int = int(raw_id)
            issued_version = int(raw_version)
        except (TypeError, ValueError):
            return None

        user = User.query.get(user_id_int)
        if user is None or not user.is_active or user.is_locked:
            return None
        current_version = user.session_version or 1
        if issued_version != current_version:
            return None

        # Also reject a stale version carried by an ordinary session cookie.
        stored_version = session.get('_auth_version')
        if stored_version is not None and stored_version != current_version:
            return None
        return user
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('IT Software Complain System startup')