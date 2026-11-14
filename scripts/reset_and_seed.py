"""Rebuild the database schema from the current models and seed defaults.

Destructive by design: drops every table known to the SQLAlchemy metadata
before recreating it.  Only run against a *test* database, never against
the production application database.

Safety contract:

  * ``DB_NAME`` must match ``helpdesk_<identifier>_test`` or
    ``TEST_DB_NAME`` must be set to such a name.  The script refuses to
    run against any other schema, including the application database.
  * The script prints the target DB name before doing anything destructive
    so the operator can confirm the target is the one they intended.

Usage::

    set TARGET_TEST_DB=1    (Windows)   or   TARGET_TEST_DB=1 (POSIX)
    python scripts/reset_and_seed.py

Without the flag, the script refuses to start.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def _target_database():
    """Return the configured test database name and assert it is test-only."""
    test_db_name = os.environ.get('TEST_DB_NAME', '')
    if not test_db_name:
        # Fall back to DB_NAME, but we still require the _test suffix.
        test_db_name = os.environ.get('DB_NAME', '')
    if not test_db_name:
        raise SystemExit(
            'reset_and_seed.py requires either TEST_DB_NAME or DB_NAME to '
            'be set.  The name must match the pattern '
            'helpdesk_<identifier>_test.'
        )
    if not re.fullmatch(r'helpdesk_[a-z0-9_]*_test', test_db_name):
        raise SystemExit(
            f'reset_and_seed.py refuses to target database {test_db_name!r}. '
            'The name must match helpdesk_<identifier>_test. '
            'Set TEST_DB_NAME=helpdesk_<identifier>_test before running.'
        )
    return test_db_name


def main():
    """Entry point: validate the test-only target, then run the rebuild."""
    if os.environ.get('TARGET_TEST_DB') != '1':
        raise SystemExit(
            'refusing to run: set TARGET_TEST_DB=1 to confirm this is a '
            'test-only run against a helpdesk_<identifier>_test database.'
        )
    if os.environ.get('FLASK_ENV', '').lower() == 'production':
        raise SystemExit('refusing to run reset_and_seed.py in production.')
    target = _target_database()
    host = os.environ.get('DB_HOST', 'localhost').strip().lower()
    if host not in {'localhost', '127.0.0.1', '::1'}:
        raise SystemExit('refusing destructive reset on a non-local database host.')
    db_user = os.environ.get('DB_USER', '').strip()
    db_password = os.environ.get('DB_PASSWORD', '')
    if not db_user or db_user.lower() == 'root' or not db_password:
        raise SystemExit('Set a non-root DB_USER and non-empty DB_PASSWORD for the disposable test database.')
    from sqlalchemy.engine import URL
    database_url = URL.create('mysql+pymysql', username=db_user,
        password=db_password, host=host,
        port=int(os.environ.get('DB_PORT', '3306')), database=target)
    os.environ['TEST_DB_NAME'] = target
    os.environ['DATABASE_URL'] = database_url.render_as_string(hide_password=False)
    _do_rebuild()


PERMISSIONS = [
    # dashboard
    ('dashboard.view', 'View Dashboard', 'dashboard', 'view'),
    # complaints — exactly 9 permissions per spec
    ('complaints.create', 'Create Complaint', 'complaints', 'create'),
    ('complaints.view_all', 'View All Complaints', 'complaints', 'view_all'),
    ('complaints.view_confidential', 'View Confidential Complaints', 'complaints', 'view_confidential'),
    ('complaints.view_my', 'View My Complaints', 'complaints', 'view_my'),
    ('complaints.edit', 'Edit Complaint', 'complaints', 'edit'),
    ('complaints.assign', 'Assign Complaint', 'complaints', 'assign'),
    ('complaints.transfer', 'Transfer Complaint', 'complaints', 'transfer'),
    ('complaints.change_status_own', 'Change Status of Own Complaints', 'complaints', 'change_status_own'),
    ('complaints.change_status_all', 'Change Status of Any Complaint', 'complaints', 'change_status_all'),
    ('complaints.status_unlock', 'Access Restricted Statuses', 'complaints', 'status_unlock'),
    ('complaints.delete', 'Delete Complaints', 'complaints', 'delete'),
    # comments
    ('comments.add_internal', 'Add Internal Comment', 'comments', 'add_internal'),
    ('comments.add_reporter_visible', 'Add Reporter Comment', 'comments', 'add_reporter_visible'),
    ('comments.view_internal', 'View Internal Comments', 'comments', 'view_internal'),
    # attachments
    ('attachments.upload', 'Upload Attachments', 'attachments', 'upload'),
    ('attachments.download_all', 'Download All Attachments', 'attachments', 'download_all'),
    ('attachments.delete', 'Delete Any Attachment', 'attachments', 'delete'),
    ('attachments.delete_own', 'Delete Own Attachment', 'attachments', 'delete_own'),
    # reports
    ('reports.view', 'View Reports', 'reports', 'view'),
    ('reports.export', 'Export Reports', 'reports', 'export'),
    # users / rbac
    ('users.view', 'View Users', 'users', 'view'),
    ('users.edit', 'Edit Users', 'users', 'edit'),
    ('users.manage', 'Manage Users', 'users', 'manage'),
    ('roles.manage', 'Manage Roles', 'roles', 'manage'),
    ('permissions.manage', 'Manage Permissions', 'permissions', 'manage'),
    # administration
    ('config.manage', 'Manage Configuration', 'config', 'manage'),
    ('settings.manage', 'Manage System Settings', 'settings', 'manage'),
    ('departments.manage', 'Manage Departments', 'departments', 'manage'),
    ('categories.manage', 'Manage Categories', 'categories', 'manage'),
    ('priorities.manage', 'Manage Priorities', 'priorities', 'manage'),
    ('statuses.manage', 'Manage Statuses', 'statuses', 'manage'),
    ('sla.manage', 'Manage SLA Policies', 'sla', 'manage'),
    ('software.manage', 'Manage Software Catalog', 'software', 'manage'),
    ('audit.view', 'View Audit Logs', 'audit', 'view'),
]

AGENT_PERMISSIONS = [
    'dashboard.view',
    'complaints.create', 'complaints.view_all', 'complaints.view_my',
    'complaints.edit', 'complaints.assign', 'complaints.transfer',
    'complaints.change_status_own', 'complaints.change_status_all',
    'complaints.status_unlock',
    'comments.add_internal', 'comments.add_reporter_visible', 'comments.view_internal',
    'attachments.upload', 'attachments.download_all', 'attachments.delete',
    'reports.view', 'reports.export', 'users.view',
]

SUPPORT_AGENT_PERMISSIONS = [
    'dashboard.view',
    'complaints.create', 'complaints.view_my',
    'complaints.edit', 'complaints.transfer',
    'complaints.change_status_own',
    'comments.add_internal', 'comments.add_reporter_visible', 'comments.view_internal',
    'attachments.upload', 'attachments.download_all',
    'reports.view', 'reports.export', 'notifications.view',
]

USER_PERMISSIONS = [
    'dashboard.view',
    'complaints.create',
    'comments.add_reporter_visible',
    'attachments.upload', 'attachments.delete_own',
]

STATUSES = [
    # name, code, category, is_initial, is_terminal, requires_reason,
    # requires_resolution, color, icon, sort_order
    ('New', 'new', 'open', True, False, False, False, '#3B82F6', 'inbox', 1),
    ('Assigned', 'assigned', 'open', False, False, False, False, '#8B5CF6', 'user-check', 2),
    ('In Progress', 'in_progress', 'in_progress', False, False, False, False, '#F59E0B', 'loader', 3),
    ('Pending Info', 'pending_info', 'pending', False, False, False, False, '#F97316', 'help-circle', 4),
    ('On Hold', 'on_hold', 'pending', False, False, False, False, '#6B7280', 'pause', 5),
    ('Resolved', 'resolved', 'resolved', False, False, False, True, '#10B981', 'check-circle', 6),
    ('Closed', 'closed', 'closed', False, True, False, False, '#4B5563', 'lock', 7),
    ('Reopened', 'reopened', 'open', False, False, True, False, '#EF4444', 'rotate-ccw', 8),
    ('Rejected', 'rejected', 'closed', False, True, True, False, '#DC2626', 'x-circle', 9),
]

PRIORITIES = [
    # name, code, level, color, icon, description, sort_order
    ('Critical', 'CRITICAL', 1, '#EF4444', 'alert-octagon', 'Patient safety or full outage', 1),
    ('High', 'HIGH', 2, '#F97316', 'alert-triangle', 'Major disruption to clinical work', 2),
    ('Medium', 'MEDIUM', 3, '#3B82F6', 'alert-circle', 'Limited impact with a workaround', 3),
    ('Low', 'LOW', 4, '#6B7280', 'info', 'Minor or cosmetic issue', 4),
]

SLA_TARGETS = {
    'CRITICAL': (60, 240),
    'HIGH': (240, 1440),
    'MEDIUM': (480, 2880),
    'LOW': (1440, 5760),
}

DEPARTMENTS = [
    ('IT Helpdesk', 'IT', 'First-line IT support', 'Ground Floor, Building A'),
    ('Network Operations', 'NET', 'Network and connectivity team', 'Basement, Building A'),
    ('Clinical Systems', 'CLN', 'HIS, LIS, PACS and clinical applications', 'Second Floor, Building B'),
    ('Patient Administration', 'PAT', 'Admissions, records and patient portal', 'First Floor, Building B'),
    ('Billing', 'BIL', 'Billing and finance systems', 'Third Floor, Building A'),
]

CATEGORIES = [
    ('Hardware', 'HARDWARE', 'Computers, printers, peripherals'),
    ('Software', 'SOFTWARE', 'Applications and licenses'),
    ('Network', 'NETWORK', 'Connectivity, Wi-Fi, VPN'),
    ('Access & Accounts', 'ACCESS', 'Accounts, passwords and permissions'),
    ('Printing', 'PRINTING', 'Printers and print queues'),
    ('Clinical Application', 'CLINICAL', 'Clinical system issues'),
    ('Other', 'OTHER', 'Anything else'),
]

SOFTWARE = [
    ('Hospital Information System', 'HIS', 'Core hospital information system', 'Vendor A'),
    ('Laboratory Information System', 'LIS', 'Lab order and result management', 'Vendor B'),
    ('PACS', 'PACS', 'Medical imaging archive', 'Vendor C'),
    ('Radiology Information System', 'RIS', 'Radiology workflow', 'Vendor C'),
    ('Pharmacy System', 'PHARM', 'Pharmacy dispensing and stock', 'Vendor D'),
    ('Billing & ERP', 'ERP', 'Finance and billing suite', 'Vendor E'),
    ('Email', 'EMAIL', 'Corporate email service', 'Vendor F'),
]

SETTINGS = [
    ('app_name', 'IT Software Complain System', 'string', 'general', 'Application title', True),
    ('support_email', 'it-helpdesk@hospital.local', 'string', 'general', 'Helpdesk contact email', True),
    ('sla_warning_threshold_percent', '80', 'integer', 'sla', 'Warn when SLA elapsed exceeds this percentage', False),
    ('allow_self_registration', 'false', 'boolean', 'security', 'Allow users to self-register', False),
    ('max_attachment_size_mb', '16', 'integer', 'general', 'Maximum attachment size in MB', False),
]


def table_counts():
    tables = [
        'users', 'roles', 'permissions', 'departments', 'categories',
        'statuses', 'priorities', 'sla_policies', 'working_schedules',
        'software_catalog', 'system_settings',
    ]
    for name in tables:
        try:
            count = db.session.execute(text(f'SELECT COUNT(*) FROM `{name}`')).scalar()
            print(f'  {name}: {count}')
        except Exception as exc:  # noqa: BLE001
            print(f'  {name}: ERROR {exc}')


def _do_rebuild():
    """Perform the destructive schema reset + seed against the target DB.

    ``create_app`` reads ``SQLALCHEMY_DATABASE_URI`` from the environment,
    which main() has already pointed at the validated test database.
    """
    from sqlalchemy import text

    from app import create_app
    from app.extensions import db
    import app.models  # noqa: F401  (registers all mappers / tables)
    from app.models import (
        User, Role, Permission, UserProfile, LoginAttempt,
        Department, SoftwareCatalog, Category, Priority, Status,
        Complaint, ComplaintAssignment, ComplaintStatusHistory,
        ComplaintHistory, Comment, Attachment,
        SLAPolicy, SLAHistory, Holiday, WorkingSchedule,
        Notification, AuditLog, SystemSetting,
    )

    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    with app.app_context():
        # Fail-closed: confirm we are talking to the target test database.
        target = os.environ.get('TEST_DB_NAME')
        with db.engine.connect() as connection:
            actual_database, actual_host = connection.execute(
                text('SELECT DATABASE(), @@hostname')
            ).one()
        if not target or actual_database != target:
            raise SystemExit('Connected database identity does not match TEST_DB_NAME; aborting.')
        if os.environ.get('DB_HOST', 'localhost').strip().lower() not in {'localhost', '127.0.0.1', '::1'}:
            raise SystemExit('Destructive reset is restricted to a local database host.')
        print(f'Database: {actual_database} on {actual_host} (credentials hidden)')
        print('Dropping existing tables...')
        db.session.remove()
        existing = db.inspect(db.engine).get_table_names()
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=0'))
        for name in existing:
            db.session.execute(text(f'DROP TABLE IF EXISTS `{name}`'))
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=1'))
        db.session.commit()

        print('Creating tables from current models...')
        db.create_all()

        # 1. Permissions
        permissions = {}
        for name, display_name, module, action in PERMISSIONS:
            perm = Permission(name=name, display_name=display_name,
                              module=module, action=action)
            db.session.add(perm)
            permissions[name] = perm
        db.session.flush()
        print(f'Created {len(permissions)} permissions')

        # 2. Roles
        admin_role = Role(name='admin', display_name='Administrator',
                          description='Full system access', is_system=True)
        admin_role.permissions.extend(permissions.values())

        helpdesk_role = Role(name='helpdesk_agent', display_name='Helpdesk Agent',
                             description='Intake and manage complaints end-to-end', is_system=True)
        helpdesk_role.permissions.extend(permissions[p] for p in AGENT_PERMISSIONS)

        support_role = Role(name='support_agent', display_name='Support Agent',
                            description='Resolve assigned complaints', is_system=True)
        support_role.permissions.extend(permissions[p] for p in SUPPORT_AGENT_PERMISSIONS)

        user_role = Role(name='user', display_name='End User',
                         description='Submit and track own complaints', is_system=True)
        user_role.permissions.extend(permissions[p] for p in USER_PERMISSIONS)

        db.session.add_all([admin_role, helpdesk_role, support_role, user_role])
        db.session.flush()
        print('Created 4 roles')

        # 3. Working schedule (needed by SLA policies)
        schedule = WorkingSchedule(
            name='Standard Business Hours',
            description='Monday to Friday, 09:00-17:00',
            timezone='UTC',
            weekly_schedule={
                '0': {'start': '09:00', 'end': '17:00'},
                '1': {'start': '09:00', 'end': '17:00'},
                '2': {'start': '09:00', 'end': '17:00'},
                '3': {'start': '09:00', 'end': '17:00'},
                '4': {'start': '09:00', 'end': '17:00'},
                '5': None,
                '6': None,
            },
            exceptions={},
            is_active=True,
            is_default=True,
        )
        db.session.add(schedule)
        db.session.flush()
        print('Created default working schedule')

        # 4. Departments
        departments = {}
        for name, code, description, location in DEPARTMENTS:
            dept = Department(name=name, code=code, description=description,
                              location=location, is_active=True)
            db.session.add(dept)
            departments[code] = dept
        db.session.flush()
        print(f'Created {len(departments)} departments')

        # 5. Statuses
        for name, code, category, is_initial, is_terminal, requires_reason, \
                requires_resolution, color, icon, sort_order in STATUSES:
            db.session.add(Status(
                name=name, code=code, category=category, is_initial=is_initial,
                is_terminal=is_terminal, requires_reason=requires_reason,
                requires_resolution=requires_resolution, color=color, icon=icon,
                sort_order=sort_order, is_active=True,
            ))
        db.session.flush()
        print(f'Created {len(STATUSES)} statuses')

        # 6. Priorities
        priorities = {}
        for name, code, level, color, icon, description, sort_order in PRIORITIES:
            pri = Priority(name=name, code=code, level=level, color=color,
                           icon=icon, description=description,
                           sort_order=sort_order, is_active=True)
            db.session.add(pri)
            priorities[code] = pri
        db.session.flush()
        print(f'Created {len(priorities)} priorities')

        # 7. SLA policies linked to priorities
        for code, (response_minutes, resolution_minutes) in SLA_TARGETS.items():
            pri = priorities[code]
            policy = SLAPolicy(
                name=f'{pri.name} Priority SLA',
                description=f'Default SLA for {pri.name.lower()} priority complaints',
                priority_id=pri.id,
                response_target_minutes=response_minutes,
                resolution_target_minutes=resolution_minutes,
                use_business_hours=True,
                working_schedule_id=schedule.id,
                escalation_enabled=code in ('CRITICAL', 'HIGH'),
                pause_on_pending_info=True,
                pause_on_hold=True,
                is_active=True,
                is_default=(code == 'MEDIUM'),
                sort_order=pri.level,
            )
            db.session.add(policy)
            db.session.flush()
            pri.default_sla_policy_id = policy.id
        print(f'Created {len(SLA_TARGETS)} SLA policies')

        # 8. Categories
        for name, code, description in CATEGORIES:
            db.session.add(Category(name=name, code=code, description=description,
                                    is_active=True))
        print(f'Created {len(CATEGORIES)} categories')

        # 9. Software catalog
        for name, code, description, vendor in SOFTWARE:
            db.session.add(SoftwareCatalog(
                name=name, code=code, description=description, vendor=vendor,
                department_id=departments['CLN'].id, is_active=True,
            ))
        print(f'Created {len(SOFTWARE)} software catalog entries')

        # 10. System settings
        for key, value, value_type, category, description, is_public in SETTINGS:
            db.session.add(SystemSetting(
                key=key, value=value, value_type=value_type, category=category,
                description=description, is_public=is_public, is_editable=True,
            ))
        print(f'Created {len(SETTINGS)} system settings')

        # 11. Admin user
        admin = User(
            username='admin',
            email='admin@hospital.local',
            first_name='System',
            last_name='Administrator',
            employee_number='ADMIN001',
            phone='0000000000',
            is_active=True,
        )
        admin.set_password('Admin@123')
        admin.roles.append(admin_role)
        db.session.add(admin)

        # 12. Demo helpdesk agent, support agent and end user
        helpdesk = User(
            username='helpdesk',
            email='helpdesk@hospital.local',
            first_name='Helpdesk',
            last_name='Agent',
            employee_number='HD001',
            department_id=departments['IT'].id,
            is_active=True,
        )
        helpdesk.set_password('Helpdesk@123')
        helpdesk.roles.append(helpdesk_role)
        db.session.add(helpdesk)

        support = User(
            username='support',
            email='support@hospital.local',
            first_name='Support',
            last_name='Agent',
            employee_number='SA001',
            department_id=departments['IT'].id,
            is_active=True,
        )
        support.set_password('Support@123')
        support.roles.append(support_role)
        db.session.add(support)

        end_user = User(
            username='user',
            email='user@hospital.local',
            first_name='Hospital',
            last_name='User',
            employee_number='USR001',
            department_id=departments['PAT'].id,
            is_active=True,
        )
        end_user.set_password('User@123')
        end_user.roles.append(user_role)
        db.session.add(end_user)

        db.session.commit()
        print('Created users: admin / Admin@123, helpdesk / Helpdesk@123, support / Support@123, user / User@123')

        print('\nFinal counts:')
        table_counts()
        print('\nDatabase rebuilt and seeded successfully.')


if __name__ == '__main__':
    main()
