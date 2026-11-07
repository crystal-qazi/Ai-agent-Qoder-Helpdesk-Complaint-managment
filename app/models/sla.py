"""SLA and related models."""
from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel


class SLAPolicy(BaseModel):
    """SLA Policy model for response and resolution time targets."""
    __tablename__ = 'sla_policies'
    
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Scope
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    department = db.relationship('Department', lazy='joined')
    priority_id = db.Column(db.Integer, db.ForeignKey('priorities.id', name='fk_sla_policies_priority'), nullable=True)
    priority = db.relationship('Priority', foreign_keys=[priority_id], lazy='joined')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', name='fk_sla_policies_category'), nullable=True)
    category = db.relationship('Category', foreign_keys=[category_id], lazy='joined')
    
    # Time targets (in minutes)
    response_target_minutes = db.Column(db.Integer, nullable=False)
    resolution_target_minutes = db.Column(db.Integer, nullable=False)
    
    # Business hours configuration
    use_business_hours = db.Column(db.Boolean, default=True, nullable=False)
    working_schedule_id = db.Column(db.Integer, db.ForeignKey('working_schedules.id'), nullable=True)
    working_schedule = db.relationship('WorkingSchedule', lazy='joined')
    
    # Escalation
    escalation_enabled = db.Column(db.Boolean, default=False, nullable=False)
    escalation_levels = db.Column(db.JSON, nullable=True)  # List of escalation rules
    
    # Pause rules (JSON configuration for when to pause SLA)
    pause_on_pending_info = db.Column(db.Boolean, default=True, nullable=False)
    pause_on_hold = db.Column(db.Boolean, default=True, nullable=False)
    pause_on_reassignment = db.Column(db.Boolean, default=False, nullable=False)
    pause_on_reopen = db.Column(db.Boolean, default=True, nullable=False)
    
    # Statuses that pause SLA (JSON array of status IDs)
    pause_on_status_ids = db.Column(db.JSON, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f'<SLAPolicy {self.name}>'
    
    def get_response_target_hours(self):
        """Get response target in hours."""
        return self.response_target_minutes / 60
    
    def get_resolution_target_hours(self):
        """Get resolution target in hours."""
        return self.resolution_target_minutes / 60


class SLAHistory(BaseModel):
    """SLA calculation history for tracking changes."""
    __tablename__ = 'sla_history'
    
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, index=True)
    sla_policy_id = db.Column(db.Integer, db.ForeignKey('sla_policies.id'), nullable=True)
    sla_policy = db.relationship('SLAPolicy', lazy='joined')
    
    # Deadlines
    response_deadline = db.Column(db.DateTime, nullable=True, index=True)
    resolution_deadline = db.Column(db.DateTime, nullable=True, index=True)
    
    # Calculation details
    calculation_method = db.Column(db.String(50), nullable=True)  # business_hours, calendar_hours
    business_hours_used = db.Column(db.Boolean, default=False, nullable=False)
    working_schedule_id = db.Column(db.Integer, db.ForeignKey('working_schedules.id'), nullable=True)
    
    # Pause/Resume tracking
    is_paused = db.Column(db.Boolean, default=False, nullable=False)
    paused_at = db.Column(db.DateTime, nullable=True)
    paused_by_status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=True)
    paused_by_status = db.relationship('Status', foreign_keys=[paused_by_status_id], lazy='joined')
    pause_reason = db.Column(db.Text, nullable=True)
    resumed_at = db.Column(db.DateTime, nullable=True)
    resume_reason = db.Column(db.Text, nullable=True)
    total_paused_minutes = db.Column(db.Integer, default=0, nullable=False)
    
    # Status
    response_breached = db.Column(db.Boolean, default=False, nullable=False)
    resolution_breached = db.Column(db.Boolean, default=False, nullable=False)
    response_breached_at = db.Column(db.DateTime, nullable=True)
    resolution_breached_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    calculated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    calculated_by = db.relationship('User', foreign_keys=[calculated_by_user_id], lazy='joined')
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<SLAHistory {self.complaint_id}>'


class Holiday(BaseModel):
    """Holiday calendar for SLA calculations."""
    __tablename__ = 'holidays'
    
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)  # Annual recurring
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f'<Holiday {self.name} on {self.date}>'


class WorkingSchedule(BaseModel):
    """Working schedule for business hours calculation."""
    __tablename__ = 'working_schedules'
    
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    
    # Weekly schedule (JSON: {0: {"start": "08:00", "end": "17:00"}, ...})
    # 0=Monday, 6=Sunday
    weekly_schedule = db.Column(db.JSON, nullable=False)
    
    # Exceptions (specific dates with different hours)
    exceptions = db.Column(db.JSON, nullable=True)
    
    # Department association
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    department = db.relationship('Department', lazy='joined')
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<WorkingSchedule {self.name}>'
    
    def is_working_day(self, date):
        """Check if a date is a working day."""
        from datetime import date as date_class
        if isinstance(date, datetime):
            date = date.date()
        
        # Check if it's a holiday
        holiday = Holiday.query.filter_by(date=date, is_active=True).first()
        if holiday:
            return False
        
        # Check weekly schedule
        weekday = date.weekday()  # 0=Monday
        day_schedule = self.weekly_schedule.get(str(weekday))
        if not day_schedule:
            return False
        
        return True
    
    def get_working_hours_for_date(self, date):
        """Get working hours for a specific date."""
        from datetime import date as date_class
        if isinstance(date, datetime):
            date = date.date()
        
        weekday = date.weekday()
        day_schedule = self.weekly_schedule.get(str(weekday))
        if not day_schedule:
            return None
        
        # Check exceptions
        if self.exceptions and str(date) in self.exceptions:
            return self.exceptions[str(date)]
        
        return day_schedule