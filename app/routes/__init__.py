"""Routes package initialization."""
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.complaints import complaints_bp
from app.routes.users import users_bp
from app.routes.admin import admin_bp
from app.routes.reports import reports_bp
from app.routes.notifications import notifications_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'complaints_bp',
    'users_bp',
    'admin_bp',
    'reports_bp',
    'notifications_bp',
]