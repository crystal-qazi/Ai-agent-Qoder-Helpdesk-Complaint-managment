"""Complaint and related models."""
from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel, TimestampMixin


class Complaint(BaseModel):
    """Main complaint model."""
    __tablename__ = 'complaints'
    
    # Complaint identification
    complaint_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Classification
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    priority_id = db.Column(db.Integer, db.ForeignKey('priorities.id'), nullable=False, index=True)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=False, index=True)
    
    # Department and application
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False, index=True)
    software_id = db.Column(db.Integer, db.ForeignKey('software_catalog.id'), nullable=False, index=True)
    affected_location = db.Column(db.String(200), nullable=True)
    affected_device = db.Column(db.String(200), nullable=True)
    ward_or_location = db.Column(db.String(200), nullable=True)
    affected_users_count = db.Column(db.Integer, default=1, nullable=False)
    
    # Reporter information
    reported_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reporter_name = db.Column(db.String(100), nullable=True)
    reporter_employee_number = db.Column(db.String(20), nullable=True)
    reporter_department = db.Column(db.String(100), nullable=True)
    reporter_extension = db.Column(db.String(10), nullable=True)
    reporter_contact = db.Column(db.String(100), nullable=True)
    reporter_patient_mrn = db.Column(db.String(50), nullable=True)
    
    # Complaint handling
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    source_type = db.Column(db.String(50), nullable=True)  # phone, email, walk_in, portal, system
    source_reference = db.Column(db.String(100), nullable=True)
    severity = db.Column(db.String(20), nullable=True, index=True)  # Critical, High, Medium, Low
    assignment_notes = db.Column(db.Text, nullable=True)
    
    # Resolution fields
    resolution_summary = db.Column(db.Text, nullable=True)
    root_cause = db.Column(db.Text, nullable=True)
    workaround = db.Column(db.Text, nullable=True)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    incident_started_at = db.Column(db.DateTime, nullable=True, index=True)
    first_response_at = db.Column(db.DateTime, nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True, index=True)
    closed_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # SLA deadlines
    sla_response_deadline = db.Column(db.DateTime, nullable=True, index=True)
    sla_resolution_deadline = db.Column(db.DateTime, nullable=True, index=True)
    
    # Flags
    is_confidential = db.Column(db.Boolean, default=False, nullable=False)
    is_escalated = db.Column(db.Boolean, default=False, nullable=False)
    escalated_at = db.Column(db.DateTime, nullable=True)
    escalated_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    category = db.relationship('Category', lazy='joined')
    priority = db.relationship('Priority', lazy='joined')
    status = db.relationship('Status', lazy='joined')
    department = db.relationship('Department', lazy='joined')
    software = db.relationship('SoftwareCatalog', lazy='joined')
    reported_by = db.relationship('User', foreign_keys=[reported_by_user_id], lazy='joined')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id], lazy='joined')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_user_id], lazy='joined')
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_user_id], lazy='joined')
    escalated_to = db.relationship('User', foreign_keys=[escalated_to_user_id], lazy='joined')
    
    assignments = db.relationship('ComplaintAssignment', backref='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='ComplaintAssignment.assigned_at.desc()')
    status_history = db.relationship('ComplaintStatusHistory', backref='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='ComplaintStatusHistory.changed_at.desc()')
    history = db.relationship('ComplaintHistory', backref='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='ComplaintHistory.created_at.desc()')
    comments = db.relationship('Comment', backref='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='Comment.created_at.asc()')
    attachments = db.relationship('Attachment', backref='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='Attachment.created_at.desc()')
    sla_history = db.relationship('SLAHistory', backref='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='SLAHistory.created_at.desc()')
    notifications = db.relationship('Notification', back_populates='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='Notification.created_at.desc()')
    
    def __repr__(self):
        return f'<Complaint {self.complaint_number}>'
    
    @property
    def is_overdue_response(self):
        """Check if response SLA is overdue."""
        if self.sla_response_deadline and self.status and not self.status.is_terminal:
            if self.first_response_at is None:
                return datetime.utcnow() > self.sla_response_deadline
        return False
    
    @property
    def is_overdue_resolution(self):
        """Check if resolution SLA is overdue."""
        if self.sla_resolution_deadline and self.status and not self.status.is_terminal:
            return datetime.utcnow() > self.sla_resolution_deadline
        return False
    
    @property
    def sla_response_status(self):
        """Get response SLA status: 'ok', 'warning', 'breached'."""
        if not self.sla_response_deadline or self.first_response_at:
            return 'ok'
        now = datetime.utcnow()
        if now > self.sla_response_deadline:
            return 'breached'
        # Warning if within 25% of deadline
        total_seconds = (self.sla_response_deadline - self.created_at).total_seconds()
        remaining_seconds = (self.sla_response_deadline - now).total_seconds()
        if remaining_seconds / total_seconds < 0.25:
            return 'warning'
        return 'ok'
    
    @property
    def sla_resolution_status(self):
        """Get resolution SLA status: 'ok', 'warning', 'breached'."""
        if not self.sla_resolution_deadline or self.resolved_at:
            return 'ok'
        now = datetime.utcnow()
        if now > self.sla_resolution_deadline:
            return 'breached'
        total_seconds = (self.sla_resolution_deadline - self.created_at).total_seconds()
        remaining_seconds = (self.sla_resolution_deadline - now).total_seconds()
        if remaining_seconds / total_seconds < 0.25:
            return 'warning'
        return 'ok'
    
    def get_current_assignee(self):
        """Get current assignee."""
        return self.assigned_to
    
    def get_assignment_history(self):
        """Get assignment history."""
        return self.assignments.all()


class ComplaintAssignment(BaseModel):
    """Complaint assignment history."""
    __tablename__ = 'complaint_assignments'
    
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, index=True)
    previous_assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    new_assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignment_reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    previous_assignee = db.relationship('User', foreign_keys=[previous_assignee_id], lazy='joined')
    new_assignee = db.relationship('User', foreign_keys=[new_assignee_id], lazy='joined')
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_user_id], lazy='joined')
    
    def __repr__(self):
        return f'<ComplaintAssignment {self.complaint_id} -> {self.new_assignee_id}>'


class ComplaintStatusHistory(BaseModel):
    """Complaint status transition history."""
    __tablename__ = 'complaint_status_history'
    
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, index=True)
    from_status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=True)
    to_status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=False, index=True)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # SLA impact
    sla_paused = db.Column(db.Boolean, default=False, nullable=False)
    sla_resumed = db.Column(db.Boolean, default=False, nullable=False)
    sla_adjustment_reason = db.Column(db.Text, nullable=True)
    
    # Relationships
    from_status = db.relationship('Status', foreign_keys=[from_status_id], lazy='joined')
    to_status = db.relationship('Status', foreign_keys=[to_status_id], lazy='joined')
    changed_by = db.relationship('User', foreign_keys=[changed_by_user_id], lazy='joined')
    
    def __repr__(self):
        return f'<ComplaintStatusHistory {self.complaint_id}: {self.from_status_id} -> {self.to_status_id}>'


class ComplaintHistory(BaseModel):
    """General complaint activity history (audit trail for complaint)."""
    __tablename__ = 'complaint_history'
    
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False, index=True)  # created, updated, assigned, commented, attached, etc.
    field_name = db.Column(db.String(100), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')
    
    def __repr__(self):
        return f'<ComplaintHistory {self.complaint_id} - {self.action}>'


class Comment(BaseModel):
    """Complaint comments with visibility levels."""
    __tablename__ = 'comments'
    
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    visibility = db.Column(db.String(20), default='internal', nullable=False)  # internal, reporter_visible
    is_system = db.Column(db.Boolean, default=False, nullable=False)  # System-generated comments
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)  # For threaded replies
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')
    parent = db.relationship('Comment', remote_side='Comment.id', backref='replies', lazy='joined')
    
    def __repr__(self):
        return f'<Comment {self.id} on Complaint {self.complaint_id}>'
    
    @property
    def is_visible_to_reporter(self):
        """Check if comment is visible to reporter."""
        return self.visibility == 'reporter_visible'


class Attachment(BaseModel):
    """Complaint attachments."""
    __tablename__ = 'attachments'
    
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False, index=True)
    storage_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_extension = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_confidential = db.Column(db.Boolean, default=False, nullable=False)
    download_count = db.Column(db.Integer, default=0, nullable=False)
    last_downloaded_at = db.Column(db.DateTime, nullable=True)
    last_downloaded_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')
    last_downloaded_by = db.relationship('User', foreign_keys=[last_downloaded_by_user_id], lazy='joined')
    
    def __repr__(self):
        return f'<Attachment {self.original_filename}>'