"""Audit log model."""
from app.extensions import db
from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Security and administrative audit log."""
    __tablename__ = 'audit_logs'
    
    # Acting user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')
    
    # Session info
    session_id = db.Column(db.String(255), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    user_agent = db.Column(db.Text, nullable=True)
    request_id = db.Column(db.String(100), nullable=True, index=True)
    
    # Action details
    action = db.Column(db.String(100), nullable=False, index=True)  # login, logout, create_user, update_role, etc.
    entity_type = db.Column(db.String(50), nullable=True, index=True)  # user, role, permission, complaint, config, etc.
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    entity_repr = db.Column(db.String(200), nullable=True)  # Human-readable entity identifier
    
    # Change details
    old_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)
    changed_fields = db.Column(db.JSON, nullable=True)  # List of field names that changed
    
    # Result
    success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    
    # Metadata
    severity = db.Column(db.String(20), default='info', nullable=False)  # info, warning, critical
    category = db.Column(db.String(50), default='general', nullable=False)  # auth, authorization, config, data, security
    
    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id}>'
    
    @classmethod
    def log_action(cls, user_id, action, entity_type=None, entity_id=None, entity_repr=None,
                   old_values=None, new_values=None, changed_fields=None, success=True,
                   error_message=None, severity='info', category='general', request=None):
        """Log an audit action."""
        from flask import request as flask_request
        
        req = request or flask_request
        ip = None
        ua = None
        session_id = None
        request_id = None
        
        if req:
            ip = req.remote_addr or req.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            ua = req.headers.get('User-Agent')
            session_id = (req.cookies.get('session') or '')[:255] or None
            request_id = req.headers.get('X-Request-ID')
        
        log = cls(
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