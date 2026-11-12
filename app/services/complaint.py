"""Complaint management service."""
from datetime import datetime
from app.extensions import db
from app.models import (
    Complaint, ComplaintAssignment, ComplaintStatusHistory,
    ComplaintHistory, Comment, Attachment, User, Status, Priority
)
from app.services.sla import SLAService
from app.services.notification import NotificationService
from app.services.audit import AuditService


class ComplaintService:
    """Service for complaint management operations."""
    
    @staticmethod
    def generate_complaint_number():
        """Generate unique sequential complaint number."""
        # Format: ITC-YYYY-NNNNNN
        year = datetime.utcnow().year
        prefix = f'ITC-{year}-'
        
        # Find the last complaint number for this year
        last_complaint = Complaint.query.filter(
            Complaint.complaint_number.like(f'{prefix}%')
        ).order_by(Complaint.complaint_number.desc()).first()
        
        if last_complaint:
            try:
                last_number = int(last_complaint.complaint_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f'{prefix}{new_number:06d}'
    
    @classmethod
    def create_complaint(cls, data, current_user):
        """Create a new complaint with all associated records."""
        # Generate complaint number
        complaint_number = cls.generate_complaint_number()
        
        # Get initial status
        initial_status = Status.query.filter_by(is_initial=True, is_active=True).first()
        if not initial_status:
            initial_status = Status.query.filter_by(is_active=True).order_by(Status.sort_order).first()
        
        # Create complaint
        complaint = Complaint(
            complaint_number=complaint_number,
            title=data['title'].strip(),
            description=data['description'].strip(),
            category_id=data['category_id'],
            priority_id=data['priority_id'],
            status_id=initial_status.id,
            department_id=data['department_id'],
            software_id=data['software_id'],
            affected_location=data.get('affected_location', '').strip() or None,
            affected_device=data.get('affected_device', '').strip() or None,
            ward_or_location=data.get('ward_or_location', '').strip() or None,
            affected_users_count=data.get('affected_users_count', 1),
            reported_by_user_id=data['reported_by_user_id'],
            reporter_name=data.get('reporter_name', '').strip() or None,
            reporter_employee_number=data.get('reporter_employee_number', '').strip() or None,
            reporter_department=data.get('reporter_department', '').strip() or None,
            reporter_extension=data.get('reporter_extension', '').strip() or None,
            reporter_contact=data.get('reporter_contact', '').strip() or None,
            reporter_patient_mrn=data.get('reporter_patient_mrn', '').strip() or None,
            created_by_user_id=current_user.id,
            assigned_to_user_id=data.get('assigned_to_user_id') or None,
            source_type=data.get('source_type', 'portal'),
            source_reference=data.get('source_reference', '').strip() or None,
            severity=data.get('severity') or None,
            assignment_notes=data.get('assignment_notes', '').strip() or None,
            incident_started_at=data.get('incident_started_at') or None,
        )
        
        db.session.add(complaint)
        db.session.flush()
        
        # Create assignment record if assigned
        if complaint.assigned_to_user_id:
            assignment = ComplaintAssignment(
                complaint_id=complaint.id,
                previous_assignee_id=None,
                new_assignee_id=complaint.assigned_to_user_id,
                assigned_by_user_id=current_user.id,
                assignment_reason=data.get('assignment_reason', '').strip() or None,
                notes=data.get('assignment_notes', '').strip() or None,
                assigned_at=datetime.utcnow(),
            )
            db.session.add(assignment)
            
            # Update complaint assigned_at
            complaint.assigned_at = datetime.utcnow()
            
            # Send assignment notification
            NotificationService.notify_assignment(complaint, current_user)
        
        # Create status history record
        status_history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            from_status_id=None,
            to_status_id=initial_status.id,
            changed_by_user_id=current_user.id,
            reason='Complaint created',
            changed_at=datetime.utcnow(),
        )
        db.session.add(status_history)
        
        # Create complaint history record
        history = ComplaintHistory(
            complaint_id=complaint.id,
            user_id=current_user.id,
            action='created',
            description=f'Complaint created with status {initial_status.name}',
            created_at=datetime.utcnow(),
        )
        db.session.add(history)
        
        # Calculate SLA
        SLAService.calculate_complaint_sla(complaint, current_user.id)
        
        # Log audit
        AuditService.log_action(
            user_id=current_user.id,
            action='create_complaint',
            entity_type='complaint',
            entity_id=complaint.id,
            entity_repr=complaint.complaint_number,
            new_values={
                'complaint_number': complaint.complaint_number,
                'title': complaint.title,
                'status': initial_status.name,
                'priority': complaint.priority.name if complaint.priority else None,
            },
            category='data',
        )
        
        db.session.commit()
        return complaint
    
    @classmethod
    def update_complaint(cls, complaint, data, current_user):
        """Update an existing complaint."""
        old_values = {}
        new_values = {}
        changed_fields = []
        
        # Track fields that can be updated
        updatable_fields = [
            'title', 'description', 'category_id', 'priority_id', 'department_id',
            'software_id', 'affected_location', 'affected_device', 'ward_or_location',
            'affected_users_count', 'reporter_name', 'reporter_employee_number',
            'reporter_department', 'reporter_extension', 'reporter_contact',
            'reporter_patient_mrn', 'severity', 'source_type', 'source_reference',
            'incident_started_at',
        ]
        
        for field in updatable_fields:
            if field in data:
                old_value = getattr(complaint, field)
                new_value = data[field]
                
                if old_value != new_value:
                    old_values[field] = old_value
                    new_values[field] = new_value
                    changed_fields.append(field)
                    setattr(complaint, field, new_value)
        
        if changed_fields:
            complaint.updated_by_user_id = current_user.id
            
            # Create history record
            history = ComplaintHistory(
                complaint_id=complaint.id,
                user_id=current_user.id,
                action='updated',
                field_name=', '.join(changed_fields),
                old_value=str(old_values),
                new_value=str(new_values),
                description=f'Updated fields: {", ".join(changed_fields)}',
                created_at=datetime.utcnow(),
            )
            db.session.add(history)
            
            # Log audit
            AuditService.log_action(
                user_id=current_user.id,
                action='update_complaint',
                entity_type='complaint',
                entity_id=complaint.id,
                entity_repr=complaint.complaint_number,
                old_values=old_values,
                new_values=new_values,
                changed_fields=changed_fields,
                category='data',
            )
            
            db.session.commit()
        
        return complaint
    
    @classmethod
    def assign_complaint(cls, complaint, new_assignee_id, current_user, reason=None, notes=None):
        """Assign or reassign a complaint."""
        previous_assignee_id = complaint.assigned_to_user_id
        
        if previous_assignee_id == new_assignee_id:
            return False, 'Complaint is already assigned to this user.'
        
        # Create assignment record
        assignment = ComplaintAssignment(
            complaint_id=complaint.id,
            previous_assignee_id=previous_assignee_id,
            new_assignee_id=new_assignee_id,
            assigned_by_user_id=current_user.id,
            assignment_reason=reason,
            notes=notes,
            assigned_at=datetime.utcnow(),
        )
        db.session.add(assignment)
        
        # Update complaint
        old_assignee = complaint.assigned_to
        complaint.assigned_to_user_id = new_assignee_id
        complaint.assigned_at = datetime.utcnow()
        complaint.updated_by_user_id = current_user.id
        
        if complaint.status and complaint.status.code == 'new':
            # Auto-transition to assigned if in new status
            assigned_status = Status.query.filter_by(code='assigned', is_active=True).first()
            if assigned_status:
                cls.change_status(complaint, assigned_status.id, current_user, reason='Auto-assigned')
        
        # Create history record
        history = ComplaintHistory(
            complaint_id=complaint.id,
            user_id=current_user.id,
            action='assigned' if not previous_assignee_id else 'reassigned',
            old_value=str(previous_assignee_id) if previous_assignee_id else None,
            new_value=str(new_assignee_id),
            description=f'Complaint {"assigned" if not previous_assignee_id else "reassigned"} to user {new_assignee_id}',
            created_at=datetime.utcnow(),
        )
        db.session.add(history)
        
        # Send notifications
        NotificationService.notify_assignment(complaint, current_user, previous_assignee_id)
        
        # Log audit
        AuditService.log_action(
            user_id=current_user.id,
            action='assign_complaint' if not previous_assignee_id else 'reassign_complaint',
            entity_type='complaint',
            entity_id=complaint.id,
            entity_repr=complaint.complaint_number,
            old_values={'assigned_to': previous_assignee_id},
            new_values={'assigned_to': new_assignee_id},
            category='data',
        )
        
        db.session.commit()
        return True, 'Complaint assigned successfully.'
    
    @classmethod
    def change_status(cls, complaint, new_status_id, current_user, reason=None, resolution_summary=None):
        """Change complaint status with validation."""
        from app.permissions.policy import PermissionPolicy
        
        new_status = Status.query.get(new_status_id)
        if not new_status:
            return False, 'Invalid status.'
        
        old_status = complaint.status
        
        # Validate transition
        if old_status and not old_status.can_transition_to(new_status_id):
            return False, f'Transition from "{old_status.name}" to "{new_status.name}" is not allowed.'
        
        # Check permission
        if not PermissionPolicy.can_change_status(current_user, complaint, new_status):
            return False, 'You do not have permission to change to this status.'
        
        # Check required fields
        if new_status.requires_reason and not reason:
            return False, f'Reason is required for status "{new_status.name}".'
        
        if new_status.requires_resolution and new_status.code in ('resolved', 'closed'):
            if not resolution_summary and not complaint.resolution_summary:
                return False, 'Resolution summary is required for this status.'
            if resolution_summary:
                complaint.resolution_summary = resolution_summary
        
        # Create status history
        status_history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            from_status_id=old_status.id if old_status else None,
            to_status_id=new_status.id,
            changed_by_user_id=current_user.id,
            reason=reason,
            changed_at=datetime.utcnow(),
        )
        db.session.add(status_history)
        
        # Update complaint
        complaint.status_id = new_status.id
        complaint.updated_by_user_id = current_user.id
        
        # Handle special status timestamps
        now = datetime.utcnow()
        if new_status.code == 'resolved' and not complaint.resolved_at:
            complaint.resolved_at = now
            complaint.resolved_by_user_id = current_user.id
        elif new_status.code == 'closed' and not complaint.closed_at:
            complaint.closed_at = now
        elif new_status.code == 'reopened':
            complaint.resolved_at = None
            complaint.resolved_by_user_id = None
            complaint.closed_at = None
        
        # Create complaint history
        history = ComplaintHistory(
            complaint_id=complaint.id,
            user_id=current_user.id,
            action='status_change',
            field_name='status',
            old_value=old_status.name if old_status else None,
            new_value=new_status.name,
            description=f'Status changed from {old_status.name if old_status else "None"} to {new_status.name}',
            created_at=now,
        )
        db.session.add(history)
        
        # Recalculate SLA
        SLAService.recalculate_sla_on_status_change(complaint, new_status, current_user.id)
        
        # Send notifications
        NotificationService.notify_status_change(complaint, current_user, old_status, new_status)
        
        # Send resolution/closure/reopen notifications
        if new_status.code == 'resolved':
            NotificationService.notify_resolution(complaint, current_user)
        elif new_status.code == 'closed':
            NotificationService.notify_closure(complaint, current_user)
        elif new_status.code == 'reopened':
            NotificationService.notify_reopen(complaint, current_user)
        
        # Log audit
        AuditService.log_action(
            user_id=current_user.id,
            action='change_complaint_status',
            entity_type='complaint',
            entity_id=complaint.id,
            entity_repr=complaint.complaint_number,
            old_values={'status': old_status.name if old_status else None},
            new_values={'status': new_status.name},
            changed_fields=['status'],
            category='data',
        )
        
        db.session.commit()
        return True, f'Status changed to {new_status.name}.'
    
    @classmethod
    def add_comment(cls, complaint, content, current_user, visibility='internal'):
        """Add a comment to a complaint."""
        from app.permissions.policy import PermissionPolicy
        
        # Check permission for visibility
        if visibility == 'reporter_visible' and not PermissionPolicy.can_add_reporter_visible_comment(current_user, complaint):
            return False, 'You do not have permission to add reporter-visible comments.'
        elif visibility == 'internal' and not PermissionPolicy.can_add_internal_comment(current_user, complaint):
            return False, 'You do not have permission to add internal comments.'
        
        comment = Comment(
            complaint_id=complaint.id,
            user_id=current_user.id,
            content=content.strip(),
            visibility=visibility,
            is_system=False,
        )
        db.session.add(comment)
        
        # Create history
        history = ComplaintHistory(
            complaint_id=complaint.id,
            user_id=current_user.id,
            action='commented',
            description=f'Added {visibility} comment',
            created_at=datetime.utcnow(),
        )
        db.session.add(history)
        
        # Send notification
        NotificationService.notify_comment(complaint, comment, current_user)
        
        # Log audit
        AuditService.log_action(
            user_id=current_user.id,
            action='add_comment',
            entity_type='comment',
            entity_id=comment.id,
            entity_repr=f'Comment on {complaint.complaint_number}',
            new_values={'visibility': visibility, 'content_preview': content[:100]},
            category='data',
        )
        
        db.session.commit()
        return True, 'Comment added successfully.'
    
    @classmethod
    def add_attachment(cls, complaint, file_info, current_user, description=None, is_confidential=False):
        """Add an attachment to a complaint."""
        from app.permissions.policy import PermissionPolicy
        
        if not PermissionPolicy.can_upload_attachment(current_user, complaint):
            return False, 'You do not have permission to upload attachments.'
        
        attachment = Attachment(
            complaint_id=complaint.id,
            user_id=current_user.id,
            original_filename=file_info['original_filename'],
            stored_filename=file_info['stored_filename'],
            storage_path=file_info['storage_path'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            file_extension=file_info['extension'],
            description=description,
            is_confidential=is_confidential,
        )
        db.session.add(attachment)
        
        # Create history
        history = ComplaintHistory(
            complaint_id=complaint.id,
            user_id=current_user.id,
            action='attached',
            description=f'Attached file: {file_info["original_filename"]}',
            created_at=datetime.utcnow(),
        )
        db.session.add(history)
        
        # Log audit
        AuditService.log_action(
            user_id=current_user.id,
            action='upload_attachment',
            entity_type='attachment',
            entity_id=attachment.id,
            entity_repr=f'{file_info["original_filename"]} on {complaint.complaint_number}',
            new_values={
                'filename': file_info['original_filename'],
                'size': file_info['file_size'],
                'mime_type': file_info['mime_type'],
            },
            category='data',
        )
        
        db.session.commit()
        return True, 'Attachment uploaded successfully.'
    
    @classmethod
    def delete_attachment(cls, attachment, current_user):
        """Delete an attachment."""
        from app.permissions.policy import PermissionPolicy
        
        if not PermissionPolicy.can_delete_attachment(current_user, attachment):
            return False, 'You do not have permission to delete this attachment.'
        
        complaint = attachment.complaint
        
        # Delete file from storage
        import os
        if os.path.exists(attachment.storage_path):
            os.remove(attachment.storage_path)
        
        # Create history
        history = ComplaintHistory(
            complaint_id=complaint.id,
            user_id=current_user.id,
            action='detached',
            description=f'Removed attachment: {attachment.original_filename}',
            created_at=datetime.utcnow(),
        )
        db.session.add(history)
        
        # Log audit
        AuditService.log_action(
            user_id=current_user.id,
            action='delete_attachment',
            entity_type='attachment',
            entity_id=attachment.id,
            entity_repr=f'{attachment.original_filename} on {complaint.complaint_number}',
            old_values={
                'filename': attachment.original_filename,
                'size': attachment.file_size,
            },
            category='data',
        )
        
        db.session.delete(attachment)
        db.session.commit()
        return True, 'Attachment deleted successfully.'
    
    @classmethod
    def get_complaint_timeline(cls, complaint):
        """Get combined timeline of complaint activity."""
        timeline = []
        
        # Status history
        for sh in complaint.status_history:
            timeline.append({
                'type': 'status_change',
                'timestamp': sh.changed_at,
                'user': sh.changed_by,
                'from_status': sh.from_status.name if sh.from_status else None,
                'to_status': sh.to_status.name,
                'reason': sh.reason,
                'notes': sh.notes,
            })
        
        # Assignments
        for a in complaint.assignments:
            timeline.append({
                'type': 'assignment',
                'timestamp': a.assigned_at,
                'user': a.assigned_by,
                'previous_assignee': a.previous_assignee,
                'new_assignee': a.new_assignee,
                'reason': a.assignment_reason,
                'notes': a.notes,
            })
        
        # Comments
        for c in complaint.comments:
            timeline.append({
                'type': 'comment',
                'timestamp': c.created_at,
                'user': c.user,
                'content': c.content,
                'visibility': c.visibility,
            })
        
        # Attachments
        for a in complaint.attachments:
            timeline.append({
                'type': 'attachment',
                'timestamp': a.created_at,
                'user': a.user,
                'filename': a.original_filename,
                'size': a.file_size,
            })
        
        # General history
        for h in complaint.history:
            if h.action not in ['created', 'status_change', 'assigned', 'reassigned', 'commented', 'attached', 'detached']:
                timeline.append({
                    'type': 'history',
                    'timestamp': h.created_at,
                    'user': h.user,
                    'action': h.action,
                    'field': h.field_name,
                    'old_value': h.old_value,
                    'new_value': h.new_value,
                    'description': h.description,
                })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        return timeline
    
    @classmethod
    def search_complaints(cls, query_params, user, page=1, per_page=20):
        """Search complaints with filters."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        # Apply filters
        if query_params.get('search'):
            search = f"%{query_params['search']}%"
            query = query.filter(
                db.or_(
                    Complaint.complaint_number.ilike(search),
                    Complaint.title.ilike(search),
                    Complaint.description.ilike(search),
                )
            )
        
        if query_params.get('status_id'):
            query = query.filter(Complaint.status_id == query_params['status_id'])
        
        if query_params.get('priority_id'):
            query = query.filter(Complaint.priority_id == query_params['priority_id'])
        
        if query_params.get('category_id'):
            query = query.filter(Complaint.category_id == query_params['category_id'])
        
        if query_params.get('department_id'):
            query = query.filter(Complaint.department_id == query_params['department_id'])
        
        if query_params.get('software_id'):
            query = query.filter(Complaint.software_id == query_params['software_id'])
        
        if query_params.get('assigned_to_user_id'):
            query = query.filter(Complaint.assigned_to_user_id == query_params['assigned_to_user_id'])
        
        if query_params.get('reported_by_user_id'):
            query = query.filter(Complaint.reported_by_user_id == query_params['reported_by_user_id'])
        
        if query_params.get('severity'):
            query = query.filter(Complaint.severity == query_params['severity'])
        
        if query_params.get('date_from'):
            query = query.filter(Complaint.created_at >= query_params['date_from'])
        
        if query_params.get('date_to'):
            query = query.filter(Complaint.created_at <= query_params['date_to'])
        
        if query_params.get('sla_status'):
            if query_params['sla_status'] == 'overdue_response':
                query = query.filter(
                    Complaint.sla_response_deadline != None,
                    Complaint.sla_response_deadline < datetime.utcnow(),
                    Complaint.first_response_at == None,
                )
            elif query_params['sla_status'] == 'overdue_resolution':
                query = query.filter(
                    Complaint.sla_resolution_deadline != None,
                    Complaint.sla_resolution_deadline < datetime.utcnow(),
                    Complaint.resolved_at == None,
                )
        
        # Order by creation date descending
        query = query.order_by(Complaint.created_at.desc())
        
        # Paginate
        return query.paginate(page=page, per_page=per_page, error_out=False)