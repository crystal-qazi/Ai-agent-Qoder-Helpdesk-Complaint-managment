"""Rebuild the database schema from the current models and seed defaults.

Destructive by design: drops every table known to the SQLAlchemy metadata
before recreating it. Only run against the development database.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

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


PERMISSIONS = [
    # dashboard
    ('dashboard.view', 'View Dashboard', 'dashboard', 'view'),
    # complaints
    ('complaints.create', 'Create Complaint', 'complaints', 'create'),
    ('complaints.view_all', 'View All Complaints', 'complaints', 'view_all'),
    ('complaints.view_assigned', 'View Assigned Complaints', 'complaints', 'view_assigned'),
    ('complaints.edit', 'Edit Any Complaint', 'complaints', 'edit'),
    ('complaints.edit_own', 'Edit Own Complaint', 'complaints', 'edit_own'),
    ('complaints.edit_assigned', 'Edit Assigned Complaint', 'complaints', 'edit_assigned'),
    ('complaints.update', 'Update Complaint', 'complaints', 'update'),
    ('complaints.assign', 'Assign Complaints', 'complaints', 'assign'),
    ('complaints.reassign', 'Reassign Any Complaint', 'complaints', 'reassign'),
    ('complaints.reassign_own', 'Reassign Own Complaint', 'complaints', 'reassign_own'),
    ('complaints.change_status', 'Change Any Status', 'complaints', 'change_status'),
    ('complaints.change_status_assigned', 'Change Assigned Status', 'complaints', 'change_status_assigned'),
    ('complaints.resolve', 'Resolve Any Complaint', 'complaints', 'resolve'),
    ('complaints.resolve_assigned', 'Resolve Assigned Complaint', 'complaints', 'resolve_assigned'),
    ('complaints.close', 'Close Any Complaint', 'complaints', 'close'),
    ('complaints.close_assigned', 'Close Assigned Complaint', 'complaints', 'close_assigned'),
    ('complaints.reopen', 'Reopen Any Complaint', 'complaints', 'reopen'),
    ('complaints.reopen_own', 'Reopen Own Complaint', 'complaints', 'reopen_own'),
    ('complaints.reopen_assigned', 'Reopen Assigned Complaint', 'complaints', 'reopen_assigned'),
    ('complaints.reject', 'Reject Complaints', 'complaints', 'reject'),
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
    'complaints.create', 'complaints.view_all', 'complaints.view_assigned',
    'complaints.edit', 'complaints.edit_assigned', 'complaints.update',
    'complaints.assign', 'complaints.reassign', 'complaints.change_status',
    'complaints.change_status_assigned', 'complaints.resolve',
    'complaints.resolve_assigned', 'complaints.close', 'complaints.close_assigned',
    'complaints.reopen', 'complaints.reopen_assigned', 'complaints.reject',
    'comments.add_internal', 'comments.add_reporter_visible', 'comments.view_internal',
    'attachments.upload', 'attachments.download_all', 'attachments.delete',
    'reports.view', 'reports.export', 'users.view',
]

USER_PERMISSIONS = [
    'dashboard.view',
    'complaints.create', 'complaints.edit_own', 'complaints.reopen_own',
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


def main():
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    with app.app_context():
        print(f'Database: {app.config["SQLALCHEMY_DATABASE_URI"]}')
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

        agent_role = Role(name='agent', display_name='Support Agent',
                          description='Handle and resolve complaints', is_system=True)
        agent_role.permissions.extend(permissions[p] for p in AGENT_PERMISSIONS)

        user_role = Role(name='user', display_name='End User',
                         description='Submit and track own complaints', is_system=True)
        user_role.permissions.extend(permissions[p] for p in USER_PERMISSIONS)

        db.session.add_all([admin_role, agent_role, user_role])
        db.session.flush()
        print('Created 3 roles')

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

        # 12. Demo agent and end user
        agent = User(
            username='agent',
            email='agent@hospital.local',
            first_name='Support',
            last_name='Agent',
            employee_number='AGT001',
            department_id=departments['IT'].id,
            is_active=True,
        )
        agent.set_password('Agent@123')
        agent.roles.append(agent_role)
        db.session.add(agent)

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
        print('Created users: admin / Admin@123, agent / Agent@123, user / User@123')

        print('\nFinal counts:')
        table_counts()
        print('\nDatabase rebuilt and seeded successfully.')


if __name__ == '__main__':
    main()
