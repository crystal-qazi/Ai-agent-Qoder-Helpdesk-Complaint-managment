from flask import Flask
from app.config import config
from app.extensions import init_extensions
import os


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.complaints import complaints_bp
    from app.routes.users import users_bp
    from app.routes.admin import admin_bp
    from app.routes.reports import reports_bp
    from app.routes.notifications import notifications_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app


def register_error_handlers(app):
    """Register error handlers."""
    from flask import render_template
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from app.extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500


def register_template_filters(app):
    """Register custom template filters."""
    from datetime import datetime
    
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%Y-%m-%d %H:%M'):
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        return value.strftime(format)
    
    @app.template_filter('date_format')
    def date_format(value, format='%Y-%m-%d'):
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        return value.strftime(format)
    
    @app.template_filter('time_ago')
    def time_ago(value):
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        now = datetime.now()
        diff = now - value
        if diff.days > 0:
            return f'{diff.days} day{"s" if diff.days != 1 else ""} ago'
        hours = diff.seconds // 3600
        if hours > 0:
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
        minutes = (diff.seconds % 3600) // 60
        if minutes > 0:
            return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
        return 'just now'


def register_context_processors(app):
    """Register template context processors."""
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        from app.services.notification import NotificationService
        return {
            'app_name': app.config['APP_NAME'],
            'app_version': app.config['APP_VERSION'],
            'notification_service': NotificationService,
            'current_year': datetime.now().year,
        }