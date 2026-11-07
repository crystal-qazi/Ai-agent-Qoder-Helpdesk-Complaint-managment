"""Complaint validators."""
from datetime import datetime
from app.models import Category, Priority, Status, Department, SoftwareCatalog, User


def validate_complaint_data(data, complaint_id=None):
    """Validate complaint registration/update data."""
    errors = {}
    
    # Required fields
    required_fields = ['title', 'description', 'category_id', 'priority_id', 'department_id', 'software_id']
    for field in required_fields:
        if not data.get(field):
            errors[field] = f'{field.replace("_", " ").title()} is required.'
    
    # Title length
    if data.get('title') and len(data['title']) > 255:
        errors['title'] = 'Title must be 255 characters or less.'
    
    # Description length
    if data.get('description') and len(data['description']) < 10:
        errors['description'] = 'Description must be at least 10 characters.'
    
    # Validate category
    if data.get('category_id'):
        category = Category.query.get(data['category_id'])
        if not category or not category.is_active:
            errors['category_id'] = 'Invalid or inactive category.'
    
    # Validate priority
    if data.get('priority_id'):
        priority = Priority.query.get(data['priority_id'])
        if not priority or not priority.is_active:
            errors['priority_id'] = 'Invalid or inactive priority.'
    
    # Validate status (for updates)
    if data.get('status_id'):
        status = Status.query.get(data['status_id'])
        if not status or not status.is_active:
            errors['status_id'] = 'Invalid or inactive status.'
    
    # Validate department
    if data.get('department_id'):
        department = Department.query.get(data['department_id'])
        if not department or not department.is_active:
            errors['department_id'] = 'Invalid or inactive department.'
    
    # Validate software
    if data.get('software_id'):
        software = SoftwareCatalog.query.get(data['software_id'])
        if not software or not software.is_active:
            errors['software_id'] = 'Invalid or inactive software.'
    
    # Validate reported_by_user_id
    if data.get('reported_by_user_id'):
        user = User.query.get(data['reported_by_user_id'])
        if not user or not user.is_active:
            errors['reported_by_user_id'] = 'Invalid or inactive reporter.'
    
    # Validate assigned_to_user_id
    if data.get('assigned_to_user_id'):
        user = User.query.get(data['assigned_to_user_id'])
        if not user or not user.is_active:
            errors['assigned_to_user_id'] = 'Invalid or inactive assignee.'
    
    # Validate severity
    valid_severities = ['Critical', 'High', 'Medium', 'Low']
    if data.get('severity') and data['severity'] not in valid_severities:
        errors['severity'] = f'Severity must be one of: {", ".join(valid_severities)}.'
    
    # Validate affected_users_count
    if data.get('affected_users_count'):
        try:
            count = int(data['affected_users_count'])
            if count < 1:
                errors['affected_users_count'] = 'Affected users count must be at least 1.'
        except ValueError:
            errors['affected_users_count'] = 'Affected users count must be a number.'
    
    # Validate incident_started_at
    if data.get('incident_started_at'):
        try:
            if isinstance(data['incident_started_at'], str):
                datetime.fromisoformat(data['incident_started_at'].replace('Z', '+00:00'))
        except ValueError:
            errors['incident_started_at'] = 'Invalid date format for incident start time.'
    
    # Validate source_type
    valid_sources = ['phone', 'email', 'walk_in', 'portal', 'system', 'other']
    if data.get('source_type') and data['source_type'] not in valid_sources:
        errors['source_type'] = f'Source type must be one of: {", ".join(valid_sources)}.'
    
    return errors


def validate_status_transition(complaint, new_status_id, user, resolution_summary=None):
    """Validate a status transition."""
    from app.models import Status
    from app.permissions.policy import PermissionPolicy
    
    errors = {}
    
    new_status = Status.query.get(new_status_id)
    if not new_status:
        errors['status_id'] = 'Invalid status.'
        return errors
    
    if not new_status.is_active:
        errors['status_id'] = 'Status is not active.'
        return errors
    
    current_status = complaint.status
    
    # Check if transition is allowed
    if current_status and not current_status.can_transition_to(new_status_id):
        errors['status_id'] = f'Transition from "{current_status.name}" to "{new_status.name}" is not allowed.'
    
    # Check permission
    if not PermissionPolicy.can_change_status(user, complaint, new_status):
        errors['permission'] = 'You do not have permission to change to this status.'
    
    # Check required fields for specific statuses
    if new_status.requires_reason and not complaint.status_history.filter_by(to_status_id=new_status_id).first():
        # This is a new transition to a status requiring reason
        # The reason should be provided in the request
        pass  # Handled in the route
    
    if new_status.requires_resolution and new_status.category in ['resolved', 'closed']:
        if not (resolution_summary or '').strip() and not complaint.resolution_summary:
            errors['resolution_summary'] = 'Resolution summary is required for this status.'
    
    return errors


def validate_assignment_data(data):
    """Validate complaint assignment data."""
    errors = {}
    
    if not data.get('new_assignee_id'):
        errors['new_assignee_id'] = 'Assignee is required.'
    
    if data.get('new_assignee_id'):
        user = User.query.get(data['new_assignee_id'])
        if not user or not user.is_active:
            errors['new_assignee_id'] = 'Invalid or inactive user.'
    
    if data.get('assignment_reason') and len(data['assignment_reason']) > 1000:
        errors['assignment_reason'] = 'Assignment reason must be 1000 characters or less.'
    
    return errors


def validate_comment_data(data):
    """Validate comment data."""
    errors = {}
    
    if not data.get('content') or not data['content'].strip():
        errors['content'] = 'Comment content is required.'
    
    if data.get('content') and len(data['content']) > 5000:
        errors['content'] = 'Comment must be 5000 characters or less.'
    
    valid_visibilities = ['internal', 'reporter_visible']
    if data.get('visibility') and data['visibility'] not in valid_visibilities:
        errors['visibility'] = f'Visibility must be one of: {", ".join(valid_visibilities)}.'
    
    return errors