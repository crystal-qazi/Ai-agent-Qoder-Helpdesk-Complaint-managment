"""Base model classes and mixins."""
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import declared_attr
from app.extensions import db


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UserTrackingMixin:
    """Mixin for tracking created_by and updated_by users.
    Note: Relationships must be defined in individual model files to avoid circular imports.
    """
    created_by_user_id = db.Column(db.Integer, nullable=True)
    updated_by_user_id = db.Column(db.Integer, nullable=True)


class SoftDeleteMixin:
    """Mixin for soft deletion."""
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by_user_id = db.Column(db.Integer, nullable=True)
    
    def soft_delete(self, user_id=None):
        """Soft delete the record."""
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.deleted_by_user_id = user_id
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_active = True
        self.deleted_at = None
        self.deleted_by_user_id = None


class VersionMixin:
    """Mixin for optimistic locking."""
    version = db.Column(db.Integer, default=1, nullable=False)
    
    def increment_version(self):
        """Increment version for optimistic locking."""
        self.version += 1


class BaseModel(db.Model):
    """Base model with common fields."""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Include mixin columns
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_user_id = db.Column(db.Integer, nullable=True)
    updated_by_user_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by_user_id = db.Column(db.Integer, nullable=True)
    version = db.Column(db.Integer, default=1, nullable=False)
    
    def save(self, user_id=None):
        """Save the model instance."""
        if self.id is None:
            self.created_by_user_id = user_id
        self.updated_by_user_id = user_id
        self.increment_version()
        db.session.add(self)
        db.session.flush()
        return self
    
    def delete(self, user_id=None):
        """Soft delete the model instance."""
        self.soft_delete(user_id)
        db.session.add(self)
        db.session.flush()
    
    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'


# Event listeners for automatic timestamp updates
@event.listens_for(BaseModel, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    if hasattr(target, 'updated_at'):
        target.updated_at = datetime.utcnow()