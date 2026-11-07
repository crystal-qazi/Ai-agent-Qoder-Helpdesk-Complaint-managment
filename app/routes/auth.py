"""Authentication routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.extensions import db, csrf
from app.models import User, LoginAttempt, AuditLog
from app.validators.user import validate_login_data, validate_password_change_data
from app.services.audit import AuditService


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_login_data(data)
        
        if not errors:
            user = User.query.filter_by(username=data['username']).first()
            
            if user and user.check_password(data['password']):
                # Check if account is locked
                if user.is_locked:
                    flash('Your account is locked. Please contact an administrator.', 'danger')
                    AuditService.log_login(user.id, data['username'], False, 'account_locked')
                elif not user.is_active:
                    flash('Your account is deactivated. Please contact an administrator.', 'danger')
                    AuditService.log_login(user.id, data['username'], False, 'account_inactive')
                else:
                    # Successful login
                    login_user(user, remember=data.get('remember') == 'on')
                    user.record_login(request.remote_addr)
                    
                    # Log successful login
                    AuditService.log_login(user.id, data['username'], True)
                    
                    db.session.commit()
                    
                    flash('Welcome back!', 'success')
                    
                    # Redirect to next page or dashboard
                    next_page = request.args.get('next')
                    if next_page and next_page.startswith('/'):
                        return redirect(next_page)
                    return redirect(url_for('dashboard.index'))
            else:
                # Failed login
                if user:
                    user.record_failed_login(
                        current_app.config['LOGIN_MAX_ATTEMPTS'],
                        current_app.config['LOGIN_LOCKOUT_DURATION']
                    )
                    failure_reason = 'invalid_password'
                    if user.is_locked:
                        failure_reason = 'account_locked'
                else:
                    failure_reason = 'user_not_found'
                
                AuditService.log_login(user.id if user else None, data['username'], False, failure_reason)
                db.session.commit()
                
                flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    AuditService.log_logout(current_user.id)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password."""
    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_password_change_data(data, current_user)
        
        if not errors:
            current_user.set_password(data['new_password'])
            db.session.commit()
            
            AuditService.log_action(
                user_id=current_user.id,
                action='change_password',
                entity_type='user',
                entity_id=current_user.id,
                entity_repr=current_user.username,
                category='security',
            )
            
            flash('Password changed successfully.', 'success')
            return redirect(url_for('dashboard.index'))
        
        for field, error in errors.items():
            flash(error, 'danger')
    
    return render_template('auth/change_password.html')


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile."""
    from app.validators.user import validate_user_data
    from app.models import UserProfile
    
    # Get or create profile
    profile = current_user.profile
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.flush()
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Convert checkboxes
        for field in ['email_notifications', 'in_app_notifications', 'notify_on_assignment',
                      'notify_on_status_change', 'notify_on_comments', 'notify_on_sla_breach']:
            data[field] = field in data
        
        errors = validate_user_data(data, current_user.id)
        
        if not errors:
            old_data = {
                'username': current_user.username,
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'phone': current_user.phone,
                'extension': current_user.extension,
                'department_id': current_user.department_id,
            }
            
            # Update user fields
            current_user.username = data['username'].strip()
            current_user.email = data.get('email', '').strip() or None
            current_user.first_name = data['first_name'].strip()
            current_user.last_name = data['last_name'].strip()
            current_user.phone = data.get('phone', '').strip() or None
            current_user.extension = data.get('extension', '').strip() or None
            current_user.department_id = data.get('department_id', type=int) or None
            
            # Update profile
            profile.email_notifications = data.get('email_notifications', True)
            profile.in_app_notifications = data.get('in_app_notifications', True)
            profile.notify_on_assignment = data.get('notify_on_assignment', True)
            profile.notify_on_status_change = data.get('notify_on_status_change', True)
            profile.notify_on_comments = data.get('notify_on_comments', True)
            profile.notify_on_sla_breach = data.get('notify_on_sla_breach', True)
            
            db.session.commit()
            
            AuditService.log_user_updated(
                current_user.id, current_user.id,
                old_data, data, list(data.keys())
            )
            
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
        
        for field, error in errors.items():
            flash(error, 'danger')
    
    # Get departments for dropdown
    from app.models import Department
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    
    return render_template('auth/profile.html', departments=departments)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - placeholder for future implementation."""
    flash('Password reset functionality requires email configuration. Please contact your administrator.', 'info')
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password - placeholder for future implementation."""
    flash('Password reset functionality requires email configuration. Please contact your administrator.', 'info')
    return redirect(url_for('auth.login'))