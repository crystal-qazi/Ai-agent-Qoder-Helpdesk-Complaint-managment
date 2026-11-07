"""Notification service."""
from datetime import datetime
from app.extensions import db
from app.models import Notification, User, Complaint
from app.permissions.policy import PermissionPolicy


class NotificationService:
    """Service for managing notifications."""
    
    @staticmethod
    def notify_assignment(complaint, assigned_by_user, previous_assignee=None):
        """Send notification for complaint assignment."""
        # Notify new assignee
        if complaint.assigned_to_user_id:
            Notification.create_notification(
                user_id=complaint.assigned_to_user_id,
                title='New Complaint Assigned',
                message=f'You have been assigned to complaint {complaint.complaint_number}: {complaint.title}',
                notification_type='assignment',
                complaint_id=complaint.id,
                priority='high',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
        
        # Notify previous assignee if reassigned
        if previous_assignee and previous_assignee != complaint.assigned_to_user_id:
            Notification.create_notification(
                user_id=previous_assignee,
                title='Complaint Reassigned',
                message=f'Complaint {complaint.complaint_number} has been reassigned to another engineer.',
                notification_type='reassignment',
                complaint_id=complaint.id,
                priority='normal',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
    
    @staticmethod
    def notify_status_change(complaint, changed_by_user, old_status, new_status):
        """Send notification for status change."""
        # Notify assignee
        if complaint.assigned_to_user_id and complaint.assigned_to_user_id != changed_by_user.id:
            Notification.create_notification(
                user_id=complaint.assigned_to_user_id,
                title='Complaint Status Changed',
                message=f'Complaint {complaint.complaint_number} status changed from {old_status.name} to {new_status.name}.',
                notification_type='status_change',
                complaint_id=complaint.id,
                priority='normal',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
        
        # Notify reporter (if reporter-visible)
        if complaint.reported_by_user_id and complaint.reported_by_user_id != changed_by_user.id:
            Notification.create_notification(
                user_id=complaint.reported_by_user_id,
                title='Your Complaint Status Updated',
                message=f'Your complaint {complaint.complaint_number} status is now {new_status.name}.',
                notification_type='status_change',
                complaint_id=complaint.id,
                priority='normal',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
    
    @staticmethod
    def notify_comment(complaint, comment, commented_by_user):
        """Send notification for new comment."""
        notified_users = set()
        
        # Notify assignee (if not the commenter)
        if complaint.assigned_to_user_id and complaint.assigned_to_user_id != commented_by_user.id:
            notified_users.add(complaint.assigned_to_user_id)
        
        # Notify reporter for reporter-visible comments
        if comment.visibility == 'reporter_visible' and complaint.reported_by_user_id and complaint.reported_by_user_id != commented_by_user.id:
            notified_users.add(complaint.reported_by_user_id)
        
        # Notify users mentioned in comment (optional enhancement)
        # For now, just notify participants
        
        for user_id in notified_users:
            priority = 'normal'
            if comment.visibility == 'reporter_visible':
                title = 'New Comment on Your Complaint'
                message = f'New comment on complaint {complaint.complaint_number} by {commented_by_user.full_name}.'
            else:
                title = 'New Internal Comment'
                message = f'New internal comment on complaint {complaint.complaint_number} by {commented_by_user.full_name}.'
                priority = 'low'
            
            Notification.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type='comment',
                complaint_id=complaint.id,
                priority=priority,
                action_url=f'/complaints/{complaint.id}#comments',
                action_label='View Comment',
            )
    
    @staticmethod
    def notify_resolution(complaint, resolved_by_user):
        """Send notification for complaint resolution."""
        # Notify reporter
        if complaint.reported_by_user_id and complaint.reported_by_user_id != resolved_by_user.id:
            Notification.create_notification(
                user_id=complaint.reported_by_user_id,
                title='Complaint Resolved',
                message=f'Your complaint {complaint.complaint_number} has been resolved.',
                notification_type='resolution',
                complaint_id=complaint.id,
                priority='normal',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Resolution',
            )
        
        # Notify assignee if different from resolver
        if complaint.assigned_to_user_id and complaint.assigned_to_user_id != resolved_by_user.id:
            Notification.create_notification(
                user_id=complaint.assigned_to_user_id,
                title='Complaint Resolved',
                message=f'Complaint {complaint.complaint_number} has been marked as resolved.',
                notification_type='resolution',
                complaint_id=complaint.id,
                priority='normal',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
    
    @staticmethod
    def notify_closure(complaint, closed_by_user):
        """Send notification for complaint closure."""
        # Notify reporter
        if complaint.reported_by_user_id and complaint.reported_by_user_id != closed_by_user.id:
            Notification.create_notification(
                user_id=complaint.reported_by_user_id,
                title='Complaint Closed',
                message=f'Your complaint {complaint.complaint_number} has been closed.',
                notification_type='closure',
                complaint_id=complaint.id,
                priority='normal',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
        
        # Notify assignee
        if complaint.assigned_to_user_id and complaint.assigned_to_user_id != closed_by_user.id:
            Notification.create_notification(
                user_id=complaint.assigned_to_user_id,
                title='Complaint Closed',
                message=f'Complaint {complaint.complaint_number} has been closed.',
                notification_type='closure',
                complaint_id=complaint.id,
                priority='normal',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
    
    @staticmethod
    def notify_reopen(complaint, reopened_by_user):
        """Send notification for complaint reopening."""
        # Notify assignee
        if complaint.assigned_to_user_id and complaint.assigned_to_user_id != reopened_by_user.id:
            Notification.create_notification(
                user_id=complaint.assigned_to_user_id,
                title='Complaint Reopened',
                message=f'Complaint {complaint.complaint_number} has been reopened.',
                notification_type='reopen',
                complaint_id=complaint.id,
                priority='high',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
        
        # Notify previous resolver
        if complaint.resolved_by_user_id and complaint.resolved_by_user_id != reopened_by_user.id:
            Notification.create_notification(
                user_id=complaint.resolved_by_user_id,
                title='Complaint Reopened',
                message=f'Complaint {complaint.complaint_number} you resolved has been reopened.',
                notification_type='reopen',
                complaint_id=complaint.id,
                priority='high',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
    
    @staticmethod
    def notify_sla_warning(complaint, warning_type):
        """Send SLA warning notification."""
        if not complaint.assigned_to_user_id:
            return
        
        if warning_type == 'response':
            title = 'SLA Response Deadline Approaching'
            message = f'Complaint {complaint.complaint_number} response deadline is approaching.'
        else:
            title = 'SLA Resolution Deadline Approaching'
            message = f'Complaint {complaint.complaint_number} resolution deadline is approaching.'
        
        Notification.create_notification(
            user_id=complaint.assigned_to_user_id,
            title=title,
            message=message,
            notification_type='sla_warning',
            complaint_id=complaint.id,
            priority='high',
            action_url=f'/complaints/{complaint.id}',
            action_label='View Complaint',
        )
    
    @staticmethod
    def notify_sla_breach(complaint, breach_type):
        """Send SLA breach notification."""
        if not complaint.assigned_to_user_id:
            return
        
        if breach_type == 'response':
            title = 'SLA Response Breach'
            message = f'Complaint {complaint.complaint_number} has breached its response SLA.'
            priority = 'high'
        else:
            title = 'SLA Resolution Breach'
            message = f'Complaint {complaint.complaint_number} has breached its resolution SLA.'
            priority = 'urgent'
        
        Notification.create_notification(
            user_id=complaint.assigned_to_user_id,
            title=title,
            message=message,
            notification_type='sla_breach',
            complaint_id=complaint.id,
            priority=priority,
            action_url=f'/complaints/{complaint.id}',
            action_label='View Complaint',
        )
        
        # Also notify supervisors/managers for escalation
        # This could be enhanced to notify based on escalation policies
    
    @staticmethod
    def notify_escalation(complaint, escalated_by_user, escalated_to_user):
        """Send escalation notification."""
        # Notify escalated-to user
        if escalated_to_user:
            Notification.create_notification(
                user_id=escalated_to_user.id,
                title='Complaint Escalated',
                message=f'Complaint {complaint.complaint_number} has been escalated to you by {escalated_by_user.full_name}.',
                notification_type='escalation',
                complaint_id=complaint.id,
                priority='urgent',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
        
        # Notify current assignee
        if complaint.assigned_to_user_id and complaint.assigned_to_user_id != escalated_to_user.id:
            Notification.create_notification(
                user_id=complaint.assigned_to_user_id,
                title='Complaint Escalated',
                message=f'Complaint {complaint.complaint_number} has been escalated to {escalated_to_user.full_name if escalated_to_user else "another engineer"}.',
                notification_type='escalation',
                complaint_id=complaint.id,
                priority='high',
                action_url=f'/complaints/{complaint.id}',
                action_label='View Complaint',
            )
    
    @staticmethod
    def get_user_notifications(user_id, unread_only=False, limit=50, offset=0):
        """Get notifications for a user."""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for a user."""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark a notification as read."""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.mark_as_read()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a user."""
        Notification.query.filter_by(user_id=user_id, is_read=False).update({
            'is_read': True,
            'read_at': datetime.utcnow(),
        })
        db.session.commit()
    
    @staticmethod
    def delete_notification(notification_id, user_id):
        """Delete a notification."""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        return False