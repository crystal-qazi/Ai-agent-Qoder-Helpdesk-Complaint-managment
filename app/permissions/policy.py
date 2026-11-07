"""Permission policy class for complex permission checks."""
from flask_login import current_user
from app.models import Complaint, User, Role, Permission


class PermissionPolicy:
    """Centralized permission policy for complex checks."""
    
    @staticmethod
    def can_view_complaint(user, complaint):
        """Check if user can view a complaint."""
        if not user or not user.is_active:
            return False
        
        # Admin can view all
        if user.has_permission('complaints.view_all'):
            return True
        
        return user.id in (complaint.reported_by_user_id,
                           complaint.created_by_user_id,
                           complaint.assigned_to_user_id)
    
    @staticmethod
    def can_edit_complaint(user, complaint):
        """Check if user can edit a complaint."""
        if not user or not user.is_active:
            return False
        
        # Admin can edit all
        if user.has_permission('complaints.edit'):
            return True
        
        # Creator can edit own
        if complaint.created_by_user_id == user.id and user.has_permission('complaints.edit_own'):
            return True
        
        # Assignee can edit assigned
        if complaint.assigned_to_user_id == user.id and user.has_permission('complaints.edit_assigned'):
            return True
        
        return False
    
    @staticmethod
    def can_assign_complaint(user, complaint=None):
        """Check if user can assign complaints."""
        if not user or not user.is_active:
            return False
        return user.has_permission('complaints.assign')
    
    @staticmethod
    def can_reassign_complaint(user, complaint):
        """Check if user can reassign a complaint."""
        if not user or not user.is_active:
            return False
        
        # Admin can reassign all
        if user.has_permission('complaints.reassign'):
            return True
        
        # Current assignee can reassign with permission
        if complaint.assigned_to_user_id == user.id and user.has_permission('complaints.reassign_own'):
            return True
        
        return False
    
    @staticmethod
    def can_change_status(user, complaint, new_status):
        """Check if user can change complaint status."""
        if not user or not user.is_active:
            return False
        
        # Terminal-type statuses need their own right, so e.g. call intake users cannot resolve/close
        if new_status.code == 'rejected':
            return PermissionPolicy.can_reject_complaint(user, complaint)
        if new_status.category == 'resolved':
            return PermissionPolicy.can_resolve_complaint(user, complaint)
        if new_status.category == 'closed':
            return PermissionPolicy.can_close_complaint(user, complaint)
        if new_status.code == 'reopened':
            return PermissionPolicy.can_reopen_complaint(user, complaint)
        
        if user.has_permission('complaints.change_status'):
            return True
        return (complaint.assigned_to_user_id == user.id
                and user.has_permission('complaints.change_status_assigned'))
    
    @staticmethod
    def can_resolve_complaint(user, complaint):
        """Check if user can resolve a complaint."""
        if not user or not user.is_active:
            return False
        
        # Admin can resolve all
        if user.has_permission('complaints.resolve'):
            return True
        
        # Assignee can resolve
        if complaint.assigned_to_user_id == user.id and user.has_permission('complaints.resolve_assigned'):
            return True
        
        # Engineer can resolve
        if user.has_role('engineer') and user.has_permission('complaints.resolve'):
            return True
        
        return False
    
    @staticmethod
    def can_close_complaint(user, complaint):
        """Check if user can close a complaint."""
        if not user or not user.is_active:
            return False
        
        # Admin can close all
        if user.has_permission('complaints.close'):
            return True
        
        # Assignee with permission can close
        if complaint.assigned_to_user_id == user.id and user.has_permission('complaints.close_assigned'):
            return True
        
        # Agent with permission can close
        if user.has_permission('complaints.close'):
            return True
        
        return False
    
    @staticmethod
    def can_reopen_complaint(user, complaint):
        """Check if user can reopen a complaint."""
        if not user or not user.is_active:
            return False
        
        # Admin can reopen
        if user.has_permission('complaints.reopen'):
            return True
        
        # Original reporter can reopen with permission
        if complaint.reported_by_user_id == user.id and user.has_permission('complaints.reopen_own'):
            return True
        
        # Assignee can reopen with permission
        if complaint.assigned_to_user_id == user.id and user.has_permission('complaints.reopen_assigned'):
            return True
        
        return False
    
    @staticmethod
    def can_reject_complaint(user, complaint):
        """Check if user can reject a complaint."""
        if not user or not user.is_active:
            return False
        return user.has_permission('complaints.reject')
    
    @staticmethod
    def can_add_internal_comment(user, complaint):
        """Check if user can add internal comment."""
        if not user or not user.is_active:
            return False
        
        # Support staff can add internal comments
        if user.has_permission('comments.add_internal'):
            return True
        
        # Assignee can add internal comments
        if complaint.assigned_to_user_id == user.id:
            return True
        
        return False
    
    @staticmethod
    def can_add_reporter_visible_comment(user, complaint):
        """Check if user can add reporter-visible comment."""
        if not user or not user.is_active:
            return False
        
        # Support staff can add reporter-visible comments
        if user.has_permission('comments.add_reporter_visible'):
            return True
        
        # Reporter can add comments to their own complaint
        if complaint.reported_by_user_id == user.id:
            return True
        
        return False
    
    @staticmethod
    def can_view_internal_comments(user, complaint):
        """Check if user can view internal comments."""
        if not user or not user.is_active:
            return False
        
        # Support staff can view internal comments
        if user.has_permission('comments.view_internal'):
            return True
        
        # Assignee can view internal comments
        if complaint.assigned_to_user_id == user.id:
            return True
        
        return False
    
    @staticmethod
    def can_upload_attachment(user, complaint):
        """Check if user can upload attachment."""
        if not user or not user.is_active:
            return False
        
        # Support staff can upload
        if user.has_permission('attachments.upload'):
            return True
        
        # Reporter can upload
        if complaint.reported_by_user_id == user.id:
            return True
        
        # Assignee can upload
        if complaint.assigned_to_user_id == user.id:
            return True
        
        return False
    
    @staticmethod
    def can_download_attachment(user, attachment):
        """Check if user can download attachment."""
        if not user or not user.is_active:
            return False
        
        # Admin can download all
        if user.has_permission('attachments.download_all'):
            return True
        
        # Uploader can download
        if attachment.user_id == user.id:
            return True
        
        # Complaint participants can download
        complaint = attachment.complaint
        if complaint.reported_by_user_id == user.id:
            return True
        if complaint.assigned_to_user_id == user.id:
            return True
        if user.has_permission('comments.view_internal'):
            return True
        
        return False
    
    @staticmethod
    def can_delete_attachment(user, attachment):
        """Check if user can delete attachment."""
        if not user or not user.is_active:
            return False
        
        # Admin can delete all
        if user.has_permission('attachments.delete'):
            return True
        
        # Uploader can delete own
        if attachment.user_id == user.id and user.has_permission('attachments.delete_own'):
            return True
        
        return False
    
    @staticmethod
    def can_view_user(user, target_user):
        """Check if user can view another user."""
        if not user or not user.is_active:
            return False
        
        # Users can view themselves
        if user.id == target_user.id:
            return True
        
        # Admin can view all
        if user.has_permission('users.view'):
            return True
        
        # Managers can view their team
        if target_user.profile and target_user.profile.manager_id == user.id:
            return True
        
        return False
    
    @staticmethod
    def can_edit_user(user, target_user):
        """Check if user can edit another user."""
        if not user or not user.is_active:
            return False
        
        # Users can edit themselves (limited fields)
        if user.id == target_user.id:
            return True
        
        # Admin can edit all
        if user.has_permission('users.edit'):
            return True
        
        return False
    
    @staticmethod
    def can_manage_roles(user):
        """Check if user can manage roles."""
        if not user or not user.is_active:
            return False
        return user.has_permission('roles.manage')
    
    @staticmethod
    def can_manage_permissions(user):
        """Check if user can manage permissions."""
        if not user or not user.is_active:
            return False
        return user.has_permission('permissions.manage')
    
    @staticmethod
    def can_manage_departments(user):
        """Check if user can manage departments."""
        if not user or not user.is_active:
            return False
        return user.has_permission('departments.manage')
    
    @staticmethod
    def can_manage_software(user):
        """Check if user can manage software catalog."""
        if not user or not user.is_active:
            return False
        return user.has_permission('software.manage')
    
    @staticmethod
    def can_manage_categories(user):
        """Check if user can manage categories."""
        if not user or not user.is_active:
            return False
        return user.has_permission('categories.manage')
    
    @staticmethod
    def can_manage_priorities(user):
        """Check if user can manage priorities."""
        if not user or not user.is_active:
            return False
        return user.has_permission('priorities.manage')
    
    @staticmethod
    def can_manage_statuses(user):
        """Check if user can manage statuses."""
        if not user or not user.is_active:
            return False
        return user.has_permission('statuses.manage')
    
    @staticmethod
    def can_manage_sla_policies(user):
        """Check if user can manage SLA policies."""
        if not user or not user.is_active:
            return False
        return user.has_permission('sla.manage')
    
    @staticmethod
    def can_view_reports(user):
        """Check if user can view reports."""
        if not user or not user.is_active:
            return False
        return user.has_permission('reports.view')
    
    @staticmethod
    def can_export_reports(user):
        """Check if user can export reports."""
        if not user or not user.is_active:
            return False
        return user.has_permission('reports.export')
    
    @staticmethod
    def can_view_audit_logs(user):
        """Check if user can view audit logs."""
        if not user or not user.is_active:
            return False
        return user.has_permission('audit.view')
    
    @staticmethod
    def can_manage_system_settings(user):
        """Check if user can manage system settings."""
        if not user or not user.is_active:
            return False
        return user.has_permission('settings.manage')
    
    @staticmethod
    def get_accessible_complaints_query(user):
        """Get base query for complaints accessible to user."""
        from app.extensions import db
        from app.models import Complaint
        
        if user.has_permission('complaints.view_all'):
            return Complaint.query
        
        return Complaint.query.filter(
            db.or_(
                Complaint.reported_by_user_id == user.id,
                Complaint.created_by_user_id == user.id,
                Complaint.assigned_to_user_id == user.id,
            )
        )
    
    @staticmethod
    def get_assignable_users(complaint, user):
        """Get list of users that can be assigned to a complaint."""
        from app.models import User, Role
        
        # Users with engineer or agent role who are active
        assignable_roles = ['engineer', 'agent', 'admin']
        return User.query.join(User.roles).filter(
            Role.name.in_(assignable_roles),
            User.is_active == True,
            User.id != complaint.assigned_to_user_id  # Exclude current assignee
        ).distinct().all()