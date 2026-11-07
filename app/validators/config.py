"""Configuration validators."""
from app.models import Department, SoftwareCatalog, Category, Priority, Status, SLAPolicy, WorkingSchedule, Holiday, SystemSetting


def validate_department_data(data, department_id=None):
    """Validate department data."""
    errors = {}
    
    if not data.get('name') or not data['name'].strip():
        errors['name'] = 'Department name is required.'
    elif len(data['name']) > 100:
        errors['name'] = 'Department name must be 100 characters or less.'
    else:
        existing = Department.query.filter(Department.name == data['name'].strip())
        if department_id:
            existing = existing.filter(Department.id != department_id)
        if existing.first():
            errors['name'] = 'Department name already exists.'
    
    if not data.get('code') or not data['code'].strip():
        errors['code'] = 'Department code is required.'
    elif len(data['code']) > 20:
        errors['code'] = 'Department code must be 20 characters or less.'
    elif not data['code'].isupper():
        errors['code'] = 'Department code must be uppercase.'
    else:
        existing = Department.query.filter(Department.code == data['code'].strip())
        if department_id:
            existing = existing.filter(Department.id != department_id)
        if existing.first():
            errors['code'] = 'Department code already exists.'
    
    if data.get('email'):
        import re
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', data['email']):
            errors['email'] = 'Invalid email format.'
    
    if data.get('phone'):
        import re
        if not re.match(r'^[\d\s\-\+\(\)]{7,20}$', data['phone']):
            errors['phone'] = 'Invalid phone number format.'
    
    return errors


def validate_software_data(data, software_id=None):
    """Validate software catalog data."""
    errors = {}
    
    if not data.get('name') or not data['name'].strip():
        errors['name'] = 'Software name is required.'
    elif len(data['name']) > 150:
        errors['name'] = 'Software name must be 150 characters or less.'
    else:
        existing = SoftwareCatalog.query.filter(SoftwareCatalog.name == data['name'].strip())
        if software_id:
            existing = existing.filter(SoftwareCatalog.id != software_id)
        if existing.first():
            errors['name'] = 'Software name already exists.'
    
    if not data.get('code') or not data['code'].strip():
        errors['code'] = 'Software code is required.'
    elif len(data['code']) > 50:
        errors['code'] = 'Software code must be 50 characters or less.'
    else:
        existing = SoftwareCatalog.query.filter(SoftwareCatalog.code == data['code'].strip())
        if software_id:
            existing = existing.filter(SoftwareCatalog.id != software_id)
        if existing.first():
            errors['code'] = 'Software code already exists.'
    
    if data.get('vendor_support_url'):
        import re
        if not re.match(r'^https?://', data['vendor_support_url']):
            errors['vendor_support_url'] = 'URL must start with http:// or https://'
    
    if data.get('license_expiry'):
        try:
            from datetime import datetime
            datetime.strptime(data['license_expiry'], '%Y-%m-%d')
        except ValueError:
            errors['license_expiry'] = 'Invalid date format. Use YYYY-MM-DD.'
    
    return errors


def validate_category_data(data, category_id=None):
    """Validate category data."""
    errors = {}
    
    if not data.get('name') or not data['name'].strip():
        errors['name'] = 'Category name is required.'
    elif len(data['name']) > 100:
        errors['name'] = 'Category name must be 100 characters or less.'
    else:
        existing = Category.query.filter(Category.name == data['name'].strip())
        if category_id:
            existing = existing.filter(Category.id != category_id)
        if existing.first():
            errors['name'] = 'Category name already exists.'
    
    if not data.get('code') or not data['code'].strip():
        errors['code'] = 'Category code is required.'
    elif len(data['code']) > 30:
        errors['code'] = 'Category code must be 30 characters or less.'
    else:
        existing = Category.query.filter(Category.code == data['code'].strip())
        if category_id:
            existing = existing.filter(Category.id != category_id)
        if existing.first():
            errors['code'] = 'Category code already exists.'
    
    if data.get('parent_id'):
        parent = Category.query.get(data['parent_id'])
        if not parent:
            errors['parent_id'] = 'Parent category not found.'
        elif parent.id == category_id:
            errors['parent_id'] = 'Category cannot be its own parent.'
    
    return errors


def validate_priority_data(data, priority_id=None):
    """Validate priority data."""
    errors = {}
    
    if not data.get('name') or not data['name'].strip():
        errors['name'] = 'Priority name is required.'
    elif len(data['name']) > 50:
        errors['name'] = 'Priority name must be 50 characters or less.'
    else:
        existing = Priority.query.filter(Priority.name == data['name'].strip())
        if priority_id:
            existing = existing.filter(Priority.id != priority_id)
        if existing.first():
            errors['name'] = 'Priority name already exists.'
    
    if not data.get('code') or not data['code'].strip():
        errors['code'] = 'Priority code is required.'
    elif len(data['code']) > 20:
        errors['code'] = 'Priority code must be 20 characters or less.'
    else:
        existing = Priority.query.filter(Priority.code == data['code'].strip())
        if priority_id:
            existing = existing.filter(Priority.id != priority_id)
        if existing.first():
            errors['code'] = 'Priority code already exists.'
    
    if data.get('level'):
        try:
            level = int(data['level'])
            if level < 1 or level > 10:
                errors['level'] = 'Priority level must be between 1 and 10.'
        except ValueError:
            errors['level'] = 'Priority level must be a number.'
    else:
        errors['level'] = 'Priority level is required.'
    
    if data.get('color'):
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', data['color']):
            errors['color'] = 'Color must be a valid hex color (e.g., #FF0000).'
    
    return errors


def validate_status_data(data, status_id=None):
    """Validate status data."""
    errors = {}
    
    if not data.get('name') or not data['name'].strip():
        errors['name'] = 'Status name is required.'
    elif len(data['name']) > 50:
        errors['name'] = 'Status name must be 50 characters or less.'
    else:
        existing = Status.query.filter(Status.name == data['name'].strip())
        if status_id:
            existing = existing.filter(Status.id != status_id)
        if existing.first():
            errors['name'] = 'Status name already exists.'
    
    if not data.get('code') or not data['code'].strip():
        errors['code'] = 'Status code is required.'
    elif len(data['code']) > 20:
        errors['code'] = 'Status code must be 20 characters or less.'
    else:
        existing = Status.query.filter(Status.code == data['code'].strip())
        if status_id:
            existing = existing.filter(Status.id != status_id)
        if existing.first():
            errors['code'] = 'Status code already exists.'
    
    valid_categories = ['open', 'in_progress', 'pending', 'resolved', 'closed', 'special']
    if data.get('category') and data['category'] not in valid_categories:
        errors['category'] = f'Category must be one of: {", ".join(valid_categories)}.'
    elif not data.get('category'):
        errors['category'] = 'Status category is required.'
    
    if data.get('color'):
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', data['color']):
            errors['color'] = 'Color must be a valid hex color (e.g., #FF0000).'
    
    # Validate allowed_transitions
    if data.get('allowed_transitions'):
        if not isinstance(data['allowed_transitions'], list):
            errors['allowed_transitions'] = 'Allowed transitions must be a list of status IDs.'
        else:
            valid_statuses = Status.query.filter(Status.id.in_(data['allowed_transitions']), Status.is_active == True).count()
            if valid_statuses != len(data['allowed_transitions']):
                errors['allowed_transitions'] = 'One or more target statuses are invalid or inactive.'
    
    return errors


def validate_sla_policy_data(data, policy_id=None):
    """Validate SLA policy data."""
    errors = {}
    
    if not data.get('name') or not data['name'].strip():
        errors['name'] = 'Policy name is required.'
    elif len(data['name']) > 100:
        errors['name'] = 'Policy name must be 100 characters or less.'
    else:
        existing = SLAPolicy.query.filter(SLAPolicy.name == data['name'].strip())
        if policy_id:
            existing = existing.filter(SLAPolicy.id != policy_id)
        if existing.first():
            errors['name'] = 'Policy name already exists.'
    
    if data.get('response_target_minutes'):
        try:
            minutes = int(data['response_target_minutes'])
            if minutes < 1:
                errors['response_target_minutes'] = 'Response target must be at least 1 minute.'
        except ValueError:
            errors['response_target_minutes'] = 'Response target must be a number.'
    else:
        errors['response_target_minutes'] = 'Response target is required.'
    
    if data.get('resolution_target_minutes'):
        try:
            minutes = int(data['resolution_target_minutes'])
            if minutes < 1:
                errors['resolution_target_minutes'] = 'Resolution target must be at least 1 minute.'
        except ValueError:
            errors['resolution_target_minutes'] = 'Resolution target must be a number.'
    else:
        errors['resolution_target_minutes'] = 'Resolution target is required.'
    
    if data.get('department_id'):
        dept = Department.query.get(data['department_id'])
        if not dept or not dept.is_active:
            errors['department_id'] = 'Invalid or inactive department.'
    
    if data.get('priority_id'):
        priority = Priority.query.get(data['priority_id'])
        if not priority or not priority.is_active:
            errors['priority_id'] = 'Invalid or inactive priority.'
    
    if data.get('category_id'):
        category = Category.query.get(data['category_id'])
        if not category or not category.is_active:
            errors['category_id'] = 'Invalid or inactive category.'
    
    if data.get('working_schedule_id'):
        schedule = WorkingSchedule.query.get(data['working_schedule_id'])
        if not schedule or not schedule.is_active:
            errors['working_schedule_id'] = 'Invalid or inactive working schedule.'
    
    return errors


def validate_working_schedule_data(data, schedule_id=None):
    """Validate working schedule data."""
    errors = {}
    
    if not data.get('name') or not data['name'].strip():
        errors['name'] = 'Schedule name is required.'
    elif len(data['name']) > 100:
        errors['name'] = 'Schedule name must be 100 characters or less.'
    else:
        existing = WorkingSchedule.query.filter(WorkingSchedule.name == data['name'].strip())
        if schedule_id:
            existing = existing.filter(WorkingSchedule.id != schedule_id)
        if existing.first():
            errors['name'] = 'Schedule name already exists.'
    
    if not data.get('weekly_schedule'):
        errors['weekly_schedule'] = 'Weekly schedule is required.'
    else:
        # Validate weekly schedule structure
        if not isinstance(data['weekly_schedule'], dict):
            errors['weekly_schedule'] = 'Weekly schedule must be a dictionary.'
        else:
            valid_days = {'0', '1', '2', '3', '4', '5', '6'}
            for day, hours in data['weekly_schedule'].items():
                if day not in valid_days:
                    errors['weekly_schedule'] = f'Invalid day: {day}. Must be 0-6 (Monday-Sunday).'
                    break
                if hours is not None:
                    if not isinstance(hours, dict):
                        errors['weekly_schedule'] = f'Day {day} schedule must be an object with start and end.'
                        break
                    if 'start' not in hours or 'end' not in hours:
                        errors['weekly_schedule'] = f'Day {day} schedule must have start and end times.'
                        break
                    import re
                    if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', hours['start']):
                        errors['weekly_schedule'] = f'Day {day} start time must be in HH:MM format.'
                        break
                    if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', hours['end']):
                        errors['weekly_schedule'] = f'Day {day} end time must be in HH:MM format.'
                        break
    
    if data.get('exceptions'):
        if not isinstance(data['exceptions'], dict):
            errors['exceptions'] = 'Exceptions must be a dictionary.'
        else:
            import re
            date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
            for date_str, hours in data['exceptions'].items():
                if not date_pattern.match(date_str):
                    errors['exceptions'] = f'Invalid date format: {date_str}. Use YYYY-MM-DD.'
                    break
                if hours is not None:
                    if not isinstance(hours, dict) or 'start' not in hours or 'end' not in hours:
                        errors['exceptions'] = f'Exception {date_str} must have start and end times.'
                        break
    
    return errors


def validate_holiday_data(data, holiday_id=None):
    """Validate holiday data."""
    errors = {}
    
    if not data.get('name') or not data['name'].strip():
        errors['name'] = 'Holiday name is required.'
    elif len(data['name']) > 100:
        errors['name'] = 'Holiday name must be 100 characters or less.'
    
    if not data.get('date'):
        errors['date'] = 'Holiday date is required.'
    else:
        from datetime import datetime, date as date_type
        holiday_date = data['date']
        if isinstance(holiday_date, str):
            try:
                holiday_date = datetime.strptime(holiday_date, '%Y-%m-%d').date()
            except ValueError:
                errors['date'] = 'Invalid date format. Use YYYY-MM-DD.'
        if not isinstance(holiday_date, date_type):
            if 'date' not in errors:
                errors['date'] = 'Invalid date format. Use YYYY-MM-DD.'
        else:
            existing = Holiday.query.filter(Holiday.date == holiday_date, Holiday.is_active == True)
            if holiday_id:
                existing = existing.filter(Holiday.id != holiday_id)
            if existing.first():
                errors['date'] = 'Holiday already exists for this date.'

    return errors

def validate_system_setting_data(data, setting_id=None):
    """Validate system setting data."""
    errors = {}

    if not data.get('key') or not data['key'].strip():
        errors['key'] = 'Setting key is required.'
    elif len(data['key']) > 100:
        errors['key'] = 'Setting key must be 100 characters or less.'
    else:
        existing = SystemSetting.query.filter(SystemSetting.key == data['key'].strip())
        if setting_id:
            existing = existing.filter(SystemSetting.id != setting_id)
        if existing.first():
            errors['key'] = 'Setting key already exists.'

    valid_types = ['string', 'number', 'boolean', 'json']
    if data.get('setting_type') and data['setting_type'] not in valid_types:
        errors['setting_type'] = f'Setting type must be one of: {", ".join(valid_types)}.'

    return errors
