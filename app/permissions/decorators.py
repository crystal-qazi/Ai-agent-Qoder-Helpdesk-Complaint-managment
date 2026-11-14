"""Permission decorators for Flask routes."""
from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user


def permission_required(permission_name):
    """Decorator to require a specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.has_permission(permission_name):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(role_name):
    """Decorator to require a specific role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.has_role(role_name):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def any_role_required(*role_names):
    """Decorator to require any of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.has_any_role(role_names):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Convenience decorators for common roles
def admin_required(f):
    """Require Admin role."""
    return role_required('admin')(f)


def agent_required(f):
    """Require Agent role."""
    return role_required('agent')(f)


def engineer_required(f):
    """Require Software Engineer role."""
    return role_required('engineer')(f)


def intake_required(f):
    """Require Call Intake User role."""
    return role_required('intake')(f)


def employee_required(f):
    """Require Internal Employee role."""
    return role_required('employee')(f)


# Complaint-specific permission decorators
def can_view_complaint(f):
    """Check if user can view a complaint."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        complaint_id = kwargs.get('complaint_id') or kwargs.get('id')
        if complaint_id:
            from app.models import Complaint
            from app.permissions.policy import PermissionPolicy
            complaint = Complaint.query.get_or_404(complaint_id)
            if not PermissionPolicy.can_view_complaint(current_user, complaint):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_edit_complaint(f):
    """Check if user can edit a complaint.

    The check is per-complaint: the reporter of a still-open complaint
    can edit it even without ``complaints.edit``; a privileged editor
    can edit any complaint they can view (reporter or assignee, or
    ``view_all`` holders).  Terminal-status complaints lock down to
    privileged editors only.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))

        complaint_id = kwargs.get('complaint_id') or kwargs.get('id')
        if complaint_id:
            from app.models import Complaint
            from app.permissions.policy import PermissionPolicy
            complaint = Complaint.query.get_or_404(complaint_id)
            if not PermissionPolicy.can_edit_complaint(current_user, complaint):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_assign_complaint(f):
    """Check if user can assign a complaint."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.has_permission('complaints.assign'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_reassign_complaint(f):
    """Check if user can transfer (reassign) a complaint."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))

        complaint_id = kwargs.get('complaint_id') or kwargs.get('id')
        if complaint_id:
            from app.models import Complaint
            complaint = Complaint.query.get_or_404(complaint_id)
            from app.permissions.policy import PermissionPolicy
            if not PermissionPolicy.can_transfer_complaint(current_user, complaint):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_change_status_complaint(f):
    """Check if user can change status of a complaint."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))

        complaint_id = kwargs.get('complaint_id') or kwargs.get('id')
        new_status_id = request.form.get('status_id') if request.form else None
        if not complaint_id:
            abort(400)
        if not new_status_id:
            abort(400)
        try:
            new_status_id = int(new_status_id)
        except (TypeError, ValueError):
            abort(400)
        from app.models import Complaint, Status
        complaint = Complaint.query.get_or_404(complaint_id)
        new_status = Status.query.get(new_status_id)
        if not new_status:
            abort(404)
        from app.permissions.policy import PermissionPolicy
        if not PermissionPolicy.can_change_status(current_user, complaint, new_status):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_delete_complaint(f):
    """Check if user can delete a complaint."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.has_permission('complaints.delete'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_view_all_complaints(f):
    """Check if user can view all complaints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))

        if not current_user.has_permission('complaints.view_all'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_export_reports(f):
    """Check if user can export reports."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.has_permission('reports.export'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_manage_users(f):
    """Check if user can manage users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.has_permission('users.manage'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_manage_roles(f):
    """Check if user can manage roles."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.has_permission('roles.manage'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_manage_config(f):
    """Check if user can manage configuration."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.has_permission('config.manage'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_view_audit_logs(f):
    """Check if user can view audit logs."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.has_permission('audit.view'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function