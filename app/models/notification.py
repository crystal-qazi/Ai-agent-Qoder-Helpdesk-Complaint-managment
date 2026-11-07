"""Notification model."""
from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel


class Notification(BaseModel):
    """In-app notification model."""
    __tablename__ = 'notifications'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=True, index=True)
    
    # Notification content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False, index=True)  # assignment, comment, status_change, sla_warning, sla_breach, escalation, resolution, closure
    
    # Status
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Related entity
    related_entity_type = db.Column(db.String(50), nullable=True)  # complaint, comment, attachment, etc.
    related_entity_id = db.Column(db.Integer, nullable=True)
    
    # Action URL
    action_url = db.Column(db.String(500), nullable=True)
    action_label = db.Column(db.String(100), nullable=True)
    
    # Priority
    priority = db.Column(db.String(20), default='normal', nullable=False)  # low, normal, high, urgent
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')
    complaint = db.relationship('Complaint', foreign_keys=[complaint_id], back_populates='notifications', lazy='joined')
    
    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.add(self)

    def mark_as_unread(self):
        self.is_read = False
        self.read_at = None
        db.session.add(self)

    def to_dict(self):
        """Serialize notification for API responses."""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'read_at': self.read_at.strftime('%Y-%m-%d %H:%M') if self.read_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'complaint_id': self.complaint_id,
            'complaint_number': self.complaint.complaint_number if self.complaint else None,
            'priority': self.priority,
            'action_url': self.action_url,
        }
    
    @classmethod
    def create_notification(cls, user_id, title, message, notification_type, complaint_id=None, 
                           related_entity_type=None, related_entity_id=None, action_url=None, 
                           action_label=None, priority='normal'):
        """Create a new notification."""
        notification = cls(
            user_id=user_id,
            complaint_id=complaint_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            action_url=action_url,
            action_label=action_label,
            priority=priority,
        )
        db.session.add(notification)
        return notification