"""Status model."""
from app.extensions import db
from app.models.base import BaseModel


class Status(BaseModel):
    """Complaint status model."""
    __tablename__ = 'statuses'
    
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(20), nullable=False, index=True)  # open, in_progress, pending, resolved, closed, special
    is_initial = db.Column(db.Boolean, default=False, nullable=False)  # Default status for new complaints
    is_terminal = db.Column(db.Boolean, default=False, nullable=False)  # Closed, Rejected - no further transitions
    requires_reason = db.Column(db.Boolean, default=False, nullable=False)  # Require reason for this status
    requires_resolution = db.Column(db.Boolean, default=False, nullable=False)  # Require resolution summary
    color = db.Column(db.String(7), default='#6B7280', nullable=False)
    icon = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    # Allowed transitions (stored as JSON array of status IDs that can be transitioned TO from this status)
    allowed_transitions = db.Column(db.JSON, nullable=True)
    
    # Relationships
    # complaints = db.relationship('Complaint', backref='status', lazy='dynamic')  # Defined in Complaint
    # status_history = db.relationship('ComplaintStatusHistory', backref='status', lazy='dynamic')  # Defined in ComplaintStatusHistory
    
    def __repr__(self):
        return f'<Status {self.name}>'
    
    def can_transition_to(self, target_status_id):
        """Check if transition to target status is allowed."""
        if self.allowed_transitions is None:
            return True  # No restrictions configured
        return target_status_id in self.allowed_transitions