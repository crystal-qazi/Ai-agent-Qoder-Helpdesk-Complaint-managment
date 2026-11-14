"""User management routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import User, Role, Department, UserProfile, Permission
from app.validators.user import validate_user_data, validate_password_strength
from app.permissions.decorators import can_manage_users, can_manage_roles
from app.services.audit import AuditService
from app.services.admin_protection import AdminProtectionService, ProtectionCheck


users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('/')
@login_required
@can_manage_users
def list_users():
    """List all users."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.employee_number.ilike(f'%{search}%'),
            )
        )
    
    # Filter by active status
    status_filter = request.args.get('status')
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'locked':
        query = query.filter_by(is_locked=True)
    
    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('users/list.html', pagination=pagination, search=search, status_filter=status_filter)


@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@can_manage_users
def create_user():
    """Create a new user."""
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Convert checkboxes
        data['is_active'] = 'is_active' in data
        data['must_change_password'] = 'must_change_password' in data
        
        # Convert role_ids. We keep the raw list for validation; malformed
        # values are rejected by AdminProtectionService.can_assign_roles,
        # which also blocks privileged role escalation.
        raw_role_ids = request.form.getlist('role_ids')
        
        # Convert department_id
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        
        # Centralized role-assignment validation (malformed / unknown /
        # inactive / privileged-escalation). Runs before we touch the
        # database, and it is what actually rejects a bad role submission.
        assignment_check = AdminProtectionService.can_assign_roles(
            current_user, raw_role_ids, target_user_id=None,
        )

        errors = validate_user_data(data)
        # The role-assignment result is authoritative; it supersedes the
        # generic role error that validate_user_data may have produced.
        if not assignment_check.ok:
            errors['role_ids'] = assignment_check.reason
        else:
            data['role_ids'] = [int(r) for r in raw_role_ids if r.isdigit()]
            errors.pop('role_ids', None)
        
        if not errors:
            try:
                user = User(
                    username=data['username'].strip(),
                    email=data.get('email', '').strip() or None,
                    first_name=data['first_name'].strip(),
                    last_name=data['last_name'].strip(),
                    phone=data.get('phone', '').strip() or None,
                    extension=data.get('extension', '').strip() or None,
                    employee_number=data.get('employee_number', '').strip() or None,
                    department_id=data.get('department_id'),
                    is_active=data.get('is_active', True),
                    must_change_password=data.get('must_change_password', True),
                )
                
                # Set password
                if data.get('password'):
                    user.set_password(data['password'])
                else:
                    import secrets
                    temp_password = secrets.token_urlsafe(12)
                    user.set_password(temp_password)
                    flash(f'Temporary password generated: {temp_password}', 'warning')
                
                db.session.add(user)
                db.session.flush()
                
                # Assign roles (only active, validated IDs — the assignment
                # check above already rejected anything else)
                if data['role_ids']:
                    roles = Role.query.filter(Role.id.in_(data['role_ids'])).all()
                    user.roles = roles
                
                # Create profile
                profile = UserProfile(user_id=user.id)
                db.session.add(profile)
                
                db.session.commit()
                
                AuditService.log_user_created(user.id, current_user.id, {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'roles': [r.name for r in user.roles],
                })
                
                flash(f'User {user.username} created successfully.', 'success')
                return redirect(url_for('users.view_user', user_id=user.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating user: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    # Get form data
    roles = Role.query.filter_by(is_active=True).order_by(Role.display_name).all()
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    
    return render_template('users/create.html', roles=roles, departments=departments)


@users_bp.route('/<int:user_id>')
@login_required
@can_manage_users
def view_user(user_id):
    """View user details."""
    user = User.query.get_or_404(user_id)
    
    # Get user's roles and permissions
    user_roles = user.roles.all()
    user_permissions = user.get_permissions()
    
    # Get recent login attempts
    login_attempts = user.login_attempts.order_by(db.desc('created_at')).limit(20).all()
    
    return render_template('users/view.html',
                           user=user,
                           user_roles=user_roles,
                           user_permissions=user_permissions,
                           login_attempts=login_attempts)


@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_users
def edit_user(user_id):
    """Edit a user."""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Convert checkboxes
        data['is_active'] = 'is_active' in data
        data['must_change_password'] = 'must_change_password' in data
        
        # Convert role_ids. Raw values validated by AdminProtectionService
        # before any database writes.
        raw_role_ids = request.form.getlist('role_ids')
        
        # Convert department_id
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        
        errors = validate_user_data(data, user_id)

        # Centralized admin protection
        # Only run the last-admin guard when this POST actually changes an
        # active account to inactive. Ordinary profile edits must not be blocked.
        deactivation_check = (
            AdminProtectionService.can_deactivate_user(user, current_user)
            if user.is_active and not data['is_active']
            else ProtectionCheck.allow()
        )

        role_assignment_check = AdminProtectionService.can_assign_roles(
            current_user, raw_role_ids, target_user_id=user.id,
        )

        self_removal_check = AdminProtectionService.can_remove_admin_role_from(
            user, raw_role_ids, current_user,
        )

        # Fold results into the error dict; role checks are authoritative and
        # supersede the generic role error from validate_user_data.
        if not deactivation_check.ok:
            errors['is_active'] = deactivation_check.reason
        if not self_removal_check.ok:
            errors['role_ids'] = self_removal_check.reason
        elif not role_assignment_check.ok:
            errors['role_ids'] = role_assignment_check.reason
        else:
            data['role_ids'] = [int(r) for r in raw_role_ids if r.isdigit()]
            errors.pop('role_ids', None)
        
        if not errors:
            normalized_role_ids = [int(r) for r in raw_role_ids if r.isdigit()]
            data['role_ids'] = normalized_role_ids
            try:
                old_data = {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'extension': user.extension,
                    'employee_number': user.employee_number,
                    'department_id': user.department_id,
                    'is_active': user.is_active,
                    'roles': [r.id for r in user.roles],
                }
                
                # Update user fields
                user.username = data['username'].strip()
                user.email = data.get('email', '').strip() or None
                user.first_name = data['first_name'].strip()
                user.last_name = data['last_name'].strip()
                user.phone = data.get('phone', '').strip() or None
                user.extension = data.get('extension', '').strip() or None
                user.employee_number = data.get('employee_number', '').strip() or None
                user.department_id = data.get('department_id')
                user.is_active = data.get('is_active', True)
                user.must_change_password = data.get('must_change_password', False)
                
                # Update roles (validated set only)
                if normalized_role_ids:
                    roles = Role.query.filter(Role.id.in_(normalized_role_ids)).all()
                    user.roles = roles
                else:
                    user.roles = []
                
                # Update password if provided
                if data.get('password'):
                    user.set_password(data['password'])
                
                db.session.commit()
                
                new_data = {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'extension': user.extension,
                    'employee_number': user.employee_number,
                    'department_id': user.department_id,
                    'is_active': user.is_active,
                    'roles': [r.id for r in user.roles],
                }
                
                changed_fields = [k for k in old_data if old_data[k] != new_data.get(k)]
                
                AuditService.log_user_updated(user_id, current_user.id, old_data, new_data, changed_fields)
                
                flash('User updated successfully.', 'success')
                return redirect(url_for('users.view_user', user_id=user.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating user: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    # Get form data — active roles only; user's currently-assigned inactive
    # roles are surfaced as a warning in the template.
    roles = Role.query.filter_by(is_active=True).order_by(Role.display_name).all()
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    user_roles = [r.id for r in user.roles]
    
    return render_template('users/edit.html',
                           user=user,
                           roles=roles,
                           departments=departments,
                           user_roles=user_roles)


@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@can_manage_users
def delete_user(user_id):
    """Delete (deactivate) a user."""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('users.view_user', user_id=user.id))
    
    # Centralized last-admin protection
    check = AdminProtectionService.can_deactivate_user(user, current_user)
    if not check.ok:
        flash(check.reason, 'danger')
        return redirect(url_for('users.view_user', user_id=user.id))
    
    # Soft delete
    user.is_active = False
    user.updated_by_user_id = current_user.id
    db.session.commit()
    
    AuditService.log_user_deleted(user_id, current_user.id, {
        'username': user.username,
        'email': user.email,
    })
    
    flash('User deactivated successfully.', 'success')
    return redirect(url_for('users.list_users'))


@users_bp.route('/<int:user_id>/unlock', methods=['POST'])
@login_required
@can_manage_users
def unlock_user(user_id):
    """Unlock a locked user account."""
    user = User.query.get_or_404(user_id)
    
    user.unlock()
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='unlock_user',
        entity_type='user',
        entity_id=user.id,
        entity_repr=user.username,
        category='security',
    )
    
    flash('User account unlocked.', 'success')
    return redirect(url_for('users.view_user', user_id=user.id))


@users_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@login_required
@can_manage_users
def reset_user_password(user_id):
    """Reset user password."""
    user = User.query.get_or_404(user_id)
    
    import secrets
    temp_password = secrets.token_urlsafe(12)
    user.set_password(temp_password)
    user.must_change_password = True
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='reset_password',
        entity_type='user',
        entity_id=user.id,
        entity_repr=user.username,
        category='security',
        severity='warning',
    )
    
    flash(f'Password reset. Temporary password: {temp_password}', 'warning')
    return redirect(url_for('users.view_user', user_id=user.id))


@users_bp.route('/roles')
@login_required
@can_manage_roles
def list_roles():
    """List all roles."""
    roles = Role.query.order_by(Role.name).all()
    return render_template('users/roles.html', roles=roles)


@users_bp.route('/roles/create', methods=['GET', 'POST'])
@login_required
@can_manage_roles
def create_role():
    """Create a new role."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip().lower()
        display_name = request.form.get('display_name', '').strip()
        description = request.form.get('description', '').strip()
        permission_ids = request.form.getlist('permission_ids')
        
        errors = {}
        if not name:
            errors['name'] = 'Role name is required.'
        elif len(name) > 50:
            errors['name'] = 'Role name must be 50 characters or less.'
        elif not name.replace('_', '').isalnum():
            errors['name'] = 'Role name can only contain letters, numbers, and underscores.'
        elif Role.query.filter_by(name=name).first():
            errors['name'] = 'Role name already exists.'
        
        if not display_name:
            errors['display_name'] = 'Display name is required.'
        
        if not errors:
            try:
                role = Role(
                    name=name,
                    display_name=display_name,
                    description=description or None,
                )
                db.session.add(role)
                db.session.flush()
                
                # Assign permissions
                if permission_ids:
                    permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
                    role.permissions = permissions
                
                db.session.commit()
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_role',
                    entity_type='role',
                    entity_id=role.id,
                    entity_repr=role.name,
                    new_values={'name': role.name, 'display_name': role.display_name},
                    category='config',
                )
                
                flash('Role created successfully.', 'success')
                return redirect(url_for('users.list_roles'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating role: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    # Get permissions grouped by module
    permissions = Permission.query.order_by(Permission.module, Permission.action).all()
    permissions_by_module = {}
    for p in permissions:
        if p.module not in permissions_by_module:
            permissions_by_module[p.module] = []
        permissions_by_module[p.module].append(p)
    
    return render_template('users/create_role.html', permissions_by_module=permissions_by_module)


@users_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_roles
def edit_role(role_id):
    """Edit a role."""
    role = Role.query.get_or_404(role_id)
    
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        description = request.form.get('description', '').strip()
        permission_ids = request.form.getlist('permission_ids')

        # Guard the admin role before touching anything. A non-admin
        # actor must not be able to edit the admin role's permission
        # set in a way that changes effective admin privileges.
        admin_guard = AdminProtectionService.can_edit_admin_role(
            current_user,
            permission_ids,
            original_permission_ids=[p.id for p in role.permissions],
            role_id=role.id,
        )
        if not admin_guard.ok:
            flash(admin_guard.reason, 'danger')
            return redirect(url_for('users.list_roles'))

        errors = {}
        if not display_name:
            errors['display_name'] = 'Display name is required.'

        if not errors:
            try:
                old_permissions = list(role.permissions)

                role.display_name = display_name
                role.description = description or None

                if permission_ids:
                    permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
                    role.permissions = permissions
                else:
                    role.permissions = []
                
                db.session.commit()
                
                AuditService.log_permission_changed(
                    role_id, current_user.id,
                    old_permissions, role.permissions
                )
                
                flash('Role updated successfully.', 'success')
                return redirect(url_for('users.list_roles'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating role: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    permissions = Permission.query.order_by(Permission.module, Permission.action).all()
    permissions_by_module = {}
    for p in permissions:
        if p.module not in permissions_by_module:
            permissions_by_module[p.module] = []
        permissions_by_module[p.module].append(p)
    
    role_permission_ids = [p.id for p in role.permissions]
    
    return render_template('users/edit_role.html',
                           role=role,
                           permissions_by_module=permissions_by_module,
                           role_permission_ids=role_permission_ids)


@users_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
@can_manage_roles
def delete_role(role_id):
    """Delete a role."""
    role = Role.query.get_or_404(role_id)
    
    if role.is_system:
        flash('System roles cannot be deleted.', 'danger')
        return redirect(url_for('users.list_roles'))
    
    # Check if role is assigned to users
    if role.users.count() > 0:
        flash('Cannot delete role assigned to users.', 'danger')
        return redirect(url_for('users.list_roles'))
    
    db.session.delete(role)
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='delete_role',
        entity_type='role',
        entity_id=role_id,
        entity_repr=role.name,
        category='security',
        severity='warning',
    )
    
    flash('Role deleted successfully.', 'success')
    return redirect(url_for('users.list_roles'))


@users_bp.route('/roles/<int:role_id>/toggle', methods=['POST'])
@login_required
@can_manage_roles
def toggle_role(role_id):
    """Activate or deactivate a role."""
    role = Role.query.get_or_404(role_id)
    new_state = not role.is_active

    # When deactivating the admin role, ensure active admins still hold it
    # through at least one OTHER active role or there must be a safe
    # replacement process. The protection service enforces this.
    if not new_state and role.name == 'admin':
        check = AdminProtectionService.can_deactivate_admin_role(current_user)
        if not check.ok:
            flash(check.reason, 'danger')
            return redirect(url_for('users.list_roles'))

    role.is_active = new_state
    role.updated_by_user_id = current_user.id
    db.session.commit()

    AuditService.log_action(
        user_id=current_user.id,
        action='toggle_role',
        entity_type='role',
        entity_id=role.id,
        entity_repr=role.name,
        new_values={'is_active': new_state},
        category='security',
        severity='warning',
    )

    status = 'activated' if new_state else 'deactivated'
    flash(f'Role "{role.display_name}" {status}.', 'success')
    return redirect(url_for('users.list_roles'))


@users_bp.route('/permissions')
@login_required
@can_manage_roles
def list_permissions():
    """List all permissions."""
    permissions = Permission.query.order_by(Permission.module, Permission.action).all()
    return render_template('users/permissions.html', permissions=permissions)


# Import needed
from app.extensions import db