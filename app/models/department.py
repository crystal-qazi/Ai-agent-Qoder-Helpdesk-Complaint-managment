"""Department model."""
from app.extensions import db
from app.models.base import BaseModel


class Department(BaseModel):
    """Hospital department model."""
    __tablename__ = 'departments'
    
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_departments_manager'), nullable=True)
    manager = db.relationship('User', foreign_keys=[manager_id], lazy='joined')
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationships
    # users = db.relationship('User', backref='department', lazy='dynamic')  # Defined in User model
    # sla_policies = db.relationship('SLAPolicy', backref='department', lazy='dynamic')  # Defined in SLAPolicy
    # working_schedules = db.relationship('WorkingSchedule', backref='department', lazy='dynamic')  # Defined in WorkingSchedule
    
    def __repr__(self):
        return f'<Department {self.name}>'