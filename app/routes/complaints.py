"""Complaint management routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from app.extensions import db, csrf
from app.models import (
    Complaint, Category, Priority, Status, Department, SoftwareCatalog,
    User, Comment, Attachment, ComplaintAssignment, ComplaintStatusHistory
)
from app.validators.complaint import validate_complaint_data, validate_status_transition, validate_assignment_data, validate_comment_data
from app.validators.file import validate_file_upload, generate_stored_filename, sanitize_filename
from app.permissions.decorators import (
    can_view_complaint, can_edit_complaint, can_assign_complaint,
    can_change_status_complaint, can_view_all_complaints
)
from app.permissions.policy import PermissionPolicy
from app.services.complaint import ComplaintService
from app.services.sla import SLAService
from app.services.audit import AuditService


complaints_bp = Blueprint('complaints', __name__, url_prefix='/complaints')


@complaints_bp.route('/')
@login_required
def list_complaints():
    """List complaints with search and filters."""
    # Guard: users who cannot view all complaints may only access the unfiltered
    # view through "My Complaints". Restrict their base query to complaints they
    # reported or are assigned to, instead of an empty page.
    unfiltered = not any([
        request.args.get('assigned_to_user_id', type=int),
        request.args.get('reported_by_user_id', type=int),
        request.args.get('search', '').strip(),
        request.args.get('status_id', type=int),
        request.args.get('sla_status'),
    ])
    if unfiltered and not current_user.has_permission('complaints.view_all'):
        query_params_override = {
            'my_complaints': True,
        }
    else:
        query_params_override = {}

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    is_my_view = request.args.get('my') in ('1', 'true', 'True')

    # Build query params
    query_params = {
        'search': request.args.get('search', '').strip() or None,
        'status_id': request.args.get('status_id', type=int),
        'priority_id': request.args.get('priority_id', type=int),
        'category_id': request.args.get('category_id', type=int),
        'department_id': request.args.get('department_id', type=int),
        'software_id': request.args.get('software_id', type=int),
        'assigned_to_user_id': request.args.get('assigned_to_user_id', type=int),
        'reported_by_user_id': request.args.get('reported_by_user_id', type=int),
        'severity': request.args.get('severity') or None,
        'date_from': request.args.get('date_from') or None,
        'date_to': request.args.get('date_to') or None,
        'sla_status': request.args.get('sla_status') or None,
    }
    if is_my_view:
        query_params['my_complaints'] = True
    query_params.update(query_params_override)
    
    # Parse dates
    for key in ['date_from', 'date_to']:
        if query_params[key]:
            try:
                query_params[key] = datetime.fromisoformat(query_params[key])
            except ValueError:
                query_params[key] = None
    
    # Search complaints
    pagination = ComplaintService.search_complaints(query_params, current_user, page, per_page)
    
    # Get filter options
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    priorities = Priority.query.filter_by(is_active=True).order_by(Priority.level).all()
    statuses = Status.query.filter_by(is_active=True).order_by(Status.sort_order).all()
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    software = SoftwareCatalog.query.filter_by(is_active=True).order_by(SoftwareCatalog.name).all()
    
    # Get assignable users (for filter dropdown)
    assignable_users = User.query.join(User.roles).filter(
        User.is_active == True,
    ).distinct().all()
    
    return render_template('complaints/list.html',
                           pagination=pagination,
                           query_params=query_params,
                           categories=categories,
                           priorities=priorities,
                           statuses=statuses,
                           departments=departments,
                           software=software,
                           assignable_users=assignable_users)


@complaints_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_complaint():
    """Create a new complaint."""
    # Check permission
    if not current_user.has_permission('complaints.create'):
        abort(403)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Convert lists
        data['category_id'] = int(data['category_id']) if data.get('category_id') else None
        data['priority_id'] = int(data['priority_id']) if data.get('priority_id') else None
        data['department_id'] = int(data['department_id']) if data.get('department_id') else None
        data['software_id'] = int(data['software_id']) if data.get('software_id') else None

        # Reporter identity: ordinary users can only file for themselves.
        # Privileged users (complaints.view_all) may file on behalf of another
        # active user, but the selection must exist and be active.
        if current_user.has_permission('complaints.view_all'):
            selected_reporter_id = int(data['reported_by_user_id']) if data.get('reported_by_user_id') else current_user.id
            reporter = User.query.filter_by(id=selected_reporter_id, is_active=True).first()
            if reporter is None:
                flash('Selected reporter does not exist or is inactive.', 'danger')
                return redirect(url_for('complaints.create_complaint'))
            data['reported_by_user_id'] = selected_reporter_id
        else:
            data['reported_by_user_id'] = current_user.id

        data['assigned_to_user_id'] = int(data['assigned_to_user_id']) if data.get('assigned_to_user_id') else None
        data['affected_users_count'] = int(data['affected_users_count']) if data.get('affected_users_count') else 1
        
        # Parse incident_started_at
        if data.get('incident_started_at'):
            try:
                data['incident_started_at'] = datetime.fromisoformat(data['incident_started_at'])
            except ValueError:
                data['incident_started_at'] = None
        
        errors = validate_complaint_data(data)
        
        if not errors:
            try:
                complaint = ComplaintService.create_complaint(data, current_user)
                flash(f'Complaint {complaint.complaint_number} created successfully.', 'success')
                return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating complaint: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    # Get form data
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    priorities = Priority.query.filter_by(is_active=True).order_by(Priority.level).all()
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    software = SoftwareCatalog.query.filter_by(is_active=True).order_by(SoftwareCatalog.name).all()
    
    # Get users for reporter and assignee dropdowns
    if current_user.has_permission('complaints.view_all'):
        reporters = User.query.filter_by(is_active=True).order_by(User.first_name, User.last_name).all()
    else:
        reporters = [current_user]
    
    assignees = User.query.join(User.roles).filter(
        User.is_active == True,
    ).distinct().all()
    
    # Default values
    default_reporter = current_user
    
    return render_template('complaints/form.html',
                           is_edit=False,
                           categories=categories,
                           priorities=priorities,
                           departments=departments,
                           software=software,
                           reporters=reporters,
                           assignees=assignees,
                           default_reporter=default_reporter)


@complaints_bp.route('/<int:complaint_id>')
@login_required
@can_view_complaint
def view_complaint(complaint_id):
    """View complaint details."""
    complaint = Complaint.query.get_or_404(complaint_id)
    
    # Get timeline
    timeline = ComplaintService.get_complaint_timeline(complaint)
    
    # Get comments (separate internal and reporter-visible)
    internal_comments = [c for c in complaint.comments if c.visibility == 'internal']
    reporter_comments = [c for c in complaint.comments if c.visibility == 'reporter_visible']
    
    # Check permissions
    can_edit = PermissionPolicy.can_edit_complaint(current_user, complaint)
    can_assign = PermissionPolicy.can_assign_complaint(current_user, complaint)
    can_add_internal_comment = PermissionPolicy.can_add_internal_comment(current_user, complaint)
    can_add_reporter_comment = PermissionPolicy.can_add_reporter_visible_comment(current_user, complaint)
    can_upload = PermissionPolicy.can_upload_attachment(current_user, complaint)
    
    available_statuses = []
    if complaint.status:
        for s in Status.query.filter_by(is_active=True).order_by(Status.sort_order).all():
            if (s.id != complaint.status_id and complaint.status.can_transition_to(s.id)
                    and PermissionPolicy.can_change_status(current_user, complaint, s)):
                available_statuses.append(s)
    can_change_status = bool(available_statuses)
    
    # Get assignable users
    assignable_users = PermissionPolicy.get_assignable_users(complaint, current_user)
    
    return render_template('complaints/view.html',
                           complaint=complaint,
                           timeline=timeline,
                           internal_comments=internal_comments,
                           reporter_comments=reporter_comments,
                           can_edit=can_edit,
                           can_assign=can_assign,
                           can_change_status=can_change_status,
                           can_add_internal_comment=can_add_internal_comment,
                           can_add_reporter_comment=can_add_reporter_comment,
                           can_upload=can_upload,
                           available_statuses=available_statuses,
                           assignable_users=assignable_users)


@complaints_bp.route('/<int:complaint_id>/edit', methods=['GET', 'POST'])
@login_required
@can_edit_complaint
def edit_complaint(complaint_id):
    """Edit a complaint."""
    complaint = Complaint.query.get_or_404(complaint_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Convert types
        for field in ['category_id', 'priority_id', 'department_id', 'software_id', 'affected_users_count']:
            if data.get(field):
                data[field] = int(data[field])
        
        if data.get('incident_started_at'):
            try:
                data['incident_started_at'] = datetime.fromisoformat(data['incident_started_at'])
            except ValueError:
                data['incident_started_at'] = None
        
        errors = validate_complaint_data(data, complaint_id)
        
        if not errors:
            try:
                ComplaintService.update_complaint(complaint, data, current_user)
                flash('Complaint updated successfully.', 'success')
                return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating complaint: {str(e)}', 'danger')
        else:
            for field, error in errors.items():
                flash(error, 'danger')
    
    # Get form data
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    priorities = Priority.query.filter_by(is_active=True).order_by(Priority.level).all()
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    software = SoftwareCatalog.query.filter_by(is_active=True).order_by(SoftwareCatalog.name).all()
    
    return render_template('complaints/form.html',
                           is_edit=True,
                           complaint=complaint,
                           categories=categories,
                           priorities=priorities,
                           departments=departments,
                           software=software)


@complaints_bp.route('/<int:complaint_id>/assign', methods=['POST'])
@login_required
@can_assign_complaint
def assign_complaint(complaint_id):
    """Assign or reassign a complaint."""
    complaint = Complaint.query.get_or_404(complaint_id)
    
    data = request.form.to_dict()
    data['new_assignee_id'] = int(data['new_assignee_id']) if data.get('new_assignee_id') else None
    
    errors = validate_assignment_data(data)
    
    if not errors:
        success, message = ComplaintService.assign_complaint(
            complaint,
            data['new_assignee_id'],
            current_user,
            data.get('assignment_reason'),
            data.get('notes')
        )
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        for field, error in errors.items():
            flash(error, 'danger')
    
    return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))


@complaints_bp.route('/<int:complaint_id>/status', methods=['POST'])
@login_required
def change_status(complaint_id):
    """Change complaint status."""
    complaint = Complaint.query.get_or_404(complaint_id)

    # Basic access check — detailed permission is validated inside the service
    if not current_user.has_permission('complaints.change_status_own') and not current_user.has_permission('complaints.change_status_all'):
        abort(403)

    data = request.form.to_dict()
    new_status_id = int(data['status_id']) if data.get('status_id') else None

    if not new_status_id:
        flash('Status is required.', 'danger')
        return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))

    errors = validate_status_transition(complaint, new_status_id, current_user,
                                        data.get('resolution_summary'))

    if not errors:
        success, message = ComplaintService.change_status(
            complaint,
            new_status_id,
            current_user,
            data.get('reason'),
            data.get('resolution_summary')
        )
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        for field, error in errors.items():
            flash(error, 'danger')

    return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))


@complaints_bp.route('/<int:complaint_id>/comment', methods=['POST'])
@login_required
def add_comment(complaint_id):
    """Add a comment to a complaint."""
    complaint = Complaint.query.get_or_404(complaint_id)
    
    data = request.form.to_dict()
    content = data.get('content', '').strip()
    visibility = data.get('visibility', 'internal')
    
    errors = validate_comment_data({'content': content, 'visibility': visibility})
    
    if not errors:
        success, message = ComplaintService.add_comment(complaint, content, current_user, visibility)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        for field, error in errors.items():
            flash(error, 'danger')
    
    return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))


@complaints_bp.route('/<int:complaint_id>/attachment', methods=['POST'])
@login_required
def upload_attachment(complaint_id):
    """Upload an attachment to a complaint."""
    complaint = Complaint.query.get_or_404(complaint_id)
    
    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))
    
    file = request.files['file']
    description = request.form.get('description', '').strip()
    is_confidential = 'is_confidential' in request.form
    
    errors, file_info = validate_file_upload(file)
    
    if not errors:
        # Generate stored filename
        stored_filename = generate_stored_filename(file_info['original_filename'])
        
        # Ensure upload directory exists
        # Absolute path: send_file resolves relative paths against the app package, not the CWD
        upload_dir = os.path.abspath(os.path.join(current_app.config['UPLOAD_FOLDER'], 'complaints', str(complaint_id)))
        os.makedirs(upload_dir, exist_ok=True)
        
        storage_path = os.path.join(upload_dir, stored_filename)
        
        # Save file
        file.seek(0)
        file.save(storage_path)
        
        # Update file_info with storage details
        file_info['original_filename'] = file.filename
        file_info['stored_filename'] = stored_filename
        file_info['storage_path'] = storage_path
        
        success, message = ComplaintService.add_attachment(
            complaint, file_info, current_user, description, is_confidential
        )
        if success:
            flash(message, 'success')
        else:
            # Clean up file on failure
            if os.path.exists(storage_path):
                os.remove(storage_path)
            flash(message, 'danger')
    else:
        for field, error in errors.items():
            flash(error, 'danger')
    
    return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))


@complaints_bp.route('/<int:complaint_id>/attachment/<int:attachment_id>/download')
@login_required
def download_attachment(complaint_id, attachment_id):
    """Download an attachment."""
    from app.permissions.policy import PermissionPolicy
    
    attachment = Attachment.query.get_or_404(attachment_id)
    
    if attachment.complaint_id != complaint_id:
        abort(404)
    
    if not PermissionPolicy.can_download_attachment(current_user, attachment):
        abort(403)
    if not os.path.exists(attachment.storage_path):
        abort(404)
    
    # Update download count
    attachment.download_count += 1
    attachment.last_downloaded_at = datetime.utcnow()
    attachment.last_downloaded_by_user_id = current_user.id
    db.session.commit()
    
    # Log audit
    AuditService.log_action(
        user_id=current_user.id,
        action='download_attachment',
        entity_type='attachment',
        entity_id=attachment.id,
        entity_repr=attachment.original_filename,
        category='data',
    )
    
    return send_file(
        attachment.storage_path,
        as_attachment=True,
        download_name=attachment.original_filename,
        mimetype=attachment.mime_type
    )


@complaints_bp.route('/<int:complaint_id>/attachment/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(complaint_id, attachment_id):
    """Delete an attachment."""
    attachment = Attachment.query.get_or_404(attachment_id)
    
    if attachment.complaint_id != complaint_id:
        abort(404)
    
    success, message = ComplaintService.delete_attachment(attachment, current_user)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('complaints.view_complaint', complaint_id=complaint_id))


@complaints_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for searching complaints."""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    from app.permissions.policy import PermissionPolicy
    
    results = PermissionPolicy.get_accessible_complaints_query(current_user).filter(
        db.or_(
            Complaint.complaint_number.ilike(f'%{query}%'),
            Complaint.title.ilike(f'%{query}%'),
        )
    ).limit(10).all()
    
    data = []
    for c in results:
        data.append({
            'id': c.id,
            'complaint_number': c.complaint_number,
            'title': c.title,
            'status': c.status.name if c.status else '',
            'status_color': c.status.color if c.status else '#6B7280',
        })
    
    return jsonify(data)


# Import needed for query
from app.extensions import db
from flask import current_app