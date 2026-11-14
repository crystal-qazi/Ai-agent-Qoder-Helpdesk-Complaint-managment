"""Audit logging service."""
import json
import re
from datetime import datetime
from flask import request
from app.extensions import db
from app.models import AuditLog

# Fields whose values are redacted before being written to the audit
# log.  The pattern matches a dict key (case-insensitive) that signals
# a secret or PII.
_REDACT_KEY_RE = re.compile(
    r'(password|passwd|secret|token|session|csrf|api[_-]?key|private|'
    r'signature|credential|patient|mrn|ssn|dob|email)',
    re.IGNORECASE,
)
_REDACT_VALUE_RE = re.compile(
    r'(sk_live_\w+|sk_test_\w+|Bearer\s+\w+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)',
)


def _redact_dict(value):
    """Return a deep copy of ``value`` with sensitive fields redacted.

    The result is a plain JSON-serializable structure.  Values that
    match the secret/pattern shape are replaced with ``'<redacted>'``.
    Keys that look like secret/PII fields are also replaced.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if _REDACT_KEY_RE.search(str(k)):
                out[k] = '<redacted>'
            else:
                out[k] = _redact_dict(v)
        return out
    if isinstance(value, (list, tuple)):
        return [_redact_dict(item) for item in value]
    if isinstance(value, str):
        if _REDACT_VALUE_RE.search(value):
            return '<redacted>'
        return value
    return value


class AuditService:
    """Service for audit logging.

    Business operations commit audit rows inside the caller's
    transaction (atomic: an undo also undoes the audit row).
    Security-critical rejections are recorded through
    ``_log_blocked_security`` in an independent transaction so that a
    caller-side rollback cannot erase the evidence of a blocked
    operation.
    """

    @staticmethod
    def log_action(user_id, action, entity_type=None, entity_id=None, entity_repr=None,
                   old_values=None, new_values=None, changed_fields=None, success=True,
                   error_message=None, severity='info', category='general'):
        """Log an audit action in the caller's transaction.

        Passwords, tokens, and other secret-shaped fields in
        ``old_values`` / ``new_values`` are redacted before the row is
        written.
        """
        ip = None
        ua = None
        session_id = None
        request_id = None

        if request:
            from app.security_utils import client_ip, user_agent_string
            ip = client_ip()
            ua = user_agent_string()
            session_id = (request.cookies.get('session') or '')[:255] or None
            request_id = request.headers.get('X-Request-ID')

        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_repr=entity_repr,
            old_values=_redact_dict(old_values),
            new_values=_redact_dict(new_values),
            changed_fields=_redact_dict(changed_fields),
            success=success,
            error_message=error_message,
            severity=severity,
            category=category,
            ip_address=ip,
            user_agent=ua,
            session_id=session_id,
            request_id=request_id,
        )
        db.session.add(log)
        return log

    @staticmethod
    def log_blocked_security(user_id, action, entity_type=None, entity_id=None,
                             entity_repr=None, old_values=None, new_values=None,
                             changed_fields=None, error_message=None,
                             severity='warning', category='security'):
        """Persist a rejected security event in an independent transaction.

        Uses a fresh session bound directly to the engine so a
        caller-side rollback or ``flush`` cannot erase the row.  Redaction
        is applied the same way as :meth:`log_action`.
        """
        from sqlalchemy.orm import sessionmaker
        from app.extensions import db as _db
        req = request._get_current_object() if request else None
        ip = ua = session_id = request_id = None
        if req is not None:
            from app.security_utils import client_ip, user_agent_string
            ip = client_ip()
            ua = user_agent_string()
            session_id = (req.cookies.get('session') or '')[:255] or None
            request_id = req.headers.get('X-Request-ID')

        record = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_repr=entity_repr,
            old_values=_redact_dict(old_values),
            new_values=_redact_dict(new_values),
            changed_fields=_redact_dict(changed_fields),
            success=False,
            error_message=error_message,
            severity=severity,
            category=category,
            ip_address=ip,
            user_agent=ua,
            session_id=session_id,
            request_id=request_id,
        )
        AuditSession = sessionmaker(bind=_db.engine, expire_on_commit=False)
        with AuditSession.begin() as audit_session:
            audit_session.add(record)
        return record
    
    @staticmethod
    def log_login(user_id, username, success, failure_reason=None, ip=None, ua=None):
        """Log login attempt."""
        return AuditService.log_action(
            user_id=user_id,
            action='login',
            entity_type='user',
            entity_id=user_id,
            entity_repr=username,
            success=success,
            error_message=failure_reason,
            severity='warning' if not success else 'info',
            category='auth',
        )
    
    @staticmethod
    def log_logout(user_id):
        """Log logout."""
        return AuditService.log_action(
            user_id=user_id,
            action='logout',
            entity_type='user',
            entity_id=user_id,
            category='auth',
        )
    
    @staticmethod
    def log_user_created(user_id, created_by_user_id, user_data):
        """Log user creation."""
        return AuditService.log_action(
            user_id=created_by_user_id,
            action='create_user',
            entity_type='user',
            entity_id=user_id,
            entity_repr=user_data.get('username'),
            new_values=user_data,
            category='config',
        )
    
    @staticmethod
    def log_user_updated(user_id, updated_by_user_id, old_data, new_data, changed_fields):
        """Log user update."""
        return AuditService.log_action(
            user_id=updated_by_user_id,
            action='update_user',
            entity_type='user',
            entity_id=user_id,
            entity_repr=new_data.get('username'),
            old_values=old_data,
            new_values=new_data,
            changed_fields=changed_fields,
            category='config',
        )
    
    @staticmethod
    def log_user_deleted(user_id, deleted_by_user_id, user_data):
        """Log user deletion."""
        return AuditService.log_action(
            user_id=deleted_by_user_id,
            action='delete_user',
            entity_type='user',
            entity_id=user_id,
            entity_repr=user_data.get('username'),
            old_values=user_data,
            category='config',
        )
    
    @staticmethod
    def log_role_changed(user_id, changed_by_user_id, old_roles, new_roles):
        """Log role assignment change."""
        return AuditService.log_action(
            user_id=changed_by_user_id,
            action='change_user_roles',
            entity_type='user',
            entity_id=user_id,
            old_values={'roles': [r.name for r in old_roles]},
            new_values={'roles': [r.name for r in new_roles]},
            category='config',
            severity='warning',
        )
    
    @staticmethod
    def log_permission_changed(role_id, changed_by_user_id, old_permissions, new_permissions):
        """Log permission change."""
        return AuditService.log_action(
            user_id=changed_by_user_id,
            action='change_role_permissions',
            entity_type='role',
            entity_id=role_id,
            old_values={'permissions': [p.name for p in old_permissions]},
            new_values={'permissions': [p.name for p in new_permissions]},
            category='config',
            severity='warning',
        )
    
    @staticmethod
    def log_config_changed(config_key, changed_by_user_id, old_value, new_value, config_category='general'):
        """Log configuration change."""
        return AuditService.log_action(
            user_id=changed_by_user_id,
            action='change_config',
            entity_type='config',
            entity_repr=config_key,
            old_values={'value': old_value},
            new_values={'value': new_value},
            changed_fields=[config_key],
            category='config',
        )
    
    @staticmethod
    def log_failed_access(user_id, attempted_action, entity_type, entity_id, reason):
        """Log failed access attempt."""
        return AuditService.log_action(
            user_id=user_id,
            action='failed_access',
            entity_type=entity_type,
            entity_id=entity_id,
            success=False,
            error_message=reason,
            severity='warning',
            category='security',
        )
    
    @staticmethod
    def get_audit_logs(filters=None, page=1, per_page=50):
        """Get audit logs with filtering."""
        from app.models import AuditLog, User
        
        query = AuditLog.query.join(User, AuditLog.user_id == User.id, isouter=True)
        
        if filters:
            if filters.get('user_id'):
                query = query.filter(AuditLog.user_id == filters['user_id'])
            
            if filters.get('action'):
                query = query.filter(AuditLog.action.ilike(f"%{filters['action']}%"))
            
            if filters.get('entity_type'):
                query = query.filter(AuditLog.entity_type == filters['entity_type'])
            
            if filters.get('entity_id'):
                query = query.filter(AuditLog.entity_id == filters['entity_id'])
            
            if filters.get('category'):
                query = query.filter(AuditLog.category == filters['category'])
            
            if filters.get('severity'):
                query = query.filter(AuditLog.severity == filters['severity'])
            
            if filters.get('success') is not None:
                query = query.filter(AuditLog.success == filters['success'])
            
            if filters.get('date_from'):
                query = query.filter(AuditLog.created_at >= filters['date_from'])
            
            if filters.get('date_to'):
                query = query.filter(AuditLog.created_at <= filters['date_to'])
            
            if filters.get('ip_address'):
                query = query.filter(AuditLog.ip_address == filters['ip_address'])
        
        query = query.order_by(AuditLog.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_user_activity(user_id, page=1, per_page=50):
        """Get audit logs for a specific user."""
        return AuditService.get_audit_logs(
            filters={'user_id': user_id},
            page=page,
            per_page=per_page
        )
    
    @staticmethod
    def get_entity_history(entity_type, entity_id, page=1, per_page=50):
        """Get audit history for a specific entity."""
        return AuditService.get_audit_logs(
            filters={'entity_type': entity_type, 'entity_id': entity_id},
            page=page,
            per_page=per_page
        )
    
    @staticmethod
    def get_security_events(page=1, per_page=50):
        """Get security-related audit events."""
        return AuditService.get_audit_logs(
            filters={'category': 'security'},
            page=page,
            per_page=per_page
        )
    
    @staticmethod
    def get_failed_logins(page=1, per_page=50):
        """Get failed login attempts."""
        from app.models import LoginAttempt
        
        query = LoginAttempt.query.filter_by(success=False).order_by(LoginAttempt.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)