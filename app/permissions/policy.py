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

        if user.has_permission('complaints.view_all'):
            return True

        if user.has_permission('complaints.view_my') and complaint.assigned_to_user_id == user.id:
            return True

        return False

    @staticmethod
    def can_edit_complaint(user, complaint=None):
        """Check if user can edit a complaint."""
        if not user or not user.is_active:
            return False
        return user.has_permission('complaints.edit')

    @staticmethod
    def can_assign_complaint(user, complaint=None):
        """Check if user can assign complaints."""
        if not user or not user.is_active:
            return False
        return user.has_permission('complaints.assign')

    @staticmethod
    def can_transfer_complaint(user, complaint):
        """Check if user can transfer an assigned complaint."""
        if not user or not user.is_active:
            return False
        if user.has_permission('complaints.transfer'):
            return True
        if complaint.assigned_to_user_id == user.id:
            return True
        return False

    # Restricted statuses that require status_unlock permission
    _RESTRICTED_STATUS_CODES = frozenset(['new', 'closed', 'reopened'])

    @staticmethod
    def can_change_status(user, complaint, new_status):
        """Check if user can change complaint status, enforcing status restrictions."""
        if not user or not user.is_active:
            return False

        if new_status.code in PermissionPolicy._RESTRICTED_STATUS_CODES:
            if not user.has_permission('complaints.status_unlock'):
                return False

        if user.has_permission('complaints.change_status_all'):
            return True

        if (user.has_permission('complaints.change_status_own')
                and complaint.assigned_to_user_id == user.id):
            return True

        return False

    @staticmethod
    def can_reopen_complaint(user, complaint):
        """Reopen is handled through the unified change_status path with status_unlock.

        This method is kept for backwards compatibility but redirects to the new
        permission model.
        """
        if not user or not user.is_active:
            return False
        return (user.has_permission('complaints.status_unlock')
                and user.has_permission('complaints.change_status_all'))
    
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

        if user.has_permission('complaints.view_my'):
            return Complaint.query.filter(Complaint.assigned_to_user_id == user.id)

        return Complaint.query.filter(False)
    
    @staticmethod
    def get_assignable_users(complaint, user):
        """Get list of users that can be assigned to a complaint."""
        from app.models import User, Role
        
        # Users who can be assigned (agents/engineers/admin)
        assignable_roles = ['admin', 'helpdesk_agent', 'support_agent']
        return User.query.join(User.roles).filter(
            Role.name.in_(assignable_roles),
            User.is_active == True,
            User.id != complaint.assigned_to_user_id  # Exclude current assignee
        ).distinct().all()