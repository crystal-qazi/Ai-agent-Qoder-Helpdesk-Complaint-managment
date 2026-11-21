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
        """Check if transition to target status is allowed.

        The rule is deny-by-default:

        * When ``allowed_transitions`` is ``None`` (no rules configured)
          or empty, *no* transition is permitted.  This is safe against
          existing seed data because every seeded status has an explicit
          transition list.  A status with NULL or ``[]`` rules is
          treated as "do not allow any outbound transitions" — which
          also means the *terminal* status (Closed, Rejected) has no
          outbound rules, so reopening from a terminal status requires
          an explicit re-open workflow (an administrator manually
          editing the status's ``allowed_transitions`` to add a target,
          or the user invoking ``reopened`` through the restricted
          permission path).
        * When ``allowed_transitions`` is a non-empty list, the target
          ID must be present in that list.

        Returning ``False`` for an empty/missing rule list makes the
        system fail safe: an operator who accidentally clears a status
        rule cannot then move a complaint out of that status until the
        rule is restored.
        """
        if not self.allowed_transitions:
            return False
        return target_status_id in self.allowed_transitions