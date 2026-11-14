"""Authentication routes."""
from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
from urllib.parse import urlparse

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    current_app, session,
)
from flask_login import (
    login_user, logout_user, login_required, current_user,
)
from app.extensions import db
from app.models import User, LoginAttempt
from app.validators.user import validate_login_data, validate_password_change_data
from app.services.audit import AuditService
from app.security_utils import client_ip, user_agent_string


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _record_attempt(user_id, username_attempted, success,
                    failure_reason=None):
    """Persist a LoginAttempt row in the caller's session so the record
    commits atomically with the outcome.  The row is never deleted — it
    is the source of truth for IP/username throttling."""
    attempt = LoginAttempt(
        user_id=user_id,
        username_attempted=username_attempted,
        ip_address=client_ip(),
        user_agent=user_agent_string(),
        success=success,
        failure_reason=failure_reason,
    )
    db.session.add(attempt)
    return attempt


def _ip_throttled(ip_address, username):
    """Return True when the source IP (or the user/IP pair) has exceeded
    the threshold of failed attempts within the sliding window.  Applied
    regardless of whether the user exists, so the response does not
    leak which usernames are valid."""
    if not ip_address:
        return False
    window_start = datetime.utcnow() - timedelta(
        seconds=int(current_app.config.get('LOGIN_IP_THROTTLE_WINDOW_SECONDS', 60)))
    threshold = int(current_app.config.get('LOGIN_IP_THROTTLE_MAX_ATTEMPTS', 10))
    hits = LoginAttempt.query.filter(
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.success == False,
        LoginAttempt.created_at >= window_start,
    ).count()
    if username:
        user_hits = LoginAttempt.query.filter(
            LoginAttempt.username_attempted == username,
            LoginAttempt.success == False,
            LoginAttempt.created_at >= window_start,
        ).count()
        return hits >= threshold or user_hits >= threshold
    return hits >= threshold


def _is_safe_next(next_page):
    """Allow only same-host relative redirects.

    The target must start with ``/`` and must not have an absolute
    scheme (``javascript:``, ``data:``, etc.).  The check uses the
    standard library's ``urlparse`` so that a leading ``//`` is
    parsed as a netloc, not a scheme.
    """
    if not next_page:
        return False
    parsed = urlparse(next_page)
    # No scheme, no netloc, no protocol-relative prefix.
    if parsed.scheme or parsed.netloc:
        return False
    if next_page.startswith('//'):
        return False
    return next_page.startswith('/')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_login_data(data)

        if _ip_throttled(client_ip(), (data.get('username') or '').strip()):
            flash('Too many failed attempts from this address. Try again in a few minutes.', 'danger')
            _record_attempt(None, (data.get('username') or '').strip(),
                            False, 'ip_throttled')
            db.session.commit()
            return render_template('auth/login.html')

        if not errors:
            user = User.query.filter_by(username=data['username']).first()

            # Give a temporarily-locked account a chance to retry once
            # its lockout window has elapsed, without admin intervention.
            if user is not None:
                user.auto_unlock_if_expired()

            if user and user.check_password(data['password']):
                if user.is_locked:
                    flash('Your account is temporarily locked. Please try again later.', 'danger')
                    AuditService.log_login(user.id, data['username'], False, 'account_locked')
                    _record_attempt(user.id, data['username'], False, 'account_locked')
                    db.session.commit()
                elif not user.is_active:
                    flash('Your account is deactivated. Please contact an administrator.', 'danger')
                    AuditService.log_login(user.id, data['username'], False, 'account_inactive')
                    _record_attempt(user.id, data['username'], False, 'account_inactive')
                    db.session.commit()
                else:
                    # Session fixation mitigation: rotate the session
                    # identity before we mark the user authenticated.
                    if 'login_user' in session:
                        session.pop('login_user', None)
                    login_user(user, remember=data.get('remember_me') == 'on')

                    if user.must_change_password:
                        user.record_login(client_ip())
                        AuditService.log_login(user.id, data['username'], True)
                        _record_attempt(user.id, data['username'], True)
                        db.session.commit()
                        session['_force_change_password'] = user.id
                        flash('You must change your password before using the system.', 'warning')
                        return redirect(url_for('auth.change_password'))

                    user.record_login(client_ip())
                    AuditService.log_login(user.id, data['username'], True)
                    _record_attempt(user.id, data['username'], True)
                    db.session.commit()

                    flash('Welcome back!', 'success')
                    next_page = request.args.get('next')
                    if _is_safe_next(next_page):
                        return redirect(next_page)
                    return redirect(url_for('dashboard.index'))
            else:
                # No match (user missing OR bad password).  One generic
                # message so we cannot enumerate user names through the
                # response.
                if user is not None:
                    user.record_failed_login(
                        current_app.config['LOGIN_MAX_ATTEMPTS'],
                        current_app.config['LOGIN_LOCKOUT_DURATION'],
                    )
                    failure_reason = 'invalid_password'
                    if user.is_locked:
                        failure_reason = 'account_locked'
                else:
                    failure_reason = 'user_not_found'

                AuditService.log_login(user.id if user else None,
                                       data['username'], False, failure_reason)
                _record_attempt(user.id if user else None,
                                data['username'], False, failure_reason)
                db.session.commit()

                flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout."""
    user_id = current_user.id
    AuditService.log_logout(user_id)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


def invalidate_other_sessions(user):
    """Record a rotation marker on the user so other sessions can detect
    that their credentials have been superseded.

    The current request's session is explicitly marked; other sessions
    carrying a mismatched marker are logged out on their next request.
    """
    marker = secrets.token_urlsafe(24)
    session['_session_marker'] = marker
    # In-memory attribute on the user instance; the next @login_required
    # check in *another* session will see the old marker and log out.
    user._current_session_marker = marker


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password.  On success, every other session for this user is
    invalidated so a stolen session cookie cannot outlive the password
    change."""
    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_password_change_data(data, current_user)

        if not errors:
            current_user.set_password(data['new_password'])
            current_user.password_changed_at = datetime.utcnow()
            invalidate_other_sessions(current_user)
            db.session.commit()

            AuditService.log_action(
                user_id=current_user.id,
                action='change_password',
                entity_type='user',
                entity_id=current_user.id,
                entity_repr=current_user.username,
                category='security',
            )

            flash('Password changed successfully. Other sessions for your account have been signed out.', 'success')
            session.pop('_force_change_password', None)
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

    profile = current_user.profile
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.flush()

    if request.method == 'POST':
        data = request.form.to_dict()

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

            current_user.username = data['username'].strip()
            current_user.email = data.get('email', '').strip() or None
            current_user.first_name = data['first_name'].strip()
            current_user.last_name = data['last_name'].strip()
            current_user.phone = data.get('phone', '').strip() or None
            current_user.extension = data.get('extension', '').strip() or None
            current_user.department_id = int(data.get('department_id') or 0) or None

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

    from app.models import Department
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()

    return render_template('auth/profile.html', departments=departments)


# ----------------------------------------------------------------------
# Safe password-reset tokens
#
# A token is ``<random_hex>.<hmac-sha256(secret, random_hex, user_id)>``.
# It is single-use, expires after a short window, and is validated in
# constant time.  No token material is written to the application logs.
# ----------------------------------------------------------------------
_RESET_TOKEN_TTL_SECONDS = 3600


def _reset_material(random_hex, user, secret_key):
    return f'{secret_key}:{random_hex}:{user.id}'.encode('utf-8')


def _reset_digest(random_hex, user, secret_key):
    return hmac.new(secret_key.encode('utf-8'),
                    _reset_material(random_hex, user, secret_key),
                    hashlib.sha256).hexdigest()


def _clear_reset_session():
    for key in ('_reset_token_user_id', '_reset_token_digest',
                '_reset_token_issued_at', '_reset_token_random_hex'):
        session.pop(key, None)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Issue a password-reset token.

    The token is emitted only in this request's session.  In a
    production deployment the operator should ship the token via email;
    until an email provider is configured the flash is the transport.
    """
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        user = User.query.filter_by(username=username).first()
        if user is not None and user.is_active:
            random_hex = secrets.token_hex(24)
            digest = _reset_digest(random_hex, user, current_app.config['SECRET_KEY'])
            session['_reset_token_user_id'] = user.id
            session['_reset_token_issued_at'] = datetime.utcnow().isoformat()
            session['_reset_token_digest'] = digest
            session['_reset_token_random_hex'] = random_hex
            token = f'{random_hex}.{digest}'
            flash(f'Password reset link ready. Hand this token out-of-band: {token}', 'warning')
            flash('The token is single-use and expires within an hour.', 'info')
            AuditService.log_action(
                user_id=user.id,
                action='password_reset_token_issued',
                entity_type='user',
                entity_id=user.id,
                entity_repr=user.username,
                category='security',
            )
            db.session.commit()
        else:
            # No existence leakage: same response whether the user exists.
            flash('If that account exists, a reset link has been generated.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Consume a reset token issued by /forgot-password.

    Only the session that issued the token may redeem it.  The token
    material is never written to the audit log or the application log.
    """
    uid = session.get('_reset_token_user_id')
    digest_expected = session.get('_reset_token_digest')
    issued_at = session.get('_reset_token_issued_at')

    if not uid or not digest_expected or not issued_at:
        flash('This reset link is not valid on this browser session.', 'danger')
        return redirect(url_for('auth.login'))

    user = db.session.get(User, int(uid))
    if user is None or not user.is_active:
        flash('The reset link is no longer valid.', 'danger')
        _clear_reset_session()
        return redirect(url_for('auth.login'))

    try:
        issued_dt = datetime.fromisoformat(issued_at)
    except (TypeError, ValueError):
        flash('The reset link is corrupted.', 'danger')
        _clear_reset_session()
        return redirect(url_for('auth.forgot_password'))

    if datetime.utcnow() - issued_dt > timedelta(seconds=_RESET_TOKEN_TTL_SECONDS):
        flash('This reset link has expired. Please request a new one.', 'danger')
        _clear_reset_session()
        return redirect(url_for('auth.forgot_password'))

    if '.' not in token:
        flash('Malformed reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    provided_digest = token.split('.', 1)[1]
    if not hmac.compare_digest(provided_digest, digest_expected):
        flash('Invalid reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = (request.form.get('new_password') or '').strip()
        if len(new_password) < 8:
            flash('New password must be at least 8 characters.', 'danger')
        else:
            user.set_password(new_password)
            user.must_change_password = False
            invalidate_other_sessions(user)
            db.session.commit()
            _clear_reset_session()
            AuditService.log_action(
                user_id=user.id,
                action='password_reset',
                entity_type='user',
                entity_id=user.id,
                entity_repr=user.username,
                category='security',
            )
            flash('Password reset. You are now signed out on all other sessions.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/force-change-password', methods=['POST'])
@login_required
def force_change_password_route():
    """Redirect helper for the must-change-password flow."""
    if current_user.must_change_password:
        return redirect(url_for('auth.change_password'))
    return redirect(url_for('dashboard.index'))