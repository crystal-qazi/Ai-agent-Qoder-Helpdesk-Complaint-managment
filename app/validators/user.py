"""User validators."""
import re
from app.models import User, Role, Department


def validate_user_data(data, user_id=None):
    """Validate user registration/update data."""
    errors = {}
    
    # Required fields
    required_fields = ['username', 'first_name', 'last_name']
    for field in required_fields:
        if not data.get(field) or not data[field].strip():
            errors[field] = f'{field.replace("_", " ").title()} is required.'
    
    # Username validation
    if data.get('username'):
        username = data['username'].strip()
        if len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters.'
        elif len(username) > 50:
            errors['username'] = 'Username must be 50 characters or less.'
        elif not re.match(r'^[a-zA-Z0-9_\-\.]+$', username):
            errors['username'] = 'Username can only contain letters, numbers, underscores, hyphens, and periods.'
        else:
            # Check uniqueness
            existing = User.query.filter(User.username == username)
            if user_id:
                existing = existing.filter(User.id != user_id)
            if existing.first():
                errors['username'] = 'Username is already taken.'
    
    # Email validation
    if data.get('email'):
        email = data['email'].strip()
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors['email'] = 'Invalid email format.'
        else:
            # Check uniqueness
            existing = User.query.filter(User.email == email)
            if user_id:
                existing = existing.filter(User.id != user_id)
            if existing.first():
                errors['email'] = 'Email is already registered.'
    
    # Employee number validation
    if data.get('employee_number'):
        emp_num = data['employee_number'].strip()
        existing = User.query.filter(User.employee_number == emp_num)
        if user_id:
            existing = existing.filter(User.id != user_id)
        if existing.first():
            errors['employee_number'] = 'Employee number is already in use.'
    
    # Name validation
    for field in ['first_name', 'last_name']:
        if data.get(field) and len(data[field]) > 50:
            errors[field] = f'{field.replace("_", " ").title()} must be 50 characters or less.'
    
    # Phone validation
    if data.get('phone'):
        phone = data['phone'].strip()
        if not re.match(r'^[\d\s\-\+\(\)]{7,20}$', phone):
            errors['phone'] = 'Invalid phone number format.'
    
    # Extension validation
    if data.get('extension'):
        ext = data['extension'].strip()
        if not re.match(r'^\d{3,5}$', ext):
            errors['extension'] = 'Extension must be 3-5 digits.'
    
    # Role validation. ``role_ids`` may arrive as a single string from the
    # form (or be absent); normalize it to a list of role ids before
    # checking that every one of them is an active role.
    role_ids = data.get('role_ids')
    if role_ids and isinstance(role_ids, str):
        role_ids = [role_ids]
    if role_ids:
        if not isinstance(role_ids, list):
            errors['role_ids'] = 'Roles must be a list.'
        else:
            valid_roles = Role.query.filter(Role.id.in_(role_ids), Role.is_active == True).count()
            if valid_roles != len(role_ids):
                errors['role_ids'] = 'One or more selected roles do not exist or are inactive.'
    
    # Department validation
    if data.get('department_id'):
        dept = Department.query.get(data['department_id'])
        if not dept or not dept.is_active:
            errors['department_id'] = 'Invalid or inactive department.'
    
    # Password validation (for new users or password change)
    if data.get('password') or (user_id is None and not data.get('password')):
        if user_id is None and not data.get('password'):
            errors['password'] = 'Password is required for new users.'
        elif data.get('password'):
            pwd_errors = validate_password_strength(data['password'])
            if pwd_errors:
                errors['password'] = pwd_errors
    
    return errors


def validate_password_strength(password):
    """Validate password strength."""
    if not password:
        return 'Password is required.'
    
    if len(password) < 8:
        return 'Password must be at least 8 characters.'
    
    if len(password) > 128:
        return 'Password must be 128 characters or less.'
    
    # Check for uppercase, lowercase, digit, special char
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password))
    
    missing = []
    if not has_upper:
        missing.append('uppercase letter')
    if not has_lower:
        missing.append('lowercase letter')
    if not has_digit:
        missing.append('number')
    if not has_special:
        missing.append('special character')
    
    if missing:
        return f'Password must contain at least one {", ".join(missing)}.'
    
    return None


def validate_login_data(data):
    """Validate login form data."""
    errors = {}
    
    if not data.get('username'):
        errors['username'] = 'Username is required.'
    
    if not data.get('password'):
        errors['password'] = 'Password is required.'
    
    return errors


def validate_password_change_data(data, user):
    """Validate password change data."""
    errors = {}
    
    if not data.get('current_password'):
        errors['current_password'] = 'Current password is required.'
    elif not user.check_password(data['current_password']):
        errors['current_password'] = 'Current password is incorrect.'
    
    if not data.get('new_password'):
        errors['new_password'] = 'New password is required.'
    else:
        pwd_errors = validate_password_strength(data['new_password'])
        if pwd_errors:
            errors['new_password'] = pwd_errors
    
    if data.get('new_password') != data.get('confirm_password'):
        errors['confirm_password'] = 'Passwords do not match.'
    
    return errors