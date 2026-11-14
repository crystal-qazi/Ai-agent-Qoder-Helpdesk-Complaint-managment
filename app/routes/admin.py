from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    Department, SoftwareCatalog, Category, Priority, Status,
    SLAPolicy, WorkingSchedule, Holiday, SystemSetting, User, Complaint
)
from app.services.audit import AuditService
from app.permissions.decorators import can_manage_config, can_view_audit_logs
from app.validators.config import (
    validate_department_data, validate_software_data,
    validate_category_data, validate_priority_data,
    validate_status_data, validate_sla_policy_data,
    validate_working_schedule_data, validate_holiday_data,
    validate_system_setting_data
)
import json
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _unique_code(model, name, max_length=30):
    """Build a unique uppercase code from a display name."""
    base = ''.join(ch if ch.isalnum() else '_' for ch in name.upper()).strip('_')[:max_length] or 'ITEM'
    code = base
    counter = 2
    while model.query.filter_by(code=code).first():
        suffix = f'_{counter}'
        code = base[:max_length - len(suffix)] + suffix
        counter += 1
    return code


# ============================================================
# Departments
# ============================================================

@admin_bp.route('/departments')
@login_required
@can_manage_config
def list_departments():
    """List all departments."""
    departments = Department.query.order_by(Department.name).all()
    return render_template('admin/departments.html', departments=departments)


@admin_bp.route('/departments/create', methods=['GET', 'POST'])
@login_required
@can_manage_config
def create_department():
    """Create a new department."""
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        
        errors = validate_department_data(data)
        
        if not errors:
            try:
                dept = Department(
                    name=data['name'].strip(),
                    code=data['code'].strip().upper(),
                    description=data.get('description', '').strip() or None,
                    location=data.get('location', '').strip() or None,
                    phone=data.get('phone', '').strip() or None,
                    email=data.get('email', '').strip() or None,
                    is_active=data.get('is_active', True),
                )
                db.session.add(dept)
                db.session.commit()
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_department',
                    entity_type='department',
                    entity_id=dept.id,
                    entity_repr=dept.name,
                    new_values={'name': dept.name, 'code': dept.code},
                    category='config',
                )
                
                flash('Department created successfully.', 'success')
                return redirect(url_for('admin.list_departments'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating department: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    return render_template('admin/department_form.html')


@admin_bp.route('/departments/<int:dept_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_config
def edit_department(dept_id):
    """Edit a department."""
    dept = Department.query.get_or_404(dept_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        
        errors = validate_department_data(data, dept_id)
        
        if not errors:
            try:
                old_values = {
                    'name': dept.name,
                    'code': dept.code,
                    'description': dept.description,
                    'location': dept.location,
                    'phone': dept.phone,
                    'email': dept.email,
                    'is_active': dept.is_active,
                }
                
                dept.name = data['name'].strip()
                dept.code = data['code'].strip().upper()
                dept.description = data.get('description', '').strip() or None
                dept.location = data.get('location', '').strip() or None
                dept.phone = data.get('phone', '').strip() or None
                dept.email = data.get('email', '').strip() or None
                dept.is_active = data.get('is_active', True)
                dept.updated_by_user_id = current_user.id
                
                db.session.commit()
                
                new_values = {
                    'name': dept.name,
                    'code': dept.code,
                    'description': dept.description,
                    'location': dept.location,
                    'phone': dept.phone,
                    'email': dept.email,
                    'is_active': dept.is_active,
                }
                
                changed_fields = [k for k in old_values if old_values[k] != new_values.get(k)]
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='update_department',
                    entity_type='department',
                    entity_id=dept.id,
                    entity_repr=dept.name,
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    category='config',
                )
                
                flash('Department updated successfully.', 'success')
                return redirect(url_for('admin.list_departments'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating department: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    return render_template('admin/department_form.html', department=dept)


@admin_bp.route('/departments/<int:dept_id>/toggle', methods=['POST'])
@login_required
@can_manage_config
def toggle_department(dept_id):
    """Toggle department active status."""
    dept = Department.query.get_or_404(dept_id)
    dept.is_active = not dept.is_active
    dept.updated_by_user_id = current_user.id
    db.session.commit()
    
    action = 'activate' if dept.is_active else 'deactivate'
    AuditService.log_action(
        user_id=current_user.id,
        action=f'{action}_department',
        entity_type='department',
        entity_id=dept.id,
        entity_repr=dept.name,
        category='config',
    )
    
    flash(f'Department {action}d successfully.', 'success')
    return redirect(url_for('admin.list_departments'))


@admin_bp.route('/departments/<int:dept_id>/delete', methods=['POST'])
@login_required
@can_manage_config
def delete_department(dept_id):
    """Delete a department."""
    dept = Department.query.get_or_404(dept_id)
    
    # Check if department is used
    if Complaint.query.filter_by(department_id=dept.id).count() > 0:
        flash('Cannot delete department with active complaints.', 'danger')
        return redirect(url_for('admin.list_departments'))
    
    db.session.delete(dept)
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='delete_department',
        entity_type='department',
        entity_id=dept.id,
        entity_repr=dept.name,
        category='config',
    )
    
    flash('Department deleted successfully.', 'success')
    return redirect(url_for('admin.list_departments'))


# ============================================================
# Software Catalog
# ============================================================

@admin_bp.route('/software')
@login_required
@can_manage_config
def list_software():
    """List all software."""
    software = SoftwareCatalog.query.order_by(SoftwareCatalog.name).all()
    return render_template('admin/software.html', software=software)


@admin_bp.route('/software/create', methods=['GET', 'POST'])
@login_required
@can_manage_config
def create_software():
    """Create a new software entry."""
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        
        errors = validate_software_data(data)
        
        if not errors:
            try:
                license_expiry = data.get('license_expiry') or None
                if license_expiry:
                    license_expiry = datetime.strptime(license_expiry, '%Y-%m-%d').date()

                sw = SoftwareCatalog(
                    name=data['name'].strip(),
                    code=data['code'].strip().upper(),
                    version=data.get('version', '').strip() or None,
                    vendor=data.get('vendor', '').strip() or None,
                    license_type=data.get('license_type', '').strip() or None,
                    license_expiry=license_expiry,
                    vendor_support_url=data.get('vendor_support_url', '').strip() or None,
                    description=data.get('description', '').strip() or None,
                    department_id=data.get('department_id') or None,
                    is_active=data.get('is_active', True),
                )
                db.session.add(sw)
                db.session.commit()
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_software',
                    entity_type='software',
                    entity_id=sw.id,
                    entity_repr=sw.name,
                    new_values={'name': sw.name, 'code': sw.code},
                    category='config',
                )
                
                flash('Software added successfully.', 'success')
                return redirect(url_for('admin.list_software'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding software: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    return render_template('admin/software_form.html', departments=departments)


@admin_bp.route('/software/<int:sw_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_config
def edit_software(sw_id):
    """Edit a software entry."""
    sw = SoftwareCatalog.query.get_or_404(sw_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        
        if data.get('license_expiry'):
            try:
                data['license_expiry'] = datetime.strptime(data['license_expiry'], '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for license expiry.', 'danger')
                return redirect(url_for('admin.edit_software', sw_id=sw_id))
        
        errors = validate_software_data(data, sw_id)
        
        if not errors:
            try:
                old_values = {
                    'name': sw.name,
                    'code': sw.code,
                    'version': sw.version,
                    'vendor': sw.vendor,
                    'license_type': sw.license_type,
                    'license_expiry': sw.license_expiry,
                    'vendor_support_url': sw.vendor_support_url,
                    'is_active': sw.is_active,
                }
                
                sw.name = data['name'].strip()
                sw.code = data['code'].strip().upper()
                sw.version = data.get('version', '').strip() or None
                sw.vendor = data.get('vendor', '').strip() or None
                sw.license_type = data.get('license_type', '').strip() or None
                sw.license_expiry = data.get('license_expiry')
                sw.vendor_support_url = data.get('vendor_support_url', '').strip() or None
                sw.description = data.get('description', '').strip() or None
                sw.department_id = data.get('department_id') or None
                sw.is_active = data.get('is_active', True)
                sw.updated_by_user_id = current_user.id
                
                db.session.commit()
                
                new_values = {
                    'name': sw.name,
                    'code': sw.code,
                    'version': sw.version,
                    'vendor': sw.vendor,
                    'license_type': sw.license_type,
                    'license_expiry': sw.license_expiry,
                    'vendor_support_url': sw.vendor_support_url,
                    'is_active': sw.is_active,
                }
                
                changed_fields = [k for k in old_values if old_values[k] != new_values.get(k)]
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='update_software',
                    entity_type='software',
                    entity_id=sw.id,
                    entity_repr=sw.name,
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    category='config',
                )
                
                flash('Software updated successfully.', 'success')
                return redirect(url_for('admin.list_software'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating software: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    return render_template('admin/software_form.html', software=sw, departments=departments)


@admin_bp.route('/software/<int:sw_id>/toggle', methods=['POST'])
@login_required
@can_manage_config
def toggle_software(sw_id):
    """Toggle software active status."""
    sw = SoftwareCatalog.query.get_or_404(sw_id)
    sw.is_active = not sw.is_active
    sw.updated_by_user_id = current_user.id
    db.session.commit()
    
    action = 'activated' if sw.is_active else 'deactivated'
    AuditService.log_action(
        user_id=current_user.id,
        action=f'toggle_software',
        entity_type='software',
        entity_id=sw.id,
        entity_repr=sw.name,
        category='config',
    )
    
    flash(f'Software {action} successfully.', 'success')
    return redirect(url_for('admin.list_software'))


# ============================================================
# Categories
# ============================================================

@admin_bp.route('/categories')
@login_required
@can_manage_config
def list_categories():
    """List all categories."""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@can_manage_config
def create_category():
    """Create a new category."""
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['requires_asset'] = 'requires_asset' in data
        
        if data.get('parent_id'):
            data['parent_id'] = int(data['parent_id'])
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        if data.get('sla_policy_id'):
            data['sla_policy_id'] = int(data['sla_policy_id'])
        if data.get('default_sla_policy_id'):
            data['default_sla_policy_id'] = int(data['default_sla_policy_id'])
        if data.get('auto_assign_to_id'):
            data['auto_assign_to_id'] = int(data['auto_assign_to_id'])
        
        errors = validate_category_data(data)
        
        if not errors:
            try:
                cat = Category(
                    name=data['name'].strip(),
                    code=_unique_code(Category, data['name']),
                    description=data.get('description', '').strip() or None,
                    parent_id=data.get('parent_id'),
                    department_id=data.get('department_id'),
                    default_sla_policy_id=data.get('default_sla_policy_id'),
                    auto_assign_to_id=data.get('auto_assign_to_id'),
                    requires_asset=data.get('requires_asset', False),
                    is_active=data.get('is_active', True),
                )
                db.session.add(cat)
                db.session.commit()
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_category',
                    entity_type='category',
                    entity_id=cat.id,
                    entity_repr=cat.name,
                    new_values={'name': cat.name},
                    category='config',
                )
                
                flash('Category created successfully.', 'success')
                return redirect(url_for('admin.list_categories'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating category: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    # Get related data for dropdowns
    parents = Category.query.filter_by(is_active=True).all()
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    sla_policies = SLAPolicy.query.filter_by(is_active=True).all()
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    return render_template('admin/category_form.html',
                           categories=parents,
                           departments=departments,
                           sla_policies=sla_policies,
                           users=users)


@admin_bp.route('/categories/<int:cat_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_config
def edit_category(cat_id):
    """Edit a category."""
    cat = Category.query.get_or_404(cat_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['requires_asset'] = 'requires_asset' in data
        
        if data.get('parent_id'):
            data['parent_id'] = int(data['parent_id'])
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        if data.get('sla_policy_id'):
            data['sla_policy_id'] = int(data['sla_policy_id'])
        if data.get('default_sla_policy_id'):
            data['default_sla_policy_id'] = int(data['default_sla_policy_id'])
        if data.get('auto_assign_to_id'):
            data['auto_assign_to_id'] = int(data['auto_assign_to_id'])
        
        errors = validate_category_data(data, cat_id)
        
        if not errors:
            try:
                old_values = {
                    'name': cat.name,
                    'parent_id': cat.parent_id,
                    'department_id': cat.department_id,
                    'default_sla_policy_id': cat.default_sla_policy_id,
                    'auto_assign_to_id': cat.auto_assign_to_id,
                    'requires_asset': cat.requires_asset,
                    'is_active': cat.is_active,
                }
                
                cat.name = data['name'].strip()
                cat.description = data.get('description', '').strip() or None
                cat.parent_id = data.get('parent_id')
                cat.department_id = data.get('department_id')
                cat.default_sla_policy_id = data.get('default_sla_policy_id')
                cat.auto_assign_to_id = data.get('auto_assign_to_id')
                cat.requires_asset = data.get('requires_asset', False)
                cat.is_active = data.get('is_active', True)
                cat.updated_by_user_id = current_user.id
                
                db.session.commit()
                
                new_values = {
                    'name': cat.name,
                    'parent_id': cat.parent_id,
                    'department_id': cat.department_id,
                    'default_sla_policy_id': cat.default_sla_policy_id,
                    'auto_assign_to_id': cat.auto_assign_to_id,
                    'requires_asset': cat.requires_asset,
                    'is_active': cat.is_active,
                }
                
                changed_fields = [k for k in old_values if old_values[k] != new_values.get(k)]
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='update_category',
                    entity_type='category',
                    entity_id=cat.id,
                    entity_repr=cat.name,
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    category='config',
                )
                
                flash('Category updated successfully.', 'success')
                return redirect(url_for('admin.list_categories'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating category: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    # Get related data for dropdowns
    parents = Category.query.filter_by(is_active=True).all()
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    sla_policies = SLAPolicy.query.filter_by(is_active=True).all()
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    return render_template('admin/category_form.html',
                           category=cat,
                           categories=parents,
                           departments=departments,
                           sla_policies=sla_policies,
                           users=users)


@admin_bp.route('/categories/<int:cat_id>/toggle', methods=['POST'])
@login_required
@can_manage_config
def toggle_category(cat_id):
    """Toggle category active status."""
    cat = Category.query.get_or_404(cat_id)
    cat.is_active = not cat.is_active
    cat.updated_by_user_id = current_user.id
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='toggle_category',
        entity_type='category',
        entity_id=cat.id,
        entity_repr=cat.name,
        category='config',
    )
    
    flash('Category status toggled successfully.', 'success')
    return redirect(url_for('admin.list_categories'))


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
@can_manage_config
def delete_category(cat_id):
    """Delete a category."""
    cat = Category.query.get_or_404(cat_id)
    
    if Complaint.query.filter_by(category_id=cat.id).count() > 0:
        flash('Cannot delete category with existing complaints.', 'danger')
        return redirect(url_for('admin.list_categories'))
    
    if Category.query.filter_by(parent_id=cat.id).count() > 0:
        flash('Cannot delete a category that has child categories.', 'danger')
        return redirect(url_for('admin.list_categories'))
    
    db.session.delete(cat)
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='delete_category',
        entity_type='category',
        entity_id=cat.id,
        entity_repr=cat.name,
        category='config',
    )
    
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('admin.list_categories'))


# ============================================================
# Priorities
# ============================================================

@admin_bp.route('/priorities')
@login_required
@can_manage_config
def list_priorities():
    """List all priorities."""
    priorities = Priority.query.order_by(Priority.level).all()
    return render_template('admin/priorities.html', priorities=priorities)


@admin_bp.route('/priorities/create', methods=['GET', 'POST'])
@login_required
@can_manage_config
def create_priority():
    """Create a new priority."""
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['notify_assigned'] = 'notify_assigned' in data
        data['notify_on_breach'] = 'notify_on_breach' in data
        
        if data.get('level'):
            data['level'] = int(data['level'])
        if data.get('sla_response_hours'):
            data['sla_response_hours'] = float(data['sla_response_hours'])
        if data.get('sla_resolution_hours'):
            data['sla_resolution_hours'] = float(data['sla_resolution_hours'])
        if data.get('escalation_hours'):
            data['escalation_hours'] = float(data['escalation_hours'])
        
        errors = validate_priority_data(data)
        
        if not errors:
            try:
                pri = Priority(
                    name=data['name'].strip(),
                    code=data['code'].strip().upper(),
                    level=data['level'],
                    color=data['color'],
                    sla_response_hours=data.get('sla_response_hours'),
                    sla_resolution_hours=data.get('sla_resolution_hours'),
                    escalation_hours=data.get('escalation_hours'),
                    notify_assigned=data.get('notify_assigned', False),
                    notify_on_breach=data.get('notify_on_breach', False),
                    is_active=data.get('is_active', True),
                )
                db.session.add(pri)
                db.session.commit()
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_priority',
                    entity_type='priority',
                    entity_id=pri.id,
                    entity_repr=pri.name,
                    new_values={'name': pri.name, 'code': pri.code},
                    category='config',
                )
                
                flash('Priority created successfully.', 'success')
                return redirect(url_for('admin.list_priorities'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating priority: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    return render_template('admin/priority_form.html')


@admin_bp.route('/priorities/<int:priority_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_config
def edit_priority(priority_id):
    """Edit a priority."""
    pri = Priority.query.get_or_404(priority_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['notify_assigned'] = 'notify_assigned' in data
        data['notify_on_breach'] = 'notify_on_breach' in data
        
        if data.get('level'):
            data['level'] = int(data['level'])
        if data.get('sla_response_hours'):
            data['sla_response_hours'] = float(data['sla_response_hours'])
        if data.get('sla_resolution_hours'):
            data['sla_resolution_hours'] = float(data['sla_resolution_hours'])
        if data.get('escalation_hours'):
            data['escalation_hours'] = float(data['escalation_hours'])
        
        errors = validate_priority_data(data, priority_id)
        
        if not errors:
            try:
                old_values = {
                    'name': pri.name,
                    'code': pri.code,
                    'level': pri.level,
                    'color': pri.color,
                    'sla_response_hours': pri.sla_response_hours,
                    'sla_resolution_hours': pri.sla_resolution_hours,
                    'escalation_hours': pri.escalation_hours,
                    'notify_assigned': pri.notify_assigned,
                    'notify_on_breach': pri.notify_on_breach,
                    'is_active': pri.is_active,
                }
                
                pri.name = data['name'].strip()
                pri.code = data['code'].strip().upper()
                pri.level = data['level']
                pri.color = data['color']
                pri.sla_response_hours = data.get('sla_response_hours')
                pri.sla_resolution_hours = data.get('sla_resolution_hours')
                pri.escalation_hours = data.get('escalation_hours')
                pri.notify_assigned = data.get('notify_assigned', False)
                pri.notify_on_breach = data.get('notify_on_breach', False)
                pri.is_active = data.get('is_active', True)
                pri.updated_by_user_id = current_user.id
                
                db.session.commit()
                
                new_values = {
                    'name': pri.name,
                    'code': pri.code,
                    'level': pri.level,
                    'color': pri.color,
                    'sla_response_hours': pri.sla_response_hours,
                    'sla_resolution_hours': pri.sla_resolution_hours,
                    'escalation_hours': pri.escalation_hours,
                    'notify_assigned': pri.notify_assigned,
                    'notify_on_breach': pri.notify_on_breach,
                    'is_active': pri.is_active,
                }
                
                changed_fields = [k for k in old_values if old_values[k] != new_values.get(k)]
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='update_priority',
                    entity_type='priority',
                    entity_id=pri.id,
                    entity_repr=pri.name,
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    category='config',
                )
                
                flash('Priority updated successfully.', 'success')
                return redirect(url_for('admin.list_priorities'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating priority: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    return render_template('admin/priority_form.html', priority=pri)


@admin_bp.route('/priorities/<int:priority_id>/toggle', methods=['POST'])
@login_required
@can_manage_config
def toggle_priority(priority_id):
    """Toggle priority active status."""
    pri = Priority.query.get_or_404(priority_id)
    pri.is_active = not pri.is_active
    pri.updated_by_user_id = current_user.id
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='toggle_priority',
        entity_type='priority',
        entity_id=pri.id,
        entity_repr=pri.name,
        category='config',
    )
    
    flash('Priority status toggled successfully.', 'success')
    return redirect(url_for('admin.list_priorities'))


@admin_bp.route('/priorities/<int:priority_id>/delete', methods=['POST'])
@login_required
@can_manage_config
def delete_priority(priority_id):
    """Delete a priority."""
    pri = Priority.query.get_or_404(priority_id)
    
    # Check if priority is used
    if Complaint.query.filter_by(priority_id=pri.id).count() > 0:
        flash('Cannot delete priority with active complaints.', 'danger')
        return redirect(url_for('admin.list_priorities'))
    
    db.session.delete(pri)
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='delete_priority',
        entity_type='priority',
        entity_id=pri.id,
        entity_repr=pri.name,
        category='config',
    )
    
    flash('Priority deleted successfully.', 'success')
    return redirect(url_for('admin.list_priorities'))


# ============================================================
# Statuses
# ============================================================

@admin_bp.route('/statuses')
@login_required
@can_manage_config
def list_statuses():
    """List all statuses."""
    statuses = Status.query.order_by(Status.sort_order, Status.name).all()
    return render_template('admin/statuses.html', statuses=statuses)


@admin_bp.route('/statuses/create', methods=['GET', 'POST'])
@login_required
@can_manage_config
def create_status():
    """Create a new status."""
    if request.method == 'POST':
        data = request.form.to_dict()
        for flag in ('is_active', 'is_initial', 'is_terminal', 'requires_reason', 'requires_resolution'):
            data[flag] = flag in data

        transitions_json = data.get('allowed_transitions', '').strip()
        if transitions_json:
            try:
                data['allowed_transitions'] = json.loads(transitions_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in allowed transitions.', 'danger')
                return redirect(url_for('admin.create_status'))

        errors = validate_status_data(data)

        if not errors:
            try:
                status = Status(
                    name=data['name'].strip(),
                    code=data['code'].strip().lower(),
                    category=data.get('category', 'open'),
                    color=data.get('color', '#6B7280'),
                    icon=data.get('icon') or None,
                    description=data.get('description', '').strip() or None,
                    is_initial=data.get('is_initial', False),
                    is_terminal=data.get('is_terminal', False),
                    requires_reason=data.get('requires_reason', False),
                    requires_resolution=data.get('requires_resolution', False),
                    sort_order=int(data.get('sort_order') or 0),
                    is_active=data.get('is_active', True),
                    allowed_transitions=data.get('allowed_transitions'),
                )
                db.session.add(status)
                db.session.commit()

                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_status',
                    entity_type='status',
                    entity_id=status.id,
                    entity_repr=status.name,
                    new_values={'name': status.name, 'code': status.code},
                    category='config',
                )

                flash('Status created successfully.', 'success')
                return redirect(url_for('admin.list_statuses'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating status: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')

    all_statuses = Status.query.order_by(Status.sort_order).all()
    return render_template('admin/status_form.html', status=None, all_statuses=all_statuses)


@admin_bp.route('/statuses/<int:status_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_config
def edit_status(status_id):
    """Edit a status."""
    status = Status.query.get_or_404(status_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        for flag in ('is_active', 'is_initial', 'is_terminal', 'requires_reason', 'requires_resolution'):
            data[flag] = flag in data

        transitions_json = data.get('allowed_transitions', '').strip()
        if transitions_json:
            try:
                data['allowed_transitions'] = json.loads(transitions_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in allowed transitions.', 'danger')
                return redirect(url_for('admin.edit_status', status_id=status_id))

        errors = validate_status_data(data, status_id)

        if not errors:
            try:
                old_values = {
                    'name': status.name,
                    'code': status.code,
                    'category': status.category,
                    'color': status.color,
                    'sort_order': status.sort_order,
                    'is_initial': status.is_initial,
                    'is_terminal': status.is_terminal,
                    'requires_reason': status.requires_reason,
                    'requires_resolution': status.requires_resolution,
                    'is_active': status.is_active,
                }

                status.name = data['name'].strip()
                status.code = data['code'].strip().lower()
                status.category = data.get('category', status.category)
                status.color = data.get('color', status.color)
                status.icon = data.get('icon') or None
                status.sort_order = int(data.get('sort_order') or 0)
                status.description = data.get('description', '').strip() or None
                status.is_initial = data.get('is_initial', False)
                status.is_terminal = data.get('is_terminal', False)
                status.requires_reason = data.get('requires_reason', False)
                status.requires_resolution = data.get('requires_resolution', False)
                status.is_active = data.get('is_active', True)
                status.allowed_transitions = data.get('allowed_transitions')
                status.updated_by_user_id = current_user.id

                db.session.commit()

                new_values = {
                    'name': status.name,
                    'code': status.code,
                    'category': status.category,
                    'color': status.color,
                    'sort_order': status.sort_order,
                    'is_initial': status.is_initial,
                    'is_terminal': status.is_terminal,
                    'requires_reason': status.requires_reason,
                    'requires_resolution': status.requires_resolution,
                    'is_active': status.is_active,
                }

                changed_fields = [k for k in old_values if old_values[k] != new_values.get(k)]

                AuditService.log_action(
                    user_id=current_user.id,
                    action='update_status',
                    entity_type='status',
                    entity_id=status.id,
                    entity_repr=status.name,
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    category='config',
                )

                flash('Status updated successfully.', 'success')
                return redirect(url_for('admin.list_statuses'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating status: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')

    all_statuses = Status.query.order_by(Status.sort_order).all()
    return render_template('admin/status_form.html', status=status, all_statuses=all_statuses)


@admin_bp.route('/statuses/<int:status_id>/toggle', methods=['POST'])
@login_required
@can_manage_config
def toggle_status(status_id):
    """Toggle status active status."""
    status = Status.query.get_or_404(status_id)
    status.is_active = not status.is_active
    status.updated_by_user_id = current_user.id
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='toggle_status',
        entity_type='status',
        entity_id=status.id,
        entity_repr=status.name,
        category='config',
    )
    
    flash('Status toggled successfully.', 'success')
    return redirect(url_for('admin.list_statuses'))


@admin_bp.route('/statuses/<int:status_id>/delete', methods=['POST'])
@login_required
@can_manage_config
def delete_status(status_id):
    """Delete a status."""
    status = Status.query.get_or_404(status_id)
    
    # Check if status is used
    if Complaint.query.filter_by(status_id=status.id).count() > 0:
        flash('Cannot delete status with active complaints.', 'danger')
        return redirect(url_for('admin.list_statuses'))
    
    db.session.delete(status)
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='delete_status',
        entity_type='status',
        entity_id=status.id,
        entity_repr=status.name,
        category='config',
    )
    
    flash('Status deleted successfully.', 'success')
    return redirect(url_for('admin.list_statuses'))


# ============================================================
# SLA Policies
# ============================================================

@admin_bp.route('/sla')
@login_required
@can_manage_config
def list_sla_policies():
    """List all SLA policies."""
    policies = SLAPolicy.query.order_by(SLAPolicy.sort_order, SLAPolicy.name).all()
    return render_template('admin/sla_policies.html', policies=policies)


@admin_bp.route('/sla/create', methods=['GET', 'POST'])
@login_required
@can_manage_config
def create_sla_policy():
    """Create a new SLA policy."""
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['is_default'] = 'is_default' in data
        data['use_business_hours'] = 'use_business_hours' in data
        data['escalation_enabled'] = 'escalation_enabled' in data
        data['pause_on_pending_info'] = 'pause_on_pending_info' in data
        data['pause_on_hold'] = 'pause_on_hold' in data
        data['pause_on_reassignment'] = 'pause_on_reassignment' in data
        data['pause_on_reopen'] = 'pause_on_reopen' in data
        
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        if data.get('priority_id'):
            data['priority_id'] = int(data['priority_id'])
        if data.get('category_id'):
            data['category_id'] = int(data['category_id'])
        if data.get('working_schedule_id'):
            data['working_schedule_id'] = int(data['working_schedule_id'])
        if data.get('response_target_minutes'):
            data['response_target_minutes'] = int(data['response_target_minutes'])
        if data.get('resolution_target_minutes'):
            data['resolution_target_minutes'] = int(data['resolution_target_minutes'])
        if data.get('sort_order'):
            data['sort_order'] = int(data['sort_order'])
        
        # Parse escalation levels JSON
        escalation_json = data.get('escalation_levels', '').strip()
        if escalation_json:
            try:
                data['escalation_levels'] = json.loads(escalation_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in escalation levels.', 'danger')
                return redirect(url_for('admin.create_sla_policy'))
        
        # Parse pause on status IDs JSON
        pause_status_json = data.get('pause_on_status_ids', '').strip()
        if pause_status_json:
            try:
                data['pause_on_status_ids'] = json.loads(pause_status_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in pause on status IDs.', 'danger')
                return redirect(url_for('admin.create_sla_policy'))
        
        errors = validate_sla_policy_data(data)
        
        if not errors:
            try:
                policy = SLAPolicy(
                    name=data['name'].strip(),
                    description=data.get('description', '').strip() or None,
                    department_id=data.get('department_id'),
                    priority_id=data.get('priority_id'),
                    category_id=data.get('category_id'),
                    response_target_minutes=data.get('response_target_minutes', 0),
                    resolution_target_minutes=data.get('resolution_target_minutes', 0),
                    use_business_hours=data.get('use_business_hours', True),
                    working_schedule_id=data.get('working_schedule_id'),
                    escalation_enabled=data.get('escalation_enabled', False),
                    escalation_levels=data.get('escalation_levels'),
                    pause_on_pending_info=data.get('pause_on_pending_info', True),
                    pause_on_hold=data.get('pause_on_hold', True),
                    pause_on_reassignment=data.get('pause_on_reassignment', False),
                    pause_on_reopen=data.get('pause_on_reopen', True),
                    pause_on_status_ids=data.get('pause_on_status_ids'),
                    is_active=data.get('is_active', True),
                    is_default=data.get('is_default', False),
                    sort_order=data.get('sort_order', 0),
                )
                db.session.add(policy)
                db.session.commit()
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_sla_policy',
                    entity_type='sla_policy',
                    entity_id=policy.id,
                    entity_repr=policy.name,
                    new_values={'name': policy.name},
                    category='config',
                )
                
                flash('SLA policy created successfully.', 'success')
                return redirect(url_for('admin.list_sla_policies'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating SLA policy: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    # Get related data for dropdowns
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    priorities = Priority.query.filter_by(is_active=True).order_by(Priority.level).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    working_schedules = WorkingSchedule.query.filter_by(is_active=True).order_by(WorkingSchedule.name).all()
    
    return render_template('admin/create_sla_policy.html',
                           departments=departments,
                           priorities=priorities,
                           categories=categories,
                           working_schedules=working_schedules)


@admin_bp.route('/sla/<int:policy_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_config
def edit_sla_policy(policy_id):
    """Edit an SLA policy."""
    policy = SLAPolicy.query.get_or_404(policy_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['is_default'] = 'is_default' in data
        data['use_business_hours'] = 'use_business_hours' in data
        data['escalation_enabled'] = 'escalation_enabled' in data
        data['pause_on_pending_info'] = 'pause_on_pending_info' in data
        data['pause_on_hold'] = 'pause_on_hold' in data
        data['pause_on_reassignment'] = 'pause_on_reassignment' in data
        data['pause_on_reopen'] = 'pause_on_reopen' in data
        
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        if data.get('priority_id'):
            data['priority_id'] = int(data['priority_id'])
        if data.get('category_id'):
            data['category_id'] = int(data['category_id'])
        if data.get('working_schedule_id'):
            data['working_schedule_id'] = int(data['working_schedule_id'])
        if data.get('response_target_minutes'):
            data['response_target_minutes'] = int(data['response_target_minutes'])
        if data.get('resolution_target_minutes'):
            data['resolution_target_minutes'] = int(data['resolution_target_minutes'])
        if data.get('sort_order'):
            data['sort_order'] = int(data['sort_order'])
        
        # Parse escalation levels JSON
        escalation_json = data.get('escalation_levels', '').strip()
        if escalation_json:
            try:
                data['escalation_levels'] = json.loads(escalation_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in escalation levels.', 'danger')
                return redirect(url_for('admin.edit_sla_policy', policy_id=policy_id))
        
        # Parse pause on status IDs JSON
        pause_status_json = data.get('pause_on_status_ids', '').strip()
        if pause_status_json:
            try:
                data['pause_on_status_ids'] = json.loads(pause_status_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in pause on status IDs.', 'danger')
                return redirect(url_for('admin.edit_sla_policy', policy_id=policy_id))
        
        errors = validate_sla_policy_data(data, policy_id)
        
        if not errors:
            try:
                old_values = {
                    'name': policy.name,
                    'description': policy.description,
                    'department_id': policy.department_id,
                    'priority_id': policy.priority_id,
                    'category_id': policy.category_id,
                    'response_target_minutes': policy.response_target_minutes,
                    'resolution_target_minutes': policy.resolution_target_minutes,
                    'use_business_hours': policy.use_business_hours,
                    'working_schedule_id': policy.working_schedule_id,
                    'escalation_enabled': policy.escalation_enabled,
                    'escalation_levels': policy.escalation_levels,
                    'pause_on_pending_info': policy.pause_on_pending_info,
                    'pause_on_hold': policy.pause_on_hold,
                    'pause_on_reassignment': policy.pause_on_reassignment,
                    'pause_on_reopen': policy.pause_on_reopen,
                    'pause_on_status_ids': policy.pause_on_status_ids,
                    'is_active': policy.is_active,
                    'is_default': policy.is_default,
                    'sort_order': policy.sort_order,
                }
                
                policy.name = data['name'].strip()
                policy.description = data.get('description', '').strip() or None
                policy.department_id = data.get('department_id')
                policy.priority_id = data.get('priority_id')
                policy.category_id = data.get('category_id')
                policy.response_target_minutes = data.get('response_target_minutes', 0)
                policy.resolution_target_minutes = data.get('resolution_target_minutes', 0)
                policy.use_business_hours = data.get('use_business_hours', True)
                policy.working_schedule_id = data.get('working_schedule_id')
                policy.escalation_enabled = data.get('escalation_enabled', False)
                policy.escalation_levels = data.get('escalation_levels')
                policy.pause_on_pending_info = data.get('pause_on_pending_info', True)
                policy.pause_on_hold = data.get('pause_on_hold', True)
                policy.pause_on_reassignment = data.get('pause_on_reassignment', False)
                policy.pause_on_reopen = data.get('pause_on_reopen', True)
                policy.pause_on_status_ids = data.get('pause_on_status_ids')
                policy.is_active = data.get('is_active', True)
                policy.is_default = data.get('is_default', False)
                policy.sort_order = data.get('sort_order', 0)
                policy.updated_by_user_id = current_user.id
                
                db.session.commit()
                
                new_values = {
                    'name': policy.name,
                    'description': policy.description,
                    'department_id': policy.department_id,
                    'priority_id': policy.priority_id,
                    'category_id': policy.category_id,
                    'response_target_minutes': policy.response_target_minutes,
                    'resolution_target_minutes': policy.resolution_target_minutes,
                    'use_business_hours': policy.use_business_hours,
                    'working_schedule_id': policy.working_schedule_id,
                    'escalation_enabled': policy.escalation_enabled,
                    'escalation_levels': policy.escalation_levels,
                    'pause_on_pending_info': policy.pause_on_pending_info,
                    'pause_on_hold': policy.pause_on_hold,
                    'pause_on_reassignment': policy.pause_on_reassignment,
                    'pause_on_reopen': policy.pause_on_reopen,
                    'pause_on_status_ids': policy.pause_on_status_ids,
                    'is_active': policy.is_active,
                    'is_default': policy.is_default,
                    'sort_order': policy.sort_order,
                }
                
                changed_fields = [k for k in old_values if old_values[k] != new_values.get(k)]
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='update_sla_policy',
                    entity_type='sla_policy',
                    entity_id=policy.id,
                    entity_repr=policy.name,
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    category='config',
                )
                
                flash('SLA policy updated successfully.', 'success')
                return redirect(url_for('admin.list_sla_policies'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating SLA policy: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    # Get related data for dropdowns
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    priorities = Priority.query.filter_by(is_active=True).order_by(Priority.level).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    working_schedules = WorkingSchedule.query.filter_by(is_active=True).order_by(WorkingSchedule.name).all()
    
    # Convert JSON fields to strings for template
    escalation_levels = json.dumps(policy.escalation_levels) if policy.escalation_levels else ''
    pause_on_status_ids = json.dumps(policy.pause_on_status_ids) if policy.pause_on_status_ids else ''
    
    return render_template('admin/edit_sla_policy.html',
                           policy=policy,
                           departments=departments,
                           priorities=priorities,
                           categories=categories,
                           working_schedules=working_schedules,
                           escalation_levels=escalation_levels,
                           pause_on_status_ids=pause_on_status_ids)


@admin_bp.route('/sla/<int:policy_id>/delete', methods=['POST'])
@login_required
@can_manage_config
def delete_sla_policy(policy_id):
    """Delete (deactivate) an SLA policy."""
    policy = SLAPolicy.query.get_or_404(policy_id)
    
    # Check if policy is used in SLA history
    from app.models import SLAHistory
    if SLAHistory.query.filter_by(sla_policy_id=policy.id).count() > 0:
        flash('Cannot delete policy with SLA history. Deactivate instead.', 'danger')
        return redirect(url_for('admin.list_sla_policies'))
    
    policy.is_active = False
    policy.updated_by_user_id = current_user.id
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='delete_sla_policy',
        entity_type='sla_policy',
        entity_id=policy.id,
        entity_repr=policy.name,
        category='config',
    )
    
    flash('SLA policy deactivated successfully.', 'success')
    return redirect(url_for('admin.list_sla_policies'))


# ============================================================
# Working Schedules
# ============================================================

@admin_bp.route('/schedules')
@login_required
@can_manage_config
def list_working_schedules():
    """List all working schedules."""
    schedules = WorkingSchedule.query.order_by(WorkingSchedule.name).all()
    return render_template('admin/working_schedules.html', schedules=schedules)


@admin_bp.route('/schedules/create', methods=['GET', 'POST'])
@login_required
@can_manage_config
def create_working_schedule():
    """Create a new working schedule."""
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['is_default'] = 'is_default' in data
        
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        if data.get('sort_order'):
            data['sort_order'] = int(data['sort_order'])
        
        # Parse weekly schedule JSON
        weekly_schedule_json = data.get('weekly_schedule', '').strip()
        if weekly_schedule_json:
            try:
                data['weekly_schedule'] = json.loads(weekly_schedule_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in weekly schedule.', 'danger')
                return redirect(url_for('admin.create_working_schedule'))
        
        # Parse exceptions JSON
        exceptions_json = data.get('exceptions', '').strip()
        if exceptions_json:
            try:
                data['exceptions'] = json.loads(exceptions_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in exceptions.', 'danger')
                return redirect(url_for('admin.create_working_schedule'))
        
        errors = validate_working_schedule_data(data)
        
        if not errors:
            try:
                schedule = WorkingSchedule(
                    name=data['name'].strip(),
                    description=data.get('description', '').strip() or None,
                    timezone=data.get('timezone', 'UTC'),
                    weekly_schedule=data.get('weekly_schedule', {}),
                    exceptions=data.get('exceptions'),
                    department_id=data.get('department_id'),
                    is_active=data.get('is_active', True),
                    is_default=data.get('is_default', False),
                )
                db.session.add(schedule)
                db.session.commit()
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_working_schedule',
                    entity_type='working_schedule',
                    entity_id=schedule.id,
                    entity_repr=schedule.name,
                    new_values={'name': schedule.name},
                    category='config',
                )
                
                flash('Working schedule created successfully.', 'success')
                return redirect(url_for('admin.list_working_schedules'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating working schedule: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    return render_template('admin/create_working_schedule.html', departments=departments)


@admin_bp.route('/schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_config
def edit_working_schedule(schedule_id):
    """Edit a working schedule."""
    schedule = WorkingSchedule.query.get_or_404(schedule_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['is_default'] = 'is_default' in data
        
        if data.get('department_id'):
            data['department_id'] = int(data['department_id'])
        if data.get('sort_order'):
            data['sort_order'] = int(data['sort_order'])
        
        # Parse weekly schedule JSON
        weekly_schedule_json = data.get('weekly_schedule', '').strip()
        if weekly_schedule_json:
            try:
                data['weekly_schedule'] = json.loads(weekly_schedule_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in weekly schedule.', 'danger')
                return redirect(url_for('admin.edit_working_schedule', schedule_id=schedule_id))
        
        # Parse exceptions JSON
        exceptions_json = data.get('exceptions', '').strip()
        if exceptions_json:
            try:
                data['exceptions'] = json.loads(exceptions_json)
            except json.JSONDecodeError:
                flash('Invalid JSON in exceptions.', 'danger')
                return redirect(url_for('admin.edit_working_schedule', schedule_id=schedule_id))
        
        errors = validate_working_schedule_data(data, schedule_id)
        
        if not errors:
            try:
                old_values = {
                    'name': schedule.name,
                    'description': schedule.description,
                    'timezone': schedule.timezone,
                    'weekly_schedule': schedule.weekly_schedule,
                    'exceptions': schedule.exceptions,
                    'department_id': schedule.department_id,
                    'is_active': schedule.is_active,
                    'is_default': schedule.is_default,
                }

                schedule.name = data['name'].strip()
                schedule.description = data.get('description', '').strip() or None
                schedule.timezone = data.get('timezone', 'UTC')
                schedule.weekly_schedule = data.get('weekly_schedule', {})
                schedule.exceptions = data.get('exceptions')
                schedule.department_id = data.get('department_id')
                schedule.is_active = data.get('is_active', True)
                schedule.is_default = data.get('is_default', False)
                schedule.updated_by_user_id = current_user.id

                db.session.commit()

                new_values = {
                    'name': schedule.name,
                    'description': schedule.description,
                    'timezone': schedule.timezone,
                    'weekly_schedule': schedule.weekly_schedule,
                    'exceptions': schedule.exceptions,
                    'department_id': schedule.department_id,
                    'is_active': schedule.is_active,
                    'is_default': schedule.is_default,
                }
                
                changed_fields = [k for k in old_values if old_values[k] != new_values.get(k)]
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='update_working_schedule',
                    entity_type='working_schedule',
                    entity_id=schedule.id,
                    entity_repr=schedule.name,
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    category='config',
                )
                
                flash('Working schedule updated successfully.', 'success')
                return redirect(url_for('admin.list_working_schedules'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating working schedule: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    
    weekly_schedule = json.dumps(schedule.weekly_schedule) if schedule.weekly_schedule else ''
    exceptions = json.dumps(schedule.exceptions) if schedule.exceptions else ''
    
    return render_template('admin/edit_working_schedule.html',
                           schedule=schedule,
                           departments=departments,
                           weekly_schedule=weekly_schedule,
                           exceptions=exceptions)


@admin_bp.route('/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
@can_manage_config
def delete_working_schedule(schedule_id):
    """Delete (deactivate) a working schedule."""
    schedule = WorkingSchedule.query.get_or_404(schedule_id)
    
    # Check if schedule is used in SLA policies
    if SLAPolicy.query.filter_by(working_schedule_id=schedule.id).count() > 0:
        flash('Cannot deactivate a schedule referenced by an SLA policy. Update or remove the SLA policy reference first.', 'danger')
        return redirect(url_for('admin.list_working_schedules'))
    
    schedule.is_active = False
    schedule.updated_by_user_id = current_user.id
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='delete_working_schedule',
        entity_type='working_schedule',
        entity_id=schedule.id,
        entity_repr=schedule.name,
        category='config',
    )
    
    flash('Working schedule deactivated successfully.', 'success')
    return redirect(url_for('admin.list_working_schedules'))


# ============================================================
# Holidays
# ============================================================

@admin_bp.route('/holidays')
@login_required
@can_manage_config
def list_holidays():
    """List all holidays."""
    holidays = Holiday.query.order_by(Holiday.date.desc()).all()
    return render_template('admin/holidays.html', holidays=holidays)


@admin_bp.route('/holidays/create', methods=['GET', 'POST'])
@login_required
@can_manage_config
def create_holiday():
    """Create a new holiday."""
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['is_recurring'] = 'is_recurring' in data
        
        if data.get('date'):
            try:
                data['date'] = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'danger')
                return redirect(url_for('admin.create_holiday'))
        
        errors = validate_holiday_data(data)
        
        if not errors:
            try:
                holiday = Holiday(
                    name=data['name'].strip(),
                    date=data['date'],
                    is_recurring=data.get('is_recurring', False),
                    description=data.get('description', '').strip() or None,
                    is_active=data.get('is_active', True),
                )
                db.session.add(holiday)
                db.session.commit()
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_holiday',
                    entity_type='holiday',
                    entity_id=holiday.id,
                    entity_repr=holiday.name,
                    new_values={'name': holiday.name},
                    category='config',
                )
                
                flash('Holiday created successfully.', 'success')
                return redirect(url_for('admin.list_holidays'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating holiday: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    return render_template('admin/create_holiday.html')


@admin_bp.route('/holidays/<int:holiday_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_config
def edit_holiday(holiday_id):
    """Edit a holiday."""
    holiday = Holiday.query.get_or_404(holiday_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        data['is_recurring'] = 'is_recurring' in data
        
        if data.get('date'):
            try:
                data['date'] = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'danger')
                return redirect(url_for('admin.edit_holiday', holiday_id=holiday_id))
        
        errors = validate_holiday_data(data, holiday_id)
        
        if not errors:
            try:
                old_values = {
                    'name': holiday.name,
                    'date': holiday.date.isoformat(),
                    'is_recurring': holiday.is_recurring,
                    'description': holiday.description,
                    'is_active': holiday.is_active,
                }
                
                holiday.name = data['name'].strip()
                holiday.date = data['date']
                holiday.is_recurring = data.get('is_recurring', False)
                holiday.description = data.get('description', '').strip() or None
                holiday.is_active = data.get('is_active', True)
                holiday.updated_by_user_id = current_user.id
                
                db.session.commit()
                
                new_values = {
                    'name': holiday.name,
                    'date': holiday.date.isoformat(),
                    'is_recurring': holiday.is_recurring,
                    'description': holiday.description,
                    'is_active': holiday.is_active,
                }
                
                changed_fields = [k for k in old_values if old_values[k] != new_values.get(k)]
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='update_holiday',
                    entity_type='holiday',
                    entity_id=holiday.id,
                    entity_repr=holiday.name,
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    category='config',
                )
                
                flash('Holiday updated successfully.', 'success')
                return redirect(url_for('admin.list_holidays'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating holiday: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    return render_template('admin/edit_holiday.html', holiday=holiday)


@admin_bp.route('/holidays/<int:holiday_id>/delete', methods=['POST'])
@login_required
@can_manage_config
def delete_holiday(holiday_id):
    """Delete a holiday."""
    holiday = Holiday.query.get_or_404(holiday_id)
    
    db.session.delete(holiday)
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='delete_holiday',
        entity_type='holiday',
        entity_id=holiday.id,
        entity_repr=holiday.name,
        category='config',
    )
    
    flash('Holiday deleted successfully.', 'success')
    return redirect(url_for('admin.list_holidays'))


# ============================================================
# System Settings
# ============================================================

@admin_bp.route('/settings')
@login_required
@can_manage_config
def list_system_settings():
    """List all system settings."""
    settings = SystemSetting.query.order_by(SystemSetting.key).all()
    return render_template('admin/system_settings.html', settings=settings)


@admin_bp.route('/settings/create', methods=['GET', 'POST'])
@login_required
@can_manage_config
def create_system_setting():
    """Create a new system setting."""
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        
        errors = validate_system_setting_data(data)
        
        if not errors:
            try:
                setting = SystemSetting(
                    key=data['key'].strip(),
                    value=data.get('value', '').strip() or None,
                    description=data.get('description', '').strip() or None,
                    value_type=data.get('setting_type', 'string'),
                    category='general',
                )
                db.session.add(setting)
                db.session.commit()
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='create_system_setting',
                    entity_type='system_setting',
                    entity_id=setting.id,
                    entity_repr=setting.key,
                    new_values={'key': setting.key},
                    category='config',
                )
                
                flash('System setting created successfully.', 'success')
                return redirect(url_for('admin.list_system_settings'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating system setting: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    return render_template('admin/create_system_setting.html')


@admin_bp.route('/settings/<int:setting_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_config
def edit_system_setting(setting_id):
    """Edit a system setting."""
    setting = SystemSetting.query.get_or_404(setting_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in data
        
        errors = validate_system_setting_data(data, setting_id)
        
        if not errors:
            try:
                old_values = {
                    'key': setting.key,
                    'value': setting.value,
                    'description': setting.description,
                    'value_type': setting.value_type,
                }

                setting.key = data['key'].strip()
                setting.value = data.get('value', '').strip() or None
                setting.description = data.get('description', '').strip() or None
                setting.value_type = data.get('setting_type', 'string')
                setting.updated_by_user_id = current_user.id

                db.session.commit()

                new_values = {
                    'key': setting.key,
                    'value': setting.value,
                    'description': setting.description,
                    'value_type': setting.value_type,
                }
                
                changed_fields = [k for k in old_values if old_values[k] != new_values.get(k)]
                
                AuditService.log_action(
                    user_id=current_user.id,
                    action='update_system_setting',
                    entity_type='system_setting',
                    entity_id=setting.id,
                    entity_repr=setting.key,
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    category='config',
                )
                
                flash('System setting updated successfully.', 'success')
                return redirect(url_for('admin.list_system_settings'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating system setting: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    return render_template('admin/edit_system_setting.html', setting=setting)


@admin_bp.route('/settings/<int:setting_id>/delete', methods=['POST'])
@login_required
@can_manage_config
def delete_system_setting(setting_id):
    """Delete a system setting."""
    setting = SystemSetting.query.get_or_404(setting_id)
    
    if not setting.is_editable:
        flash('System settings cannot be deleted.', 'danger')
        return redirect(url_for('admin.list_system_settings'))
    
    db.session.delete(setting)
    db.session.commit()
    
    AuditService.log_action(
        user_id=current_user.id,
        action='delete_system_setting',
        entity_type='system_setting',
        entity_id=setting.id,
        entity_repr=setting.key,
        category='config',
    )
    
    flash('System setting deleted successfully.', 'success')
    return redirect(url_for('admin.list_system_settings'))


# ============================================================
# Admin Dashboard
# ============================================================

@admin_bp.route('/')
@login_required
@can_manage_config
def admin_dashboard():
    """Admin dashboard with overview stats."""
    from app.models import User, Complaint
    
    stats = {
        'total_users': User.query.filter_by(is_active=True).count(),
        'total_departments': Department.query.filter_by(is_active=True).count(),
        'total_software': SoftwareCatalog.query.filter_by(is_active=True).count(),
        'total_categories': Category.query.filter_by(is_active=True).count(),
        'total_priorities': Priority.query.filter_by(is_active=True).count(),
        'total_statuses': Status.query.filter_by(is_active=True).count(),
        'total_sla_policies': SLAPolicy.query.filter_by(is_active=True).count(),
        'total_working_schedules': WorkingSchedule.query.filter_by(is_active=True).count(),
        'total_holidays': Holiday.query.filter_by(is_active=True).count(),
        'total_settings': SystemSetting.query.filter_by(is_active=True).count(),
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/audit-logs')
@login_required
@can_view_audit_logs
def list_audit_logs():
    """List audit logs with filters."""
    filters = {}
    filters['action'] = request.args.get('action') or None
    filters['entity_type'] = request.args.get('entity_type') or None
    filters['category'] = request.args.get('category') or None
    filters['severity'] = request.args.get('severity') or None
    filters['ip_address'] = request.args.get('ip_address') or None
    if request.args.get('date_from'):
        try:
            filters['date_from'] = datetime.fromisoformat(request.args['date_from'])
        except (ValueError, KeyError):
            pass
    if request.args.get('date_to'):
        try:
            filters['date_to'] = datetime.fromisoformat(request.args['date_to'])
        except (ValueError, KeyError):
            pass

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    pagination = AuditService.get_audit_logs(filters, page, per_page)

    return render_template('admin/audit_logs.html',
                           pagination=pagination,
                           filters=filters)


# Alias used by templates/navigation that link to the admin home page.
admin_bp.add_url_rule('/index', 'index', admin_dashboard)
