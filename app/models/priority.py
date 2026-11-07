"""Priority model."""
from app.extensions import db
from app.models.base import BaseModel


class Priority(BaseModel):
    """Complaint priority model."""
    __tablename__ = 'priorities'
    
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    level = db.Column(db.Integer, nullable=False, index=True)  # 1=Critical, 2=High, 3=Medium, 4=Low
    color = db.Column(db.String(7), default='#6B7280', nullable=False)  # Hex color for UI
    icon = db.Column(db.String(50), nullable=True)  # Icon name for UI
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    sla_response_hours = db.Column(db.Float, nullable=True)
    sla_resolution_hours = db.Column(db.Float, nullable=True)
    escalation_hours = db.Column(db.Float, nullable=True)
    notify_assigned = db.Column(db.Boolean, default=False, nullable=False)
    notify_on_breach = db.Column(db.Boolean, default=False, nullable=False)
    
    # Default SLA policy reference
    default_sla_policy_id = db.Column(
        db.Integer,
        db.ForeignKey('sla_policies.id', name='fk_priorities_default_sla'),
        nullable=True,
    )
    default_sla_policy = db.relationship('SLAPolicy', foreign_keys=[default_sla_policy_id], lazy='joined')
    
    # Relationships
    # complaints = db.relationship('Complaint', backref='priority', lazy='dynamic')  # Defined in Complaint
    
    def __repr__(self):
        return f'<Priority {self.name}>'