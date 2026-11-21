"""Notifications routes."""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Notification
from app.services.audit import AuditService

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


def _safe_internal_redirect_target(action_url, host):
    """Return a validated same-origin path/URL, or None."""
    from urllib.parse import unquote, urlsplit

    if not isinstance(action_url, str) or not action_url or action_url != action_url.strip():
        return None
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in action_url) or "\\" in action_url:
        return None

    try:
        parsed = urlsplit(action_url)
    except ValueError:
        return None

    decoded_path = unquote(parsed.path or "")
    if "\\" in decoded_path or any(ord(ch) < 32 or ord(ch) == 127 for ch in decoded_path):
        return None

    if not parsed.scheme and not parsed.netloc:
        if not parsed.path.startswith("/") or parsed.path.startswith("//"):
            return None
        return action_url

    if parsed.scheme.lower() not in ("http", "https"):
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if not parsed.netloc or parsed.netloc.casefold() != str(host).casefold():
        return None
    if not parsed.path.startswith("/") or parsed.path.startswith("//"):
        return None
    return action_url


@notifications_bp.route('/')
@login_required
def list_notifications():
    """List user notifications with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filter_type = request.args.get('filter', 'all')  # all, unread, read
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if filter_type == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_type == 'read':
        query = query.filter_by(is_read=True)
    
    query = query.order_by(Notification.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    return render_template('notifications/list.html',
                           pagination=pagination,
                           filter_type=filter_type,
                           unread_count=unread_count)


@notifications_bp.route('/<int:notification_id>')
@login_required
def view_notification(notification_id):
    """View a single notification and mark as read."""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    
    if not notification.is_read:
        notification.mark_as_read()
        db.session.commit()
    
    # Redirect to action URL if present, otherwise show notification detail.
    # Only allow internal (same-origin) URLs to prevent open-redirect.
    if notification.action_url:
        safe_target = _safe_internal_redirect_target(
            notification.action_url, request.host,
        )
        if safe_target:
            return redirect(safe_target)
    
    return render_template('notifications/detail.html', notification=notification)


@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark a notification as read."""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    
    if not notification.is_read:
        notification.mark_as_read()
        db.session.commit()
    
    return jsonify({'success': True, 'read': True})


@notifications_bp.route('/<int:notification_id>/unread', methods=['POST'])
@login_required
def mark_as_unread(notification_id):
    """Mark a notification as unread."""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    
    if notification.is_read:
        notification.mark_as_unread()
        db.session.commit()
    
    return jsonify({'success': True, 'read': False})


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'All notifications marked as read'})


@notifications_bp.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a notification."""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Notification deleted'})


@notifications_bp.route('/unread-count')
@login_required
def unread_count():
    """Get unread notification count for badge."""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@notifications_bp.route('/recent')
@login_required
def recent_notifications():
    """Get recent notifications for dropdown."""
    limit = request.args.get('limit', 10, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).limit(limit).all()
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count
    })


# API endpoints for real-time notification center
@notifications_bp.route('/api/list')
@login_required
def api_list_notifications():
    """API endpoint for notification list with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filter_type = request.args.get('filter', 'all')
    notification_type = request.args.get('type')
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if filter_type == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_type == 'read':
        query = query.filter_by(is_read=True)
    
    if notification_type:
        query = query.filter_by(notification_type=notification_type)
    
    query = query.order_by(Notification.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        },
        'unread_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    })


@notifications_bp.route('/api/stats')
@login_required
def api_notification_stats():
    """Get notification statistics."""
    total = Notification.query.filter_by(user_id=current_user.id).count()
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    by_type = db.session.query(
        Notification.notification_type,
        db.func.count(Notification.id)
    ).filter_by(user_id=current_user.id).group_by(Notification.notification_type).all()
    
    return jsonify({
        'total': total,
        'unread': unread,
        'read': total - unread,
        'by_type': dict(by_type)
    })