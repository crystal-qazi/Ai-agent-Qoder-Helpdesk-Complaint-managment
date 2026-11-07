"""System Settings model."""
from app.extensions import db
from app.models.base import BaseModel


class SystemSetting(BaseModel):
    """System configuration settings."""
    __tablename__ = 'system_settings'
    
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string', nullable=False)  # string, integer, float, boolean, json
    category = db.Column(db.String(50), nullable=False, index=True)  # general, security, email, sla, ui, etc.
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)  # Can be accessed by non-admin users
    is_editable = db.Column(db.Boolean, default=True, nullable=False)  # Can be modified through admin UI
    
    def __repr__(self):
        return f'<SystemSetting {self.key}>'
    
    def get_value(self):
        """Get typed value."""
        if self.value is None:
            return None
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == 'json':
            import json
            return json.loads(self.value)
        return self.value
    
    def set_value(self, value):
        """Set typed value."""
        if value is None:
            self.value = None
        elif self.value_type == 'integer':
            self.value = str(int(value))
        elif self.value_type == 'float':
            self.value = str(float(value))
        elif self.value_type == 'boolean':
            self.value = 'true' if value else 'false'
        elif self.value_type == 'json':
            import json
            self.value = json.dumps(value)
        else:
            self.value = str(value)
        db.session.add(self)
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value by key."""
        setting = cls.query.filter_by(key=key, is_active=True).first()
        if setting:
            return setting.get_value()
        return default
    
    @classmethod
    def set_setting(cls, key, value, value_type='string', category='general', description=None, user_id=None):
        """Set a setting value by key."""
        setting = cls.query.filter_by(key=key).first()
        if not setting:
            setting = cls(key=key, value_type=value_type, category=category, description=description)
            setting.save(user_id)
        setting.set_value(value)
        setting.updated_by_user_id = user_id
        db.session.add(setting)
        return setting