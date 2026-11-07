"""Audit logging service."""
from datetime import datetime
from flask import request
from app.extensions import db
from app.models import AuditLog


class AuditService:
    """Service for audit logging."""
    
    @staticmethod
    def log_action(user_id, action, entity_type=None, entity_id=None, entity_repr=None,
                   old_values=None, new_values=None, changed_fields=None, success=True,
                   error_message=None, severity='info', category='general'):
        """Log an audit action."""
        ip = None
        ua = None
        session_id = None
        request_id = None
        
        if request:
            ip = request.remote_addr or request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            ua = request.headers.get('User-Agent')
            session_id = (request.cookies.get('session') or '')[:255] or None
            request_id = request.headers.get('X-Request-ID')
        
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_repr=entity_repr,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
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