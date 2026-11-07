"""Complaint Category model."""
from app.extensions import db
from app.models.base import BaseModel


class Category(BaseModel):
    """Complaint category model."""
    __tablename__ = 'categories'
    
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    parent = db.relationship('Category', remote_side='Category.id', backref='children', lazy='joined')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    department = db.relationship('Department', foreign_keys=[department_id], lazy='joined')

    auto_assign_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    auto_assign_to = db.relationship('User', foreign_keys=[auto_assign_to_id], lazy='joined')

    requires_asset = db.Column(db.Boolean, default=False, nullable=False)
    
    # Default SLA policy reference
    default_sla_policy_id = db.Column(
        db.Integer,
        db.ForeignKey('sla_policies.id', name='fk_categories_default_sla'),
        nullable=True,
    )
    default_sla_policy = db.relationship('SLAPolicy', foreign_keys=[default_sla_policy_id], lazy='joined')
    
    # Relationships
    # complaints = db.relationship('Complaint', backref='category', lazy='dynamic')  # Defined in Complaint
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    @property
    def full_path(self):
        """Get full category path (parent > child)."""
        if self.parent:
            return f'{self.parent.full_path} > {self.name}'
        return self.name