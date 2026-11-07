"""Software Catalog model."""
from app.extensions import db
from app.models.base import BaseModel


class SoftwareCatalog(BaseModel):
    """Software/Application catalog for complaint classification."""
    __tablename__ = 'software_catalog'
    
    name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    version = db.Column(db.String(50), nullable=True)
    vendor = db.Column(db.String(100), nullable=True)
    vendor_contact = db.Column(db.String(200), nullable=True)
    vendor_support_url = db.Column(db.String(500), nullable=True)
    license_type = db.Column(db.String(50), nullable=True)  # Commercial, Open Source, Custom, etc.
    license_expiry = db.Column(db.Date, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    department = db.relationship('Department', backref='software_catalog', lazy='joined')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationships
    # complaints = db.relationship('Complaint', backref='software', lazy='dynamic')  # Defined in Complaint
    
    def __repr__(self):
        return f'<SoftwareCatalog {self.name}>'