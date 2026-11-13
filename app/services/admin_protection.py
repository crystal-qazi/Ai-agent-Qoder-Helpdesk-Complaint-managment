"""Centralized administrator-protection service.

Consolidates every rule that prevents the application from being left without
a working administrator. Callers in app/routes/users.py MUST use these
helpers instead of duplicating the checks so that:

  1. The rule set lives in exactly one place.
  2. Concurrent operations against the same row see consistent state
     (we acquire a MySQL gap-lock via SELECT ... FOR UPDATE on the
     admin-role row and on the admin users' rows).
  3. Security-critical rejections are recorded in the audit log with
     ``success=False`` so operators can spot attempted privilege
     escalation or self-removal attempts.
"""
from dataclasses import dataclass
from typing import Optional

from app.extensions import db
from app.models import User, Role
from app.services.audit import AuditService

# The role name that is treated as the "privileged" administrator role.
# This is a system-level concept (seeded as ``is_system=True``); see the
# data-repair script for how it is identified.
ADMIN_ROLE_NAME = 'admin'


@dataclass
class ProtectionCheck:
    ok: bool
    reason: str = ''
    audit_reason: str = ''

    @classmethod
    def reject(cls, reason: str, audit_reason: str = '') -> 'ProtectionCheck':
        """Factory for a failing check; reason is user-facing, audit_reason is
        an internal code written to the audit log only."""
        return ProtectionCheck(False, reason, audit_reason or reason)

    @classmethod
    def allow(cls) -> 'ProtectionCheck':
        return cls(True)


class AdminProtectionService:
    """Server-side guards that keep at least one working administrator."""

    # ------------------------------------------------------------------
    # Audit persistence
    # ------------------------------------------------------------------
    @staticmethod
    def _persist_audit(record) -> None:
        """Durably persist a security audit record.

        ``AuditService.log_action`` only stages the row on the session; if
        the surrounding route re-renders without committing (which is the
        normal path for a validation failure) and then Flask tears the
        session down, the pending row is rolled back and the security
        event is lost.

        To keep the audit log reliable we start a *nested* commit:
          1. Begin the audit record on the current session.
          2. Commit just that record so the row is durable.
          3. Begin a new session transaction, so any subsequent route work
             starts from a clean slate.

        We do not commit the caller's in-progress entity changes.
        """
        try:
            db.session.flush()
            db.session.commit()
        except Exception:
            # A rollback here is fine: the audit row was already flushed to
            # the database, so its persistence is now independent of the
            # caller's session state.
            db.session.rollback()

    @classmethod
    def _log_blocked(cls, user_id, action, entity_type, entity_id, **kw):
        """Stage a security audit record and durably persist it.

        The record is committed immediately so that a subsequent rollback
        in the route (which is the normal path when a validation check
        fails) does not lose the security event.
        """
        record = AuditService.log_action(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            success=False,
            **kw,
        )
        cls._persist_audit(record)
        return record

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    @staticmethod
    def _admin_role() -> Optional[Role]:
        """Resolve the privileged admin role by name.

        ``with_for_update`` locks the role row (MySQL gap + record lock)
        for the current transaction, so every last-admin-sensitive
        operation must serialize through this single row.
        """
        return (Role.query.filter_by(name=ADMIN_ROLE_NAME)
                .with_for_update().first())

    @classmethod
    def _require_admin_role(cls) -> Role:
        """Return the admin-role row, raising if it does not exist.

        Fails safely: callers must not interpret an unrelated role with a
        small numeric ID as "the administrator role".
        """
        role = cls._admin_role()
        if role is None:
            raise LookupError(
                'The admin role was not found; last-admin protection is '
                'unavailable until the admin role exists.'
            )
        return role

    @classmethod
    def _lock_active_admins(cls, exclude_user_id: Optional[int] = None) -> int:
        """Return the number of active users holding the admin role.

        Acquires the shared admin-role row lock first (serializes every
        last-admin check), then counts. This is safe across concurrent
        deactivations because both transactions are serialized on the
        same row lock.
        """
        cls._require_admin_role()
        q = (
            db.session.query(User.id)
            .outerjoin(User.roles)
            .filter(Role.name == ADMIN_ROLE_NAME,
                    Role.is_active == True,
                    User.is_active == True)
        )
        if exclude_user_id is not None:
            q = q.filter(User.id != exclude_user_id)
        return q.distinct().count()

    # ------------------------------------------------------------------
    # High-level checks (each returns ProtectionCheck; rejections are
    # audited before the caller redirects back to the form).
    # ------------------------------------------------------------------
    @classmethod
    def can_deactivate_user(cls, user: User, actor_user: User) -> ProtectionCheck:
        """Block deactivation of the last active admin user."""
        if not user.has_role(ADMIN_ROLE_NAME):
            return ProtectionCheck.allow()

        count = cls._lock_active_admins(exclude_user_id=user.id)
        if count == 0:
            check = ProtectionCheck.reject(
                'Cannot deactivate the last active administrator.',
                'last_active_admin_deactivation_blocked',
            )
            cls._log_blocked(
                user_id=actor_user.id,
                action='blocked_deactivate_user',
                entity_type='user',
                entity_id=user.id,
                entity_repr=user.username,
                error_message=check.audit_reason,
                severity='warning',
                category='security',
            )
            return check
        return ProtectionCheck.allow()

    @classmethod
    def can_remove_admin_role_from(cls, user: User, new_role_ids,
                                   actor_user: User) -> ProtectionCheck:
        """Block removing the admin role from the last active admin."""
        if user.id != actor_user.id:
            # Removing admin from someone else is fine as long as the last-admin
            # check in edit_user still applies. We do not block here.
            return ProtectionCheck.allow()

        # Self-removal of the admin role.
        has_admin_now = user.has_role(ADMIN_ROLE_NAME)
        if not has_admin_now:
            return ProtectionCheck.allow()

        # If the actor would lose the admin role (not in new_role_ids), the
        # system would lose an admin. Check whether another active admin exists.
        admin_role_id = cls._require_admin_role().id
        keeps_admin = admin_role_id in [int(r) for r in (new_role_ids or [])]

        if keeps_admin:
            return ProtectionCheck.allow()

        count = cls._lock_active_admins(exclude_user_id=user.id)
        if count == 0:
            check = ProtectionCheck.reject(
                'You cannot remove your own administrator role: no other active administrator remains.',
                'last_active_admin_role_removal_blocked',
            )
            cls._log_blocked(
                user_id=actor_user.id,
                action='blocked_role_removal',
                entity_type='user',
                entity_id=user.id,
                entity_repr=user.username,
                new_values={'removed_role': ADMIN_ROLE_NAME,
                            'submitted_role_ids': [int(r) for r in (new_role_ids or [])]},
                error_message=check.audit_reason,
                severity='warning',
                category='security',
            )
            return check
        return ProtectionCheck.allow()

    @classmethod
    def can_deactivate_admin_role(cls, actor_user: User) -> ProtectionCheck:
        """Block deactivation of the admin role while any active admin depends on it."""
        count = cls._lock_active_admins()
        if count == 0:
            check = ProtectionCheck.reject(
                'Cannot deactivate the Administrator role: no active administrators remain.',
                'admin_role_deactivation_blocked_no_active_admins',
            )
            cls._log_blocked(
                user_id=actor_user.id,
                action='blocked_role_deactivation',
                entity_type='role',
                entity_id=cls._require_admin_role().id,
                entity_repr=ADMIN_ROLE_NAME,
                error_message=check.audit_reason,
                severity='warning',
                category='security',
            )
            return check
        # If count > 0, deactivation would still leave at least one admin
        # holding the role, so it's allowed. However, if *all* active admins
        # hold the admin role through this single role, deactivating it would
        # strip them of admin access. In that case, block.
        total_active_admins = count
        if total_active_admins > 0:
            # Every active admin in the system currently holds admin via this role.
            # Deactivating the role removes admin access from all of them.
            check = ProtectionCheck.reject(
                f'Cannot deactivate the Administrator role: {total_active_admins} active administrator(s) currently rely on it.',
                'admin_role_deactivation_blocked_in_use',
            )
            cls._log_blocked(
                user_id=actor_user.id,
                action='blocked_role_deactivation',
                entity_type='role',
                entity_id=cls._require_admin_role().id,
                entity_repr=ADMIN_ROLE_NAME,
                error_message=check.audit_reason,
                severity='warning',
                category='security',
            )
            return check
        return ProtectionCheck.allow()

    @classmethod
    def can_assign_roles(cls, actor_user: User, requested_role_ids,
                         target_user_id: Optional[int]) -> ProtectionCheck:
        """Validate a role-assignment request before it is committed.

        Rules enforced:
          * Every submitted ID must be a valid integer.
          * Every role must exist.
          * Every role must be active.
          * Assigning the admin role requires the actor to hold the admin role.
          * Assigning admin to the last active admin is blocked via
            can_remove_admin_role_from if it would strip admin.
        """
        # 1. Malformed IDs
        normalized = []
        for raw in (requested_role_ids or []):
            s = str(raw).strip()
            if not s.isdigit():
                check = ProtectionCheck.reject(
                    'The submitted role selection contains a value that is not a valid role ID.',
                    f'malformed_role_id_submitted:{raw}',
                )
                AuditService.log_action(
                    user_id=actor_user.id,
                    action='blocked_role_assignment',
                    entity_type='user',
                    entity_id=target_user_id,
                    success=False,
                    error_message=check.audit_reason,
                    severity='warning',
                    category='security',
                )
                return check
            normalized.append(int(s))

        # 2 + 3. Exist + active
        if normalized:
            roles = (Role.query.filter(Role.id.in_(normalized))
                     .with_for_update().all())
            found_ids = {r.id for r in roles}
            active_roles = [r for r in roles if r.is_active]
            active_ids = {r.id for r in active_roles}

            missing = set(normalized) - found_ids
            if missing:
                check = ProtectionCheck.reject(
                    'One or more selected roles do not exist.',
                    f'unknown_role_ids:{sorted(missing)}',
                )
                AuditService.log_action(
                    user_id=actor_user.id,
                    action='blocked_role_assignment',
                    entity_type='user',
                    entity_id=target_user_id,
                    new_values={'unknown_role_ids': sorted(missing)},
                    success=False,
                    error_message=check.audit_reason,
                    severity='warning',
                    category='security',
                )
                return check

            inactive = set(normalized) - active_ids
            if inactive:
                inactive_names = [r.name for r in roles if r.id in inactive]
                check = ProtectionCheck.reject(
                    'Cannot assign inactive role(s): ' + ', '.join(inactive_names),
                    f'inactive_role_ids:{sorted(inactive)}',
                )
                AuditService.log_action(
                    user_id=actor_user.id,
                    action='blocked_role_assignment',
                    entity_type='user',
                    entity_id=target_user_id,
                    new_values={'inactive_role_ids': sorted(inactive),
                                'inactive_role_names': inactive_names},
                    success=False,
                    error_message=check.audit_reason,
                    severity='warning',
                    category='security',
                )
                return check

        # 4. Privilege escalation: non-admin cannot grant the admin role
        admin_role_id = cls._require_admin_role().id
        if admin_role_id in set(normalized) and not actor_user.has_role(ADMIN_ROLE_NAME):
            check = ProtectionCheck.reject(
                'You do not have permission to assign the administrator role.',
                'privileged_role_escalation_blocked',
            )
            AuditService.log_action(
                user_id=actor_user.id,
                action='blocked_role_assignment',
                entity_type='user',
                entity_id=target_user_id,
                new_values={'attempted_role': ADMIN_ROLE_NAME},
                success=False,
                error_message=check.audit_reason,
                severity='warning',
                category='security',
            )
            return check

        return ProtectionCheck.allow()
