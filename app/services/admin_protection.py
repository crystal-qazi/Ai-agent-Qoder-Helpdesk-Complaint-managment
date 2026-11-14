"""Centralized administrator-protection service.

Consolidates every rule that prevents the application from being left without
a working administrator. Callers in app/routes/users.py MUST use these
helpers instead of duplicating the checks so that:

  1. The rule set lives in exactly one place.
  2. Concurrent operations against the same rows are serialized through
     ``SELECT ... FOR UPDATE`` row locks. The admin role row is locked first
     to provide a single, stable serialization point; the specific
     active-admin ``users`` rows are then row-locked. Callers must never
     use an aggregate ``COUNT`` as a lock.
  3. Every check runs from a single admin role row resolved by name
     (``ADMIN_ROLE_NAME``). No hardcoded role ID is used anywhere.
  4. Security-critical rejections are recorded in the audit log with
     ``success=False`` so operators can spot attempted privilege
     escalation, self-removal, or cross-admin stripping.
"""
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from app.extensions import db
from app.models import User, Role
from sqlalchemy import select

# The role name that is treated as the "privileged" administrator role.
# This is a system-level concept (seeded as ``is_system=True``); see the
# data-repair script for how it is identified.
ADMIN_ROLE_NAME = 'admin'


def _int_ids(raw: Iterable) -> list:
    return [int(x) for x in (raw or []) if str(x).strip().isdigit()]


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
    @classmethod
    def _log_blocked(cls, user_id, action, entity_type, entity_id, **kw):
        """Persist a rejected security event in an independent transaction.

        Delegates to :meth:`AuditService.log_blocked_security`, which owns
        its own session so that a caller-side rollback can never erase
        the evidence of a blocked security event.
        """
        from app.services.audit import AuditService
        return AuditService.log_blocked_security(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_repr=kw.pop('entity_repr', None),
            old_values=kw.pop('old_values', None),
            new_values=kw.pop('new_values', None),
            changed_fields=kw.pop('changed_fields', None),
            error_message=kw.pop('error_message', None),
            severity=kw.pop('severity', 'warning'),
            category=kw.pop('category', 'security'),
        )

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
    def _lock_active_admins(cls, exclude_user_id: Optional[int] = None):
        """Return the list of active users holding the admin role.

        Acquires the shared admin-role row lock first (a single stable
        serialization point for every last-admin check), then row-locks
        each active admin's ``users`` row via ``SELECT ... FOR UPDATE``
        on the specific row (MySQL 8+ supports this on InnoDB). The
        result is used for membership decisions, not as a lock itself;
        no caller may substitute an aggregate COUNT for this.
        """
        cls._require_admin_role()
        q = (
            db.session.query(User)
            .join(User.roles)
            .filter(Role.name == ADMIN_ROLE_NAME,
                    Role.is_active == True,
                    User.is_active == True)
            .with_for_update()
            .order_by(User.id.asc())
        )
        admins = q.all()
        if exclude_user_id is not None:
            admins = [u for u in admins if u.id != exclude_user_id]
        return admins

    # ------------------------------------------------------------------
    # High-level checks (each returns ProtectionCheck; rejections are
    # audited before the caller redirects back to the form).
    # ------------------------------------------------------------------
    @classmethod
    def can_deactivate_user(cls, user: User, actor_user: User) -> ProtectionCheck:
        """Block deactivation of the last active admin user."""
        if not user.has_role(ADMIN_ROLE_NAME):
            return ProtectionCheck.allow()

        admins = cls._lock_active_admins(exclude_user_id=user.id)
        if len(admins) == 0:
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
        """Block removing the admin role in any last-admin-impacting case.

        Two independent rules are enforced here so that a non-admin actor
        with ``users.manage`` cannot strip administrator privileges from
        another admin, and a self-actor cannot drop the last admin.

        Both checks run on the row-locked admin set returned by
        ``_lock_active_admins`` — never on an aggregate COUNT.
        """
        submitted = _int_ids(new_role_ids)
        admin_role = cls._require_admin_role()
        admin_role_id = admin_role.id

        # Privilege-escalation rule: only an admin may strip admin.
        target_is_admin = user.has_role(ADMIN_ROLE_NAME)
        if target_is_admin and admin_role_id not in submitted:
            # The submission would remove the admin role from the target.
            actor_is_admin = actor_user.has_role(ADMIN_ROLE_NAME)
            if not actor_is_admin:
                check = ProtectionCheck.reject(
                    'You do not have permission to remove the administrator role from another user.',
                    'admin_role_removal_from_other_blocked',
                )
                cls._log_blocked(
                    user_id=actor_user.id,
                    action='blocked_admin_role_removal_from_other',
                    entity_type='user',
                    entity_id=user.id,
                    entity_repr=user.username,
                    new_values={'target_user_id': user.id,
                                'submitted_role_ids': submitted},
                    error_message=check.audit_reason,
                    severity='warning',
                    category='security',
                )
                return check

        # Last-admin rule: whoever the target is, no admin set may drop
        # below one remaining active admin.
        if target_is_admin and admin_role_id not in submitted:
            # Target is admin and is about to lose admin; count the
            # remaining admins excluding this target.
            remaining = cls._lock_active_admins(exclude_user_id=user.id)
            if len(remaining) == 0:
                check = ProtectionCheck.reject(
                    'Cannot remove the administrator role: no other active administrator remains.',
                    'last_active_admin_role_removal_blocked',
                )
                cls._log_blocked(
                    user_id=actor_user.id,
                    action='blocked_role_removal',
                    entity_type='user',
                    entity_id=user.id,
                    entity_repr=user.username,
                    new_values={'removed_role': ADMIN_ROLE_NAME,
                                'submitted_role_ids': submitted},
                    error_message=check.audit_reason,
                    severity='warning',
                    category='security',
                )
                return check

        return ProtectionCheck.allow()

    @classmethod
    def can_deactivate_admin_role(cls, actor_user: User) -> ProtectionCheck:
        """Block deactivation of the admin role while any active admin depends on it."""
        admins = cls._lock_active_admins()
        if len(admins) == 0:
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
        # Every active admin in the system currently holds admin via
        # this single role. Deactivating it would strip them all.
        check = ProtectionCheck.reject(
            f'Cannot deactivate the Administrator role: {len(admins)} active administrator(s) currently rely on it.',
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

    @classmethod
    def can_edit_admin_role(cls, actor_user: User, submitted_permission_ids,
                           original_permission_ids: Optional[Sequence[int]] = None,
                           role_id: Optional[int] = None) -> ProtectionCheck:
        """Guard edits to the admin role's permission set.

        A non-admin with ``roles.manage`` must not be able to modify the
        admin role's permissions in a way that would change what any
        active admin can do. The rule:

        * If the submitted set is empty or omits every permission that
          an active admin currently holds, reject unless the actor is
          themselves an active admin.
        * If the actor is not an active admin at all, reject any edit
          of the admin role, full stop.

        The admin role row is locked via ``_require_admin_role`` and
        the active admin users are row-locked via ``_lock_active_admins``
        — no aggregate count is used as a lock.
        """
        admin_role = cls._require_admin_role()
        if role_id is not None and role_id != admin_role.id:
            return ProtectionCheck.allow()

        submitted = set(_int_ids(submitted_permission_ids))
        original = set(original_permission_ids) if original_permission_ids else None

        # If the actor does not hold the admin role, only allow edits that
        # do not reduce the effective permission set of any active admin.
        actor_is_admin = actor_user.has_role(ADMIN_ROLE_NAME)
        admins = cls._lock_active_admins()
        if actor_is_admin:
            return ProtectionCheck.allow()

        # Non-admin actor: block any edit to the admin role.
        check = ProtectionCheck.reject(
            'Only administrators may modify the administrator role.',
            'admin_role_edit_by_non_admin_blocked',
        )
        cls._log_blocked(
            user_id=actor_user.id,
            action='blocked_admin_role_edit',
            entity_type='role',
            entity_id=admin_role.id,
            entity_repr=ADMIN_ROLE_NAME,
            new_values={'submitted_permission_ids': sorted(submitted)},
            error_message=check.audit_reason,
            severity='warning',
            category='security',
        )
        return check

    @classmethod
    def can_assign_roles(cls, actor_user: User, requested_role_ids,
                         target_user_id: Optional[int]) -> ProtectionCheck:
        """Validate a role-assignment request before it is committed.

        Rules enforced:
          * Every submitted ID must be a valid integer.
          * Every role must exist.
          * Every role must be active.
          * Assigning the admin role requires the actor to hold the admin role.
          * Removing the admin role from a target user requires the actor to
            hold the admin role (cross-admin stripping is blocked).
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
                cls._log_blocked(
                    user_id=actor_user.id,
                    action='blocked_role_assignment',
                    entity_type='user',
                    entity_id=target_user_id,
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
                cls._log_blocked(
                    user_id=actor_user.id,
                    action='blocked_role_assignment',
                    entity_type='user',
                    entity_id=target_user_id,
                    new_values={'unknown_role_ids': sorted(missing)},
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
                cls._log_blocked(
                    user_id=actor_user.id,
                    action='blocked_role_assignment',
                    entity_type='user',
                    entity_id=target_user_id,
                    new_values={'inactive_role_ids': sorted(inactive),
                                'inactive_role_names': inactive_names},
                    error_message=check.audit_reason,
                    severity='warning',
                    category='security',
                )
                return check

        # 4. Privilege escalation: non-admin cannot grant the admin role
        admin_role_id = cls._require_admin_role().id
        admin_in_set = admin_role_id in set(normalized)
        actor_is_admin = actor_user.has_role(ADMIN_ROLE_NAME)
        if admin_in_set and not actor_is_admin:
            check = ProtectionCheck.reject(
                'You do not have permission to assign the administrator role.',
                'privileged_role_escalation_blocked',
            )
            cls._log_blocked(
                user_id=actor_user.id,
                action='blocked_role_assignment',
                entity_type='user',
                entity_id=target_user_id,
                new_values={'attempted_role': ADMIN_ROLE_NAME},
                error_message=check.audit_reason,
                severity='warning',
                category='security',
            )
            return check

        # 5. Cross-admin stripping: if the target is an admin user and the
        #    submitted set omits the admin role, the actor must be an admin.
        if target_user_id is not None and not admin_in_set:
            target = db.session.get(User, target_user_id)
            if target is not None and target.has_role(ADMIN_ROLE_NAME) and not actor_is_admin:
                check = ProtectionCheck.reject(
                    'You do not have permission to remove the administrator role from another user.',
                    'admin_role_removal_from_other_blocked',
                )
                cls._log_blocked(
                    user_id=actor_user.id,
                    action='blocked_admin_role_removal_from_other',
                    entity_type='user',
                    entity_id=target_user_id,
                    entity_repr=target.username,
                    new_values={'submitted_role_ids': normalized},
                    error_message=check.audit_reason,
                    severity='warning',
                    category='security',
                )
                return check

        return ProtectionCheck.allow()
