"""User, Role, Permission, and authentication models."""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db
from app.models.base import BaseModel, TimestampMixin


# Association tables with explicit foreign keys
user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow, nullable=False),
    db.Column('assigned_by_user_id', db.Integer, db.ForeignKey('users.id'), nullable=True),
)

role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow, nullable=False),
    db.Column('assigned_by_user_id', db.Integer, db.ForeignKey('users.id'), nullable=True),
)


class Permission(BaseModel):
    """Permission model for granular access control."""
    __tablename__ = 'permissions'
    
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    module = db.Column(db.String(50), nullable=False, index=True)  # e.g., 'complaints', 'users', 'admin'
    action = db.Column(db.String(50), nullable=False)  # e.g., 'create', 'read', 'update', 'delete', 'assign'
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    @property
    def full_name(self):
        return f'{self.module}.{self.action}'


class Role(BaseModel):
    """Role model for RBAC."""
    __tablename__ = 'roles'
    
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_system = db.Column(db.Boolean, default=False, nullable=False)  # System roles cannot be deleted
    
    # Relationships
    users = db.relationship(
        'User', secondary=user_roles, back_populates='roles', lazy='dynamic',
        primaryjoin=lambda: Role.id == user_roles.c.role_id,
        secondaryjoin=lambda: User.id == user_roles.c.user_id,
    )
    permissions = db.relationship('Permission', secondary=role_permissions, backref='roles', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, permission_name):
        """Check if role has a specific permission."""
        return self.permissions.filter(Permission.name == permission_name).count() > 0
    
    def add_permission(self, permission):
        """Add a permission to this role."""
        if not self.has_permission(permission.name):
            self.permissions.append(permission)
    
    def remove_permission(self, permission):
        """Remove a permission from this role."""
        if self.has_permission(permission.name):
            self.permissions.remove(permission)


class User(BaseModel, UserMixin):
    """User model with authentication and RBAC."""
    __tablename__ = 'users'
    
    # Authentication fields
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    employee_number = db.Column(db.String(20), unique=True, nullable=True, index=True)
    
    # Profile fields
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    extension = db.Column(db.String(10), nullable=True)
    
    # Status fields
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    locked_at = db.Column(db.DateTime, nullable=True)
    lock_reason = db.Column(db.Text, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    last_failed_login_at = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    
    # Department relationship
    department_id = db.Column(
        db.Integer,
        db.ForeignKey('departments.id', name='fk_users_department'),
        nullable=True,
    )
    department = db.relationship(
        'Department', backref='users', lazy='joined',
        foreign_keys=[department_id],
    )
    
    # Relationships
    roles = db.relationship(
        'Role', secondary=user_roles, back_populates='users', lazy='dynamic',
        primaryjoin=lambda: User.id == user_roles.c.user_id,
        secondaryjoin=lambda: Role.id == user_roles.c.role_id,
    )
    profile = db.relationship(
        'UserProfile', uselist=False, back_populates='user',
        cascade='all, delete-orphan', foreign_keys='UserProfile.user_id',
    )
    login_attempts = db.relationship('LoginAttempt', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Complaint relationships (Complaint defines its own forward relationships)
    reported_complaints = db.relationship('Complaint', foreign_keys='Complaint.reported_by_user_id', lazy='dynamic')
    created_complaints = db.relationship('Complaint', foreign_keys='Complaint.created_by_user_id', lazy='dynamic')
    assigned_complaints = db.relationship('Complaint', foreign_keys='Complaint.assigned_to_user_id', lazy='dynamic')
    resolved_complaints = db.relationship('Complaint', foreign_keys='Complaint.resolved_by_user_id', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
        self.must_change_password = False
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission_name):
        """Check if user has a specific permission through any active role.

        Inactive roles and inactive permissions never grant access.
        """
        from app.models import Role, Permission
        return db.session.query(role_permissions.c.permission_id).join(
            user_roles, user_roles.c.role_id == role_permissions.c.role_id
        ).join(
            Role, Role.id == user_roles.c.role_id
        ).join(
            Permission, Permission.id == role_permissions.c.permission_id
        ).filter(
            user_roles.c.user_id == self.id,
            Permission.name == permission_name,
            Role.is_active == True,
            Permission.is_active == True,
        ).count() > 0
    
    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.roles.filter(Role.name == role_name).count() > 0
    
    def has_any_role(self, role_names):
        """Check if user has any of the specified roles."""
        return self.roles.filter(Role.name.in_(role_names)).count() > 0
    
    def get_permissions(self):
        """Get all effective permissions for this user (active roles + active permissions only)."""
        from app.models import Role, Permission
        return Permission.query.join(
            role_permissions, role_permissions.c.permission_id == Permission.id
        ).join(
            Role, Role.id == role_permissions.c.role_id
        ).join(
            user_roles, user_roles.c.role_id == Role.id
        ).filter(
            user_roles.c.user_id == self.id,
            Role.is_active == True,
            Permission.is_active == True,
        ).distinct().all()
    
    def record_login(self, ip_address):
        """Record successful login."""
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.last_failed_login_at = None
        self.is_locked = False
        self.locked_at = None
        self.lock_reason = None
        db.session.add(self)
    
    def record_failed_login(self, max_attempts=5, lockout_duration=900):
        """Record failed login attempt and lock if necessary."""
        self.failed_login_attempts += 1
        self.last_failed_login_at = datetime.utcnow()
        if self.failed_login_attempts >= max_attempts:
            self.is_locked = True
            self.locked_at = datetime.utcnow()
            self.lock_reason = f'Exceeded {max_attempts} failed login attempts'
        db.session.add(self)
    
    def unlock(self):
        """Unlock user account."""
        self.is_locked = False
        self.locked_at = None
        self.lock_reason = None
        self.failed_login_attempts = 0
        self.last_failed_login_at = None
        db.session.add(self)


class UserProfile(BaseModel):
    """Extended user profile information."""
    __tablename__ = 'user_profiles'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    user = db.relationship('User', back_populates='profile', foreign_keys=[user_id])
    
    # Additional profile fields
    title = db.Column(db.String(100), nullable=True)  # Job title
    hire_date = db.Column(db.Date, nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    avatar_path = db.Column(db.String(255), nullable=True)
    preferences = db.Column(db.JSON, nullable=True)  # UI preferences, notification settings, etc.
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    in_app_notifications = db.Column(db.Boolean, default=True, nullable=False)
    notify_on_assignment = db.Column(db.Boolean, default=True, nullable=False)
    notify_on_status_change = db.Column(db.Boolean, default=True, nullable=False)
    notify_on_comments = db.Column(db.Boolean, default=True, nullable=False)
    notify_on_sla_breach = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f'<UserProfile {self.user_id}>'


class LoginAttempt(BaseModel):
    """Track login attempts for security monitoring."""
    __tablename__ = 'login_attempts'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    username_attempted = db.Column(db.String(50), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    user_agent = db.Column(db.Text, nullable=True)
    success = db.Column(db.Boolean, default=False, nullable=False)
    failure_reason = db.Column(db.String(100), nullable=True)  # invalid_password, account_locked, user_not_found, etc.
    
    def __repr__(self):
        return f'<LoginAttempt {self.username_attempted} from {self.ip_address}>'